"""Project editing view."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QFont, QKeySequence
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto import EntityDefinitionDTO, FieldDefinitionDTO
# Domain imports removed - presentation layer uses strings, not typed IDs (DTO-only MVVM)
from doc_helper.presentation.adapters.qt_translation_adapter import QtTranslationAdapter
from doc_helper.presentation.dialogs import (
    FieldHistoryDialog,
    ImportExportDialog,
    SearchDialog,
    SettingsDialog,
)
from doc_helper.presentation.factories import FieldWidgetFactory
from doc_helper.presentation.viewmodels.project_viewmodel import ProjectViewModel
from doc_helper.presentation.views.base_view import BaseView
from doc_helper.presentation.widgets.field_widget import IFieldWidget


class ProjectView(BaseView):
    """Project editing view.

    Main window for editing project fields.

    v1 Implementation:
    - Entity navigation sidebar (v1: single entity - Soil Investigation)
    - Dynamic field form based on schema
    - Field widgets for all 12 field types
    - Save button
    - Validation error indicators
    - Document generation button

    v2+ Deferred:
    - Multi-entity navigation
    - Quick search
    - Field history

    RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md):
    - Presentation layer uses DTOs, NOT domain objects
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        viewmodel: ProjectViewModel,
        entity_definition: EntityDefinitionDTO,
        translation_adapter: QtTranslationAdapter,
        widget_factory: Optional[FieldWidgetFactory] = None,
    ) -> None:
        """Initialize project view.

        Args:
            parent: Parent widget
            viewmodel: ProjectViewModel instance
            entity_definition: Entity definition DTO (NOT domain object)
            translation_adapter: Qt translation adapter for i18n with RTL/LTR support
            widget_factory: Factory for creating field widgets (default: new instance)
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._entity_definition = entity_definition
        self._translation_adapter = translation_adapter
        self._widget_factory = widget_factory or FieldWidgetFactory()

        # UI components
        self._fields_widget: Optional[QWidget] = None
        self._scroll_area: Optional[QScrollArea] = None
        self._save_button: Optional[QPushButton] = None
        self._generate_button: Optional[QPushButton] = None
        self._status_bar: Optional[QStatusBar] = None

        # Undo/Redo actions (U6 Phase 5)
        self._undo_action: Optional[QAction] = None
        self._redo_action: Optional[QAction] = None

        # Navigation actions (U7)
        self._back_action: Optional[QAction] = None
        self._forward_action: Optional[QAction] = None

        # Field widgets mapped by field ID
        self._field_widgets: dict[str, IFieldWidget] = {}
        # Field containers (QWidgets) mapped by field ID for navigation
        self._field_containers: dict[str, QWidget] = {}

        # Track if we've shown undo restoration message (ADR-031)
        self._shown_undo_restore_message = False

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Create main window
        self._root = QMainWindow(self._parent)
        self._root.setWindowTitle("Doc Helper - Project")
        self._root.resize(1024, 768)

        # Menu bar
        self._create_menu()

        # Central widget with main layout
        central_widget = QWidget()
        self._root.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Sidebar (v1: minimal - just project info)
        sidebar = self._create_sidebar()
        sidebar.setFixedWidth(200)
        main_layout.addWidget(sidebar)

        # Content area (fields form) with scroll
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._fields_widget = QWidget()
        fields_layout = QVBoxLayout(self._fields_widget)
        self._scroll_area.setWidget(self._fields_widget)

        main_layout.addWidget(self._scroll_area, 1)  # Stretch factor 1

        # Build field widgets
        self._build_field_widgets()

        # Status bar
        self._status_bar = QStatusBar()
        self._root.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        # Bind to ViewModel property changes
        self._viewmodel.subscribe("has_unsaved_changes", self._on_unsaved_changes)
        self._viewmodel.subscribe("project_name", self._on_project_name_changed)
        self._viewmodel.subscribe("can_undo", self._on_undo_state_changed)
        self._viewmodel.subscribe("can_redo", self._on_redo_state_changed)
        self._viewmodel.subscribe("can_go_back", self._on_nav_back_state_changed)
        self._viewmodel.subscribe("can_go_forward", self._on_nav_forward_state_changed)

        # Initialize undo/redo action states
        self._update_undo_action()
        self._update_redo_action()

        # Initialize navigation action states (U7)
        self._update_back_action()
        self._update_forward_action()

        # Perform initial validation
        self._update_validation()

    def _create_menu(self) -> None:
        """Create menu bar."""
        menubar = self._root.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        save_action = QAction("Save", self._root)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        generate_action = QAction("Generate Document", self._root)
        generate_action.triggered.connect(self._on_generate_document)
        file_menu.addAction(generate_action)

        file_menu.addSeparator()

        import_export_action = QAction("Import/Export...", self._root)
        import_export_action.triggered.connect(self._on_import_export)
        file_menu.addAction(import_export_action)

        file_menu.addSeparator()

        close_action = QAction("Close", self._root)
        close_action.triggered.connect(self._on_close)
        file_menu.addAction(close_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        undo_action = QAction("Undo", self._root)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.setToolTip(
            "Undo last change (Ctrl+Z)\n\n"
            "Undo history persists across saves and restarts.\n"
            "Cleared only when closing the project."
        )
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)
        self._undo_action = undo_action  # Store reference for state updates

        redo_action = QAction("Redo", self._root)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.setToolTip(
            "Redo previously undone change (Ctrl+Y)\n\n"
            "Redo history persists across saves and restarts.\n"
            "Cleared only when closing the project."
        )
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)
        self._redo_action = redo_action  # Store reference for state updates

        edit_menu.addSeparator()

        find_action = QAction("Find Fields...", self._root)
        find_action.setShortcut(QKeySequence("Ctrl+F"))
        find_action.triggered.connect(self._on_find_fields)
        edit_menu.addAction(find_action)

        # View menu (U7 - Navigation)
        view_menu = menubar.addMenu("View")

        back_action = QAction("Back", self._root)
        back_action.setShortcut(QKeySequence("Alt+Left"))
        back_action.triggered.connect(self._on_nav_back)
        view_menu.addAction(back_action)
        self._back_action = back_action  # Store reference for state updates

        forward_action = QAction("Forward", self._root)
        forward_action.setShortcut(QKeySequence("Alt+Right"))
        forward_action.triggered.connect(self._on_nav_forward)
        view_menu.addAction(forward_action)
        self._forward_action = forward_action  # Store reference for state updates

        view_menu.addSeparator()

        field_history_action = QAction("Field History...", self._root)
        field_history_action.triggered.connect(self._on_field_history)
        view_menu.addAction(field_history_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        settings_action = QAction("Settings...", self._root)
        settings_action.triggered.connect(self._on_settings)
        tools_menu.addAction(settings_action)

    def _create_sidebar(self) -> QWidget:
        """Create sidebar.

        Returns:
            Sidebar widget
        """
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)

        # Project info
        info_group = QGroupBox("Project")
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)

        project_name_label = QLabel(self._viewmodel.project_name)
        name_font = QFont("Arial", 10)
        name_font.setBold(True)
        project_name_label.setFont(name_font)
        project_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(project_name_label)

        sidebar_layout.addWidget(info_group)

        # Buttons
        self._save_button = QPushButton("Save")
        self._save_button.clicked.connect(self._on_save)
        sidebar_layout.addWidget(self._save_button)

        self._generate_button = QPushButton("Generate Document")
        self._generate_button.clicked.connect(self._on_generate_document)
        sidebar_layout.addWidget(self._generate_button)

        sidebar_layout.addStretch()

        return sidebar

    def _build_field_widgets(self) -> None:
        """Build field widgets based on entity definition.

        Creates widgets for all fields in entity definition using FieldWidgetFactory.
        Wires up value change callbacks to sync with ProjectViewModel.
        """
        if not self._fields_widget:
            return

        layout = self._fields_widget.layout()
        if not layout:
            return

        # Clear existing widgets
        self._field_widgets.clear()
        self._field_containers.clear()

        # Create widget for each field in entity definition
        for field_def in self._entity_definition.fields:
            # Create field widget using factory
            widget = self._widget_factory.create_widget(field_def)
            if not widget:
                # Unknown field type - skip (should not happen in v1)
                continue

            # Create field container with label and widget
            field_container = self._create_field_container(field_def, widget)
            layout.addWidget(field_container)

            # Store widget by field ID for later access
            self._field_widgets[field_def.id] = widget
            # Store container for navigation (ADR-026)
            self._field_containers[field_def.id] = field_container

            # Wire up value change callback
            field_id_value = field_def.id  # Capture for closure
            widget.on_value_changed(
                lambda value, fid=field_id_value: self._on_field_value_changed(fid, value)
            )

            # Set initial value from project
            self._set_initial_field_value(field_def.id, widget)

        # Add stretch to push fields to top
        layout.addStretch()

    def _create_field_container(
        self, field_def: FieldDefinitionDTO, widget: IFieldWidget
    ) -> QWidget:
        """Create a container widget for field with label.

        Args:
            field_def: Field definition DTO
            widget: Field widget instance

        Returns:
            Container widget with label and input
        """
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 4, 8, 4)

        # Field label with required indicator
        label_text = field_def.label
        if field_def.required:
            label_text += " *"

        field_label = QLabel(label_text)
        label_font = QFont("Arial", 9)
        if field_def.required:
            label_font.setBold(True)
        field_label.setFont(label_font)
        container_layout.addWidget(field_label)

        # Help text (if provided)
        if field_def.help_text:
            help_label = QLabel(field_def.help_text)
            help_font = QFont("Arial", 8)
            help_label.setFont(help_font)
            help_label.setStyleSheet("color: #666666;")
            help_label.setWordWrap(True)
            container_layout.addWidget(help_label)

        # Widget placeholder (actual Qt widget will be added by widget implementation)
        # For now, just add a placeholder label for the widget
        widget_placeholder = QLabel(f"[{field_def.field_type} widget placeholder]")
        widget_placeholder.setStyleSheet("padding: 4px; background-color: #f0f0f0; border: 1px solid #cccccc;")
        container_layout.addWidget(widget_placeholder)

        # Enable context menu for field history (ADR-027)
        container.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        container.customContextMenuRequested.connect(
            lambda pos, fid=field_def.id, fdef=field_def: self._show_field_context_menu(
                pos, fid, fdef, container
            )
        )

        return container

    def _set_initial_field_value(self, field_id: str, widget: IFieldWidget) -> None:
        """Set initial field value from project.

        Args:
            field_id: Field ID
            widget: Widget to set value on
        """
        if not self._viewmodel.current_project:
            return

        # TODO: Get field value from project DTO
        # For now, no initial value set
        pass

    def _on_field_value_changed(self, field_id: str, value: any) -> None:
        """Handle field value change.

        Args:
            field_id: Field ID that changed
            value: New field value
        """
        # Pass string ID directly (DTO-only MVVM compliance)
        self._viewmodel.update_field(field_id, value)

        # Re-validate after field change
        self._update_validation()

    def _update_validation(self) -> None:
        """Update validation state for all fields.

        Validates project and updates field widgets with validation errors.
        Updates status bar with validation summary.
        """
        if not self._viewmodel.current_project:
            return

        # Get validation result from viewmodel
        validation_result = self._viewmodel.validate_project()

        if validation_result.is_valid:
            self._status_bar.showMessage("No validation errors")
            self._status_bar.setStyleSheet("")
            # Clear errors from all widgets
            for widget in self._field_widgets.values():
                widget.set_validation_errors([])
        else:
            # Build error map by field ID
            error_map: dict[str, list[str]] = {}
            for error in validation_result.errors:
                if error.field_id:
                    if error.field_id not in error_map:
                        error_map[error.field_id] = []
                    error_map[error.field_id].append(error.message)

            # Update each widget with its errors
            for field_id, widget in self._field_widgets.items():
                errors = error_map.get(field_id, [])
                widget.set_validation_errors(errors)

            # Update status bar
            error_count = len(validation_result.errors)
            self._status_bar.showMessage(f"{error_count} validation error(s)")
            self._status_bar.setStyleSheet("background-color: #ffe6e6;")

    def _show_field_context_menu(
        self,
        pos,
        field_id: str,
        field_def: FieldDefinitionDTO,
        container: QWidget,
    ) -> None:
        """Show context menu for field container.

        ADR-027: Field History Storage
        Provides access to field history via right-click context menu.

        Args:
            pos: Position where menu was requested
            field_id: Field ID
            field_def: Field definition DTO
            container: Container widget that was right-clicked
        """
        # Create context menu
        menu = QMenu(container)

        # Add "View History" action
        history_action = menu.addAction("View History")
        history_action.triggered.connect(
            lambda: self._show_field_history(field_id, field_def)
        )

        # Show menu at cursor position
        menu.exec(container.mapToGlobal(pos))

    def _show_field_history(
        self, field_id: str, field_def: FieldDefinitionDTO
    ) -> None:
        """Show field history dialog for the specified field.

        ADR-027: Field History Storage

        Args:
            field_id: Field ID
            field_def: Field definition DTO
        """
        # Get field history from ViewModel
        history_result = self._viewmodel.get_field_history(field_id)

        # Build field path for dialog (format: "entity_id.field_id")
        field_path = f"{self._entity_definition.id}.{field_id}"

        # Show field history dialog
        FieldHistoryDialog.show_field_history(
            parent=self._root,
            field_label=field_def.label,
            field_path=field_path,
            history_result=history_result,
        )

        self._status_bar.showMessage(f"Field history viewed: {field_def.label}")

    def _on_unsaved_changes(self) -> None:
        """Handle unsaved changes state change."""
        if self._viewmodel.has_unsaved_changes:
            self._root.setWindowTitle(f"Doc Helper - {self._viewmodel.project_name} *")
            self._status_bar.showMessage("Unsaved changes")
        else:
            self._root.setWindowTitle(f"Doc Helper - {self._viewmodel.project_name}")
            self._status_bar.showMessage("Saved")

    def _on_project_name_changed(self) -> None:
        """Handle project name change.

        ADR-031: Undo History Persistence
        Resets undo restoration message flag when project changes.
        """
        suffix = " *" if self._viewmodel.has_unsaved_changes else ""
        self._root.setWindowTitle(f"Doc Helper - {self._viewmodel.project_name}{suffix}")

        # Reset undo restoration message flag for new project
        self._shown_undo_restore_message = False

    def _on_undo_state_changed(self) -> None:
        """Handle undo state change from ViewModel.

        ADR-031: Undo History Persistence
        Shows informative message when undo history is restored after project load.
        """
        self._update_undo_action()

        # Show undo restoration message once per project load (ADR-031)
        if self._viewmodel.can_undo and not self._shown_undo_restore_message:
            self._shown_undo_restore_message = True
            # Get undo description if available
            desc = ""
            if hasattr(self._viewmodel, '_history_adapter'):
                desc = self._viewmodel._history_adapter._undo_manager.undo_description
                if desc:
                    desc = f": {desc}"
            self._status_bar.showMessage(
                f"Undo history restored{desc} (persists across saves)"
            )

    def _on_redo_state_changed(self) -> None:
        """Handle redo state change from ViewModel."""
        self._update_redo_action()

    def _update_undo_action(self) -> None:
        """Update undo action enabled state based on ViewModel."""
        if self._undo_action:
            self._undo_action.setEnabled(self._viewmodel.can_undo)

    def _update_redo_action(self) -> None:
        """Update redo action enabled state based on ViewModel."""
        if self._redo_action:
            self._redo_action.setEnabled(self._viewmodel.can_redo)

    def _on_nav_back_state_changed(self) -> None:
        """Handle navigation back state change from ViewModel (U7)."""
        self._update_back_action()

    def _on_nav_forward_state_changed(self) -> None:
        """Handle navigation forward state change from ViewModel (U7)."""
        self._update_forward_action()

    def _update_back_action(self) -> None:
        """Update back action enabled state based on ViewModel (U7)."""
        if self._back_action:
            self._back_action.setEnabled(self._viewmodel.can_go_back)

    def _update_forward_action(self) -> None:
        """Update forward action enabled state based on ViewModel (U7)."""
        if self._forward_action:
            self._forward_action.setEnabled(self._viewmodel.can_go_forward)

    def _on_save(self) -> None:
        """Handle Save action.

        ADR-031: Undo History Persistence
        Undo history is preserved across saves (not cleared).
        """
        if self._viewmodel.save_project():
            # Check if undo history exists to provide informative message
            undo_count = 0
            if self._viewmodel.can_undo and hasattr(self._viewmodel, '_history_adapter'):
                # Count available undo actions (approximate from can_undo state)
                undo_count = 1 if self._viewmodel.can_undo else 0

            # Show status message with undo preservation info
            if undo_count > 0:
                self._status_bar.showMessage(
                    "Project saved - undo history preserved"
                )
            else:
                self._status_bar.showMessage("Project saved")

            QMessageBox.information(
                self._root,
                "Save",
                "Project saved successfully.\n\n"
                "Your undo history has been preserved and will be "
                "restored when you reopen this project.",
            )
        else:
            QMessageBox.critical(self._root, "Save Error", "Failed to save project")

    def _on_undo(self) -> None:
        """Handle Undo action (Ctrl+Z).

        Triggers undo operation through ViewModel and displays command description
        in status bar.
        """
        self._viewmodel.undo()
        # Show status message with command description if available
        if hasattr(self._viewmodel, '_history_adapter'):
            desc = self._viewmodel._history_adapter._undo_manager.undo_description
            self._status_bar.showMessage(f"Undo: {desc}" if desc else "Undo")
        else:
            self._status_bar.showMessage("Undo")

    def _on_redo(self) -> None:
        """Handle Redo action (Ctrl+Y).

        Triggers redo operation through ViewModel and displays command description
        in status bar.
        """
        self._viewmodel.redo()
        # Show status message with command description if available
        if hasattr(self._viewmodel, '_history_adapter'):
            desc = self._viewmodel._history_adapter._undo_manager.redo_description
            self._status_bar.showMessage(f"Redo: {desc}" if desc else "Redo")
        else:
            self._status_bar.showMessage("Redo")

    def _on_nav_back(self) -> None:
        """Handle Back navigation (Alt+Left) (U7).

        Navigates back in navigation history (entities, groups, fields).
        """
        if self._viewmodel.go_back():
            self._status_bar.showMessage("Navigated back")
        else:
            self._status_bar.showMessage("Cannot go back")

    def _on_nav_forward(self) -> None:
        """Handle Forward navigation (Alt+Right) (U7).

        Navigates forward in navigation history (entities, groups, fields).
        """
        if self._viewmodel.go_forward():
            self._status_bar.showMessage("Navigated forward")
        else:
            self._status_bar.showMessage("Cannot go forward")

    def _on_settings(self) -> None:
        """Handle Settings action.

        Opens settings dialog for user preferences (language, theme, etc.).
        """
        # Show settings dialog
        SettingsDialog.show_settings(self._root, self._translation_adapter)

        # Note: Language change takes effect immediately via translation adapter
        # The adapter emits signals and applies RTL/LTR layout direction
        # UI components that subscribe to language_changed will update automatically
        self._status_bar.showMessage("Settings updated")

    def _on_generate_document(self) -> None:
        """Handle Generate Document action.

        Note:
            This is a basic implementation for U3.
            Full document generation dialog is in Milestone U11.
        """
        # Validate before generation
        validation_result = self._viewmodel.validate_project()
        if not validation_result.is_valid:
            error_count = len(validation_result.errors)
            QMessageBox.warning(
                self._root,
                "Validation Errors",
                f"Cannot generate document. Please fix {error_count} validation error(s) first.",
            )
            return

        # Save project before generation
        if self._viewmodel.has_unsaved_changes:
            if not self._viewmodel.save_project():
                QMessageBox.critical(
                    self._root,
                    "Save Error",
                    "Failed to save project before generation.",
                )
                return

        # Placeholder for document generation
        # Full implementation with dialog in U11
        QMessageBox.information(
            self._root,
            "Generate Document",
            "Document generation dialog will be implemented in Milestone U11.",
        )
        self._status_bar.showMessage("Ready for document generation (U11)")

    def navigate_to_field(self, field_path: str) -> bool:
        """Navigate to a field by its path.

        ADR-026: Search Architecture
        Field path format: "entity_id.field_id"

        Args:
            field_path: Dot-separated path to the field (e.g., "project.site_location")

        Returns:
            True if navigation successful, False if field not found

        Side Effects:
            - Scrolls field container into view
            - Highlights field container briefly
        """
        # Parse field path (format: "entity_id.field_id")
        parts = field_path.split(".", 1)
        if len(parts) != 2:
            self._status_bar.showMessage(f"Invalid field path: {field_path}")
            return False

        entity_id, field_id = parts

        # Find field container by field ID
        container = self._field_containers.get(field_id)
        if not container or not self._scroll_area:
            self._status_bar.showMessage(f"Field not found: {field_id}")
            return False

        # Scroll to make container visible
        self._scroll_area.ensureWidgetVisible(container, 50, 50)  # 50px margins

        # Briefly highlight the field container for visual feedback
        # Store original style
        original_style = container.styleSheet()

        # Apply highlight
        container.setStyleSheet(
            "QWidget { background-color: #ffffcc; border: 2px solid #ff9900; }"
        )

        # Use a timer to remove highlight after 1 second
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: container.setStyleSheet(original_style))

        # Get field label for status message
        field_def = next(
            (f for f in self._entity_definition.fields if f.id == field_id), None
        )
        field_label = field_def.label if field_def else field_id

        # Show success message
        self._status_bar.showMessage(f"Navigated to: {field_label}")
        return True

    def _on_find_fields(self) -> None:
        """Handle Find Fields action (Ctrl+F).

        ADR-026: Search Architecture
        Opens search dialog for finding fields within the project.
        """

        def search_callback(search_term: str) -> list:
            """Execute search query."""
            return self._viewmodel.search_fields(search_term)

        def navigate_callback(field_path: str) -> None:
            """Navigate to field by path."""
            self.navigate_to_field(field_path)

        # Show non-modal search dialog
        SearchDialog.show_search(
            parent=self._root,
            search_callback=search_callback,
            navigate_callback=navigate_callback,
        )
        self._status_bar.showMessage("Search dialog opened")

    def _on_field_history(self) -> None:
        """Handle Field History menu action.

        ADR-027: Field History Storage
        Provides instructions for accessing field history via context menu.
        """
        QMessageBox.information(
            self._root,
            "Field History",
            "Field history is available via field context menus.\n\n"
            "To view a field's history:\n"
            "1. Right-click on any field in the form\n"
            "2. Select 'View History' from the context menu\n\n"
            "The history shows all changes made to that field, "
            "including timestamps and previous values.",
        )
        self._status_bar.showMessage("Field history instructions displayed")

    def _on_import_export(self) -> None:
        """Handle Import/Export action.

        ADR-039: Import/Export Data Format
        Opens import/export dialog for project data interchange.
        """

        def export_callback(output_path: str):
            """Execute export command via ViewModel."""
            return self._viewmodel.export_project(output_path)

        def import_callback(input_path: str):
            """Execute import command via ViewModel."""
            return self._viewmodel.import_project(input_path)

        # Show import/export dialog
        ImportExportDialog.show_import_export(
            parent=self._root,
            export_callback=export_callback,
            import_callback=import_callback,
            current_project_name=self._viewmodel.project_name,
        )
        self._status_bar.showMessage("Import/Export dialog opened")

    def _on_close(self) -> None:
        """Handle window close."""
        if self._viewmodel.has_unsaved_changes:
            reply = QMessageBox.question(
                self._root,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                if not self._viewmodel.save_project():
                    QMessageBox.critical(
                        self._root, "Save Error", "Failed to save project"
                    )
                    return

        self.dispose()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event.

        Args:
            event: Close event
        """
        self._on_close()
        event.accept()

    def dispose(self) -> None:
        """Dispose of the view."""
        # Unsubscribe from ViewModel
        if self._viewmodel:
            self._viewmodel.unsubscribe("has_unsaved_changes", self._on_unsaved_changes)
            self._viewmodel.unsubscribe("project_name", self._on_project_name_changed)
            self._viewmodel.unsubscribe("can_undo", self._on_undo_state_changed)
            self._viewmodel.unsubscribe("can_redo", self._on_redo_state_changed)
            self._viewmodel.unsubscribe("can_go_back", self._on_nav_back_state_changed)
            self._viewmodel.unsubscribe("can_go_forward", self._on_nav_forward_state_changed)

        # Dispose field widgets
        for widget in self._field_widgets.values():
            widget.dispose()
        self._field_widgets.clear()
        self._field_containers.clear()

        super().dispose()

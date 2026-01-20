"""Project editing view."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QFont, QKeySequence
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto import EntityDefinitionDTO, FieldDefinitionDTO
from doc_helper.domain.common.translation import ITranslationService
from doc_helper.domain.schema.schema_ids import FieldDefinitionId
from doc_helper.presentation.dialogs import SettingsDialog
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
        translation_service: ITranslationService,
        widget_factory: Optional[FieldWidgetFactory] = None,
    ) -> None:
        """Initialize project view.

        Args:
            parent: Parent widget
            viewmodel: ProjectViewModel instance
            entity_definition: Entity definition DTO (NOT domain object)
            translation_service: Translation service for i18n
            widget_factory: Factory for creating field widgets (default: new instance)
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._entity_definition = entity_definition
        self._translation_service = translation_service
        self._widget_factory = widget_factory or FieldWidgetFactory()

        # UI components
        self._fields_widget: Optional[QWidget] = None
        self._save_button: Optional[QPushButton] = None
        self._generate_button: Optional[QPushButton] = None
        self._status_bar: Optional[QStatusBar] = None

        # Undo/Redo actions (U6 Phase 5)
        self._undo_action: Optional[QAction] = None
        self._redo_action: Optional[QAction] = None

        # Field widgets mapped by field ID
        self._field_widgets: dict[str, IFieldWidget] = {}

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
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._fields_widget = QWidget()
        fields_layout = QVBoxLayout(self._fields_widget)
        scroll_area.setWidget(self._fields_widget)

        main_layout.addWidget(scroll_area, 1)  # Stretch factor 1

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

        # Initialize undo/redo action states
        self._update_undo_action()
        self._update_redo_action()

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

        close_action = QAction("Close", self._root)
        close_action.triggered.connect(self._on_close)
        file_menu.addAction(close_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        undo_action = QAction("Undo", self._root)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)
        self._undo_action = undo_action  # Store reference for state updates

        redo_action = QAction("Redo", self._root)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)
        self._redo_action = redo_action  # Store reference for state updates

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
        # Convert string ID to typed ID and update via viewmodel
        field_definition_id = FieldDefinitionId(field_id)
        self._viewmodel.update_field(field_definition_id, value)

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

    def _on_unsaved_changes(self) -> None:
        """Handle unsaved changes state change."""
        if self._viewmodel.has_unsaved_changes:
            self._root.setWindowTitle(f"Doc Helper - {self._viewmodel.project_name} *")
            self._status_bar.showMessage("Unsaved changes")
        else:
            self._root.setWindowTitle(f"Doc Helper - {self._viewmodel.project_name}")
            self._status_bar.showMessage("Saved")

    def _on_project_name_changed(self) -> None:
        """Handle project name change."""
        suffix = " *" if self._viewmodel.has_unsaved_changes else ""
        self._root.setWindowTitle(f"Doc Helper - {self._viewmodel.project_name}{suffix}")

    def _on_undo_state_changed(self) -> None:
        """Handle undo state change from ViewModel."""
        self._update_undo_action()

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

    def _on_save(self) -> None:
        """Handle Save action."""
        if self._viewmodel.save_project():
            self._status_bar.showMessage("Project saved")
            QMessageBox.information(
                self._root, "Save", "Project saved successfully"
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

    def _on_settings(self) -> None:
        """Handle Settings action.

        Opens settings dialog for user preferences (language, theme, etc.).
        """
        # Show settings dialog
        SettingsDialog.show_settings(self._root, self._translation_service)

        # Note: Language change takes effect immediately via translation service
        # UI components that subscribe to language changes will update automatically
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

        # Dispose field widgets
        for widget in self._field_widgets.values():
            widget.dispose()
        self._field_widgets.clear()

        super().dispose()

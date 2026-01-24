"""Schema Designer View (Phase 2 + Phase 6B + Phase 7).

UI component for viewing and creating schema definitions.
Displays entities, fields, validation rules, and relationships in a four-panel layout.

Phase 2 Step 1 Scope (COMPLETE):
- READ-ONLY display
- Entity list panel
- Field list panel for selected entity
- Validation rules panel for selected field
- Selection navigation between panels

Phase 2 Step 2 Scope (COMPLETE):
- "Add Entity" button and dialog
- "Add Field" button and dialog (when entity selected)
- Create new entities
- Add fields to existing entities

Phase 5: UX Polish & Onboarding (COMPLETE)
- Persistent header subtitle (dismissible per session)
- Empty state messaging for entity and field lists
- Tooltips for toolbar buttons
- First-launch welcome dialog (permanently dismissible)
- "What is this?" help access point
- Static help dialog
- Unsaved changes indicator (asterisk in title)
- Close warning for unsaved changes

Phase 6B: Relationship UI (ADR-022)
- Relationships panel showing entity relationships
- "Add Relationship" button and dialog
- ADD-ONLY semantics (no edit/delete)
- Clear messaging about immutability

Phase 7: Export UI
- "Export Schema" button in toolbar
- Export dialog with file picker
- Display export warnings

Phase SD-1: Import UI
- "Import Schema" button in toolbar
- Import dialog with file picker and options
- Display compatibility analysis
- Display import warnings/errors

NOT in current scope:
- No edit/delete buttons for entities/fields/relationships
- No formulas/controls/output mappings display
- No validation rule creation
"""

from typing import Optional

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from doc_helper.presentation.viewmodels.schema_designer_viewmodel import (
    SchemaDesignerViewModel,
)
from doc_helper.presentation.views.base_view import BaseView


class _CloseEventFilter(QObject):
    """Event filter to intercept dialog close events.

    Phase 5 Step 3: Used to warn about unsaved changes when closing.
    """

    def __init__(self, view: "SchemaDesignerView") -> None:
        """Initialize the event filter.

        Args:
            view: The SchemaDesignerView to check for unsaved changes
        """
        super().__init__()
        self._view = view

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter close events to warn about unsaved changes.

        Args:
            obj: Object that received the event
            event: The event

        Returns:
            True to filter the event (stop it), False to let it through
        """
        if event.type() == QEvent.Type.Close:
            if not self._view._confirm_close_if_unsaved():
                event.ignore()
                return True  # Block the close

        return False


class SchemaDesignerView(BaseView):
    """View for Schema Designer.

    Layout:
        ┌────────────────────────────────────────────────────────────────────┐
        │  Schema Designer - Create Entities & Fields                        │
        ├──────────────┬──────────────┬──────────────┬───────────────────────┤
        │ Entities     │ Fields       │ Validation   │ Relationships         │
        │              │              │ Rules        │ (ADD-ONLY)            │
        │ [Entity 1]   │ [Field 1]    │ [Rule 1]     │ [Entity→Entity]       │
        │ [Entity 2]   │ [Field 2]    │ [Rule 2]     │ [Entity→Entity]       │
        │ [Entity 3]   │ [Field 3]    │              │                       │
        │              │              │              │                       │
        └──────────────┴──────────────┴──────────────┴───────────────────────┘

    Interactions:
    - Click entity → display its fields and relationships
    - Click field → display its validation rules
    - Add Relationship → opens dialog (ADD-ONLY per ADR-022)

    Design:
    - Four-panel splitter layout (resizable)
    - CREATE operations for entities, fields, and relationships
    - Relationships are immutable once created (ADD-ONLY)
    - Clear visual selection feedback
    """

    def __init__(
        self,
        viewmodel: SchemaDesignerViewModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize Schema Designer View.

        Args:
            viewmodel: ViewModel managing presentation state
            parent: Parent widget (None for standalone dialog)
        """
        super().__init__(parent)
        self._viewmodel = viewmodel

        # UI Components (created in _build_ui)
        self._entity_list: Optional[QListWidget] = None
        self._field_list: Optional[QListWidget] = None
        self._validation_list: Optional[QListWidget] = None

        # Phase 6B: Relationship UI components
        self._relationship_list: Optional[QListWidget] = None
        self._relationship_info_label: Optional[QLabel] = None
        self._relationship_empty_label: Optional[QLabel] = None
        self._add_relationship_button: Optional[QPushButton] = None

        # Phase 5: UX Polish
        self._subtitle_frame: Optional[QFrame] = None
        self._subtitle_dismissed: bool = False
        self._entity_empty_label: Optional[QLabel] = None
        self._field_empty_label: Optional[QLabel] = None

        # Phase 5 Step 3: Unsaved changes tracking (view-level only)
        self._has_unsaved_changes: bool = False
        self._base_window_title: str = "Schema Designer - Create Entities & Fields"
        self._close_event_filter: Optional[_CloseEventFilter] = None

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Create dialog
        dialog = QDialog(self._parent)
        dialog.setWindowTitle("Schema Designer - Create Entities & Fields")
        dialog.resize(1200, 600)

        # Main layout
        main_layout = QVBoxLayout(dialog)

        # Title row with help link
        title_layout = QHBoxLayout()

        title_label = QLabel("Schema Designer - Create Entities & Fields")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # Phase SD-1: Import Schema button
        import_button = QPushButton("Import Schema")
        import_button.setStyleSheet("font-size: 9pt; padding: 5px 15px;")
        import_button.clicked.connect(self._on_import_schema_clicked)
        import_button.setToolTip(
            "Import schema from JSON file.\n"
            "Replaces all entities, fields, constraints, and relationships."
        )
        title_layout.addWidget(import_button)

        # Phase 7: Export Schema button
        export_button = QPushButton("Export Schema")
        export_button.setStyleSheet("font-size: 9pt; padding: 5px 15px;")
        export_button.clicked.connect(self._on_export_schema_clicked)
        export_button.setToolTip(
            "Export schema to JSON file.\n"
            "Includes entities, fields, constraints, and relationships."
        )
        title_layout.addWidget(export_button)

        # Phase 5 Step 2: "What is this?" help access point
        help_link = QPushButton("What is this?")
        help_link.setFlat(True)
        help_link.setCursor(Qt.CursorShape.PointingHandCursor)
        help_link.setStyleSheet(
            "QPushButton { "
            "color: #4299e1; "
            "text-decoration: underline; "
            "border: none; "
            "padding: 10px; "
            "font-size: 9pt; "
            "} "
            "QPushButton:hover { "
            "color: #2b6cb0; "
            "}"
        )
        help_link.setToolTip("Learn more about Schema Designer")
        help_link.clicked.connect(self._on_help_clicked)
        title_layout.addWidget(help_link)

        main_layout.addLayout(title_layout)

        # Phase 5: Persistent header subtitle (dismissible per session)
        self._subtitle_frame = self._create_subtitle_frame()
        main_layout.addWidget(self._subtitle_frame)

        # Info label
        info_label = QLabel(
            "Select an entity to view its fields, "
            "then select a field to view its validation rules."
        )
        info_label.setStyleSheet("color: gray; padding: 5px;")
        main_layout.addWidget(info_label)

        # Create four-panel splitter (Phase 6B: added relationships)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel 1: Entity list
        entity_panel = self._create_entity_panel()
        splitter.addWidget(entity_panel)

        # Panel 2: Field list
        field_panel = self._create_field_panel()
        splitter.addWidget(field_panel)

        # Panel 3: Validation rules
        validation_panel = self._create_validation_panel()
        splitter.addWidget(validation_panel)

        # Panel 4: Relationships (Phase 6B - ADR-022)
        relationship_panel = self._create_relationship_panel()
        splitter.addWidget(relationship_panel)

        # Set initial splitter sizes (equal distribution)
        splitter.setSizes([300, 300, 300, 300])

        main_layout.addWidget(splitter)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self._on_close_requested)
        close_button.setToolTip("Close the Schema Designer")
        button_layout.addWidget(close_button)

        main_layout.addLayout(button_layout)

        self._root = dialog

        # Phase 5 Step 3: Install event filter to catch window close (X button)
        self._close_event_filter = _CloseEventFilter(self)
        dialog.installEventFilter(self._close_event_filter)

        # Subscribe to ViewModel changes
        self._viewmodel.subscribe("entities", self._on_entities_changed)
        self._viewmodel.subscribe("fields", self._on_fields_changed)
        self._viewmodel.subscribe("validation_rules", self._on_validation_rules_changed)
        self._viewmodel.subscribe("error_message", self._on_error_changed)
        # Phase 6B: Subscribe to relationships
        self._viewmodel.subscribe("entity_relationships", self._on_relationships_changed)

        # Load entities
        self._load_entities()

        # Phase 5 Step 2: Show welcome dialog on first launch
        self._show_welcome_if_first_launch()

    def _show_welcome_if_first_launch(self) -> None:
        """Show the welcome dialog if this is the first launch.

        Uses QSettings to persist the "don't show again" preference.
        Phase 5 Step 2: Onboarding only, no business logic.
        """
        from doc_helper.presentation.dialogs.schema_designer_welcome_dialog import (
            SchemaDesignerWelcomeDialog,
        )

        SchemaDesignerWelcomeDialog.show_if_first_launch(self._root)

    def _create_entity_panel(self) -> QWidget:
        """Create the entity list panel.

        Returns:
            Widget containing entity list
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Panel title with Add button
        header_layout = QHBoxLayout()
        title = QLabel("Entities")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Add Entity button (Phase 2 Step 2)
        add_entity_button = QPushButton("+ Add Entity")
        add_entity_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        add_entity_button.clicked.connect(self._on_add_entity_clicked)
        # Phase 5: Add tooltip
        add_entity_button.setToolTip(
            "Create a new entity definition.\n"
            "Entities are containers for field definitions\n"
            "(e.g., 'Project Info', 'Boreholes', 'Samples')."
        )
        header_layout.addWidget(add_entity_button)

        layout.addLayout(header_layout)

        # Phase 5: Empty state label (shown when no entities)
        self._entity_empty_label = QLabel(
            "No entities defined.\n\n"
            "Click '+ Add Entity' to create your first entity.\n"
            "Entities define the structure of your schema."
        )
        self._entity_empty_label.setStyleSheet(
            "color: #718096; "
            "font-style: italic; "
            "padding: 20px; "
            "background-color: #f7fafc; "
            "border: 1px dashed #cbd5e0; "
            "border-radius: 4px;"
        )
        self._entity_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._entity_empty_label.setWordWrap(True)
        layout.addWidget(self._entity_empty_label)

        # Entity list
        self._entity_list = QListWidget()
        self._entity_list.currentItemChanged.connect(self._on_entity_selected)
        layout.addWidget(self._entity_list)

        return panel

    def _create_field_panel(self) -> QWidget:
        """Create the field list panel.

        Returns:
            Widget containing field list
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Panel title with Add button
        header_layout = QHBoxLayout()
        title = QLabel("Fields")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Add Field button (Phase 2 Step 2)
        # Enabled only when entity is selected
        self._add_field_button = QPushButton("+ Add Field")
        self._add_field_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        self._add_field_button.clicked.connect(self._on_add_field_clicked)
        self._add_field_button.setEnabled(False)  # Disabled until entity selected
        # Phase 5: Add tooltip
        self._add_field_button.setToolTip(
            "Add a new field to the selected entity.\n"
            "Fields define the data structure\n"
            "(e.g., 'Project Name', 'Depth', 'Sample Date')."
        )
        header_layout.addWidget(self._add_field_button)

        layout.addLayout(header_layout)

        # Info label (shows when no entity selected)
        self._field_info_label = QLabel("Select an entity to view its fields")
        self._field_info_label.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
        self._field_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._field_info_label)

        # Phase 5: Empty state label (shown when entity selected but has no fields)
        self._field_empty_label = QLabel(
            "This entity has no fields.\n\n"
            "Click '+ Add Field' to define fields for this entity."
        )
        self._field_empty_label.setStyleSheet(
            "color: #718096; "
            "font-style: italic; "
            "padding: 20px; "
            "background-color: #f7fafc; "
            "border: 1px dashed #cbd5e0; "
            "border-radius: 4px;"
        )
        self._field_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._field_empty_label.setWordWrap(True)
        self._field_empty_label.setVisible(False)
        layout.addWidget(self._field_empty_label)

        # Field list
        self._field_list = QListWidget()
        self._field_list.currentItemChanged.connect(self._on_field_selected)
        self._field_list.setVisible(False)  # Hidden until entity selected
        layout.addWidget(self._field_list)

        return panel

    def _create_validation_panel(self) -> QWidget:
        """Create the validation rules panel.

        Returns:
            Widget containing validation rules list
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Panel title
        title = QLabel("Validation Rules")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        layout.addWidget(title)

        # Info label (shows when no field selected)
        info = QLabel("Select a field to view its validation rules")
        info.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        # Validation rules list
        self._validation_list = QListWidget()
        self._validation_list.setVisible(False)  # Hidden until field selected
        layout.addWidget(self._validation_list)

        return panel

    def _create_relationship_panel(self) -> QWidget:
        """Create the relationships panel (Phase 6B - ADR-022).

        Relationships are ADD-ONLY per ADR-022:
        - Can view relationships for selected entity
        - Can add new relationships
        - CANNOT edit or delete relationships

        Returns:
            Widget containing relationships list and add button
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Panel title with Add button
        header_layout = QHBoxLayout()
        title = QLabel("Relationships")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Add Relationship button
        self._add_relationship_button = QPushButton("+ Add Relationship")
        self._add_relationship_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        self._add_relationship_button.clicked.connect(self._on_add_relationship_clicked)
        self._add_relationship_button.setToolTip(
            "Define a new relationship between entities.\n"
            "Relationships describe how entities are connected\n"
            "(e.g., 'Project contains Boreholes').\n\n"
            "Note: Relationships are immutable once created."
        )
        header_layout.addWidget(self._add_relationship_button)

        layout.addLayout(header_layout)

        # ADD-ONLY notice
        notice = QLabel("Relationships are immutable (ADD-ONLY)")
        notice.setStyleSheet(
            "color: #b45309; "
            "font-size: 8pt; "
            "font-style: italic; "
            "padding: 2px 5px;"
        )
        layout.addWidget(notice)

        # Info label (shows when no entity selected)
        self._relationship_info_label = QLabel(
            "Select an entity to view its relationships"
        )
        self._relationship_info_label.setStyleSheet(
            "color: gray; font-style: italic; padding: 10px;"
        )
        self._relationship_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._relationship_info_label)

        # Empty state label (shown when entity selected but has no relationships)
        self._relationship_empty_label = QLabel(
            "No relationships defined for this entity.\n\n"
            "Click '+ Add Relationship' to define\n"
            "how this entity connects to others."
        )
        self._relationship_empty_label.setStyleSheet(
            "color: #718096; "
            "font-style: italic; "
            "padding: 20px; "
            "background-color: #f7fafc; "
            "border: 1px dashed #cbd5e0; "
            "border-radius: 4px;"
        )
        self._relationship_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._relationship_empty_label.setWordWrap(True)
        self._relationship_empty_label.setVisible(False)
        layout.addWidget(self._relationship_empty_label)

        # Relationship list
        self._relationship_list = QListWidget()
        self._relationship_list.setVisible(False)  # Hidden until entity selected
        layout.addWidget(self._relationship_list)

        return panel

    # -------------------------------------------------------------------------
    # Phase 5: UX Components
    # -------------------------------------------------------------------------

    def _create_subtitle_frame(self) -> QFrame:
        """Create the persistent subtitle frame (dismissible per session).

        Explains:
        - Schema Designer is a TOOL AppType
        - Edits meta-schema, not project data
        - Manual export & deployment required

        Returns:
            QFrame containing subtitle with dismiss button
        """
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { "
            "background-color: #f0f4f8; "
            "border: 1px solid #d0d8e0; "
            "border-radius: 4px; "
            "margin: 5px 10px; "
            "}"
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 8, 8)

        # Subtitle text explaining the tool
        subtitle_text = QLabel(
            "This is a TOOL for editing meta-schema (entity and field definitions), "
            "not project data. After editing, export your schema and deploy it manually "
            "to the target app type folder."
        )
        subtitle_text.setWordWrap(True)
        subtitle_text.setStyleSheet(
            "color: #4a5568; "
            "font-size: 9pt; "
            "border: none; "
            "background: transparent;"
        )
        layout.addWidget(subtitle_text, 1)

        # Dismiss button (X)
        dismiss_button = QPushButton("×")
        dismiss_button.setFixedSize(20, 20)
        dismiss_button.setStyleSheet(
            "QPushButton { "
            "border: none; "
            "background: transparent; "
            "color: #718096; "
            "font-size: 14pt; "
            "font-weight: bold; "
            "} "
            "QPushButton:hover { "
            "color: #4a5568; "
            "background-color: #e2e8f0; "
            "border-radius: 10px; "
            "}"
        )
        dismiss_button.setToolTip("Dismiss this message for this session")
        dismiss_button.clicked.connect(self._on_subtitle_dismissed)
        layout.addWidget(dismiss_button)

        return frame

    def _on_subtitle_dismissed(self) -> None:
        """Handle subtitle dismiss button click."""
        self._subtitle_dismissed = True
        if self._subtitle_frame:
            self._subtitle_frame.setVisible(False)

    def _set_unsaved_changes(self, has_changes: bool) -> None:
        """Set the unsaved changes state and update window title.

        Phase 5 Step 3: UX indicator only, no business logic.
        Shows asterisk (*) in window title when there are unsaved changes.

        Args:
            has_changes: True if there are unsaved changes
        """
        self._has_unsaved_changes = has_changes

        if self._root:
            if has_changes:
                self._root.setWindowTitle(f"* {self._base_window_title}")
            else:
                self._root.setWindowTitle(self._base_window_title)

    def _on_help_clicked(self) -> None:
        """Handle 'What is this?' help link click.

        Opens the static help dialog explaining Schema Designer.
        Phase 5 Step 2: Navigation only, no business logic.
        """
        from doc_helper.presentation.dialogs.schema_designer_help_dialog import (
            SchemaDesignerHelpDialog,
        )

        SchemaDesignerHelpDialog.show_help(self._root)

    def _on_close_requested(self) -> None:
        """Handle close button click.

        Phase 5 Step 3: Warn if there are unsaved changes before closing.
        """
        if self._confirm_close_if_unsaved():
            self._root.close()

    def _confirm_close_if_unsaved(self) -> bool:
        """Check for unsaved changes and confirm close if needed.

        Phase 5 Step 3: UX warning only, does not prevent closing.

        Returns:
            True if user confirms close or no unsaved changes, False to cancel
        """
        if not self._has_unsaved_changes:
            return True

        result = QMessageBox.warning(
            self._root,
            "Unsaved Changes",
            "You have unsaved changes.\n\n"
            "Changes made in Schema Designer are not automatically saved. "
            "If you close now, your changes will be lost.\n\n"
            "Do you want to close anyway?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        return result == QMessageBox.StandardButton.Yes

    # -------------------------------------------------------------------------
    # Event Handlers (User Interactions)
    # -------------------------------------------------------------------------

    def _on_entity_selected(
        self,
        current: Optional[QListWidgetItem],
        previous: Optional[QListWidgetItem],
    ) -> None:
        """Handle entity selection.

        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if current:
            entity_id = current.data(Qt.ItemDataRole.UserRole)
            self._viewmodel.select_entity(entity_id)

    def _on_field_selected(
        self,
        current: Optional[QListWidgetItem],
        previous: Optional[QListWidgetItem],
    ) -> None:
        """Handle field selection.

        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if current:
            field_id = current.data(Qt.ItemDataRole.UserRole)
            self._viewmodel.select_field(field_id)

    # -------------------------------------------------------------------------
    # ViewModel Change Handlers
    # -------------------------------------------------------------------------

    def _on_entities_changed(self) -> None:
        """Handle entities list change."""
        self._entity_list.clear()

        entities = self._viewmodel.entities

        # Phase 5: Show/hide empty state
        has_entities = len(entities) > 0
        if self._entity_empty_label:
            self._entity_empty_label.setVisible(not has_entities)
        self._entity_list.setVisible(has_entities)

        for entity_dto in entities:
            # Create list item
            item = QListWidgetItem(entity_dto.name)
            item.setData(Qt.ItemDataRole.UserRole, entity_dto.id)

            # Add badge for root entity
            if entity_dto.is_root_entity:
                item.setText(f"{entity_dto.name} (Root)")

            # Add field count
            item.setToolTip(
                f"{entity_dto.name}\n"
                f"Fields: {entity_dto.field_count}\n"
                f"{'Root entity' if entity_dto.is_root_entity else 'Child entity'}"
            )

            self._entity_list.addItem(item)

    def _on_fields_changed(self) -> None:
        """Handle fields list change."""
        self._field_list.clear()

        fields = self._viewmodel.fields
        entity_selected = self._viewmodel.selected_entity_id is not None

        # Phase 5: Manage visibility of info label, empty state, and field list
        if not entity_selected:
            # No entity selected - show info label
            if hasattr(self, '_field_info_label'):
                self._field_info_label.setVisible(True)
            if self._field_empty_label:
                self._field_empty_label.setVisible(False)
            self._field_list.setVisible(False)
            if hasattr(self, '_add_field_button'):
                self._add_field_button.setEnabled(False)
            return

        # Entity is selected - hide info label
        if hasattr(self, '_field_info_label'):
            self._field_info_label.setVisible(False)

        if not fields:
            # Entity selected but no fields - show empty state
            if self._field_empty_label:
                self._field_empty_label.setVisible(True)
            self._field_list.setVisible(False)
            # Enable Add Field button since entity is selected
            if hasattr(self, '_add_field_button'):
                self._add_field_button.setEnabled(True)
            return

        # Entity selected and has fields - show field list
        if self._field_empty_label:
            self._field_empty_label.setVisible(False)
        self._field_list.setVisible(True)
        if hasattr(self, '_add_field_button'):
            self._add_field_button.setEnabled(True)

        for field_dto in fields:
            # Create list item
            item_text = f"{field_dto.label} ({field_dto.field_type})"
            if field_dto.required:
                item_text += " *"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, field_dto.id)

            # Add tooltip with field details
            tooltip_parts = [
                f"Label: {field_dto.label}",
                f"Type: {field_dto.field_type}",
                f"Required: {'Yes' if field_dto.required else 'No'}",
            ]

            if field_dto.help_text:
                tooltip_parts.append(f"Help: {field_dto.help_text}")

            if field_dto.default_value:
                tooltip_parts.append(f"Default: {field_dto.default_value}")

            if field_dto.is_calculated:
                tooltip_parts.append("Calculated field")

            item.setToolTip("\n".join(tooltip_parts))

            self._field_list.addItem(item)

    def _on_validation_rules_changed(self) -> None:
        """Handle validation rules list change."""
        self._validation_list.clear()

        rules = self._viewmodel.validation_rules
        if not rules:
            self._validation_list.setVisible(False)
            return

        self._validation_list.setVisible(True)

        for rule_text in rules:
            item = QListWidgetItem(rule_text)
            self._validation_list.addItem(item)

        # Show message if no rules
        if not rules:
            item = QListWidgetItem("No validation rules defined")
            item.setForeground(Qt.GlobalColor.gray)
            self._validation_list.addItem(item)

    def _on_error_changed(self) -> None:
        """Handle error message change."""
        error = self._viewmodel.error_message
        if error:
            QMessageBox.critical(self._root, "Error Loading Schema", error)

    def _on_relationships_changed(self) -> None:
        """Handle relationships list change (Phase 6B)."""
        if not self._relationship_list:
            return

        self._relationship_list.clear()

        relationships = self._viewmodel.entity_relationships
        entity_selected = self._viewmodel.selected_entity_id is not None

        # Manage visibility of info label, empty state, and list
        if not entity_selected:
            # No entity selected - show info label
            if self._relationship_info_label:
                self._relationship_info_label.setVisible(True)
            if self._relationship_empty_label:
                self._relationship_empty_label.setVisible(False)
            self._relationship_list.setVisible(False)
            return

        # Entity is selected - hide info label
        if self._relationship_info_label:
            self._relationship_info_label.setVisible(False)

        if not relationships:
            # Entity selected but no relationships - show empty state
            if self._relationship_empty_label:
                self._relationship_empty_label.setVisible(True)
            self._relationship_list.setVisible(False)
            return

        # Entity selected and has relationships - show list
        if self._relationship_empty_label:
            self._relationship_empty_label.setVisible(False)
        self._relationship_list.setVisible(True)

        selected_entity = self._viewmodel.selected_entity_id

        for rel_dto in relationships:
            # Determine direction relative to selected entity
            if rel_dto.source_entity_id == selected_entity:
                # Outgoing relationship
                arrow = "→"
                other_entity = rel_dto.target_entity_id
                direction = "outgoing"
            else:
                # Incoming relationship
                arrow = "←"
                other_entity = rel_dto.source_entity_id
                direction = "incoming"

            # Create list item text
            item_text = f"{rel_dto.relationship_type} {arrow} {other_entity}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, rel_dto.id)

            # Add tooltip with relationship details
            tooltip_parts = [
                f"ID: {rel_dto.id}",
                f"Type: {rel_dto.relationship_type}",
                f"Source: {rel_dto.source_entity_id}",
                f"Target: {rel_dto.target_entity_id}",
                f"Direction: {direction}",
                "",
                "Relationships are immutable (ADD-ONLY)",
            ]

            if rel_dto.name_key:
                tooltip_parts.insert(4, f"Name Key: {rel_dto.name_key}")

            if rel_dto.description_key:
                tooltip_parts.insert(5, f"Description Key: {rel_dto.description_key}")

            item.setToolTip("\n".join(tooltip_parts))

            self._relationship_list.addItem(item)

    # -------------------------------------------------------------------------
    # Commands
    # -------------------------------------------------------------------------

    def _load_entities(self) -> None:
        """Load entities from repository."""
        success = self._viewmodel.load_entities()
        if not success:
            QMessageBox.critical(
                self._root,
                "Error",
                "Failed to load schema entities. Check error message.",
            )

    # -------------------------------------------------------------------------
    # Phase 2 Step 2: Creation Operations
    # -------------------------------------------------------------------------

    def _on_add_entity_clicked(self) -> None:
        """Handle Add Entity button click."""
        from doc_helper.presentation.dialogs.add_entity_dialog import AddEntityDialog

        dialog = AddEntityDialog(parent=self._root)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entity_data = dialog.get_entity_data()
            if not entity_data:
                return

            # Create entity via ViewModel
            result = self._viewmodel.create_entity(
                entity_id=entity_data["entity_id"],
                name_key=entity_data["name_key"],
                description_key=entity_data["description_key"],
                is_root_entity=entity_data["is_root_entity"],
            )

            if result.is_success():
                # Phase 5 Step 3: Mark as having unsaved changes
                self._set_unsaved_changes(True)

                QMessageBox.information(
                    self._root,
                    "Success",
                    f"Entity '{entity_data['entity_id']}' created successfully!",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Creating Entity",
                    f"Failed to create entity: {result.error}",
                )

    def _on_add_field_clicked(self) -> None:
        """Handle Add Field button click."""
        # Get currently selected entity
        if not self._viewmodel.selected_entity_id:
            QMessageBox.warning(
                self._root,
                "No Entity Selected",
                "Please select an entity first before adding a field.",
            )
            return

        # Get entity name for dialog title
        entity_name = "Unknown"
        for entity_dto in self._viewmodel.entities:
            if entity_dto.id == self._viewmodel.selected_entity_id:
                entity_name = entity_dto.name
                break

        from doc_helper.presentation.dialogs.add_field_dialog import AddFieldDialog

        dialog = AddFieldDialog(entity_name=entity_name, parent=self._root)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            field_data = dialog.get_field_data()
            if not field_data:
                return

            # Add field via ViewModel
            result = self._viewmodel.add_field(
                entity_id=self._viewmodel.selected_entity_id,
                field_id=field_data["field_id"],
                field_type=field_data["field_type"],
                label_key=field_data["label_key"],
                help_text_key=field_data["help_text_key"],
                required=field_data["required"],
                default_value=field_data["default_value"],
            )

            if result.is_success():
                # Phase 5 Step 3: Mark as having unsaved changes
                self._set_unsaved_changes(True)

                QMessageBox.information(
                    self._root,
                    "Success",
                    f"Field '{field_data['field_id']}' added to '{entity_name}' successfully!",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Adding Field",
                    f"Failed to add field: {result.error}",
                )

    # -------------------------------------------------------------------------
    # Phase 6B: Relationship Operations (ADD-ONLY per ADR-022)
    # -------------------------------------------------------------------------

    def _on_add_relationship_clicked(self) -> None:
        """Handle Add Relationship button click (Phase 6B).

        Opens dialog to create a new relationship.
        Relationships are ADD-ONLY per ADR-022.
        """
        # Get list of entities for dropdown
        entities = self._viewmodel.get_entity_list_for_relationship()

        if len(entities) < 2:
            QMessageBox.warning(
                self._root,
                "Cannot Add Relationship",
                "At least two entities are required to create a relationship.\n"
                "Please add more entities first.",
            )
            return

        from doc_helper.presentation.dialogs.add_relationship_dialog import (
            AddRelationshipDialog,
        )

        dialog = AddRelationshipDialog(entities=entities, parent=self._root)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rel_data = dialog.get_relationship_data()
            if not rel_data:
                return

            # Create relationship via ViewModel
            result = self._viewmodel.create_relationship(
                relationship_id=rel_data["relationship_id"],
                source_entity_id=rel_data["source_entity_id"],
                target_entity_id=rel_data["target_entity_id"],
                relationship_type=rel_data["relationship_type"],
                name_key=rel_data["name_key"],
                description_key=rel_data["description_key"],
                inverse_name_key=rel_data["inverse_name_key"],
            )

            if result.is_success():
                # Mark as having unsaved changes
                self._set_unsaved_changes(True)

                QMessageBox.information(
                    self._root,
                    "Relationship Created",
                    f"Relationship '{rel_data['relationship_id']}' created successfully!\n\n"
                    f"{rel_data['source_entity_id']} {rel_data['relationship_type']} "
                    f"{rel_data['target_entity_id']}\n\n"
                    "Note: Relationships are immutable and cannot be edited or deleted.",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Creating Relationship",
                    f"Failed to create relationship:\n\n{result.error}",
                )

    # -------------------------------------------------------------------------
    # Phase SD-1: Import Operations
    # -------------------------------------------------------------------------

    def _on_import_schema_clicked(self) -> None:
        """Handle Import Schema button click (Phase SD-1).

        Opens dialog to import schema from JSON file.
        Displays warnings and errors returned by ImportSchemaCommand.
        """
        from doc_helper.presentation.dialogs.import_schema_dialog import (
            ImportSchemaDialog,
        )

        dialog = ImportSchemaDialog(parent=self._root)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            import_params = dialog.get_import_params()
            if not import_params:
                return

            # Import schema via ViewModel
            result = self._viewmodel.import_schema(
                file_path=import_params["file_path"],
                enforcement_policy=import_params["enforcement_policy"],
                identical_action=import_params["identical_action"],
                force=import_params["force"],
            )

            if result.success:
                # Build success message
                if result.was_skipped:
                    QMessageBox.information(
                        self._root,
                        "Import Skipped",
                        "Schema was not imported because it is identical to the existing schema.",
                    )
                else:
                    message = "Schema imported successfully!\n\n"
                    message += f"Entities: {result.entity_count}\n"
                    message += f"Fields: {result.field_count}\n"
                    message += f"Relationships: {result.relationship_count}"

                    # Include warning count if any
                    if result.warnings:
                        warning_count = len(result.warnings)
                        message += f"\n\nWarnings: {warning_count}"

                        # Show first few warnings in message
                        for warning in result.warnings[:5]:
                            message += f"\n- [{warning.category}] {warning.message}"

                        if warning_count > 5:
                            message += f"\n... and {warning_count - 5} more warnings"

                    QMessageBox.information(
                        self._root,
                        "Import Successful",
                        message,
                    )

                    # Mark as having unsaved changes (schema was modified)
                    self._set_unsaved_changes(True)
            else:
                # Build error message
                message = "Failed to import schema:\n\n"

                if result.error:
                    message += f"{result.error}\n"

                if result.validation_errors:
                    message += f"\nValidation Errors ({len(result.validation_errors)}):"
                    for error in result.validation_errors[:5]:
                        location = f" at {error.location}" if error.location else ""
                        message += f"\n- [{error.category}]{location}: {error.message}"

                    if len(result.validation_errors) > 5:
                        message += f"\n... and {len(result.validation_errors) - 5} more errors"

                QMessageBox.critical(
                    self._root,
                    "Import Failed",
                    message,
                )

    # -------------------------------------------------------------------------
    # Phase 7: Export Operations
    # -------------------------------------------------------------------------

    def _on_export_schema_clicked(self) -> None:
        """Handle Export Schema button click (Phase 7).

        Opens dialog to export schema to JSON file.
        Displays warnings returned by ExportSchemaCommand.
        """
        from doc_helper.presentation.dialogs.export_schema_dialog import (
            ExportSchemaDialog,
        )

        dialog = ExportSchemaDialog(parent=self._root)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            export_data = dialog.get_export_data()
            if not export_data:
                return

            # Export schema via ViewModel
            success, export_result, error = self._viewmodel.export_schema(
                schema_id=export_data["schema_id"],
                file_path=export_data["file_path"],
                version=export_data["version"],
            )

            if success and export_result:
                # Build success message
                file_path = export_data["file_path"]
                message = f"Schema exported successfully!\n\nFile: {file_path}"

                # Include warning count if any
                if export_result.warnings:
                    warning_count = len(export_result.warnings)
                    message += f"\n\nWarnings: {warning_count}"

                    # Show first few warnings in message
                    for i, warning in enumerate(export_result.warnings[:5]):
                        message += f"\n- {warning.message}"

                    if warning_count > 5:
                        message += f"\n... and {warning_count - 5} more warnings"

                QMessageBox.information(
                    self._root,
                    "Export Successful",
                    message,
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Export Failed",
                    f"Failed to export schema:\n\n{error}",
                )

    def dispose(self) -> None:
        """Clean up resources."""
        # Unsubscribe from ViewModel
        if self._viewmodel:
            self._viewmodel.dispose()

        super().dispose()

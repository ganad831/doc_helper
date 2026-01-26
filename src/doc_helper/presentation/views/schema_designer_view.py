"""Schema Designer View (Phase 2 + Phase 6B + Phase 7 + Phase F-1 + Phase F-9 + Phase F-12 + Phase F-13).

UI component for viewing and creating schema definitions.
Displays entities, fields, validation rules, relationships, formula editor,
and control rules preview in a six-panel layout.

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

Phase SD-2: Add Constraint UI
- "Add Constraint" button in validation rules panel
- Add constraint dialog with type selector
- Support: Required, MinValue, MaxValue, MinLength, MaxLength
- Refresh validation rules after adding

Phase SD-3: Entity Edit/Delete UI
- Edit button to update entity metadata
- Delete button with confirmation dialog
- Dependency warning before delete

Phase SD-4: Field Edit/Delete UI
- Edit button to update field metadata
- Delete button with confirmation dialog
- Dependency warning before delete (formulas, controls, lookup references)

Phase F-1: Formula Editor UI (Read-Only, Design-Time)
- Formula Editor panel (5th panel)
- Live syntax validation
- Field reference validation against schema
- Inferred result type display
- Error/warning display
- NO formula execution
- NO schema mutation from formula editor

Phase F-9: Control Rules Preview UI (UI-Only, In-Memory)
- Control Rules Preview panel (6th panel)
- Toggle preview mode ON/OFF
- Enter temporary field values for preview
- Define control rules (VISIBILITY, ENABLED, REQUIRED)
- Evaluate rules via use-cases
- Apply rule effects to UI only (no persistence)
- Display blocked rules with reasons
- NO schema mutation
- NO persistence

Phase F-12: Control Rules UI (Persisted, Design-Time)
- Control Rules section in validation panel
- Add/Edit/Delete persisted control rules
- Display rule type, target field, formula
- Route all operations through SchemaDesignerViewModel
- Design-time only (no runtime enforcement)
- NO business logic in UI
- NO validation logic in UI
- NO formula execution in UI

Phase F-13: Output Mapping Formula UI (Persisted, Design-Time)
- Output Mappings section in validation panel
- Add/Edit/Delete persisted output mappings
- Display target type (TEXT/NUMBER/BOOLEAN), formula
- Route all operations through SchemaDesignerViewModel
- Design-time only (no runtime execution)
- NO business logic in UI
- NO validation logic in UI
- NO formula execution in UI

NOT in current scope:
- No edit/delete buttons for relationships
"""

from typing import Optional

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto.control_rule_dto import ControlRuleType
from doc_helper.presentation.viewmodels.schema_designer_viewmodel import (
    SchemaDesignerViewModel,
)
from doc_helper.presentation.views.base_view import BaseView
from doc_helper.presentation.widgets.formula_editor_widget import FormulaEditorWidget


class _CloseEventFilter(QObject):
    """Event filter to intercept dialog close events.

    Phase 5 Step 3: Used to confirm close of Schema Designer.
    """

    def __init__(self, view: "SchemaDesignerView") -> None:
        """Initialize the event filter.

        Args:
            view: The SchemaDesignerView to confirm close
        """
        super().__init__()
        self._view = view

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter close events to confirm close.

        Args:
            obj: Object that received the event
            event: The event

        Returns:
            True to filter the event (stop it), False to let it through
        """
        if event.type() == QEvent.Type.Close:
            if not self._view._confirm_close():
                event.ignore()
                return True  # Block the close

        return False


class SchemaDesignerView(BaseView):
    """View for Schema Designer.

    Layout:
        ┌────────────────────────────────────────────────────────────────────────────────────────────┐
        │  Schema Designer - Create Entities & Fields                                                 │
        ├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┬──────────────────┤
        │ Entities    │ Fields      │ Validation  │ Relation-   │ Formula Editor  │ Control Rules    │
        │             │             │ Rules       │ ships       │ (Phase F-1)     │ Preview (F-9)    │
        │ [Entity 1]  │ [Field 1]   │ [Rule 1]    │ [Rel 1]     │ [Formula Input] │ [x] Preview Mode │
        │ [Entity 2]  │ [Field 2]   │ [Rule 2]    │ [Rel 2]     │ [Type: NUMBER]  │ [Field Values]   │
        │ [Entity 3]  │ [Field 3]   │             │             │ [Errors/Warn]   │ [Rules List]     │
        └─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┴──────────────────┘

    Interactions:
    - Click entity → display its fields and relationships
    - Click field → display its validation rules and formula editor
    - Add Relationship → opens dialog (ADD-ONLY per ADR-022)
    - Formula Editor → validates formula, shows type inference (READ-ONLY)
    - Control Rules Preview → test control rules with temporary values (UI-ONLY)

    Design:
    - Six-panel splitter layout (resizable)
    - CREATE operations for entities, fields, and relationships
    - Relationships are immutable once created (ADD-ONLY)
    - Formula Editor is READ-ONLY with respect to schema
    - Control Rules Preview is UI-ONLY (no persistence)
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

        # Phase SD-2: Add Constraint UI
        self._add_constraint_button: Optional[QPushButton] = None
        self._validation_info_label: Optional[QLabel] = None

        # Phase F-12: Control Rules UI (Persisted)
        self._control_rules_list: Optional[QListWidget] = None
        self._control_rules_info_label: Optional[QLabel] = None
        self._add_control_rule_button: Optional[QPushButton] = None

        # Phase SD-3: Entity Edit/Delete UI
        self._edit_entity_button: Optional[QPushButton] = None
        self._delete_entity_button: Optional[QPushButton] = None

        # Phase 5: UX Polish
        self._subtitle_frame: Optional[QFrame] = None
        self._subtitle_dismissed: bool = False
        self._entity_empty_label: Optional[QLabel] = None
        self._field_empty_label: Optional[QLabel] = None

        # Phase 5 Step 3: Unsaved changes tracking (view-level only)
        self._has_unsaved_changes: bool = False
        self._base_window_title: str = "Schema Designer - Create Entities & Fields"
        self._close_event_filter: Optional[_CloseEventFilter] = None

        # Phase F-1: Formula Editor UI
        self._formula_editor_widget: Optional[FormulaEditorWidget] = None
        self._formula_panel_info_label: Optional[QLabel] = None

        # Phase F-9: Control Rules Preview UI
        self._preview_mode_checkbox: Optional[QCheckBox] = None
        self._preview_fields_container: Optional[QWidget] = None
        self._preview_field_inputs: dict[str, QLineEdit] = {}
        self._preview_rules_list: Optional[QListWidget] = None
        self._preview_field_states_list: Optional[QListWidget] = None
        self._add_preview_rule_button: Optional[QPushButton] = None
        self._preview_panel_info_label: Optional[QLabel] = None

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
            "Start by selecting an entity on the left to view its fields. "
            "Then select a field to view or add validation constraints."
        )
        info_label.setStyleSheet("color: gray; padding: 5px;")
        main_layout.addWidget(info_label)

        # Create five-panel splitter (Phase 6B: relationships, Phase F-1: formula editor)
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

        # Panel 5: Formula Editor (Phase F-1)
        formula_panel = self._create_formula_panel()
        splitter.addWidget(formula_panel)

        # Panel 6: Control Rules Preview (Phase F-9)
        preview_panel = self._create_preview_panel()
        splitter.addWidget(preview_panel)

        # Set initial splitter sizes (equal distribution)
        splitter.setSizes([200, 200, 200, 200, 200, 200])

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
        # Phase F-9: Subscribe to preview mode changes
        self._viewmodel.subscribe("preview_mode_state", self._on_preview_mode_state_changed)
        self._viewmodel.subscribe("preview_results", self._on_preview_results_changed)
        # Phase F-12: Subscribe to control rules changes
        self._viewmodel.subscribe("control_rules", self._on_control_rules_changed)
        # Phase F-13: Subscribe to output mappings changes
        self._viewmodel.subscribe("output_mappings", self._on_output_mappings_changed)

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
        add_entity_button.setToolTip(
            "Create a new entity definition.\n"
            "Entities are containers for field definitions\n"
            "(e.g., 'Project Info', 'Boreholes', 'Samples')."
        )
        header_layout.addWidget(add_entity_button)

        # Edit Entity button (Phase SD-3)
        self._edit_entity_button = QPushButton("Edit")
        self._edit_entity_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        self._edit_entity_button.clicked.connect(self._on_edit_entity_clicked)
        self._edit_entity_button.setToolTip(
            "Edit the selected entity's metadata.\n"
            "(Name, description, root status)"
        )
        self._edit_entity_button.setEnabled(False)  # Disabled until entity selected
        header_layout.addWidget(self._edit_entity_button)

        # Delete Entity button (Phase SD-3)
        self._delete_entity_button = QPushButton("Delete")
        self._delete_entity_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        self._delete_entity_button.clicked.connect(self._on_delete_entity_clicked)
        self._delete_entity_button.setToolTip(
            "Delete the selected entity.\n"
            "Cannot delete if entity is referenced by other entities."
        )
        self._delete_entity_button.setEnabled(False)  # Disabled until entity selected
        header_layout.addWidget(self._delete_entity_button)

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

        # Edit Field button (Phase SD-4)
        self._edit_field_button = QPushButton("Edit")
        self._edit_field_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        self._edit_field_button.clicked.connect(self._on_edit_field_clicked)
        self._edit_field_button.setToolTip(
            "Edit the selected field's metadata.\n"
            "(Label, help text, required, default value)"
        )
        self._edit_field_button.setEnabled(False)  # Disabled until field selected
        header_layout.addWidget(self._edit_field_button)

        # Delete Field button (Phase SD-4)
        self._delete_field_button = QPushButton("Delete")
        self._delete_field_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        self._delete_field_button.clicked.connect(self._on_delete_field_clicked)
        self._delete_field_button.setToolTip(
            "Delete the selected field.\n"
            "Cannot delete if field is referenced by formulas or controls."
        )
        self._delete_field_button.setEnabled(False)  # Disabled until field selected
        header_layout.addWidget(self._delete_field_button)

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

        Phase SD-2: Add Constraint button added.

        Returns:
            Widget containing validation rules list and add constraint button
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Panel title with Add Constraint button
        header_layout = QHBoxLayout()
        title = QLabel("Validation Rules")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Add Constraint button (Phase SD-2)
        self._add_constraint_button = QPushButton("+ Add Constraint")
        self._add_constraint_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        self._add_constraint_button.clicked.connect(self._on_add_constraint_clicked)
        self._add_constraint_button.setToolTip(
            "Add a validation constraint to the selected field.\n\n"
            "Available constraints (vary by field type):\n"
            "- Required: Field must not be empty\n"
            "- Min/Max Value: Numeric or date range\n"
            "- Min/Max Length: Text length limits\n"
            "- Pattern: Regex validation\n"
            "- Allowed Values: Restrict to specific values\n"
            "- File Extension: Allowed file types\n"
            "- Max File Size: File size limit"
        )
        self._add_constraint_button.setEnabled(False)  # Disabled until field selected
        header_layout.addWidget(self._add_constraint_button)

        layout.addLayout(header_layout)

        # Info label (shows when no field selected)
        self._validation_info_label = QLabel(
            "Select a field to view its validation rules.\n"
            "You can add constraints like Required, Min/Max, Pattern, etc."
        )
        self._validation_info_label.setStyleSheet(
            "color: gray; font-style: italic; padding: 10px;"
        )
        self._validation_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._validation_info_label)

        # Validation rules list
        self._validation_list = QListWidget()
        self._validation_list.setVisible(False)  # Hidden until field selected
        layout.addWidget(self._validation_list)

        # Phase F-12: Control Rules Section (Persisted)
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #d0d8e0; margin: 10px 0px;")
        layout.addWidget(separator)

        # Control Rules header with Add button
        control_rules_header = QHBoxLayout()
        control_rules_title = QLabel("Control Rules (Persisted)")
        control_rules_title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        control_rules_header.addWidget(control_rules_title)
        control_rules_header.addStretch()

        # Add Control Rule button (Phase F-12)
        self._add_control_rule_button = QPushButton("+ Add Control Rule")
        self._add_control_rule_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        self._add_control_rule_button.clicked.connect(self._on_add_control_rule_clicked)
        self._add_control_rule_button.setToolTip(
            "Add a persisted control rule to the selected field.\n\n"
            "Control rules define inter-field dependencies:\n"
            "- VISIBILITY: Controls whether a field is visible\n"
            "- ENABLED: Controls whether a field is enabled/disabled\n"
            "- REQUIRED: Controls whether a field is required\n\n"
            "Rules are saved in the schema and enforced at design-time."
        )
        self._add_control_rule_button.setEnabled(False)  # Disabled until field selected
        control_rules_header.addWidget(self._add_control_rule_button)

        layout.addLayout(control_rules_header)

        # Info label (shows when no field selected)
        self._control_rules_info_label = QLabel(
            "Select a field to view its control rules.\n"
            "Control rules define inter-field dependencies (VISIBILITY, ENABLED, REQUIRED)."
        )
        self._control_rules_info_label.setStyleSheet(
            "color: gray; font-style: italic; padding: 10px;"
        )
        self._control_rules_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._control_rules_info_label)

        # Control rules list
        self._control_rules_list = QListWidget()
        self._control_rules_list.setVisible(False)  # Hidden until field selected
        self._control_rules_list.itemDoubleClicked.connect(self._on_control_rule_double_clicked)
        self._control_rules_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._control_rules_list.customContextMenuRequested.connect(self._on_control_rule_context_menu)
        layout.addWidget(self._control_rules_list)

        # Phase F-13: Output Mappings Section (Persisted)
        # Separator line
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setStyleSheet("color: #d0d8e0; margin: 10px 0px;")
        layout.addWidget(separator2)

        # Output Mappings header with Add button
        output_mappings_header = QHBoxLayout()
        output_mappings_title = QLabel("Output Mappings (Persisted)")
        output_mappings_title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        output_mappings_header.addWidget(output_mappings_title)
        output_mappings_header.addStretch()

        # Add Output Mapping button (Phase F-13)
        self._add_output_mapping_button = QPushButton("+ Add Output Mapping")
        self._add_output_mapping_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        self._add_output_mapping_button.clicked.connect(self._on_add_output_mapping_clicked)
        self._add_output_mapping_button.setEnabled(False)  # Disabled until field selected
        output_mappings_header.addWidget(self._add_output_mapping_button)

        layout.addLayout(output_mappings_header)

        # Info label (shows when no field selected)
        self._output_mappings_info_label = QLabel(
            "Select a field to view its output mappings.\n"
            "Output mappings define how field values are transformed for document output."
        )
        self._output_mappings_info_label.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
        self._output_mappings_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._output_mappings_info_label)

        # Output mappings list
        self._output_mappings_list = QListWidget()
        self._output_mappings_list.setVisible(False)  # Hidden until field selected
        self._output_mappings_list.itemDoubleClicked.connect(self._on_output_mapping_double_clicked)
        self._output_mappings_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._output_mappings_list.customContextMenuRequested.connect(self._on_output_mapping_context_menu)
        layout.addWidget(self._output_mappings_list)

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
        notice = QLabel("\u26a0\ufe0f Relationships are immutable (ADD-ONLY)")
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

    def _create_formula_panel(self) -> QWidget:
        """Create the formula editor panel (Phase F-1).

        The Formula Editor provides:
        - Live syntax validation
        - Field reference validation against schema
        - Inferred result type display
        - Error/warning display

        Phase F-1 Constraints:
        - READ-ONLY with respect to schema
        - NO formula execution
        - NO schema mutation

        Returns:
            Widget containing formula editor or placeholder
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Panel title
        title = QLabel("Formula Editor")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        layout.addWidget(title)

        # Phase F-1 notice
        notice = QLabel("Read-only validation (no execution)")
        notice.setStyleSheet(
            "color: #718096; "
            "font-size: 8pt; "
            "font-style: italic; "
            "padding: 2px 5px;"
        )
        layout.addWidget(notice)

        # Info label (shows when no field selected or formula editor not available)
        self._formula_panel_info_label = QLabel(
            "Select a field to validate formulas.\n\n"
            "The formula editor validates syntax and\n"
            "field references against the schema."
        )
        self._formula_panel_info_label.setStyleSheet(
            "color: gray; font-style: italic; padding: 10px;"
        )
        self._formula_panel_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._formula_panel_info_label)

        # Create Formula Editor Widget if ViewModel has formula support
        formula_editor_vm = self._viewmodel.formula_editor_viewmodel
        if formula_editor_vm is not None:
            self._formula_editor_widget = FormulaEditorWidget(
                viewmodel=formula_editor_vm,
                parent=panel,
            )
            self._formula_editor_widget.setVisible(False)  # Hidden until field selected
            layout.addWidget(self._formula_editor_widget)
        else:
            # Show message if formula support not available
            no_support_label = QLabel(
                "Formula validation not available.\n\n"
                "FormulaUseCases not configured."
            )
            no_support_label.setStyleSheet(
                "color: #b45309; "
                "font-style: italic; "
                "padding: 20px; "
                "background-color: #fffff0; "
                "border: 1px dashed #f6e05e; "
                "border-radius: 4px;"
            )
            no_support_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_support_label)

        layout.addStretch()
        return panel

    def _create_preview_panel(self) -> QWidget:
        """Create the control rules preview panel (Phase F-9).

        The Control Rules Preview provides:
        - Toggle to enable/disable preview mode
        - Field value inputs for temporary preview values
        - Control rules list for defining rules
        - Field preview states showing applied effects

        Phase F-9 Constraints:
        - UI-ONLY with respect to schema
        - NO persistence
        - NO schema mutation
        - In-memory preview values only

        Returns:
            Widget containing preview controls
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Panel title
        title = QLabel("Control Rules Preview")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        layout.addWidget(title)

        # Phase F-9 notice
        notice = QLabel("UI-only preview (no persistence)")
        notice.setStyleSheet(
            "color: #718096; "
            "font-size: 8pt; "
            "font-style: italic; "
            "padding: 2px 5px;"
        )
        layout.addWidget(notice)

        # Preview mode toggle
        self._preview_mode_checkbox = QCheckBox("Enable Preview Mode")
        self._preview_mode_checkbox.setStyleSheet("padding: 5px;")
        self._preview_mode_checkbox.setToolTip(
            "Toggle preview mode to test control rules.\n"
            "When enabled, you can set temporary field values\n"
            "and define control rules to see their effects."
        )
        self._preview_mode_checkbox.stateChanged.connect(self._on_preview_mode_toggled)
        layout.addWidget(self._preview_mode_checkbox)

        # Info label (shows when preview mode disabled or no entity selected)
        self._preview_panel_info_label = QLabel(
            "Enable preview mode and select an entity\n"
            "to test control rules with temporary values.\n\n"
            "Control rules govern field behavior:\n"
            "• VISIBILITY: Show/hide fields\n"
            "• ENABLED: Enable/disable fields\n"
            "• REQUIRED: Show required indicator"
        )
        self._preview_panel_info_label.setStyleSheet(
            "color: gray; font-style: italic; padding: 10px;"
        )
        self._preview_panel_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_panel_info_label.setWordWrap(True)
        layout.addWidget(self._preview_panel_info_label)

        # Preview fields container (scrollable)
        fields_scroll = QScrollArea()
        fields_scroll.setWidgetResizable(True)
        fields_scroll.setMaximumHeight(150)
        fields_scroll.setVisible(False)

        self._preview_fields_container = QWidget()
        self._preview_fields_layout = QVBoxLayout(self._preview_fields_container)
        self._preview_fields_layout.setContentsMargins(5, 5, 5, 5)
        self._preview_fields_layout.addStretch()

        fields_scroll.setWidget(self._preview_fields_container)
        self._preview_fields_scroll = fields_scroll
        layout.addWidget(fields_scroll)

        # Control rules section
        rules_header = QHBoxLayout()
        rules_label = QLabel("Preview Rules:")
        rules_label.setStyleSheet("font-weight: bold; padding: 3px;")
        rules_header.addWidget(rules_label)
        rules_header.addStretch()

        self._add_preview_rule_button = QPushButton("+ Add Rule")
        self._add_preview_rule_button.setStyleSheet("font-size: 9pt; padding: 3px 8px;")
        self._add_preview_rule_button.clicked.connect(self._on_add_preview_rule_clicked)
        self._add_preview_rule_button.setToolTip(
            "Add a control rule for preview.\n"
            "Rules are evaluated against temporary field values."
        )
        self._add_preview_rule_button.setEnabled(False)
        self._add_preview_rule_button.setVisible(False)
        rules_header.addWidget(self._add_preview_rule_button)

        layout.addLayout(rules_header)

        # Preview rules list
        self._preview_rules_list = QListWidget()
        self._preview_rules_list.setMaximumHeight(100)
        self._preview_rules_list.setVisible(False)
        self._preview_rules_list.setToolTip(
            "Control rules defined for preview.\n"
            "Double-click to edit, select and press Delete to remove."
        )
        layout.addWidget(self._preview_rules_list)

        # Field preview states section
        states_label = QLabel("Field States:")
        states_label.setStyleSheet("font-weight: bold; padding: 3px;")
        states_label.setVisible(False)
        self._preview_states_label = states_label
        layout.addWidget(states_label)

        self._preview_field_states_list = QListWidget()
        self._preview_field_states_list.setVisible(False)
        self._preview_field_states_list.setToolTip(
            "Preview of how control rules affect each field.\n"
            "Shows visibility, enabled, and required states."
        )
        layout.addWidget(self._preview_field_states_list)

        layout.addStretch()
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

        Phase 5 Step 3: Confirm close. No save/discard logic needed
        since changes are applied immediately via commands.
        """
        if self._confirm_close():
            self._root.close()

    def _confirm_close(self) -> bool:
        """Confirm close of Schema Designer.

        Phase 5 Step 3: Simple close confirmation. Changes are applied
        immediately via commands, so no save/discard logic needed.

        Returns:
            True if user confirms close or no changes made, False to cancel
        """
        # If no changes were made this session, close immediately
        if not self._has_unsaved_changes:
            return True

        # Inform user that changes were applied and confirm close
        result = QMessageBox.information(
            self._root,
            "Close Schema Designer",
            "All changes have been applied to the schema.\n\n"
            "Close Schema Designer?",
            QMessageBox.StandardButton.Close | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Close,
        )

        return result == QMessageBox.StandardButton.Close

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
        entity_selected = current is not None

        # Phase SD-3: Enable/disable Edit and Delete buttons
        if self._edit_entity_button:
            self._edit_entity_button.setEnabled(entity_selected)
        if self._delete_entity_button:
            self._delete_entity_button.setEnabled(entity_selected)

        if current:
            entity_id = current.data(Qt.ItemDataRole.UserRole)
            self._viewmodel.select_entity(entity_id)

        # Phase F-9: Update preview panel when entity changes
        if self._viewmodel.is_preview_mode_enabled:
            self._on_preview_mode_state_changed()

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
        field_selected = current is not None

        # Phase SD-4: Enable/disable Edit and Delete buttons
        if self._edit_field_button:
            self._edit_field_button.setEnabled(field_selected)
        if self._delete_field_button:
            self._delete_field_button.setEnabled(field_selected)

        # Phase F-1: Update formula editor visibility
        self._update_formula_editor_visibility(field_selected)

        if current:
            field_id = current.data(Qt.ItemDataRole.UserRole)
            self._viewmodel.select_field(field_id)

    def _update_formula_editor_visibility(self, field_selected: bool) -> None:
        """Update formula editor panel visibility based on field selection.

        Phase F-1: Formula Editor appears when a field is selected.
        Shows info label when no field selected.

        Args:
            field_selected: True if a field is currently selected
        """
        if self._formula_panel_info_label:
            self._formula_panel_info_label.setVisible(not field_selected)

        if self._formula_editor_widget:
            self._formula_editor_widget.setVisible(field_selected)

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

        # Phase SD-4: Disable Edit/Delete buttons when field list changes
        # (field selection is cleared when list is refreshed)
        if self._edit_field_button:
            self._edit_field_button.setEnabled(False)
        if self._delete_field_button:
            self._delete_field_button.setEnabled(False)

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
            # Use dto.is_required (derived in Application layer, authoritative for UI)
            item_text = f"{field_dto.label} ({field_dto.field_type})"
            if field_dto.is_required:
                item_text += " *"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, field_dto.id)

            # Add tooltip with field details
            tooltip_parts = [
                f"Label: {field_dto.label}",
                f"Type: {field_dto.field_type}",
                f"Required: {'Yes' if field_dto.is_required else 'No'}",
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
        """Handle validation rules list change.

        Phase SD-2: Also manages Add Constraint button state.
        """
        self._validation_list.clear()

        rules = self._viewmodel.validation_rules
        field_selected = self._viewmodel.selected_field_id is not None

        # Manage visibility of info label and list
        if self._validation_info_label:
            self._validation_info_label.setVisible(not field_selected)

        # Manage Add Constraint button state
        if self._add_constraint_button:
            self._add_constraint_button.setEnabled(field_selected)

        if not field_selected:
            self._validation_list.setVisible(False)
            return

        # Field is selected - show the list
        self._validation_list.setVisible(True)

        if rules:
            for rule_text in rules:
                item = QListWidgetItem(rule_text)
                self._validation_list.addItem(item)
        else:
            # Show message if no rules defined
            item = QListWidgetItem("No validation rules defined")
            item.setForeground(Qt.GlobalColor.gray)
            self._validation_list.addItem(item)

    def _on_control_rules_changed(self) -> None:
        """Handle control rules list change (Phase F-12).

        Updates the control rules list when a field is selected or when rules change.
        Manages Add Control Rule button state based on field selection.
        """
        if not self._control_rules_list:
            return

        self._control_rules_list.clear()

        rules = self._viewmodel.control_rules
        field_selected = self._viewmodel.selected_field_id is not None

        # Manage visibility of info label and list
        if self._control_rules_info_label:
            self._control_rules_info_label.setVisible(not field_selected)

        # Manage Add Control Rule button state
        if self._add_control_rule_button:
            self._add_control_rule_button.setEnabled(field_selected)

        if not field_selected:
            self._control_rules_list.setVisible(False)
            return

        # Field is selected - show the list
        self._control_rules_list.setVisible(True)

        if rules:
            for rule_dto in rules:
                # Format: "VISIBILITY → field2: {{status}} == 'active'"
                rule_display = f"{rule_dto.rule_type} → {rule_dto.target_field_id}: {rule_dto.formula_text}"
                item = QListWidgetItem(rule_display)
                # Store the full DTO in UserRole for Edit/Delete operations
                item.setData(Qt.ItemDataRole.UserRole, rule_dto)

                # Add governance status indicator if available
                tooltip = (
                    f"Type: {rule_dto.rule_type}\n"
                    f"Target Field: {rule_dto.target_field_id}\n"
                    f"Formula: {rule_dto.formula_text}"
                )
                item.setToolTip(tooltip)

                self._control_rules_list.addItem(item)
        else:
            # Show message if no rules defined
            item = QListWidgetItem("No control rules defined")
            item.setForeground(Qt.GlobalColor.gray)
            self._control_rules_list.addItem(item)

    def _on_output_mappings_changed(self) -> None:
        """Handle output mappings list change (Phase F-13).

        Updates the output mappings list when a field is selected or when mappings change.
        Manages Add Output Mapping button state based on field selection.
        """
        if not self._output_mappings_list:
            return

        self._output_mappings_list.clear()

        mappings = self._viewmodel.output_mappings
        field_selected = self._viewmodel.selected_field_id is not None

        # Manage visibility of info label and list
        if self._output_mappings_info_label:
            self._output_mappings_info_label.setVisible(not field_selected)

        # Manage Add Output Mapping button state
        if self._add_output_mapping_button:
            self._add_output_mapping_button.setEnabled(field_selected)

        if not field_selected:
            self._output_mappings_list.setVisible(False)
            return

        # Field is selected - show the list
        self._output_mappings_list.setVisible(True)

        if mappings:
            for mapping_dto in mappings:
                # Format: "TEXT → {{depth_from}} - {{depth_to}}"
                mapping_display = f"{mapping_dto.target} → {mapping_dto.formula_text}"
                item = QListWidgetItem(mapping_display)
                # Store the full DTO in UserRole for Edit/Delete operations
                item.setData(Qt.ItemDataRole.UserRole, mapping_dto)

                # Add tooltip
                tooltip = (
                    f"Target: {mapping_dto.target}\n"
                    f"Formula: {mapping_dto.formula_text}"
                )
                item.setToolTip(tooltip)

                self._output_mappings_list.addItem(item)
        else:
            # Show message if no mappings defined
            item = QListWidgetItem("No output mappings defined")
            item.setForeground(Qt.GlobalColor.gray)
            self._output_mappings_list.addItem(item)

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

            if result.success:
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

    def _on_edit_entity_clicked(self) -> None:
        """Handle Edit Entity button click (Phase SD-3)."""
        if not self._viewmodel.selected_entity_id:
            QMessageBox.warning(
                self._root,
                "No Entity Selected",
                "Please select an entity first.",
            )
            return

        # Find the selected entity DTO
        selected_entity = None
        for entity_dto in self._viewmodel.entities:
            if entity_dto.id == self._viewmodel.selected_entity_id:
                selected_entity = entity_dto
                break

        if not selected_entity:
            QMessageBox.warning(
                self._root,
                "Entity Not Found",
                "The selected entity could not be found.",
            )
            return

        from doc_helper.presentation.dialogs.edit_entity_dialog import EditEntityDialog

        dialog = EditEntityDialog(
            entity_id=selected_entity.id,
            current_name_key=selected_entity.name_key,
            current_description_key=selected_entity.description_key,
            current_is_root=selected_entity.is_root_entity,
            parent=self._root,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            entity_data = dialog.get_entity_data()
            if not entity_data:
                return

            # Update entity via ViewModel
            result = self._viewmodel.update_entity(
                entity_id=entity_data["entity_id"],
                name_key=entity_data["name_key"],
                description_key=entity_data["description_key"],
                is_root_entity=entity_data["is_root_entity"],
            )

            if result.success:
                self._set_unsaved_changes(True)
                QMessageBox.information(
                    self._root,
                    "Entity Updated",
                    f"Entity '{entity_data['entity_id']}' updated successfully!",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Updating Entity",
                    f"Failed to update entity:\n\n{result.error}",
                )

    def _on_delete_entity_clicked(self) -> None:
        """Handle Delete Entity button click (Phase SD-3)."""
        if not self._viewmodel.selected_entity_id:
            QMessageBox.warning(
                self._root,
                "No Entity Selected",
                "Please select an entity first.",
            )
            return

        entity_id = self._viewmodel.selected_entity_id

        # Find entity name for confirmation message
        entity_name = entity_id
        for entity_dto in self._viewmodel.entities:
            if entity_dto.id == entity_id:
                entity_name = entity_dto.name
                break

        # Confirmation dialog
        confirm = QMessageBox.warning(
            self._root,
            "Confirm Delete",
            f"Are you sure you want to delete entity '{entity_name}'?\n\n"
            "This will also delete all fields defined in this entity.\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        # Delete entity via ViewModel
        result = self._viewmodel.delete_entity(entity_id=entity_id)

        if result.success:
            self._set_unsaved_changes(True)
            QMessageBox.information(
                self._root,
                "Entity Deleted",
                f"Entity '{entity_name}' deleted successfully!",
            )
        else:
            # Show detailed error message (includes dependency info)
            QMessageBox.critical(
                self._root,
                "Cannot Delete Entity",
                result.error,
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

            if result.success:
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
    # Phase SD-4: Field Edit/Delete Operations
    # -------------------------------------------------------------------------

    def _on_edit_field_clicked(self) -> None:
        """Handle Edit Field button click (Phase SD-4)."""
        if not self._viewmodel.selected_entity_id:
            QMessageBox.warning(
                self._root,
                "No Entity Selected",
                "Please select an entity first.",
            )
            return

        if not self._viewmodel.selected_field_id:
            QMessageBox.warning(
                self._root,
                "No Field Selected",
                "Please select a field first.",
            )
            return

        # Find the selected field DTO
        selected_field = None
        fields = self._viewmodel.fields
        for field_dto in fields:
            if field_dto.id == self._viewmodel.selected_field_id:
                selected_field = field_dto
                break

        if not selected_field:
            QMessageBox.warning(
                self._root,
                "Field Not Found",
                "The selected field could not be found.",
            )
            return

        # Get available entities for LOOKUP/TABLE dropdowns
        available_entities = tuple(
            (entity.id, entity.name) for entity in self._viewmodel.entities
        )

        from doc_helper.presentation.dialogs.edit_field_dialog import EditFieldDialog

        # For choice fields (DROPDOWN, RADIO), prepare option callbacks (Phase F-14)
        is_choice_field = selected_field.field_type in ("DROPDOWN", "RADIO")
        current_options = None
        on_add_option = None
        on_update_option = None
        on_delete_option = None
        on_reorder_options = None
        get_options = None

        if is_choice_field:
            # Load current options from ViewModel
            self._viewmodel.load_field_options()
            current_options = self._viewmodel.field_options

            # Wrap callbacks to also track unsaved changes
            def _wrap_option_callback(fn):
                def wrapper(*args):
                    result = fn(*args)
                    if result.success:
                        self._set_unsaved_changes(True)
                    return result
                return wrapper

            on_add_option = _wrap_option_callback(self._viewmodel.add_field_option)
            on_update_option = _wrap_option_callback(self._viewmodel.update_field_option)
            on_delete_option = _wrap_option_callback(self._viewmodel.delete_field_option)
            on_reorder_options = _wrap_option_callback(self._viewmodel.reorder_field_options)
            get_options = lambda: self._viewmodel.field_options

        dialog = EditFieldDialog(
            entity_id=self._viewmodel.selected_entity_id,
            field_id=selected_field.id,
            field_type=selected_field.field_type,
            current_label_key=selected_field.label,  # DTO has translated label
            current_help_text_key=selected_field.help_text,  # DTO has translated help_text
            current_required=selected_field.is_required,  # Use DTO.is_required (authoritative)
            current_default_value=selected_field.default_value,
            current_formula=selected_field.formula,
            current_lookup_entity_id=selected_field.lookup_entity_id,
            current_lookup_display_field=selected_field.lookup_display_field,
            current_child_entity_id=selected_field.child_entity_id,
            available_entities=available_entities,
            current_options=current_options,
            on_add_option=on_add_option,
            on_update_option=on_update_option,
            on_delete_option=on_delete_option,
            on_reorder_options=on_reorder_options,
            get_options=get_options,
            parent=self._root,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            field_data = dialog.get_field_data()
            if not field_data:
                return

            # Update field via ViewModel
            result = self._viewmodel.update_field(
                entity_id=field_data["entity_id"],
                field_id=field_data["field_id"],
                label_key=field_data["label_key"],
                help_text_key=field_data["help_text_key"],
                required=field_data["required"],
                default_value=field_data["default_value"],
                formula=field_data.get("formula"),
                lookup_entity_id=field_data.get("lookup_entity_id"),
                lookup_display_field=field_data.get("lookup_display_field"),
                child_entity_id=field_data.get("child_entity_id"),
            )

            if result.success:
                self._set_unsaved_changes(True)
                QMessageBox.information(
                    self._root,
                    "Field Updated",
                    f"Field '{field_data['field_id']}' updated successfully!",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Updating Field",
                    f"Failed to update field:\n\n{result.error}",
                )

    def _on_delete_field_clicked(self) -> None:
        """Handle Delete Field button click (Phase SD-4)."""
        if not self._viewmodel.selected_entity_id:
            QMessageBox.warning(
                self._root,
                "No Entity Selected",
                "Please select an entity first.",
            )
            return

        if not self._viewmodel.selected_field_id:
            QMessageBox.warning(
                self._root,
                "No Field Selected",
                "Please select a field first.",
            )
            return

        entity_id = self._viewmodel.selected_entity_id
        field_id = self._viewmodel.selected_field_id

        # Find field label for confirmation message
        field_label = field_id
        for field_dto in self._viewmodel.fields:
            if field_dto.id == field_id:
                field_label = field_dto.label
                break

        # Confirmation dialog
        confirm = QMessageBox.warning(
            self._root,
            "Confirm Delete",
            f"Are you sure you want to delete field '{field_label}'?\n\n"
            "This will also remove any validation constraints on this field.\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        # Delete field via ViewModel
        result = self._viewmodel.delete_field(
            entity_id=entity_id,
            field_id=field_id,
        )

        if result.success:
            self._set_unsaved_changes(True)
            QMessageBox.information(
                self._root,
                "Field Deleted",
                f"Field '{field_label}' deleted successfully!",
            )
        else:
            # Show detailed error message (includes dependency info)
            QMessageBox.critical(
                self._root,
                "Cannot Delete Field",
                result.error,
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

            if result.success:
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
    # Phase SD-2: Constraint Operations
    # -------------------------------------------------------------------------

    def _on_add_constraint_clicked(self) -> None:
        """Handle Add Constraint button click (Phase SD-2).

        Opens dialog to add a validation constraint to the selected field.
        """
        # Verify field is selected
        if not self._viewmodel.selected_field_id:
            QMessageBox.warning(
                self._root,
                "No Field Selected",
                "Please select a field first before adding a constraint.",
            )
            return

        if not self._viewmodel.selected_entity_id:
            QMessageBox.warning(
                self._root,
                "No Entity Selected",
                "Please select an entity and field first.",
            )
            return

        # Get field label and type from authoritative DTO (Phase S-3: NO fallbacks)
        field_label = self._viewmodel.selected_field_id
        field_type: str | None = None  # Must be resolved from DTO
        for entity_dto in self._viewmodel.entities:
            if entity_dto.id == self._viewmodel.selected_entity_id:
                for field_dto in entity_dto.fields:
                    if field_dto.id == self._viewmodel.selected_field_id:
                        field_label = field_dto.label or field_dto.id
                        field_type = field_dto.field_type  # Authoritative source
                        break
                break

        # FAIL-FAST: field_type MUST be resolved from DTO - no silent defaults
        if field_type is None:
            QMessageBox.critical(
                self._root,
                "Invariant Violation",
                f"Cannot determine field type for '{self._viewmodel.selected_field_id}'.\n\n"
                "This indicates a data inconsistency. The selected field does not exist "
                "in the current schema state.\n\n"
                "Please refresh the schema and try again.",
            )
            return

        from doc_helper.presentation.dialogs.add_constraint_dialog import (
            AddConstraintDialog,
        )

        dialog = AddConstraintDialog(
            field_id=self._viewmodel.selected_field_id,
            field_label=field_label,
            field_type=field_type,  # Authoritative - never defaulted
            parent=self._root,
        )

        # ISSUE 1 FIX: Loop until validation passes or user cancels.
        # Dialog MUST remain open on validation failure so user can correct input.
        while True:
            if dialog.exec() != QDialog.DialogCode.Accepted:
                # User cancelled - exit loop
                break

            constraint_data = dialog.get_constraint_data()
            if not constraint_data:
                # No data - exit loop
                break

            # Add constraint via ViewModel
            result = self._viewmodel.add_constraint(
                entity_id=self._viewmodel.selected_entity_id,
                field_id=self._viewmodel.selected_field_id,
                constraint_type=constraint_data["constraint_type"],
                value=constraint_data["value"],
                severity=constraint_data["severity"],
            )

            if result.success:
                # Mark as having unsaved changes
                self._set_unsaved_changes(True)

                QMessageBox.information(
                    self._root,
                    "Constraint Added",
                    f"Constraint '{constraint_data['constraint_type']}' added to "
                    f"field '{field_label}' successfully!",
                )
                # Success - exit loop
                break
            else:
                # ISSUE 1: Show error but keep dialog open for retry.
                # User can correct their input without losing it.
                QMessageBox.critical(
                    self._root,
                    "Error Adding Constraint",
                    f"Failed to add constraint:\n\n{result.error}",
                )
                # Loop continues - dialog will re-show with preserved input

    # -------------------------------------------------------------------------
    # Phase F-12: Control Rules Operations
    # -------------------------------------------------------------------------

    def _on_add_control_rule_clicked(self) -> None:
        """Handle Add Control Rule button click (Phase F-12).

        Opens dialog to add a persisted control rule to the selected field.
        """
        # Verify field is selected
        if not self._viewmodel.selected_field_id:
            QMessageBox.warning(
                self._root,
                "No Field Selected",
                "Please select a field first before adding a control rule.",
            )
            return

        if not self._viewmodel.selected_entity_id:
            QMessageBox.warning(
                self._root,
                "No Entity Selected",
                "Please select an entity and field first.",
            )
            return

        # Get available fields from current entity for target field selection
        available_fields = ()
        for entity_dto in self._viewmodel.entities:
            if entity_dto.id == self._viewmodel.selected_entity_id:
                available_fields = entity_dto.fields
                break

        if not available_fields:
            QMessageBox.warning(
                self._root,
                "No Fields Available",
                "The current entity has no fields available as control targets.",
            )
            return

        from doc_helper.presentation.dialogs.control_rule_dialog import (
            ControlRuleDialog,
        )

        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=self._root,
            existing_rule=None,  # Add mode
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            rule_type = dialog.get_rule_type()
            target_field_id = dialog.get_target_field_id()
            formula_text = dialog.get_formula_text()

            if not formula_text.strip():
                QMessageBox.warning(
                    self._root,
                    "Invalid Formula",
                    "Formula text cannot be empty.",
                )
                return

            # Add control rule via ViewModel
            result = self._viewmodel.add_control_rule(
                rule_type=rule_type,
                target_field_id=target_field_id,
                formula_text=formula_text,
            )

            if result.success:
                # Mark as having unsaved changes
                self._set_unsaved_changes(True)

                QMessageBox.information(
                    self._root,
                    "Control Rule Added",
                    f"Control rule '{rule_type}' added successfully!",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Adding Control Rule",
                    f"Failed to add control rule:\n\n{result.error}",
                )

    def _on_control_rule_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle control rule list item double-click (Phase F-12).

        Opens edit dialog for the selected control rule.

        Args:
            item: The list item that was double-clicked
        """
        # Get the rule DTO from the item
        rule_dto = item.data(Qt.ItemDataRole.UserRole)
        if not rule_dto:
            return  # Empty state item

        # Get available fields from current entity
        available_fields = ()
        for entity_dto in self._viewmodel.entities:
            if entity_dto.id == self._viewmodel.selected_entity_id:
                available_fields = entity_dto.fields
                break

        from doc_helper.presentation.dialogs.control_rule_dialog import (
            ControlRuleDialog,
        )

        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=self._root,
            existing_rule=rule_dto,  # Edit mode
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            formula_text = dialog.get_formula_text()

            if not formula_text.strip():
                QMessageBox.warning(
                    self._root,
                    "Invalid Formula",
                    "Formula text cannot be empty.",
                )
                return

            # Update control rule via ViewModel (rule_type identifies the rule)
            result = self._viewmodel.update_control_rule(
                rule_type=rule_dto.rule_type,
                formula_text=formula_text,
            )

            if result.success:
                # Mark as having unsaved changes
                self._set_unsaved_changes(True)

                QMessageBox.information(
                    self._root,
                    "Control Rule Updated",
                    f"Control rule '{rule_dto.rule_type}' updated successfully!",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Updating Control Rule",
                    f"Failed to update control rule:\n\n{result.error}",
                )

    def _on_control_rule_context_menu(self, position) -> None:
        """Handle control rule list context menu request (Phase F-12).

        Shows Edit and Delete options for the selected control rule.

        Args:
            position: The position where the context menu was requested
        """
        from PyQt6.QtWidgets import QMenu

        # Get the item at the position
        item = self._control_rules_list.itemAt(position)
        if not item:
            return

        rule_dto = item.data(Qt.ItemDataRole.UserRole)
        if not rule_dto:
            return  # Empty state item

        # Create context menu
        menu = QMenu(self._control_rules_list)

        # Edit action
        edit_action = menu.addAction("Edit...")
        edit_action.triggered.connect(lambda: self._on_control_rule_double_clicked(item))

        # Delete action
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._on_delete_control_rule(rule_dto))

        # Show menu
        menu.exec(self._control_rules_list.mapToGlobal(position))

    def _on_delete_control_rule(self, rule_dto) -> None:
        """Handle control rule deletion (Phase F-12).

        Shows confirmation dialog and deletes the control rule if confirmed.

        Args:
            rule_dto: The ControlRuleExportDTO to delete
        """
        # Confirmation dialog
        result = QMessageBox.question(
            self._root,
            "Delete Control Rule",
            f"Are you sure you want to delete the control rule '{rule_dto.rule_type}' → {rule_dto.target_field_id}?\n\n"
            f"Formula: {rule_dto.formula_text}\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result == QMessageBox.StandardButton.Yes:
            # Delete control rule via ViewModel
            delete_result = self._viewmodel.delete_control_rule(
                rule_type=rule_dto.rule_type
            )

            if delete_result.success:
                # Mark as having unsaved changes
                self._set_unsaved_changes(True)

                QMessageBox.information(
                    self._root,
                    "Control Rule Deleted",
                    f"Control rule '{rule_dto.rule_type}' deleted successfully!",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Deleting Control Rule",
                    f"Failed to delete control rule:\n\n{delete_result.error}",
                )

    # -------------------------------------------------------------------------
    # Phase F-13: Output Mapping Operations
    # -------------------------------------------------------------------------

    def _on_add_output_mapping_clicked(self) -> None:
        """Handle Add Output Mapping button click (Phase F-13).

        Opens dialog to add a persisted output mapping to the selected field.
        """
        # Verify field is selected
        if not self._viewmodel.selected_field_id:
            QMessageBox.warning(
                self._root,
                "No Field Selected",
                "Please select a field first before adding an output mapping.",
            )
            return

        if not self._viewmodel.selected_entity_id:
            QMessageBox.warning(
                self._root,
                "No Entity Selected",
                "Please select an entity and field first.",
            )
            return

        from doc_helper.presentation.dialogs.output_mapping_dialog import (
            OutputMappingDialog,
        )

        dialog = OutputMappingDialog(
            parent=self._root,
            existing_mapping=None,  # Add mode
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            target = dialog.get_target()
            formula_text = dialog.get_formula_text()

            if not formula_text.strip():
                QMessageBox.warning(
                    self._root,
                    "Invalid Formula",
                    "Formula text cannot be empty.",
                )
                return

            # Add output mapping via ViewModel
            result = self._viewmodel.add_output_mapping(
                target=target,
                formula_text=formula_text,
            )

            if result.success:
                # Mark as having unsaved changes
                self._set_unsaved_changes(True)

                QMessageBox.information(
                    self._root,
                    "Output Mapping Added",
                    f"Output mapping for '{target}' added successfully!",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Adding Output Mapping",
                    f"Failed to add output mapping:\n\n{result.error}",
                )

    def _on_output_mapping_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle output mapping list item double-click (Phase F-13).

        Opens edit dialog for the selected output mapping.

        Args:
            item: The list item that was double-clicked
        """
        # Get the mapping DTO from the item
        mapping_dto = item.data(Qt.ItemDataRole.UserRole)
        if not mapping_dto:
            return  # Empty state item

        from doc_helper.presentation.dialogs.output_mapping_dialog import (
            OutputMappingDialog,
        )

        dialog = OutputMappingDialog(
            parent=self._root,
            existing_mapping=mapping_dto,  # Edit mode
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            formula_text = dialog.get_formula_text()

            if not formula_text.strip():
                QMessageBox.warning(
                    self._root,
                    "Invalid Formula",
                    "Formula text cannot be empty.",
                )
                return

            # Update output mapping via ViewModel (target identifies the mapping)
            result = self._viewmodel.update_output_mapping(
                target=mapping_dto.target,
                formula_text=formula_text,
            )

            if result.success:
                # Mark as having unsaved changes
                self._set_unsaved_changes(True)

                QMessageBox.information(
                    self._root,
                    "Output Mapping Updated",
                    f"Output mapping for '{mapping_dto.target}' updated successfully!",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Updating Output Mapping",
                    f"Failed to update output mapping:\n\n{result.error}",
                )

    def _on_output_mapping_context_menu(self, position) -> None:
        """Handle output mapping list context menu request (Phase F-13).

        Shows Edit and Delete options for the selected output mapping.

        Args:
            position: The position where the context menu was requested
        """
        from PyQt6.QtWidgets import QMenu

        # Get the item at the position
        item = self._output_mappings_list.itemAt(position)
        if not item:
            return

        mapping_dto = item.data(Qt.ItemDataRole.UserRole)
        if not mapping_dto:
            return  # Empty state item

        # Create context menu
        menu = QMenu(self._output_mappings_list)

        # Edit action
        edit_action = menu.addAction("Edit...")
        edit_action.triggered.connect(lambda: self._on_output_mapping_double_clicked(item))

        # Delete action
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._on_delete_output_mapping(mapping_dto))

        # Show menu
        menu.exec(self._output_mappings_list.mapToGlobal(position))

    def _on_delete_output_mapping(self, mapping_dto) -> None:
        """Handle output mapping deletion (Phase F-13).

        Shows confirmation dialog and deletes the output mapping if confirmed.

        Args:
            mapping_dto: The OutputMappingExportDTO to delete
        """
        # Confirmation dialog
        result = QMessageBox.question(
            self._root,
            "Delete Output Mapping",
            f"Are you sure you want to delete the output mapping for '{mapping_dto.target}'?\n\n"
            f"Formula: {mapping_dto.formula_text}\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result == QMessageBox.StandardButton.Yes:
            # Delete output mapping via ViewModel
            delete_result = self._viewmodel.delete_output_mapping(
                target=mapping_dto.target
            )

            if delete_result.success:
                # Mark as having unsaved changes
                self._set_unsaved_changes(True)

                QMessageBox.information(
                    self._root,
                    "Output Mapping Deleted",
                    f"Output mapping for '{mapping_dto.target}' deleted successfully!",
                )
            else:
                QMessageBox.critical(
                    self._root,
                    "Error Deleting Output Mapping",
                    f"Failed to delete output mapping:\n\n{delete_result.error}",
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

    # -------------------------------------------------------------------------
    # Phase F-9: Control Rules Preview Operations
    # -------------------------------------------------------------------------

    def _on_preview_mode_toggled(self, state: int) -> None:
        """Handle preview mode checkbox toggle (Phase F-9).

        Args:
            state: Checkbox state (0=unchecked, 2=checked)
        """
        is_enabled = state == 2  # Qt.CheckState.Checked.value

        if is_enabled:
            self._viewmodel.enable_preview_mode()
        else:
            self._viewmodel.disable_preview_mode()

    def _on_preview_mode_state_changed(self) -> None:
        """Handle preview mode state changes from ViewModel (Phase F-9)."""
        preview_state = self._viewmodel.preview_mode_state
        is_enabled = preview_state.is_enabled
        has_entity = self._viewmodel.selected_entity_id is not None

        # Update checkbox without triggering signal
        if self._preview_mode_checkbox:
            self._preview_mode_checkbox.blockSignals(True)
            self._preview_mode_checkbox.setChecked(is_enabled)
            self._preview_mode_checkbox.blockSignals(False)

        # Show/hide preview controls
        show_controls = is_enabled and has_entity

        if self._preview_panel_info_label:
            self._preview_panel_info_label.setVisible(not show_controls)

        if hasattr(self, '_preview_fields_scroll'):
            self._preview_fields_scroll.setVisible(show_controls)

        if self._add_preview_rule_button:
            self._add_preview_rule_button.setEnabled(show_controls)
            self._add_preview_rule_button.setVisible(show_controls)

        if self._preview_rules_list:
            self._preview_rules_list.setVisible(show_controls)

        if hasattr(self, '_preview_states_label'):
            self._preview_states_label.setVisible(show_controls)

        if self._preview_field_states_list:
            self._preview_field_states_list.setVisible(show_controls)

        # Update field inputs when preview mode enabled
        if show_controls:
            self._update_preview_field_inputs()
            self._update_preview_rules_list()
            self._update_preview_field_states()

    def _on_preview_results_changed(self) -> None:
        """Handle preview results changes from ViewModel (Phase F-9)."""
        self._update_preview_field_states()

    def _update_preview_field_inputs(self) -> None:
        """Update field input widgets for preview (Phase F-9)."""
        if not self._preview_fields_container:
            return

        # Clear existing inputs
        layout = self._preview_fields_layout
        while layout.count() > 1:  # Keep the stretch
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._preview_field_inputs.clear()

        # Get fields for selected entity
        fields = self._viewmodel.fields
        if not fields:
            return

        # Create input for each field
        for field_dto in fields:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)

            label = QLabel(f"{field_dto.label}:")
            label.setMinimumWidth(80)
            label.setToolTip(f"Field: {field_dto.id}\nType: {field_dto.field_type}")
            row_layout.addWidget(label)

            input_field = QLineEdit()
            input_field.setPlaceholderText(f"({field_dto.field_type})")
            input_field.setToolTip(
                f"Enter a temporary value for '{field_dto.label}'.\n"
                "This value is used for preview only (not saved)."
            )
            input_field.textChanged.connect(
                lambda text, fid=field_dto.id: self._on_preview_field_value_changed(fid, text)
            )
            row_layout.addWidget(input_field)

            self._preview_field_inputs[field_dto.id] = input_field
            layout.insertWidget(layout.count() - 1, row)

    def _on_preview_field_value_changed(self, field_id: str, value: str) -> None:
        """Handle preview field value change (Phase F-9).

        Args:
            field_id: ID of field that changed
            value: New text value
        """
        # Convert value based on field type
        parsed_value = self._parse_preview_value(field_id, value)
        self._viewmodel.set_preview_field_value(field_id, parsed_value)

    def _parse_preview_value(self, field_id: str, value: str):
        """Parse preview field value based on field type.

        Args:
            field_id: ID of field
            value: Raw text value

        Returns:
            Parsed value (str, int, float, bool, or original string)
        """
        # Find field type
        field_type = None
        for field_dto in self._viewmodel.fields:
            if field_dto.id == field_id:
                field_type = field_dto.field_type
                break

        if not value.strip():
            return None

        # Try to parse based on type
        if field_type == "NUMBER":
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value
        elif field_type == "CHECKBOX":
            lower = value.lower().strip()
            if lower in ("true", "yes", "1"):
                return True
            elif lower in ("false", "no", "0"):
                return False
            return value
        else:
            return value

    def _update_preview_rules_list(self) -> None:
        """Update preview rules list (Phase F-9)."""
        if not self._preview_rules_list:
            return

        self._preview_rules_list.clear()

        rules = self._viewmodel.preview_control_rules
        results = self._viewmodel.preview_results

        if not rules:
            item = QListWidgetItem("No rules defined")
            item.setForeground(Qt.GlobalColor.gray)
            self._preview_rules_list.addItem(item)
            return

        for i, rule_input in enumerate(rules):
            # Get result if available
            result = results[i] if i < len(results) else None

            # Build display text
            status_icon = "✓" if result and result.is_allowed else "✗" if result and result.is_blocked else "?"
            text = f"{status_icon} {rule_input.rule_type.value}: {rule_input.target_field_id}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, i)

            # Set color based on status
            if result:
                if result.is_blocked:
                    item.setForeground(Qt.GlobalColor.red)
                    item.setToolTip(f"BLOCKED: {result.block_reason}")
                elif result.is_allowed:
                    exec_result = "True" if result.execution_result else "False"
                    item.setToolTip(
                        f"Formula: {rule_input.formula_text}\n"
                        f"Result: {exec_result}"
                    )
                    if result.execution_result:
                        item.setForeground(Qt.GlobalColor.darkGreen)
                    else:
                        item.setForeground(Qt.GlobalColor.darkYellow)

            self._preview_rules_list.addItem(item)

    def _update_preview_field_states(self) -> None:
        """Update field preview states list (Phase F-9)."""
        if not self._preview_field_states_list:
            return

        self._preview_field_states_list.clear()

        preview_state = self._viewmodel.preview_mode_state

        if not preview_state.field_states:
            item = QListWidgetItem("No field states")
            item.setForeground(Qt.GlobalColor.gray)
            self._preview_field_states_list.addItem(item)
            return

        for field_state in preview_state.field_states:
            # Build status indicators
            indicators = []
            if not field_state.is_visible:
                indicators.append("👁 Hidden")
            if not field_state.is_enabled:
                indicators.append("🔒 Disabled")
            if field_state.show_required_indicator:
                indicators.append("* Required")

            if indicators:
                text = f"{field_state.field_id}: {', '.join(indicators)}"
            else:
                text = f"{field_state.field_id}: (no effects)"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, field_state.field_id)

            # Build tooltip with details
            tooltip_parts = [
                f"Field: {field_state.field_id}",
                f"Visible: {'Yes' if field_state.is_visible else 'No'}",
                f"Enabled: {'Yes' if field_state.is_enabled else 'No'}",
                f"Required: {'Yes' if field_state.show_required_indicator else 'No'}",
            ]

            if field_state.applied_rules:
                tooltip_parts.append(f"\nApplied Rules: {', '.join(r.value for r in field_state.applied_rules)}")

            if field_state.blocked_rules:
                blocked = [f"{r[0].value}: {r[1]}" for r in field_state.blocked_rules]
                tooltip_parts.append(f"\nBlocked Rules:\n" + "\n".join(f"  - {b}" for b in blocked))

            item.setToolTip("\n".join(tooltip_parts))

            # Color code based on state
            if not field_state.is_visible:
                item.setForeground(Qt.GlobalColor.gray)
            elif not field_state.is_enabled:
                item.setForeground(Qt.GlobalColor.darkGray)
            elif field_state.show_required_indicator:
                item.setForeground(Qt.GlobalColor.darkRed)

            self._preview_field_states_list.addItem(item)

    def _on_add_preview_rule_clicked(self) -> None:
        """Handle Add Preview Rule button click (Phase F-9)."""
        # Show simple dialog to add a control rule
        from PyQt6.QtWidgets import QInputDialog

        # Get rule type
        rule_types = [rt.value for rt in ControlRuleType]
        rule_type_str, ok = QInputDialog.getItem(
            self._root,
            "Add Preview Rule",
            "Select rule type:",
            rule_types,
            0,
            False,
        )
        if not ok:
            return

        rule_type = ControlRuleType(rule_type_str)

        # Get target field
        fields = self._viewmodel.fields
        if not fields:
            QMessageBox.warning(
                self._root,
                "No Fields",
                "No fields available in the selected entity.",
            )
            return

        field_ids = [f.id for f in fields]
        target_field, ok = QInputDialog.getItem(
            self._root,
            "Add Preview Rule",
            "Select target field:",
            field_ids,
            0,
            False,
        )
        if not ok:
            return

        # Get formula
        formula, ok = QInputDialog.getText(
            self._root,
            "Add Preview Rule",
            f"Enter boolean formula for {rule_type_str}:\n"
            f"(e.g., 'field_name == \"value\"', 'count > 0')",
        )
        if not ok or not formula.strip():
            return

        # Add the rule
        self._viewmodel.add_preview_control_rule(
            rule_type=rule_type,
            target_field_id=target_field,
            formula_text=formula.strip(),
        )

        # Update the rules list
        self._update_preview_rules_list()

    def dispose(self) -> None:
        """Clean up resources."""
        # Phase F-1: Clean up formula editor widget
        if self._formula_editor_widget:
            self._formula_editor_widget.dispose()
            self._formula_editor_widget = None

        # Phase F-9: Clear preview field inputs
        self._preview_field_inputs.clear()

        # Unsubscribe from ViewModel
        if self._viewmodel:
            self._viewmodel.dispose()

        super().dispose()

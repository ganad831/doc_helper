"""Add Field Dialog (Phase 2 Step 2).

Dialog for adding field definitions to existing entities.

Phase 5: UX Polish
- Added tooltips to field type selector explaining each type
"""

from typing import Callable, Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QLabel,
    QWidget,
)
from PyQt6.QtCore import Qt

from doc_helper.presentation.utils.field_type_utils import normalize_field_type


class AddFieldDialog(QDialog):
    """Dialog for adding a new field to an entity.

    Phase 2 Step 2 Scope:
    - Simple form with: field ID, label key, field type, required flag
    - Field type dropdown with all 12 types
    - Basic validation (non-empty fields)
    - Returns field data as dict

    Phase A1: LOOKUP field support
    - When field_type == LOOKUP, show required lookup_entity_id dropdown
    - Optional lookup_display_field text input
    - Validation: LOOKUP fields must have lookup_entity_id

    NOT in Step 2:
    - Validation rule creation
    - Formula creation
    - Control rule creation
    - Options for DROPDOWN/RADIO fields
    - Display order customization

    Layout:
        Field ID: [text input]
        Label Key: [text input]
        Help Text Key: [text input]
        Field Type: [dropdown]
        Required: [checkbox]
        Default Value: [text input]

        --- LOOKUP Field Properties (shown when LOOKUP selected) ---
        Lookup Entity: [dropdown] (required)
        Lookup Display Field: [dropdown] (optional, filtered to valid types)

        [Cancel] [Add Field]
    """

    def __init__(
        self,
        entity_id: str,
        entity_name: str,
        available_entities: Optional[tuple[tuple[str, str], ...]] = None,
        get_valid_display_fields: Optional[Callable[[str], tuple[tuple[str, str], ...]]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize dialog.

        Args:
            entity_id: ID of entity to add field to (used to filter from LOOKUP dropdown)
            entity_name: Name of entity to add field to
            available_entities: List of (entity_id, entity_name) for LOOKUP dropdowns
            get_valid_display_fields: Callback to get valid display fields for an entity.
                Takes entity_id, returns tuple of (field_id, field_label).
                Used to populate the lookup display field dropdown with only valid types.
            parent: Parent widget
        """
        super().__init__(parent)
        self._entity_id = entity_id
        self._entity_name = entity_name
        self._available_entities = available_entities or ()
        self._get_valid_display_fields = get_valid_display_fields
        self.setWindowTitle(f"Add Field to {entity_name}")
        self.setModal(True)
        self.resize(500, 450)

        # Result data (populated on accept)
        self.field_data: Optional[dict] = None

        # LOOKUP field UI components (initialized in _build_ui)
        self._lookup_entity_combo: Optional[QComboBox] = None
        self._lookup_display_field_combo: Optional[QComboBox] = None
        self._lookup_section: Optional[QWidget] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            f"Add a new field to the '{self._entity_name}' entity. "
            "Field ID should be lowercase with underscores (e.g., 'sample_depth')."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info)

        # Form layout
        form = QFormLayout()

        # Field ID
        self._field_id_input = QLineEdit()
        self._field_id_input.setPlaceholderText("e.g., sample_depth")
        form.addRow("Field ID*:", self._field_id_input)

        # Label Key
        self._label_key_input = QLineEdit()
        self._label_key_input.setPlaceholderText("e.g., field.sample_depth")
        form.addRow("Label Key*:", self._label_key_input)

        # Help Text Key
        self._help_text_key_input = QLineEdit()
        self._help_text_key_input.setPlaceholderText("e.g., field.sample_depth.help")
        form.addRow("Help Text Key:", self._help_text_key_input)

        # Field Type (dropdown with all 12 types)
        # Phase 5: Added descriptive tooltips for each field type
        self._field_type_combo = QComboBox()

        # Define field types with their tooltips
        field_types_with_tooltips = [
            ("TEXT", "Single-line text input for short strings"),
            ("TEXTAREA", "Multi-line text input for longer content"),
            ("NUMBER", "Numeric input with optional decimal support"),
            ("DATE", "Date picker for selecting dates"),
            ("DROPDOWN", "Single selection from a predefined list of options"),
            ("CHECKBOX", "Boolean true/false toggle"),
            ("RADIO", "Single selection displayed as radio buttons"),
            ("CALCULATED", "Read-only value computed from other fields"),
            ("LOOKUP", "Value referenced from another entity"),
            ("FILE", "File attachment with upload support"),
            ("IMAGE", "Image attachment with preview support"),
            ("TABLE", "Nested tabular data with child records"),
        ]

        for field_type, tooltip in field_types_with_tooltips:
            self._field_type_combo.addItem(field_type)
            index = self._field_type_combo.count() - 1
            self._field_type_combo.setItemData(index, tooltip, Qt.ItemDataRole.ToolTipRole)

        # Set overall tooltip for the combo box
        self._field_type_combo.setToolTip("Select the data type for this field")
        form.addRow("Field Type*:", self._field_type_combo)

        # Required checkbox
        self._required_checkbox = QCheckBox("Field is required")
        self._required_checkbox.setToolTip(
            "If checked, this field must have a value.\n"
            "Empty values will trigger a validation error."
        )
        form.addRow("Required:", self._required_checkbox)

        # INVARIANT: CALCULATED fields cannot be required - update checkbox on type change
        self._field_type_combo.currentTextChanged.connect(self._on_field_type_changed)

        # Default Value
        self._default_value_input = QLineEdit()
        self._default_value_input.setPlaceholderText("Optional default value")
        form.addRow("Default Value:", self._default_value_input)

        layout.addLayout(form)

        # LOOKUP field properties section (hidden by default)
        self._lookup_section = QWidget()
        lookup_layout = QVBoxLayout(self._lookup_section)
        lookup_layout.setContentsMargins(0, 10, 0, 0)

        lookup_label = QLabel("--- LOOKUP Field Properties ---")
        lookup_label.setStyleSheet("color: #4a5568; font-weight: bold;")
        lookup_layout.addWidget(lookup_label)

        lookup_form = QFormLayout()

        self._lookup_entity_combo = QComboBox()
        self._lookup_entity_combo.addItem("(Select entity)*", "")
        for eid, ename in self._available_entities:
            # Filter out current entity - UX safety only (enforcement is at UseCases layer)
            if eid == self._entity_id:
                continue
            self._lookup_entity_combo.addItem(f"{ename} ({eid})", eid)
        self._lookup_entity_combo.setToolTip(
            "Select the entity to lookup values from (required)"
        )
        self._lookup_entity_combo.currentIndexChanged.connect(
            self._on_lookup_entity_changed
        )
        lookup_form.addRow("Lookup Entity*:", self._lookup_entity_combo)

        self._lookup_display_field_combo = QComboBox()
        self._lookup_display_field_combo.addItem("(None)", "")
        self._lookup_display_field_combo.setToolTip(
            "Field from the lookup entity to display (optional).\n"
            "Only user-readable fields are shown (not CALCULATED, TABLE, FILE, IMAGE)."
        )
        lookup_form.addRow("Display Field:", self._lookup_display_field_combo)

        lookup_layout.addLayout(lookup_form)
        layout.addWidget(self._lookup_section)
        self._lookup_section.hide()  # Hidden by default

        # Note about next steps
        note = QLabel(
            "Tip: After adding this field, you can add validation constraints "
            "(Required, Min/Max, Pattern, etc.) from the main Schema Designer view."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
        layout.addWidget(note)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        add_button = QPushButton("Add Field")
        add_button.setDefault(True)
        add_button.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(add_button)

        layout.addLayout(button_layout)

    def _on_field_type_changed(self, field_type: str) -> None:
        """Handle field type change.

        - Disable Required for CALCULATED fields (invariant)
        - Show/hide LOOKUP section for LOOKUP fields
        """
        field_type_normalized = normalize_field_type(field_type)

        # INVARIANT: CALCULATED fields cannot be required
        if field_type_normalized == "calculated":
            self._required_checkbox.setChecked(False)
            self._required_checkbox.setEnabled(False)
            self._required_checkbox.setToolTip(
                "CALCULATED fields cannot be required. "
                "They derive their values from formulas."
            )
        else:
            self._required_checkbox.setEnabled(True)
            self._required_checkbox.setToolTip(
                "If checked, this field must have a value.\n"
                "Empty values will trigger a validation error."
            )

        # Show/hide LOOKUP section
        if self._lookup_section:
            if field_type_normalized == "lookup":
                self._lookup_section.show()
            else:
                self._lookup_section.hide()

    def _on_lookup_entity_changed(self, index: int) -> None:
        """Handle lookup entity selection change.

        Updates the display field dropdown with valid fields from the selected entity.
        Only fields with user-readable types are shown (not CALCULATED, TABLE, FILE, IMAGE).
        """
        if not self._lookup_display_field_combo:
            return

        # Clear existing items
        self._lookup_display_field_combo.clear()
        self._lookup_display_field_combo.addItem("(None)", "")

        # Get selected entity ID
        if not self._lookup_entity_combo:
            return

        selected_entity_id = self._lookup_entity_combo.currentData()
        if not selected_entity_id:
            return

        # Get valid display fields via callback
        if self._get_valid_display_fields:
            valid_fields = self._get_valid_display_fields(selected_entity_id)
            for field_id, field_label in valid_fields:
                self._lookup_display_field_combo.addItem(
                    f"{field_label} ({field_id})", field_id
                )

    def _on_add_clicked(self) -> None:
        """Handle add button click."""
        # Validate inputs
        field_id = self._field_id_input.text().strip()
        label_key = self._label_key_input.text().strip()
        help_text_key = self._help_text_key_input.text().strip()
        field_type = normalize_field_type(self._field_type_combo.currentText())
        required = self._required_checkbox.isChecked()
        default_value = self._default_value_input.text().strip()

        # Validation
        if not field_id:
            QMessageBox.warning(self, "Validation Error", "Field ID is required")
            self._field_id_input.setFocus()
            return

        if not label_key:
            QMessageBox.warning(self, "Validation Error", "Label Key is required")
            self._label_key_input.setFocus()
            return

        # Validate field_id format (lowercase, underscores, alphanumeric)
        if not field_id.replace("_", "").isalnum():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Field ID must contain only letters, numbers, and underscores",
            )
            self._field_id_input.setFocus()
            return

        if field_id[0].isdigit():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Field ID cannot start with a number",
            )
            self._field_id_input.setFocus()
            return

        # LOOKUP field validation - lookup_entity_id is required
        lookup_entity_id = None
        lookup_display_field = None
        if field_type == "lookup":
            if self._lookup_entity_combo:
                lookup_entity_id = self._lookup_entity_combo.currentData()
                if not lookup_entity_id:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "LOOKUP fields require a Lookup Entity.\n"
                        "Please select an entity to lookup values from.",
                    )
                    self._lookup_entity_combo.setFocus()
                    return
            if self._lookup_display_field_combo:
                lookup_display_field = self._lookup_display_field_combo.currentData()
                lookup_display_field = lookup_display_field if lookup_display_field else None

        # Store result
        self.field_data = {
            "field_id": field_id,
            "label_key": label_key,
            "help_text_key": help_text_key if help_text_key else None,
            "field_type": field_type,
            "required": required,
            "default_value": default_value if default_value else None,
            "lookup_entity_id": lookup_entity_id,
            "lookup_display_field": lookup_display_field,
        }

        self.accept()

    def get_field_data(self) -> Optional[dict]:
        """Get field data if dialog was accepted.

        Returns:
            Dict with field data or None if cancelled
        """
        return self.field_data

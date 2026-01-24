"""Edit Field Dialog (Phase SD-4).

Dialog for editing existing field definitions.

Phase SD-4 Scope:
- Edit field metadata (label key, help text key, required, default value)
- Edit type-specific properties (formula, lookup, child entity)
- Field ID and Field Type are read-only (immutable)
- Pre-populate with current values

NOT in scope:
- Field type changes (immutable per Decision 1)
- Constraint editing (separate dialog)
- Option editing for choice fields
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class EditFieldDialog(QDialog):
    """Dialog for editing an existing field.

    Phase SD-4: Edit field metadata.

    Layout:
        Entity ID: [read-only text]
        Field ID: [read-only text]
        Field Type: [read-only text]
        Label Key: [text input]
        Help Text Key: [text input]
        Required: [checkbox]
        Default Value: [text input]

        --- Type-specific (shown conditionally) ---
        Formula: [text input] (CALCULATED only)
        Lookup Entity: [dropdown] (LOOKUP only)
        Lookup Display Field: [text input] (LOOKUP only)
        Child Entity: [dropdown] (TABLE only)

        [Cancel] [Save Changes]
    """

    def __init__(
        self,
        entity_id: str,
        field_id: str,
        field_type: str,
        current_label_key: str,
        current_help_text_key: Optional[str],
        current_required: bool,
        current_default_value: Optional[str],
        current_formula: Optional[str] = None,
        current_lookup_entity_id: Optional[str] = None,
        current_lookup_display_field: Optional[str] = None,
        current_child_entity_id: Optional[str] = None,
        available_entities: Optional[tuple[tuple[str, str], ...]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize dialog.

        Args:
            entity_id: Parent entity ID (read-only)
            field_id: Field ID (read-only)
            field_type: Field type (read-only)
            current_label_key: Current label translation key
            current_help_text_key: Current help text translation key
            current_required: Current required flag
            current_default_value: Current default value
            current_formula: Current formula (CALCULATED fields)
            current_lookup_entity_id: Current lookup entity (LOOKUP fields)
            current_lookup_display_field: Current lookup display field (LOOKUP fields)
            current_child_entity_id: Current child entity (TABLE fields)
            available_entities: List of (entity_id, entity_name) for dropdowns
            parent: Parent widget
        """
        super().__init__(parent)
        self._entity_id = entity_id
        self._field_id = field_id
        self._field_type = field_type
        self._available_entities = available_entities or ()

        self.setWindowTitle(f"Edit Field: {field_id}")
        self.setModal(True)
        self.resize(550, 450)

        # Result data (populated on accept)
        self.field_data: Optional[dict] = None

        # Build UI
        self._build_ui(
            current_label_key,
            current_help_text_key,
            current_required,
            current_default_value,
            current_formula,
            current_lookup_entity_id,
            current_lookup_display_field,
            current_child_entity_id,
        )

    def _build_ui(
        self,
        current_label_key: str,
        current_help_text_key: Optional[str],
        current_required: bool,
        current_default_value: Optional[str],
        current_formula: Optional[str],
        current_lookup_entity_id: Optional[str],
        current_lookup_display_field: Optional[str],
        current_child_entity_id: Optional[str],
    ) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            "Edit field metadata. Field ID and Type cannot be changed."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info)

        # Form layout
        form = QFormLayout()

        # Entity ID (read-only)
        entity_id_display = QLineEdit(self._entity_id)
        entity_id_display.setReadOnly(True)
        entity_id_display.setStyleSheet(
            "background-color: #f0f0f0; color: #666;"
        )
        form.addRow("Entity ID:", entity_id_display)

        # Field ID (read-only)
        field_id_display = QLineEdit(self._field_id)
        field_id_display.setReadOnly(True)
        field_id_display.setStyleSheet(
            "background-color: #f0f0f0; color: #666;"
        )
        form.addRow("Field ID:", field_id_display)

        # Field Type (read-only)
        field_type_display = QLineEdit(self._field_type)
        field_type_display.setReadOnly(True)
        field_type_display.setStyleSheet(
            "background-color: #f0f0f0; color: #666;"
        )
        form.addRow("Field Type:", field_type_display)

        # Label Key
        self._label_key_input = QLineEdit()
        self._label_key_input.setText(current_label_key)
        self._label_key_input.setPlaceholderText("e.g., field.sample_depth")
        form.addRow("Label Key*:", self._label_key_input)

        # Help Text Key
        self._help_text_key_input = QLineEdit()
        self._help_text_key_input.setText(current_help_text_key or "")
        self._help_text_key_input.setPlaceholderText(
            "e.g., field.sample_depth.help"
        )
        form.addRow("Help Text Key:", self._help_text_key_input)

        # Required
        self._required_checkbox = QCheckBox("Field is required")
        self._required_checkbox.setChecked(current_required)
        form.addRow("Required:", self._required_checkbox)

        # Default Value
        self._default_value_input = QLineEdit()
        self._default_value_input.setText(current_default_value or "")
        self._default_value_input.setPlaceholderText("Optional default value")
        form.addRow("Default Value:", self._default_value_input)

        layout.addLayout(form)

        # Type-specific section
        self._add_type_specific_fields(
            layout,
            current_formula,
            current_lookup_entity_id,
            current_lookup_display_field,
            current_child_entity_id,
        )

        # Stretch to push buttons to bottom
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save Changes")
        save_button.setDefault(True)
        save_button.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

    def _add_type_specific_fields(
        self,
        layout: QVBoxLayout,
        current_formula: Optional[str],
        current_lookup_entity_id: Optional[str],
        current_lookup_display_field: Optional[str],
        current_child_entity_id: Optional[str],
    ) -> None:
        """Add type-specific fields based on field type."""
        # Initialize optional attributes
        self._formula_input: Optional[QLineEdit] = None
        self._lookup_entity_combo: Optional[QComboBox] = None
        self._lookup_display_field_input: Optional[QLineEdit] = None
        self._child_entity_combo: Optional[QComboBox] = None

        if self._field_type == "CALCULATED":
            # Formula section
            formula_form = QFormLayout()
            formula_label = QLabel("--- CALCULATED Field Properties ---")
            formula_label.setStyleSheet("color: #4a5568; font-weight: bold; margin-top: 10px;")
            layout.addWidget(formula_label)

            self._formula_input = QLineEdit()
            self._formula_input.setText(current_formula or "")
            self._formula_input.setPlaceholderText("e.g., {{field1}} + {{field2}}")
            formula_form.addRow("Formula:", self._formula_input)
            layout.addLayout(formula_form)

        elif self._field_type == "LOOKUP":
            # Lookup section
            lookup_form = QFormLayout()
            lookup_label = QLabel("--- LOOKUP Field Properties ---")
            lookup_label.setStyleSheet("color: #4a5568; font-weight: bold; margin-top: 10px;")
            layout.addWidget(lookup_label)

            self._lookup_entity_combo = QComboBox()
            self._lookup_entity_combo.addItem("(None)", "")
            for entity_id, entity_name in self._available_entities:
                self._lookup_entity_combo.addItem(f"{entity_name} ({entity_id})", entity_id)
            # Set current selection
            if current_lookup_entity_id:
                index = self._lookup_entity_combo.findData(current_lookup_entity_id)
                if index >= 0:
                    self._lookup_entity_combo.setCurrentIndex(index)
            lookup_form.addRow("Lookup Entity:", self._lookup_entity_combo)

            self._lookup_display_field_input = QLineEdit()
            self._lookup_display_field_input.setText(current_lookup_display_field or "")
            self._lookup_display_field_input.setPlaceholderText("e.g., name")
            lookup_form.addRow("Display Field:", self._lookup_display_field_input)
            layout.addLayout(lookup_form)

        elif self._field_type == "TABLE":
            # Table section
            table_form = QFormLayout()
            table_label = QLabel("--- TABLE Field Properties ---")
            table_label.setStyleSheet("color: #4a5568; font-weight: bold; margin-top: 10px;")
            layout.addWidget(table_label)

            self._child_entity_combo = QComboBox()
            self._child_entity_combo.addItem("(None)", "")
            for entity_id, entity_name in self._available_entities:
                self._child_entity_combo.addItem(f"{entity_name} ({entity_id})", entity_id)
            # Set current selection
            if current_child_entity_id:
                index = self._child_entity_combo.findData(current_child_entity_id)
                if index >= 0:
                    self._child_entity_combo.setCurrentIndex(index)
            table_form.addRow("Child Entity:", self._child_entity_combo)
            layout.addLayout(table_form)

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        # Validate inputs
        label_key = self._label_key_input.text().strip()
        help_text_key = self._help_text_key_input.text().strip()
        required = self._required_checkbox.isChecked()
        default_value = self._default_value_input.text().strip()

        # Validation
        if not label_key:
            QMessageBox.warning(self, "Validation Error", "Label Key is required")
            self._label_key_input.setFocus()
            return

        # Store result
        self.field_data = {
            "entity_id": self._entity_id,
            "field_id": self._field_id,
            "label_key": label_key,
            "help_text_key": help_text_key if help_text_key else None,
            "required": required,
            "default_value": default_value if default_value else None,
        }

        # Add type-specific data
        if self._field_type == "CALCULATED" and self._formula_input:
            formula = self._formula_input.text().strip()
            self.field_data["formula"] = formula if formula else None

        elif self._field_type == "LOOKUP":
            if self._lookup_entity_combo:
                lookup_entity_id = self._lookup_entity_combo.currentData()
                self.field_data["lookup_entity_id"] = lookup_entity_id if lookup_entity_id else None
            if self._lookup_display_field_input:
                lookup_display_field = self._lookup_display_field_input.text().strip()
                self.field_data["lookup_display_field"] = lookup_display_field if lookup_display_field else None

        elif self._field_type == "TABLE" and self._child_entity_combo:
            child_entity_id = self._child_entity_combo.currentData()
            self.field_data["child_entity_id"] = child_entity_id if child_entity_id else None

        self.accept()

    def get_field_data(self) -> Optional[dict]:
        """Get field data if dialog was accepted.

        Returns:
            Dict with field data or None if cancelled
        """
        return self.field_data

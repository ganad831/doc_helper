"""Add Field Dialog (Phase 2 Step 2).

Dialog for adding field definitions to existing entities.

Phase 5: UX Polish
- Added tooltips to field type selector explaining each type
"""

from typing import Optional

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


class AddFieldDialog(QDialog):
    """Dialog for adding a new field to an entity.

    Phase 2 Step 2 Scope:
    - Simple form with: field ID, label key, field type, required flag
    - Field type dropdown with all 12 types
    - Basic validation (non-empty fields)
    - Returns field data as dict

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

        [Cancel] [Add Field]
    """

    def __init__(
        self,
        entity_name: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize dialog.

        Args:
            entity_name: Name of entity to add field to
            parent: Parent widget
        """
        super().__init__(parent)
        self._entity_name = entity_name
        self.setWindowTitle(f"Add Field to {entity_name}")
        self.setModal(True)
        self.resize(500, 400)

        # Result data (populated on accept)
        self.field_data: Optional[dict] = None

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
        """Handle field type change - disable Required for CALCULATED fields.

        INVARIANT: CALCULATED fields cannot be required because they derive
        their values from formulas, not user input.
        """
        if field_type.upper() == "CALCULATED":
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

    def _on_add_clicked(self) -> None:
        """Handle add button click."""
        # Validate inputs
        field_id = self._field_id_input.text().strip()
        label_key = self._label_key_input.text().strip()
        help_text_key = self._help_text_key_input.text().strip()
        field_type = self._field_type_combo.currentText().lower()
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

        # Store result
        self.field_data = {
            "field_id": field_id,
            "label_key": label_key,
            "help_text_key": help_text_key if help_text_key else None,
            "field_type": field_type,
            "required": required,
            "default_value": default_value if default_value else None,
        }

        self.accept()

    def get_field_data(self) -> Optional[dict]:
        """Get field data if dialog was accepted.

        Returns:
            Dict with field data or None if cancelled
        """
        return self.field_data

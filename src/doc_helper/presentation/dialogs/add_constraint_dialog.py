"""Add Constraint Dialog (Phase SD-2).

Dialog for adding validation constraints to fields.

Phase SD-2 Scope:
- Constraint type selector
- Dynamic value input based on constraint type
- Severity selection (ERROR, WARNING, INFO)
- Support for: Required, MinValue, MaxValue, MinLength, MaxLength

NOT in scope:
- No Pattern/regex constraint
- No editing existing constraints
- No deleting constraints
- No domain layer changes
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


# Constraint type definitions (UI only - no domain imports)
CONSTRAINT_TYPES = {
    "REQUIRED": {
        "label": "Required",
        "description": "Field value must not be empty",
        "has_value": False,
        "value_type": None,
    },
    "MIN_VALUE": {
        "label": "Minimum Value",
        "description": "Field value must be >= specified value",
        "has_value": True,
        "value_type": "float",
    },
    "MAX_VALUE": {
        "label": "Maximum Value",
        "description": "Field value must be <= specified value",
        "has_value": True,
        "value_type": "float",
    },
    "MIN_LENGTH": {
        "label": "Minimum Length",
        "description": "Field value must have >= specified characters",
        "has_value": True,
        "value_type": "int",
    },
    "MAX_LENGTH": {
        "label": "Maximum Length",
        "description": "Field value must have <= specified characters",
        "has_value": True,
        "value_type": "int",
    },
}

SEVERITY_OPTIONS = {
    "ERROR": "Error - Blocks workflow",
    "WARNING": "Warning - Requires confirmation",
    "INFO": "Info - Informational only",
}


class AddConstraintDialog(QDialog):
    """Dialog for adding a validation constraint to a field.

    Phase SD-2: Add Constraint UI for Schema Designer.

    Layout:
        Constraint Type: [dropdown]
        [Description of selected type]
        Value: [input - shown only when needed]
        Severity: [dropdown]

        [Cancel] [Add Constraint]
    """

    def __init__(
        self,
        field_id: str,
        field_label: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize dialog.

        Args:
            field_id: ID of the field to add constraint to
            field_label: Human-readable label of the field
            parent: Parent widget
        """
        super().__init__(parent)
        self._field_id = field_id
        self._field_label = field_label

        self.setWindowTitle("Add Validation Constraint")
        self.setModal(True)
        self.resize(450, 300)

        # Result data (populated on accept)
        self.constraint_data: Optional[dict] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Field info
        field_info = QLabel(f"Adding constraint to field: <b>{self._field_label}</b>")
        field_info.setStyleSheet("padding: 10px;")
        layout.addWidget(field_info)

        # Form layout
        form = QFormLayout()

        # Constraint type dropdown
        self._type_combo = QComboBox()
        for type_id, type_info in CONSTRAINT_TYPES.items():
            self._type_combo.addItem(type_info["label"], type_id)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Constraint Type:", self._type_combo)

        # Description label (updates based on selected type)
        self._description_label = QLabel()
        self._description_label.setWordWrap(True)
        self._description_label.setStyleSheet("color: gray; font-style: italic; padding: 5px;")
        form.addRow("", self._description_label)

        # Value input - integer (for length constraints)
        self._int_value_input = QSpinBox()
        self._int_value_input.setRange(0, 999999)
        self._int_value_input.setValue(0)
        self._int_value_label = QLabel("Value:")
        form.addRow(self._int_value_label, self._int_value_input)

        # Value input - float (for min/max value constraints)
        self._float_value_input = QDoubleSpinBox()
        self._float_value_input.setRange(-999999999.0, 999999999.0)
        self._float_value_input.setDecimals(4)
        self._float_value_input.setValue(0.0)
        self._float_value_label = QLabel("Value:")
        form.addRow(self._float_value_label, self._float_value_input)

        # Severity dropdown
        self._severity_combo = QComboBox()
        for sev_id, sev_label in SEVERITY_OPTIONS.items():
            self._severity_combo.addItem(sev_label, sev_id)
        # Default to ERROR
        self._severity_combo.setCurrentIndex(0)
        form.addRow("Severity:", self._severity_combo)

        layout.addLayout(form)

        # Stretch
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        self._add_button = QPushButton("Add Constraint")
        self._add_button.setDefault(True)
        self._add_button.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(self._add_button)

        layout.addLayout(button_layout)

        # Initialize UI state
        self._on_type_changed(0)

    def _on_type_changed(self, index: int) -> None:
        """Handle constraint type selection change."""
        type_id = self._type_combo.currentData()
        type_info = CONSTRAINT_TYPES.get(type_id, {})

        # Update description
        description = type_info.get("description", "")
        self._description_label.setText(description)

        # Show/hide value inputs based on type
        has_value = type_info.get("has_value", False)
        value_type = type_info.get("value_type")

        # Hide both value inputs initially
        self._int_value_label.setVisible(False)
        self._int_value_input.setVisible(False)
        self._float_value_label.setVisible(False)
        self._float_value_input.setVisible(False)

        if has_value:
            if value_type == "int":
                self._int_value_label.setVisible(True)
                self._int_value_input.setVisible(True)
            elif value_type == "float":
                self._float_value_label.setVisible(True)
                self._float_value_input.setVisible(True)

    def _on_add_clicked(self) -> None:
        """Handle Add Constraint button click."""
        type_id = self._type_combo.currentData()
        type_info = CONSTRAINT_TYPES.get(type_id, {})

        # Get value if needed
        value = None
        if type_info.get("has_value", False):
            value_type = type_info.get("value_type")
            if value_type == "int":
                value = self._int_value_input.value()
            elif value_type == "float":
                value = self._float_value_input.value()

            # Validate value for length constraints
            if value_type == "int" and value < 0:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Length value must be >= 0",
                )
                return

        # Get severity
        severity = self._severity_combo.currentData()

        # Store result
        self.constraint_data = {
            "constraint_type": type_id,
            "value": value,
            "severity": severity,
        }

        self.accept()

    def get_constraint_data(self) -> Optional[dict]:
        """Get constraint data if dialog was accepted.

        Returns:
            Dict with constraint parameters or None if cancelled:
            - constraint_type: str (REQUIRED, MIN_VALUE, etc.)
            - value: Optional[float] (None for REQUIRED)
            - severity: str (ERROR, WARNING, INFO)
        """
        return self.constraint_data

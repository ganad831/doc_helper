"""Add Constraint Dialog (Phase SD-2, Extended in SD-6).

Dialog for adding validation constraints to fields.

Phase SD-2 Scope:
- Constraint type selector
- Dynamic value input based on constraint type
- Severity selection (ERROR, WARNING, INFO)
- Support for: Required, MinValue, MaxValue, MinLength, MaxLength

Phase SD-6 Extensions:
- Field-type-aware constraint filtering
- Pattern constraint with regex input and description
- AllowedValues constraint with multi-value input
- FileExtension constraint with extension list
- MaxFileSize constraint with unit selector (KB/MB/GB)
- Date picker for date field Min/Max constraints
"""

from typing import Optional

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from doc_helper.presentation.utils.constraint_availability import (
    get_allowed_constraints,
)


# Constraint type definitions (UI only - no domain imports)
# Extended in Phase SD-6 with additional constraints
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
        "value_type": "float",  # or "date" for date fields
    },
    "MAX_VALUE": {
        "label": "Maximum Value",
        "description": "Field value must be <= specified value",
        "has_value": True,
        "value_type": "float",  # or "date" for date fields
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
    # Phase SD-6: Advanced constraints
    "PATTERN": {
        "label": "Pattern (Regex)",
        "description": "Field value must match the specified regular expression",
        "has_value": True,
        "value_type": "pattern",
    },
    "ALLOWED_VALUES": {
        "label": "Allowed Values",
        "description": "Field value must be one of the specified values",
        "has_value": True,
        "value_type": "values_list",
    },
    "FILE_EXTENSION": {
        "label": "File Extension",
        "description": "File must have one of the specified extensions",
        "has_value": True,
        "value_type": "extension_list",
    },
    "MAX_FILE_SIZE": {
        "label": "Maximum File Size",
        "description": "File size must not exceed the specified limit",
        "has_value": True,
        "value_type": "file_size",
    },
}

SEVERITY_OPTIONS = {
    "ERROR": "Error - Blocks workflow",
    "WARNING": "Warning - Requires confirmation",
    "INFO": "Info - Informational only",
}

# File size units for MaxFileSize constraint
FILE_SIZE_UNITS = {
    "KB": 1024,
    "MB": 1024 * 1024,
    "GB": 1024 * 1024 * 1024,
}


class AddConstraintDialog(QDialog):
    """Dialog for adding a validation constraint to a field.

    Phase SD-2: Add Constraint UI for Schema Designer.
    Phase SD-6: Extended with field-type filtering and advanced constraints.

    Layout:
        Constraint Type: [dropdown - filtered by field type]
        [Description of selected type]
        Value: [input - dynamic based on constraint type]
        Severity: [dropdown]

        [Cancel] [Add Constraint]
    """

    def __init__(
        self,
        field_id: str,
        field_label: str,
        field_type: str = "text",  # Phase SD-6: field type for filtering
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize dialog.

        Args:
            field_id: ID of the field to add constraint to
            field_label: Human-readable label of the field
            field_type: Field type (text, number, date, etc.) for constraint filtering
            parent: Parent widget
        """
        super().__init__(parent)
        self._field_id = field_id
        self._field_label = field_label
        self._field_type = field_type.lower()

        self.setWindowTitle("Add Validation Constraint")
        self.setModal(True)
        self.resize(500, 400)

        # Result data (populated on accept)
        self.constraint_data: Optional[dict] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Field info
        field_info = QLabel(
            f"Adding constraint to field: <b>{self._field_label}</b> "
            f"(Type: {self._field_type.upper()})"
        )
        field_info.setStyleSheet("padding: 10px;")
        layout.addWidget(field_info)

        # Form layout
        form = QFormLayout()

        # Constraint type dropdown - filtered by field type
        self._type_combo = QComboBox()
        allowed_constraints = get_allowed_constraints(self._field_type)
        for type_id, type_info in CONSTRAINT_TYPES.items():
            if type_id in allowed_constraints:
                self._type_combo.addItem(type_info["label"], type_id)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Constraint Type:", self._type_combo)

        # Description label (updates based on selected type)
        self._description_label = QLabel()
        self._description_label.setWordWrap(True)
        self._description_label.setStyleSheet(
            "color: gray; font-style: italic; padding: 5px;"
        )
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

        # Phase SD-6: Date input (for date field min/max constraints)
        self._date_value_input = QDateEdit()
        self._date_value_input.setCalendarPopup(True)
        self._date_value_input.setDate(QDate.currentDate())
        self._date_value_label = QLabel("Date:")
        form.addRow(self._date_value_label, self._date_value_input)

        # Phase SD-6: Pattern input (regex + description)
        self._pattern_input = QLineEdit()
        self._pattern_input.setPlaceholderText("e.g., ^[A-Z]{2}\\d{4}$")
        self._pattern_label = QLabel("Pattern (Regex):")
        form.addRow(self._pattern_label, self._pattern_input)

        self._pattern_desc_input = QLineEdit()
        self._pattern_desc_input.setPlaceholderText(
            "e.g., Must be 2 letters followed by 4 digits"
        )
        self._pattern_desc_label = QLabel("Pattern Description:")
        form.addRow(self._pattern_desc_label, self._pattern_desc_input)

        # Phase SD-6: Allowed values input (multi-line, one per line)
        self._values_input = QTextEdit()
        self._values_input.setPlaceholderText(
            "Enter one value per line:\nValue 1\nValue 2\nValue 3"
        )
        self._values_input.setMaximumHeight(100)
        self._values_label = QLabel("Allowed Values:")
        form.addRow(self._values_label, self._values_input)

        # Phase SD-6: File extension input (comma-separated)
        self._extensions_input = QLineEdit()
        self._extensions_input.setPlaceholderText("e.g., .pdf, .doc, .docx")
        self._extensions_label = QLabel("Allowed Extensions:")
        form.addRow(self._extensions_label, self._extensions_input)

        # Phase SD-6: File size input with unit selector
        file_size_layout = QHBoxLayout()
        self._file_size_input = QSpinBox()
        self._file_size_input.setRange(1, 999999)
        self._file_size_input.setValue(10)
        file_size_layout.addWidget(self._file_size_input)

        self._file_size_unit = QComboBox()
        for unit in FILE_SIZE_UNITS.keys():
            self._file_size_unit.addItem(unit)
        self._file_size_unit.setCurrentText("MB")
        file_size_layout.addWidget(self._file_size_unit)

        file_size_widget = QWidget()
        file_size_widget.setLayout(file_size_layout)
        self._file_size_label = QLabel("Maximum Size:")
        form.addRow(self._file_size_label, file_size_widget)
        self._file_size_widget = file_size_widget

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
        if self._type_combo.count() > 0:
            self._on_type_changed(0)
        else:
            # No constraints available for this field type
            self._hide_all_value_inputs()
            no_constraints_msg = "No constraints available for this field type."
            # Add explanatory message for specific field types
            if self._field_type == "checkbox":
                no_constraints_msg += (
                    "\n\nCheckbox fields are boolean (true/false) "
                    "and do not support validation constraints."
                )
            elif self._field_type == "calculated":
                no_constraints_msg += (
                    "\n\nCalculated fields are read-only and derive their value "
                    "from formulas, so constraints are not applicable."
                )
            self._description_label.setText(no_constraints_msg)
            self._add_button.setEnabled(False)

    def _hide_all_value_inputs(self) -> None:
        """Hide all value input widgets."""
        self._int_value_label.setVisible(False)
        self._int_value_input.setVisible(False)
        self._float_value_label.setVisible(False)
        self._float_value_input.setVisible(False)
        self._date_value_label.setVisible(False)
        self._date_value_input.setVisible(False)
        self._pattern_label.setVisible(False)
        self._pattern_input.setVisible(False)
        self._pattern_desc_label.setVisible(False)
        self._pattern_desc_input.setVisible(False)
        self._values_label.setVisible(False)
        self._values_input.setVisible(False)
        self._extensions_label.setVisible(False)
        self._extensions_input.setVisible(False)
        self._file_size_label.setVisible(False)
        self._file_size_widget.setVisible(False)

    def _on_type_changed(self, index: int) -> None:
        """Handle constraint type selection change."""
        type_id = self._type_combo.currentData()
        type_info = CONSTRAINT_TYPES.get(type_id, {})

        # Update description
        description = type_info.get("description", "")
        self._description_label.setText(description)

        # Hide all value inputs first
        self._hide_all_value_inputs()

        # Show appropriate input based on type
        has_value = type_info.get("has_value", False)
        value_type = type_info.get("value_type")

        if has_value:
            if value_type == "int":
                self._int_value_label.setVisible(True)
                self._int_value_input.setVisible(True)
            elif value_type == "float":
                # For date fields, show date picker instead
                if self._field_type == "date" and type_id in ("MIN_VALUE", "MAX_VALUE"):
                    self._date_value_label.setVisible(True)
                    self._date_value_input.setVisible(True)
                else:
                    self._float_value_label.setVisible(True)
                    self._float_value_input.setVisible(True)
            elif value_type == "pattern":
                self._pattern_label.setVisible(True)
                self._pattern_input.setVisible(True)
                self._pattern_desc_label.setVisible(True)
                self._pattern_desc_input.setVisible(True)
            elif value_type == "values_list":
                self._values_label.setVisible(True)
                self._values_input.setVisible(True)
            elif value_type == "extension_list":
                self._extensions_label.setVisible(True)
                self._extensions_input.setVisible(True)
            elif value_type == "file_size":
                self._file_size_label.setVisible(True)
                self._file_size_widget.setVisible(True)

    def _on_add_clicked(self) -> None:
        """Handle Add Constraint button click."""
        type_id = self._type_combo.currentData()
        type_info = CONSTRAINT_TYPES.get(type_id, {})

        # Initialize result data
        result: dict = {
            "constraint_type": type_id,
            "value": None,
            "severity": self._severity_combo.currentData(),
            # Phase SD-6: Additional fields
            "pattern": None,
            "pattern_description": None,
            "allowed_values": None,
            "allowed_extensions": None,
            "max_size_bytes": None,
        }

        # Get value based on constraint type
        if type_info.get("has_value", False):
            value_type = type_info.get("value_type")

            if value_type == "int":
                result["value"] = self._int_value_input.value()
                if result["value"] < 0:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "Length value must be >= 0",
                    )
                    return

            elif value_type == "float":
                # For date fields, get date value
                if self._field_type == "date" and type_id in ("MIN_VALUE", "MAX_VALUE"):
                    # Store date as ISO string for use-case
                    result["value"] = self._date_value_input.date().toString(
                        Qt.DateFormat.ISODate
                    )
                else:
                    result["value"] = self._float_value_input.value()

            elif value_type == "pattern":
                pattern = self._pattern_input.text().strip()
                if not pattern:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "Pattern (regex) is required",
                    )
                    return
                result["pattern"] = pattern
                result["pattern_description"] = (
                    self._pattern_desc_input.text().strip() or None
                )

            elif value_type == "values_list":
                # Parse multi-line input
                values_text = self._values_input.toPlainText().strip()
                if not values_text:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "At least one allowed value is required",
                    )
                    return
                values = tuple(
                    v.strip() for v in values_text.split("\n") if v.strip()
                )
                if not values:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "At least one allowed value is required",
                    )
                    return
                result["allowed_values"] = values

            elif value_type == "extension_list":
                # Parse comma-separated extensions
                ext_text = self._extensions_input.text().strip()
                if not ext_text:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "At least one file extension is required",
                    )
                    return
                extensions = tuple(
                    ext.strip().lower()
                    for ext in ext_text.split(",")
                    if ext.strip()
                )
                # Ensure extensions start with dot
                extensions = tuple(
                    ext if ext.startswith(".") else f".{ext}"
                    for ext in extensions
                )
                if not extensions:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "At least one file extension is required",
                    )
                    return
                result["allowed_extensions"] = extensions

            elif value_type == "file_size":
                size_value = self._file_size_input.value()
                unit = self._file_size_unit.currentText()
                multiplier = FILE_SIZE_UNITS.get(unit, 1024 * 1024)
                result["max_size_bytes"] = size_value * multiplier

        # Store result
        self.constraint_data = result
        self.accept()

    def get_constraint_data(self) -> Optional[dict]:
        """Get constraint data if dialog was accepted.

        Returns:
            Dict with constraint parameters or None if cancelled:
            - constraint_type: str (REQUIRED, MIN_VALUE, etc.)
            - value: Optional[float] (None for REQUIRED, string for date)
            - severity: str (ERROR, WARNING, INFO)

            Phase SD-6 additions:
            - pattern: Optional[str] (regex pattern for PATTERN constraint)
            - pattern_description: Optional[str] (human-readable description)
            - allowed_values: Optional[tuple] (for ALLOWED_VALUES constraint)
            - allowed_extensions: Optional[tuple] (for FILE_EXTENSION constraint)
            - max_size_bytes: Optional[int] (for MAX_FILE_SIZE constraint)
        """
        return self.constraint_data

"""Control Rule Add/Edit Dialog (Phase F-12).

UI-only dialog for adding or editing persisted control rules.
Routes all operations through SchemaDesignerViewModel (Rule 0 compliant).

PHASE F-12 CONSTRAINTS:
- NO business logic
- NO validation logic (ViewModel handles via SchemaUseCases)
- NO execution logic
- NO domain/application layer imports (DTOs only)
- Design-time only, no runtime enforcement

FORBIDDEN:
- Import commands, queries, repositories
- Import domain classes
- Implement validation in UI
- Execute formulas
- Apply UI behavior changes
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto.control_rule_dto import ControlRuleType
from doc_helper.application.dto.export_dto import ControlRuleExportDTO
from doc_helper.application.dto.schema_dto import FieldDefinitionDTO


class ControlRuleDialog(QDialog):
    """Dialog for adding or editing a control rule (Phase F-12).

    This is a UI-only dialog that collects user input and returns it.
    All validation and persistence is handled by the ViewModel.

    Phase F-12 Compliance:
        - UI-only, no business logic
        - Returns user input as primitive types
        - NO validation (delegated to ViewModel)
        - NO execution
        - Design-time only
    """

    def __init__(
        self,
        available_fields: tuple[FieldDefinitionDTO, ...],
        parent: Optional[QWidget] = None,
        existing_rule: Optional[ControlRuleExportDTO] = None,
    ) -> None:
        """Initialize Control Rule Dialog.

        Args:
            available_fields: Fields available to select as target (from current entity)
            parent: Parent widget
            existing_rule: Existing rule to edit (None for add mode)
        """
        super().__init__(parent)

        self._available_fields = available_fields
        self._existing_rule = existing_rule
        self._is_edit_mode = existing_rule is not None

        # UI components
        self._rule_type_combo: Optional[QComboBox] = None
        self._target_field_combo: Optional[QComboBox] = None
        self._formula_edit: Optional[QTextEdit] = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Set dialog title
        title = "Edit Control Rule" if self._is_edit_mode else "Add Control Rule"
        self.setWindowTitle(title)
        self.resize(500, 400)

        # Main layout
        layout = QVBoxLayout(self)

        # Info label
        info_text = (
            "Control rules define inter-field dependencies using boolean formulas.\n"
            "VISIBILITY: Controls whether a field is visible\n"
            "ENABLED: Controls whether a field is enabled/disabled\n"
            "REQUIRED: Controls whether a field is required"
        )
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: gray; font-style: italic; padding: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Form layout
        form_layout = QFormLayout()

        # Rule Type (combo box)
        self._rule_type_combo = QComboBox()
        self._rule_type_combo.addItem("VISIBILITY", ControlRuleType.VISIBILITY.value)
        self._rule_type_combo.addItem("ENABLED", ControlRuleType.ENABLED.value)
        self._rule_type_combo.addItem("REQUIRED", ControlRuleType.REQUIRED.value)

        # If editing, pre-select the rule type and disable changing it
        if self._is_edit_mode and self._existing_rule:
            index = self._rule_type_combo.findData(self._existing_rule.rule_type)
            if index >= 0:
                self._rule_type_combo.setCurrentIndex(index)
            # Lock rule type in edit mode (can't change type)
            self._rule_type_combo.setEnabled(False)

        form_layout.addRow("Rule Type:", self._rule_type_combo)

        # Target Field (combo box in add mode, label in edit mode)
        if self._is_edit_mode and self._existing_rule:
            # Edit mode: show target field as read-only label
            target_field_label = QLabel(self._existing_rule.target_field_id)
            target_field_label.setStyleSheet("font-family: monospace;")
            form_layout.addRow("Target Field:", target_field_label)
        else:
            # Add mode: allow selecting target field
            self._target_field_combo = QComboBox()
            for field in self._available_fields:
                self._target_field_combo.addItem(
                    f"{field.id} ({field.label})",  # Display text
                    field.id,  # Data (field ID)
                )
            self._target_field_combo.setToolTip(
                "Select the field that this control rule will affect.\n"
                "The formula will determine when this field is visible/enabled/required."
            )
            form_layout.addRow("Target Field:", self._target_field_combo)

        # Formula Text (multi-line text edit)
        self._formula_edit = QTextEdit()
        self._formula_edit.setPlaceholderText(
            "Enter boolean formula...\nExample: {{status}} == 'active'"
        )
        self._formula_edit.setStyleSheet("font-family: monospace;")
        self._formula_edit.setMinimumHeight(150)

        # If editing, pre-fill formula
        if self._is_edit_mode and self._existing_rule:
            self._formula_edit.setPlainText(self._existing_rule.formula_text)

        form_layout.addRow("Formula:", self._formula_edit)

        layout.addLayout(form_layout)

        # Help text
        help_text = (
            "Formula must be a boolean expression using field references like {{field_id}}.\n"
            "Validation and governance checks will be performed when you confirm."
        )
        help_label = QLabel(help_text)
        help_label.setStyleSheet("color: gray; font-size: 9pt; padding: 5px;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_rule_type(self) -> str:
        """Get selected rule type.

        Returns:
            Rule type string (VISIBILITY, ENABLED, REQUIRED)
        """
        if self._rule_type_combo:
            return self._rule_type_combo.currentData()
        return ControlRuleType.VISIBILITY.value

    def get_formula_text(self) -> str:
        """Get formula text entered by user.

        Returns:
            Formula text string
        """
        if self._formula_edit:
            return self._formula_edit.toPlainText().strip()
        return ""

    def get_target_field_id(self) -> str:
        """Get target field ID.

        Returns:
            Target field ID (from existing rule in edit mode, from combo in add mode)
        """
        if self._is_edit_mode and self._existing_rule:
            return self._existing_rule.target_field_id
        elif self._target_field_combo:
            return self._target_field_combo.currentData() or ""
        return ""

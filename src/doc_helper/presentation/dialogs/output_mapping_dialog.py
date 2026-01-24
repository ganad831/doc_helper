"""Output Mapping Dialog (Phase F-13).

This dialog allows users to add or edit output mapping definitions
for field-level document output transformation.

PHASE F-13 RULES:
- This is a UI-only dialog that collects user input
- All validation and persistence is handled by the ViewModel
- NO domain/application layer modifications
- NO formula execution or preview
- Design-time metadata editing only
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

from doc_helper.application.dto.export_dto import OutputMappingExportDTO


class OutputMappingDialog(QDialog):
    """Dialog for adding or editing an output mapping (Phase F-13).

    This is a UI-only dialog that collects user input and returns it.
    All validation and persistence is handled by the ViewModel.

    Output mappings define how field values are transformed for
    document output (Word, Excel, PDF). This is design-time metadata only.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        existing_mapping: Optional[OutputMappingExportDTO] = None,
    ):
        """Initialize the output mapping dialog.

        Args:
            parent: Parent widget
            existing_mapping: If provided, dialog opens in Edit mode.
                            If None, dialog opens in Add mode.
        """
        super().__init__(parent)

        # Track mode
        self._is_edit_mode = existing_mapping is not None
        self._existing_mapping = existing_mapping

        # UI components
        self._target_combo: Optional[QComboBox] = None
        self._formula_edit: Optional[QTextEdit] = None

        # Build UI
        self._build_ui()

        # If edit mode, populate fields
        if self._is_edit_mode and self._existing_mapping:
            self._populate_from_existing()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Set dialog properties
        if self._is_edit_mode:
            self.setWindowTitle("Edit Output Mapping")
        else:
            self.setWindowTitle("Add Output Mapping")

        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(
            "Output mappings define how field values are transformed "
            "for document output (Word, Excel, PDF). This is design-time "
            "metadata only - no runtime execution."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(info_label)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Target type field
        if self._is_edit_mode and self._existing_mapping:
            # Edit mode: show target as read-only label
            target_label = QLabel(self._existing_mapping.target)
            target_label.setStyleSheet("font-weight: bold;")
            form_layout.addRow("Target Type:", target_label)
        else:
            # Add mode: allow selecting target type
            self._target_combo = QComboBox()
            self._target_combo.addItems(["TEXT", "NUMBER", "BOOLEAN"])
            self._target_combo.setToolTip(
                "Select the output target type:\n"
                "• TEXT: Text-based output\n"
                "• NUMBER: Numeric output\n"
                "• BOOLEAN: Boolean output"
            )
            form_layout.addRow("Target Type:", self._target_combo)

        # Formula text editor
        formula_label = QLabel("Formula:")
        self._formula_edit = QTextEdit()
        self._formula_edit.setPlaceholderText(
            "Enter formula expression for output transformation...\n"
            "Example: {{depth_from}} - {{depth_to}}"
        )
        self._formula_edit.setStyleSheet("font-family: monospace;")
        self._formula_edit.setMinimumHeight(150)
        self._formula_edit.setAcceptRichText(False)
        form_layout.addRow(formula_label, self._formula_edit)

        main_layout.addLayout(form_layout)

        # Help text
        help_label = QLabel(
            "Use {{field_id}} syntax to reference field values in the formula.\n"
            "The formula will be applied during document generation."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 9pt;")
        main_layout.addWidget(help_label)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _populate_from_existing(self) -> None:
        """Populate dialog fields from existing output mapping."""
        if not self._existing_mapping:
            return

        # Target is shown as read-only label in edit mode, no need to set

        # Set formula text
        if self._formula_edit:
            self._formula_edit.setPlainText(self._existing_mapping.formula_text)

    def get_target(self) -> str:
        """Get the selected target type.

        Returns:
            Target type string (TEXT, NUMBER, or BOOLEAN)
        """
        if self._is_edit_mode and self._existing_mapping:
            return self._existing_mapping.target

        if self._target_combo:
            return self._target_combo.currentText()

        return "TEXT"  # Default

    def get_formula_text(self) -> str:
        """Get the formula text entered by the user.

        Returns:
            Formula text as string
        """
        if self._formula_edit:
            return self._formula_edit.toPlainText().strip()
        return ""

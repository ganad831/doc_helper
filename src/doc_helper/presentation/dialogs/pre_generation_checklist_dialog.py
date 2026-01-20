"""Pre-generation checklist dialog for validating project before document generation.

RULES (AGENT_RULES.md Section 3-4):
- Uses DTOs only (ValidationErrorDTO, not domain types)
- No business logic (display only)
- Translation adapter for i18n
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto import ValidationErrorDTO
from doc_helper.presentation.adapters.qt_translation_adapter import QtTranslationAdapter


class PreGenerationChecklistDialog(QDialog):
    """Pre-generation checklist dialog.

    Displays validation errors before document generation.
    Blocks generation if errors exist.

    v1 Implementation:
    - List of validation errors (errors only, no warnings)
    - Error count display
    - Cancel/Generate buttons (Generate disabled if errors exist)
    - Color-coded error indicators

    v2+ Features (deferred):
    - Warning-level validation (can proceed with warnings)
    - Info-level validation (informational only)
    - Color-coded severity (red/yellow/blue)
    - Filter by severity
    - Export error list

    RULES (AGENT_RULES.md Section 3-4):
    - Uses DTOs only (ValidationErrorDTO)
    - No domain logic
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        errors: tuple[ValidationErrorDTO, ...],
        translation_adapter: QtTranslationAdapter,
    ) -> None:
        """Initialize pre-generation checklist dialog.

        Args:
            parent: Parent widget
            errors: Tuple of validation error DTOs
            translation_adapter: Qt translation adapter for i18n
        """
        super().__init__(parent)
        self._errors = errors
        self._translation_adapter = translation_adapter
        self._can_generate = len(errors) == 0

        # UI components
        self._error_list: Optional[QListWidget] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        self.setWindowTitle(self._translation_adapter.translate("dialog.pre_generation.title"))
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Title and status
        if self._can_generate:
            # No errors - ready to generate
            status_label = QLabel(
                self._translation_adapter.translate("dialog.pre_generation.ready")
            )
            status_label.setStyleSheet("font-weight: bold; color: #388e3c; font-size: 14px;")
            main_layout.addWidget(status_label)

            instructions = QLabel(
                self._translation_adapter.translate("dialog.pre_generation.ready_instructions")
            )
            instructions.setWordWrap(True)
            main_layout.addWidget(instructions)

        else:
            # Has errors - cannot generate
            error_count_label = QLabel(
                self._translation_adapter.translate(
                    "dialog.pre_generation.error_count",
                    count=len(self._errors)
                )
            )
            error_count_label.setStyleSheet("font-weight: bold; color: #d32f2f; font-size: 14px;")
            main_layout.addWidget(error_count_label)

            instructions = QLabel(
                self._translation_adapter.translate("dialog.pre_generation.error_instructions")
            )
            instructions.setWordWrap(True)
            main_layout.addWidget(instructions)

            # Error list
            errors_label = QLabel(
                self._translation_adapter.translate("dialog.pre_generation.errors_list")
            )
            errors_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            main_layout.addWidget(errors_label)

            self._error_list = QListWidget()
            self._error_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
            main_layout.addWidget(self._error_list, 1)  # Stretch factor 1

            # Populate errors
            self._populate_errors()

        # Buttons
        if self._can_generate:
            # Show Cancel/Generate buttons
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Cancel |
                QDialogButtonBox.StandardButton.Ok
            )

            # Rename OK button to "Generate"
            generate_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
            if generate_button:
                generate_button.setText(
                    self._translation_adapter.translate("dialog.pre_generation.generate")
                )

            button_box.accepted.connect(self._on_generate)
            button_box.rejected.connect(self._on_cancel)

        else:
            # Show only Close button (cannot generate with errors)
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.rejected.connect(self._on_cancel)

        main_layout.addWidget(button_box)

    def _populate_errors(self) -> None:
        """Populate error list with validation errors."""
        # CRITICAL FIX: Check for None explicitly, not truthiness
        # Empty QListWidget evaluates to False in boolean context!
        if self._error_list is None:
            return

        for error in self._errors:
            # Create error item with field name and message
            error_text = f"• {error.message}"

            item = QListWidgetItem(error_text)
            item.setForeground(Qt.GlobalColor.red)

            # Add field ID as tooltip for debugging (optional)
            item.setToolTip(f"Field: {error.field_id}")

            self._error_list.addItem(item)

    def _on_generate(self) -> None:
        """Handle Generate button click."""
        # Only called if can_generate is True
        self.accept()

    def _on_cancel(self) -> None:
        """Handle Cancel/Close button click."""
        self.reject()

    def can_generate(self) -> bool:
        """Check if generation can proceed.

        Returns:
            True if no errors, False if errors exist
        """
        return self._can_generate

    @staticmethod
    def check_and_confirm(
        parent: Optional[QWidget],
        errors: tuple[ValidationErrorDTO, ...],
        translation_adapter: QtTranslationAdapter,
    ) -> bool:
        """Show pre-generation checklist and return whether to proceed.

        Args:
            parent: Parent widget
            errors: Tuple of validation error DTOs
            translation_adapter: Qt translation adapter

        Returns:
            True if user clicked Generate (and no errors), False otherwise
        """
        dialog = PreGenerationChecklistDialog(parent, errors, translation_adapter)
        result = dialog.exec()

        # Only return True if dialog accepted AND can generate
        return result == QDialog.DialogCode.Accepted and dialog.can_generate()

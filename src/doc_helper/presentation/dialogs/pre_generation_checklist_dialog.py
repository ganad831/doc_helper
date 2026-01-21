"""Pre-generation checklist dialog for validating project before document generation.

RULES (AGENT_RULES.md Section 3-4):
- Uses DTOs only (ValidationErrorDTO, not domain types)
- No business logic (display only)
- Translation adapter for i18n

ADR-025: Validation Severity Levels
- ERROR (red): Blocks generation unconditionally
- WARNING (yellow): Requires user confirmation to proceed
- INFO (blue): Informational only, does not block
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
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

    Displays validation errors grouped by severity before document generation.

    ADR-025 Implementation:
    - ERROR-level failures: Block generation (red, must resolve)
    - WARNING-level failures: Allow generation with confirmation (yellow/orange)
    - INFO-level failures: Informational display (blue, non-blocking)
    - Visual differentiation with color coding
    - Separate sections for each severity level

    RULES (AGENT_RULES.md Section 3-4):
    - Uses DTOs only (ValidationErrorDTO with severity string field)
    - No domain logic (no imports from domain layer)
    - Severity consumed as primitive string from DTO
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
            errors: Tuple of validation error DTOs (with severity field)
            translation_adapter: Qt translation adapter for i18n
        """
        super().__init__(parent)
        self._errors = errors
        self._translation_adapter = translation_adapter

        # Group errors by severity (using DTO string field, not domain enum)
        self._errors_by_severity = self._group_by_severity(errors)
        self._has_blocking_errors = len(self._errors_by_severity["ERROR"]) > 0
        self._can_generate = not self._has_blocking_errors

        # UI components
        self._error_list: Optional[QListWidget] = None
        self._warning_list: Optional[QListWidget] = None
        self._info_list: Optional[QListWidget] = None

        # Build UI
        self._build_ui()

    @staticmethod
    def _group_by_severity(errors: tuple[ValidationErrorDTO, ...]) -> dict[str, list[ValidationErrorDTO]]:
        """Group validation errors by severity level.

        Args:
            errors: Tuple of validation error DTOs

        Returns:
            Dict mapping severity string ("ERROR", "WARNING", "INFO") to list of errors
        """
        grouped: dict[str, list[ValidationErrorDTO]] = {
            "ERROR": [],
            "WARNING": [],
            "INFO": [],
        }

        for error in errors:
            # Use DTO severity field (primitive string, not domain enum)
            severity = error.severity.upper()  # Normalize to uppercase
            if severity in grouped:
                grouped[severity].append(error)
            else:
                # Unknown severity - treat as ERROR for safety
                grouped["ERROR"].append(error)

        return grouped

    def _build_ui(self) -> None:
        """Build the UI components with severity-based grouping.

        ADR-025: Display errors grouped by severity with visual differentiation.
        """
        self.setWindowTitle(self._translation_adapter.translate("dialog.pre_generation.title"))
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Title and overall status
        if not self._has_blocking_errors and len(self._errors) == 0:
            # No validation issues - ready to generate
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

        elif self._has_blocking_errors:
            # Has ERROR-level failures - cannot generate
            error_count = len(self._errors_by_severity["ERROR"])
            status_label = QLabel(
                self._translation_adapter.translate(
                    "dialog.pre_generation.error_count",
                    count=error_count
                )
            )
            status_label.setStyleSheet("font-weight: bold; color: #d32f2f; font-size: 14px;")
            main_layout.addWidget(status_label)

            instructions = QLabel(
                self._translation_adapter.translate("dialog.pre_generation.error_instructions")
            )
            instructions.setWordWrap(True)
            main_layout.addWidget(instructions)

        else:
            # Has WARNING/INFO only - can generate with confirmation
            warning_count = len(self._errors_by_severity["WARNING"])
            info_count = len(self._errors_by_severity["INFO"])

            status_label = QLabel(
                self._translation_adapter.translate(
                    "dialog.pre_generation.warnings_info_count",
                    warning_count=warning_count,
                    info_count=info_count
                )
            )
            status_label.setStyleSheet("font-weight: bold; color: #f57c00; font-size: 14px;")
            main_layout.addWidget(status_label)

            instructions = QLabel(
                self._translation_adapter.translate("dialog.pre_generation.warning_instructions")
            )
            instructions.setWordWrap(True)
            main_layout.addWidget(instructions)

        # ERROR section (red, blocks generation)
        if len(self._errors_by_severity["ERROR"]) > 0:
            error_group = self._create_severity_group(
                "ERROR",
                self._errors_by_severity["ERROR"],
                "#d32f2f",  # Red
                "dialog.pre_generation.errors_section"
            )
            main_layout.addWidget(error_group)
            self._error_list = error_group.findChild(QListWidget)

        # WARNING section (yellow/orange, requires confirmation)
        if len(self._errors_by_severity["WARNING"]) > 0:
            warning_group = self._create_severity_group(
                "WARNING",
                self._errors_by_severity["WARNING"],
                "#f57c00",  # Orange
                "dialog.pre_generation.warnings_section"
            )
            main_layout.addWidget(warning_group)
            self._warning_list = warning_group.findChild(QListWidget)

        # INFO section (blue, informational only)
        if len(self._errors_by_severity["INFO"]) > 0:
            info_group = self._create_severity_group(
                "INFO",
                self._errors_by_severity["INFO"],
                "#1976d2",  # Blue
                "dialog.pre_generation.info_section"
            )
            main_layout.addWidget(info_group)
            self._info_list = info_group.findChild(QListWidget)

        # Buttons
        if self._can_generate:
            # No blocking errors - show Cancel/Generate buttons
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Cancel |
                QDialogButtonBox.StandardButton.Ok
            )

            # Rename OK button
            generate_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
            if generate_button:
                if len(self._errors_by_severity["WARNING"]) > 0:
                    # Has warnings - show "Continue Anyway"
                    generate_button.setText(
                        self._translation_adapter.translate("dialog.pre_generation.continue_anyway")
                    )
                else:
                    # No warnings - show "Generate"
                    generate_button.setText(
                        self._translation_adapter.translate("dialog.pre_generation.generate")
                    )

            button_box.accepted.connect(self._on_generate)
            button_box.rejected.connect(self._on_cancel)

        else:
            # Has blocking errors - show only Close button
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.rejected.connect(self._on_cancel)

        main_layout.addWidget(button_box)

    def _create_severity_group(
        self,
        severity: str,
        errors: list[ValidationErrorDTO],
        color: str,
        title_key: str,
    ) -> QGroupBox:
        """Create a grouped section for a specific severity level.

        Args:
            severity: Severity level string ("ERROR", "WARNING", "INFO")
            errors: List of validation errors for this severity
            color: Hex color code for this severity
            title_key: Translation key for section title

        Returns:
            QGroupBox containing the error list
        """
        group = QGroupBox(
            self._translation_adapter.translate(title_key, count=len(errors))
        )
        group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {color}; }}")

        group_layout = QVBoxLayout(group)

        # List widget for errors
        error_list = QListWidget()
        error_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        error_list.setMaximumHeight(150)  # Limit height per section

        # Populate errors
        for error in errors:
            error_text = f"• {error.message}"
            item = QListWidgetItem(error_text)

            # Set color based on severity
            if severity == "ERROR":
                item.setForeground(Qt.GlobalColor.red)
            elif severity == "WARNING":
                item.setForeground(Qt.GlobalColor.darkYellow)
            elif severity == "INFO":
                item.setForeground(Qt.GlobalColor.blue)

            # Add field ID as tooltip
            item.setToolTip(f"Field: {error.field_id}")

            error_list.addItem(item)

        group_layout.addWidget(error_list)

        return group

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

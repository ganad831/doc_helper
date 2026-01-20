"""Conflict resolution dialog for resolving override conflicts.

RULES (AGENT_RULES.md Section 3-4):
- Uses DTOs only (ConflictDTO, not domain types)
- No business logic (display and selection only)
- Translation adapter for i18n
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto import ConflictDTO
from doc_helper.presentation.adapters.qt_translation_adapter import QtTranslationAdapter


class ConflictResolutionDialog(QDialog):
    """Conflict resolution dialog.

    Displays conflicts between user overrides and system-computed values
    (formulas or controls).

    v1 Implementation:
    - Table of all conflicts (field, type, values)
    - Detailed description of each conflict
    - Read-only display (resolution happens elsewhere)
    - Close button

    v2+ Features (deferred):
    - Interactive resolution (choose which value to keep)
    - Batch resolution options
    - Conflict history

    RULES (AGENT_RULES.md Section 3-4):
    - Uses DTOs only (ConflictDTO)
    - No domain logic
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        conflicts: tuple[ConflictDTO, ...],
        translation_adapter: QtTranslationAdapter,
    ) -> None:
        """Initialize conflict resolution dialog.

        Args:
            parent: Parent widget
            conflicts: Tuple of conflict DTOs
            translation_adapter: Qt translation adapter for i18n
        """
        super().__init__(parent)
        self._conflicts = conflicts
        self._translation_adapter = translation_adapter

        # UI components
        self._conflict_table: Optional[QTableWidget] = None
        self._description_text: Optional[QTextEdit] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        self.setWindowTitle(self._translation_adapter.translate("dialog.conflict_resolution.title"))
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Instructions label
        instructions = QLabel(
            self._translation_adapter.translate("dialog.conflict_resolution.instructions")
        )
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)

        # Conflict count
        count_label = QLabel(
            self._translation_adapter.translate(
                "dialog.conflict_resolution.conflict_count",
                count=len(self._conflicts)
            )
        )
        count_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
        main_layout.addWidget(count_label)

        # Conflict table
        self._conflict_table = QTableWidget()
        self._conflict_table.setColumnCount(4)
        self._conflict_table.setHorizontalHeaderLabels([
            self._translation_adapter.translate("dialog.conflict_resolution.field"),
            self._translation_adapter.translate("dialog.conflict_resolution.type"),
            self._translation_adapter.translate("dialog.conflict_resolution.user_value"),
            self._translation_adapter.translate("dialog.conflict_resolution.system_value"),
        ])

        # Configure table
        header = self._conflict_table.horizontalHeader()
        if header:
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Field name
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Type
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # User value
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # System value

        self._conflict_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._conflict_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._conflict_table.currentItemChanged.connect(self._on_conflict_selected)

        main_layout.addWidget(self._conflict_table, 1)  # Stretch factor 1

        # Description panel
        desc_label = QLabel(self._translation_adapter.translate("dialog.conflict_resolution.description"))
        main_layout.addWidget(desc_label)

        self._description_text = QTextEdit()
        self._description_text.setReadOnly(True)
        self._description_text.setMaximumHeight(150)
        main_layout.addWidget(self._description_text)

        # Populate table
        self._populate_conflicts()

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self._on_close)
        main_layout.addWidget(button_box)

    def _populate_conflicts(self) -> None:
        """Populate conflict table with data."""
        if not self._conflict_table:
            return

        self._conflict_table.setRowCount(len(self._conflicts))

        for row, conflict in enumerate(self._conflicts):
            # Field name
            field_item = QTableWidgetItem(conflict.field_label)
            field_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            field_item.setData(Qt.ItemDataRole.UserRole, row)  # Store conflict index
            self._conflict_table.setItem(row, 0, field_item)

            # Conflict type
            type_display = self._get_conflict_type_display(conflict.conflict_type)
            type_item = QTableWidgetItem(type_display)
            type_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._conflict_table.setItem(row, 1, type_item)

            # User value
            user_item = QTableWidgetItem(conflict.user_value)
            user_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._conflict_table.setItem(row, 2, user_item)

            # System value (formula or control)
            system_value = conflict.formula_value or conflict.control_value or ""
            system_item = QTableWidgetItem(system_value)
            system_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._conflict_table.setItem(row, 3, system_item)

        # Select first row by default
        if len(self._conflicts) > 0:
            self._conflict_table.selectRow(0)
            self._show_conflict_description(self._conflicts[0])

    def _get_conflict_type_display(self, conflict_type: str) -> str:
        """Get display text for conflict type.

        Args:
            conflict_type: Conflict type ("formula" | "control" | "formula_control")

        Returns:
            Translated display text
        """
        type_key = f"dialog.conflict_resolution.type_{conflict_type}"
        return self._translation_adapter.translate(type_key)

    def _on_conflict_selected(self, current: Optional[QTableWidgetItem], previous: Optional[QTableWidgetItem]) -> None:
        """Handle conflict selection change.

        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if not current:
            return

        # Get conflict index
        row = self._conflict_table.row(current)
        if row < 0 or row >= len(self._conflicts):
            return

        conflict = self._conflicts[row]
        self._show_conflict_description(conflict)

    def _show_conflict_description(self, conflict: ConflictDTO) -> None:
        """Show detailed description of conflict.

        Args:
            conflict: Conflict DTO to display
        """
        if not self._description_text:
            return

        # Build HTML description
        description_parts = []

        # Field name
        description_parts.append(f"<b>{conflict.field_label}</b>")

        # Conflict description
        description_parts.append(f"<p>{conflict.description}</p>")

        # Values comparison
        description_parts.append("<table style='margin-top: 10px;'>")

        # User value row
        user_label = self._translation_adapter.translate("dialog.conflict_resolution.user_override")
        description_parts.append(
            f"<tr><td style='padding: 5px;'><b>{user_label}:</b></td>"
            f"<td style='padding: 5px;'>{conflict.user_value}</td></tr>"
        )

        # Formula value row (if present)
        if conflict.formula_value:
            formula_label = self._translation_adapter.translate("dialog.conflict_resolution.formula_computed")
            description_parts.append(
                f"<tr><td style='padding: 5px;'><b>{formula_label}:</b></td>"
                f"<td style='padding: 5px;'>{conflict.formula_value}</td></tr>"
            )

        # Control value row (if present)
        if conflict.control_value:
            control_label = self._translation_adapter.translate("dialog.conflict_resolution.control_set")
            description_parts.append(
                f"<tr><td style='padding: 5px;'><b>{control_label}:</b></td>"
                f"<td style='padding: 5px;'>{conflict.control_value}</td></tr>"
            )

        description_parts.append("</table>")

        # Resolution note
        resolution_note = self._translation_adapter.translate("dialog.conflict_resolution.resolution_note")
        description_parts.append(f"<p style='margin-top: 10px;'><i>{resolution_note}</i></p>")

        self._description_text.setHtml("\n".join(description_parts))

    def _on_close(self) -> None:
        """Handle Close button click."""
        # Close dialog
        self.accept()

    @staticmethod
    def show_conflicts(
        parent: Optional[QWidget],
        conflicts: tuple[ConflictDTO, ...],
        translation_adapter: QtTranslationAdapter,
    ) -> None:
        """Show conflict resolution dialog.

        Args:
            parent: Parent widget
            conflicts: Tuple of conflict DTOs
            translation_adapter: Qt translation adapter
        """
        dialog = ConflictResolutionDialog(parent, conflicts, translation_adapter)
        dialog.exec()

"""Override management dialog for reviewing and accepting/rejecting overrides.

RULES (AGENT_RULES.md Section 3-4):
- Uses DTOs only (OverrideDTO, not domain types)
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
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from doc_helper.application.dto import OverrideDTO
from doc_helper.presentation.adapters.qt_translation_adapter import QtTranslationAdapter


class OverrideManagementDialog(QDialog):
    """Override management dialog.

    v1 Implementation:
    - Table of all overrides (field, system value, report value, state)
    - Accept/Reject individual overrides
    - Accept All/Reject All buttons
    - Close button

    v2+ Features (deferred):
    - Filter by state (PENDING, ACCEPTED, etc.)
    - Search by field name
    - Batch selection with checkboxes
    - Export override list

    RULES (AGENT_RULES.md Section 3-4):
    - Uses DTOs only (OverrideDTO)
    - No domain logic
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        overrides: tuple[OverrideDTO, ...],
        translation_adapter: QtTranslationAdapter,
    ) -> None:
        """Initialize override management dialog.

        Args:
            parent: Parent widget
            overrides: Tuple of override DTOs
            translation_adapter: Qt translation adapter for i18n
        """
        super().__init__(parent)
        self._overrides = overrides
        self._translation_adapter = translation_adapter

        # Track user actions (field_id -> "accept" | "reject" | None)
        self._actions: dict[str, str] = {}

        # UI components
        self._override_table: Optional[QTableWidget] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        self.setWindowTitle(self._translation_adapter.translate("dialog.override_management.title"))
        self.setModal(True)
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Instructions label
        instructions = QLabel(
            self._translation_adapter.translate("dialog.override_management.instructions")
        )
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)

        # Override table
        self._override_table = QTableWidget()
        self._override_table.setColumnCount(5)
        self._override_table.setHorizontalHeaderLabels([
            self._translation_adapter.translate("dialog.override_management.field"),
            self._translation_adapter.translate("dialog.override_management.system_value"),
            self._translation_adapter.translate("dialog.override_management.report_value"),
            self._translation_adapter.translate("dialog.override_management.state"),
            self._translation_adapter.translate("dialog.override_management.action"),
        ])

        # Configure table
        header = self._override_table.horizontalHeader()
        if header:
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Field name
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # System value
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Report value
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # State
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Action

        self._override_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._override_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        main_layout.addWidget(self._override_table, 1)  # Stretch factor 1

        # Populate table
        self._populate_overrides()

        # Bulk action buttons
        bulk_layout = QHBoxLayout()

        accept_all_button = QPushButton(
            self._translation_adapter.translate("dialog.override_management.accept_all")
        )
        accept_all_button.clicked.connect(self._on_accept_all)
        bulk_layout.addWidget(accept_all_button)

        reject_all_button = QPushButton(
            self._translation_adapter.translate("dialog.override_management.reject_all")
        )
        reject_all_button.clicked.connect(self._on_reject_all)
        bulk_layout.addWidget(reject_all_button)

        bulk_layout.addStretch()

        main_layout.addLayout(bulk_layout)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self._on_close)
        main_layout.addWidget(button_box)

    def _populate_overrides(self) -> None:
        """Populate override table with data."""
        if not self._override_table:
            return

        self._override_table.setRowCount(len(self._overrides))

        for row, override in enumerate(self._overrides):
            # Field name
            field_item = QTableWidgetItem(override.field_label)
            field_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._override_table.setItem(row, 0, field_item)

            # System value
            system_item = QTableWidgetItem(override.system_value)
            system_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._override_table.setItem(row, 1, system_item)

            # Report value
            report_item = QTableWidgetItem(override.report_value)
            report_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._override_table.setItem(row, 2, report_item)

            # State
            state_item = QTableWidgetItem(override.state)
            state_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._override_table.setItem(row, 3, state_item)

            # Action buttons
            action_widget = self._create_action_widget(override)
            self._override_table.setCellWidget(row, 4, action_widget)

    def _create_action_widget(self, override: OverrideDTO) -> QWidget:
        """Create action button widget for override row.

        Args:
            override: Override DTO

        Returns:
            Widget with Accept/Reject buttons
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Accept button
        accept_button = QPushButton(
            self._translation_adapter.translate("dialog.override_management.accept")
        )
        accept_button.setEnabled(override.can_accept)
        accept_button.clicked.connect(lambda: self._on_accept_override(override.field_id))
        layout.addWidget(accept_button)

        # Reject button
        reject_button = QPushButton(
            self._translation_adapter.translate("dialog.override_management.reject")
        )
        reject_button.setEnabled(override.can_reject)
        reject_button.clicked.connect(lambda: self._on_reject_override(override.field_id))
        layout.addWidget(reject_button)

        return widget

    def _on_accept_override(self, field_id: str) -> None:
        """Handle accept action for individual override.

        Args:
            field_id: Field ID of override to accept
        """
        self._actions[field_id] = "accept"

    def _on_reject_override(self, field_id: str) -> None:
        """Handle reject action for individual override.

        Args:
            field_id: Field ID of override to reject
        """
        self._actions[field_id] = "reject"

    def _on_accept_all(self) -> None:
        """Handle Accept All button click."""
        for override in self._overrides:
            if override.can_accept:
                self._actions[override.field_id] = "accept"

    def _on_reject_all(self) -> None:
        """Handle Reject All button click."""
        for override in self._overrides:
            if override.can_reject:
                self._actions[override.field_id] = "reject"

    def _on_close(self) -> None:
        """Handle Close button click."""
        # Accept dialog with actions
        self.accept()

    def get_actions(self) -> dict[str, str]:
        """Get user actions for overrides.

        Returns:
            Dictionary mapping field_id to action ("accept" | "reject")
        """
        return self._actions.copy()

    @staticmethod
    def manage_overrides(
        parent: Optional[QWidget],
        overrides: tuple[OverrideDTO, ...],
        translation_adapter: QtTranslationAdapter,
    ) -> dict[str, str]:
        """Show override management dialog and return user actions.

        Args:
            parent: Parent widget
            overrides: Tuple of override DTOs
            translation_adapter: Qt translation adapter

        Returns:
            Dictionary mapping field_id to action ("accept" | "reject")
            Empty dict if no actions taken
        """
        dialog = OverrideManagementDialog(parent, overrides, translation_adapter)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            return dialog.get_actions()

        return {}

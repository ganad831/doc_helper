"""Field History dialog for viewing field value changes over time.

ADR-027: Field History Storage
RULES (AGENT_RULES.md Section 3-4):
- Uses DTOs only (FieldHistoryEntryDTO, FieldHistoryResultDTO)
- No domain objects in presentation
- Read-only display (no revert functionality in v1)
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto.field_history_dto import (
    FieldHistoryEntryDTO,
    FieldHistoryResultDTO,
)


class FieldHistoryDialog(QDialog):
    """Field History dialog for viewing field value changes.

    ADR-027: Field History Storage
    - Displays append-only record of field value changes
    - Shows timestamp, old/new values, change source, user attribution
    - Read-only view (no revert capability in v1)
    - Supports pagination for large history datasets

    v1 Implementation:
    - Chronological list of changes (newest first)
    - Change source badges (USER, FORMULA, OVERRIDE, CONTROL)
    - Previous/Next page buttons for pagination
    - Close button

    v2+ Features (deferred):
    - Revert to historical value
    - Export history to CSV
    - Filter by change source
    - Date range filtering
    - Search within history

    RULES (AGENT_RULES.md Section 3-4):
    - Uses FieldHistoryResultDTO only (no domain objects)
    - Pagination handled by parent (query with offset/limit)
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        field_label: str,
        field_path: str,
        history_result: FieldHistoryResultDTO,
    ) -> None:
        """Initialize field history dialog.

        Args:
            parent: Parent widget
            field_label: Display label for the field
            field_path: Field path for reference
            history_result: History result DTO with entries and pagination metadata
        """
        super().__init__(parent)
        self._field_label = field_label
        self._field_path = field_path
        self._history_result = history_result

        # UI components
        self._history_list: Optional[QListWidget] = None
        self._status_label: Optional[QLabel] = None
        self._prev_button: Optional[QPushButton] = None
        self._next_button: Optional[QPushButton] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        self.setWindowTitle(f"Field History - {self._field_label}")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Header section
        header_layout = QVBoxLayout()

        # Field info
        field_info_label = QLabel(f"<b>Field:</b> {self._field_label}")
        field_path_label = QLabel(f"<i>Path:</i> {self._field_path}")
        field_path_label.setStyleSheet("color: gray;")

        header_layout.addWidget(field_info_label)
        header_layout.addWidget(field_path_label)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)

        # Status label (shows pagination info)
        self._status_label = QLabel()
        self._update_status_label()
        main_layout.addWidget(self._status_label)

        # History list
        history_label = QLabel("Change History:")
        main_layout.addWidget(history_label)

        self._history_list = QListWidget()
        self._history_list.setAlternatingRowColors(True)
        main_layout.addWidget(self._history_list, 1)  # Stretch factor 1

        # Populate history
        self._populate_history()

        # Pagination buttons
        pagination_layout = QHBoxLayout()

        self._prev_button = QPushButton("◀ Previous Page")
        self._prev_button.setEnabled(self._history_result.offset > 0)
        # Note: Pagination callback would be handled by parent in full implementation

        self._next_button = QPushButton("Next Page ▶")
        has_more = (
            self._history_result.offset + len(self._history_result.entries)
            < self._history_result.total_count
        )
        self._next_button.setEnabled(has_more)

        pagination_layout.addWidget(self._prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self._next_button)

        main_layout.addLayout(pagination_layout)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        main_layout.addWidget(button_box)

    def _update_status_label(self) -> None:
        """Update status label with pagination info."""
        if not self._status_label:
            return

        total = self._history_result.total_count
        if total == 0:
            self._status_label.setText("No history entries found")
            self._status_label.setStyleSheet("color: gray; font-style: italic;")
            return

        start = self._history_result.offset + 1
        end = min(
            self._history_result.offset + len(self._history_result.entries),
            total,
        )

        self._status_label.setText(f"Showing {start}-{end} of {total} changes")
        self._status_label.setStyleSheet("color: green;")

    def _populate_history(self) -> None:
        """Populate history list with entries."""
        if not self._history_list:
            return

        # Clear previous entries
        self._history_list.clear()

        # Check if empty
        if not self._history_result.entries:
            item = QListWidgetItem("No history entries found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Not selectable
            self._history_list.addItem(item)
            return

        # Add history entries (newest first)
        for entry in self._history_result.entries:
            display_text = self._format_history_entry(entry)
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, entry)  # Store DTO in item data

            # Style based on change source
            if entry.is_user_initiated():
                item.setBackground(Qt.GlobalColor.white)
            else:
                item.setBackground(Qt.GlobalColor.lightGray)

            self._history_list.addItem(item)

    def _format_history_entry(self, entry: FieldHistoryEntryDTO) -> str:
        """Format history entry for display.

        Args:
            entry: History entry DTO

        Returns:
            Formatted display string
        """
        # Parse timestamp for display (ISO format to readable)
        timestamp = self._format_timestamp(entry.timestamp)

        # Format change source badge
        source_badge = self._get_source_badge(entry.change_source)

        # Format old/new values (truncate if too long)
        old_value = self._format_value(entry.previous_value)
        new_value = self._format_value(entry.new_value)

        # Build display string
        # Line 1: Timestamp and source badge
        line1 = f"{timestamp} | {source_badge}"

        # Line 2: Value change
        line2 = f"  Changed from: {old_value}"
        line3 = f"  Changed to:   {new_value}"

        # Line 4: User attribution (if applicable)
        lines = [line1, line2, line3]
        if entry.user_id:
            lines.append(f"  By user: {entry.user_id}")

        return "\n".join(lines)

    def _format_timestamp(self, iso_timestamp: str) -> str:
        """Format ISO timestamp for display.

        Args:
            iso_timestamp: ISO 8601 timestamp string

        Returns:
            Human-readable timestamp
        """
        # Parse ISO timestamp (e.g., "2024-01-15T10:30:00")
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(iso_timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            # Fallback: return as-is if parsing fails
            return iso_timestamp

    def _get_source_badge(self, change_source: str) -> str:
        """Get display badge for change source.

        Args:
            change_source: Change source string

        Returns:
            Formatted badge string
        """
        badges = {
            "USER_EDIT": "[USER EDIT]",
            "FORMULA_RECOMPUTATION": "[FORMULA]",
            "OVERRIDE_ACCEPTANCE": "[OVERRIDE]",
            "CONTROL_EFFECT": "[CONTROL]",
            "UNDO_OPERATION": "[UNDO]",
            "REDO_OPERATION": "[REDO]",
        }
        return badges.get(change_source, f"[{change_source}]")

    def _format_value(self, value: any) -> str:
        """Format value for display (with truncation).

        Args:
            value: Value to format

        Returns:
            Formatted value string
        """
        if value is None:
            return "(empty)"

        value_str = str(value)
        if len(value_str) > 50:
            return value_str[:47] + "..."
        return value_str

    @staticmethod
    def show_history(
        parent: Optional[QWidget],
        field_label: str,
        field_path: str,
        history_result: FieldHistoryResultDTO,
    ) -> None:
        """Show field history dialog.

        Args:
            parent: Parent widget
            field_label: Display label for the field
            field_path: Field path for reference
            history_result: History result DTO
        """
        dialog = FieldHistoryDialog(parent, field_label, field_path, history_result)
        dialog.exec()

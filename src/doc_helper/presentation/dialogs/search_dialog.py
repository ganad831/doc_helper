"""Search dialog for finding fields within a project.

ADR-026: Search Architecture
RULES (AGENT_RULES.md Section 3-4):
- Uses DTOs only (SearchResultDTO)
- No domain objects in presentation
- Read-only navigation (no inline editing)
"""

from typing import Callable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto.search_result_dto import SearchResultDTO


class SearchDialog(QDialog):
    """Search dialog for finding fields within a project.

    ADR-026: Search Architecture
    - Search operates within current project only
    - Searches field labels, field IDs, and field values
    - Results are read-only (navigation only, no inline editing)
    - Respects domain visibility rules

    v1 Implementation:
    - Text search with live results
    - Results list with field path and current value
    - Navigate to field on selection
    - Close button

    v2+ Features (deferred):
    - Advanced search syntax (regex, boolean operators)
    - Search history
    - Saved searches
    - Search highlighting

    RULES (AGENT_RULES.md Section 3-4):
    - Uses SearchResultDTO only (no domain objects)
    - Navigation callback provided by parent
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        search_callback: Callable[[str], list[SearchResultDTO]],
        navigate_callback: Callable[[str], None],
    ) -> None:
        """Initialize search dialog.

        Args:
            parent: Parent widget
            search_callback: Callback to execute search (takes search_term, returns list[SearchResultDTO])
            navigate_callback: Callback to navigate to field (takes field_path)
        """
        super().__init__(parent)
        self._search_callback = search_callback
        self._navigate_callback = navigate_callback

        # UI components
        self._search_input: Optional[QLineEdit] = None
        self._results_list: Optional[QListWidget] = None
        self._status_label: Optional[QLabel] = None
        self._navigate_button: Optional[QPushButton] = None

        # Current results
        self._current_results: list[SearchResultDTO] = []

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        self.setWindowTitle("Search Fields")
        self.setModal(False)  # Non-modal so users can see form while searching
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Search input section
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(
            "Enter field name, label, or value..."
        )
        self._search_input.textChanged.connect(self._on_search_text_changed)
        self._search_input.returnPressed.connect(self._execute_search)

        search_button = QPushButton("Search")
        search_button.clicked.connect(self._execute_search)
        search_button.setDefault(True)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_input, 1)  # Stretch factor 1
        search_layout.addWidget(search_button)

        main_layout.addLayout(search_layout)

        # Status label
        self._status_label = QLabel("Enter search term to find fields")
        self._status_label.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(self._status_label)

        # Results list
        results_label = QLabel("Results:")
        main_layout.addWidget(results_label)

        self._results_list = QListWidget()
        self._results_list.itemDoubleClicked.connect(self._on_result_double_clicked)
        self._results_list.itemSelectionChanged.connect(self._on_selection_changed)
        main_layout.addWidget(self._results_list, 1)  # Stretch factor 1

        # Button section
        button_layout = QHBoxLayout()

        self._navigate_button = QPushButton("Go to Field")
        self._navigate_button.clicked.connect(self._on_navigate)
        self._navigate_button.setEnabled(False)  # Disabled until selection

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(self._navigate_button)
        button_layout.addWidget(close_button)

        main_layout.addLayout(button_layout)

        # Set focus to search input
        self._search_input.setFocus()

    def _on_search_text_changed(self, text: str) -> None:
        """Handle search text changes (live search disabled for v1).

        Args:
            text: Current search text

        Note: Live search disabled in v1 for performance.
        User must press Enter or click Search button.
        """
        # Update status to prompt user to search
        if not text.strip():
            if self._status_label:
                self._status_label.setText("Enter search term to find fields")
                self._status_label.setStyleSheet("color: gray; font-style: italic;")

    def _execute_search(self) -> None:
        """Execute search via callback and display results."""
        if not self._search_input:
            return

        search_term = self._search_input.text().strip()

        # Validate search term
        if not search_term:
            if self._status_label:
                self._status_label.setText("Please enter a search term")
                self._status_label.setStyleSheet("color: orange;")
            return

        # Execute search via callback
        try:
            results = self._search_callback(search_term)
            self._current_results = results
            self._display_results(results)
        except Exception as e:
            # Handle search errors
            if self._status_label:
                self._status_label.setText(f"Search error: {str(e)}")
                self._status_label.setStyleSheet("color: red;")
            if self._results_list:
                self._results_list.clear()
            self._current_results = []

    def _display_results(self, results: list[SearchResultDTO]) -> None:
        """Display search results in list.

        Args:
            results: List of search results to display
        """
        if not self._results_list or not self._status_label:
            return

        # Clear previous results
        self._results_list.clear()

        # Update status
        if not results:
            self._status_label.setText("No results found")
            self._status_label.setStyleSheet("color: gray;")
            return

        self._status_label.setText(f"Found {len(results)} result(s)")
        self._status_label.setStyleSheet("color: green;")

        # Add results to list
        for result in results:
            # Format display text
            display_text = self._format_result_display(result)

            # Create list item
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, result)  # Store DTO in item data

            # Add to list
            self._results_list.addItem(item)

    def _format_result_display(self, result: SearchResultDTO) -> str:
        """Format search result for display in list.

        Args:
            result: Search result DTO

        Returns:
            Formatted display string
        """
        # Format: "Field Label (Entity Name) | Path: field.path | Value: current_value"
        display_parts = [f"{result.field_label} ({result.entity_name})"]
        display_parts.append(f"Path: {result.field_path}")

        if result.has_value():
            # Truncate value if too long
            value_str = str(result.current_value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
            display_parts.append(f"Value: {value_str}")
        else:
            display_parts.append("Value: (empty)")

        return " | ".join(display_parts)

    def _on_selection_changed(self) -> None:
        """Handle result selection change."""
        # Enable navigate button if item selected
        has_selection = bool(
            self._results_list and self._results_list.currentItem()
        )
        if self._navigate_button:
            self._navigate_button.setEnabled(has_selection)

    def _on_result_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle result double-click (navigate to field).

        Args:
            item: Double-clicked list item
        """
        self._navigate_to_selected_result(item)

    def _on_navigate(self) -> None:
        """Handle Navigate button click."""
        if not self._results_list:
            return

        current_item = self._results_list.currentItem()
        if current_item:
            self._navigate_to_selected_result(current_item)

    def _navigate_to_selected_result(self, item: QListWidgetItem) -> None:
        """Navigate to field from selected result.

        Args:
            item: Selected list item containing SearchResultDTO
        """
        # Retrieve SearchResultDTO from item data
        result = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(result, SearchResultDTO):
            return

        # Execute navigate callback with field path
        try:
            self._navigate_callback(result.field_path)
            # Close dialog after successful navigation
            self.close()
        except Exception as e:
            # Show error if navigation fails
            if self._status_label:
                self._status_label.setText(f"Navigation error: {str(e)}")
                self._status_label.setStyleSheet("color: red;")

    @staticmethod
    def show_search(
        parent: Optional[QWidget],
        search_callback: Callable[[str], list[SearchResultDTO]],
        navigate_callback: Callable[[str], None],
    ) -> None:
        """Show search dialog (non-modal).

        Args:
            parent: Parent widget
            search_callback: Callback to execute search
            navigate_callback: Callback to navigate to field

        Note: Dialog is non-modal so users can see form while searching
        """
        dialog = SearchDialog(parent, search_callback, navigate_callback)
        dialog.show()  # Non-modal show (not exec)

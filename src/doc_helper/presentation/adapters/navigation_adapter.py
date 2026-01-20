"""Qt adapter for navigation history.

Bridges framework-independent NavigationHistory to PyQt6 signals for UI integration.
"""

from PyQt6.QtCore import QObject, pyqtSignal

from doc_helper.application.navigation.navigation_entry import NavigationEntry
from doc_helper.application.navigation.navigation_history import NavigationHistory


class NavigationAdapter(QObject):
    """Qt signal adapter for NavigationHistory.

    Provides Qt signals for navigation state changes, allowing UI components
    to react to navigation events.

    Signals:
        navigation_changed(entity_id, group_id, field_id): Navigation changed
        entity_changed(entity_id): Entity/tab changed
        can_go_back_changed(bool): Back navigation availability changed
        can_go_forward_changed(bool): Forward navigation availability changed

    Example:
        nav_history = NavigationHistory()
        adapter = NavigationAdapter(nav_history)

        # Connect to signals
        adapter.navigation_changed.connect(on_nav_changed)
        adapter.can_go_back_changed.connect(update_back_button)

        # Navigate
        adapter.navigate_to_entity("project_info")
        adapter.go_back()
    """

    # Signals
    navigation_changed = pyqtSignal(str, str, str)  # (entity_id, group_id, field_id)
    entity_changed = pyqtSignal(str)  # (entity_id)
    can_go_back_changed = pyqtSignal(bool)
    can_go_forward_changed = pyqtSignal(bool)

    def __init__(self, navigation_history: NavigationHistory) -> None:
        """Initialize NavigationAdapter.

        Args:
            navigation_history: Framework-independent navigation history service
        """
        super().__init__()
        self._navigation_history = navigation_history

        # Subscribe to navigation history changes
        self._navigation_history.subscribe_to_changes(self._on_navigation_changed)
        self._navigation_history.subscribe_to_back_state(
            self._on_back_state_changed
        )
        self._navigation_history.subscribe_to_forward_state(
            self._on_forward_state_changed
        )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def can_go_back(self) -> bool:
        """Check if back navigation is available."""
        return self._navigation_history.can_go_back

    @property
    def can_go_forward(self) -> bool:
        """Check if forward navigation is available."""
        return self._navigation_history.can_go_forward

    @property
    def current_entity_id(self) -> str:
        """Get current entity ID."""
        return self._navigation_history.current_entity_id or ""

    @property
    def current_group_id(self) -> str:
        """Get current group ID."""
        return self._navigation_history.current_group_id or ""

    @property
    def current_field_id(self) -> str:
        """Get current field ID."""
        return self._navigation_history.current_field_id or ""

    # -------------------------------------------------------------------------
    # Navigation methods
    # -------------------------------------------------------------------------

    def navigate_to_entity(self, entity_id: str) -> None:
        """Navigate to an entity/tab.

        Args:
            entity_id: Entity identifier
        """
        entry = NavigationEntry(entity_id=entity_id)
        self._navigation_history.navigate_to(entry)

    def navigate_to_group(self, entity_id: str, group_id: str) -> None:
        """Navigate to a group within an entity.

        Args:
            entity_id: Entity identifier
            group_id: Group identifier
        """
        entry = NavigationEntry(entity_id=entity_id, group_id=group_id)
        self._navigation_history.navigate_to(entry)

    def navigate_to_field(
        self, entity_id: str, group_id: str, field_id: str
    ) -> None:
        """Navigate to a specific field.

        Args:
            entity_id: Entity identifier
            group_id: Group identifier
            field_id: Field identifier
        """
        entry = NavigationEntry(
            entity_id=entity_id, group_id=group_id, field_id=field_id
        )
        self._navigation_history.navigate_to(entry)

    def go_back(self) -> bool:
        """Navigate back in history.

        Returns:
            True if navigation was performed, False if at beginning
        """
        return self._navigation_history.go_back()

    def go_forward(self) -> bool:
        """Navigate forward in history.

        Returns:
            True if navigation was performed, False if at end
        """
        return self._navigation_history.go_forward()

    def clear(self) -> None:
        """Clear all navigation state and history."""
        self._navigation_history.clear()

    # -------------------------------------------------------------------------
    # Serialization (for state persistence)
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize navigation state to dictionary for persistence.

        Returns:
            Dictionary containing current state and history
        """
        return self._navigation_history.to_dict()

    def restore_from_dict(self, data: dict) -> None:
        """Restore navigation state from dictionary.

        Args:
            data: Dictionary containing serialized state
        """
        self._navigation_history.restore_from_dict(data)

    # -------------------------------------------------------------------------
    # Observer callbacks (convert to Qt signals)
    # -------------------------------------------------------------------------

    def _on_navigation_changed(self, entry: NavigationEntry) -> None:
        """Handle navigation change from NavigationHistory.

        Args:
            entry: New navigation entry
        """
        self.navigation_changed.emit(
            entry.entity_id,
            entry.group_id or "",
            entry.field_id or "",
        )

        # Emit entity change if entity changed
        # (Note: In v1 with single entity, this may not be used much,
        # but included for completeness)
        self.entity_changed.emit(entry.entity_id)

    def _on_back_state_changed(self, can_go_back: bool) -> None:
        """Handle can_go_back state change from NavigationHistory.

        Args:
            can_go_back: Whether back navigation is available
        """
        self.can_go_back_changed.emit(can_go_back)

    def _on_forward_state_changed(self, can_go_forward: bool) -> None:
        """Handle can_go_forward state change from NavigationHistory.

        Args:
            can_go_forward: Whether forward navigation is available
        """
        self.can_go_forward_changed.emit(can_go_forward)

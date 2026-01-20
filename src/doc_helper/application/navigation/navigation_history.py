"""Navigation history service (framework-independent).

Tracks navigation history and provides back/forward navigation without
framework dependencies. Uses observer pattern for change notifications.
"""

from typing import Callable, List, Optional

from doc_helper.application.navigation.navigation_entry import NavigationEntry


class NavigationHistory:
    """Framework-independent navigation history manager.

    Tracks current navigation location and history stack with back/forward support.
    Uses observer pattern for change notifications (no Qt signals).

    Example:
        history = NavigationHistory(max_size=50)

        # Subscribe to changes
        def on_navigation_changed(entry: NavigationEntry):
            print(f"Navigated to {entry.entity_id}")

        history.subscribe_to_changes(on_navigation_changed)

        # Navigate
        history.navigate_to(NavigationEntry(entity_id="project_info"))
        history.navigate_to(NavigationEntry(entity_id="borehole"))

        # Go back
        history.go_back()  # Returns to project_info
    """

    DEFAULT_MAX_SIZE = 50

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE) -> None:
        """Initialize NavigationHistory.

        Args:
            max_size: Maximum history stack size (default: 50)
        """
        self._max_size = max_size

        # Current navigation state
        self._current_entry: Optional[NavigationEntry] = None

        # History stack
        self._history: List[NavigationEntry] = []
        self._history_index: int = -1
        self._is_navigating_history: bool = False

        # Observers (callback functions)
        self._change_observers: List[Callable[[NavigationEntry], None]] = []
        self._back_state_observers: List[Callable[[bool], None]] = []
        self._forward_state_observers: List[Callable[[bool], None]] = []

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def current_entry(self) -> Optional[NavigationEntry]:
        """Get current navigation entry."""
        return self._current_entry

    @property
    def current_entity_id(self) -> Optional[str]:
        """Get current entity ID."""
        return self._current_entry.entity_id if self._current_entry else None

    @property
    def current_group_id(self) -> Optional[str]:
        """Get current group ID."""
        return self._current_entry.group_id if self._current_entry else None

    @property
    def current_field_id(self) -> Optional[str]:
        """Get current field ID."""
        return self._current_entry.field_id if self._current_entry else None

    @property
    def can_go_back(self) -> bool:
        """Check if back navigation is available."""
        return self._history_index > 0

    @property
    def can_go_forward(self) -> bool:
        """Check if forward navigation is available."""
        return self._history_index < len(self._history) - 1

    # -------------------------------------------------------------------------
    # Navigation methods
    # -------------------------------------------------------------------------

    def navigate_to(self, entry: NavigationEntry) -> None:
        """Navigate to a location.

        Args:
            entry: Navigation entry to navigate to

        Note:
            If navigating to same entry as current, does nothing.
            Adds entry to history unless navigating via back/forward.
        """
        # Don't navigate to same location
        if self._current_entry == entry:
            return

        self._current_entry = entry

        # Add to history (unless navigating history)
        if not self._is_navigating_history:
            self._add_to_history(entry)

        # Notify observers
        self._notify_change_observers()

    def go_back(self) -> bool:
        """Navigate back in history.

        Returns:
            True if navigation was performed, False if at beginning
        """
        if not self.can_go_back:
            return False

        self._is_navigating_history = True
        self._history_index -= 1
        entry = self._history[self._history_index]

        self._current_entry = entry
        self._notify_change_observers()

        self._is_navigating_history = False
        self._notify_history_state_observers()
        return True

    def go_forward(self) -> bool:
        """Navigate forward in history.

        Returns:
            True if navigation was performed, False if at end
        """
        if not self.can_go_forward:
            return False

        self._is_navigating_history = True
        self._history_index += 1
        entry = self._history[self._history_index]

        self._current_entry = entry
        self._notify_change_observers()

        self._is_navigating_history = False
        self._notify_history_state_observers()
        return True

    def clear(self) -> None:
        """Clear all navigation state and history."""
        self._current_entry = None
        self._history.clear()
        self._history_index = -1

        self._notify_change_observers()
        self._notify_history_state_observers()

    # -------------------------------------------------------------------------
    # Observer pattern (for change notifications)
    # -------------------------------------------------------------------------

    def subscribe_to_changes(
        self, observer: Callable[[NavigationEntry], None]
    ) -> None:
        """Subscribe to navigation changes.

        Args:
            observer: Callback function called when navigation changes
                     Receives NavigationEntry parameter
        """
        if observer not in self._change_observers:
            self._change_observers.append(observer)

    def unsubscribe_from_changes(
        self, observer: Callable[[NavigationEntry], None]
    ) -> None:
        """Unsubscribe from navigation changes.

        Args:
            observer: Callback function to remove
        """
        if observer in self._change_observers:
            self._change_observers.remove(observer)

    def subscribe_to_back_state(self, observer: Callable[[bool], None]) -> None:
        """Subscribe to can_go_back state changes.

        Args:
            observer: Callback function called when can_go_back changes
                     Receives bool parameter (True if can go back)
        """
        if observer not in self._back_state_observers:
            self._back_state_observers.append(observer)

    def unsubscribe_from_back_state(
        self, observer: Callable[[bool], None]
    ) -> None:
        """Unsubscribe from can_go_back state changes.

        Args:
            observer: Callback function to remove
        """
        if observer in self._back_state_observers:
            self._back_state_observers.remove(observer)

    def subscribe_to_forward_state(
        self, observer: Callable[[bool], None]
    ) -> None:
        """Subscribe to can_go_forward state changes.

        Args:
            observer: Callback function called when can_go_forward changes
                     Receives bool parameter (True if can go forward)
        """
        if observer not in self._forward_state_observers:
            self._forward_state_observers.append(observer)

    def unsubscribe_from_forward_state(
        self, observer: Callable[[bool], None]
    ) -> None:
        """Unsubscribe from can_go_forward state changes.

        Args:
            observer: Callback function to remove
        """
        if observer in self._forward_state_observers:
            self._forward_state_observers.remove(observer)

    # -------------------------------------------------------------------------
    # Serialization (for state persistence)
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize navigation state to dictionary for persistence.

        Returns:
            Dictionary containing current state and history
        """
        return {
            "current_entry": (
                self._current_entry.to_dict() if self._current_entry else None
            ),
            "history": [entry.to_dict() for entry in self._history],
            "history_index": self._history_index,
        }

    def restore_from_dict(self, data: dict) -> None:
        """Restore navigation state from dictionary.

        Args:
            data: Dictionary containing serialized state
        """
        if not data:
            return

        # Restore current entry
        current_data = data.get("current_entry")
        self._current_entry = (
            NavigationEntry.from_dict(current_data) if current_data else None
        )

        # Restore history
        self._history.clear()
        for entry_data in data.get("history", []):
            entry = NavigationEntry.from_dict(entry_data)
            self._history.append(entry)

        # Restore history index
        self._history_index = data.get("history_index", -1)

        # Validate history index
        if self._history_index >= len(self._history):
            self._history_index = len(self._history) - 1

        # Notify observers
        self._notify_change_observers()
        self._notify_history_state_observers()

    # -------------------------------------------------------------------------
    # Internal methods
    # -------------------------------------------------------------------------

    def _add_to_history(self, entry: NavigationEntry) -> None:
        """Add entry to history stack.

        Args:
            entry: Navigation entry to add

        Note:
            - Removes forward history when navigating to new location
            - Does not add duplicate consecutive entries
            - Trims history if exceeds max size
        """
        # Don't add duplicate consecutive entries
        if self._history and self._history_index >= 0:
            if self._history[self._history_index] == entry:
                return

        # Remove forward history when navigating to new location
        if self._history_index < len(self._history) - 1:
            self._history = self._history[: self._history_index + 1]

        # Add new entry
        self._history.append(entry)
        self._history_index = len(self._history) - 1

        # Trim history if too large
        if len(self._history) > self._max_size:
            excess = len(self._history) - self._max_size
            self._history = self._history[excess:]
            self._history_index -= excess

        self._notify_history_state_observers()

    def _notify_change_observers(self) -> None:
        """Notify all change observers of navigation change."""
        if self._current_entry:
            for observer in self._change_observers:
                try:
                    observer(self._current_entry)
                except Exception:
                    # Ignore observer errors
                    pass

    def _notify_history_state_observers(self) -> None:
        """Notify all history state observers (can_go_back, can_go_forward)."""
        # Notify back state observers
        can_back = self.can_go_back
        for observer in self._back_state_observers:
            try:
                observer(can_back)
            except Exception:
                pass

        # Notify forward state observers
        can_forward = self.can_go_forward
        for observer in self._forward_state_observers:
            try:
                observer(can_forward)
            except Exception:
                pass

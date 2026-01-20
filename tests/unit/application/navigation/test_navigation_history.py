"""Unit tests for NavigationHistory service."""

import pytest

from doc_helper.application.navigation.navigation_entry import NavigationEntry
from doc_helper.application.navigation.navigation_history import NavigationHistory


class TestNavigationHistory:
    """Test NavigationHistory service."""

    def test_initial_state(self):
        """Test initial state of NavigationHistory."""
        history = NavigationHistory()

        assert history.current_entry is None
        assert history.current_entity_id is None
        assert history.current_group_id is None
        assert history.current_field_id is None
        assert not history.can_go_back
        assert not history.can_go_forward

    def test_navigate_to_entity(self):
        """Test navigating to an entity."""
        history = NavigationHistory()
        entry = NavigationEntry(entity_id="project_info")

        history.navigate_to(entry)

        assert history.current_entry == entry
        assert history.current_entity_id == "project_info"
        assert history.current_group_id is None
        assert history.current_field_id is None
        assert not history.can_go_back  # First entry, no back
        assert not history.can_go_forward

    def test_navigate_to_group(self):
        """Test navigating to a group within entity."""
        history = NavigationHistory()
        entry = NavigationEntry(entity_id="borehole", group_id="location")

        history.navigate_to(entry)

        assert history.current_entity_id == "borehole"
        assert history.current_group_id == "location"
        assert history.current_field_id is None

    def test_navigate_to_field(self):
        """Test navigating to a field."""
        history = NavigationHistory()
        entry = NavigationEntry(
            entity_id="borehole", group_id="location", field_id="depth"
        )

        history.navigate_to(entry)

        assert history.current_entity_id == "borehole"
        assert history.current_group_id == "location"
        assert history.current_field_id == "depth"

    def test_navigate_to_same_location_does_nothing(self):
        """Test that navigating to same location doesn't add to history."""
        history = NavigationHistory()
        entry = NavigationEntry(entity_id="project_info")

        history.navigate_to(entry)
        history.navigate_to(entry)  # Navigate to same location again

        # Should still have only one entry
        assert not history.can_go_back

    def test_multiple_navigation_creates_history(self):
        """Test that multiple navigations create history stack."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")
        entry3 = NavigationEntry(entity_id="test_results")

        history.navigate_to(entry1)
        history.navigate_to(entry2)
        history.navigate_to(entry3)

        assert history.current_entry == entry3
        assert history.can_go_back
        assert not history.can_go_forward

    def test_go_back_single_step(self):
        """Test going back one step in history."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")

        history.navigate_to(entry1)
        history.navigate_to(entry2)

        # Go back
        result = history.go_back()

        assert result is True
        assert history.current_entry == entry1
        assert history.can_go_forward
        assert not history.can_go_back

    def test_go_back_multiple_steps(self):
        """Test going back multiple steps."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")
        entry3 = NavigationEntry(entity_id="test_results")

        history.navigate_to(entry1)
        history.navigate_to(entry2)
        history.navigate_to(entry3)

        # Go back twice
        history.go_back()
        history.go_back()

        assert history.current_entry == entry1
        assert not history.can_go_back
        assert history.can_go_forward

    def test_go_back_at_beginning_returns_false(self):
        """Test that go_back at beginning returns False."""
        history = NavigationHistory()
        entry = NavigationEntry(entity_id="project_info")

        history.navigate_to(entry)

        # Try to go back when at beginning
        result = history.go_back()

        assert result is False
        assert history.current_entry == entry

    def test_go_forward_single_step(self):
        """Test going forward one step."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")

        history.navigate_to(entry1)
        history.navigate_to(entry2)
        history.go_back()

        # Go forward
        result = history.go_forward()

        assert result is True
        assert history.current_entry == entry2
        assert history.can_go_back
        assert not history.can_go_forward

    def test_go_forward_multiple_steps(self):
        """Test going forward multiple steps."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")
        entry3 = NavigationEntry(entity_id="test_results")

        history.navigate_to(entry1)
        history.navigate_to(entry2)
        history.navigate_to(entry3)
        history.go_back()
        history.go_back()

        # Go forward twice
        history.go_forward()
        history.go_forward()

        assert history.current_entry == entry3
        assert history.can_go_back
        assert not history.can_go_forward

    def test_go_forward_at_end_returns_false(self):
        """Test that go_forward at end returns False."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")

        history.navigate_to(entry1)
        history.navigate_to(entry2)

        # Try to go forward when at end
        result = history.go_forward()

        assert result is False
        assert history.current_entry == entry2

    def test_new_navigation_clears_forward_history(self):
        """Test that new navigation clears forward history."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")
        entry3 = NavigationEntry(entity_id="test_results")
        entry4 = NavigationEntry(entity_id="samples")

        history.navigate_to(entry1)
        history.navigate_to(entry2)
        history.navigate_to(entry3)
        history.go_back()  # Now at entry2, can go forward to entry3

        # Navigate to new location - should clear entry3 from forward history
        history.navigate_to(entry4)

        assert history.current_entry == entry4
        assert not history.can_go_forward  # Forward history cleared

        # Go back should return to entry2, not entry3
        history.go_back()
        assert history.current_entry == entry2

    def test_clear_resets_all_state(self):
        """Test that clear resets all navigation state."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")

        history.navigate_to(entry1)
        history.navigate_to(entry2)

        # Clear
        history.clear()

        assert history.current_entry is None
        assert history.current_entity_id is None
        assert not history.can_go_back
        assert not history.can_go_forward

    def test_max_size_trims_history(self):
        """Test that history is trimmed when exceeding max size."""
        history = NavigationHistory(max_size=3)

        # Add 5 entries (exceeds max of 3)
        for i in range(5):
            entry = NavigationEntry(entity_id=f"entity_{i}")
            history.navigate_to(entry)

        # Should only keep last 3 entries
        # Go back twice to check
        history.go_back()
        history.go_back()

        # Should be at entity_2
        assert history.current_entity_id == "entity_2"

        # Should not be able to go back further (entity_0 and entity_1 trimmed)
        assert not history.can_go_back

    def test_duplicate_consecutive_entries_not_added(self):
        """Test that duplicate consecutive entries are not added to history."""
        history = NavigationHistory()
        entry = NavigationEntry(entity_id="project_info")

        # Add same entry through history (not via navigate_to which checks)
        history._history.append(entry)
        history._history_index = 0
        history._current_entry = entry

        # Try to add duplicate
        history._add_to_history(entry)

        # Should still have only one entry
        assert len(history._history) == 1

    def test_change_observer_notification(self):
        """Test that change observers are notified on navigation."""
        history = NavigationHistory()
        entry = NavigationEntry(entity_id="project_info")

        # Track notifications
        notifications = []

        def observer(nav_entry: NavigationEntry) -> None:
            notifications.append(nav_entry)

        history.subscribe_to_changes(observer)

        # Navigate
        history.navigate_to(entry)

        assert len(notifications) == 1
        assert notifications[0] == entry

    def test_change_observer_multiple_notifications(self):
        """Test change observer receives multiple notifications."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")

        notifications = []

        def observer(nav_entry: NavigationEntry) -> None:
            notifications.append(nav_entry)

        history.subscribe_to_changes(observer)

        history.navigate_to(entry1)
        history.navigate_to(entry2)

        assert len(notifications) == 2
        assert notifications[0] == entry1
        assert notifications[1] == entry2

    def test_back_state_observer_notification(self):
        """Test that back state observers are notified."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")

        back_states = []

        def observer(can_back: bool) -> None:
            back_states.append(can_back)

        history.subscribe_to_back_state(observer)

        history.navigate_to(entry1)
        history.navigate_to(entry2)  # Now can go back

        # Should have been notified
        assert True in back_states

    def test_forward_state_observer_notification(self):
        """Test that forward state observers are notified."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")

        forward_states = []

        def observer(can_forward: bool) -> None:
            forward_states.append(can_forward)

        history.subscribe_to_forward_state(observer)

        history.navigate_to(entry1)
        history.navigate_to(entry2)
        history.go_back()  # Now can go forward

        # Should have been notified
        assert True in forward_states

    def test_unsubscribe_from_changes(self):
        """Test unsubscribing from change notifications."""
        history = NavigationHistory()
        entry = NavigationEntry(entity_id="project_info")

        notifications = []

        def observer(nav_entry: NavigationEntry) -> None:
            notifications.append(nav_entry)

        history.subscribe_to_changes(observer)
        history.navigate_to(entry)

        # Unsubscribe
        history.unsubscribe_from_changes(observer)

        # Navigate again
        entry2 = NavigationEntry(entity_id="borehole")
        history.navigate_to(entry2)

        # Should only have first notification
        assert len(notifications) == 1

    def test_observer_error_does_not_crash(self):
        """Test that observer errors don't crash the history."""
        history = NavigationHistory()
        entry = NavigationEntry(entity_id="project_info")

        def bad_observer(nav_entry: NavigationEntry) -> None:
            raise ValueError("Observer error")

        history.subscribe_to_changes(bad_observer)

        # Should not raise
        history.navigate_to(entry)

        # Navigation should still work
        assert history.current_entry == entry

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        history = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole")

        history.navigate_to(entry1)
        history.navigate_to(entry2)

        data = history.to_dict()

        assert "current_entry" in data
        assert "history" in data
        assert "history_index" in data
        assert data["current_entry"]["entity_id"] == "borehole"
        assert len(data["history"]) == 2
        assert data["history_index"] == 1

    def test_to_dict_with_no_current_entry(self):
        """Test serialization with no current entry."""
        history = NavigationHistory()

        data = history.to_dict()

        assert data["current_entry"] is None
        assert data["history"] == []
        assert data["history_index"] == -1

    def test_restore_from_dict(self):
        """Test deserialization from dictionary."""
        history = NavigationHistory()

        data = {
            "current_entry": {
                "entity_id": "borehole",
                "group_id": "location",
                "field_id": None,
            },
            "history": [
                {"entity_id": "project_info", "group_id": None, "field_id": None},
                {
                    "entity_id": "borehole",
                    "group_id": "location",
                    "field_id": None,
                },
            ],
            "history_index": 1,
        }

        history.restore_from_dict(data)

        assert history.current_entity_id == "borehole"
        assert history.current_group_id == "location"
        assert history.can_go_back
        assert not history.can_go_forward

    def test_restore_from_dict_notifies_observers(self):
        """Test that restore_from_dict notifies observers."""
        history = NavigationHistory()

        notifications = []

        def observer(nav_entry: NavigationEntry) -> None:
            notifications.append(nav_entry)

        history.subscribe_to_changes(observer)

        data = {
            "current_entry": {"entity_id": "borehole", "group_id": None, "field_id": None},
            "history": [
                {"entity_id": "borehole", "group_id": None, "field_id": None}
            ],
            "history_index": 0,
        }

        history.restore_from_dict(data)

        assert len(notifications) == 1
        assert notifications[0].entity_id == "borehole"

    def test_restore_from_dict_with_empty_data(self):
        """Test restore with empty/None data does nothing."""
        history = NavigationHistory()
        entry = NavigationEntry(entity_id="project_info")
        history.navigate_to(entry)

        # Try to restore with None
        history.restore_from_dict(None)

        # Should still have original state
        assert history.current_entry == entry

    def test_restore_from_dict_validates_history_index(self):
        """Test that restore validates history index."""
        history = NavigationHistory()

        data = {
            "current_entry": {"entity_id": "borehole", "group_id": None, "field_id": None},
            "history": [
                {"entity_id": "borehole", "group_id": None, "field_id": None}
            ],
            "history_index": 999,  # Invalid index
        }

        history.restore_from_dict(data)

        # Index should be clamped to valid range
        assert history._history_index == 0

    def test_round_trip_serialization(self):
        """Test that serialization->deserialization preserves state."""
        history1 = NavigationHistory()
        entry1 = NavigationEntry(entity_id="project_info")
        entry2 = NavigationEntry(entity_id="borehole", group_id="location")
        entry3 = NavigationEntry(
            entity_id="borehole", group_id="location", field_id="depth"
        )

        history1.navigate_to(entry1)
        history1.navigate_to(entry2)
        history1.navigate_to(entry3)
        history1.go_back()

        # Serialize
        data = history1.to_dict()

        # Deserialize into new instance
        history2 = NavigationHistory()
        history2.restore_from_dict(data)

        # Should have same state
        assert history2.current_entry == history1.current_entry
        assert history2.can_go_back == history1.can_go_back
        assert history2.can_go_forward == history1.can_go_forward

    def test_complex_navigation_sequence(self):
        """Test a complex sequence of navigation operations."""
        history = NavigationHistory()

        # Navigate to multiple locations
        history.navigate_to(NavigationEntry(entity_id="project_info"))
        history.navigate_to(
            NavigationEntry(entity_id="borehole", group_id="location")
        )
        history.navigate_to(
            NavigationEntry(entity_id="borehole", group_id="location", field_id="depth")
        )
        history.navigate_to(NavigationEntry(entity_id="test_results"))

        # Go back twice
        history.go_back()
        history.go_back()

        # Should be at borehole/location
        assert history.current_entity_id == "borehole"
        assert history.current_group_id == "location"
        assert history.current_field_id is None

        # Navigate to new location (clears forward history)
        history.navigate_to(NavigationEntry(entity_id="samples"))

        # Can't go forward to test_results anymore
        assert not history.can_go_forward

        # But can go back
        assert history.can_go_back

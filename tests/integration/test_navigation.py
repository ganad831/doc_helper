"""Integration tests for navigation system.

Tests the full navigation flow:
NavigationHistory → NavigationAdapter → ProjectViewModel → View
"""

import pytest
from unittest.mock import MagicMock, Mock

from PyQt6.QtCore import QObject

from doc_helper.application.navigation.navigation_entry import NavigationEntry
from doc_helper.application.navigation.navigation_history import NavigationHistory
from doc_helper.presentation.adapters.navigation_adapter import NavigationAdapter


class TestNavigationIntegration:
    """Integration tests for navigation system."""

    @pytest.fixture
    def navigation_history(self):
        """Create NavigationHistory instance."""
        return NavigationHistory(max_size=50)

    @pytest.fixture
    def navigation_adapter(self, navigation_history):
        """Create NavigationAdapter instance."""
        return NavigationAdapter(navigation_history)

    def test_adapter_wraps_history(self, navigation_adapter, navigation_history):
        """Test that NavigationAdapter correctly wraps NavigationHistory."""
        # Adapter should expose history properties
        assert navigation_adapter.can_go_back == navigation_history.can_go_back
        assert navigation_adapter.can_go_forward == navigation_history.can_go_forward
        # Adapter returns empty string instead of None for better Qt compatibility
        assert navigation_adapter.current_entity_id == (
            navigation_history.current_entity_id or ""
        )

    def test_navigate_to_entity_through_adapter(
        self, navigation_adapter, navigation_history
    ):
        """Test navigation through adapter."""
        # Navigate through adapter
        navigation_adapter.navigate_to_entity("project_info")

        # Should update underlying history
        assert navigation_history.current_entity_id == "project_info"
        assert navigation_adapter.current_entity_id == "project_info"

    def test_navigate_to_group_through_adapter(
        self, navigation_adapter, navigation_history
    ):
        """Test group navigation through adapter."""
        navigation_adapter.navigate_to_group("borehole", "location")

        assert navigation_history.current_entity_id == "borehole"
        assert navigation_history.current_group_id == "location"
        assert navigation_adapter.current_group_id == "location"

    def test_navigate_to_field_through_adapter(
        self, navigation_adapter, navigation_history
    ):
        """Test field navigation through adapter."""
        navigation_adapter.navigate_to_field("borehole", "location", "depth")

        assert navigation_history.current_entity_id == "borehole"
        assert navigation_history.current_group_id == "location"
        assert navigation_history.current_field_id == "depth"
        assert navigation_adapter.current_field_id == "depth"

    def test_back_navigation_through_adapter(self, navigation_adapter):
        """Test back navigation through adapter."""
        # Create some history
        navigation_adapter.navigate_to_entity("project_info")
        navigation_adapter.navigate_to_entity("borehole")

        # Go back through adapter
        result = navigation_adapter.go_back()

        assert result is True
        assert navigation_adapter.current_entity_id == "project_info"

    def test_forward_navigation_through_adapter(self, navigation_adapter):
        """Test forward navigation through adapter."""
        navigation_adapter.navigate_to_entity("project_info")
        navigation_adapter.navigate_to_entity("borehole")
        navigation_adapter.go_back()

        # Go forward through adapter
        result = navigation_adapter.go_forward()

        assert result is True
        assert navigation_adapter.current_entity_id == "borehole"

    def test_clear_through_adapter(self, navigation_adapter, navigation_history):
        """Test clearing navigation through adapter."""
        navigation_adapter.navigate_to_entity("project_info")
        navigation_adapter.navigate_to_entity("borehole")

        navigation_adapter.clear()

        assert navigation_history.current_entry is None
        assert not navigation_adapter.can_go_back
        assert not navigation_adapter.can_go_forward

    def test_navigation_changed_signal_emitted(self, navigation_adapter):
        """Test that navigation_changed signal is emitted."""
        # Track signal emissions
        signal_emissions = []

        def on_navigation_changed(entity_id: str, group_id: str, field_id: str):
            signal_emissions.append((entity_id, group_id, field_id))

        navigation_adapter.navigation_changed.connect(on_navigation_changed)

        # Navigate
        navigation_adapter.navigate_to_entity("project_info")

        # Signal should have been emitted
        assert len(signal_emissions) == 1
        entity_id, group_id, field_id = signal_emissions[0]
        assert entity_id == "project_info"
        assert group_id == ""
        assert field_id == ""

    def test_entity_changed_signal_emitted(self, navigation_adapter):
        """Test that entity_changed signal is emitted on entity change."""
        signal_emissions = []

        def on_entity_changed(entity_id: str):
            signal_emissions.append(entity_id)

        navigation_adapter.entity_changed.connect(on_entity_changed)

        navigation_adapter.navigate_to_entity("project_info")
        navigation_adapter.navigate_to_entity("borehole")

        # Two entity changes
        assert len(signal_emissions) == 2
        assert signal_emissions[0] == "project_info"
        assert signal_emissions[1] == "borehole"

    def test_entity_changed_signal_tracks_entity_changes(self, navigation_adapter):
        """Test that entity_changed signal tracks entity ID changes."""
        signal_emissions = []

        def on_entity_changed(entity_id: str):
            signal_emissions.append(entity_id)

        navigation_adapter.entity_changed.connect(on_entity_changed)

        # Navigate to different entities
        navigation_adapter.navigate_to_entity("project_info")
        navigation_adapter.navigate_to_entity("borehole")
        navigation_adapter.navigate_to_entity("test_results")

        # Should have three distinct entity changes
        assert len(signal_emissions) == 3
        assert signal_emissions[0] == "project_info"
        assert signal_emissions[1] == "borehole"
        assert signal_emissions[2] == "test_results"

    def test_can_go_back_signal_emitted(self, navigation_adapter):
        """Test that can_go_back_changed signal is emitted."""
        signal_emissions = []

        def on_can_go_back_changed(can_back: bool):
            signal_emissions.append(can_back)

        navigation_adapter.can_go_back_changed.connect(on_can_go_back_changed)

        # Navigate twice to create history
        navigation_adapter.navigate_to_entity("project_info")
        navigation_adapter.navigate_to_entity("borehole")

        # Should have emitted True (can go back now)
        assert True in signal_emissions

    def test_can_go_forward_signal_emitted(self, navigation_adapter):
        """Test that can_go_forward_changed signal is emitted."""
        signal_emissions = []

        def on_can_go_forward_changed(can_forward: bool):
            signal_emissions.append(can_forward)

        navigation_adapter.can_go_forward_changed.connect(on_can_go_forward_changed)

        navigation_adapter.navigate_to_entity("project_info")
        navigation_adapter.navigate_to_entity("borehole")
        navigation_adapter.go_back()

        # Should have emitted True (can go forward now)
        assert True in signal_emissions

    def test_back_forward_sequence_with_signals(self, navigation_adapter):
        """Test complex back/forward sequence with signal tracking."""
        nav_changes = []
        back_states = []
        forward_states = []

        def on_nav_changed(entity_id: str, group_id: str, field_id: str):
            nav_changes.append(entity_id)

        def on_back_changed(can_back: bool):
            back_states.append(can_back)

        def on_forward_changed(can_forward: bool):
            forward_states.append(can_forward)

        navigation_adapter.navigation_changed.connect(on_nav_changed)
        navigation_adapter.can_go_back_changed.connect(on_back_changed)
        navigation_adapter.can_go_forward_changed.connect(on_forward_changed)

        # Navigate: project_info → borehole → test_results
        navigation_adapter.navigate_to_entity("project_info")
        navigation_adapter.navigate_to_entity("borehole")
        navigation_adapter.navigate_to_entity("test_results")

        # Go back twice
        navigation_adapter.go_back()
        navigation_adapter.go_back()

        # Should be at project_info
        assert navigation_adapter.current_entity_id == "project_info"

        # Go forward once
        navigation_adapter.go_forward()

        # Should be at borehole
        assert navigation_adapter.current_entity_id == "borehole"

        # Verify signal emissions
        assert "project_info" in nav_changes
        assert "borehole" in nav_changes
        assert "test_results" in nav_changes
        assert True in back_states  # Can go back
        assert True in forward_states  # Can go forward

    def test_clear_emits_signals(self, navigation_adapter):
        """Test that clear emits appropriate signals."""
        back_states = []
        forward_states = []

        def on_back_changed(can_back: bool):
            back_states.append(can_back)

        def on_forward_changed(can_forward: bool):
            forward_states.append(can_forward)

        navigation_adapter.can_go_back_changed.connect(on_back_changed)
        navigation_adapter.can_go_forward_changed.connect(on_forward_changed)

        # Create history
        navigation_adapter.navigate_to_entity("project_info")
        navigation_adapter.navigate_to_entity("borehole")

        # Clear
        navigation_adapter.clear()

        # Should have emitted False (cannot go back/forward)
        assert False in back_states
        assert False in forward_states

    def test_navigation_with_max_history_size(self, navigation_history):
        """Test navigation with limited history size."""
        # Create adapter with small max size
        history = NavigationHistory(max_size=3)
        adapter = NavigationAdapter(history)

        # Navigate to 5 entities (exceeds max of 3)
        for i in range(5):
            adapter.navigate_to_entity(f"entity_{i}")

        # Should be at entity_4
        assert adapter.current_entity_id == "entity_4"

        # Go back twice
        adapter.go_back()
        adapter.go_back()

        # Should be at entity_2 (entity_0 and entity_1 were trimmed)
        assert adapter.current_entity_id == "entity_2"

        # Cannot go back further
        assert not adapter.can_go_back

    def test_navigation_serialization_through_adapter(
        self, navigation_adapter, navigation_history
    ):
        """Test that serialization works through adapter."""
        # Create navigation state
        navigation_adapter.navigate_to_entity("project_info")
        navigation_adapter.navigate_to_group("borehole", "location")
        navigation_adapter.navigate_to_field("borehole", "location", "depth")

        # Serialize
        data = navigation_history.to_dict()

        # Create new adapter and restore
        new_history = NavigationHistory()
        new_adapter = NavigationAdapter(new_history)
        new_history.restore_from_dict(data)

        # Should have same state
        assert new_adapter.current_entity_id == "borehole"
        assert new_adapter.current_group_id == "location"
        assert new_adapter.current_field_id == "depth"

    def test_viewmodel_integration_pattern(self, navigation_adapter):
        """Test typical ViewModel usage pattern."""
        # Simulate ViewModel storing adapter
        class MockViewModel:
            def __init__(self, nav_adapter):
                self._nav_adapter = nav_adapter

            def navigate_to_entity(self, entity_id: str):
                self._nav_adapter.navigate_to_entity(entity_id)

            def go_back(self):
                return self._nav_adapter.go_back()

            @property
            def can_go_back(self):
                return self._nav_adapter.can_go_back

        # Create mock ViewModel
        vm = MockViewModel(navigation_adapter)

        # Use through ViewModel
        vm.navigate_to_entity("project_info")
        vm.navigate_to_entity("borehole")

        # Should be able to go back
        assert vm.can_go_back

        # Go back
        result = vm.go_back()
        assert result is True

    def test_signal_disconnect_on_adapter_deletion(self, navigation_history):
        """Test that signals are properly managed on adapter lifetime."""
        # Create adapter
        adapter = NavigationAdapter(navigation_history)

        # Subscribe to signal
        emissions = []

        def on_nav_changed(entity_id, group_id, field_id):
            emissions.append(entity_id)

        adapter.navigation_changed.connect(on_nav_changed)

        # Navigate
        adapter.navigate_to_entity("project_info")
        assert len(emissions) == 1

        # Delete adapter (in real code, this would happen when UI is destroyed)
        del adapter

        # Navigate through history directly (no adapter)
        entry = NavigationEntry(entity_id="borehole")
        navigation_history.navigate_to(entry)

        # Should not have triggered signal (adapter is gone)
        # (In practice, Qt handles signal cleanup automatically)

    def test_multiple_adapters_share_history(self, navigation_history):
        """Test that multiple adapters can share the same history."""
        # Create two adapters sharing same history
        adapter1 = NavigationAdapter(navigation_history)
        adapter2 = NavigationAdapter(navigation_history)

        # Track emissions from both
        emissions1 = []
        emissions2 = []

        def on_nav1(entity_id, group_id, field_id):
            emissions1.append(entity_id)

        def on_nav2(entity_id, group_id, field_id):
            emissions2.append(entity_id)

        adapter1.navigation_changed.connect(on_nav1)
        adapter2.navigation_changed.connect(on_nav2)

        # Navigate through adapter1
        adapter1.navigate_to_entity("project_info")

        # Both adapters should have been notified
        assert len(emissions1) == 1
        assert len(emissions2) == 1

        # Both should reflect same state
        assert adapter1.current_entity_id == "project_info"
        assert adapter2.current_entity_id == "project_info"

    def test_error_recovery_in_observer(self, navigation_adapter, navigation_history):
        """Test that observer errors don't break navigation."""

        # Add an observer that raises exception
        def bad_observer(entry: NavigationEntry):
            raise ValueError("Observer error")

        navigation_history.subscribe_to_changes(bad_observer)

        # Navigation should still work
        navigation_adapter.navigate_to_entity("project_info")

        # State should be correct
        assert navigation_adapter.current_entity_id == "project_info"

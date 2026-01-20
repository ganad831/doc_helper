"""Tests for BaseViewModel."""

import pytest

from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


class SampleViewModel(BaseViewModel):
    """Sample implementation of BaseViewModel for testing."""

    def __init__(self) -> None:
        """Initialize sample view model."""
        super().__init__()
        self._test_value = 0

    @property
    def test_value(self) -> int:
        """Get test value."""
        return self._test_value

    def set_test_value(self, value: int) -> None:
        """Set test value and notify."""
        self._test_value = value
        self.notify_change("test_value")


class TestBaseViewModel:
    """Tests for BaseViewModel."""

    def test_subscribe_and_notify(self) -> None:
        """Test subscribing to property changes and receiving notifications."""
        # Arrange
        viewmodel = SampleViewModel()
        callback_called = False
        received_value = None

        def callback() -> None:
            nonlocal callback_called, received_value
            callback_called = True
            received_value = viewmodel.test_value

        # Act
        viewmodel.subscribe("test_value", callback)
        viewmodel.set_test_value(42)

        # Assert
        assert callback_called
        assert received_value == 42

    def test_unsubscribe(self) -> None:
        """Test unsubscribing from property changes."""
        # Arrange
        viewmodel = SampleViewModel()
        callback_called = False

        def callback() -> None:
            nonlocal callback_called
            callback_called = True

        viewmodel.subscribe("test_value", callback)

        # Act
        viewmodel.unsubscribe("test_value", callback)
        viewmodel.set_test_value(42)

        # Assert
        assert not callback_called

    def test_multiple_subscribers(self) -> None:
        """Test multiple subscribers to same property."""
        # Arrange
        viewmodel = SampleViewModel()
        callback1_count = 0
        callback2_count = 0

        def callback1() -> None:
            nonlocal callback1_count
            callback1_count += 1

        def callback2() -> None:
            nonlocal callback2_count
            callback2_count += 1

        # Act
        viewmodel.subscribe("test_value", callback1)
        viewmodel.subscribe("test_value", callback2)
        viewmodel.set_test_value(1)
        viewmodel.set_test_value(2)

        # Assert
        assert callback1_count == 2
        assert callback2_count == 2

    def test_unsubscribe_one_of_multiple(self) -> None:
        """Test unsubscribing one callback while others remain."""
        # Arrange
        viewmodel = SampleViewModel()
        callback1_count = 0
        callback2_count = 0

        def callback1() -> None:
            nonlocal callback1_count
            callback1_count += 1

        def callback2() -> None:
            nonlocal callback2_count
            callback2_count += 1

        viewmodel.subscribe("test_value", callback1)
        viewmodel.subscribe("test_value", callback2)

        # Act
        viewmodel.unsubscribe("test_value", callback1)
        viewmodel.set_test_value(1)

        # Assert
        assert callback1_count == 0
        assert callback2_count == 1

    def test_dispose(self) -> None:
        """Test disposing viewmodel clears all subscriptions."""
        # Arrange
        viewmodel = SampleViewModel()
        callback_called = False

        def callback() -> None:
            nonlocal callback_called
            callback_called = True

        viewmodel.subscribe("test_value", callback)

        # Act
        viewmodel.dispose()
        viewmodel.set_test_value(42)

        # Assert
        assert not callback_called
        assert len(viewmodel._change_handlers) == 0

    def test_notify_nonexistent_property(self) -> None:
        """Test notifying change for property with no subscribers."""
        # Arrange
        viewmodel = SampleViewModel()

        # Act & Assert - should not raise exception
        viewmodel.notify_change("nonexistent_property")

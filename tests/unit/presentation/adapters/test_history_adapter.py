"""Unit tests for HistoryAdapter.

RULES (unified_upgrade_plan_FINAL.md U6 Phase 2):
- Test Qt signal emissions on state changes
- Verify method forwarding to UndoManager
- Test property delegation
- Test dispose() cleanup
"""

import pytest
from unittest.mock import MagicMock

from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.presentation.adapters.history_adapter import HistoryAdapter


@pytest.fixture
def undo_manager():
    """Create UndoManager instance."""
    return UndoManager()


@pytest.fixture
def adapter(undo_manager):
    """Create HistoryAdapter instance."""
    return HistoryAdapter(undo_manager)


def test_create_adapter(adapter):
    """Test: Adapter instance created successfully."""
    assert isinstance(adapter, HistoryAdapter)


def test_adapter_subscribes_to_undo_manager(undo_manager):
    """Test: Adapter subscribes to UndoManager on creation."""
    # Before creating adapter
    assert len(undo_manager._on_state_changed) == 0

    # Create adapter
    adapter = HistoryAdapter(undo_manager)

    # Verify subscription
    assert len(undo_manager._on_state_changed) == 1


def test_signals_emitted_on_state_change(adapter, undo_manager):
    """Test: Qt signals emitted when UndoManager state changes."""
    # Setup signal spies
    can_undo_spy = MagicMock()
    can_redo_spy = MagicMock()
    undo_text_spy = MagicMock()
    redo_text_spy = MagicMock()

    adapter.can_undo_changed.connect(can_undo_spy)
    adapter.can_redo_changed.connect(can_redo_spy)
    adapter.undo_text_changed.connect(undo_text_spy)
    adapter.redo_text_changed.connect(redo_text_spy)

    # Trigger state change by notifying manually
    undo_manager._notify_state_changed()

    # Verify signals emitted
    can_undo_spy.assert_called_once_with(False)  # No commands yet
    can_redo_spy.assert_called_once_with(False)  # No commands yet
    undo_text_spy.assert_called_once_with("")    # No description
    redo_text_spy.assert_called_once_with("")    # No description


def test_undo_method_forwards_to_manager(adapter, undo_manager):
    """Test: undo() method forwards to UndoManager.undo()."""
    # Setup: Add a mock command to undo stack
    from doc_helper.application.undo.undoable_command import UndoableCommand

    class MockCommand(UndoableCommand):
        def __init__(self):
            self.execute_called = False
            self.undo_called = False

        @property
        def command_type(self) -> str:
            return "mock_command"

        def execute(self) -> bool:
            self.execute_called = True
            return True

        def undo(self) -> bool:
            self.undo_called = True
            return True

        def redo(self) -> bool:
            return True

        @property
        def description(self) -> str:
            return "Mock command"

        def can_merge_with(self, other) -> bool:
            return False

        def merge_with(self, other):
            raise ValueError("Mock command does not support merging")

    command = MockCommand()
    undo_manager.execute(command)

    # Call adapter.undo()
    result = adapter.undo()

    # Verify forwarding
    assert result is True
    assert command.undo_called is True
    assert undo_manager.can_redo is True


def test_redo_method_forwards_to_manager(adapter, undo_manager):
    """Test: redo() method forwards to UndoManager.redo()."""
    # Setup: Add command and undo it
    from doc_helper.application.undo.undoable_command import UndoableCommand

    class MockCommand(UndoableCommand):
        def __init__(self):
            self.redo_called = False

        @property
        def command_type(self) -> str:
            return "mock_command"

        def execute(self) -> bool:
            return True

        def undo(self) -> bool:
            return True

        def redo(self) -> bool:
            self.redo_called = True
            return True

        @property
        def description(self) -> str:
            return "Mock command"

        def can_merge_with(self, other) -> bool:
            return False

        def merge_with(self, other):
            raise ValueError("Mock command does not support merging")

    command = MockCommand()
    undo_manager.execute(command)
    undo_manager.undo()

    # Call adapter.redo()
    result = adapter.redo()

    # Verify forwarding
    assert result is True
    assert command.redo_called is True


def test_clear_method_forwards_to_manager(adapter, undo_manager):
    """Test: clear() method forwards to UndoManager.clear()."""
    # Setup: Add command to undo stack
    from doc_helper.application.undo.undoable_command import UndoableCommand

    class MockCommand(UndoableCommand):
        @property
        def command_type(self) -> str:
            return "mock_command"

        def execute(self) -> bool:
            return True

        def undo(self) -> bool:
            return True

        def redo(self) -> bool:
            return True

        @property
        def description(self) -> str:
            return "Mock command"

        def can_merge_with(self, other) -> bool:
            return False

        def merge_with(self, other):
            raise ValueError("Mock command does not support merging")

    command = MockCommand()
    undo_manager.execute(command)
    assert undo_manager.can_undo is True

    # Call adapter.clear()
    adapter.clear()

    # Verify forwarding
    assert undo_manager.can_undo is False
    assert undo_manager.can_redo is False


def test_can_undo_property_delegates_to_manager(adapter, undo_manager):
    """Test: can_undo property delegates to UndoManager."""
    # Initial state
    assert adapter.can_undo is False
    assert adapter.can_undo == undo_manager.can_undo

    # Add command
    from doc_helper.application.undo.undoable_command import UndoableCommand

    class MockCommand(UndoableCommand):
        @property
        def command_type(self) -> str:
            return "mock_command"

        def execute(self) -> bool:
            return True

        def undo(self) -> bool:
            return True

        def redo(self) -> bool:
            return True

        @property
        def description(self) -> str:
            return "Mock command"

        def can_merge_with(self, other) -> bool:
            return False

        def merge_with(self, other):
            raise ValueError("Mock command does not support merging")

    undo_manager.execute(MockCommand())

    # Verify property updated
    assert adapter.can_undo is True
    assert adapter.can_undo == undo_manager.can_undo


def test_can_redo_property_delegates_to_manager(adapter, undo_manager):
    """Test: can_redo property delegates to UndoManager."""
    # Initial state
    assert adapter.can_redo is False
    assert adapter.can_redo == undo_manager.can_redo

    # Add command and undo
    from doc_helper.application.undo.undoable_command import UndoableCommand

    class MockCommand(UndoableCommand):
        @property
        def command_type(self) -> str:
            return "mock_command"

        def execute(self) -> bool:
            return True

        def undo(self) -> bool:
            return True

        def redo(self) -> bool:
            return True

        @property
        def description(self) -> str:
            return "Mock command"

        def can_merge_with(self, other) -> bool:
            return False

        def merge_with(self, other):
            raise ValueError("Mock command does not support merging")

    undo_manager.execute(MockCommand())
    undo_manager.undo()

    # Verify property updated
    assert adapter.can_redo is True
    assert adapter.can_redo == undo_manager.can_redo


def test_dispose_unsubscribes_from_manager(undo_manager):
    """Test: dispose() unsubscribes from UndoManager."""
    # Create adapter
    adapter = HistoryAdapter(undo_manager)
    assert len(undo_manager._on_state_changed) == 1

    # Dispose
    adapter.dispose()

    # Verify unsubscription
    assert len(undo_manager._on_state_changed) == 0


def test_signals_emitted_on_command_execution(adapter, undo_manager):
    """Test: Signals emitted when command executed via UndoManager."""
    # Setup signal spies
    can_undo_spy = MagicMock()
    can_redo_spy = MagicMock()

    adapter.can_undo_changed.connect(can_undo_spy)
    adapter.can_redo_changed.connect(can_redo_spy)

    # Execute command via UndoManager
    from doc_helper.application.undo.undoable_command import UndoableCommand

    class MockCommand(UndoableCommand):
        @property
        def command_type(self) -> str:
            return "mock_command"

        def execute(self) -> bool:
            return True

        def undo(self) -> bool:
            return True

        def redo(self) -> bool:
            return True

        @property
        def description(self) -> str:
            return "Mock command"

        def can_merge_with(self, other) -> bool:
            return False

        def merge_with(self, other):
            raise ValueError("Mock command does not support merging")

    undo_manager.execute(MockCommand())

    # Verify signals emitted
    assert can_undo_spy.called
    assert can_undo_spy.call_args[0][0] is True  # can_undo = True
    assert can_redo_spy.called
    assert can_redo_spy.call_args[0][0] is False  # can_redo = False (cleared)


def test_signals_emitted_on_undo_via_adapter(adapter, undo_manager):
    """Test: Signals emitted when undo() called via adapter."""
    # Setup: Add command
    from doc_helper.application.undo.undoable_command import UndoableCommand

    class MockCommand(UndoableCommand):
        @property
        def command_type(self) -> str:
            return "mock_command"

        def execute(self) -> bool:
            return True

        def undo(self) -> bool:
            return True

        def redo(self) -> bool:
            return True

        @property
        def description(self) -> str:
            return "Mock command"

        def can_merge_with(self, other) -> bool:
            return False

        def merge_with(self, other):
            raise ValueError("Mock command does not support merging")

    undo_manager.execute(MockCommand())

    # Setup signal spies AFTER initial command
    can_undo_spy = MagicMock()
    can_redo_spy = MagicMock()

    adapter.can_undo_changed.connect(can_undo_spy)
    adapter.can_redo_changed.connect(can_redo_spy)

    # Undo via adapter
    adapter.undo()

    # Verify signals emitted
    assert can_undo_spy.called
    assert can_undo_spy.call_args[0][0] is False  # can_undo = False (empty stack)
    assert can_redo_spy.called
    assert can_redo_spy.call_args[0][0] is True   # can_redo = True (command moved to redo)


def test_signals_emitted_on_clear_via_adapter(adapter, undo_manager):
    """Test: Signals emitted when clear() called via adapter."""
    # Setup: Add command
    from doc_helper.application.undo.undoable_command import UndoableCommand

    class MockCommand(UndoableCommand):
        @property
        def command_type(self) -> str:
            return "mock_command"

        def execute(self) -> bool:
            return True

        def undo(self) -> bool:
            return True

        def redo(self) -> bool:
            return True

        @property
        def description(self) -> str:
            return "Mock command"

        def can_merge_with(self, other) -> bool:
            return False

        def merge_with(self, other):
            raise ValueError("Mock command does not support merging")

    undo_manager.execute(MockCommand())

    # Setup signal spies AFTER initial command
    can_undo_spy = MagicMock()
    can_redo_spy = MagicMock()

    adapter.can_undo_changed.connect(can_undo_spy)
    adapter.can_redo_changed.connect(can_redo_spy)

    # Clear via adapter
    adapter.clear()

    # Verify signals emitted
    assert can_undo_spy.called
    assert can_undo_spy.call_args[0][0] is False  # can_undo = False (cleared)
    assert can_redo_spy.called
    assert can_redo_spy.call_args[0][0] is False  # can_redo = False (cleared)

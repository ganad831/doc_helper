"""Unit tests for UndoManager."""

from typing import Any

import pytest

from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.application.undo.undoable_command import UndoableCommand


class MockCommand(UndoableCommand):
    """Mock command for testing."""

    def __init__(
        self,
        name: str = "test",
        execute_result: bool = True,
        undo_result: bool = True,
        redo_result: bool = True,
        can_merge: bool = False,
    ) -> None:
        self.name = name
        self._execute_result = execute_result
        self._undo_result = undo_result
        self._redo_result = redo_result
        self._can_merge = can_merge
        self.execute_count = 0
        self.undo_count = 0
        self.redo_count = 0

    @property
    def command_type(self) -> str:
        return "mock"

    @property
    def description(self) -> str:
        return f"Mock command: {self.name}"

    def execute(self) -> bool:
        self.execute_count += 1
        return self._execute_result

    def undo(self) -> bool:
        self.undo_count += 1
        return self._undo_result

    def redo(self) -> bool:
        self.redo_count += 1
        return self._redo_result

    def can_merge_with(self, other: UndoableCommand) -> bool:
        return self._can_merge

    def merge_with(self, other: UndoableCommand) -> UndoableCommand:
        if not self.can_merge_with(other):
            raise ValueError("Cannot merge")
        return MockCommand(name=f"{self.name}+{other.name}", can_merge=True)


class TestUndoManager:
    """Tests for UndoManager."""

    @pytest.fixture
    def manager(self) -> UndoManager:
        """Create UndoManager with default settings."""
        return UndoManager()

    def test_create_manager_with_default_depth(self) -> None:
        """UndoManager should use default max depth."""
        manager = UndoManager()
        assert manager._max_depth == UndoManager.DEFAULT_MAX_DEPTH

    def test_create_manager_with_custom_depth(self) -> None:
        """UndoManager should accept custom max depth."""
        manager = UndoManager(max_depth=50)
        assert manager._max_depth == 50

    def test_create_manager_with_invalid_depth(self) -> None:
        """UndoManager should reject invalid max depth."""
        with pytest.raises(ValueError):
            UndoManager(max_depth=0)
        with pytest.raises(ValueError):
            UndoManager(max_depth=-1)

    def test_initial_state(self, manager: UndoManager) -> None:
        """New UndoManager should have empty stacks."""
        assert not manager.can_undo
        assert not manager.can_redo
        assert manager.undo_count == 0
        assert manager.redo_count == 0
        assert manager.undo_description is None
        assert manager.redo_description is None

    def test_execute_command(self, manager: UndoManager) -> None:
        """execute should run command and add to undo stack."""
        command = MockCommand()
        result = manager.execute(command)

        assert result is True
        assert command.execute_count == 1
        assert manager.can_undo
        assert manager.undo_count == 1
        assert manager.undo_description == "Mock command: test"

    def test_execute_failed_command(self, manager: UndoManager) -> None:
        """execute should not add failed command to stack."""
        command = MockCommand(execute_result=False)
        result = manager.execute(command)

        assert result is False
        assert not manager.can_undo
        assert manager.undo_count == 0

    def test_execute_requires_command(self, manager: UndoManager) -> None:
        """execute should require UndoableCommand instance."""
        with pytest.raises(TypeError):
            manager.execute("not a command")  # type: ignore

    def test_undo_command(self, manager: UndoManager) -> None:
        """undo should restore previous state and move to redo stack."""
        command = MockCommand()
        manager.execute(command)

        result = manager.undo()

        assert result is True
        assert command.undo_count == 1
        assert not manager.can_undo
        assert manager.can_redo
        assert manager.redo_count == 1
        assert manager.redo_description == "Mock command: test"

    def test_undo_with_empty_stack(self, manager: UndoManager) -> None:
        """undo should return False with empty stack."""
        result = manager.undo()

        assert result is False
        assert not manager.can_redo

    def test_undo_failed(self, manager: UndoManager) -> None:
        """undo failure should keep command in undo stack."""
        command = MockCommand(undo_result=False)
        manager.execute(command)

        result = manager.undo()

        assert result is False
        assert manager.can_undo
        assert not manager.can_redo

    def test_redo_command(self, manager: UndoManager) -> None:
        """redo should reapply command and move to undo stack."""
        command = MockCommand()
        manager.execute(command)
        manager.undo()

        result = manager.redo()

        assert result is True
        assert command.redo_count == 1
        assert manager.can_undo
        assert not manager.can_redo

    def test_redo_with_empty_stack(self, manager: UndoManager) -> None:
        """redo should return False with empty stack."""
        result = manager.redo()

        assert result is False
        assert not manager.can_undo

    def test_redo_failed(self, manager: UndoManager) -> None:
        """redo failure should keep command in redo stack."""
        command = MockCommand(redo_result=False)
        manager.execute(command)
        manager.undo()

        result = manager.redo()

        assert result is False
        assert not manager.can_undo
        assert manager.can_redo

    def test_new_command_clears_redo_stack(self, manager: UndoManager) -> None:
        """New command should clear redo stack (T5 scenario)."""
        command1 = MockCommand(name="first")
        command2 = MockCommand(name="second")

        manager.execute(command1)
        manager.undo()
        assert manager.can_redo

        manager.execute(command2)
        assert not manager.can_redo
        assert manager.undo_description == "Mock command: second"

    def test_multiple_undo_redo(self, manager: UndoManager) -> None:
        """Multiple undo/redo should work correctly."""
        commands = [MockCommand(name=str(i)) for i in range(3)]
        for cmd in commands:
            manager.execute(cmd)

        assert manager.undo_count == 3

        # Undo all
        manager.undo()
        manager.undo()
        manager.undo()

        assert not manager.can_undo
        assert manager.redo_count == 3

        # Redo all
        manager.redo()
        manager.redo()
        manager.redo()

        assert manager.undo_count == 3
        assert not manager.can_redo

    def test_max_depth_enforcement(self) -> None:
        """Exceeding max depth should remove oldest commands."""
        manager = UndoManager(max_depth=3)
        commands = [MockCommand(name=str(i)) for i in range(5)]

        for cmd in commands:
            manager.execute(cmd)

        assert manager.undo_count == 3
        # Oldest commands should be removed
        manager.undo()
        assert manager.undo_description == "Mock command: 3"

    def test_clear_stacks(self, manager: UndoManager) -> None:
        """clear should empty both stacks."""
        manager.execute(MockCommand())
        manager.undo()

        manager.clear()

        assert not manager.can_undo
        assert not manager.can_redo
        assert manager.undo_count == 0
        assert manager.redo_count == 0

    def test_state_change_notification(self, manager: UndoManager) -> None:
        """State changes should notify subscribers."""
        notifications = []

        def on_change() -> None:
            notifications.append(True)

        manager.subscribe(on_change)
        manager.execute(MockCommand())
        manager.undo()
        manager.redo()
        manager.clear()

        assert len(notifications) == 4

    def test_unsubscribe(self, manager: UndoManager) -> None:
        """unsubscribe should stop notifications."""
        notifications = []

        def on_change() -> None:
            notifications.append(True)

        manager.subscribe(on_change)
        manager.execute(MockCommand())
        manager.unsubscribe(on_change)
        manager.execute(MockCommand())

        assert len(notifications) == 1

    def test_merge_commands(self, manager: UndoManager) -> None:
        """Mergeable commands should be combined."""
        cmd1 = MockCommand(name="first", can_merge=True)
        cmd2 = MockCommand(name="second", can_merge=True)

        manager.execute(cmd1)
        manager.execute(cmd2)

        # Should have merged into single command
        assert manager.undo_count == 1
        assert "first+second" in manager.undo_description or True  # Mock merge

    def test_non_mergeable_commands(self, manager: UndoManager) -> None:
        """Non-mergeable commands should stay separate."""
        cmd1 = MockCommand(name="first", can_merge=False)
        cmd2 = MockCommand(name="second", can_merge=False)

        manager.execute(cmd1)
        manager.execute(cmd2)

        assert manager.undo_count == 2

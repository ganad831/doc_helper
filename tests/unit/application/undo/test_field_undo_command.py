"""Unit tests for SetFieldValueCommand."""

from typing import Any

import pytest

from doc_helper.application.undo.field_undo_command import (
    SetFieldValueCommand,
    IFieldService,
)
from doc_helper.application.undo.undo_state_dto import UndoFieldState


class MockFieldService:
    """Mock field service for testing."""

    def __init__(self, success: bool = True) -> None:
        self._success = success
        self.calls: list[tuple[str, str, Any]] = []

    def set_field_value(
        self,
        project_id: str,
        field_id: str,
        value: Any,
    ) -> bool:
        self.calls.append((project_id, field_id, value))
        return self._success


class TestSetFieldValueCommand:
    """Tests for SetFieldValueCommand."""

    @pytest.fixture
    def field_service(self) -> MockFieldService:
        """Create mock field service."""
        return MockFieldService()

    @pytest.fixture
    def state(self) -> UndoFieldState:
        """Create sample undo state."""
        return UndoFieldState.create(
            field_id="F1",
            previous_value="100",
            new_value="150",
            was_formula_computed=False,
        )

    @pytest.fixture
    def command(
        self, state: UndoFieldState, field_service: MockFieldService
    ) -> SetFieldValueCommand:
        """Create sample command."""
        return SetFieldValueCommand(
            project_id="project-123",
            state=state,
            field_service=field_service,
        )

    def test_create_command(self, command: SetFieldValueCommand) -> None:
        """SetFieldValueCommand should store provided values."""
        assert command.project_id == "project-123"
        assert command.field_id == "F1"
        assert command.previous_value == "100"
        assert command.new_value == "150"

    def test_create_requires_project_id(
        self, state: UndoFieldState, field_service: MockFieldService
    ) -> None:
        """SetFieldValueCommand should require valid project_id."""
        with pytest.raises(ValueError):
            SetFieldValueCommand(
                project_id="",
                state=state,
                field_service=field_service,
            )

    def test_create_requires_state(
        self, field_service: MockFieldService
    ) -> None:
        """SetFieldValueCommand should require UndoFieldState."""
        with pytest.raises(TypeError):
            SetFieldValueCommand(
                project_id="project-123",
                state="not a state",  # type: ignore
                field_service=field_service,
            )

    def test_command_type(self, command: SetFieldValueCommand) -> None:
        """command_type should return field_edit."""
        assert command.command_type == "field_edit"

    def test_description(self, command: SetFieldValueCommand) -> None:
        """description should include field ID."""
        assert "F1" in command.description

    def test_execute(
        self, command: SetFieldValueCommand, field_service: MockFieldService
    ) -> None:
        """execute should set field to new value."""
        result = command.execute()

        assert result is True
        assert len(field_service.calls) == 1
        call = field_service.calls[0]
        assert call == ("project-123", "F1", "150")

    def test_execute_failure(
        self, state: UndoFieldState
    ) -> None:
        """execute should return False on service failure."""
        failing_service = MockFieldService(success=False)
        command = SetFieldValueCommand(
            project_id="project-123",
            state=state,
            field_service=failing_service,
        )

        result = command.execute()

        assert result is False

    def test_undo(
        self, command: SetFieldValueCommand, field_service: MockFieldService
    ) -> None:
        """undo should restore field to previous value."""
        result = command.undo()

        assert result is True
        assert len(field_service.calls) == 1
        call = field_service.calls[0]
        assert call == ("project-123", "F1", "100")

    def test_redo(
        self, command: SetFieldValueCommand, field_service: MockFieldService
    ) -> None:
        """redo should set field to new value."""
        result = command.redo()

        assert result is True
        assert len(field_service.calls) == 1
        call = field_service.calls[0]
        assert call == ("project-123", "F1", "150")

    def test_can_merge_same_field(
        self, state: UndoFieldState, field_service: MockFieldService
    ) -> None:
        """can_merge_with should return True for same field within window."""
        cmd1 = SetFieldValueCommand(
            project_id="project-123",
            state=state,
            field_service=field_service,
        )
        # Create second state with same timestamp (within window)
        state2 = UndoFieldState(
            field_id="F1",
            previous_value="150",
            new_value="200",
            was_formula_computed=False,
            timestamp=state.timestamp,  # Same timestamp
        )
        cmd2 = SetFieldValueCommand(
            project_id="project-123",
            state=state2,
            field_service=field_service,
        )

        assert cmd1.can_merge_with(cmd2) is True

    def test_cannot_merge_different_field(
        self, state: UndoFieldState, field_service: MockFieldService
    ) -> None:
        """can_merge_with should return False for different fields."""
        cmd1 = SetFieldValueCommand(
            project_id="project-123",
            state=state,
            field_service=field_service,
        )
        state2 = UndoFieldState.create(
            field_id="F2",  # Different field
            previous_value="50",
            new_value="75",
        )
        cmd2 = SetFieldValueCommand(
            project_id="project-123",
            state=state2,
            field_service=field_service,
        )

        assert cmd1.can_merge_with(cmd2) is False

    def test_cannot_merge_different_project(
        self, state: UndoFieldState, field_service: MockFieldService
    ) -> None:
        """can_merge_with should return False for different projects."""
        cmd1 = SetFieldValueCommand(
            project_id="project-123",
            state=state,
            field_service=field_service,
        )
        cmd2 = SetFieldValueCommand(
            project_id="project-456",  # Different project
            state=state,
            field_service=field_service,
        )

        assert cmd1.can_merge_with(cmd2) is False

    def test_merge_with(
        self, state: UndoFieldState, field_service: MockFieldService
    ) -> None:
        """merge_with should combine commands."""
        cmd1 = SetFieldValueCommand(
            project_id="project-123",
            state=state,
            field_service=field_service,
        )
        state2 = UndoFieldState(
            field_id="F1",
            previous_value="150",
            new_value="200",
            was_formula_computed=False,
            timestamp=state.timestamp,
        )
        cmd2 = SetFieldValueCommand(
            project_id="project-123",
            state=state2,
            field_service=field_service,
        )

        merged = cmd1.merge_with(cmd2)

        # Merged command should keep original previous and latest new
        assert merged.previous_value == "100"
        assert merged.new_value == "200"

    def test_merge_with_non_mergeable(
        self, command: SetFieldValueCommand, state: UndoFieldState, field_service: MockFieldService
    ) -> None:
        """merge_with should raise for non-mergeable commands."""
        state2 = UndoFieldState.create(
            field_id="F2",  # Different field
            previous_value="50",
            new_value="75",
        )
        cmd2 = SetFieldValueCommand(
            project_id="project-123",
            state=state2,
            field_service=field_service,
        )

        with pytest.raises(ValueError):
            command.merge_with(cmd2)


class TestUndoFieldState:
    """Tests for UndoFieldState."""

    def test_create_state(self) -> None:
        """UndoFieldState.create should create valid state."""
        state = UndoFieldState.create(
            field_id="F1",
            previous_value="old",
            new_value="new",
            was_formula_computed=True,
        )

        assert state.field_id == "F1"
        assert state.previous_value == "old"
        assert state.new_value == "new"
        assert state.was_formula_computed is True
        assert state.timestamp  # Should have timestamp

    def test_state_is_immutable(self) -> None:
        """UndoFieldState should be immutable."""
        state = UndoFieldState.create(
            field_id="F1",
            previous_value="old",
            new_value="new",
        )

        with pytest.raises(Exception):  # frozen dataclass raises
            state.field_id = "F2"  # type: ignore

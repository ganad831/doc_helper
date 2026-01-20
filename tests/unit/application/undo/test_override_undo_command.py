"""Unit tests for override undo commands."""

from typing import Any

import pytest

from doc_helper.application.undo.override_undo_command import (
    AcceptOverrideCommand,
    RejectOverrideCommand,
    IOverrideService,
    IFieldService,
)
from doc_helper.application.undo.undo_state_dto import UndoOverrideState


class MockOverrideService:
    """Mock override service for testing."""

    def __init__(self, success: bool = True) -> None:
        self._success = success
        self.accept_calls: list[tuple[str, str]] = []
        self.reject_calls: list[tuple[str, str]] = []
        self.restore_calls: list[tuple[str, str]] = []

    def accept_override(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        self.accept_calls.append((project_id, override_id))
        return self._success

    def reject_override(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        self.reject_calls.append((project_id, override_id))
        return self._success

    def restore_override_to_pending(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        self.restore_calls.append((project_id, override_id))
        return self._success


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


class TestAcceptOverrideCommand:
    """Tests for AcceptOverrideCommand."""

    @pytest.fixture
    def override_service(self) -> MockOverrideService:
        """Create mock override service."""
        return MockOverrideService()

    @pytest.fixture
    def field_service(self) -> MockFieldService:
        """Create mock field service."""
        return MockFieldService()

    @pytest.fixture
    def state(self) -> UndoOverrideState:
        """Create sample undo state."""
        return UndoOverrideState.create(
            override_id="override-1",
            field_id="F1",
            previous_override_state="PENDING",
            previous_field_value="100",
            accepted_value="150",
            affected_formula_fields=("F2", "F3"),
        )

    @pytest.fixture
    def command(
        self,
        state: UndoOverrideState,
        override_service: MockOverrideService,
        field_service: MockFieldService,
    ) -> AcceptOverrideCommand:
        """Create sample command."""
        return AcceptOverrideCommand(
            project_id="project-123",
            state=state,
            override_service=override_service,
            field_service=field_service,
        )

    def test_create_command(self, command: AcceptOverrideCommand) -> None:
        """AcceptOverrideCommand should store provided values."""
        assert command.project_id == "project-123"
        assert command.override_id == "override-1"
        assert command.field_id == "F1"

    def test_create_requires_project_id(
        self,
        state: UndoOverrideState,
        override_service: MockOverrideService,
        field_service: MockFieldService,
    ) -> None:
        """AcceptOverrideCommand should require valid project_id."""
        with pytest.raises(ValueError):
            AcceptOverrideCommand(
                project_id="",
                state=state,
                override_service=override_service,
                field_service=field_service,
            )

    def test_create_requires_state(
        self,
        override_service: MockOverrideService,
        field_service: MockFieldService,
    ) -> None:
        """AcceptOverrideCommand should require UndoOverrideState."""
        with pytest.raises(TypeError):
            AcceptOverrideCommand(
                project_id="project-123",
                state="not a state",  # type: ignore
                override_service=override_service,
                field_service=field_service,
            )

    def test_command_type(self, command: AcceptOverrideCommand) -> None:
        """command_type should return override_accept."""
        assert command.command_type == "override_accept"

    def test_description(self, command: AcceptOverrideCommand) -> None:
        """description should include field ID."""
        assert "F1" in command.description

    def test_execute(
        self,
        command: AcceptOverrideCommand,
        override_service: MockOverrideService,
    ) -> None:
        """execute should accept the override."""
        result = command.execute()

        assert result is True
        assert len(override_service.accept_calls) == 1
        call = override_service.accept_calls[0]
        assert call == ("project-123", "override-1")

    def test_undo(
        self,
        command: AcceptOverrideCommand,
        override_service: MockOverrideService,
        field_service: MockFieldService,
    ) -> None:
        """undo should restore override to pending and restore field value."""
        result = command.undo()

        assert result is True
        # Should restore override to pending
        assert len(override_service.restore_calls) == 1
        assert override_service.restore_calls[0] == ("project-123", "override-1")
        # Should restore field value
        assert len(field_service.calls) == 1
        assert field_service.calls[0] == ("project-123", "F1", "100")

    def test_undo_failure_on_override_restore(
        self,
        state: UndoOverrideState,
        field_service: MockFieldService,
    ) -> None:
        """undo should return False if override restore fails."""
        failing_service = MockOverrideService(success=False)
        command = AcceptOverrideCommand(
            project_id="project-123",
            state=state,
            override_service=failing_service,
            field_service=field_service,
        )

        result = command.undo()

        assert result is False
        # Field value should not be set
        assert len(field_service.calls) == 0

    def test_redo(
        self,
        command: AcceptOverrideCommand,
        override_service: MockOverrideService,
    ) -> None:
        """redo should re-accept the override."""
        result = command.redo()

        assert result is True
        assert len(override_service.accept_calls) == 1
        assert override_service.accept_calls[0] == ("project-123", "override-1")

    def test_cannot_merge(self, command: AcceptOverrideCommand) -> None:
        """Override commands cannot be merged."""
        assert command.can_merge_with(command) is False

    def test_merge_raises(self, command: AcceptOverrideCommand) -> None:
        """merge_with should raise for override commands."""
        with pytest.raises(ValueError):
            command.merge_with(command)


class TestRejectOverrideCommand:
    """Tests for RejectOverrideCommand."""

    @pytest.fixture
    def override_service(self) -> MockOverrideService:
        """Create mock override service."""
        return MockOverrideService()

    @pytest.fixture
    def state(self) -> UndoOverrideState:
        """Create sample undo state."""
        return UndoOverrideState.create(
            override_id="override-1",
            field_id="F1",
            previous_override_state="PENDING",
            previous_field_value="100",
            accepted_value="150",
        )

    @pytest.fixture
    def command(
        self,
        state: UndoOverrideState,
        override_service: MockOverrideService,
    ) -> RejectOverrideCommand:
        """Create sample command."""
        return RejectOverrideCommand(
            project_id="project-123",
            state=state,
            override_service=override_service,
        )

    def test_create_command(self, command: RejectOverrideCommand) -> None:
        """RejectOverrideCommand should store provided values."""
        assert command.project_id == "project-123"
        assert command.override_id == "override-1"
        assert command.field_id == "F1"

    def test_command_type(self, command: RejectOverrideCommand) -> None:
        """command_type should return override_reject."""
        assert command.command_type == "override_reject"

    def test_execute(
        self,
        command: RejectOverrideCommand,
        override_service: MockOverrideService,
    ) -> None:
        """execute should reject the override."""
        result = command.execute()

        assert result is True
        assert len(override_service.reject_calls) == 1
        assert override_service.reject_calls[0] == ("project-123", "override-1")

    def test_undo(
        self,
        command: RejectOverrideCommand,
        override_service: MockOverrideService,
    ) -> None:
        """undo should restore override to pending."""
        result = command.undo()

        assert result is True
        assert len(override_service.restore_calls) == 1
        assert override_service.restore_calls[0] == ("project-123", "override-1")

    def test_redo(
        self,
        command: RejectOverrideCommand,
        override_service: MockOverrideService,
    ) -> None:
        """redo should re-reject the override."""
        result = command.redo()

        assert result is True
        assert len(override_service.reject_calls) == 1
        assert override_service.reject_calls[0] == ("project-123", "override-1")

    def test_cannot_merge(self, command: RejectOverrideCommand) -> None:
        """Override commands cannot be merged."""
        assert command.can_merge_with(command) is False


class TestUndoOverrideState:
    """Tests for UndoOverrideState."""

    def test_create_state(self) -> None:
        """UndoOverrideState.create should create valid state."""
        state = UndoOverrideState.create(
            override_id="override-1",
            field_id="F1",
            previous_override_state="PENDING",
            previous_field_value="100",
            accepted_value="150",
            affected_formula_fields=("F2",),
        )

        assert state.override_id == "override-1"
        assert state.field_id == "F1"
        assert state.previous_override_state == "PENDING"
        assert state.previous_field_value == "100"
        assert state.accepted_value == "150"
        assert state.affected_formula_fields == ("F2",)
        assert state.timestamp  # Should have timestamp

    def test_state_is_immutable(self) -> None:
        """UndoOverrideState should be immutable."""
        state = UndoOverrideState.create(
            override_id="override-1",
            field_id="F1",
            previous_override_state="PENDING",
            previous_field_value="100",
            accepted_value="150",
        )

        with pytest.raises(Exception):  # frozen dataclass raises
            state.override_id = "override-2"  # type: ignore

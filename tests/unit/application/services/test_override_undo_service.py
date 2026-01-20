"""Unit tests for OverrideUndoService wrapper.

RULES (unified_upgrade_plan_FINAL.md U6 Phase 1):
- Test state capture BEFORE operation (override state, field value)
- Test command creation with captured state
- Test UndoManager.execute() invocation
- Test accept and reject operations
"""

import pytest
from typing import Any
from unittest.mock import Mock

from doc_helper.application.services.override_undo_service import OverrideUndoService
from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.domain.common.result import Failure, Success


class MockOverrideService:
    """Mock override service for testing."""

    def __init__(self):
        self.get_override_state_return = Success("PENDING")
        self.get_override_field_id_return = Success("field-1")
        self.get_override_value_return = Success("override_value")
        self.accept_override_return = True
        self.reject_override_return = True
        self.restore_override_to_pending_return = True

        self.accept_override_called = []
        self.reject_override_called = []
        self.restore_override_to_pending_called = []

    def get_override_state(self, project_id: str, override_id: str):
        return self.get_override_state_return

    def get_override_field_id(self, project_id: str, override_id: str):
        return self.get_override_field_id_return

    def get_override_value(self, project_id: str, override_id: str):
        return self.get_override_value_return

    def accept_override(self, project_id: str, override_id: str) -> bool:
        self.accept_override_called.append((project_id, override_id))
        return self.accept_override_return

    def reject_override(self, project_id: str, override_id: str) -> bool:
        self.reject_override_called.append((project_id, override_id))
        return self.reject_override_return

    def restore_override_to_pending(self, project_id: str, override_id: str) -> bool:
        self.restore_override_to_pending_called.append((project_id, override_id))
        return self.restore_override_to_pending_return


class MockFieldService:
    """Mock field service for testing."""

    def __init__(self):
        self.get_field_value_return = Success("field_value")
        self.set_field_value_return = True
        self.set_field_value_called = []

    def get_field_value(self, project_id: str, field_id: str):
        return self.get_field_value_return

    def set_field_value(self, project_id: str, field_id: str, value: Any) -> bool:
        self.set_field_value_called.append((project_id, field_id, value))
        return self.set_field_value_return


@pytest.fixture
def mock_override_service():
    """Create mock override service."""
    return MockOverrideService()


@pytest.fixture
def mock_field_service():
    """Create mock field service."""
    return MockFieldService()


@pytest.fixture
def undo_manager():
    """Create real undo manager."""
    return UndoManager()


@pytest.fixture
def override_undo_service(mock_override_service, mock_field_service, undo_manager):
    """Create override undo service with mocks."""
    return OverrideUndoService(mock_override_service, mock_field_service, undo_manager)


def test_create_service(override_undo_service):
    """Test: Service instance created successfully."""
    assert isinstance(override_undo_service, OverrideUndoService)


def test_accept_override_captures_state_before_accepting(
    override_undo_service, mock_override_service, mock_field_service, undo_manager
):
    """Test: accept_override() captures state BEFORE accepting.

    RULES (H1 State Capture Specification):
    - Captures previous_override_state (e.g., "PENDING")
    - Captures previous_field_value
    - Captures override's accepted_value
    """
    # Arrange
    project_id = "project-123"
    override_id = "override-1"
    mock_override_service.get_override_state_return = Success("PENDING")
    mock_override_service.get_override_field_id_return = Success("borehole_depth")
    mock_override_service.get_override_value_return = Success(150)
    mock_field_service.get_field_value_return = Success(100)

    # Act
    result = override_undo_service.accept_override(project_id, override_id)

    # Assert: Success returned
    assert isinstance(result, Success)

    # Assert: Override accepted
    assert len(mock_override_service.accept_override_called) == 1
    assert mock_override_service.accept_override_called[0] == (project_id, override_id)

    # Assert: Command added to undo stack
    assert undo_manager.can_undo
    assert undo_manager.undo_count == 1


def test_accept_override_undo_restores_pending_and_field_value(
    override_undo_service, mock_override_service, mock_field_service, undo_manager
):
    """Test: Undoing accept_override restores PENDING state and field value.

    RULES (H1 Command-Based Undo Model):
    - undo() restores override to PENDING
    - undo() restores field to previous_value
    """
    # Arrange
    project_id = "project-123"
    override_id = "override-1"
    field_id = "borehole_depth"
    previous_field_value = 100
    accepted_value = 150

    mock_override_service.get_override_state_return = Success("PENDING")
    mock_override_service.get_override_field_id_return = Success(field_id)
    mock_override_service.get_override_value_return = Success(accepted_value)
    mock_field_service.get_field_value_return = Success(previous_field_value)

    # Act: Accept override
    result = override_undo_service.accept_override(project_id, override_id)
    assert isinstance(result, Success)

    # Act: Undo
    undo_success = undo_manager.undo()

    # Assert: Undo succeeded
    assert undo_success is True

    # Assert: Override restored to PENDING
    assert len(mock_override_service.restore_override_to_pending_called) == 1
    assert mock_override_service.restore_override_to_pending_called[0] == (
        project_id,
        override_id,
    )

    # Assert: Field value restored
    assert len(mock_field_service.set_field_value_called) == 1
    assert mock_field_service.set_field_value_called[0] == (
        project_id,
        field_id,
        previous_field_value,
    )

    # Assert: Can now redo
    assert undo_manager.can_redo


def test_accept_override_redo_reaccepts_override(
    override_undo_service, mock_override_service, mock_field_service, undo_manager
):
    """Test: Redoing accept_override re-accepts the override.

    RULES (H1 Command-Based Undo Model):
    - redo() re-accepts override
    - redo() reapplies accepted_value to field
    """
    # Arrange
    project_id = "project-123"
    override_id = "override-1"
    mock_override_service.get_override_state_return = Success("PENDING")
    mock_override_service.get_override_field_id_return = Success("field-1")
    mock_override_service.get_override_value_return = Success(150)
    mock_field_service.get_field_value_return = Success(100)

    # Act: Accept override, then undo
    override_undo_service.accept_override(project_id, override_id)
    undo_manager.undo()

    # Clear call history
    mock_override_service.accept_override_called.clear()

    # Act: Redo
    redo_success = undo_manager.redo()

    # Assert: Redo succeeded
    assert redo_success is True

    # Assert: Override re-accepted
    assert len(mock_override_service.accept_override_called) == 1
    assert mock_override_service.accept_override_called[0] == (project_id, override_id)


def test_reject_override_captures_state_before_rejecting(
    override_undo_service, mock_override_service, mock_field_service, undo_manager
):
    """Test: reject_override() captures state BEFORE rejecting.

    RULES (H1 State Capture Specification):
    - Captures previous_override_state (e.g., "PENDING")
    - Captures current_field_value (unchanged by reject)
    """
    # Arrange
    project_id = "project-123"
    override_id = "override-1"
    mock_override_service.get_override_state_return = Success("PENDING")
    mock_override_service.get_override_field_id_return = Success("borehole_depth")
    mock_override_service.get_override_value_return = Success(150)
    mock_field_service.get_field_value_return = Success(100)

    # Act
    result = override_undo_service.reject_override(project_id, override_id)

    # Assert: Success returned
    assert isinstance(result, Success)

    # Assert: Override rejected
    assert len(mock_override_service.reject_override_called) == 1
    assert mock_override_service.reject_override_called[0] == (project_id, override_id)

    # Assert: Command added to undo stack
    assert undo_manager.can_undo
    assert undo_manager.undo_count == 1


def test_reject_override_undo_restores_pending(
    override_undo_service, mock_override_service, mock_field_service, undo_manager
):
    """Test: Undoing reject_override restores PENDING state.

    RULES (H1 Command-Based Undo Model):
    - undo() restores override to PENDING
    - Field value unchanged (reject doesn't change field)
    """
    # Arrange
    project_id = "project-123"
    override_id = "override-1"
    mock_override_service.get_override_state_return = Success("PENDING")
    mock_override_service.get_override_field_id_return = Success("field-1")
    mock_override_service.get_override_value_return = Success(150)
    mock_field_service.get_field_value_return = Success(100)

    # Act: Reject override
    result = override_undo_service.reject_override(project_id, override_id)
    assert isinstance(result, Success)

    # Act: Undo
    undo_success = undo_manager.undo()

    # Assert: Undo succeeded
    assert undo_success is True

    # Assert: Override restored to PENDING
    assert len(mock_override_service.restore_override_to_pending_called) == 1
    assert mock_override_service.restore_override_to_pending_called[0] == (
        project_id,
        override_id,
    )

    # Assert: Can now redo
    assert undo_manager.can_redo


def test_accept_override_fails_if_get_state_fails(
    override_undo_service, mock_override_service, mock_field_service, undo_manager
):
    """Test: accept_override() fails if cannot get override state.

    RULES (H1 State Capture Specification):
    - Previous state MUST be captured
    - If capture fails, operation aborts
    """
    # Arrange
    project_id = "project-123"
    override_id = "override-1"
    mock_override_service.get_override_state_return = Failure("Override not found")

    # Act
    result = override_undo_service.accept_override(project_id, override_id)

    # Assert: Failure returned
    assert isinstance(result, Failure)
    assert "Failed to get override state" in result.error

    # Assert: No command added to undo stack
    assert not undo_manager.can_undo

    # Assert: accept_override NOT called
    assert len(mock_override_service.accept_override_called) == 0


def test_accept_override_fails_if_command_execution_fails(
    override_undo_service, mock_override_service, mock_field_service, undo_manager
):
    """Test: accept_override() fails if command execution fails.

    RULES:
    - If command.execute() returns False, wrapper returns Failure
    """
    # Arrange
    project_id = "project-123"
    override_id = "override-1"
    mock_override_service.get_override_state_return = Success("PENDING")
    mock_override_service.get_override_field_id_return = Success("field-1")
    mock_override_service.get_override_value_return = Success(150)
    mock_field_service.get_field_value_return = Success(100)
    mock_override_service.accept_override_return = False  # Command execution will fail

    # Act
    result = override_undo_service.accept_override(project_id, override_id)

    # Assert: Failure returned
    assert isinstance(result, Failure)
    assert "Command execution failed" in result.error

    # Assert: Command NOT added to undo stack (failed commands don't add)
    assert not undo_manager.can_undo


def test_override_commands_not_mergeable(
    override_undo_service, mock_override_service, mock_field_service, undo_manager
):
    """Test: Override commands are NOT mergeable (unlike field edits).

    RULES (H1 Command-Based Undo Model):
    - Override commands cannot merge
    - Each accept/reject creates a separate undo command
    """
    # Arrange
    project_id = "project-123"
    override_id_1 = "override-1"
    override_id_2 = "override-2"

    mock_override_service.get_override_state_return = Success("PENDING")
    mock_override_service.get_override_field_id_return = Success("field-1")
    mock_override_service.get_override_value_return = Success(150)
    mock_field_service.get_field_value_return = Success(100)

    # Act: Accept two overrides in rapid succession
    override_undo_service.accept_override(project_id, override_id_1)
    override_undo_service.accept_override(project_id, override_id_2)

    # Assert: Two commands in undo stack (no merging)
    assert undo_manager.undo_count == 2


def test_clear_undo_stack(
    override_undo_service, mock_override_service, mock_field_service, undo_manager
):
    """Test: Clearing undo stack removes all commands.

    RULES (v1.3.1):
    - undo_manager.clear() removes all undo/redo commands
    - Called on project close/open
    """
    # Arrange
    project_id = "project-123"
    override_id = "override-1"
    mock_override_service.get_override_state_return = Success("PENDING")
    mock_override_service.get_override_field_id_return = Success("field-1")
    mock_override_service.get_override_value_return = Success(150)
    mock_field_service.get_field_value_return = Success(100)

    # Act: Accept override
    override_undo_service.accept_override(project_id, override_id)
    assert undo_manager.can_undo

    # Act: Clear stack (simulates project close)
    undo_manager.clear()

    # Assert: No undo/redo available
    assert not undo_manager.can_undo
    assert not undo_manager.can_redo

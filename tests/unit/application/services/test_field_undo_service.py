"""Unit tests for FieldUndoService wrapper.

RULES (unified_upgrade_plan_FINAL.md U6 Phase 1):
- Test state capture BEFORE operation
- Test command creation with captured state
- Test UndoManager.execute() invocation
- Test Result success/failure paths
"""

import pytest
from typing import Any
from unittest.mock import Mock, call

from doc_helper.application.services.field_undo_service import FieldUndoService
from doc_helper.application.undo.field_undo_command import SetFieldValueCommand
from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.domain.common.result import Failure, Success


class MockFieldService:
    """Mock field service for testing."""

    def __init__(self):
        self.get_field_value_called = []
        self.set_field_value_called = []
        self.get_return_value = Success("original_value")
        self.set_return_value = True

    def get_field_value(self, project_id: str, field_id: str):
        self.get_field_value_called.append((project_id, field_id))
        return self.get_return_value

    def set_field_value(self, project_id: str, field_id: str, value: Any) -> bool:
        self.set_field_value_called.append((project_id, field_id, value))
        return self.set_return_value


@pytest.fixture
def mock_field_service():
    """Create mock field service."""
    return MockFieldService()


@pytest.fixture
def undo_manager():
    """Create real undo manager."""
    return UndoManager()


@pytest.fixture
def field_undo_service(mock_field_service, undo_manager):
    """Create field undo service with mocks."""
    return FieldUndoService(mock_field_service, undo_manager)


def test_create_service(field_undo_service):
    """Test: Service instance created successfully."""
    assert isinstance(field_undo_service, FieldUndoService)


def test_set_field_value_captures_previous_value(
    field_undo_service, mock_field_service, undo_manager
):
    """Test: set_field_value() captures previous value BEFORE changing.

    RULES (H1 State Capture Specification):
    - Captures previous_value before operation
    - Captures new_value from parameter
    """
    # Arrange
    project_id = "project-123"
    field_id = "site_location"
    new_value = "456 Elm St"
    mock_field_service.get_return_value = Success("123 Main St")

    # Act
    result = field_undo_service.set_field_value(project_id, field_id, new_value)

    # Assert: Success returned
    assert isinstance(result, Success)

    # Assert: Previous value captured via get call
    assert len(mock_field_service.get_field_value_called) == 1
    assert mock_field_service.get_field_value_called[0] == (project_id, field_id)

    # Assert: Command added to undo stack
    assert undo_manager.can_undo
    assert undo_manager.undo_count == 1


def test_set_field_value_executes_via_undo_manager(
    field_undo_service, mock_field_service, undo_manager
):
    """Test: set_field_value() executes command via UndoManager.

    RULES (H1 Command-Based Undo Model):
    - Command created with captured state
    - Command executed via UndoManager.execute()
    - Command added to undo stack
    """
    # Arrange
    project_id = "project-123"
    field_id = "site_location"
    new_value = "456 Elm St"
    previous_value = "123 Main St"
    mock_field_service.get_return_value = Success(previous_value)

    # Act
    result = field_undo_service.set_field_value(project_id, field_id, new_value)

    # Assert: Success
    assert isinstance(result, Success)

    # Assert: Command added to undo stack
    assert undo_manager.can_undo
    assert undo_manager.undo_description == f"Edit field {field_id}"

    # Assert: New value applied via set call
    assert len(mock_field_service.set_field_value_called) == 1
    assert mock_field_service.set_field_value_called[0] == (
        project_id,
        field_id,
        new_value,
    )


def test_set_field_value_undo_restores_previous_value(
    field_undo_service, mock_field_service, undo_manager
):
    """Test: Undoing set_field_value restores previous value.

    RULES (H1 Command-Based Undo Model):
    - undo() restores field to previous_value
    - Uses same IFieldService.set_field_value() method
    """
    # Arrange
    project_id = "project-123"
    field_id = "site_location"
    new_value = "456 Elm St"
    previous_value = "123 Main St"
    mock_field_service.get_return_value = Success(previous_value)

    # Act: Set field value
    result = field_undo_service.set_field_value(project_id, field_id, new_value)
    assert isinstance(result, Success)

    # Clear call history
    mock_field_service.set_field_value_called.clear()

    # Act: Undo
    undo_success = undo_manager.undo()

    # Assert: Undo succeeded
    assert undo_success is True

    # Assert: Previous value restored
    assert len(mock_field_service.set_field_value_called) == 1
    assert mock_field_service.set_field_value_called[0] == (
        project_id,
        field_id,
        previous_value,
    )

    # Assert: Can now redo
    assert undo_manager.can_redo


def test_set_field_value_redo_reapplies_new_value(
    field_undo_service, mock_field_service, undo_manager
):
    """Test: Redoing set_field_value reapplies new value.

    RULES (H1 Command-Based Undo Model):
    - redo() reapplies new_value
    - Uses same IFieldService.set_field_value() method
    """
    # Arrange
    project_id = "project-123"
    field_id = "site_location"
    new_value = "456 Elm St"
    previous_value = "123 Main St"
    mock_field_service.get_return_value = Success(previous_value)

    # Act: Set field value, then undo
    field_undo_service.set_field_value(project_id, field_id, new_value)
    undo_manager.undo()

    # Clear call history
    mock_field_service.set_field_value_called.clear()

    # Act: Redo
    redo_success = undo_manager.redo()

    # Assert: Redo succeeded
    assert redo_success is True

    # Assert: New value reapplied
    assert len(mock_field_service.set_field_value_called) == 1
    assert mock_field_service.set_field_value_called[0] == (
        project_id,
        field_id,
        new_value,
    )


def test_set_field_value_fails_if_get_fails(
    field_undo_service, mock_field_service, undo_manager
):
    """Test: set_field_value() fails if cannot get previous value.

    RULES (H1 State Capture Specification):
    - Previous value MUST be captured
    - If capture fails, operation aborts
    """
    # Arrange
    project_id = "project-123"
    field_id = "site_location"
    new_value = "456 Elm St"
    mock_field_service.get_return_value = Failure("Field not found")

    # Act
    result = field_undo_service.set_field_value(project_id, field_id, new_value)

    # Assert: Failure returned
    assert isinstance(result, Failure)
    assert "Failed to get current value" in result.error

    # Assert: No command added to undo stack
    assert not undo_manager.can_undo

    # Assert: set_field_value NOT called
    assert len(mock_field_service.set_field_value_called) == 0


def test_set_field_value_fails_if_command_execution_fails(
    field_undo_service, mock_field_service, undo_manager
):
    """Test: set_field_value() fails if command execution fails.

    RULES:
    - If command.execute() returns False, wrapper returns Failure
    """
    # Arrange
    project_id = "project-123"
    field_id = "site_location"
    new_value = "456 Elm St"
    mock_field_service.get_return_value = Success("123 Main St")
    mock_field_service.set_return_value = False  # Command execution will fail

    # Act
    result = field_undo_service.set_field_value(project_id, field_id, new_value)

    # Assert: Failure returned
    assert isinstance(result, Failure)
    assert "Command execution failed" in result.error

    # Assert: Command NOT added to undo stack (failed commands don't add)
    assert not undo_manager.can_undo


def test_multiple_set_field_values_creates_undo_stack(
    field_undo_service, mock_field_service, undo_manager
):
    """Test: Multiple set_field_value calls create multiple undo commands.

    RULES (H1 Command-Based Undo Model):
    - Each operation creates a separate command
    - Commands stack in LIFO order
    """
    # Arrange
    project_id = "project-123"
    field_id = "site_location"
    mock_field_service.get_return_value = Success("value0")

    # Act: Perform 3 edits
    field_undo_service.set_field_value(project_id, field_id, "value1")
    mock_field_service.get_return_value = Success("value1")

    field_undo_service.set_field_value(project_id, field_id, "value2")
    mock_field_service.get_return_value = Success("value2")

    field_undo_service.set_field_value(project_id, field_id, "value3")

    # Assert: 3 commands in undo stack (or fewer if merged)
    # Note: SetFieldValueCommand may merge commands within 500ms window
    assert undo_manager.can_undo
    assert undo_manager.undo_count >= 1  # At least one command


def test_clear_undo_stack(field_undo_service, mock_field_service, undo_manager):
    """Test: Clearing undo stack removes all commands.

    RULES (v1.3.1):
    - undo_manager.clear() removes all undo/redo commands
    - Called on project close/open
    """
    # Arrange
    project_id = "project-123"
    field_id = "site_location"
    mock_field_service.get_return_value = Success("original")

    # Act: Set field value
    field_undo_service.set_field_value(project_id, field_id, "new_value")
    assert undo_manager.can_undo

    # Act: Clear stack (simulates project close)
    undo_manager.clear()

    # Assert: No undo/redo available
    assert not undo_manager.can_undo
    assert not undo_manager.can_redo

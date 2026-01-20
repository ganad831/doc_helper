"""Wraps field operations in undoable commands.

RULES (unified_upgrade_plan_FINAL.md U6, H1-H5):
- Wrapper service pattern: captures state, creates command, executes via UndoManager
- State captured BEFORE operation (previous_value)
- Commands delegate to IFieldService for actual operation
- Side effects (formula recalc, validation) triggered via event bus
"""

from typing import Any, Protocol

from doc_helper.application.undo.field_undo_command import SetFieldValueCommand
from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.application.undo.undo_state_dto import UndoFieldState
from doc_helper.domain.common.result import Failure, Result, Success


class IFieldService(Protocol):
    """Protocol for field service operations needed by undo wrapper.

    The actual field service implementation must provide these methods.
    Typically implemented by a service that wraps UpdateFieldCommand.
    """

    def get_field_value(
        self,
        project_id: str,
        field_id: str,
    ) -> Result[Any, str]:
        """Get current field value.

        Args:
            project_id: Project identifier
            field_id: Field identifier

        Returns:
            Success(value) if found, Failure(error) otherwise
        """
        ...

    def set_field_value(
        self,
        project_id: str,
        field_id: str,
        value: Any,
    ) -> bool:
        """Set a field value.

        Args:
            project_id: Project identifier
            field_id: Field identifier
            value: New value to set

        Returns:
            True if successful, False otherwise
        """
        ...


class FieldUndoService:
    """Wraps field service calls with undo commands.

    Implements the wrapper service pattern for U6:
    1. Captures current state BEFORE change
    2. Creates SetFieldValueCommand with captured state
    3. Executes command via UndoManager (adds to undo stack)
    4. Returns result to caller

    Example:
        field_service = ... # concrete implementation
        undo_manager = UndoManager()
        field_undo_service = FieldUndoService(field_service, undo_manager)

        # User edits field
        result = field_undo_service.set_field_value(
            project_id="project-123",
            field_id="site_location",
            new_value="456 Elm St",
        )

        # Later: undo
        undo_manager.undo()  # Restores previous value
    """

    def __init__(
        self,
        field_service: IFieldService,
        undo_manager: UndoManager,
    ) -> None:
        """Initialize FieldUndoService.

        Args:
            field_service: Service for actual field operations
            undo_manager: Manager for undo/redo stack
        """
        self._field_service = field_service
        self._undo_manager = undo_manager

    def set_field_value(
        self,
        project_id: str,
        field_id: str,
        new_value: Any,
    ) -> Result[None, str]:
        """Set field value with undo support.

        Captures current state, creates command, executes via UndoManager.

        Args:
            project_id: Project identifier
            field_id: Field identifier
            new_value: New value to set

        Returns:
            Success(None) if successful, Failure(error) otherwise

        Side Effects:
            - Command added to undo stack
            - Redo stack cleared (standard undo semantics)
            - Domain events emitted (formula recalc, control eval, validation)
        """
        # 1. Get current value BEFORE change
        current_result = self._field_service.get_field_value(project_id, field_id)
        if isinstance(current_result, Failure):
            return Failure(f"Failed to get current value: {current_result.error}")

        previous_value = current_result.value

        # 2. Create undo state with captured values
        undo_state = UndoFieldState.create(
            field_id=field_id,
            previous_value=previous_value,
            new_value=new_value,
            was_formula_computed=False,  # TODO: detect if previous was formula result
        )

        # 3. Create command
        command = SetFieldValueCommand(
            project_id=project_id,
            state=undo_state,
            field_service=self._field_service,
        )

        # 4. Execute via UndoManager (adds to undo stack)
        success = self._undo_manager.execute(command)

        if success:
            return Success(None)
        else:
            return Failure("Command execution failed")

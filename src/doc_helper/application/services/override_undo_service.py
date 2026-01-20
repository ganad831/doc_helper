"""Wraps override operations in undoable commands.

RULES (unified_upgrade_plan_FINAL.md U6, H1-H5):
- Wrapper service pattern: captures state, creates command, executes via UndoManager
- State captured BEFORE operation (override state, field value)
- Commands delegate to IOverrideService for actual operation
- Override operations are NOT mergeable (unlike field edits)
"""

from typing import Any, Protocol

from doc_helper.application.undo.override_undo_command import (
    AcceptOverrideCommand,
    RejectOverrideCommand,
)
from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.application.undo.undo_state_dto import UndoOverrideState
from doc_helper.domain.common.result import Failure, Result, Success


class IOverrideService(Protocol):
    """Protocol for override service operations needed by undo wrapper.

    The actual override service implementation must provide these methods.
    """

    def get_override_state(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[str, str]:
        """Get current override state.

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            Success(state) if found, Failure(error) otherwise
            State values: "PENDING", "ACCEPTED", "REJECTED", "SYNCED", etc.
        """
        ...

    def get_override_field_id(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[str, str]:
        """Get field ID associated with override.

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            Success(field_id) if found, Failure(error) otherwise
        """
        ...

    def get_override_value(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[Any, str]:
        """Get override's proposed value.

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            Success(value) if found, Failure(error) otherwise
        """
        ...

    def accept_override(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        """Accept an override.

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            True if successful, False otherwise
        """
        ...

    def reject_override(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        """Reject an override.

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            True if successful, False otherwise
        """
        ...

    def restore_override_to_pending(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        """Restore an override to pending state.

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            True if successful, False otherwise
        """
        ...


class IFieldService(Protocol):
    """Protocol for field service operations needed by override commands."""

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


class OverrideUndoService:
    """Wraps override service calls with undo commands.

    Implements the wrapper service pattern for U6:
    1. Captures current state BEFORE operation (override state, field value)
    2. Creates AcceptOverrideCommand or RejectOverrideCommand
    3. Executes command via UndoManager (adds to undo stack)
    4. Returns result to caller

    Example:
        override_service = ... # concrete implementation
        field_service = ... # concrete implementation
        undo_manager = UndoManager()
        override_undo_service = OverrideUndoService(
            override_service, field_service, undo_manager
        )

        # User accepts override
        result = override_undo_service.accept_override(
            project_id="project-123",
            override_id="override-1",
        )

        # Later: undo (restores override to PENDING, restores field value)
        undo_manager.undo()
    """

    def __init__(
        self,
        override_service: IOverrideService,
        field_service: IFieldService,
        undo_manager: UndoManager,
    ) -> None:
        """Initialize OverrideUndoService.

        Args:
            override_service: Service for override state operations
            field_service: Service for field value operations
            undo_manager: Manager for undo/redo stack
        """
        self._override_service = override_service
        self._field_service = field_service
        self._undo_manager = undo_manager

    def accept_override(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[None, str]:
        """Accept override with undo support.

        Captures current state (override state, field value), creates command,
        executes via UndoManager.

        Args:
            project_id: Project identifier
            override_id: Override identifier to accept

        Returns:
            Success(None) if successful, Failure(error) otherwise

        Side Effects:
            - Override state changed to ACCEPTED
            - Field value set to override's value
            - Command added to undo stack
            - Redo stack cleared
            - Domain events emitted (formula recalc, control eval, validation)
        """
        # 1. Get override state BEFORE acceptance
        state_result = self._override_service.get_override_state(project_id, override_id)
        if isinstance(state_result, Failure):
            return Failure(f"Failed to get override state: {state_result.error}")

        previous_override_state = state_result.value

        # 2. Get field ID associated with override
        field_id_result = self._override_service.get_override_field_id(
            project_id, override_id
        )
        if isinstance(field_id_result, Failure):
            return Failure(f"Failed to get override field ID: {field_id_result.error}")

        field_id = field_id_result.value

        # 3. Get current field value BEFORE override accepted
        field_value_result = self._field_service.get_field_value(project_id, field_id)
        if isinstance(field_value_result, Failure):
            return Failure(f"Failed to get field value: {field_value_result.error}")

        previous_field_value = field_value_result.value

        # 4. Get override's proposed value
        override_value_result = self._override_service.get_override_value(
            project_id, override_id
        )
        if isinstance(override_value_result, Failure):
            return Failure(f"Failed to get override value: {override_value_result.error}")

        accepted_value = override_value_result.value

        # 5. Create undo state with captured values
        undo_state = UndoOverrideState.create(
            override_id=override_id,
            field_id=field_id,
            previous_override_state=previous_override_state,
            previous_field_value=previous_field_value,
            accepted_value=accepted_value,
            affected_formula_fields=(),  # TODO: detect dependent formulas
        )

        # 6. Create command
        command = AcceptOverrideCommand(
            project_id=project_id,
            state=undo_state,
            override_service=self._override_service,
            field_service=self._field_service,
        )

        # 7. Execute via UndoManager (adds to undo stack)
        success = self._undo_manager.execute(command)

        if success:
            return Success(None)
        else:
            return Failure("Command execution failed")

    def reject_override(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[None, str]:
        """Reject override with undo support.

        Captures current state (override state), creates command,
        executes via UndoManager.

        Args:
            project_id: Project identifier
            override_id: Override identifier to reject

        Returns:
            Success(None) if successful, Failure(error) otherwise

        Side Effects:
            - Override state changed to REJECTED
            - Field value unchanged (stays at current value)
            - Command added to undo stack
            - Redo stack cleared
        """
        # 1. Get override state BEFORE rejection
        state_result = self._override_service.get_override_state(project_id, override_id)
        if isinstance(state_result, Failure):
            return Failure(f"Failed to get override state: {state_result.error}")

        previous_override_state = state_result.value

        # 2. Get field ID associated with override
        field_id_result = self._override_service.get_override_field_id(
            project_id, override_id
        )
        if isinstance(field_id_result, Failure):
            return Failure(f"Failed to get override field ID: {field_id_result.error}")

        field_id = field_id_result.value

        # 3. Get current field value (unchanged by reject, but needed for undo state)
        field_value_result = self._field_service.get_field_value(project_id, field_id)
        if isinstance(field_value_result, Failure):
            return Failure(f"Failed to get field value: {field_value_result.error}")

        current_field_value = field_value_result.value

        # 4. Get override's proposed value (for undo state completeness)
        override_value_result = self._override_service.get_override_value(
            project_id, override_id
        )
        if isinstance(override_value_result, Failure):
            return Failure(f"Failed to get override value: {override_value_result.error}")

        override_value = override_value_result.value

        # 5. Create undo state with captured values
        undo_state = UndoOverrideState.create(
            override_id=override_id,
            field_id=field_id,
            previous_override_state=previous_override_state,
            previous_field_value=current_field_value,
            accepted_value=override_value,
            affected_formula_fields=(),
        )

        # 6. Create command
        command = RejectOverrideCommand(
            project_id=project_id,
            state=undo_state,
            override_service=self._override_service,
        )

        # 7. Execute via UndoManager (adds to undo stack)
        success = self._undo_manager.execute(command)

        if success:
            return Success(None)
        else:
            return Failure("Command execution failed")

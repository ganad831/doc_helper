"""Override undo commands for override state changes.

RULES (unified_upgrade_plan.md v1.3, H1, H5):
- Command-based undo captures: override_id, field_id, previous states
- Execute/undo/redo via service method calls
- Side effects cascade via event bus (formula recalc, control eval)
"""

from typing import Any, Protocol

from doc_helper.application.undo.undoable_command import UndoableCommand
from doc_helper.application.undo.undo_state_dto import UndoOverrideState


class IOverrideService(Protocol):
    """Protocol for override service operations needed by undo commands."""

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
            True if successful
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
            True if successful
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
            True if successful
        """
        ...


class IFieldService(Protocol):
    """Protocol for field service operations needed by override commands."""

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
            True if successful
        """
        ...


class AcceptOverrideCommand(UndoableCommand):
    """Command for undoable override acceptance.

    Captures the state before accepting an override, allowing
    the acceptance to be undone and redone.

    RULES (H1 COMMAND-BASED UNDO MODEL):
    - execute(): Accepts override, sets field to override value
    - undo(): Restores override to PENDING, restores field to previous value
    - redo(): Re-accepts override, sets field to override value

    Example:
        command = AcceptOverrideCommand(
            project_id="project-123",
            state=UndoOverrideState.create(
                override_id="override-1",
                field_id="F1",
                previous_override_state="PENDING",
                previous_field_value="100",
                accepted_value="150",
            ),
            override_service=override_service,
            field_service=field_service,
        )
        undo_manager.execute(command)
    """

    COMMAND_TYPE = "override_accept"

    def __init__(
        self,
        project_id: str,
        state: UndoOverrideState,
        override_service: IOverrideService,
        field_service: IFieldService,
    ) -> None:
        """Initialize AcceptOverrideCommand.

        Args:
            project_id: ID of project containing the override
            state: Captured undo state with previous states
            override_service: Service for override state changes
            field_service: Service for field value changes
        """
        if not isinstance(project_id, str) or not project_id:
            raise ValueError("project_id must be a non-empty string")
        if not isinstance(state, UndoOverrideState):
            raise TypeError("state must be an UndoOverrideState")

        self._project_id = project_id
        self._state = state
        self._override_service = override_service
        self._field_service = field_service

    @property
    def command_type(self) -> str:
        """Get the command type identifier."""
        return self.COMMAND_TYPE

    @property
    def description(self) -> str:
        """Get a human-readable description of the command."""
        return f"Accept override for field {self._state.field_id}"

    @property
    def project_id(self) -> str:
        """Get the project ID."""
        return self._project_id

    @property
    def override_id(self) -> str:
        """Get the override ID."""
        return self._state.override_id

    @property
    def field_id(self) -> str:
        """Get the field ID."""
        return self._state.field_id

    @property
    def state(self) -> UndoOverrideState:
        """Get the undo state."""
        return self._state

    def execute(self) -> bool:
        """Execute the command (accept the override).

        Returns:
            True if execution succeeded
        """
        return self._override_service.accept_override(
            project_id=self._project_id,
            override_id=self._state.override_id,
        )

    def undo(self) -> bool:
        """Undo the command (restore to pending and restore field value).

        Returns:
            True if undo succeeded
        """
        # Restore override to pending state
        if not self._override_service.restore_override_to_pending(
            project_id=self._project_id,
            override_id=self._state.override_id,
        ):
            return False

        # Restore field to previous value
        return self._field_service.set_field_value(
            project_id=self._project_id,
            field_id=self._state.field_id,
            value=self._state.previous_field_value,
        )

    def redo(self) -> bool:
        """Redo the command (re-accept the override).

        Returns:
            True if redo succeeded
        """
        return self._override_service.accept_override(
            project_id=self._project_id,
            override_id=self._state.override_id,
        )

    def can_merge_with(self, other: UndoableCommand) -> bool:
        """Check if this command can be merged with another.

        Override commands cannot be merged.

        Args:
            other: Another command

        Returns:
            Always False for override commands
        """
        return False

    def merge_with(self, other: UndoableCommand) -> UndoableCommand:
        """Merge this command with another.

        Args:
            other: The command to merge with

        Raises:
            ValueError: Always, as override commands cannot be merged
        """
        raise ValueError("Override commands cannot be merged")


class RejectOverrideCommand(UndoableCommand):
    """Command for undoable override rejection.

    Captures the state before rejecting an override, allowing
    the rejection to be undone and redone.

    RULES (H1 COMMAND-BASED UNDO MODEL):
    - execute(): Rejects override (keeps field at current value)
    - undo(): Restores override to PENDING
    - redo(): Re-rejects override

    Example:
        command = RejectOverrideCommand(
            project_id="project-123",
            state=UndoOverrideState.create(
                override_id="override-1",
                field_id="F1",
                previous_override_state="PENDING",
                previous_field_value="100",
                accepted_value="150",
            ),
            override_service=override_service,
        )
        undo_manager.execute(command)
    """

    COMMAND_TYPE = "override_reject"

    def __init__(
        self,
        project_id: str,
        state: UndoOverrideState,
        override_service: IOverrideService,
    ) -> None:
        """Initialize RejectOverrideCommand.

        Args:
            project_id: ID of project containing the override
            state: Captured undo state with previous states
            override_service: Service for override state changes
        """
        if not isinstance(project_id, str) or not project_id:
            raise ValueError("project_id must be a non-empty string")
        if not isinstance(state, UndoOverrideState):
            raise TypeError("state must be an UndoOverrideState")

        self._project_id = project_id
        self._state = state
        self._override_service = override_service

    @property
    def command_type(self) -> str:
        """Get the command type identifier."""
        return self.COMMAND_TYPE

    @property
    def description(self) -> str:
        """Get a human-readable description of the command."""
        return f"Reject override for field {self._state.field_id}"

    @property
    def project_id(self) -> str:
        """Get the project ID."""
        return self._project_id

    @property
    def override_id(self) -> str:
        """Get the override ID."""
        return self._state.override_id

    @property
    def field_id(self) -> str:
        """Get the field ID."""
        return self._state.field_id

    @property
    def state(self) -> UndoOverrideState:
        """Get the undo state."""
        return self._state

    def execute(self) -> bool:
        """Execute the command (reject the override).

        Returns:
            True if execution succeeded
        """
        return self._override_service.reject_override(
            project_id=self._project_id,
            override_id=self._state.override_id,
        )

    def undo(self) -> bool:
        """Undo the command (restore to pending).

        Returns:
            True if undo succeeded
        """
        return self._override_service.restore_override_to_pending(
            project_id=self._project_id,
            override_id=self._state.override_id,
        )

    def redo(self) -> bool:
        """Redo the command (re-reject the override).

        Returns:
            True if redo succeeded
        """
        return self._override_service.reject_override(
            project_id=self._project_id,
            override_id=self._state.override_id,
        )

    def can_merge_with(self, other: UndoableCommand) -> bool:
        """Check if this command can be merged with another.

        Override commands cannot be merged.

        Args:
            other: Another command

        Returns:
            Always False for override commands
        """
        return False

    def merge_with(self, other: UndoableCommand) -> UndoableCommand:
        """Merge this command with another.

        Args:
            other: The command to merge with

        Raises:
            ValueError: Always, as override commands cannot be merged
        """
        raise ValueError("Override commands cannot be merged")

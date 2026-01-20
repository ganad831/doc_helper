"""Field undo commands for field value changes.

RULES (unified_upgrade_plan.md v1.3, H1):
- Command-based undo captures: field_id, previous_value, new_value
- Execute/undo/redo via service method calls
- Side effects cascade via event bus (formula recalc, control eval)
"""

from typing import Any, Protocol

from doc_helper.application.undo.undoable_command import UndoableCommand
from doc_helper.application.undo.undo_state_dto import UndoFieldState


class IFieldService(Protocol):
    """Protocol for field service operations needed by undo commands."""

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


class SetFieldValueCommand(UndoableCommand):
    """Command for undoable field value changes.

    Captures the previous and new values for a field, allowing
    the change to be undone and redone.

    RULES (H1 COMMAND-BASED UNDO MODEL):
    - Captures field_id, previous_value, new_value
    - execute(): Sets field to new_value
    - undo(): Restores field to previous_value
    - redo(): Sets field to new_value again

    Example:
        command = SetFieldValueCommand(
            project_id="project-123",
            state=UndoFieldState.create(
                field_id="F1",
                previous_value="100",
                new_value="150",
            ),
            field_service=field_service,
        )
        undo_manager.execute(command)
    """

    COMMAND_TYPE = "field_edit"
    MERGE_WINDOW_MS = 500  # Merge commands within 500ms

    def __init__(
        self,
        project_id: str,
        state: UndoFieldState,
        field_service: IFieldService,
    ) -> None:
        """Initialize SetFieldValueCommand.

        Args:
            project_id: ID of project containing the field
            state: Captured undo state with previous/new values
            field_service: Service for applying field value changes
        """
        if not isinstance(project_id, str) or not project_id:
            raise ValueError("project_id must be a non-empty string")
        if not isinstance(state, UndoFieldState):
            raise TypeError("state must be an UndoFieldState")

        self._project_id = project_id
        self._state = state
        self._field_service = field_service

    @property
    def command_type(self) -> str:
        """Get the command type identifier."""
        return self.COMMAND_TYPE

    @property
    def description(self) -> str:
        """Get a human-readable description of the command."""
        return f"Edit field {self._state.field_id}"

    @property
    def project_id(self) -> str:
        """Get the project ID."""
        return self._project_id

    @property
    def field_id(self) -> str:
        """Get the field ID."""
        return self._state.field_id

    @property
    def previous_value(self) -> Any:
        """Get the previous value."""
        return self._state.previous_value

    @property
    def new_value(self) -> Any:
        """Get the new value."""
        return self._state.new_value

    @property
    def state(self) -> UndoFieldState:
        """Get the undo state."""
        return self._state

    def execute(self) -> bool:
        """Execute the command (apply the new value).

        Returns:
            True if execution succeeded
        """
        return self._field_service.set_field_value(
            project_id=self._project_id,
            field_id=self._state.field_id,
            value=self._state.new_value,
        )

    def undo(self) -> bool:
        """Undo the command (restore previous value).

        Returns:
            True if undo succeeded
        """
        return self._field_service.set_field_value(
            project_id=self._project_id,
            field_id=self._state.field_id,
            value=self._state.previous_value,
        )

    def redo(self) -> bool:
        """Redo the command (reapply new value).

        Returns:
            True if redo succeeded
        """
        return self._field_service.set_field_value(
            project_id=self._project_id,
            field_id=self._state.field_id,
            value=self._state.new_value,
        )

    def can_merge_with(self, other: UndoableCommand) -> bool:
        """Check if this command can be merged with another.

        Merges consecutive edits to the same field within MERGE_WINDOW_MS.

        Args:
            other: Another command to potentially merge with

        Returns:
            True if commands can be merged
        """
        if not isinstance(other, SetFieldValueCommand):
            return False

        # Must be same project and field
        if self._project_id != other._project_id:
            return False
        if self._state.field_id != other._state.field_id:
            return False

        # Check timestamp proximity (simple string comparison for ISO timestamps)
        # In practice, you might want more sophisticated time comparison
        from datetime import datetime

        try:
            self_time = datetime.fromisoformat(self._state.timestamp)
            other_time = datetime.fromisoformat(other._state.timestamp)
            diff_ms = abs((other_time - self_time).total_seconds() * 1000)
            return diff_ms <= self.MERGE_WINDOW_MS
        except (ValueError, TypeError):
            return False

    def merge_with(self, other: UndoableCommand) -> UndoableCommand:
        """Merge this command with another.

        The merged command keeps this command's previous_value
        and uses the other command's new_value.

        Args:
            other: The command to merge with

        Returns:
            New merged command

        Raises:
            ValueError: If commands cannot be merged
        """
        if not self.can_merge_with(other):
            raise ValueError("Commands cannot be merged")

        if not isinstance(other, SetFieldValueCommand):
            raise ValueError("Can only merge with SetFieldValueCommand")

        # Create merged state: keep original previous_value, use latest new_value
        merged_state = UndoFieldState(
            field_id=self._state.field_id,
            previous_value=self._state.previous_value,
            new_value=other._state.new_value,
            was_formula_computed=self._state.was_formula_computed,
            timestamp=other._state.timestamp,  # Use later timestamp
        )

        return SetFieldValueCommand(
            project_id=self._project_id,
            state=merged_state,
            field_service=self._field_service,
        )

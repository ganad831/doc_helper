"""UndoManager for managing undo/redo operations.

RULES (unified_upgrade_plan.md v1.3, H1):
- Command-based undo model (not snapshot)
- LIFO stacks for undo and redo
- Max depth: 100 (configurable)
- Cleared on: project close, project save (UPDATED by ADR-031: cleared ONLY on project close)
- New action clears redo stack

ADR-031: Undo History Persistence
- export_state(): Serialize undo/redo stacks to persistence DTO
- import_state(): Restore undo/redo stacks from persistence DTO
- Undo history persists across application restarts and saves
"""

from datetime import datetime
from typing import Callable, Optional

from doc_helper.application.undo.undoable_command import UndoableCommand
from doc_helper.application.undo.undo_persistence_dto import (
    UndoCommandPersistenceDTO,
    UndoHistoryPersistenceDTO,
)
from doc_helper.application.undo.field_undo_command import SetFieldValueCommand


class UndoManager:
    """Manages undo/redo operations using command pattern.

    Coordinates execution, undo, and redo of undoable commands.
    Maintains two stacks: undo stack and redo stack.

    RULES (H1 COMMAND-BASED UNDO MODEL):
    - execute(): Apply change, push to undo stack, clear redo stack
    - undo(): Pop from undo stack, call command.undo(), push to redo stack
    - redo(): Pop from redo stack, call command.redo(), push to undo stack

    Example:
        manager = UndoManager()

        # Execute a command
        command = SetFieldValueCommand(...)
        manager.execute(command)

        # Undo the last action
        if manager.can_undo:
            manager.undo()

        # Redo the undone action
        if manager.can_redo:
            manager.redo()
    """

    DEFAULT_MAX_DEPTH = 100

    def __init__(self, max_depth: int = DEFAULT_MAX_DEPTH) -> None:
        """Initialize UndoManager.

        Args:
            max_depth: Maximum number of commands in undo stack
        """
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")

        self._max_depth = max_depth
        self._undo_stack: list[UndoableCommand] = []
        self._redo_stack: list[UndoableCommand] = []
        self._on_state_changed: list[Callable[[], None]] = []

    @property
    def can_undo(self) -> bool:
        """Check if undo is available.

        Returns:
            True if there are commands to undo
        """
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        """Check if redo is available.

        Returns:
            True if there are commands to redo
        """
        return len(self._redo_stack) > 0

    @property
    def undo_description(self) -> Optional[str]:
        """Get description of the command that would be undone.

        Returns:
            Description string or None if no command to undo
        """
        if self._undo_stack:
            return self._undo_stack[-1].description
        return None

    @property
    def redo_description(self) -> Optional[str]:
        """Get description of the command that would be redone.

        Returns:
            Description string or None if no command to redo
        """
        if self._redo_stack:
            return self._redo_stack[-1].description
        return None

    @property
    def undo_count(self) -> int:
        """Get number of commands in undo stack.

        Returns:
            Number of undoable commands
        """
        return len(self._undo_stack)

    @property
    def redo_count(self) -> int:
        """Get number of commands in redo stack.

        Returns:
            Number of redoable commands
        """
        return len(self._redo_stack)

    def execute(self, command: UndoableCommand) -> bool:
        """Execute a command and add it to the undo stack.

        Args:
            command: The command to execute

        Returns:
            True if execution succeeded

        Side Effects:
            - Executes the command
            - Clears the redo stack (standard undo semantics)
            - Pushes command to undo stack
            - May merge with previous command if compatible
            - Notifies state change listeners
        """
        if not isinstance(command, UndoableCommand):
            raise TypeError("command must be an UndoableCommand")

        # Execute the command
        if not command.execute():
            return False

        # Clear redo stack (new action invalidates redo history)
        self._redo_stack.clear()

        # Check if we can merge with the last command
        if self._undo_stack and self._undo_stack[-1].can_merge_with(command):
            merged = self._undo_stack[-1].merge_with(command)
            self._undo_stack[-1] = merged
        else:
            # Push to undo stack
            self._undo_stack.append(command)

            # Enforce max depth
            while len(self._undo_stack) > self._max_depth:
                self._undo_stack.pop(0)

        self._notify_state_changed()
        return True

    def undo(self) -> bool:
        """Undo the most recent command.

        Returns:
            True if undo succeeded, False if nothing to undo or undo failed

        Side Effects:
            - Pops command from undo stack
            - Calls command.undo() to restore previous state
            - Pushes command to redo stack
            - Triggers formula/control recalculation via event bus
            - Notifies state change listeners
        """
        if not self._undo_stack:
            return False

        command = self._undo_stack.pop()

        if not command.undo():
            # Undo failed, restore to undo stack
            self._undo_stack.append(command)
            return False

        self._redo_stack.append(command)
        self._notify_state_changed()
        return True

    def redo(self) -> bool:
        """Redo the most recently undone command.

        Returns:
            True if redo succeeded, False if nothing to redo or redo failed

        Side Effects:
            - Pops command from redo stack
            - Calls command.redo() to reapply change
            - Pushes command to undo stack
            - Triggers formula/control recalculation via event bus
            - Notifies state change listeners
        """
        if not self._redo_stack:
            return False

        command = self._redo_stack.pop()

        if not command.redo():
            # Redo failed, restore to redo stack
            self._redo_stack.append(command)
            return False

        self._undo_stack.append(command)
        self._notify_state_changed()
        return True

    def clear(self) -> None:
        """Clear both undo and redo stacks.

        ADR-031: Called ONLY on explicit project close (not on save).
        Undo history now persists across saves and application restarts.

        Side Effects:
            - Clears undo stack
            - Clears redo stack
            - Notifies state change listeners
        """
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify_state_changed()

    def subscribe(self, callback: Callable[[], None]) -> None:
        """Subscribe to state change notifications.

        Args:
            callback: Function to call when undo/redo state changes
        """
        if callback not in self._on_state_changed:
            self._on_state_changed.append(callback)

    def unsubscribe(self, callback: Callable[[], None]) -> None:
        """Unsubscribe from state change notifications.

        Args:
            callback: Previously subscribed callback
        """
        if callback in self._on_state_changed:
            self._on_state_changed.remove(callback)

    def export_state(self, project_id: str) -> UndoHistoryPersistenceDTO:
        """Export undo/redo stacks to persistence DTO for saving.

        ADR-031: Converts in-memory command objects to serializable DTOs
        containing only the minimal state needed to reconstruct commands.

        Args:
            project_id: Project ID for the undo history

        Returns:
            UndoHistoryPersistenceDTO containing serialized undo/redo stacks

        Example:
            persistence_dto = undo_manager.export_state(project_id="proj-123")
            undo_history_repo.save(persistence_dto)
        """
        # Convert commands to persistence DTOs
        undo_persistence_stack = tuple(
            self._command_to_persistence_dto(cmd) for cmd in self._undo_stack
        )
        redo_persistence_stack = tuple(
            self._command_to_persistence_dto(cmd) for cmd in self._redo_stack
        )

        return UndoHistoryPersistenceDTO(
            project_id=project_id,
            undo_stack=undo_persistence_stack,
            redo_stack=redo_persistence_stack,
            max_stack_depth=self._max_depth,
            last_modified=datetime.utcnow().isoformat(),
        )

    def import_state(
        self,
        history: UndoHistoryPersistenceDTO,
        command_factory: Callable[[UndoCommandPersistenceDTO], Optional[UndoableCommand]],
    ) -> None:
        """Restore undo/redo stacks from persistence DTO.

        ADR-031: Reconstructs command objects from persistence DTOs using
        provided factory. The factory must inject runtime dependencies
        (field_service, etc.) when creating commands.

        Args:
            history: Persistence DTO containing serialized undo/redo stacks
            command_factory: Factory function to reconstruct commands from DTOs.
                            Returns None if command cannot be reconstructed.

        Side Effects:
            - Clears existing undo and redo stacks
            - Restores stacks from persistence DTO
            - Notifies state change listeners

        Example:
            def factory(dto: UndoCommandPersistenceDTO) -> Optional[UndoableCommand]:
                if dto.command_type == "field_value":
                    state = dto.to_field_state()
                    return SetFieldValueCommand(
                        project_id=project_id,
                        state=state,
                        field_service=field_service  # Fresh dependency
                    )
                return None

            undo_manager.import_state(persistence_dto, factory)
        """
        # Clear existing stacks
        self._undo_stack.clear()
        self._redo_stack.clear()

        # Reconstruct commands from persistence DTOs
        for persistence_dto in history.undo_stack:
            command = command_factory(persistence_dto)
            if command is not None:
                self._undo_stack.append(command)

        for persistence_dto in history.redo_stack:
            command = command_factory(persistence_dto)
            if command is not None:
                self._redo_stack.append(command)

        # Update max depth from persisted value
        self._max_depth = history.max_stack_depth

        self._notify_state_changed()

    def _command_to_persistence_dto(
        self, command: UndoableCommand
    ) -> UndoCommandPersistenceDTO:
        """Convert an UndoableCommand to a persistence DTO.

        ADR-031: Extracts only the state needed to reconstruct the command,
        omitting runtime dependencies (field_service, etc.).

        Args:
            command: Command to convert

        Returns:
            UndoCommandPersistenceDTO containing command state

        Raises:
            ValueError: If command type is unknown
        """
        if isinstance(command, SetFieldValueCommand):
            return UndoCommandPersistenceDTO.from_field_state(command.state)

        # Add more command types as they're implemented (e.g., override commands)
        # For now, raise error for unknown types
        raise ValueError(f"Unknown command type: {type(command).__name__}")

    def _notify_state_changed(self) -> None:
        """Notify all subscribers of state change."""
        for callback in self._on_state_changed:
            try:
                callback()
            except Exception:
                # Don't let subscriber errors break the undo manager
                pass

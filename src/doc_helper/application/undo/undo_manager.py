"""UndoManager for managing undo/redo operations.

RULES (unified_upgrade_plan.md v1.3, H1):
- Command-based undo model (not snapshot)
- LIFO stacks for undo and redo
- Max depth: 100 (configurable)
- Cleared on: project close, project save
- New action clears redo stack
"""

from typing import Callable, Optional

from doc_helper.application.undo.undoable_command import UndoableCommand


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

        Called on project close or project save.

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

    def _notify_state_changed(self) -> None:
        """Notify all subscribers of state change."""
        for callback in self._on_state_changed:
            try:
                callback()
            except Exception:
                # Don't let subscriber errors break the undo manager
                pass

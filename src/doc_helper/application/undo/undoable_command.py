"""UndoableCommand interface for undo/redo system.

RULES (unified_upgrade_plan.md v1.3, H1):
- Command-based undo model: each command captures what changed
- Commands know how to undo and redo themselves
- Commands are immutable after creation
"""

from abc import ABC, abstractmethod
from typing import Any


class UndoableCommand(ABC):
    """Base interface for undoable commands.

    All undoable operations must implement this interface.
    Commands capture the state needed to undo/redo the operation.

    RULES (H1 COMMAND-BASED UNDO MODEL):
    - Commands capture: field_id, previous_value, new_value, command_type
    - Commands execute, undo, and redo via service method calls
    - Commands are stored in UndoStack/RedoStack (LIFO)

    Example:
        command = SetFieldValueCommand(
            field_id="F1",
            previous_value="100",
            new_value="150",
            services=service_bundle
        )
        undo_manager.execute(command)  # Applies change, pushes to undo stack
        undo_manager.undo()  # Restores previous value
        undo_manager.redo()  # Reapplies new value
    """

    @property
    @abstractmethod
    def command_type(self) -> str:
        """Get the command type identifier.

        Returns:
            String identifying the command type (e.g., "field_edit", "override_accept")
        """
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Get a human-readable description of the command.

        Returns:
            Description for display in undo/redo UI (e.g., "Edit field F1")
        """
        ...

    @abstractmethod
    def execute(self) -> bool:
        """Execute the command (apply the change).

        Returns:
            True if execution succeeded, False otherwise

        Side Effects:
            - Applies change to domain via application services
            - May trigger formula recalculation via event bus
            - May trigger control evaluation via event bus
        """
        ...

    @abstractmethod
    def undo(self) -> bool:
        """Undo the command (restore previous state).

        Returns:
            True if undo succeeded, False otherwise

        Side Effects:
            - Restores previous state via application services
            - Triggers formula recalculation for affected dependents
            - Triggers control re-evaluation
        """
        ...

    @abstractmethod
    def redo(self) -> bool:
        """Redo the command (reapply the change).

        Returns:
            True if redo succeeded, False otherwise

        Side Effects:
            - Reapplies the change via application services
            - Triggers formula recalculation
            - Triggers control evaluation
        """
        ...

    @abstractmethod
    def can_merge_with(self, other: "UndoableCommand") -> bool:
        """Check if this command can be merged with another.

        Merging combines consecutive similar commands (e.g., rapid keystrokes
        in a text field) into a single undo step.

        Args:
            other: Another command to potentially merge with

        Returns:
            True if commands can be merged, False otherwise
        """
        ...

    @abstractmethod
    def merge_with(self, other: "UndoableCommand") -> "UndoableCommand":
        """Merge this command with another.

        Args:
            other: The command to merge with (must be mergeable)

        Returns:
            New merged command

        Raises:
            ValueError: If commands cannot be merged
        """
        ...

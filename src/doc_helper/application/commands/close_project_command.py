"""Command for closing a project.

RULES (IMPLEMENTATION_RULES.md Section 5):
- Commands take IDs and primitive data, NOT domain objects
- Domain objects are loaded internally and never cross boundaries

ADR-031: Undo History Persistence
- Deletes persisted undo history on explicit project close (session boundary)
- Clears undo/redo stacks in UndoManager
- Undo history does NOT survive project close
"""

from typing import Optional

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.application.undo.undo_history_repository import IUndoHistoryRepository
from doc_helper.application.undo.undo_manager import UndoManager


class CloseProjectCommand:
    """Command to close a project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands return Result[None, str]
    - Commands take IDs, not domain objects

    ADR-031: On explicit project close, deletes persisted undo history
    and clears undo/redo stacks. This marks a session boundary - undo
    history does not survive project close.

    Note: This is distinct from SaveProjectCommand, which preserves
    undo history. Close is an explicit session termination.

    Example:
        command = CloseProjectCommand(
            undo_history_repository=undo_repo,
            undo_manager=undo_mgr
        )
        result = command.execute(project_id=project_id)
        if isinstance(result, Success):
            print("Project closed, undo history cleared")
    """

    def __init__(
        self,
        undo_history_repository: Optional[IUndoHistoryRepository] = None,
        undo_manager: Optional[UndoManager] = None,
    ) -> None:
        """Initialize command.

        Args:
            undo_history_repository: Repository for deleting undo history (optional)
            undo_manager: Undo manager for clearing undo/redo stacks (optional)
        """
        self._undo_history_repository = undo_history_repository
        self._undo_manager = undo_manager

    def execute(self, project_id: ProjectId) -> Result[None, str]:
        """Execute close project command.

        ADR-031: Deletes persisted undo history and clears undo/redo stacks.

        Args:
            project_id: ID of project to close

        Returns:
            Success(None) if closed, Failure(error) otherwise
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        # ADR-031: Clear undo/redo stacks (session boundary)
        if self._undo_manager is not None:
            self._undo_manager.clear()

        # ADR-031: Delete persisted undo history
        if self._undo_history_repository is not None:
            delete_result = self._undo_history_repository.delete(
                project_id=str(project_id.value)
            )

            if isinstance(delete_result, Failure):
                # Log warning but don't fail close operation
                print(
                    f"Warning: Failed to delete undo history: {delete_result.error}"
                )

        return Success(None)

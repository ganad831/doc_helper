"""Repository interface for undo history persistence.

ADR-031: Undo History Persistence
RULES:
- Interface in Application layer (undo is application-level concern)
- Implementation in Infrastructure layer
- Project-scoped storage (one undo history per project)
- Best-effort restoration (failure doesn't prevent project open)
"""

from abc import ABC, abstractmethod
from typing import Optional

from doc_helper.application.undo.undo_persistence_dto import UndoHistoryPersistenceDTO
from doc_helper.domain.common.result import Result


class IUndoHistoryRepository(ABC):
    """Repository interface for persisting and restoring undo history.

    ADR-031: Project-scoped undo history storage.

    Lifecycle:
    - save(): Called on project save and application close
    - load(): Called on project open
    - delete(): Called on explicit project close (session boundary)
    - exists(): Check if persisted undo exists for project

    Example:
        repo = SqliteUndoHistoryRepository(db_path="project.db")

        # Save undo history
        history = UndoHistoryPersistenceDTO(...)
        result = repo.save(history)

        # Load undo history
        load_result = repo.load(project_id="proj-123")
        if load_result.is_success and load_result.value is not None:
            history = load_result.value

        # Delete on project close
        repo.delete(project_id="proj-123")
    """

    @abstractmethod
    def save(self, history: UndoHistoryPersistenceDTO) -> Result[None, str]:
        """Save undo history for a project.

        ADR-031: Called during project save and application close.
        Overwrites existing undo history for the project.

        Args:
            history: UndoHistoryPersistenceDTO containing undo/redo stacks

        Returns:
            Success(None) if saved successfully
            Failure(error) if save failed

        Example:
            history = UndoHistoryPersistenceDTO(
                project_id="proj-123",
                undo_stack=(cmd1, cmd2, cmd3),
                redo_stack=(),
                max_stack_depth=50,
                last_modified="2026-01-21T10:00:00.000Z"
            )
            result = repo.save(history)
        """
        pass

    @abstractmethod
    def load(self, project_id: str) -> Result[Optional[UndoHistoryPersistenceDTO], str]:
        """Load undo history for a project.

        ADR-031: Called during project open. Best-effort restoration - if load
        fails, returns Success(None) (project opens with empty undo stack).

        Args:
            project_id: Project identifier

        Returns:
            Success(UndoHistoryPersistenceDTO) if found
            Success(None) if not found (new project or first open after feature)
            Failure(error) only on severe database errors

        Example:
            result = repo.load(project_id="proj-123")
            if result.is_success:
                history = result.value  # May be None
                if history is None:
                    print("No persisted undo history")
                else:
                    print(f"Restored {len(history.undo_stack)} undo operations")
        """
        pass

    @abstractmethod
    def delete(self, project_id: str) -> Result[None, str]:
        """Delete undo history for a project.

        ADR-031: Called when project is explicitly closed (session boundary).
        Undo history does not survive project close.

        Args:
            project_id: Project identifier

        Returns:
            Success(None) if deleted successfully
            Failure(error) if delete failed

        Example:
            result = repo.delete(project_id="proj-123")
        """
        pass

    @abstractmethod
    def exists(self, project_id: str) -> Result[bool, str]:
        """Check if undo history exists for a project.

        Optional convenience method for checking existence before load.

        Args:
            project_id: Project identifier

        Returns:
            Success(True) if undo history exists
            Success(False) if not found
            Failure(error) on database error

        Example:
            result = repo.exists(project_id="proj-123")
            if result.is_success and result.value:
                print("Undo history available")
        """
        pass

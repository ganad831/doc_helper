"""Command for saving a project.

RULES (IMPLEMENTATION_RULES.md Section 5):
- Commands take IDs and primitive data, NOT domain objects
- Domain objects are loaded internally and never cross boundaries

ADR-031: Undo History Persistence
- Saves undo history after successful project save
- Undo history persists across application restarts
- Undo persistence failure logs warning but doesn't block save
"""

from typing import Optional

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.application.undo.undo_history_repository import IUndoHistoryRepository
from doc_helper.application.undo.undo_manager import UndoManager


class SaveProjectCommand:
    """Command to save a project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands modify state and return Result[None, str]
    - Commands take IDs, not domain objects

    ADR-031: After successfully saving project, persists undo history
    to allow undo/redo across application restarts. Undo persistence
    failure is non-blocking (logs warning, doesn't fail save operation).

    Note: This command explicitly saves a project to ensure persistence.
    The UpdateFieldCommand may save automatically on each update, but this
    command provides explicit save semantics for batched changes or when
    the project's is_saved flag needs to be updated.

    Example:
        command = SaveProjectCommand(
            project_repository=repo,
            undo_history_repository=undo_repo,
            undo_manager=undo_mgr
        )
        result = command.execute(project_id=project_id)
        if isinstance(result, Success):
            print("Project saved")
    """

    def __init__(
        self,
        project_repository: IProjectRepository,
        undo_history_repository: Optional[IUndoHistoryRepository] = None,
        undo_manager: Optional[UndoManager] = None,
    ) -> None:
        """Initialize command.

        Args:
            project_repository: Repository for persisting projects
            undo_history_repository: Repository for persisting undo history (optional)
            undo_manager: Undo manager for exporting undo state (optional)
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        self._project_repository = project_repository
        self._undo_history_repository = undo_history_repository
        self._undo_manager = undo_manager

    def execute(self, project_id: ProjectId) -> Result[None, str]:
        """Execute save project command.

        ADR-031: After successful save, persists undo history for cross-session restoration.

        Args:
            project_id: ID of project to save

        Returns:
            Success(None) if saved, Failure(error) otherwise
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        # Load project
        load_result = self._project_repository.get_by_id(project_id)
        if isinstance(load_result, Failure):
            return Failure(f"Failed to load project: {load_result.error}")

        project = load_result.value
        if project is None:
            return Failure(f"Project not found: {project_id.value}")

        # Save project
        save_result = self._project_repository.save(project)
        if isinstance(save_result, Failure):
            return Failure(f"Failed to save project: {save_result.error}")

        # ADR-031: Persist undo history after successful project save
        # (failure is non-blocking - logs warning but doesn't fail save)
        self._persist_undo_history(project_id)

        return Success(None)

    def _persist_undo_history(self, project_id: ProjectId) -> None:
        """Persist undo history after successful project save.

        ADR-031: Best-effort persistence - failure logs warning but doesn't block.

        Args:
            project_id: Project ID for undo history
        """
        # Skip if undo persistence not configured
        if self._undo_history_repository is None or self._undo_manager is None:
            return

        try:
            # Export undo state from manager
            undo_history_dto = self._undo_manager.export_state(
                project_id=str(project_id.value)
            )

            # Persist to repository
            persist_result = self._undo_history_repository.save(undo_history_dto)
            if isinstance(persist_result, Failure):
                # ADR-031: Non-blocking failure - log warning
                print(
                    f"Warning: Failed to persist undo history: {persist_result.error}"
                )
        except Exception as e:
            # ADR-031: Non-blocking failure - log warning
            print(f"Warning: Exception while persisting undo history: {str(e)}")

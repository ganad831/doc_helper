"""Command for saving a project.

RULES (IMPLEMENTATION_RULES.md Section 5):
- Commands take IDs and primitive data, NOT domain objects
- Domain objects are loaded internally and never cross boundaries
"""

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository


class SaveProjectCommand:
    """Command to save a project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands modify state and return Result[None, str]
    - Commands take IDs, not domain objects

    Note: This command explicitly saves a project to ensure persistence.
    The UpdateFieldCommand may save automatically on each update, but this
    command provides explicit save semantics for batched changes or when
    the project's is_saved flag needs to be updated.

    Example:
        command = SaveProjectCommand(project_repository=repo)
        result = command.execute(project_id=project_id)
        if isinstance(result, Success):
            print("Project saved")
    """

    def __init__(self, project_repository: IProjectRepository) -> None:
        """Initialize command.

        Args:
            project_repository: Repository for persisting projects
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        self._project_repository = project_repository

    def execute(self, project_id: ProjectId) -> Result[None, str]:
        """Execute save project command.

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

        return Success(None)

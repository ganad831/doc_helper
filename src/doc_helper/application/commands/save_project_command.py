"""Command for saving a project."""

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_repository import IProjectRepository


class SaveProjectCommand:
    """Command to save a project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands modify state and return Result[None, str]

    Example:
        command = SaveProjectCommand(project_repository=repo)
        result = command.execute(project=project)
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

    def execute(self, project: Project) -> Result[None, str]:
        """Execute save project command.

        Args:
            project: Project to save

        Returns:
            Success(None) if saved, Failure(error) otherwise
        """
        if not isinstance(project, Project):
            return Failure("project must be a Project instance")

        # Save project
        save_result = self._project_repository.save(project)
        if isinstance(save_result, Failure):
            return Failure(f"Failed to save project: {save_result.error}")

        return Success(None)

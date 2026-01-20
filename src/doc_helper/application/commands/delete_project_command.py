"""Command for deleting a project."""

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository


class DeleteProjectCommand:
    """Command to delete a project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands modify state and return Result[None, str]

    Example:
        command = DeleteProjectCommand(project_repository=repo)
        result = command.execute(project_id=project_id)
        if isinstance(result, Success):
            print("Project deleted")
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
        """Execute delete project command.

        Args:
            project_id: Project ID to delete

        Returns:
            Success(None) if deleted, Failure(error) otherwise
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        # Delete project
        delete_result = self._project_repository.delete(project_id)
        if isinstance(delete_result, Failure):
            return Failure(f"Failed to delete project: {delete_result.error}")

        return Success(None)

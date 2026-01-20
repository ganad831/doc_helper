"""Query for retrieving a project.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- Queries return DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary
- Use mappers to convert Domain → DTO
"""

from typing import Optional

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.application.dto import ProjectDTO
from doc_helper.application.mappers import ProjectMapper


class GetProjectQuery:
    """Query to retrieve a project by ID.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return DTOs, not domain objects
    - CQRS pattern: separate reads from writes

    Example:
        query = GetProjectQuery(project_repository=repo)
        result = query.execute(project_id=project_id)
        if isinstance(result, Success):
            project_dto = result.value  # Returns ProjectDTO, not Project
    """

    def __init__(self, project_repository: IProjectRepository) -> None:
        """Initialize query.

        Args:
            project_repository: Repository for loading projects
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        self._project_repository = project_repository

    def execute(self, project_id: ProjectId) -> Result[Optional[ProjectDTO], str]:
        """Execute get project query.

        Args:
            project_id: Project ID to retrieve

        Returns:
            Success(ProjectDTO) if found, Success(None) if not found,
            Failure(error) on error
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        # Load project
        result = self._project_repository.get_by_id(project_id)
        if isinstance(result, Failure):
            return result

        project = result.value
        if project is None:
            return Success(None)

        # Map to DTO before returning (domain objects don't cross Application boundary)
        return Success(ProjectMapper.to_dto(project))


class GetAllProjectsQuery:
    """Query to retrieve all projects.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return DTOs, not domain objects

    Example:
        query = GetAllProjectsQuery(project_repository=repo)
        result = query.execute()
        if isinstance(result, Success):
            project_dtos = result.value  # List of ProjectSummaryDTO
    """

    def __init__(self, project_repository: IProjectRepository) -> None:
        """Initialize query.

        Args:
            project_repository: Repository for loading projects
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        self._project_repository = project_repository

    def execute(self) -> Result[list, str]:  # Result[List[ProjectSummaryDTO], str]
        """Execute get all projects query.

        Returns:
            Success(list of ProjectSummaryDTO) if successful, Failure(error) otherwise
        """
        result = self._project_repository.get_all()
        if isinstance(result, Failure):
            return result

        # Map to DTOs before returning
        projects = result.value
        return Success([ProjectMapper.to_summary_dto(p) for p in projects])


class GetRecentProjectsQuery:
    """Query to retrieve recent projects.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return DTOs, not domain objects

    Example:
        query = GetRecentProjectsQuery(project_repository=repo)
        result = query.execute(limit=5)
        if isinstance(result, Success):
            project_dtos = result.value  # List of ProjectSummaryDTO
    """

    def __init__(self, project_repository: IProjectRepository) -> None:
        """Initialize query.

        Args:
            project_repository: Repository for loading projects
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        self._project_repository = project_repository

    def execute(self, limit: int = 10) -> Result[list, str]:  # Result[List[ProjectSummaryDTO], str]
        """Execute get recent projects query.

        Args:
            limit: Maximum number of projects to return

        Returns:
            Success(list of ProjectSummaryDTO) if successful, Failure(error) otherwise
        """
        if not isinstance(limit, int) or limit <= 0:
            return Failure("limit must be a positive integer")

        result = self._project_repository.get_recent(limit)
        if isinstance(result, Failure):
            return result

        # Map to DTOs before returning
        projects = result.value
        return Success([ProjectMapper.to_summary_dto(p) for p in projects])

"""Query for retrieving a project."""

from typing import Optional

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository


class GetProjectQuery:
    """Query to retrieve a project by ID.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return data and don't modify state
    - CQRS pattern: separate reads from writes

    Example:
        query = GetProjectQuery(project_repository=repo)
        result = query.execute(project_id=project_id)
        if isinstance(result, Success):
            project = result.value
    """

    def __init__(self, project_repository: IProjectRepository) -> None:
        """Initialize query.

        Args:
            project_repository: Repository for loading projects
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        self._project_repository = project_repository

    def execute(self, project_id: ProjectId) -> Result[Optional[Project], str]:
        """Execute get project query.

        Args:
            project_id: Project ID to retrieve

        Returns:
            Success(Project) if found, Success(None) if not found,
            Failure(error) on error
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        # Load project
        return self._project_repository.get_by_id(project_id)


class GetAllProjectsQuery:
    """Query to retrieve all projects.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return data and don't modify state

    Example:
        query = GetAllProjectsQuery(project_repository=repo)
        result = query.execute()
        if isinstance(result, Success):
            projects = result.value
    """

    def __init__(self, project_repository: IProjectRepository) -> None:
        """Initialize query.

        Args:
            project_repository: Repository for loading projects
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        self._project_repository = project_repository

    def execute(self) -> Result[list, str]:  # Result[List[Project], str]
        """Execute get all projects query.

        Returns:
            Success(list of Projects) if successful, Failure(error) otherwise
        """
        return self._project_repository.get_all()


class GetRecentProjectsQuery:
    """Query to retrieve recent projects.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return data and don't modify state

    Example:
        query = GetRecentProjectsQuery(project_repository=repo)
        result = query.execute(limit=5)
        if isinstance(result, Success):
            projects = result.value
    """

    def __init__(self, project_repository: IProjectRepository) -> None:
        """Initialize query.

        Args:
            project_repository: Repository for loading projects
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        self._project_repository = project_repository

    def execute(self, limit: int = 10) -> Result[list, str]:  # Result[List[Project], str]
        """Execute get recent projects query.

        Args:
            limit: Maximum number of projects to return

        Returns:
            Success(list of Projects) if successful, Failure(error) otherwise
        """
        if not isinstance(limit, int) or limit <= 0:
            return Failure("limit must be a positive integer")

        return self._project_repository.get_recent(limit)

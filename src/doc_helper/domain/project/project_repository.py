"""Project repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from doc_helper.domain.common.result import Result
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId


class IProjectRepository(ABC):
    """Repository interface for Project aggregate.

    The repository provides access to Project aggregates following
    the Repository pattern (ADR-005).

    RULES:
    - Only aggregate roots have repositories
    - Repository returns Result[T, E] for error handling
    - Infrastructure implements this interface
    - Domain defines the interface

    Example:
        # Save project
        result = repository.save(project)
        if isinstance(result, Success):
            print("Project saved")

        # Get project by ID
        result = repository.get_by_id(project_id)
        if isinstance(result, Success):
            project = result.value

        # Get all projects
        result = repository.get_all()
        if isinstance(result, Success):
            projects = result.value
    """

    @abstractmethod
    def save(self, project: Project) -> Result[None, str]:
        """Save or update a project.

        Args:
            project: Project to save

        Returns:
            Success(None) if saved, Failure(error) otherwise
        """
        pass

    @abstractmethod
    def get_by_id(self, project_id: ProjectId) -> Result[Optional[Project], str]:
        """Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Success(Project) if found, Success(None) if not found, Failure(error) on error
        """
        pass

    @abstractmethod
    def get_all(self) -> Result[list, str]:  # Result[List[Project], str]
        """Get all projects.

        Returns:
            Success(list of Projects) if successful, Failure(error) otherwise
        """
        pass

    @abstractmethod
    def delete(self, project_id: ProjectId) -> Result[None, str]:
        """Delete a project.

        Args:
            project_id: Project ID

        Returns:
            Success(None) if deleted, Failure(error) otherwise
        """
        pass

    @abstractmethod
    def exists(self, project_id: ProjectId) -> Result[bool, str]:
        """Check if project exists.

        Args:
            project_id: Project ID

        Returns:
            Success(True) if exists, Success(False) if not, Failure(error) on error
        """
        pass

    @abstractmethod
    def get_recent(self, limit: int = 10) -> Result[list, str]:  # Result[List[Project], str]
        """Get recent projects ordered by modification date.

        Args:
            limit: Maximum number of projects to return (default 10)

        Returns:
            Success(list of Projects) if successful, Failure(error) otherwise
        """
        pass

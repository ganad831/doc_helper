"""Override repository interfaces."""

from abc import ABC, abstractmethod
from typing import Optional

from doc_helper.domain.common.result import Result
from doc_helper.domain.override.override_entity import Override
from doc_helper.domain.override.override_ids import OverrideId
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class IOverrideRepository(ABC):
    """Repository interface for Override aggregate.

    Provides persistence operations for Override entities.

    RULES:
    - Repository returns domain objects, not DTOs
    - All operations return Result[T, E] for explicit error handling
    - Repository has no business logic, only persistence
    - Interface defined in domain, implementation in infrastructure

    Example:
        class SqliteOverrideRepository(IOverrideRepository):
            def get_by_id(self, override_id: OverrideId) -> Result[Override, str]:
                # SQLite implementation
                pass
    """

    @abstractmethod
    def get_by_id(self, override_id: OverrideId) -> Result[Override, str]:
        """Get override by ID.

        Args:
            override_id: Override identifier

        Returns:
            Success(override) if found
            Failure(error) if not found or error occurred
        """
        pass

    @abstractmethod
    def get_by_project_and_field(
        self, project_id: ProjectId, field_id: FieldDefinitionId
    ) -> Result[Optional[Override], str]:
        """Get override for a specific field in a project.

        Args:
            project_id: Project identifier
            field_id: Field identifier

        Returns:
            Success(override) if found
            Success(None) if no override exists for this field
            Failure(error) if error occurred
        """
        pass

    @abstractmethod
    def list_by_project(self, project_id: ProjectId) -> Result[tuple[Override, ...], str]:
        """Get all overrides for a project.

        Args:
            project_id: Project identifier

        Returns:
            Success(tuple of overrides) if found (may be empty tuple)
            Failure(error) if error occurred
        """
        pass

    @abstractmethod
    def save(self, override: Override) -> Result[None, str]:
        """Save override (create or update).

        Args:
            override: Override to save

        Returns:
            Success(None) if saved successfully
            Failure(error) if save failed
        """
        pass

    @abstractmethod
    def delete(self, override_id: OverrideId) -> Result[None, str]:
        """Delete override by ID.

        Args:
            override_id: Override identifier

        Returns:
            Success(None) if deleted successfully
            Failure(error) if delete failed or override not found
        """
        pass

    @abstractmethod
    def delete_by_project_and_field(
        self, project_id: ProjectId, field_id: FieldDefinitionId
    ) -> Result[None, str]:
        """Delete override for a specific field in a project.

        Args:
            project_id: Project identifier
            field_id: Field identifier

        Returns:
            Success(None) if deleted successfully (or no override existed)
            Failure(error) if error occurred
        """
        pass

    @abstractmethod
    def exists(self, override_id: OverrideId) -> Result[bool, str]:
        """Check if override exists.

        Args:
            override_id: Override identifier

        Returns:
            Success(True) if exists
            Success(False) if does not exist
            Failure(error) if error occurred
        """
        pass

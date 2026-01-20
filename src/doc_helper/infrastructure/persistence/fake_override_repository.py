"""Fake in-memory override repository for testing.

TEMPORARY IMPLEMENTATION (v1):
- Used as a placeholder until full override UI is implemented
- Provides in-memory storage for testing purposes
- Will be replaced with SqliteOverrideRepository in future milestones

RULES (AGENT_RULES.md):
- Implements IOverrideRepository interface
- Returns domain objects, not DTOs
- All operations return Result[T, E]
"""

from typing import Optional

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.override.override_entity import Override
from doc_helper.domain.override.override_ids import OverrideId
from doc_helper.domain.override.repositories import IOverrideRepository
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class FakeOverrideRepository(IOverrideRepository):
    """In-memory fake override repository for testing.

    TEMPORARY: This is a placeholder implementation used in v1 since
    the override UI is not fully integrated. Will be replaced with
    SqliteOverrideRepository when override functionality is completed.

    Example:
        repo = FakeOverrideRepository()
        result = repo.save(override)
        if result.is_success:
            print("Override saved")
    """

    def __init__(self) -> None:
        """Initialize empty in-memory store."""
        self._overrides: dict[str, Override] = {}

    def get_by_id(self, override_id: OverrideId) -> Result[Override, str]:
        """Get override by ID.

        Args:
            override_id: Override identifier

        Returns:
            Success(override) if found
            Failure(error) if not found
        """
        override = self._overrides.get(override_id.value)
        if override is None:
            return Failure(f"Override {override_id.value} not found")
        return Success(override)

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
        """
        for override in self._overrides.values():
            if (
                override.project_id == project_id
                and override.field_id == field_id
            ):
                return Success(override)
        return Success(None)

    def list_by_project(self, project_id: ProjectId) -> Result[tuple[Override, ...], str]:
        """Get all overrides for a project.

        Args:
            project_id: Project identifier

        Returns:
            Success(tuple of overrides) (may be empty tuple)
        """
        project_overrides = [
            override
            for override in self._overrides.values()
            if override.project_id == project_id
        ]
        return Success(tuple(project_overrides))

    def save(self, override: Override) -> Result[None, str]:
        """Save override (create or update).

        Args:
            override: Override to save

        Returns:
            Success(None) if saved successfully
        """
        self._overrides[override.id.value] = override
        return Success(None)

    def delete(self, override_id: OverrideId) -> Result[None, str]:
        """Delete override by ID.

        Args:
            override_id: Override identifier

        Returns:
            Success(None) if deleted successfully
            Failure(error) if override not found
        """
        if override_id.value not in self._overrides:
            return Failure(f"Override {override_id.value} not found")
        del self._overrides[override_id.value]
        return Success(None)

    def delete_by_project_and_field(
        self, project_id: ProjectId, field_id: FieldDefinitionId
    ) -> Result[None, str]:
        """Delete override for a specific field in a project.

        Args:
            project_id: Project identifier
            field_id: Field identifier

        Returns:
            Success(None) if deleted successfully (or no override existed)
        """
        # Find and delete matching override
        override_to_delete = None
        for override_id, override in self._overrides.items():
            if (
                override.project_id == project_id
                and override.field_id == field_id
            ):
                override_to_delete = override_id
                break

        if override_to_delete is not None:
            del self._overrides[override_to_delete]

        return Success(None)

    def exists(self, override_id: OverrideId) -> Result[bool, str]:
        """Check if override exists.

        Args:
            override_id: Override identifier

        Returns:
            Success(True) if exists
            Success(False) if does not exist
        """
        exists = override_id.value in self._overrides
        return Success(exists)

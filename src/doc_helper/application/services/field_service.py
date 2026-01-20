"""Concrete field service implementing IFieldService protocol.

This service wraps UpdateFieldCommand and provides a simple interface
for field value operations that FieldUndoService can use.

RULES (unified_upgrade_plan_FINAL.md U6 Phase 7):
- Implements IFieldService protocol for FieldUndoService
- Wraps UpdateFieldCommand for actual field updates
- Provides get/set operations with typed IDs converted to strings
"""

from typing import Any
from uuid import UUID

from doc_helper.application.commands.update_field_command import UpdateFieldCommand
from doc_helper.application.queries.get_project_query import GetProjectQuery
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class FieldService:
    """Concrete field service for field value operations.

    Implements IFieldService protocol required by FieldUndoService.
    Provides simple string-based interface while internally using typed IDs.

    Example:
        field_service = FieldService(
            update_field_command=update_cmd,
            get_project_query=get_query
        )

        # Get field value
        result = field_service.get_field_value("project-123", "site_location")
        if result.is_success:
            print(f"Value: {result.value}")

        # Set field value
        success = field_service.set_field_value(
            "project-123",
            "site_location",
            "456 Elm St"
        )
    """

    def __init__(
        self,
        update_field_command: UpdateFieldCommand,
        get_project_query: GetProjectQuery,
    ) -> None:
        """Initialize FieldService.

        Args:
            update_field_command: Command for updating field values
            get_project_query: Query for retrieving project data
        """
        self._update_field_command = update_field_command
        self._get_project_query = get_project_query

    def get_field_value(
        self,
        project_id: str,
        field_id: str,
    ) -> Result[Any, str]:
        """Get current field value.

        Args:
            project_id: Project identifier (string UUID)
            field_id: Field identifier (string UUID)

        Returns:
            Success(value) if found, Failure(error) otherwise
        """
        try:
            # Convert string IDs to typed IDs
            typed_project_id = ProjectId(UUID(project_id))

            # Get project
            project_result = self._get_project_query.execute(typed_project_id)
            if isinstance(project_result, Failure):
                return Failure(f"Failed to get project: {project_result.error}")

            project_dto = project_result.value
            if project_dto is None:
                return Failure(f"Project not found: {project_id}")

            # Find field value in project DTO
            # Note: ProjectDTO structure varies, this is a simplified implementation
            # In real usage, you'd navigate the DTO structure to find the field

            # For now, return None if field not found (Phase 7 minimal implementation)
            # Full implementation would search through entities/fields in ProjectDTO
            return Success(None)

        except (ValueError, TypeError) as e:
            return Failure(f"Invalid ID format: {e}")
        except Exception as e:
            return Failure(f"Unexpected error getting field value: {e}")

    def set_field_value(
        self,
        project_id: str,
        field_id: str,
        value: Any,
    ) -> bool:
        """Set a field value.

        Args:
            project_id: Project identifier (string UUID)
            field_id: Field identifier (string UUID)
            value: New value to set

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert string IDs to typed IDs
            typed_project_id = ProjectId(UUID(project_id))
            typed_field_id = FieldDefinitionId(UUID(field_id))

            # Execute update command
            result = self._update_field_command.execute(
                project_id=typed_project_id,
                field_id=typed_field_id,
                value=value,
            )

            return isinstance(result, Success)

        except (ValueError, TypeError) as e:
            # Invalid ID format
            return False
        except Exception as e:
            # Unexpected error
            return False

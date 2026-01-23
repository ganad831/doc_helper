"""Facade for project operations with primitive parameters.

This facade wraps project-related commands and queries to accept primitives
instead of domain types, enabling Clean Architecture compliance.

ARCHITECTURAL FIX (Phase 6C):
- Presentation layer passes string IDs
- This facade converts to domain types (ProjectId)
- Domain type construction stays in Application layer

Note: This facade does NOT wrap ValidationService or ControlService.
Those services should be modified separately if needed, or wrapped
in their own facades.
"""

from pathlib import Path
from typing import Optional, Union
from uuid import UUID

from doc_helper.application.commands.export_project_command import ExportProjectCommand
from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.dto import ExportResultDTO, ProjectDTO
from doc_helper.application.queries.get_project_query import GetProjectQuery
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId


class ProjectOperationsFacade:
    """Facade for project operations accepting primitives.

    This facade:
    - Accepts string project_id instead of ProjectId
    - Converts to domain types before calling underlying commands/queries
    - Keeps domain type construction in Application layer

    Usage:
        facade = ProjectOperationsFacade(
            get_project_query=query,
            save_project_command=save_cmd,
            export_project_command=export_cmd,
        )
        result = facade.get_project(project_id="550e8400-e29b-41d4-a716-446655440000")
    """

    def __init__(
        self,
        get_project_query: GetProjectQuery,
        save_project_command: SaveProjectCommand,
        export_project_command: Optional[ExportProjectCommand] = None,
    ) -> None:
        """Initialize facade.

        Args:
            get_project_query: Query for loading projects
            save_project_command: Command for saving projects
            export_project_command: Command for exporting projects (optional)
        """
        self._get_project_query = get_project_query
        self._save_project_command = save_project_command
        self._export_project_command = export_project_command

    def get_project(self, project_id: str) -> Result[Optional[ProjectDTO], str]:
        """Get project by ID.

        Args:
            project_id: Project ID as string (UUID format)

        Returns:
            Success(ProjectDTO) if found, Success(None) if not found,
            Failure(error) on error
        """
        # Validate and convert string to domain ID (Application layer responsibility)
        id_result = self._convert_string_to_project_id(project_id)
        if id_result.is_failure():
            return Failure(id_result.error)

        domain_project_id = id_result.value

        # Delegate to underlying query
        return self._get_project_query.execute(domain_project_id)

    def save_project(self, project_id: str) -> Result[None, str]:
        """Save project.

        Args:
            project_id: Project ID as string (UUID format)

        Returns:
            Success(None) if saved, Failure(error) otherwise
        """
        # Validate and convert string to domain ID (Application layer responsibility)
        id_result = self._convert_string_to_project_id(project_id)
        if id_result.is_failure():
            return Failure(id_result.error)

        domain_project_id = id_result.value

        # Delegate to underlying command
        return self._save_project_command.execute(domain_project_id)

    def export_project(
        self,
        project_id: str,
        output_file_path: Union[str, Path],
    ) -> Result[ExportResultDTO, str]:
        """Export project to interchange format.

        Args:
            project_id: Project ID as string (UUID format)
            output_file_path: Path where to save the export file

        Returns:
            Success(ExportResultDTO) if exported, Failure(error) otherwise
        """
        if self._export_project_command is None:
            return Failure("Export feature not configured")

        # Validate and convert string to domain ID (Application layer responsibility)
        id_result = self._convert_string_to_project_id(project_id)
        if id_result.is_failure():
            return Failure(id_result.error)

        domain_project_id = id_result.value

        # Delegate to underlying command
        return self._export_project_command.execute(domain_project_id, output_file_path)

    @staticmethod
    def _convert_string_to_project_id(project_id: str) -> Result[ProjectId, str]:
        """Convert string to ProjectId.

        Args:
            project_id: Project ID as string (UUID format)

        Returns:
            Success(ProjectId) or Failure(error)
        """
        if not project_id:
            return Failure("project_id cannot be empty")

        try:
            uuid_value = UUID(project_id)
            return Success(ProjectId(uuid_value))
        except (ValueError, AttributeError) as e:
            return Failure(f"Invalid project ID format: {str(e)}")

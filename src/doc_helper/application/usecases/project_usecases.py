"""Project Use Cases (Architecture Enforcement Phase).

Application layer use-case class that encapsulates ALL project operations.

RULE 0 ENFORCEMENT:
- Presentation ONLY calls use-case methods
- All domain type construction happens HERE
- All command/query orchestration happens HERE
- Returns primitives/DTOs to Presentation (no domain types)

This class wraps:
- GetProjectQuery (load project)
- SaveProjectCommand (save project)
- ExportProjectCommand (export project)
- ImportProjectCommand (import project from file)
- SearchFieldsQuery (search fields in project)
- GetFieldHistoryQuery (get field history)
"""

from pathlib import Path
from typing import Optional, Union
from uuid import UUID

from doc_helper.application.commands.export_project_command import ExportProjectCommand
from doc_helper.application.commands.import_project_command import ImportProjectCommand
from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.dto import (
    ExportResultDTO,
    FieldHistoryResultDTO,
    ImportResultDTO,
    ProjectDTO,
    SearchResultDTO,
)
from doc_helper.application.queries.get_field_history_query import (
    GetFieldHistoryQuery,
)
from doc_helper.application.queries.get_project_query import GetProjectQuery
from doc_helper.application.queries.search_fields_query import SearchFieldsQuery
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId


class ProjectUseCases:
    """Use-case class for ALL project operations.

    This class provides a clean boundary between Presentation and Application layers.

    RULE 0 COMPLIANCE:
        - Presentation receives ONLY this use-case class via DI
        - NO commands, queries, or repositories are exposed
        - All domain type construction happens internally

    Usage in ViewModel:
        # ViewModel __init__ receives ProjectUseCases via DI
        def __init__(self, project_usecases: ProjectUseCases, ...):
            self._project_usecases = project_usecases

        # ViewModel calls use-case methods with primitives
        def load_project(self, project_id: str):
            return self._project_usecases.get_project(project_id)
    """

    def __init__(
        self,
        get_project_query: Optional[GetProjectQuery] = None,
        save_project_command: Optional[SaveProjectCommand] = None,
        export_project_command: Optional[ExportProjectCommand] = None,
        import_project_command: Optional[ImportProjectCommand] = None,
        search_fields_query: Optional[SearchFieldsQuery] = None,
        get_field_history_query: Optional[GetFieldHistoryQuery] = None,
    ) -> None:
        """Initialize ProjectUseCases.

        Args:
            get_project_query: Query for loading projects (optional)
            save_project_command: Command for saving projects (optional)
            export_project_command: Command for exporting projects (optional)
            import_project_command: Command for importing projects (optional)
            search_fields_query: Query for searching fields (optional)
            get_field_history_query: Query for field history (optional)

        Note:
            All dependencies are optional to support feature flags.
        """
        self._get_project_query = get_project_query
        self._save_project_command = save_project_command
        self._export_project_command = export_project_command
        self._import_project_command = import_project_command
        self._search_fields_query = search_fields_query
        self._get_field_history_query = get_field_history_query

    # =========================================================================
    # Core Project Operations (formerly in ProjectOperationsFacade)
    # =========================================================================

    def get_project(self, project_id: str) -> Result[Optional[ProjectDTO], str]:
        """Get project by ID.

        Args:
            project_id: Project ID as string (UUID format)

        Returns:
            Success(ProjectDTO) if found, Success(None) if not found,
            Failure(error) on error
        """
        if not self._get_project_query:
            return Failure("Get project feature not available")

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
        if not self._save_project_command:
            return Failure("Save project feature not available")

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
        if not self._export_project_command:
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

    # =========================================================================
    # Import/Search/History Operations
    # =========================================================================

    def import_project(self, file_path: str) -> ImportResultDTO:
        """Import project from file.

        Args:
            file_path: Path to import file

        Returns:
            ImportResultDTO with success/failure information
        """
        if not self._import_project_command:
            return ImportResultDTO(
                success=False,
                project_id="",
                project_name="",
                error_message="Import feature not available.",
                format_version="",
                imported_at="",
                entity_count=0,
                record_count=0,
                field_value_count=0,
                validation_warnings=[],
            )

        result = self._import_project_command.execute(file_path)

        if result.is_success():
            return result.value
        else:
            return ImportResultDTO(
                success=False,
                project_id="",
                project_name="",
                error_message=result.error,
                format_version="",
                imported_at="",
                entity_count=0,
                record_count=0,
                field_value_count=0,
                validation_warnings=[],
            )

    def search_fields(
        self,
        project_id: str,
        search_term: str,
        limit: int = 100,
    ) -> list[SearchResultDTO]:
        """Search for fields in a project.

        Args:
            project_id: Project ID
            search_term: Search term (minimum 2 characters)
            limit: Maximum results to return

        Returns:
            List of SearchResultDTO (empty if not available or no matches)
        """
        if not self._search_fields_query:
            return []

        if not search_term or len(search_term.strip()) < 2:
            return []

        result = self._search_fields_query.execute(
            project_id=project_id,
            search_term=search_term.strip(),
            limit=limit,
        )

        if result.is_success():
            return result.value
        else:
            return []

    def get_field_history(
        self,
        project_id: str,
        field_id: str,
        limit: Optional[int] = 20,
        offset: int = 0,
    ) -> Optional[FieldHistoryResultDTO]:
        """Get history for a specific field.

        Args:
            project_id: Project ID
            field_id: Field ID
            limit: Maximum entries to return
            offset: Pagination offset

        Returns:
            FieldHistoryResultDTO or None if not available
        """
        if not self._get_field_history_query:
            return None

        result = self._get_field_history_query.execute_for_field(
            project_id=project_id,
            field_id=field_id,
            limit=limit,
            offset=offset,
        )

        if result.is_success():
            return result.value
        else:
            return None

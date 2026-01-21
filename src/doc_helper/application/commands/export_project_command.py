"""Command for exporting a project to interchange format.

ADR-039: Import/Export Data Format
RULES (AGENT_RULES.md Section 5):
- Commands take IDs and primitive data, NOT domain objects
- Domain objects are loaded internally and never cross boundaries
- Commands return Result[DTO, str] for operations that produce output

Export Workflow:
1. Load project from repository
2. Load schema from schema repository
3. Delegate serialization to infrastructure ProjectExporter
4. Return ExportResultDTO with file path and metadata
"""

from pathlib import Path
from datetime import datetime, timezone

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.application.dto import ExportResultDTO


class ExportProjectCommand:
    """Command to export a project to interchange format.

    ADR-039: Export serializes complete project (schema + data) to JSON.
    Export is project-scoped (one project per export file).
    Export never modifies the project (read-only operation).

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands return Result[DTO, str]
    - Commands take IDs, not domain objects

    Example:
        command = ExportProjectCommand(
            project_repository=repo,
            schema_repository=schema_repo,
            project_exporter=exporter
        )
        result = command.execute(
            project_id=project_id,
            output_file_path="/path/to/export.json"
        )
        if isinstance(result, Success):
            export_dto = result.value
            print(f"Exported to: {export_dto.file_path}")
    """

    def __init__(
        self,
        project_repository: IProjectRepository,
        schema_repository: ISchemaRepository,
        project_exporter: "IProjectExporter",  # Forward reference - to be defined
    ) -> None:
        """Initialize command.

        Args:
            project_repository: Repository for loading projects
            schema_repository: Repository for loading schema
            project_exporter: Infrastructure service for JSON serialization
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        # Note: project_exporter interface to be defined in infrastructure layer
        self._project_repository = project_repository
        self._schema_repository = schema_repository
        self._project_exporter = project_exporter

    def execute(
        self,
        project_id: ProjectId,
        output_file_path: str | Path,
    ) -> Result[ExportResultDTO, str]:
        """Execute export project command.

        ADR-039: Export workflow:
        1. Validate inputs
        2. Load project from repository
        3. Load schema from repository
        4. Delegate JSON serialization to infrastructure
        5. Return ExportResultDTO with success/failure status

        Args:
            project_id: ID of project to export
            output_file_path: Absolute path where export file should be written

        Returns:
            Success(ExportResultDTO) if exported, Failure(error) otherwise
        """
        # Validate inputs
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        if not output_file_path:
            return Failure("output_file_path must not be empty")

        output_path = Path(output_file_path) if isinstance(output_file_path, str) else output_file_path

        # Ensure parent directory exists
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return Failure(f"Failed to create output directory: {str(e)}")

        # Load project
        load_result = self._project_repository.get_by_id(project_id)
        if isinstance(load_result, Failure):
            return Failure(f"Failed to load project: {load_result.error}")

        project = load_result.value
        if project is None:
            return Failure(f"Project not found: {project_id.value}")

        # Load schema (all entity definitions)
        schema_result = self._schema_repository.get_all()
        if isinstance(schema_result, Failure):
            return Failure(f"Failed to load schema: {schema_result.error}")

        entity_definitions = schema_result.value
        if not entity_definitions:
            return Failure("Schema not found")

        # Delegate serialization to infrastructure
        export_result = self._project_exporter.export_to_file(
            project=project,
            entity_definitions=entity_definitions,
            output_path=output_path,
        )

        if isinstance(export_result, Failure):
            return Failure(f"Failed to export project: {export_result.error}")

        # Return ExportResultDTO
        export_info = export_result.value
        return Success(
            ExportResultDTO(
                success=True,
                file_path=str(output_path.absolute()),
                project_id=str(project_id.value),
                project_name=project.name,
                error_message=None,
                format_version=export_info.get("format_version", "1.0"),
                exported_at=datetime.now(timezone.utc).isoformat(),
                entity_count=export_info.get("entity_count", 0),
                record_count=export_info.get("record_count", 0),
                field_value_count=export_info.get("field_value_count", 0),
            )
        )

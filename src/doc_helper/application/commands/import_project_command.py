"""Command for importing a project from interchange format.

ADR-039: Import/Export Data Format
RULES (AGENT_RULES.md Section 5):
- Commands take IDs and primitive data, NOT domain objects
- Domain objects are loaded internally and never cross boundaries
- Commands return Result[DTO, str] for operations that produce output

Import Workflow:
1. Load and parse JSON file from input path
2. Validate interchange format structure
3. Validate data against schema (same validation as manual entry)
4. Create new project with imported data
5. Save project to repository
6. Return ImportResultDTO with project_id or validation errors
"""

from pathlib import Path
from datetime import datetime, timezone

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.application.dto import ImportResultDTO, ImportValidationErrorDTO
from doc_helper.application.services.validation_service import ValidationService


class ImportProjectCommand:
    """Command to import a project from interchange format.

    ADR-039: Import creates NEW project (never modifies existing).
    Import is atomic (all-or-nothing): validation failures prevent project creation.
    Import uses same domain validation as manual field entry.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands return Result[DTO, str]
    - Commands take primitive types, not domain objects

    Example:
        command = ImportProjectCommand(
            project_repository=repo,
            schema_repository=schema_repo,
            project_importer=importer,
            validation_service=validation_svc
        )
        result = command.execute(
            input_file_path="/path/to/import.json"
        )
        if isinstance(result, Success):
            import_dto = result.value
            if import_dto.success:
                print(f"Imported project: {import_dto.project_id}")
            else:
                print(f"Import failed: {import_dto.error_message}")
                for error in import_dto.validation_errors:
                    print(f"  - {error.field_path}: {error.error_message}")
    """

    def __init__(
        self,
        project_repository: IProjectRepository,
        schema_repository: ISchemaRepository,
        project_importer: "IProjectImporter",  # Forward reference - to be defined
        validation_service: ValidationService,
    ) -> None:
        """Initialize command.

        Args:
            project_repository: Repository for saving projects
            schema_repository: Repository for loading schema
            project_importer: Infrastructure service for JSON deserialization
            validation_service: Service for validating imported data
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        if not isinstance(validation_service, ValidationService):
            raise TypeError("validation_service must be a ValidationService instance")
        # Note: project_importer interface to be defined in infrastructure layer
        self._project_repository = project_repository
        self._schema_repository = schema_repository
        self._project_importer = project_importer
        self._validation_service = validation_service

    def execute(
        self,
        input_file_path: str | Path,
    ) -> Result[ImportResultDTO, str]:
        """Execute import project command.

        ADR-039: Import workflow:
        1. Validate input file exists and is readable
        2. Load schema from repository
        3. Delegate JSON parsing to infrastructure
        4. Validate imported data using domain validation
        5. If validation passes: create and save project
        6. If validation fails: return errors without creating project
        7. Return ImportResultDTO with success/failure status

        Args:
            input_file_path: Absolute path to interchange format JSON file

        Returns:
            Success(ImportResultDTO) always (even if import fails - DTO contains status)
            Failure(error) only for unexpected infrastructure errors
        """
        # Validate input file path
        if not input_file_path:
            return Success(
                ImportResultDTO(
                    success=False,
                    project_id=None,
                    project_name=None,
                    error_message="input_file_path must not be empty",
                    validation_errors=(),
                    format_version="unknown",
                    source_app_version=None,
                    warnings=(),
                )
            )

        input_path = Path(input_file_path) if isinstance(input_file_path, str) else input_file_path

        # Check file exists
        if not input_path.exists():
            return Success(
                ImportResultDTO(
                    success=False,
                    project_id=None,
                    project_name=None,
                    error_message=f"Import file not found: {input_path}",
                    validation_errors=(),
                    format_version="unknown",
                    source_app_version=None,
                    warnings=(),
                )
            )

        # Load schema (all entity definitions)
        schema_result = self._schema_repository.get_all()
        if isinstance(schema_result, Failure):
            return Success(
                ImportResultDTO(
                    success=False,
                    project_id=None,
                    project_name=None,
                    error_message=f"Failed to load schema: {schema_result.error}",
                    validation_errors=(),
                    format_version="unknown",
                    source_app_version=None,
                    warnings=(),
                )
            )

        entity_definitions = schema_result.value
        if not entity_definitions:
            return Success(
                ImportResultDTO(
                    success=False,
                    project_id=None,
                    project_name=None,
                    error_message="Schema not found",
                    validation_errors=(),
                    format_version="unknown",
                    source_app_version=None,
                    warnings=(),
                )
            )

        # Delegate parsing and initial validation to infrastructure
        import_result = self._project_importer.import_from_file(
            input_path=input_path,
            entity_definitions=entity_definitions,
        )

        if isinstance(import_result, Failure):
            return Success(
                ImportResultDTO(
                    success=False,
                    project_id=None,
                    project_name=None,
                    error_message=f"Failed to parse import file: {import_result.error}",
                    validation_errors=(),
                    format_version="unknown",
                    source_app_version=None,
                    warnings=(),
                )
            )

        import_data = import_result.value

        # Extract metadata from import
        format_version = import_data.get("format_version", "unknown")
        source_app_version = import_data.get("source_app_version")
        project_name = import_data.get("project_name", "Imported Project")
        warnings = tuple(import_data.get("warnings", []))

        # Get project from import data
        project = import_data.get("project")
        if project is None:
            return Success(
                ImportResultDTO(
                    success=False,
                    project_id=None,
                    project_name=project_name,
                    error_message="Failed to create project from import data",
                    validation_errors=(),
                    format_version=format_version,
                    source_app_version=source_app_version,
                    warnings=warnings,
                )
            )

        # Validate imported project using domain validation
        validation_result = self._validation_service.validate_project(project)
        if isinstance(validation_result, Failure):
            return Success(
                ImportResultDTO(
                    success=False,
                    project_id=None,
                    project_name=project_name,
                    error_message=f"Validation service error: {validation_result.error}",
                    validation_errors=(),
                    format_version=format_version,
                    source_app_version=source_app_version,
                    warnings=warnings,
                )
            )

        validation_dto = validation_result.value

        # ADR-039: Import is atomic - validation failures prevent project creation
        if validation_dto.has_blocking_errors():
            # Convert validation errors to ImportValidationErrorDTO
            validation_errors = []
            for error in validation_dto.errors:
                validation_errors.append(
                    ImportValidationErrorDTO(
                        entity_id=error.entity_id or "unknown",
                        record_id=error.record_id,
                        field_id=error.field_id or "unknown",
                        error_message=error.message,
                        error_type=error.severity.name if hasattr(error, 'severity') else "ERROR",
                        field_path=f"{error.entity_id}.{error.field_id}" if error.entity_id and error.field_id else "unknown",
                    )
                )

            return Success(
                ImportResultDTO(
                    success=False,
                    project_id=None,
                    project_name=project_name,
                    error_message=f"Import validation failed: {len(validation_errors)} error(s) found",
                    validation_errors=tuple(validation_errors),
                    format_version=format_version,
                    source_app_version=source_app_version,
                    warnings=warnings,
                )
            )

        # Validation passed - save project to repository
        save_result = self._project_repository.save(project)
        if isinstance(save_result, Failure):
            return Success(
                ImportResultDTO(
                    success=False,
                    project_id=None,
                    project_name=project_name,
                    error_message=f"Failed to save imported project: {save_result.error}",
                    validation_errors=(),
                    format_version=format_version,
                    source_app_version=source_app_version,
                    warnings=warnings,
                )
            )

        # Success!
        return Success(
            ImportResultDTO(
                success=True,
                project_id=str(project.id.value),
                project_name=project.name,
                error_message=None,
                validation_errors=(),
                format_version=format_version,
                source_app_version=source_app_version,
                warnings=warnings,
            )
        )

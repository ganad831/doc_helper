"""Query for getting validation results for a project."""

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.validation.validation_result import ValidationResult
from doc_helper.application.services.validation_service import ValidationService


class GetValidationResultQuery:
    """Query to get validation results for a project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return data and don't modify state
    - Uses ValidationService to perform validation

    Example:
        query = GetValidationResultQuery(
            project_repository=project_repo,
            schema_repository=schema_repo,
            validation_service=validation_service
        )
        result = query.execute(project_id=project_id)
        if isinstance(result, Success):
            validation_result = result.value
            if validation_result.is_invalid():
                print(f"Found {validation_result.error_count} errors")
    """

    def __init__(
        self,
        project_repository: IProjectRepository,
        schema_repository: ISchemaRepository,
        validation_service: ValidationService,
    ) -> None:
        """Initialize query.

        Args:
            project_repository: Repository for loading projects
            schema_repository: Repository for loading schema definitions
            validation_service: Service for validating projects
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        if not isinstance(validation_service, ValidationService):
            raise TypeError("validation_service must be a ValidationService instance")

        self._project_repository = project_repository
        self._schema_repository = schema_repository
        self._validation_service = validation_service

    def execute(self, project_id: ProjectId) -> Result[ValidationResult, str]:
        """Execute get validation result query.

        Args:
            project_id: Project ID to validate

        Returns:
            Success(ValidationResult) if validation completed,
            Failure(error) if unable to validate
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        # Load project
        project_result = self._project_repository.get_by_id(project_id)
        if isinstance(project_result, Failure):
            return Failure(f"Failed to load project: {project_result.error}")

        project = project_result.value
        if project is None:
            return Failure(f"Project not found: {project_id.value}")

        # Load entity definition
        entity_result = self._schema_repository.get_by_id(
            project.entity_definition_id
        )
        if isinstance(entity_result, Failure):
            return Failure(f"Failed to load entity definition: {entity_result.error}")

        entity_definition = entity_result.value

        # Validate project
        validation_result = self._validation_service.validate_project(
            project=project,
            entity_definition=entity_definition,
        )

        return Success(validation_result)


class GetFieldValidationQuery:
    """Query to get validation result for a single field.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return data and don't modify state

    Example:
        query = GetFieldValidationQuery(
            schema_repository=schema_repo,
            validation_service=validation_service
        )
        result = query.execute(
            entity_id=EntityDefinitionId("project"),
            field_id=FieldDefinitionId("site_location"),
            value="123 Main St"
        )
        if isinstance(result, Success):
            validation_result = result.value
    """

    def __init__(
        self,
        schema_repository: ISchemaRepository,
        validation_service: ValidationService,
    ) -> None:
        """Initialize query.

        Args:
            schema_repository: Repository for loading schema definitions
            validation_service: Service for validating fields
        """
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        if not isinstance(validation_service, ValidationService):
            raise TypeError("validation_service must be a ValidationService instance")

        self._schema_repository = schema_repository
        self._validation_service = validation_service

    def execute(
        self,
        entity_id: EntityDefinitionId,
        field_id: str,  # Field ID as string
        value: any,
    ) -> Result[ValidationResult, str]:
        """Execute get field validation query.

        Args:
            entity_id: Entity definition ID
            field_id: Field ID to validate
            value: Field value to validate

        Returns:
            Success(ValidationResult) if validation completed,
            Failure(error) if unable to validate
        """
        from doc_helper.domain.schema.schema_ids import FieldDefinitionId

        if not isinstance(entity_id, EntityDefinitionId):
            return Failure("entity_id must be an EntityDefinitionId")
        if not isinstance(field_id, str):
            return Failure("field_id must be a string")

        # Load entity definition
        entity_result = self._schema_repository.get_by_id(entity_id)
        if isinstance(entity_result, Failure):
            return Failure(f"Failed to load entity definition: {entity_result.error}")

        entity_definition = entity_result.value

        # Get field definition
        field_def_id = FieldDefinitionId(field_id)
        field_def = entity_definition.fields.get(field_def_id)
        if field_def is None:
            return Failure(f"Field not found: {field_id}")

        # Validate field
        validation_result = self._validation_service.validate_field(
            field_path=field_id,
            value=value,
            field_definition=field_def,
        )

        return Success(validation_result)

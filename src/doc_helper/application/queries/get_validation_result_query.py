"""Query for getting validation results for a project.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- Queries return DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary
- Use mappers to convert Domain → DTO
"""

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.common.translation import ITranslationService
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.application.dto import ValidationResultDTO
from doc_helper.application.mappers import ValidationMapper
from doc_helper.application.services.validation_service import ValidationService


class GetValidationResultQuery:
    """Query to get validation results for a project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return DTOs, not domain objects
    - Uses ValidationService to perform validation

    Example:
        query = GetValidationResultQuery(
            project_repository=project_repo,
            schema_repository=schema_repo,
            validation_service=validation_service,
            translation_service=ts
        )
        result = query.execute(project_id=project_id)
        if isinstance(result, Success):
            validation_dto = result.value  # Returns ValidationResultDTO
            if not validation_dto.is_valid:
                print(f"Found {len(validation_dto.errors)} errors")
    """

    def __init__(
        self,
        project_repository: IProjectRepository,
        schema_repository: ISchemaRepository,
        validation_service: ValidationService,
        translation_service: ITranslationService,
    ) -> None:
        """Initialize query.

        Args:
            project_repository: Repository for loading projects
            schema_repository: Repository for loading schema definitions
            validation_service: Service for validating projects
            translation_service: Service for translating i18n keys
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
        self._validation_mapper = ValidationMapper(translation_service)

    def execute(self, project_id: ProjectId) -> Result[ValidationResultDTO, str]:
        """Execute get validation result query.

        Args:
            project_id: Project ID to validate

        Returns:
            Success(ValidationResultDTO) if validation completed,
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

        # Map to DTO before returning
        return Success(self._validation_mapper.to_dto(validation_result))


class GetFieldValidationQuery:
    """Query to get validation result for a single field.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return DTOs, not domain objects

    Example:
        query = GetFieldValidationQuery(
            schema_repository=schema_repo,
            validation_service=validation_service,
            translation_service=ts
        )
        result = query.execute(
            entity_id=EntityDefinitionId("project"),
            field_id="site_location",
            value="123 Main St"
        )
        if isinstance(result, Success):
            validation_dto = result.value  # Returns ValidationResultDTO
    """

    def __init__(
        self,
        schema_repository: ISchemaRepository,
        validation_service: ValidationService,
        translation_service: ITranslationService,
    ) -> None:
        """Initialize query.

        Args:
            schema_repository: Repository for loading schema definitions
            validation_service: Service for validating fields
            translation_service: Service for translating i18n keys
        """
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        if not isinstance(validation_service, ValidationService):
            raise TypeError("validation_service must be a ValidationService instance")

        self._schema_repository = schema_repository
        self._validation_service = validation_service
        self._validation_mapper = ValidationMapper(translation_service)

    def execute(
        self,
        entity_id: EntityDefinitionId,
        field_id: str,  # Field ID as string
        value: any,
    ) -> Result[ValidationResultDTO, str]:
        """Execute get field validation query.

        Args:
            entity_id: Entity definition ID
            field_id: Field ID to validate
            value: Field value to validate

        Returns:
            Success(ValidationResultDTO) if validation completed,
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

        # Map to DTO before returning (with field_id for context)
        return Success(self._validation_mapper.to_dto(validation_result, field_id))

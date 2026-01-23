"""Validation service for coordinating field validation.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md):
- Services can work with domain objects internally
- Methods called from presentation should take IDs and return Results
"""

from typing import Any, Optional
from uuid import UUID

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.validation.validation_result import ValidationResult
from doc_helper.domain.validation.validators import get_validator_for_field_type


class ValidationService:
    """Service for validating project field values.

    Coordinates validation across multiple fields in a project,
    applying constraints from field definitions.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Service is stateless (no instance state)
    - Service coordinates domain logic, doesn't contain it
    - Returns ValidationResult (immutable value object)

    Example:
        service = ValidationService(project_repo, schema_repo)
        result = service.validate_by_project_id(project_id)
        if isinstance(result, Success) and result.value.is_invalid():
            for error in result.value.errors:
                print(error.message_key)
    """

    def __init__(
        self,
        project_repository: Optional[IProjectRepository] = None,
        schema_repository: Optional[ISchemaRepository] = None,
    ) -> None:
        """Initialize validation service.

        Args:
            project_repository: Repository for loading projects (optional for backward compat)
            schema_repository: Repository for loading schemas (optional for backward compat)
        """
        self._project_repository = project_repository
        self._schema_repository = schema_repository

    def validate_by_project_id(
        self,
        project_id: ProjectId,
    ) -> Result[ValidationResult, str]:
        """Validate a project by its ID.

        This method loads the project and entity definition internally,
        suitable for calling from presentation layer.

        Args:
            project_id: ID of project to validate

        Returns:
            Success(ValidationResult) if validation completes, Failure(error) otherwise
        """
        if not self._project_repository:
            return Failure("ValidationService requires project_repository for validate_by_project_id")
        if not self._schema_repository:
            return Failure("ValidationService requires schema_repository for validate_by_project_id")
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
        entity_def_result = self._schema_repository.get_entity_definition(
            project.entity_definition_id
        )
        if isinstance(entity_def_result, Failure):
            return Failure(f"Failed to load entity definition: {entity_def_result.error}")

        entity_definition = entity_def_result.value
        if entity_definition is None:
            return Failure(f"Entity definition not found: {project.entity_definition_id.value}")

        # Validate
        result = self.validate_project(project, entity_definition)
        return Success(result)

    def validate_by_project_id_str(
        self,
        project_id: str,
    ) -> Result[ValidationResult, str]:
        """Validate a project by its string ID.

        PHASE 6C: String-accepting variant for Presentation layer.
        Converts string to domain ID internally.

        Args:
            project_id: Project ID as string (UUID format)

        Returns:
            Success(ValidationResult) if validation completes, Failure(error) otherwise
        """
        if not project_id:
            return Failure("project_id cannot be empty")

        try:
            domain_project_id = ProjectId(UUID(project_id))
        except (ValueError, AttributeError) as e:
            return Failure(f"Invalid project ID format: {str(e)}")

        return self.validate_by_project_id(domain_project_id)

    def validate_project(
        self,
        project: Project,
        entity_definition: EntityDefinition,
    ) -> ValidationResult:
        """Validate all fields in a project.

        Args:
            project: Project to validate
            entity_definition: Entity definition with field constraints

        Returns:
            ValidationResult with all validation errors
        """
        if not isinstance(project, Project):
            raise TypeError("project must be a Project instance")
        if not isinstance(entity_definition, EntityDefinition):
            raise TypeError("entity_definition must be an EntityDefinition")

        all_errors = []

        # Validate each field value
        for field_id, field_value in project.field_values.items():
            # Get field definition
            field_def = entity_definition.fields.get(field_id)
            if field_def is None:
                # Skip fields not in definition (orphaned fields)
                continue

            # Validate field
            result = self.validate_field(
                field_path=field_id.value,
                value=field_value.value,
                field_definition=field_def,
            )

            # Collect errors
            if result.is_invalid():
                all_errors.extend(result.errors)

        if all_errors:
            return ValidationResult.failure(tuple(all_errors))
        return ValidationResult.success()

    def validate_field(
        self,
        field_path: str,
        value: Any,
        field_definition: FieldDefinition,
    ) -> ValidationResult:
        """Validate a single field value.

        Args:
            field_path: Dot-notation path to field (for error reporting)
            value: Field value to validate
            field_definition: Field definition with constraints

        Returns:
            ValidationResult for the field
        """
        if not isinstance(field_path, str):
            raise TypeError("field_path must be a string")
        if not isinstance(field_definition, FieldDefinition):
            raise TypeError("field_definition must be a FieldDefinition")

        # Get validator for field type
        validator = get_validator_for_field_type(
            field_type=field_definition.field_type,
            constraints=field_definition.constraints,
        )

        # Validate field
        return validator.validate(field_path=field_path, value=value)

    def validate_fields(
        self,
        field_values: dict[FieldDefinitionId, Any],
        entity_definition: EntityDefinition,
    ) -> ValidationResult:
        """Validate multiple field values.

        Args:
            field_values: Dictionary of field_id -> value
            entity_definition: Entity definition with field constraints

        Returns:
            ValidationResult with all validation errors
        """
        if not isinstance(field_values, dict):
            raise TypeError("field_values must be a dictionary")
        if not isinstance(entity_definition, EntityDefinition):
            raise TypeError("entity_definition must be an EntityDefinition")

        all_errors = []

        for field_id, value in field_values.items():
            # Get field definition
            field_def = entity_definition.fields.get(field_id)
            if field_def is None:
                continue

            # Validate field
            result = self.validate_field(
                field_path=field_id.value,
                value=value,
                field_definition=field_def,
            )

            # Collect errors
            if result.is_invalid():
                all_errors.extend(result.errors)

        if all_errors:
            return ValidationResult.failure(tuple(all_errors))
        return ValidationResult.success()

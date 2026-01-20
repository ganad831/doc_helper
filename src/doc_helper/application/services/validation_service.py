"""Validation service for coordinating field validation."""

from typing import Any

from doc_helper.domain.project.project import Project
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.schema_ids import FieldDefinitionId
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
        service = ValidationService()
        result = service.validate_project(
            project=project,
            entity_definition=entity_definition
        )
        if result.is_invalid():
            for error in result.errors:
                print(error.message_key)
    """

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

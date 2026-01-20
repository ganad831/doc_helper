"""Unit tests for ValidationService."""

from uuid import uuid4

import pytest

from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.validation.constraints import RequiredConstraint, MinLengthConstraint
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.domain.common.i18n import TranslationKey


class TestValidationService:
    """Tests for ValidationService."""

    @pytest.fixture
    def service(self) -> ValidationService:
        """Create validation service instance."""
        return ValidationService()

    @pytest.fixture
    def entity_definition(self) -> EntityDefinition:
        """Create sample entity definition with constraints."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("field1"): FieldDefinition(
                    id=FieldDefinitionId("field1"),
                    label_key=TranslationKey("fields.field1"),
                    field_type=FieldType.TEXT,
                    constraints=(RequiredConstraint(),),
                ),
                FieldDefinitionId("field2"): FieldDefinition(
                    id=FieldDefinitionId("field2"),
                    label_key=TranslationKey("fields.field2"),
                    field_type=FieldType.TEXT,
                    constraints=(MinLengthConstraint(min_length=5),),
                ),
            },
        )

    @pytest.fixture
    def valid_project(self, entity_definition: EntityDefinition) -> Project:
        """Create valid project."""
        return Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_definition.id,
            field_values={
                FieldDefinitionId("field1"): FieldValue(
                    field_id=FieldDefinitionId("field1"),
                    value="Value 1",
                ),
                FieldDefinitionId("field2"): FieldValue(
                    field_id=FieldDefinitionId("field2"),
                    value="Value 2",
                ),
            },
        )

    def test_validate_project_success(
        self,
        service: ValidationService,
        valid_project: Project,
        entity_definition: EntityDefinition,
    ) -> None:
        """validate_project should return success for valid project."""
        result = service.validate_project(valid_project, entity_definition)

        assert result.is_valid()
        assert result.error_count == 0

    def test_validate_project_with_errors(
        self,
        service: ValidationService,
        entity_definition: EntityDefinition,
    ) -> None:
        """validate_project should return errors for invalid project."""
        # Create project with invalid field values
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_definition.id,
            field_values={
                FieldDefinitionId("field1"): FieldValue(
                    field_id=FieldDefinitionId("field1"),
                    value=None,  # Required but None
                ),
                FieldDefinitionId("field2"): FieldValue(
                    field_id=FieldDefinitionId("field2"),
                    value="Val",  # Too short (min length 5)
                ),
            },
        )

        result = service.validate_project(project, entity_definition)

        assert result.is_invalid()
        assert result.error_count == 2  # field1 required, field2 too short

    def test_validate_project_requires_project(
        self, service: ValidationService, entity_definition: EntityDefinition
    ) -> None:
        """validate_project should require Project instance."""
        with pytest.raises(TypeError):
            service.validate_project("not a project", entity_definition)  # type: ignore

    def test_validate_project_requires_entity_definition(
        self, service: ValidationService, valid_project: Project
    ) -> None:
        """validate_project should require EntityDefinition instance."""
        with pytest.raises(TypeError):
            service.validate_project(valid_project, "not an entity")  # type: ignore

    def test_validate_field_success(
        self, service: ValidationService, entity_definition: EntityDefinition
    ) -> None:
        """validate_field should return success for valid field."""
        field_def = entity_definition.fields[FieldDefinitionId("field1")]

        result = service.validate_field(
            field_path="field1",
            value="Valid value",
            field_definition=field_def,
        )

        assert result.is_valid()

    def test_validate_field_with_error(
        self, service: ValidationService, entity_definition: EntityDefinition
    ) -> None:
        """validate_field should return errors for invalid field."""
        field_def = entity_definition.fields[FieldDefinitionId("field1")]

        result = service.validate_field(
            field_path="field1",
            value=None,  # Required but None
            field_definition=field_def,
        )

        assert result.is_invalid()
        assert result.error_count == 1

    def test_validate_fields_success(
        self, service: ValidationService, entity_definition: EntityDefinition
    ) -> None:
        """validate_fields should return success for valid fields."""
        field_values = {
            FieldDefinitionId("field1"): "Value 1",
            FieldDefinitionId("field2"): "Value 2 Long",
        }

        result = service.validate_fields(field_values, entity_definition)

        assert result.is_valid()

    def test_validate_fields_with_errors(
        self, service: ValidationService, entity_definition: EntityDefinition
    ) -> None:
        """validate_fields should return errors for invalid fields."""
        field_values = {
            FieldDefinitionId("field1"): None,  # Required
            FieldDefinitionId("field2"): "Val",  # Too short
        }

        result = service.validate_fields(field_values, entity_definition)

        assert result.is_invalid()
        assert result.error_count == 2

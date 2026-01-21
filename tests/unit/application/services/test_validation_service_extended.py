"""Extended unit tests for ValidationService to improve coverage.

This file contains additional tests for validation_service.py to reach 85%+ coverage.
Tests focus on uncovered branches and error paths.
"""

from uuid import uuid4
from unittest.mock import Mock

import pytest

from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.domain.common.i18n import TranslationKey


class TestValidationServiceValidateByProjectId:
    """Tests for ValidationService.validate_by_project_id method."""

    def test_missing_project_repository(self) -> None:
        """validate_by_project_id should fail when project_repository is None."""
        service = ValidationService(project_repository=None, schema_repository=None)
        result = service.validate_by_project_id(ProjectId(uuid4()))

        assert isinstance(result, Failure)
        assert "requires project_repository" in result.error

    def test_missing_schema_repository(self) -> None:
        """validate_by_project_id should fail when schema_repository is None."""
        mock_repo = Mock()
        service = ValidationService(project_repository=mock_repo, schema_repository=None)
        result = service.validate_by_project_id(ProjectId(uuid4()))

        assert isinstance(result, Failure)
        assert "requires schema_repository" in result.error

    def test_invalid_project_id_type(self) -> None:
        """validate_by_project_id should fail when project_id is not ProjectId."""
        mock_project_repo = Mock()
        mock_schema_repo = Mock()
        service = ValidationService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )

        result = service.validate_by_project_id("not_a_project_id")  # type: ignore

        assert isinstance(result, Failure)
        assert "project_id must be a ProjectId" in result.error

    def test_project_load_failure(self) -> None:
        """validate_by_project_id should fail when project loading fails."""
        mock_project_repo = Mock()
        mock_project_repo.get_by_id.return_value = Failure("Database error")
        mock_schema_repo = Mock()

        service = ValidationService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )
        result = service.validate_by_project_id(ProjectId(uuid4()))

        assert isinstance(result, Failure)
        assert "Failed to load project" in result.error

    def test_project_not_found(self) -> None:
        """validate_by_project_id should fail when project is not found."""
        mock_project_repo = Mock()
        mock_project_repo.get_by_id.return_value = Success(None)
        mock_schema_repo = Mock()

        service = ValidationService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )
        project_id = ProjectId(uuid4())
        result = service.validate_by_project_id(project_id)

        assert isinstance(result, Failure)
        assert "Project not found" in result.error

    def test_entity_definition_load_failure(self) -> None:
        """validate_by_project_id should fail when entity definition loading fails."""
        entity_def_id = EntityDefinitionId("test_entity")
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def_id,
            field_values={},
        )

        mock_project_repo = Mock()
        mock_project_repo.get_by_id.return_value = Success(project)

        mock_schema_repo = Mock()
        mock_schema_repo.get_entity_definition.return_value = Failure("Schema error")

        service = ValidationService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )
        result = service.validate_by_project_id(project.id)

        assert isinstance(result, Failure)
        assert "Failed to load entity definition" in result.error

    def test_entity_definition_not_found(self) -> None:
        """validate_by_project_id should fail when entity definition is not found."""
        entity_def_id = EntityDefinitionId("test_entity")
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def_id,
            field_values={},
        )

        mock_project_repo = Mock()
        mock_project_repo.get_by_id.return_value = Success(project)

        mock_schema_repo = Mock()
        mock_schema_repo.get_entity_definition.return_value = Success(None)

        service = ValidationService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )
        result = service.validate_by_project_id(project.id)

        assert isinstance(result, Failure)
        assert "Entity definition not found" in result.error

    def test_success(self) -> None:
        """validate_by_project_id should succeed with valid repositories."""
        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={},
        )

        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def.id,
            field_values={},
        )

        mock_project_repo = Mock()
        mock_project_repo.get_by_id.return_value = Success(project)

        mock_schema_repo = Mock()
        mock_schema_repo.get_entity_definition.return_value = Success(entity_def)

        service = ValidationService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )
        result = service.validate_by_project_id(project.id)

        assert isinstance(result, Success)
        validation_result = result.value
        assert validation_result.is_valid()
        mock_project_repo.get_by_id.assert_called_once_with(project.id)
        mock_schema_repo.get_entity_definition.assert_called_once_with(entity_def.id)


class TestValidationServiceValidateProject:
    """Tests for ValidationService.validate_project method edge cases."""

    def test_orphaned_field_skipped(self) -> None:
        """validate_project should skip fields not in entity definition."""
        # Entity definition with only one field
        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("field1"): FieldDefinition(
                    id=FieldDefinitionId("field1"),
                    label_key=TranslationKey("fields.field1"),
                    field_type=FieldType.TEXT,
                    constraints=(),
                ),
            },
        )

        # Project with orphaned field (field2 not in entity definition)
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def.id,
            field_values={
                FieldDefinitionId("field1"): FieldValue(
                    field_id=FieldDefinitionId("field1"),
                    value="valid text",
                ),
                FieldDefinitionId("field2"): FieldValue(
                    field_id=FieldDefinitionId("field2"),
                    value="orphaned value",
                ),
            },
        )

        service = ValidationService()
        result = service.validate_project(project, entity_def)

        # Orphaned field should be skipped, no errors
        assert result.is_valid()


class TestValidationServiceValidateField:
    """Tests for ValidationService.validate_field type validation."""

    def test_invalid_field_path_type(self) -> None:
        """validate_field should raise TypeError for invalid field_path."""
        field_def = FieldDefinition(
            id=FieldDefinitionId("field1"),
            label_key=TranslationKey("fields.field1"),
            field_type=FieldType.TEXT,
            constraints=(),
        )

        service = ValidationService()
        with pytest.raises(TypeError, match="field_path must be a string"):
            service.validate_field(
                field_path=123,  # type: ignore
                value="test",
                field_definition=field_def,
            )

    def test_invalid_field_definition_type(self) -> None:
        """validate_field should raise TypeError for invalid field_definition."""
        service = ValidationService()
        with pytest.raises(TypeError, match="field_definition must be a FieldDefinition"):
            service.validate_field(
                field_path="field1",
                value="test",
                field_definition="not_a_field_def",  # type: ignore
            )


class TestValidationServiceValidateFields:
    """Tests for ValidationService.validate_fields type validation and edge cases."""

    def test_invalid_field_values_type(self) -> None:
        """validate_fields should raise TypeError for invalid field_values."""
        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={},
        )

        service = ValidationService()
        with pytest.raises(TypeError, match="field_values must be a dictionary"):
            service.validate_fields(
                field_values="not_a_dict",  # type: ignore
                entity_definition=entity_def,
            )

    def test_invalid_entity_definition_type(self) -> None:
        """validate_fields should raise TypeError for invalid entity_definition."""
        service = ValidationService()
        with pytest.raises(TypeError, match="entity_definition must be an EntityDefinition"):
            service.validate_fields(
                field_values={},
                entity_definition="not_an_entity_def",  # type: ignore
            )

    def test_orphaned_field_skipped_in_validate_fields(self) -> None:
        """validate_fields should skip fields not in entity definition."""
        # Entity definition with only one field
        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("field1"): FieldDefinition(
                    id=FieldDefinitionId("field1"),
                    label_key=TranslationKey("fields.field1"),
                    field_type=FieldType.TEXT,
                    constraints=(),
                ),
            },
        )

        # Field values with orphaned field (field2 not in entity definition)
        field_values = {
            FieldDefinitionId("field1"): "valid text",
            FieldDefinitionId("field2"): "orphaned value",
        }

        service = ValidationService()
        result = service.validate_fields(field_values, entity_def)

        # Orphaned field should be skipped, no errors
        assert result.is_valid()

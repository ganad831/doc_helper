"""Smoke tests to verify basic integration of all layers."""

from pathlib import Path
from uuid import uuid4

import pytest

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Success
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.validation.constraints import RequiredConstraint
from doc_helper.infrastructure.persistence.sqlite_project_repository import (
    SqliteProjectRepository,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create temporary database."""
    return tmp_path / "test.db"


class TestIntegrationSmoke:
    """Smoke tests for basic integration."""

    def test_repository_save_and_load_project(self, temp_db: Path) -> None:
        """Test: Create project → Save to repository → Load from repository."""
        # Create project
        project_id = ProjectId(uuid4())
        entity_id = EntityDefinitionId("soil_investigation")

        project = Project(
            id=project_id,
            name="Test Project",
            app_type_id="soil_investigation",
            entity_definition_id=entity_id,
            field_values={},
            description="Test description",
        )

        # Save to repository
        repo = SqliteProjectRepository(temp_db)
        save_result = repo.save(project)
        assert isinstance(save_result, Success)

        # Load from repository
        load_result = repo.get_by_id(project_id)
        assert isinstance(load_result, Success)

        loaded_project = load_result.value
        assert loaded_project.id == project_id
        assert loaded_project.name == "Test Project"
        assert loaded_project.description == "Test description"

    def test_project_with_field_values(self, temp_db: Path) -> None:
        """Test: Project with field values → Save → Load → Verify values."""
        # Create project with field values
        project_id = ProjectId(uuid4())
        entity_id = EntityDefinitionId("soil_investigation")

        field_values = {
            FieldDefinitionId("name"): FieldValue(
                field_id=FieldDefinitionId("name"),
                value="Site Name",
            ),
            FieldDefinitionId("location"): FieldValue(
                field_id=FieldDefinitionId("location"),
                value="Test Location",
            ),
        }

        project = Project(
            id=project_id,
            name="Project with Fields",
            app_type_id="soil_investigation",
            entity_definition_id=entity_id,
            field_values=field_values,
        )

        # Save and load
        repo = SqliteProjectRepository(temp_db)
        repo.save(project)
        load_result = repo.get_by_id(project_id)

        assert isinstance(load_result, Success)
        loaded_project = load_result.value

        # Verify field values
        name_value = loaded_project.get_field_value(FieldDefinitionId("name"))
        assert name_value is not None
        assert name_value.value == "Site Name"

        location_value = loaded_project.get_field_value(FieldDefinitionId("location"))
        assert location_value is not None
        assert location_value.value == "Test Location"

    def test_entity_definition_with_fields(self) -> None:
        """Test: Create entity definition with fields → Verify structure."""
        # Create fields
        name_field_id = FieldDefinitionId("name")
        name_field = FieldDefinition(
            id=name_field_id,
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            required=True,
            constraints=(RequiredConstraint(),),
        )

        location_field_id = FieldDefinitionId("location")
        location_field = FieldDefinition(
            id=location_field_id,
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.location"),
            required=False,
        )

        # Create entity definition
        entity_def = EntityDefinition(
            id=EntityDefinitionId("soil_investigation"),
            name_key=TranslationKey("entity.soil_investigation"),
            fields={
                name_field_id: name_field,
                location_field_id: location_field,
            },
        )

        # Verify structure
        assert entity_def.has_field(name_field_id)
        assert entity_def.has_field(location_field_id)

        retrieved_name_field = entity_def.get_field(name_field_id)
        assert retrieved_name_field is not None
        assert retrieved_name_field.field_type == FieldType.TEXT
        assert retrieved_name_field.required is True

        retrieved_location_field = entity_def.get_field(location_field_id)
        assert retrieved_location_field is not None
        assert retrieved_location_field.required is False

    def test_multiple_projects_independence(self, temp_db: Path) -> None:
        """Test: Create multiple projects → Verify they are independent."""
        repo = SqliteProjectRepository(temp_db)

        # Create first project
        project1_id = ProjectId(uuid4())
        project1 = Project(
            id=project1_id,
            name="Project 1",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("soil_investigation"),
            field_values={},
        )
        repo.save(project1)

        # Create second project
        project2_id = ProjectId(uuid4())
        project2 = Project(
            id=project2_id,
            name="Project 2",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("soil_investigation"),
            field_values={},
        )
        repo.save(project2)

        # Load both projects
        load1_result = repo.get_by_id(project1_id)
        load2_result = repo.get_by_id(project2_id)

        assert isinstance(load1_result, Success)
        assert isinstance(load2_result, Success)

        loaded1 = load1_result.value
        loaded2 = load2_result.value

        # Verify independence
        assert loaded1.id != loaded2.id
        assert loaded1.name == "Project 1"
        assert loaded2.name == "Project 2"

"""Tests for project aggregate."""

import pytest
from uuid import uuid4

from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId


class TestProject:
    """Tests for Project aggregate root."""

    def test_create_project(self) -> None:
        """Project should be created with required fields."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=EntityDefinitionId("project"),
        )
        assert project.name == "Test Project"
        assert project.entity_definition_id == EntityDefinitionId("project")
        assert len(project.field_values) == 0
        assert project.description is None
        assert project.file_path is None

    def test_create_project_with_field_values(self) -> None:
        """Project should be created with initial field values."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="value1")
        field2 = FieldValue(field_id=FieldDefinitionId("field2"), value=42)

        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={
                FieldDefinitionId("field1"): field1,
                FieldDefinitionId("field2"): field2,
            },
        )
        assert len(project.field_values) == 2
        assert project.get_field_value(FieldDefinitionId("field1")) == field1
        assert project.get_field_value(FieldDefinitionId("field2")) == field2

    def test_create_project_with_description(self) -> None:
        """Project should accept optional description."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=EntityDefinitionId("project"),
            description="Project description",
        )
        assert project.description == "Project description"

    def test_project_requires_name(self) -> None:
        """Project should require string name."""
        with pytest.raises(TypeError, match="name must be a string"):
            Project(
                id=ProjectId(uuid4()),
                name=123,  # type: ignore
                entity_definition_id=EntityDefinitionId("project"),
            )

    def test_project_name_cannot_be_empty(self) -> None:
        """Project name cannot be empty."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Project(
                id=ProjectId(uuid4()),
                name="   ",  # Whitespace only
                entity_definition_id=EntityDefinitionId("project"),
            )

    def test_project_requires_entity_definition_id(self) -> None:
        """Project should require EntityDefinitionId."""
        with pytest.raises(TypeError, match="entity_definition_id must be an EntityDefinitionId"):
            Project(
                id=ProjectId(uuid4()),
                name="Test",
                entity_definition_id="project",  # type: ignore
            )

    def test_project_field_values_must_be_dict(self) -> None:
        """Project field_values must be dict."""
        with pytest.raises(TypeError, match="field_values must be a dict"):
            Project(
                id=ProjectId(uuid4()),
                name="Test",
                entity_definition_id=EntityDefinitionId("project"),
                field_values=[],  # type: ignore
            )

    def test_project_field_values_keys_must_be_field_definition_id(self) -> None:
        """Project field_values keys must be FieldDefinitionId."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="value1")
        with pytest.raises(TypeError, match="All field_values keys must be FieldDefinitionId"):
            Project(
                id=ProjectId(uuid4()),
                name="Test",
                entity_definition_id=EntityDefinitionId("project"),
                field_values={"field1": field1},  # type: ignore - string key
            )

    def test_project_field_values_values_must_be_field_value(self) -> None:
        """Project field_values values must be FieldValue."""
        with pytest.raises(TypeError, match="All field_values values must be FieldValue"):
            Project(
                id=ProjectId(uuid4()),
                name="Test",
                entity_definition_id=EntityDefinitionId("project"),
                field_values={FieldDefinitionId("field1"): "value1"},  # type: ignore
            )

    def test_project_field_value_id_must_match_key(self) -> None:
        """FieldValue field_id must match dictionary key."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="value1")
        with pytest.raises(ValueError, match="FieldValue field_id mismatch"):
            Project(
                id=ProjectId(uuid4()),
                name="Test",
                entity_definition_id=EntityDefinitionId("project"),
                field_values={FieldDefinitionId("field2"): field1},  # Mismatch!
            )

    def test_get_field_value(self) -> None:
        """get_field_value should return field value by ID."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="value1")
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={FieldDefinitionId("field1"): field1},
        )
        result = project.get_field_value(FieldDefinitionId("field1"))
        assert result == field1

    def test_get_field_value_not_found(self) -> None:
        """get_field_value should return None if field not found."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        result = project.get_field_value(FieldDefinitionId("nonexistent"))
        assert result is None

    def test_get_field_value_requires_field_definition_id(self) -> None:
        """get_field_value should require FieldDefinitionId."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        with pytest.raises(TypeError, match="field_id must be a FieldDefinitionId"):
            project.get_field_value("field1")  # type: ignore

    def test_has_field_value(self) -> None:
        """has_field_value should check field existence."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="value1")
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={FieldDefinitionId("field1"): field1},
        )
        assert project.has_field_value(FieldDefinitionId("field1")) is True
        assert project.has_field_value(FieldDefinitionId("field2")) is False

    def test_set_field_value_new(self) -> None:
        """set_field_value should create new field value."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        project.set_field_value(FieldDefinitionId("field1"), "value1")

        field_value = project.get_field_value(FieldDefinitionId("field1"))
        assert field_value is not None
        assert field_value.value == "value1"
        assert field_value.is_computed is False

    def test_set_field_value_update(self) -> None:
        """set_field_value should update existing field value."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="old_value")
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={FieldDefinitionId("field1"): field1},
        )
        project.set_field_value(FieldDefinitionId("field1"), "new_value")

        field_value = project.get_field_value(FieldDefinitionId("field1"))
        assert field_value is not None
        assert field_value.value == "new_value"

    def test_set_field_value_on_computed_creates_override(self) -> None:
        """set_field_value on computed field should create override."""
        computed_field = FieldValue(
            field_id=FieldDefinitionId("total"),
            value=1500,
            is_computed=True,
            computed_from="a + b",
        )
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={FieldDefinitionId("total"): computed_field},
        )
        project.set_field_value(FieldDefinitionId("total"), 1600)

        field_value = project.get_field_value(FieldDefinitionId("total"))
        assert field_value is not None
        assert field_value.value == 1600
        assert field_value.is_override is True
        assert field_value.original_computed_value == 1500

    def test_set_field_value_touches_entity(self) -> None:
        """set_field_value should update modified timestamp."""
        import time

        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        original_modified = project.modified_at
        time.sleep(0.001)
        project.set_field_value(FieldDefinitionId("field1"), "value1")
        assert project.modified_at > original_modified

    def test_set_computed_field_value(self) -> None:
        """set_computed_field_value should set computed value."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        project.set_computed_field_value(FieldDefinitionId("total"), 1500, "a + b")

        field_value = project.get_field_value(FieldDefinitionId("total"))
        assert field_value is not None
        assert field_value.value == 1500
        assert field_value.is_computed is True
        assert field_value.computed_from == "a + b"

    def test_set_computed_field_value_preserves_override(self) -> None:
        """set_computed_field_value should preserve existing override."""
        override_field = FieldValue(
            field_id=FieldDefinitionId("total"),
            value=1600,
            is_override=True,
            original_computed_value=1500,
        )
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={FieldDefinitionId("total"): override_field},
        )
        project.set_computed_field_value(FieldDefinitionId("total"), 1550, "a + b")

        field_value = project.get_field_value(FieldDefinitionId("total"))
        assert field_value is not None
        assert field_value.value == 1600  # Override preserved
        assert field_value.is_override is True
        assert field_value.original_computed_value == 1550  # Updated

    def test_set_computed_field_value_requires_formula_string(self) -> None:
        """set_computed_field_value should require formula string."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        with pytest.raises(TypeError, match="formula must be a string"):
            project.set_computed_field_value(FieldDefinitionId("total"), 1500, 123)  # type: ignore

    def test_clear_field_override(self) -> None:
        """clear_field_override should restore computed value."""
        override_field = FieldValue(
            field_id=FieldDefinitionId("total"),
            value=1600,
            is_override=True,
            original_computed_value=1500,
        )
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={FieldDefinitionId("total"): override_field},
        )
        project.clear_field_override(FieldDefinitionId("total"))

        field_value = project.get_field_value(FieldDefinitionId("total"))
        assert field_value is not None
        assert field_value.value == 1500  # Restored
        assert field_value.is_override is False

    def test_clear_field_override_not_found_raises(self) -> None:
        """clear_field_override should raise if field not found."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        with pytest.raises(KeyError, match="Field 'nonexistent' not found"):
            project.clear_field_override(FieldDefinitionId("nonexistent"))

    def test_clear_field_override_not_override_raises(self) -> None:
        """clear_field_override should raise if field is not override."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value=42)
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={FieldDefinitionId("field1"): field1},
        )
        with pytest.raises(ValueError, match="this value is not an override"):
            project.clear_field_override(FieldDefinitionId("field1"))

    def test_remove_field_value(self) -> None:
        """remove_field_value should remove field."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="value1")
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={FieldDefinitionId("field1"): field1},
        )
        project.remove_field_value(FieldDefinitionId("field1"))

        assert project.has_field_value(FieldDefinitionId("field1")) is False

    def test_remove_field_value_not_found_raises(self) -> None:
        """remove_field_value should raise if field not found."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        with pytest.raises(KeyError, match="Field 'nonexistent' not found"):
            project.remove_field_value(FieldDefinitionId("nonexistent"))

    def test_get_all_field_values(self) -> None:
        """get_all_field_values should return all fields."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="value1")
        field2 = FieldValue(field_id=FieldDefinitionId("field2"), value=42)
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={
                FieldDefinitionId("field1"): field1,
                FieldDefinitionId("field2"): field2,
            },
        )
        all_fields = project.get_all_field_values()

        assert len(all_fields) == 2
        assert (FieldDefinitionId("field1"), field1) in all_fields
        assert (FieldDefinitionId("field2"), field2) in all_fields

    def test_get_computed_field_ids(self) -> None:
        """get_computed_field_ids should return computed field IDs."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="value1")
        field2 = FieldValue(
            field_id=FieldDefinitionId("total"),
            value=1500,
            is_computed=True,
            computed_from="a + b",
        )
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={
                FieldDefinitionId("field1"): field1,
                FieldDefinitionId("total"): field2,
            },
        )
        computed_ids = project.get_computed_field_ids()

        assert len(computed_ids) == 1
        assert FieldDefinitionId("total") in computed_ids

    def test_get_overridden_field_ids(self) -> None:
        """get_overridden_field_ids should return overridden field IDs."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="value1")
        field2 = FieldValue(
            field_id=FieldDefinitionId("total"),
            value=1600,
            is_override=True,
            original_computed_value=1500,
        )
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={
                FieldDefinitionId("field1"): field1,
                FieldDefinitionId("total"): field2,
            },
        )
        override_ids = project.get_overridden_field_ids()

        assert len(override_ids) == 1
        assert FieldDefinitionId("total") in override_ids

    def test_rename_project(self) -> None:
        """rename should update project name."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Old Name",
            entity_definition_id=EntityDefinitionId("project"),
        )
        project.rename("New Name")
        assert project.name == "New Name"

    def test_rename_requires_string(self) -> None:
        """rename should require string."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        with pytest.raises(TypeError, match="new_name must be a string"):
            project.rename(123)  # type: ignore

    def test_rename_cannot_be_empty(self) -> None:
        """rename cannot use empty string."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        with pytest.raises(ValueError, match="new_name cannot be empty"):
            project.rename("   ")

    def test_update_description(self) -> None:
        """update_description should update description."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        project.update_description("New description")
        assert project.description == "New description"

    def test_update_description_to_none(self) -> None:
        """update_description should allow None to clear."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            description="Old description",
        )
        project.update_description(None)
        assert project.description is None

    def test_set_file_path(self) -> None:
        """set_file_path should update file path."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        project.set_file_path("/path/to/project.dhproj")
        assert project.file_path == "/path/to/project.dhproj"

    def test_set_file_path_requires_string(self) -> None:
        """set_file_path should require string."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        with pytest.raises(TypeError, match="file_path must be a string"):
            project.set_file_path(123)  # type: ignore

    def test_field_count_property(self) -> None:
        """field_count should return number of fields."""
        field1 = FieldValue(field_id=FieldDefinitionId("field1"), value="value1")
        field2 = FieldValue(field_id=FieldDefinitionId("field2"), value=42)
        project = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={
                FieldDefinitionId("field1"): field1,
                FieldDefinitionId("field2"): field2,
            },
        )
        assert project.field_count == 2

    def test_is_saved_property(self) -> None:
        """is_saved should return True if project has file path."""
        project1 = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
        )
        assert project1.is_saved is False

        project2 = Project(
            id=ProjectId(uuid4()),
            name="Test",
            entity_definition_id=EntityDefinitionId("project"),
            file_path="/path/to/project.dhproj",
        )
        assert project2.is_saved is True

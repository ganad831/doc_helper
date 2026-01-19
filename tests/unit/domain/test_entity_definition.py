"""Tests for EntityDefinition."""

import pytest
from datetime import datetime

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.validation.constraints import RequiredConstraint


class TestEntityDefinition:
    """Tests for EntityDefinition."""

    def test_create_empty_entity(self) -> None:
        """EntityDefinition should create entity with no fields."""
        entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        assert entity.id.value == "project"
        assert entity.field_count == 0
        assert len(entity.get_all_fields()) == 0

    def test_create_entity_with_fields(self) -> None:
        """EntityDefinition should create entity with fields."""
        fields = {
            FieldDefinitionId("site_location"): FieldDefinition(
                id=FieldDefinitionId("site_location"),
                field_type=FieldType.TEXT,
                label_key=TranslationKey("field.site_location"),
            ),
            FieldDefinitionId("project_date"): FieldDefinition(
                id=FieldDefinitionId("project_date"),
                field_type=FieldType.DATE,
                label_key=TranslationKey("field.project_date"),
            ),
        }
        entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            fields=fields,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        assert entity.field_count == 2
        assert len(entity.get_all_fields()) == 2

    def test_create_root_entity(self) -> None:
        """EntityDefinition should create root entity."""
        entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        assert entity.is_root_entity
        assert not entity.is_child_entity

    def test_create_child_entity(self) -> None:
        """EntityDefinition should create child entity."""
        entity = EntityDefinition(
            id=EntityDefinitionId("borehole"),
            name_key=TranslationKey("entity.borehole"),
            parent_entity_id=EntityDefinitionId("project"),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        assert entity.is_child_entity
        assert not entity.is_root_entity
        assert entity.parent_entity_id == EntityDefinitionId("project")

    def test_get_field_by_id(self) -> None:
        """EntityDefinition should get field by ID."""
        field = FieldDefinition(
            id=FieldDefinitionId("site_location"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.site_location"),
        )
        fields = {FieldDefinitionId("site_location"): field}
        entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            fields=fields,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )

        retrieved = entity.get_field(FieldDefinitionId("site_location"))
        assert retrieved is not None
        assert retrieved.id == FieldDefinitionId("site_location")

        not_found = entity.get_field(FieldDefinitionId("nonexistent"))
        assert not_found is None

    def test_has_field(self) -> None:
        """EntityDefinition should check field existence."""
        field = FieldDefinition(
            id=FieldDefinitionId("site_location"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.site_location"),
        )
        fields = {FieldDefinitionId("site_location"): field}
        entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            fields=fields,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )

        assert entity.has_field(FieldDefinitionId("site_location"))
        assert not entity.has_field(FieldDefinitionId("nonexistent"))

    def test_get_all_fields(self) -> None:
        """EntityDefinition should return all fields."""
        fields = {
            FieldDefinitionId("field1"): FieldDefinition(
                id=FieldDefinitionId("field1"),
                field_type=FieldType.TEXT,
                label_key=TranslationKey("field.field1"),
            ),
            FieldDefinitionId("field2"): FieldDefinition(
                id=FieldDefinitionId("field2"),
                field_type=FieldType.NUMBER,
                label_key=TranslationKey("field.field2"),
            ),
        }
        entity = EntityDefinition(
            id=EntityDefinitionId("entity"),
            name_key=TranslationKey("entity.name"),
            fields=fields,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )

        all_fields = entity.get_all_fields()
        assert len(all_fields) == 2
        assert isinstance(all_fields, tuple)

    def test_get_required_fields(self) -> None:
        """EntityDefinition should filter required fields."""
        fields = {
            FieldDefinitionId("required_field"): FieldDefinition(
                id=FieldDefinitionId("required_field"),
                field_type=FieldType.TEXT,
                label_key=TranslationKey("field.required"),
                required=True,
            ),
            FieldDefinitionId("optional_field"): FieldDefinition(
                id=FieldDefinitionId("optional_field"),
                field_type=FieldType.TEXT,
                label_key=TranslationKey("field.optional"),
                required=False,
            ),
        }
        entity = EntityDefinition(
            id=EntityDefinitionId("entity"),
            name_key=TranslationKey("entity.name"),
            fields=fields,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )

        required_fields = entity.get_required_fields()
        assert len(required_fields) == 1
        assert required_fields[0].id == FieldDefinitionId("required_field")

    def test_get_calculated_fields(self) -> None:
        """EntityDefinition should filter calculated fields."""
        fields = {
            FieldDefinitionId("input_field"): FieldDefinition(
                id=FieldDefinitionId("input_field"),
                field_type=FieldType.NUMBER,
                label_key=TranslationKey("field.input"),
            ),
            FieldDefinitionId("calculated_field"): FieldDefinition(
                id=FieldDefinitionId("calculated_field"),
                field_type=FieldType.CALCULATED,
                label_key=TranslationKey("field.calculated"),
                formula="input_field * 2",
            ),
        }
        entity = EntityDefinition(
            id=EntityDefinitionId("entity"),
            name_key=TranslationKey("entity.name"),
            fields=fields,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )

        calculated_fields = entity.get_calculated_fields()
        assert len(calculated_fields) == 1
        assert calculated_fields[0].id == FieldDefinitionId("calculated_field")

    def test_get_table_fields(self) -> None:
        """EntityDefinition should filter table fields."""
        fields = {
            FieldDefinitionId("name"): FieldDefinition(
                id=FieldDefinitionId("name"),
                field_type=FieldType.TEXT,
                label_key=TranslationKey("field.name"),
            ),
            FieldDefinitionId("boreholes"): FieldDefinition(
                id=FieldDefinitionId("boreholes"),
                field_type=FieldType.TABLE,
                label_key=TranslationKey("field.boreholes"),
                child_entity_id="borehole",
            ),
        }
        entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            fields=fields,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )

        table_fields = entity.get_table_fields()
        assert len(table_fields) == 1
        assert table_fields[0].id == FieldDefinitionId("boreholes")

    def test_validate_field_reference_success(self) -> None:
        """EntityDefinition should validate existing field reference."""
        fields = {
            FieldDefinitionId("field1"): FieldDefinition(
                id=FieldDefinitionId("field1"),
                field_type=FieldType.TEXT,
                label_key=TranslationKey("field.field1"),
            ),
        }
        entity = EntityDefinition(
            id=EntityDefinitionId("entity"),
            name_key=TranslationKey("entity.name"),
            fields=fields,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )

        # Should not raise
        entity.validate_field_reference(FieldDefinitionId("field1"))

    def test_validate_field_reference_failure(self) -> None:
        """EntityDefinition should reject invalid field reference."""
        entity = EntityDefinition(
            id=EntityDefinitionId("entity"),
            name_key=TranslationKey("entity.name"),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="does not exist"):
            entity.validate_field_reference(FieldDefinitionId("nonexistent"))

    def test_field_id_mismatch_raises(self) -> None:
        """EntityDefinition should reject field ID mismatch."""
        fields = {
            FieldDefinitionId("key_id"): FieldDefinition(
                id=FieldDefinitionId("different_id"),
                field_type=FieldType.TEXT,
                label_key=TranslationKey("field.name"),
            ),
        }

        with pytest.raises(ValueError, match="Field definition ID mismatch"):
            EntityDefinition(
                id=EntityDefinitionId("entity"),
                name_key=TranslationKey("entity.name"),
                fields=fields,
                created_at=datetime.now(),
                modified_at=datetime.now(),
            )

    def test_fields_must_be_dict(self) -> None:
        """EntityDefinition should reject non-dict fields."""
        with pytest.raises(ValueError, match="fields must be a dict"):
            EntityDefinition(
                id=EntityDefinitionId("entity"),
                name_key=TranslationKey("entity.name"),
                fields=[],  # type: ignore
                created_at=datetime.now(),
                modified_at=datetime.now(),
            )

    def test_field_keys_must_be_field_definition_id(self) -> None:
        """EntityDefinition should reject non-FieldDefinitionId keys."""
        fields = {
            "string_key": FieldDefinition(  # type: ignore
                id=FieldDefinitionId("field"),
                field_type=FieldType.TEXT,
                label_key=TranslationKey("field.name"),
            ),
        }

        with pytest.raises(ValueError, match="All field keys must be FieldDefinitionId"):
            EntityDefinition(
                id=EntityDefinitionId("entity"),
                name_key=TranslationKey("entity.name"),
                fields=fields,
                created_at=datetime.now(),
                modified_at=datetime.now(),
            )

    def test_field_values_must_be_field_definition(self) -> None:
        """EntityDefinition should reject non-FieldDefinition values."""
        fields = {
            FieldDefinitionId("field"): "not a field definition",  # type: ignore
        }

        with pytest.raises(ValueError, match="All field values must be FieldDefinition"):
            EntityDefinition(
                id=EntityDefinitionId("entity"),
                name_key=TranslationKey("entity.name"),
                fields=fields,
                created_at=datetime.now(),
                modified_at=datetime.now(),
            )

    def test_entity_with_description(self) -> None:
        """EntityDefinition should accept description key."""
        entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            description_key=TranslationKey("entity.project.description"),
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        assert entity.description_key is not None
        assert entity.description_key.key == "entity.project.description"

"""Tests for schema strongly-typed IDs."""

import pytest

from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId


class TestFieldDefinitionId:
    """Tests for FieldDefinitionId."""

    def test_valid_field_id(self) -> None:
        """FieldDefinitionId should accept valid IDs."""
        field_id = FieldDefinitionId("site_location")
        assert field_id.value == "site_location"
        assert str(field_id) == "site_location"

    def test_field_id_with_underscore(self) -> None:
        """FieldDefinitionId should accept underscores."""
        field_id = FieldDefinitionId("total_depth_meters")
        assert field_id.value == "total_depth_meters"

    def test_field_id_with_hyphen(self) -> None:
        """FieldDefinitionId should accept hyphens."""
        field_id = FieldDefinitionId("water-table-depth")
        assert field_id.value == "water-table-depth"

    def test_field_id_numeric(self) -> None:
        """FieldDefinitionId should accept alphanumeric."""
        field_id = FieldDefinitionId("borehole1")
        assert field_id.value == "borehole1"

    def test_empty_field_id_raises(self) -> None:
        """FieldDefinitionId should reject empty value."""
        with pytest.raises(ValueError, match="cannot be empty"):
            FieldDefinitionId("")

    def test_invalid_characters_raises(self) -> None:
        """FieldDefinitionId should reject invalid characters."""
        with pytest.raises(ValueError, match="invalid characters"):
            FieldDefinitionId("field@name")

        with pytest.raises(ValueError, match="invalid characters"):
            FieldDefinitionId("field name")  # space

        with pytest.raises(ValueError, match="invalid characters"):
            FieldDefinitionId("field.name")  # dot

    def test_uppercase_raises(self) -> None:
        """FieldDefinitionId should reject uppercase."""
        with pytest.raises(ValueError, match="must be lowercase"):
            FieldDefinitionId("SiteLocation")

        with pytest.raises(ValueError, match="must be lowercase"):
            FieldDefinitionId("SITE_LOCATION")

    def test_field_id_immutable(self) -> None:
        """FieldDefinitionId should be immutable."""
        field_id = FieldDefinitionId("site_location")
        with pytest.raises(AttributeError):
            field_id.value = "changed"  # type: ignore

    def test_field_id_equality(self) -> None:
        """FieldDefinitionId should compare by value."""
        id1 = FieldDefinitionId("site_location")
        id2 = FieldDefinitionId("site_location")
        id3 = FieldDefinitionId("soil_type")

        assert id1 == id2
        assert id1 != id3

    def test_field_id_hashable(self) -> None:
        """FieldDefinitionId should be hashable (for use in dicts/sets)."""
        id1 = FieldDefinitionId("site_location")
        id2 = FieldDefinitionId("soil_type")

        field_set = {id1, id2}
        assert id1 in field_set
        assert FieldDefinitionId("site_location") in field_set


class TestEntityDefinitionId:
    """Tests for EntityDefinitionId."""

    def test_valid_entity_id(self) -> None:
        """EntityDefinitionId should accept valid IDs."""
        entity_id = EntityDefinitionId("project")
        assert entity_id.value == "project"
        assert str(entity_id) == "project"

    def test_entity_id_with_underscore(self) -> None:
        """EntityDefinitionId should accept underscores."""
        entity_id = EntityDefinitionId("lab_test")
        assert entity_id.value == "lab_test"

    def test_entity_id_with_hyphen(self) -> None:
        """EntityDefinitionId should accept hyphens."""
        entity_id = EntityDefinitionId("soil-sample")
        assert entity_id.value == "soil-sample"

    def test_empty_entity_id_raises(self) -> None:
        """EntityDefinitionId should reject empty value."""
        with pytest.raises(ValueError, match="cannot be empty"):
            EntityDefinitionId("")

    def test_invalid_characters_raises(self) -> None:
        """EntityDefinitionId should reject invalid characters."""
        with pytest.raises(ValueError, match="invalid characters"):
            EntityDefinitionId("entity@name")

        with pytest.raises(ValueError, match="invalid characters"):
            EntityDefinitionId("entity name")  # space

    def test_uppercase_raises(self) -> None:
        """EntityDefinitionId should reject uppercase."""
        with pytest.raises(ValueError, match="must be lowercase"):
            EntityDefinitionId("Project")

        with pytest.raises(ValueError, match="must be lowercase"):
            EntityDefinitionId("LAB_TEST")

    def test_entity_id_immutable(self) -> None:
        """EntityDefinitionId should be immutable."""
        entity_id = EntityDefinitionId("project")
        with pytest.raises(AttributeError):
            entity_id.value = "changed"  # type: ignore

    def test_entity_id_equality(self) -> None:
        """EntityDefinitionId should compare by value."""
        id1 = EntityDefinitionId("project")
        id2 = EntityDefinitionId("project")
        id3 = EntityDefinitionId("borehole")

        assert id1 == id2
        assert id1 != id3

    def test_entity_id_hashable(self) -> None:
        """EntityDefinitionId should be hashable (for use in dicts/sets)."""
        id1 = EntityDefinitionId("project")
        id2 = EntityDefinitionId("borehole")

        entity_set = {id1, id2}
        assert id1 in entity_set
        assert EntityDefinitionId("project") in entity_set

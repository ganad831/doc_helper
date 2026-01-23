"""Tests for relationship domain entities (Phase 6A - ADR-022).

Tests for:
- RelationshipType enum
- RelationshipDefinitionId value object
- RelationshipDefinition aggregate root
"""

import pytest

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.relationship_type import RelationshipType
from doc_helper.domain.schema.schema_ids import (
    EntityDefinitionId,
    RelationshipDefinitionId,
)


class TestRelationshipType:
    """Tests for RelationshipType enum."""

    def test_contains_value(self) -> None:
        """CONTAINS type should have correct value."""
        assert RelationshipType.CONTAINS.value == "CONTAINS"

    def test_references_value(self) -> None:
        """REFERENCES type should have correct value."""
        assert RelationshipType.REFERENCES.value == "REFERENCES"

    def test_associates_value(self) -> None:
        """ASSOCIATES type should have correct value."""
        assert RelationshipType.ASSOCIATES.value == "ASSOCIATES"

    def test_from_string(self) -> None:
        """Should create enum from string value."""
        assert RelationshipType("CONTAINS") == RelationshipType.CONTAINS
        assert RelationshipType("REFERENCES") == RelationshipType.REFERENCES
        assert RelationshipType("ASSOCIATES") == RelationshipType.ASSOCIATES

    def test_invalid_string_raises(self) -> None:
        """Should raise ValueError for invalid type string."""
        with pytest.raises(ValueError):
            RelationshipType("INVALID")

    def test_all_types_defined(self) -> None:
        """Should have exactly 3 relationship types per ADR-022."""
        assert len(RelationshipType) == 3


class TestRelationshipDefinitionId:
    """Tests for RelationshipDefinitionId value object."""

    def test_valid_id(self) -> None:
        """Should accept valid ID."""
        rel_id = RelationshipDefinitionId("project_contains_boreholes")
        assert rel_id.value == "project_contains_boreholes"
        assert str(rel_id) == "project_contains_boreholes"

    def test_id_with_underscore(self) -> None:
        """Should accept underscores."""
        rel_id = RelationshipDefinitionId("project_has_samples")
        assert rel_id.value == "project_has_samples"

    def test_id_with_hyphen(self) -> None:
        """Should accept hyphens."""
        rel_id = RelationshipDefinitionId("borehole-references-sample")
        assert rel_id.value == "borehole-references-sample"

    def test_empty_id_raises(self) -> None:
        """Should reject empty value."""
        with pytest.raises(ValueError, match="cannot be empty"):
            RelationshipDefinitionId("")

    def test_invalid_characters_raises(self) -> None:
        """Should reject invalid characters."""
        with pytest.raises(ValueError, match="invalid characters"):
            RelationshipDefinitionId("rel@name")

        with pytest.raises(ValueError, match="invalid characters"):
            RelationshipDefinitionId("rel name")  # space

        with pytest.raises(ValueError, match="invalid characters"):
            RelationshipDefinitionId("rel.name")  # dot

    def test_uppercase_raises(self) -> None:
        """Should reject uppercase."""
        with pytest.raises(ValueError, match="must be lowercase"):
            RelationshipDefinitionId("Project_Contains_Boreholes")

    def test_id_immutable(self) -> None:
        """Should be immutable."""
        rel_id = RelationshipDefinitionId("project_contains_boreholes")
        with pytest.raises(AttributeError):
            rel_id.value = "changed"  # type: ignore

    def test_id_equality(self) -> None:
        """Should compare by value."""
        id1 = RelationshipDefinitionId("project_contains_boreholes")
        id2 = RelationshipDefinitionId("project_contains_boreholes")
        id3 = RelationshipDefinitionId("project_has_samples")

        assert id1 == id2
        assert id1 != id3

    def test_id_hashable(self) -> None:
        """Should be hashable (for use in dicts/sets)."""
        id1 = RelationshipDefinitionId("project_contains_boreholes")
        id2 = RelationshipDefinitionId("project_has_samples")

        rel_set = {id1, id2}
        assert id1 in rel_set
        assert RelationshipDefinitionId("project_contains_boreholes") in rel_set


class TestRelationshipDefinition:
    """Tests for RelationshipDefinition aggregate root."""

    def test_create_valid_relationship(self) -> None:
        """Should create valid relationship with all required fields."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.project_boreholes"),
        )

        assert relationship.id.value == "project_contains_boreholes"
        assert relationship.source_entity_id.value == "project"
        assert relationship.target_entity_id.value == "borehole"
        assert relationship.relationship_type == RelationshipType.CONTAINS
        assert relationship.name_key.key == "relationship.project_boreholes"
        assert relationship.description_key is None
        assert relationship.inverse_name_key is None

    def test_create_relationship_with_optional_fields(self) -> None:
        """Should create relationship with all optional fields."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.project_boreholes"),
            description_key=TranslationKey("relationship.project_boreholes.desc"),
            inverse_name_key=TranslationKey("relationship.borehole_project"),
        )

        assert relationship.description_key.key == "relationship.project_boreholes.desc"
        assert relationship.inverse_name_key.key == "relationship.borehole_project"

    def test_same_source_target_raises(self) -> None:
        """Should reject relationship where source equals target."""
        with pytest.raises(ValueError, match="Source and target entity must be different"):
            RelationshipDefinition(
                id=RelationshipDefinitionId("self_reference"),
                source_entity_id=EntityDefinitionId("project"),
                target_entity_id=EntityDefinitionId("project"),  # Same as source
                relationship_type=RelationshipType.REFERENCES,
                name_key=TranslationKey("relationship.self"),
            )

    def test_invalid_relationship_type_raises(self) -> None:
        """Should reject invalid relationship type."""
        with pytest.raises(ValueError, match="relationship_type must be a RelationshipType"):
            RelationshipDefinition(
                id=RelationshipDefinitionId("invalid"),
                source_entity_id=EntityDefinitionId("project"),
                target_entity_id=EntityDefinitionId("borehole"),
                relationship_type="CONTAINS",  # type: ignore - String instead of enum
                name_key=TranslationKey("relationship.test"),
            )

    def test_is_contains_property(self) -> None:
        """is_contains should return True for CONTAINS type."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )

        assert relationship.is_contains is True
        assert relationship.is_references is False
        assert relationship.is_associates is False

    def test_is_references_property(self) -> None:
        """is_references should return True for REFERENCES type."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("sample_references_lab"),
            source_entity_id=EntityDefinitionId("sample"),
            target_entity_id=EntityDefinitionId("lab_test"),
            relationship_type=RelationshipType.REFERENCES,
            name_key=TranslationKey("relationship.test"),
        )

        assert relationship.is_contains is False
        assert relationship.is_references is True
        assert relationship.is_associates is False

    def test_is_associates_property(self) -> None:
        """is_associates should return True for ASSOCIATES type."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("borehole_assoc_equipment"),
            source_entity_id=EntityDefinitionId("borehole"),
            target_entity_id=EntityDefinitionId("equipment"),
            relationship_type=RelationshipType.ASSOCIATES,
            name_key=TranslationKey("relationship.test"),
        )

        assert relationship.is_contains is False
        assert relationship.is_references is False
        assert relationship.is_associates is True

    def test_involves_entity_source(self) -> None:
        """involves_entity should return True for source entity."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )

        assert relationship.involves_entity(EntityDefinitionId("project")) is True

    def test_involves_entity_target(self) -> None:
        """involves_entity should return True for target entity."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )

        assert relationship.involves_entity(EntityDefinitionId("borehole")) is True

    def test_involves_entity_unrelated(self) -> None:
        """involves_entity should return False for unrelated entity."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )

        assert relationship.involves_entity(EntityDefinitionId("sample")) is False

    def test_add_only_semantics_note(self) -> None:
        """Relationship immutability is enforced via ADD-ONLY repository semantics.

        Note: The dataclass is not frozen due to AggregateRoot inheritance.
        Immutability is enforced at the repository level per ADR-022.
        """
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )
        # Relationship definition should be created successfully
        assert relationship.id.value == "project_contains_boreholes"

    def test_equality(self) -> None:
        """Relationships with same data should be equal."""
        rel1 = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )

        rel2 = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )

        assert rel1 == rel2

    def test_inequality_different_id(self) -> None:
        """Relationships with different IDs should not be equal."""
        rel1 = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )

        rel2 = RelationshipDefinition(
            id=RelationshipDefinitionId("different_relationship"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )

        assert rel1 != rel2

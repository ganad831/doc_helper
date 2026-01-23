"""RelationshipDefinition aggregate root (Phase 6A - ADR-022).

RelationshipDefinition is a first-class domain entity that defines
explicit semantic relationships between entities.

ADR-022 DECISIONS:
- Relationships are first-class domain entities, not derived metadata
- ADD-ONLY semantics (no update/delete)
- RelationshipType is descriptive metadata only (no runtime behavior)
- All fields are immutable after creation
"""

from dataclasses import dataclass
from typing import Optional

from doc_helper.domain.common.entity import AggregateRoot
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.relationship_type import RelationshipType
from doc_helper.domain.schema.schema_ids import (
    EntityDefinitionId,
    RelationshipDefinitionId,
)


@dataclass(kw_only=True)
class RelationshipDefinition(AggregateRoot[RelationshipDefinitionId]):
    """Definition of a relationship between two entities.

    RelationshipDefinition is an aggregate root that:
    - Defines semantic relationships between entities
    - Provides human-readable names via translation keys
    - Is immutable after creation (ADD-ONLY per ADR-022)
    - Carries descriptive metadata only (no runtime behavior)

    Note: frozen=True not used due to AggregateRoot inheritance.
    Immutability enforced via ADD-ONLY repository semantics.

    RULES (ADR-022):
    - RelationshipDefinition is an aggregate root (ADR-002)
    - All fields are immutable after creation (ADR-010)
    - IDs are strongly typed (ADR-009)
    - Errors returned via Result monad (ADR-008)

    IMPORTANT: RelationshipType is descriptive metadata only.
    The system does NOT enforce cardinality, perform cascade deletes,
    or navigate relationships at runtime.

    Example:
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.project_boreholes"),
            description_key=TranslationKey("relationship.project_boreholes.desc"),
            inverse_name_key=TranslationKey("relationship.borehole_project"),
        )
    """

    # Required fields
    source_entity_id: EntityDefinitionId
    target_entity_id: EntityDefinitionId
    relationship_type: RelationshipType
    name_key: TranslationKey

    # Optional fields
    description_key: Optional[TranslationKey] = None
    inverse_name_key: Optional[TranslationKey] = None

    def __post_init__(self) -> None:
        """Validate relationship definition."""
        # Validate source and target are different entities
        if self.source_entity_id == self.target_entity_id:
            raise ValueError(
                f"Source and target entity must be different. "
                f"Got: {self.source_entity_id.value}"
            )

        # Validate relationship type is valid enum
        if not isinstance(self.relationship_type, RelationshipType):
            raise ValueError(
                f"relationship_type must be a RelationshipType enum, "
                f"got {type(self.relationship_type)}"
            )

    @property
    def is_contains(self) -> bool:
        """Check if this is a CONTAINS relationship.

        Returns:
            True if relationship type is CONTAINS
        """
        return self.relationship_type == RelationshipType.CONTAINS

    @property
    def is_references(self) -> bool:
        """Check if this is a REFERENCES relationship.

        Returns:
            True if relationship type is REFERENCES
        """
        return self.relationship_type == RelationshipType.REFERENCES

    @property
    def is_associates(self) -> bool:
        """Check if this is an ASSOCIATES relationship.

        Returns:
            True if relationship type is ASSOCIATES
        """
        return self.relationship_type == RelationshipType.ASSOCIATES

    def involves_entity(self, entity_id: EntityDefinitionId) -> bool:
        """Check if this relationship involves a given entity.

        Args:
            entity_id: Entity ID to check

        Returns:
            True if entity is source or target of this relationship
        """
        return (
            self.source_entity_id == entity_id or
            self.target_entity_id == entity_id
        )

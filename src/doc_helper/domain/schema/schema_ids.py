"""Strongly-typed IDs for schema domain.

Following ADR-009: Strongly Typed IDs pattern.
"""

from dataclasses import dataclass

from doc_helper.domain.common.value_object import ValueObject


@dataclass(frozen=True)
class FieldDefinitionId(ValueObject):
    """Strongly-typed ID for FieldDefinition.

    Field IDs are unique within an EntityDefinition.
    Convention: lowercase with underscores (e.g., "site_location", "soil_type")

    RULES (ADR-009):
    - Use strongly-typed IDs instead of raw strings
    - IDs are immutable value objects
    - IDs enforce validation rules

    Example:
        field_id = FieldDefinitionId("site_location")
        field_id2 = FieldDefinitionId("soil_type")
    """

    value: str

    def __post_init__(self) -> None:
        """Validate field ID."""
        if not self.value:
            raise ValueError("FieldDefinitionId cannot be empty")
        if not self.value.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"FieldDefinitionId contains invalid characters: {self.value}. "
                "Only alphanumeric, hyphens, and underscores allowed."
            )
        if self.value != self.value.lower():
            raise ValueError(
                f"FieldDefinitionId must be lowercase: {self.value}"
            )

    def __str__(self) -> str:
        """String representation is the value itself."""
        return self.value


@dataclass(frozen=True)
class EntityDefinitionId(ValueObject):
    """Strongly-typed ID for EntityDefinition.

    Entity IDs are unique within an application schema.
    Convention: lowercase with underscores (e.g., "project", "borehole", "lab_test")

    RULES (ADR-009):
    - Use strongly-typed IDs instead of raw strings
    - IDs are immutable value objects
    - IDs enforce validation rules

    Example:
        entity_id = EntityDefinitionId("project")
        entity_id2 = EntityDefinitionId("borehole")
    """

    value: str

    def __post_init__(self) -> None:
        """Validate entity ID."""
        if not self.value:
            raise ValueError("EntityDefinitionId cannot be empty")
        if not self.value.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"EntityDefinitionId contains invalid characters: {self.value}. "
                "Only alphanumeric, hyphens, and underscores allowed."
            )
        if self.value != self.value.lower():
            raise ValueError(
                f"EntityDefinitionId must be lowercase: {self.value}"
            )

    def __str__(self) -> str:
        """String representation is the value itself."""
        return self.value


@dataclass(frozen=True)
class RelationshipDefinitionId(ValueObject):
    """Strongly-typed ID for RelationshipDefinition (Phase 6A - ADR-022).

    Relationship IDs are unique within an application schema.
    Convention: lowercase with underscores (e.g., "project_contains_boreholes")

    RULES (ADR-009):
    - Use strongly-typed IDs instead of raw strings
    - IDs are immutable value objects
    - IDs enforce validation rules

    Example:
        rel_id = RelationshipDefinitionId("project_contains_boreholes")
        rel_id2 = RelationshipDefinitionId("borehole_references_project")
    """

    value: str

    def __post_init__(self) -> None:
        """Validate relationship ID."""
        if not self.value:
            raise ValueError("RelationshipDefinitionId cannot be empty")
        if not self.value.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"RelationshipDefinitionId contains invalid characters: {self.value}. "
                "Only alphanumeric, hyphens, and underscores allowed."
            )
        if self.value != self.value.lower():
            raise ValueError(
                f"RelationshipDefinitionId must be lowercase: {self.value}"
            )

    def __str__(self) -> str:
        """String representation is the value itself."""
        return self.value

"""RelationshipType enumeration (Phase 6A - ADR-022).

Defines the semantic types of relationships between entities.

NOTE: RelationshipType is DESCRIPTIVE METADATA ONLY.
It does NOT imply runtime traversal, enforcement, cascade behavior,
or any data-level operations. The system does not enforce cardinality
or navigate relationships at runtime.
"""

from enum import Enum


class RelationshipType(Enum):
    """Semantic type of relationship between entities.

    These types describe the conceptual relationship between entities
    for documentation and schema understanding purposes only.

    Values:
        CONTAINS: Parent-child containment (conceptually 1:N)
            Example: Project contains Boreholes
        REFERENCES: Loose reference (conceptually N:1)
            Example: Sample references Lab
        ASSOCIATES: Peer association (conceptually N:M, logical only)
            Example: Test associates with Standard

    IMPORTANT: These are descriptive labels only. The system does NOT:
        - Enforce cardinality at runtime
        - Perform cascade deletes through relationships
        - Navigate or traverse relationships in queries
        - Validate data consistency based on relationship type

    Usage:
        rel_type = RelationshipType.CONTAINS
        if rel_type == RelationshipType.CONTAINS:
            # Display "contains" relationship in UI
    """

    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    ASSOCIATES = "ASSOCIATES"

    def __str__(self) -> str:
        """String representation is the value itself."""
        return self.value

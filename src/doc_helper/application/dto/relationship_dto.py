"""Relationship DTO for UI display.

RULES (AGENT_RULES.md Section 3-4):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)

Moved from get_relationships_query.py for proper DTO organization.
Presentation layer MUST import from here, NOT from query modules.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RelationshipDTO:
    """Data Transfer Object for relationship information.

    Provides a simple, serializable representation of a relationship
    for use in application and presentation layers.
    """

    id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    name_key: str
    description_key: Optional[str]
    inverse_name_key: Optional[str]

"""Schema DTOs for UI display.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FieldOptionDTO:
    """UI-facing field option data for dropdown/radio fields.

    Contains the display-ready option value and label.
    """

    value: str  # Option value
    label: str  # Translated label for display


@dataclass(frozen=True)
class FieldDefinitionDTO:
    """UI-facing field definition data for display.

    This DTO represents a field definition for UI consumption.
    All values are display-ready (translated, formatted).

    FORBIDDEN in this DTO:
    - Domain value objects (FieldDefinitionId, FieldType, TranslationKey)
    - Domain constraints (FieldConstraint instances)
    - Previous values for undo
    """

    id: str  # Field ID as string (from FieldDefinitionId.value)
    field_type: str  # Field type as string (e.g., "TEXT", "NUMBER", "DROPDOWN")
    label: str  # Translated label for display
    help_text: Optional[str]  # Translated help text (or None)
    required: bool  # Whether field is required
    default_value: Optional[str]  # Default value as string (or None)
    options: tuple[FieldOptionDTO, ...]  # Options for choice fields (empty tuple if not choice)
    formula: Optional[str]  # Formula expression (for CALCULATED fields)
    is_calculated: bool  # Whether field is read-only calculated
    is_choice_field: bool  # Whether field has options (dropdown, radio)
    is_collection_field: bool  # Whether field is a table/collection
    lookup_entity_id: Optional[str]  # Entity ID for lookup fields
    child_entity_id: Optional[str]  # Entity ID for table fields


@dataclass(frozen=True)
class EntityDefinitionDTO:
    """UI-facing entity definition data for display.

    This DTO represents an entity definition for UI consumption.
    All values are display-ready (translated).

    FORBIDDEN in this DTO:
    - Domain aggregates (EntityDefinition)
    - Domain value objects (EntityDefinitionId, TranslationKey)
    - Previous values for undo
    """

    id: str  # Entity ID as string (from EntityDefinitionId.value)
    name: str  # Translated entity name for display
    description: Optional[str]  # Translated description (or None)
    name_key: str  # Raw translation key for name (for editing)
    description_key: Optional[str]  # Raw translation key for description (for editing)
    field_count: int  # Number of fields in entity
    is_root_entity: bool  # Whether this is a top-level entity
    parent_entity_id: Optional[str]  # Parent entity ID (or None)
    fields: tuple[FieldDefinitionDTO, ...]  # Field definitions for this entity

"""Field DTOs for UI display.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class FieldValueDTO:
    """UI-facing field value data for display.

    This DTO represents a field's current value for UI consumption.
    Contains display-ready data about the value and its state.

    FORBIDDEN in this DTO:
    - Domain value objects (FieldValue, FieldDefinitionId)
    - Previous values for undo
    - Internal state for restoration
    """

    field_id: str  # Field ID as string (from FieldDefinitionId.value)
    value: Any  # Current value (can be any type)
    display_value: str  # Formatted value for display
    is_computed: bool  # Whether value came from formula
    is_override: bool  # Whether user overrode a computed value
    computed_from: Optional[str]  # Formula expression (if computed)
    has_original_value: bool  # Whether there's an original computed value to restore


@dataclass(frozen=True)
class FieldStateDTO:
    """UI-facing field state combining definition and value.

    This DTO combines field definition metadata with current value state
    for rendering a complete field in the UI.
    """

    # From FieldDefinition
    field_id: str
    field_type: str
    label: str
    help_text: Optional[str]
    required: bool
    is_calculated: bool
    is_choice_field: bool

    # From FieldValue (if exists)
    has_value: bool
    value: Any
    display_value: str
    is_computed: bool
    is_override: bool

    # Validation state
    is_valid: bool
    validation_errors: tuple[str, ...]  # Tuple of error messages

    # Control state
    is_visible: bool
    is_enabled: bool

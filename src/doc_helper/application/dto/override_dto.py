"""Override DTOs for UI display.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)

IMPORTANT (unified_upgrade_plan.md H2):
This is a UI DTO for DISPLAY purposes only.
UndoState DTOs for override undo are in application/undo/.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class OverrideDTO:
    """UI-facing override data for display in dialogs/lists.

    This DTO represents an override for UI consumption.
    It contains display-ready data about the override state.

    FORBIDDEN in this DTO (per unified_upgrade_plan.md H2):
    - Previous values for undo (use UndoOverrideState instead)
    - Raw domain types (Override, OverrideState enum)
    - Internal state for restoration
    """

    id: str  # Override ID as string
    field_id: str  # Field ID as string
    field_label: str  # Human-readable field name (translated)
    system_value: str  # Display-formatted system value
    report_value: str  # Display-formatted report value
    state: str  # "PENDING" | "ACCEPTED" | "SYNCED" | "INVALID"
    can_accept: bool  # Pre-computed: is accept action available?
    can_reject: bool  # Pre-computed: is reject action available?


@dataclass(frozen=True)
class ConflictDTO:
    """UI-facing conflict data for display in conflict resolution dialog.

    Represents a conflict between user override and system-computed values
    (formulas or controls).

    FORBIDDEN in this DTO (per unified_upgrade_plan.md H2):
    - Domain types (ConflictInfo, FieldDefinitionId)
    - Internal resolution state
    """

    field_id: str  # Field ID as string
    field_label: str  # Human-readable field name (translated)
    conflict_type: str  # "formula" | "control" | "formula_control"
    user_value: str  # Display-formatted user override value
    formula_value: str | None  # Display-formatted formula value (if formula conflict)
    control_value: str | None  # Display-formatted control value (if control conflict)
    description: str  # Human-readable conflict description (translated)

"""Internal UndoState DTOs for the undo engine.

RULES (unified_upgrade_plan.md v1.3, H2, ADR-021):
- These DTOs are INTERNAL to Application layer
- NEVER import in presentation/ - use static check to enforce
- NEVER return from queries
- Contains raw values for restoration, NOT display-formatted values
- Stored only in the undo stack

FORBIDDEN:
- Importing in presentation layer
- Returning from query handlers
- Using for UI display
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class UndoFieldState:
    """Internal state captured for field value undo.

    NOT for UI display - contains raw values for restoration.

    RULES (H5 State Capture Specification):
    Captured:
    - field_id: Identify target field
    - previous_value: Value to restore on undo
    - new_value: Value to restore on redo
    - was_formula_computed: Know if previous was formula result
    - timestamp: Debugging, ordering

    NOT Captured:
    - Dependent formula results (recomputed via event cascade)
    - Validation state (recomputed after value change)
    - UI display format (UI layer concern)
    - Widget state (presentation layer concern)
    """

    field_id: str
    previous_value: Any
    new_value: Any
    was_formula_computed: bool
    timestamp: str

    @classmethod
    def create(
        cls,
        field_id: str,
        previous_value: Any,
        new_value: Any,
        was_formula_computed: bool = False,
    ) -> "UndoFieldState":
        """Create UndoFieldState with current timestamp.

        Args:
            field_id: Field identifier as string
            previous_value: Value before change (raw, not formatted)
            new_value: Value after change (raw, not formatted)
            was_formula_computed: True if previous value was from formula

        Returns:
            New UndoFieldState instance
        """
        return cls(
            field_id=field_id,
            previous_value=previous_value,
            new_value=new_value,
            was_formula_computed=was_formula_computed,
            timestamp=datetime.utcnow().isoformat(),
        )


@dataclass(frozen=True)
class UndoOverrideState:
    """Internal state captured for override undo.

    NOT for UI display - contains raw values for restoration.

    RULES (H5 State Capture Specification):
    Captured:
    - override_id: Identify target override
    - field_id: Know which field affected
    - previous_override_state: State to restore on undo
    - previous_field_value: Field value to restore on undo
    - accepted_value: Value to restore on redo
    - affected_formula_fields: Fields that depend on this (for debugging)
    - timestamp: Debugging, ordering

    NOT Captured:
    - Formula recomputation results (recomputed via event cascade)
    - Control visibility changes (recomputed via event cascade)
    - Override DTO display formatting (UI layer concern)
    - Conflict state changes (recomputed from override states)
    """

    override_id: str
    field_id: str
    previous_override_state: str  # "PENDING", "ACCEPTED", etc.
    previous_field_value: Any
    accepted_value: Any
    affected_formula_fields: tuple[str, ...]
    timestamp: str

    @classmethod
    def create(
        cls,
        override_id: str,
        field_id: str,
        previous_override_state: str,
        previous_field_value: Any,
        accepted_value: Any,
        affected_formula_fields: tuple[str, ...] = (),
    ) -> "UndoOverrideState":
        """Create UndoOverrideState with current timestamp.

        Args:
            override_id: Override identifier as string
            field_id: Affected field identifier as string
            previous_override_state: State before action ("PENDING", etc.)
            previous_field_value: Field value before override accepted
            accepted_value: Value after override accepted
            affected_formula_fields: Field IDs that depend on this field

        Returns:
            New UndoOverrideState instance
        """
        return cls(
            override_id=override_id,
            field_id=field_id,
            previous_override_state=previous_override_state,
            previous_field_value=previous_field_value,
            accepted_value=accepted_value,
            affected_formula_fields=affected_formula_fields,
            timestamp=datetime.utcnow().isoformat(),
        )

"""Formula DTOs for UI display.

Phase F-1: Formula Editor (Read-Only, Design-Time)

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior (only computed properties)
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)

PHASE F-1 CONSTRAINTS:
- Read-only with respect to schema
- Used for formula validation display only
- NO execution results
- NO persistence
"""

from dataclasses import dataclass
from enum import Enum


class FormulaResultType(Enum):
    """Inferred result type of a formula expression.

    Used by the Formula Editor to display the expected output type.
    """
    BOOLEAN = "BOOLEAN"
    NUMBER = "NUMBER"
    TEXT = "TEXT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FormulaValidationResultDTO:
    """UI-facing formula validation result for display.

    Represents the validation state of a formula expression.
    Used by the Formula Editor to show live validation feedback.

    Phase F-1: Read-only validation result, no schema mutation.

    FORBIDDEN in this DTO:
    - AST objects (formulas are strings only)
    - Domain value objects
    - Previous validation states for undo
    - Execution results
    """

    is_valid: bool  # Whether formula is syntactically and semantically valid
    errors: tuple[str, ...]  # Error messages (blocking issues)
    warnings: tuple[str, ...]  # Warning messages (non-blocking issues)
    inferred_type: str  # Result type: "BOOLEAN", "NUMBER", "TEXT", "UNKNOWN"
    field_references: tuple[str, ...]  # Field IDs referenced in formula

    @property
    def has_errors(self) -> bool:
        """Check if result contains errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if result contains warnings."""
        return len(self.warnings) > 0

    @property
    def error_count(self) -> int:
        """Get count of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Get count of warnings."""
        return len(self.warnings)

    @property
    def all_messages(self) -> tuple[str, ...]:
        """Get all messages (errors + warnings)."""
        return self.errors + self.warnings


@dataclass(frozen=True)
class SchemaFieldInfoDTO:
    """Minimal field info for formula validation context.

    Used to provide schema field information to the Formula Editor
    without exposing full FieldDefinitionDTO complexity.

    Phase F-1: Read-only schema snapshot for validation.
    """

    field_id: str  # Field ID
    field_type: str  # Field type (TEXT, NUMBER, etc.)
    entity_id: str  # Parent entity ID
    label: str  # Display label (for autocomplete/tooltips)

"""Formula DTOs for UI display.

Phase F-1: Formula Editor (Read-Only, Design-Time)
Phase F-2: Formula Runtime Execution
Phase F-3: Formula Dependency Discovery (Analysis-Only)

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior (only computed properties)
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)

PHASE F-1 CONSTRAINTS:
- Read-only with respect to schema
- Used for formula validation display only
- NO persistence

PHASE F-2 CONSTRAINTS (ADR-040):
- Pure execution results (no side effects)
- No persistence of computed values
- No schema mutation
- No dependency tracking
- Execution is pull-based, not push-based

PHASE F-3 CONSTRAINTS (ADR-040):
- Analysis only (no execution)
- No persistence of dependencies
- No DAG/graph construction
- No cycle detection
- Read-only schema access
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


@dataclass(frozen=True)
class FormulaExecutionResultDTO:
    """UI-facing formula execution result (Phase F-2).

    Represents the result of executing a formula expression
    with runtime field values.

    PHASE F-2 CONSTRAINTS (per ADR-040):
    - Pure execution result (no side effects)
    - No persistence of computed values
    - No schema mutation
    - No dependency tracking
    - Execution is pull-based, not push-based

    FORBIDDEN in this DTO:
    - AST objects (internal implementation)
    - Domain value objects
    - Previous execution states for undo
    - Cached results
    """

    success: bool  # Whether execution succeeded
    value: object  # Computed value (primitive: int, float, str, bool, None)
    error: str | None  # Error message if execution failed

    @property
    def has_error(self) -> bool:
        """Check if execution resulted in an error."""
        return not self.success

    @property
    def is_null(self) -> bool:
        """Check if result value is null."""
        return self.success and self.value is None


# =============================================================================
# PHASE F-3: Formula Dependency Discovery (Analysis-Only)
# =============================================================================


@dataclass(frozen=True)
class FormulaDependencyDTO:
    """UI-facing formula dependency information (Phase F-3).

    Represents a single field dependency discovered in a formula expression.

    PHASE F-3 CONSTRAINTS:
    - Analysis result only (no execution)
    - No persistence
    - No graph/DAG construction
    - Read-only

    FORBIDDEN in this DTO:
    - AST nodes
    - Domain value objects
    - Graph edges or pointers
    - Execution results
    """

    field_id: str  # ID of the referenced field
    is_known: bool  # Whether field exists in schema context
    field_type: str | None  # Field type if known, None if unknown


@dataclass(frozen=True)
class FormulaDependencyAnalysisResultDTO:
    """UI-facing formula dependency analysis result (Phase F-3).

    Represents the complete dependency analysis of a formula expression.
    Identifies all field references and validates against schema context.

    PHASE F-3 CONSTRAINTS:
    - Analysis result only (no execution)
    - Deterministic: same input -> same output
    - No persistence
    - No graph/DAG construction
    - No cycle detection
    - Read-only schema access

    FORBIDDEN in this DTO:
    - AST objects
    - Domain value objects
    - Graph structures
    - Cached results
    - Execution results
    """

    dependencies: tuple[FormulaDependencyDTO, ...]  # All discovered dependencies
    unknown_fields: tuple[str, ...]  # Field IDs not found in schema
    has_parse_error: bool  # Whether formula failed to parse
    parse_error: str | None  # Parse error message if any

    @property
    def has_unknown_fields(self) -> bool:
        """Check if any referenced fields are unknown."""
        return len(self.unknown_fields) > 0

    @property
    def known_dependencies(self) -> tuple[FormulaDependencyDTO, ...]:
        """Get only known (valid) dependencies."""
        return tuple(d for d in self.dependencies if d.is_known)

    @property
    def dependency_count(self) -> int:
        """Get total count of dependencies."""
        return len(self.dependencies)

    @property
    def unknown_count(self) -> int:
        """Get count of unknown field references."""
        return len(self.unknown_fields)

    @property
    def field_ids(self) -> tuple[str, ...]:
        """Get all referenced field IDs."""
        return tuple(d.field_id for d in self.dependencies)

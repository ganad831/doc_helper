"""Formula DTOs for UI display.

Phase F-1: Formula Editor (Read-Only, Design-Time)
Phase F-2: Formula Runtime Execution
Phase F-3: Formula Dependency Discovery (Analysis-Only)
Phase F-4: Formula Cycle Detection (Design-Time Analysis)
Phase F-6: Formula Governance & Enforcement (Policy Decisions)
Phase F-7: Formula Binding & Persistence Rules (Policy Only)

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

PHASE F-4 CONSTRAINTS (ADR-041):
- Analysis only (no execution)
- No persistence of cycle results
- No schema mutation
- No blocking of saves or edits
- Cycles reported, not prevented
- Deterministic: same input -> same output
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


# =============================================================================
# PHASE F-4: Formula Cycle Detection (Design-Time Analysis)
# =============================================================================


@dataclass(frozen=True)
class FormulaCycleDTO:
    """UI-facing formula cycle information (Phase F-4).

    Represents a single dependency cycle detected in formula fields.

    PHASE F-4 CONSTRAINTS (ADR-041):
    - Analysis result only (no execution)
    - No persistence
    - No schema mutation
    - Non-blocking (informs, does not prevent)
    - Deterministic output

    FORBIDDEN in this DTO:
    - AST nodes
    - Domain value objects
    - Graph edges or pointers
    - Execution results
    - Blocking logic
    """

    field_ids: tuple[str, ...]  # Fields forming the cycle, in order
    cycle_path: str  # Human-readable path (e.g., "A → B → C → A")
    severity: str  # Always "ERROR" for cycles

    @property
    def cycle_length(self) -> int:
        """Get number of fields in the cycle."""
        return len(self.field_ids)

    @property
    def is_self_reference(self) -> bool:
        """Check if this is a self-referential cycle (A → A)."""
        return len(self.field_ids) == 1


@dataclass(frozen=True)
class FormulaCycleAnalysisResultDTO:
    """UI-facing formula cycle analysis result (Phase F-4).

    Represents the complete cycle analysis of formula dependencies
    within a single entity.

    PHASE F-4 CONSTRAINTS (ADR-041):
    - Analysis result only (no execution)
    - Deterministic: same input -> same output
    - No persistence
    - No schema mutation
    - Non-blocking (informs, does not prevent saves)
    - Same-entity scope only (no cross-entity cycles)

    FORBIDDEN in this DTO:
    - AST objects
    - Domain value objects
    - Graph structures (stored)
    - Cached results
    - Execution results
    - Blocking flags
    """

    has_cycles: bool  # Whether any cycle was detected
    cycles: tuple[FormulaCycleDTO, ...]  # All detected cycles
    analyzed_field_count: int  # Number of formula fields analyzed

    @property
    def cycle_count(self) -> int:
        """Get number of cycles detected."""
        return len(self.cycles)

    @property
    def all_cycle_field_ids(self) -> tuple[str, ...]:
        """Get all field IDs involved in any cycle."""
        all_ids: set[str] = set()
        for cycle in self.cycles:
            all_ids.update(cycle.field_ids)
        return tuple(sorted(all_ids))

    @property
    def cycle_errors(self) -> tuple[str, ...]:
        """Get all cycle paths as error messages."""
        return tuple(f"Circular dependency: {c.cycle_path}" for c in self.cycles)


# =============================================================================
# PHASE F-6: Formula Governance & Enforcement (Policy Decisions)
# =============================================================================


class FormulaGovernanceStatus(Enum):
    """Governance status for a formula (Phase F-6).

    Represents the overall acceptability of a formula based on
    existing diagnostics from F-1 through F-4.

    PHASE F-6 CONSTRAINTS:
    - Policy decision only (no new analysis)
    - Deterministic: same diagnostics -> same status
    - No execution
    - No persistence
    - No schema mutation
    """

    EMPTY = "EMPTY"  # No formula text (neutral, not blocked)
    INVALID = "INVALID"  # Blocked due to errors (syntax, unknown fields, cycles)
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"  # Allowed but has warnings
    VALID = "VALID"  # Fully valid, no issues


@dataclass(frozen=True)
class FormulaGovernanceResultDTO:
    """UI-facing formula governance decision (Phase F-6).

    Represents the governance evaluation of a formula based on
    existing diagnostics. Determines whether a formula is allowed
    to be saved, exported, or accepted as schema-valid.

    PHASE F-6 CONSTRAINTS:
    - Policy evaluation only (no new analysis)
    - Deterministic: same input -> same output
    - No execution
    - No persistence
    - No schema mutation
    - No blocking of saves (informational only)

    FORBIDDEN in this DTO:
    - AST objects
    - Domain value objects
    - Execution results
    - New diagnostic analysis
    - Cached results

    Governance Rules:
    - INVALID: Syntax errors, unknown fields, or cycles exist
    - VALID_WITH_WARNINGS: No blocking issues but has type warnings
    - VALID: No errors and no warnings
    - EMPTY: No formula text (neutral)
    """

    status: FormulaGovernanceStatus  # Overall governance status
    blocking_reasons: tuple[str, ...]  # Reasons formula is blocked (if any)
    warning_reasons: tuple[str, ...]  # Non-blocking warnings (if any)

    @property
    def is_allowed(self) -> bool:
        """Check if formula is allowed (not blocked).

        A formula is allowed if it has status EMPTY, VALID, or VALID_WITH_WARNINGS.
        Only INVALID status blocks the formula.
        """
        return self.status != FormulaGovernanceStatus.INVALID

    @property
    def is_blocked(self) -> bool:
        """Check if formula is blocked.

        A formula is blocked only if it has INVALID status.
        """
        return self.status == FormulaGovernanceStatus.INVALID

    @property
    def is_empty(self) -> bool:
        """Check if formula is empty (neutral state)."""
        return self.status == FormulaGovernanceStatus.EMPTY

    @property
    def is_valid(self) -> bool:
        """Check if formula is fully valid (no errors, no warnings)."""
        return self.status == FormulaGovernanceStatus.VALID

    @property
    def has_warnings(self) -> bool:
        """Check if formula has warnings."""
        return len(self.warning_reasons) > 0

    @property
    def blocking_count(self) -> int:
        """Get count of blocking reasons."""
        return len(self.blocking_reasons)

    @property
    def warning_count(self) -> int:
        """Get count of warning reasons."""
        return len(self.warning_reasons)

    @property
    def summary_message(self) -> str:
        """Get human-readable governance summary.

        Returns a concise message describing the governance decision.
        """
        if self.status == FormulaGovernanceStatus.EMPTY:
            return ""
        elif self.status == FormulaGovernanceStatus.INVALID:
            return f"Formula blocked: {self.blocking_count} issue(s)"
        elif self.status == FormulaGovernanceStatus.VALID_WITH_WARNINGS:
            return f"Formula valid with {self.warning_count} warning(s)"
        else:
            return "Formula is valid"


# =============================================================================
# PHASE F-7: Formula Binding & Persistence Rules (Policy Only)
# =============================================================================


class FormulaBindingTarget(Enum):
    """Target types for formula binding (Phase F-7).

    Defines the schema elements that can own a formula.

    PHASE F-7 CONSTRAINTS:
    - Policy definition only (no execution)
    - No persistence
    - No schema mutation
    - Deterministic binding rules

    Allowed Targets (v1):
    - CALCULATED_FIELD: Formula bound to a calculated field (ALLOWED)

    Future Targets (NOT implemented):
    - VALIDATION_RULE: Formula for custom validation (FORBIDDEN in F-7)
    - OUTPUT_MAPPING: Formula for output transformation (FORBIDDEN in F-7)
    """

    CALCULATED_FIELD = "CALCULATED_FIELD"  # Allowed in F-7
    VALIDATION_RULE = "VALIDATION_RULE"  # Placeholder - FORBIDDEN in F-7
    OUTPUT_MAPPING = "OUTPUT_MAPPING"  # Placeholder - FORBIDDEN in F-7


class FormulaBindingStatus(Enum):
    """Status of a formula binding attempt (Phase F-7).

    Represents the result of checking whether a formula can be bound
    to a specific target.

    PHASE F-7 CONSTRAINTS:
    - Policy decision only
    - No persistence
    - No execution
    - Deterministic
    """

    ALLOWED = "ALLOWED"  # Binding is permitted
    BLOCKED_INVALID_FORMULA = "BLOCKED_INVALID_FORMULA"  # Formula has errors
    BLOCKED_UNSUPPORTED_TARGET = "BLOCKED_UNSUPPORTED_TARGET"  # Target type not allowed
    CLEARED = "CLEARED"  # Formula was empty (binding cleared)


@dataclass(frozen=True)
class FormulaBindingDTO:
    """UI-facing formula binding information (Phase F-7).

    Represents a formula bound to a specific schema element.
    This is a policy/wiring DTO - NO persistence, NO execution.

    PHASE F-7 CONSTRAINTS:
    - Policy representation only
    - No persistence of bindings
    - No execution triggers
    - No schema mutation
    - No domain objects
    - Strings and primitives only

    FORBIDDEN in this DTO:
    - AST objects
    - Domain value objects
    - Persistence identifiers
    - Execution state
    - Observer/listener references
    """

    target_type: FormulaBindingTarget  # What kind of element owns this formula
    target_id: str  # ID of the owning element (field_id, rule_id, etc.)
    formula_text: str  # The formula expression text
    governance_status: FormulaGovernanceStatus  # Governance status from F-6

    @property
    def is_bound(self) -> bool:
        """Check if formula is actively bound (non-empty)."""
        return bool(self.formula_text and self.formula_text.strip())

    @property
    def is_valid_binding(self) -> bool:
        """Check if binding is valid (non-blocked governance)."""
        return self.governance_status != FormulaGovernanceStatus.INVALID

    @property
    def is_empty(self) -> bool:
        """Check if binding has no formula (cleared state)."""
        return not self.formula_text or not self.formula_text.strip()


@dataclass(frozen=True)
class FormulaBindingResultDTO:
    """UI-facing formula binding operation result (Phase F-7).

    Represents the result of a bind/unbind operation.

    PHASE F-7 CONSTRAINTS:
    - Policy result only (no persistence)
    - Deterministic: same input -> same output
    - No execution
    - No schema mutation

    FORBIDDEN in this DTO:
    - AST objects
    - Domain value objects
    - Persistence state
    - Execution triggers
    """

    status: FormulaBindingStatus  # Result status
    binding: FormulaBindingDTO | None  # The binding if successful, None if blocked
    block_reason: str | None  # Reason for blocking (if blocked)

    @property
    def is_allowed(self) -> bool:
        """Check if binding operation was allowed."""
        return self.status in (
            FormulaBindingStatus.ALLOWED,
            FormulaBindingStatus.CLEARED,
        )

    @property
    def is_blocked(self) -> bool:
        """Check if binding operation was blocked."""
        return self.status in (
            FormulaBindingStatus.BLOCKED_INVALID_FORMULA,
            FormulaBindingStatus.BLOCKED_UNSUPPORTED_TARGET,
        )

    @property
    def is_cleared(self) -> bool:
        """Check if binding was cleared (empty formula)."""
        return self.status == FormulaBindingStatus.CLEARED

    @property
    def status_message(self) -> str:
        """Get human-readable status message."""
        if self.status == FormulaBindingStatus.ALLOWED:
            return "Formula binding allowed"
        elif self.status == FormulaBindingStatus.CLEARED:
            return "Formula binding cleared"
        elif self.status == FormulaBindingStatus.BLOCKED_INVALID_FORMULA:
            return f"Binding blocked: {self.block_reason or 'Invalid formula'}"
        elif self.status == FormulaBindingStatus.BLOCKED_UNSUPPORTED_TARGET:
            return f"Binding blocked: {self.block_reason or 'Unsupported target type'}"
        else:
            return "Unknown binding status"

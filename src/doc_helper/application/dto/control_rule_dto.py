"""Control Rule DTOs for UI display.

Phase F-8: Control Rules (Boolean Formulas Only)

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior (only computed properties)
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)

PHASE F-8 CONSTRAINTS:
- Control Rules use BOOLEAN formulas only
- Non-boolean result type -> Rule BLOCKED
- Read-only with respect to schema
- NO persistence
- NO execution against real data
- NO runtime observers
- NO DAG building
- NO schema mutation
- Reuse FormulaUseCases for validation, dependency, cycle, governance
"""

from dataclasses import dataclass
from enum import Enum

from doc_helper.application.dto.formula_dto import (
    FormulaGovernanceStatus,
    FormulaValidationResultDTO,
    FormulaDependencyAnalysisResultDTO,
    FormulaCycleAnalysisResultDTO,
    FormulaGovernanceResultDTO,
)


class ControlRuleType(Enum):
    """Type of control rule (Phase F-8).

    Defines the UI behavior that a control rule governs.

    PHASE F-8 CONSTRAINTS:
    - UI behavior governance only
    - No data mutation
    - No execution
    - Boolean formulas only

    Rule Types:
    - VISIBILITY: Controls whether a field is visible
    - ENABLED: Controls whether a field is enabled/disabled
    - REQUIRED: Controls whether a field is required
    """

    VISIBILITY = "VISIBILITY"
    ENABLED = "ENABLED"
    REQUIRED = "REQUIRED"


class ControlRuleStatus(Enum):
    """Status of a control rule (Phase F-8).

    Represents the result of evaluating whether a control rule is valid.

    PHASE F-8 CONSTRAINTS:
    - Policy decision only (no execution)
    - Deterministic: same input -> same output
    - No persistence
    - No schema mutation

    Status Values:
    - ALLOWED: Rule is valid and can be applied
    - BLOCKED: Rule is invalid (non-boolean, errors, governance failed)
    - CLEARED: Rule was empty (no formula)
    """

    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    CLEARED = "CLEARED"


@dataclass(frozen=True)
class ControlRuleDiagnosticsDTO:
    """UI-facing control rule diagnostics (Phase F-8).

    Aggregates all diagnostic information from the underlying formula
    analysis phases (F-1 through F-6).

    PHASE F-8 CONSTRAINTS:
    - Aggregation of existing diagnostics only
    - No new analysis
    - No persistence
    - No execution
    - Deterministic

    FORBIDDEN in this DTO:
    - AST objects
    - Domain value objects
    - Execution results
    - New diagnostic analysis
    """

    validation_result: FormulaValidationResultDTO | None
    dependency_result: FormulaDependencyAnalysisResultDTO | None
    cycle_result: FormulaCycleAnalysisResultDTO | None
    governance_result: FormulaGovernanceResultDTO | None

    @property
    def has_validation(self) -> bool:
        """Check if validation result exists."""
        return self.validation_result is not None

    @property
    def has_dependencies(self) -> bool:
        """Check if dependency analysis result exists."""
        return self.dependency_result is not None

    @property
    def has_cycle_analysis(self) -> bool:
        """Check if cycle analysis result exists."""
        return self.cycle_result is not None

    @property
    def has_governance(self) -> bool:
        """Check if governance result exists."""
        return self.governance_result is not None

    @property
    def inferred_type(self) -> str:
        """Get inferred formula type from validation."""
        if self.validation_result:
            return self.validation_result.inferred_type
        return "UNKNOWN"

    @property
    def is_boolean(self) -> bool:
        """Check if formula infers to BOOLEAN type."""
        return self.inferred_type == "BOOLEAN"

    @property
    def error_count(self) -> int:
        """Get total error count from all diagnostics."""
        count = 0
        if self.validation_result:
            count += self.validation_result.error_count
        if self.cycle_result and self.cycle_result.has_cycles:
            count += self.cycle_result.cycle_count
        return count

    @property
    def warning_count(self) -> int:
        """Get total warning count from all diagnostics."""
        if self.validation_result:
            return self.validation_result.warning_count
        return 0


@dataclass(frozen=True)
class ControlRuleDTO:
    """UI-facing control rule information (Phase F-8).

    Represents a control rule with its formula and diagnostics.
    This is a policy/display DTO - NO persistence, NO execution.

    PHASE F-8 CONSTRAINTS:
    - Policy representation only
    - No persistence
    - No execution against real data
    - No runtime observers
    - No schema mutation
    - Boolean formulas only (non-boolean -> BLOCKED)

    FORBIDDEN in this DTO:
    - AST objects
    - Domain value objects
    - Persistence identifiers
    - Execution state
    - Observer/listener references
    """

    rule_type: ControlRuleType  # What UI behavior this rule controls
    target_field_id: str  # ID of the field this rule applies to
    formula_text: str  # The boolean formula expression
    diagnostics: ControlRuleDiagnosticsDTO | None  # Aggregated diagnostics

    @property
    def is_empty(self) -> bool:
        """Check if rule has no formula (cleared state)."""
        return not self.formula_text or not self.formula_text.strip()

    @property
    def has_diagnostics(self) -> bool:
        """Check if diagnostics are available."""
        return self.diagnostics is not None

    @property
    def governance_status(self) -> FormulaGovernanceStatus | None:
        """Get governance status from diagnostics."""
        if self.diagnostics and self.diagnostics.governance_result:
            return self.diagnostics.governance_result.status
        return None

    @property
    def inferred_type(self) -> str:
        """Get inferred formula type."""
        if self.diagnostics:
            return self.diagnostics.inferred_type
        return "UNKNOWN"

    @property
    def is_boolean_formula(self) -> bool:
        """Check if formula is boolean type."""
        if self.diagnostics:
            return self.diagnostics.is_boolean
        return False


@dataclass(frozen=True)
class ControlRuleResultDTO:
    """UI-facing control rule operation result (Phase F-8).

    Represents the result of validating or applying a control rule.

    PHASE F-8 CONSTRAINTS:
    - Policy result only (no persistence)
    - Deterministic: same input -> same output
    - No execution against real data
    - No schema mutation
    - Boolean enforcement: non-boolean -> BLOCKED

    FORBIDDEN in this DTO:
    - AST objects
    - Domain value objects
    - Persistence state
    - Execution triggers
    """

    status: ControlRuleStatus  # Result status
    rule: ControlRuleDTO | None  # The rule if successful, None if empty
    block_reason: str | None  # Reason for blocking (if blocked)

    @property
    def is_allowed(self) -> bool:
        """Check if rule operation was allowed."""
        return self.status == ControlRuleStatus.ALLOWED

    @property
    def is_blocked(self) -> bool:
        """Check if rule operation was blocked."""
        return self.status == ControlRuleStatus.BLOCKED

    @property
    def is_cleared(self) -> bool:
        """Check if rule was cleared (empty formula)."""
        return self.status == ControlRuleStatus.CLEARED

    @property
    def governance_status(self) -> FormulaGovernanceStatus | None:
        """Get governance status from underlying rule."""
        if self.rule:
            return self.rule.governance_status
        return None

    @property
    def diagnostics(self) -> ControlRuleDiagnosticsDTO | None:
        """Get diagnostics from underlying rule."""
        if self.rule:
            return self.rule.diagnostics
        return None

    @property
    def status_message(self) -> str:
        """Get human-readable status message."""
        if self.status == ControlRuleStatus.ALLOWED:
            return "Control rule is valid"
        elif self.status == ControlRuleStatus.CLEARED:
            return "Control rule cleared"
        elif self.status == ControlRuleStatus.BLOCKED:
            return f"Control rule blocked: {self.block_reason or 'Invalid formula'}"
        else:
            return "Unknown control rule status"

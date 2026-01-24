"""Control Rule Editor ViewModel (Phase F-8: Control Rules).

Manages presentation state for the Control Rule Editor UI.
Control Rules use BOOLEAN formulas only to govern UI behavior.

PHASE F-8 SCOPE:
- Hold control rule state (rule_type, formula_text, target_field_id)
- Validate formula for boolean requirement
- Expose diagnostics, governance status
- Expose is_rule_allowed, blocking_reason
- Provide clear_rule() method

PHASE F-8 CONSTRAINTS:
- Control Rules use BOOLEAN formulas only
- Non-boolean result type -> Rule BLOCKED
- Read-only with respect to schema
- NO persistence
- NO execution against real data
- NO runtime observers
- NO DAG building
- NO schema mutation

ARCHITECTURE ENFORCEMENT (Rule 0 Compliance):
- ViewModel depends ONLY on ControlRuleUseCases (Application layer use-case)
- NO command imports
- NO query imports
- NO repository access
- NO domain object imports
- Schema passed as DTOs (read-only snapshot)
"""

from typing import Optional

from doc_helper.application.dto.control_rule_dto import (
    ControlRuleDiagnosticsDTO,
    ControlRuleDTO,
    ControlRuleResultDTO,
    ControlRuleStatus,
    ControlRuleType,
)
from doc_helper.application.dto.formula_dto import (
    FormulaGovernanceStatus,
    SchemaFieldInfoDTO,
)
from doc_helper.application.usecases.control_rule_usecases import ControlRuleUseCases
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


class ControlRuleEditorViewModel(BaseViewModel):
    """ViewModel for Control Rule Editor.

    Responsibilities:
    - Hold control rule state (rule_type, formula_text, target_field_id)
    - Perform validation via use-case (boolean enforcement)
    - Expose validation result and diagnostics to UI
    - Track available fields from schema
    - Expose governance evaluation
    - Provide clear_rule() method

    Phase F-8 Compliance:
    - Read-only schema access (DTOs)
    - No schema mutation
    - No formula execution against real data
    - No persistence
    - Boolean-only enforcement

    Usage:
        vm = ControlRuleEditorViewModel(control_rule_usecases)
        vm.set_schema_context(schema_fields)
        vm.set_rule_type(ControlRuleType.VISIBILITY)
        vm.set_target_field_id("secret_field")
        vm.set_formula("is_admin == true")

        if vm.is_rule_allowed:
            # Valid boolean formula
            rule = vm.get_rule_result().rule
        else:
            # Show blocking reason
            print(vm.blocking_reason)

    Observable Properties:
        - rule_type: Current rule type (VISIBILITY, ENABLED, REQUIRED)
        - target_field_id: ID of the field this rule applies to
        - formula_text: Current formula text
        - is_rule_allowed: Whether rule is valid and allowed
        - is_rule_blocked: Whether rule is blocked
        - is_rule_cleared: Whether rule is cleared (empty)
        - blocking_reason: Reason rule is blocked (if any)
        - diagnostics: Aggregated diagnostics DTO
        - governance_status: Governance status enum value
        - inferred_type: Inferred formula type (should be BOOLEAN)
        - is_boolean_formula: Whether formula is boolean type
        - status_message: Human-readable status message
        - error_count: Total error count
        - warning_count: Total warning count
    """

    def __init__(
        self,
        control_rule_usecases: ControlRuleUseCases,
    ) -> None:
        """Initialize Control Rule Editor ViewModel.

        Args:
            control_rule_usecases: Use-case class for control rule validation

        Architecture Compliance:
            ViewModel receives ONLY use-case class via DI.
            NO commands, queries, or repositories are injected.
        """
        super().__init__()
        self._control_rule_usecases = control_rule_usecases

        # State
        self._rule_type: ControlRuleType = ControlRuleType.VISIBILITY
        self._target_field_id: str = ""
        self._formula_text: str = ""
        self._rule_result: Optional[ControlRuleResultDTO] = None
        self._schema_fields: tuple[SchemaFieldInfoDTO, ...] = ()

    # =========================================================================
    # Properties (Observable)
    # =========================================================================

    @property
    def rule_type(self) -> ControlRuleType:
        """Get current rule type."""
        return self._rule_type

    @property
    def target_field_id(self) -> str:
        """Get target field ID."""
        return self._target_field_id

    @property
    def formula_text(self) -> str:
        """Get current formula text."""
        return self._formula_text

    @property
    def has_formula(self) -> bool:
        """Check if formula text is non-empty."""
        return bool(self._formula_text.strip())

    @property
    def rule_result(self) -> Optional[ControlRuleResultDTO]:
        """Get latest rule validation result."""
        return self._rule_result

    @property
    def is_rule_allowed(self) -> bool:
        """Check if rule is valid and allowed (Phase F-8).

        A rule is allowed if:
        - Formula is valid BOOLEAN type
        - Governance passes (VALID or VALID_WITH_WARNINGS)

        Returns:
            True if rule is allowed
        """
        if self._rule_result is None:
            return False
        return self._rule_result.is_allowed

    @property
    def is_rule_blocked(self) -> bool:
        """Check if rule is blocked (Phase F-8).

        A rule is blocked if:
        - Formula has errors (syntax, unknown fields, cycles)
        - Formula is not BOOLEAN type
        - Governance status is INVALID

        Returns:
            True if rule is blocked
        """
        if self._rule_result is None:
            return False
        return self._rule_result.is_blocked

    @property
    def is_rule_cleared(self) -> bool:
        """Check if rule is cleared (empty formula).

        Returns:
            True if rule has no formula (cleared state)
        """
        if self._rule_result is None:
            return not self.has_formula
        return self._rule_result.is_cleared

    @property
    def blocking_reason(self) -> Optional[str]:
        """Get reason why rule is blocked (Phase F-8).

        Returns:
            Block reason string, or None if rule is allowed/cleared
        """
        if self._rule_result is None:
            return None
        return self._rule_result.block_reason

    @property
    def diagnostics(self) -> Optional[ControlRuleDiagnosticsDTO]:
        """Get aggregated diagnostics (Phase F-8).

        Returns:
            ControlRuleDiagnosticsDTO or None if not validated
        """
        if self._rule_result is None or self._rule_result.rule is None:
            return None
        return self._rule_result.rule.diagnostics

    @property
    def governance_status(self) -> Optional[FormulaGovernanceStatus]:
        """Get governance status (Phase F-8).

        Returns:
            FormulaGovernanceStatus or None if not validated
        """
        if self._rule_result is None or self._rule_result.rule is None:
            return None
        return self._rule_result.rule.governance_status

    @property
    def inferred_type(self) -> str:
        """Get inferred formula type.

        Should be BOOLEAN for valid control rules.

        Returns:
            Inferred type string (BOOLEAN, NUMBER, TEXT, UNKNOWN)
        """
        if self._rule_result is None or self._rule_result.rule is None:
            return "UNKNOWN"
        return self._rule_result.rule.inferred_type

    @property
    def is_boolean_formula(self) -> bool:
        """Check if formula is BOOLEAN type (Phase F-8 requirement).

        Returns:
            True if formula infers to BOOLEAN type
        """
        return self.inferred_type == "BOOLEAN"

    @property
    def status_message(self) -> str:
        """Get human-readable status message (Phase F-8).

        Returns a concise status message suitable for inline display.
        """
        if self._rule_result is None:
            return ""

        return self._rule_result.status_message

    @property
    def error_count(self) -> int:
        """Get total error count from diagnostics."""
        diagnostics = self.diagnostics
        if diagnostics is None:
            return 0
        return diagnostics.error_count

    @property
    def warning_count(self) -> int:
        """Get total warning count from diagnostics."""
        diagnostics = self.diagnostics
        if diagnostics is None:
            return 0
        return diagnostics.warning_count

    @property
    def available_fields(self) -> tuple[SchemaFieldInfoDTO, ...]:
        """Get available schema fields for autocomplete."""
        return self._schema_fields

    @property
    def rule_status(self) -> ControlRuleStatus:
        """Get current rule status.

        Returns:
            ControlRuleStatus enum value
        """
        if self._rule_result is None:
            if not self.has_formula:
                return ControlRuleStatus.CLEARED
            return ControlRuleStatus.BLOCKED
        return self._rule_result.status

    # =========================================================================
    # Commands (User Actions)
    # =========================================================================

    def set_schema_context(
        self,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Set schema context for validation.

        This provides the schema snapshot for formula validation.
        Must be called before validation can check field references.

        Args:
            schema_fields: Read-only schema field snapshot (DTOs)

        Phase F-8 Compliance:
            Schema is passed as DTOs (read-only snapshot).
            No schema mutation occurs.
        """
        self._schema_fields = schema_fields
        self.notify_change("available_fields")

        # Re-validate if formula exists
        if self._formula_text.strip():
            self._validate_rule()

    def set_rule_type(self, rule_type: ControlRuleType) -> None:
        """Set the control rule type.

        Args:
            rule_type: Type of control rule (VISIBILITY, ENABLED, REQUIRED)
        """
        self._rule_type = rule_type
        self.notify_change("rule_type")

        # Re-validate if formula exists
        if self._formula_text.strip():
            self._validate_rule()

    def set_target_field_id(self, target_field_id: str) -> None:
        """Set the target field ID.

        Args:
            target_field_id: ID of the field this rule applies to
        """
        self._target_field_id = target_field_id
        self.notify_change("target_field_id")

        # Re-validate if formula exists
        if self._formula_text.strip():
            self._validate_rule()

    def set_formula(self, formula_text: str) -> None:
        """Set formula text and validate.

        Args:
            formula_text: New formula text (must be BOOLEAN type)

        Triggers validation and notifies all observers.
        """
        self._formula_text = formula_text
        self.notify_change("formula_text")
        self.notify_change("has_formula")

        # Validate the rule
        self._validate_rule()

    def clear_rule(self) -> ControlRuleResultDTO:
        """Clear the control rule (Phase F-8).

        Clears the formula text and returns a CLEARED result.

        Returns:
            ControlRuleResultDTO with CLEARED status
        """
        self._formula_text = ""
        self._rule_result = self._control_rule_usecases.clear_control_rule(
            rule_type=self._rule_type,
            target_field_id=self._target_field_id,
        )

        # Notify all observers
        self._notify_all_changes()

        return self._rule_result

    def get_rule_result(self) -> ControlRuleResultDTO:
        """Get the current rule validation result.

        Returns:
            ControlRuleResultDTO with current validation state

        Usage:
            result = vm.get_rule_result()
            if result.is_allowed:
                rule = result.rule
                # Use rule DTO
            elif result.is_blocked:
                print(result.block_reason)
        """
        if self._rule_result is not None:
            return self._rule_result

        # Return cleared result if no formula
        if not self.has_formula:
            return ControlRuleResultDTO(
                status=ControlRuleStatus.CLEARED,
                rule=None,
                block_reason=None,
            )

        # Trigger validation if not yet validated
        self._validate_rule()
        return self._rule_result or ControlRuleResultDTO(
            status=ControlRuleStatus.BLOCKED,
            rule=None,
            block_reason="Validation failed",
        )

    def validate(self) -> ControlRuleResultDTO:
        """Manually trigger validation.

        Returns:
            ControlRuleResultDTO with validation results
        """
        self._validate_rule()
        return self.get_rule_result()

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _validate_rule(self) -> None:
        """Validate current rule via use-case.

        Internal method that:
        1. Calls use-case for validation (boolean enforcement)
        2. Updates rule result state
        3. Notifies all relevant observers
        """
        self._rule_result = self._control_rule_usecases.validate_control_rule(
            rule_type=self._rule_type,
            target_field_id=self._target_field_id,
            formula_text=self._formula_text,
            schema_fields=self._schema_fields,
        )

        # Notify all observers
        self._notify_all_changes()

    def _notify_all_changes(self) -> None:
        """Notify all property change observers."""
        self.notify_change("formula_text")
        self.notify_change("has_formula")
        self.notify_change("rule_result")
        self.notify_change("is_rule_allowed")
        self.notify_change("is_rule_blocked")
        self.notify_change("is_rule_cleared")
        self.notify_change("blocking_reason")
        self.notify_change("diagnostics")
        self.notify_change("governance_status")
        self.notify_change("inferred_type")
        self.notify_change("is_boolean_formula")
        self.notify_change("status_message")
        self.notify_change("error_count")
        self.notify_change("warning_count")
        self.notify_change("rule_status")

    def dispose(self) -> None:
        """Clean up resources."""
        super().dispose()
        self._formula_text = ""
        self._rule_result = None
        self._schema_fields = ()
        self._target_field_id = ""

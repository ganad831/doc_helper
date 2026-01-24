"""Control Rule Use Cases (Phase F-8).

Application layer use-case class for control rule operations.
Control Rules use BOOLEAN formulas only to govern UI behavior.

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

ARCHITECTURE COMPLIANCE:
- ControlRuleUseCases delegates to FormulaUseCases (no duplication)
- ViewModel calls ONLY use-case methods
- Returns DTOs to Presentation
- No domain object exposure
"""

from typing import Any

from doc_helper.application.dto.control_rule_dto import (
    ControlRuleDiagnosticsDTO,
    ControlRuleDTO,
    ControlRuleResultDTO,
    ControlRuleStatus,
    ControlRuleType,
)
from doc_helper.application.dto.control_rule_preview_dto import (
    ControlRulePreviewInputDTO,
    ControlRulePreviewResultDTO,
)
from doc_helper.application.dto.formula_dto import (
    FormulaGovernanceStatus,
    FormulaResultType,
    SchemaFieldInfoDTO,
)
from doc_helper.application.usecases.formula_usecases import FormulaUseCases


class ControlRuleUseCases:
    """Use-case class for control rule validation and management.

    Provides control rule operations using BOOLEAN formulas only.
    Delegates all formula analysis to FormulaUseCases.

    PHASE F-8 SCOPE:
    - validate_control_rule(): Validate formula and check boolean requirement
    - can_apply_control_rule(): Check if rule can be applied
    - clear_control_rule(): Clear/remove a control rule

    FORBIDDEN OPERATIONS:
    - Persistence
    - Execution against real data
    - Runtime observers
    - DAG building
    - Schema mutation
    - Duplication of formula logic

    Usage in ViewModel:
        usecases = ControlRuleUseCases()
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="field_name",
            formula_text="is_admin == true",
            schema_fields=schema_fields
        )
        if result.is_allowed:
            # Rule is valid boolean formula
            pass
        elif result.is_blocked:
            # Show block reason
            print(result.block_reason)

    Boolean Enforcement:
        - Formula MUST infer BOOLEAN result type
        - Non-boolean formula -> BLOCKED with reason
        - Empty formula -> CLEARED (no rule)

    Governance Integration:
        - INVALID governance -> BLOCKED
        - VALID or VALID_WITH_WARNINGS with BOOLEAN type -> ALLOWED
        - EMPTY governance -> CLEARED
    """

    def __init__(
        self,
        formula_usecases: FormulaUseCases | None = None,
    ) -> None:
        """Initialize ControlRuleUseCases.

        Args:
            formula_usecases: FormulaUseCases instance for formula validation.
                If None, creates a new instance.
        """
        self._formula_usecases = formula_usecases or FormulaUseCases()

    def validate_control_rule(
        self,
        rule_type: ControlRuleType,
        target_field_id: str,
        formula_text: str,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
        formula_dependencies: dict[str, tuple[str, ...]] | None = None,
    ) -> ControlRuleResultDTO:
        """Validate a control rule formula.

        Performs full validation including:
        1. Formula syntax and semantic validation (via FormulaUseCases)
        2. Dependency analysis (via FormulaUseCases)
        3. Cycle detection (via FormulaUseCases, if dependencies provided)
        4. Governance evaluation (via FormulaUseCases)
        5. BOOLEAN type enforcement (Phase F-8 requirement)

        Args:
            rule_type: Type of control rule (VISIBILITY, ENABLED, REQUIRED)
            target_field_id: ID of the field this rule applies to
            formula_text: Boolean formula expression
            schema_fields: Read-only schema field snapshot (DTOs)
            formula_dependencies: Optional dependency map for cycle detection

        Returns:
            ControlRuleResultDTO with:
            - status: ALLOWED, BLOCKED, or CLEARED
            - rule: ControlRuleDTO if allowed, None otherwise
            - block_reason: Reason if blocked

        Boolean Enforcement:
            Formula MUST infer BOOLEAN result type.
            Non-boolean formula returns BLOCKED with reason.

        Example:
            result = usecases.validate_control_rule(
                rule_type=ControlRuleType.VISIBILITY,
                target_field_id="secret_field",
                formula_text="user_role == 'admin'",
                schema_fields=schema_fields
            )
            if result.is_allowed:
                # Valid boolean formula
                pass

        Phase F-8 Compliance:
            - Read-only schema access (DTOs)
            - No schema mutation
            - No execution against real data
            - No persistence
            - Deterministic: same input -> same output
            - Returns DTO only
        """
        # Handle empty formula -> CLEARED
        if not formula_text or not formula_text.strip():
            return ControlRuleResultDTO(
                status=ControlRuleStatus.CLEARED,
                rule=None,
                block_reason=None,
            )

        # Step 1: Validate formula (Phase F-1)
        validation_result = self._formula_usecases.validate_formula(
            formula_text=formula_text,
            schema_fields=schema_fields,
        )

        # Step 2: Analyze dependencies (Phase F-3)
        dependency_result = self._formula_usecases.analyze_dependencies(
            formula_text=formula_text,
            schema_fields=schema_fields,
        )

        # Step 3: Detect cycles if dependencies provided (Phase F-4)
        cycle_result = None
        if formula_dependencies is not None:
            cycle_result = self._formula_usecases.detect_cycles(
                formula_dependencies=formula_dependencies,
            )

        # Step 4: Evaluate governance (Phase F-6)
        governance_result = self._formula_usecases.evaluate_governance(
            formula_text=formula_text,
            validation_result=validation_result,
            cycle_result=cycle_result,
        )

        # Build diagnostics DTO
        diagnostics = ControlRuleDiagnosticsDTO(
            validation_result=validation_result,
            dependency_result=dependency_result,
            cycle_result=cycle_result,
            governance_result=governance_result,
        )

        # Step 5: Check governance status
        if governance_result.status == FormulaGovernanceStatus.INVALID:
            # Formula has errors -> BLOCKED
            reasons = ", ".join(governance_result.blocking_reasons)
            rule_dto = ControlRuleDTO(
                rule_type=rule_type,
                target_field_id=target_field_id,
                formula_text=formula_text,
                diagnostics=diagnostics,
            )
            return ControlRuleResultDTO(
                status=ControlRuleStatus.BLOCKED,
                rule=rule_dto,
                block_reason=f"Formula has errors: {reasons}",
            )

        # Step 6: BOOLEAN type enforcement (Phase F-8 requirement)
        inferred_type = validation_result.inferred_type
        if inferred_type != FormulaResultType.BOOLEAN.value:
            # Non-boolean formula -> BLOCKED
            rule_dto = ControlRuleDTO(
                rule_type=rule_type,
                target_field_id=target_field_id,
                formula_text=formula_text,
                diagnostics=diagnostics,
            )
            return ControlRuleResultDTO(
                status=ControlRuleStatus.BLOCKED,
                rule=rule_dto,
                block_reason=(
                    f"Control rules require BOOLEAN formulas. "
                    f"Inferred type: {inferred_type}"
                ),
            )

        # VALID or VALID_WITH_WARNINGS with BOOLEAN type -> ALLOWED
        rule_dto = ControlRuleDTO(
            rule_type=rule_type,
            target_field_id=target_field_id,
            formula_text=formula_text,
            diagnostics=diagnostics,
        )

        return ControlRuleResultDTO(
            status=ControlRuleStatus.ALLOWED,
            rule=rule_dto,
            block_reason=None,
        )

    def can_apply_control_rule(
        self,
        rule_type: ControlRuleType,
        formula_text: str,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> ControlRuleResultDTO:
        """Check if a control rule can be applied.

        This is a lighter-weight check than validate_control_rule.
        Performs validation and boolean type check only.

        Args:
            rule_type: Type of control rule (VISIBILITY, ENABLED, REQUIRED)
            formula_text: Boolean formula expression
            schema_fields: Read-only schema field snapshot (DTOs)

        Returns:
            ControlRuleResultDTO with:
            - status: ALLOWED, BLOCKED, or CLEARED
            - rule: None (this method doesn't create a rule)
            - block_reason: Reason if blocked

        Example:
            result = usecases.can_apply_control_rule(
                rule_type=ControlRuleType.ENABLED,
                formula_text="has_permission == true",
                schema_fields=schema_fields
            )
            if result.is_allowed:
                # Can proceed to create the rule
                pass

        Phase F-8 Compliance:
            - Policy evaluation only
            - Deterministic
            - No persistence
            - No execution
            - Returns DTO only
        """
        # Handle empty formula -> CLEARED
        if not formula_text or not formula_text.strip():
            return ControlRuleResultDTO(
                status=ControlRuleStatus.CLEARED,
                rule=None,
                block_reason=None,
            )

        # Validate formula
        validation_result = self._formula_usecases.validate_formula(
            formula_text=formula_text,
            schema_fields=schema_fields,
        )

        # Evaluate governance (without cycle detection for lighter check)
        governance_result = self._formula_usecases.evaluate_governance(
            formula_text=formula_text,
            validation_result=validation_result,
            cycle_result=None,
        )

        # Check governance status
        if governance_result.status == FormulaGovernanceStatus.INVALID:
            reasons = ", ".join(governance_result.blocking_reasons)
            return ControlRuleResultDTO(
                status=ControlRuleStatus.BLOCKED,
                rule=None,
                block_reason=f"Formula has errors: {reasons}",
            )

        # BOOLEAN type enforcement
        inferred_type = validation_result.inferred_type
        if inferred_type != FormulaResultType.BOOLEAN.value:
            return ControlRuleResultDTO(
                status=ControlRuleStatus.BLOCKED,
                rule=None,
                block_reason=(
                    f"Control rules require BOOLEAN formulas. "
                    f"Inferred type: {inferred_type}"
                ),
            )

        # ALLOWED
        return ControlRuleResultDTO(
            status=ControlRuleStatus.ALLOWED,
            rule=None,
            block_reason=None,
        )

    def clear_control_rule(
        self,
        rule_type: ControlRuleType,
        target_field_id: str,
    ) -> ControlRuleResultDTO:
        """Clear/remove a control rule.

        Returns a CLEARED result indicating the rule should be removed.
        The actual removal is done by the caller.

        Args:
            rule_type: Type of control rule being cleared
            target_field_id: ID of the field the rule was applied to

        Returns:
            ControlRuleResultDTO with:
            - status: CLEARED
            - rule: None
            - block_reason: None

        Example:
            result = usecases.clear_control_rule(
                rule_type=ControlRuleType.VISIBILITY,
                target_field_id="secret_field"
            )
            # result.is_cleared == True
            # Caller removes the rule from their state

        Phase F-8 Compliance:
            - Pure result creation
            - Deterministic
            - No persistence
            - No execution
            - Returns DTO only
        """
        return ControlRuleResultDTO(
            status=ControlRuleStatus.CLEARED,
            rule=None,
            block_reason=None,
        )

    def preview_control_rule(
        self,
        rule_input: ControlRulePreviewInputDTO,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
        field_values: dict[str, Any],
    ) -> ControlRulePreviewResultDTO:
        """Preview a control rule with temporary field values.

        PHASE F-9: Control Rules Preview Application

        This method:
        1. Validates the control rule using validate_control_rule()
        2. If ALLOWED, executes the formula using FormulaUseCases.execute_formula()
        3. Returns a ControlRulePreviewResultDTO with validation + execution results

        Args:
            rule_input: Control rule definition (type, target, formula)
            schema_fields: Read-only schema field snapshot (DTOs)
            field_values: Temporary field values for preview (in-memory only)

        Returns:
            ControlRulePreviewResultDTO with:
            - rule_input: The input rule definition
            - validation_status: ALLOWED, BLOCKED, or CLEARED
            - is_allowed: True if rule passes validation
            - is_blocked: True if rule is blocked by governance/type
            - block_reason: Reason if blocked
            - execution_result: Boolean result of formula execution (if allowed)
            - execution_error: Error message if execution failed

        Example:
            result = usecases.preview_control_rule(
                rule_input=ControlRulePreviewInputDTO(
                    rule_type=ControlRuleType.VISIBILITY,
                    target_field_id="secret_field",
                    formula_text="user_role == 'admin'"
                ),
                schema_fields=schema_fields,
                field_values={"user_role": "admin"}
            )
            if result.is_allowed and result.execution_result is True:
                # Field should be visible
                pass

        Phase F-9 Compliance:
            - UI-only preview, no persistence
            - In-memory field values only
            - Read-only schema access (DTOs)
            - No schema mutation
            - Deterministic execution
            - Returns DTO only
        """
        # Handle empty formula -> CLEARED (no effect)
        if not rule_input.formula_text or not rule_input.formula_text.strip():
            return ControlRulePreviewResultDTO(
                rule_input=rule_input,
                validation_status=ControlRuleStatus.CLEARED,
                is_allowed=False,
                is_blocked=False,
                block_reason=None,
                execution_result=None,
                execution_error=None,
            )

        # Step 1: Validate the control rule using existing validation
        validation_result = self.validate_control_rule(
            rule_type=rule_input.rule_type,
            target_field_id=rule_input.target_field_id,
            formula_text=rule_input.formula_text,
            schema_fields=schema_fields,
        )

        # If BLOCKED, return without execution
        if validation_result.status == ControlRuleStatus.BLOCKED:
            return ControlRulePreviewResultDTO(
                rule_input=rule_input,
                validation_status=ControlRuleStatus.BLOCKED,
                is_allowed=False,
                is_blocked=True,
                block_reason=validation_result.block_reason,
                execution_result=None,
                execution_error=None,
            )

        # If CLEARED, return without execution
        if validation_result.status == ControlRuleStatus.CLEARED:
            return ControlRulePreviewResultDTO(
                rule_input=rule_input,
                validation_status=ControlRuleStatus.CLEARED,
                is_allowed=False,
                is_blocked=False,
                block_reason=None,
                execution_result=None,
                execution_error=None,
            )

        # Step 2: ALLOWED - Execute formula with temporary field values
        execution_result = self._formula_usecases.execute_formula(
            formula_text=rule_input.formula_text,
            field_values=field_values,
        )

        # Handle execution failure
        if not execution_result.success:
            return ControlRulePreviewResultDTO(
                rule_input=rule_input,
                validation_status=ControlRuleStatus.ALLOWED,
                is_allowed=True,
                is_blocked=False,
                block_reason=None,
                execution_result=None,
                execution_error=execution_result.error,
            )

        # Coerce result to boolean (control rules require boolean)
        # The formula should return boolean based on F-8 validation,
        # but we handle edge cases gracefully
        bool_result: bool | None = None
        if execution_result.value is not None:
            if isinstance(execution_result.value, bool):
                bool_result = execution_result.value
            else:
                # Coerce to boolean for truthy/falsy evaluation
                bool_result = bool(execution_result.value)

        return ControlRulePreviewResultDTO(
            rule_input=rule_input,
            validation_status=ControlRuleStatus.ALLOWED,
            is_allowed=True,
            is_blocked=False,
            block_reason=None,
            execution_result=bool_result,
            execution_error=None,
        )

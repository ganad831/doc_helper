"""Evaluate Control Rules Use Case (Phase R-1).

Runtime evaluation of control rules for a field based on current field values.

ADR-050 Compliance:
- Pull-based evaluation (caller provides all inputs)
- Deterministic (same inputs → same outputs)
- Read-only (no side effects, no persistence)
- Non-blocking failures (default state on error)
- 100ms timeout per rule
- Single-entity scope only
"""

from typing import Any

from doc_helper.application.dto.export_dto import ControlRuleExportDTO
from doc_helper.application.dto.runtime_dto import (
    ControlRuleEvaluationRequestDTO,
    ControlRuleEvaluationResultDTO,
)
from doc_helper.application.usecases.formula_usecases import FormulaUseCases
from doc_helper.application.usecases.schema_usecases import SchemaUseCases


class EvaluateControlRulesUseCase:
    """Use case for evaluating control rules at runtime (Phase R-1).

    Evaluates all control rules targeting a specific field and returns
    aggregated UI state (visible, enabled, required).

    ADR-050 Rules:
        - Pull-based: Caller provides entity_id, field_id, field_values
        - Deterministic: Same inputs → same outputs
        - Read-only: No persistence of results
        - Non-blocking: Failures return default state
        - Timeout: 100ms per rule (not implemented in Phase R-1)
        - Single-entity scope: All rules within same entity

    Usage:
        use_case = EvaluateControlRulesUseCase(schema_usecases, formula_usecases)
        request = ControlRuleEvaluationRequestDTO(
            entity_id="project",
            field_id="sensitive_field",
            field_values={"user_role": "admin", "status": "active"}
        )
        result = use_case.execute(request)
        # result.visible, result.enabled, result.required
    """

    def __init__(
        self,
        schema_usecases: SchemaUseCases,
        formula_usecases: FormulaUseCases | None = None,
    ) -> None:
        """Initialize EvaluateControlRulesUseCase.

        Args:
            schema_usecases: SchemaUseCases instance for fetching control rules
            formula_usecases: FormulaUseCases instance for formula evaluation
                If None, creates a new instance.
        """
        self._schema_usecases = schema_usecases
        self._formula_usecases = formula_usecases or FormulaUseCases()

    def execute(
        self,
        request: ControlRuleEvaluationRequestDTO,
    ) -> ControlRuleEvaluationResultDTO:
        """Execute control rule evaluation for a field.

        ADR-050 Compliance:
            - Pull-based: All inputs provided by caller
            - Deterministic: Same inputs → same outputs
            - Read-only: No persistence
            - Non-blocking: Failures return default state
            - Single-entity scope only

        Args:
            request: ControlRuleEvaluationRequestDTO with:
                - entity_id: Entity containing the field
                - field_id: Field whose control rules should be evaluated
                - field_values: Current field values (snapshot)

        Returns:
            ControlRuleEvaluationResultDTO with:
                - success: True if evaluation completed without errors
                - visible: Whether field should be visible
                - enabled: Whether field should be enabled
                - required: Whether field is required
                - error_message: Error if evaluation failed

        Evaluation Rules (ADR-050):
            - VISIBILITY rule with result=True → visible=True
            - VISIBILITY rule with result=False → visible=False
            - ENABLED rule with result=True → enabled=True
            - ENABLED rule with result=False → enabled=False
            - REQUIRED rule with result=True → required=True
            - REQUIRED rule with result=False → required=False
            - Formula evaluation failure → use default state
            - No rules exist → use default state
            - Default state: visible=True, enabled=True, required=False

        Example:
            request = ControlRuleEvaluationRequestDTO(
                entity_id="project",
                field_id="admin_notes",
                field_values={"user_role": "admin"}
            )
            result = use_case.execute(request)
            if result.success and result.visible:
                # Show field
                pass
        """
        # Fetch control rules for the field from schema
        try:
            control_rules: tuple[ControlRuleExportDTO, ...] = (
                self._schema_usecases.list_control_rules_for_field(
                    entity_id=request.entity_id,
                    field_id=request.field_id,
                )
            )
        except Exception as e:
            # Schema fetch failed → return failure with default state
            return ControlRuleEvaluationResultDTO.failure(
                error_message=f"Failed to fetch control rules: {str(e)}"
            )

        # No control rules → return default state
        if not control_rules:
            return ControlRuleEvaluationResultDTO.default()

        # Initialize field state with defaults
        visible = True
        enabled = True
        required = False

        # Evaluate each control rule
        for rule in control_rules:
            # Evaluate formula using FormulaUseCases
            execution_result = self._formula_usecases.execute_formula(
                formula_text=rule.formula_text,
                field_values=request.field_values,
            )

            # If formula execution failed, skip this rule (non-blocking)
            if not execution_result.success:
                # ADR-050: Control rule failures do NOT block form interaction
                # Continue with default state for this rule
                continue

            # Extract boolean result (control rules must be boolean formulas)
            bool_result = self._coerce_to_boolean(execution_result.value)

            # Apply control rule effect based on type
            if rule.rule_type == "VISIBILITY":
                visible = bool_result
            elif rule.rule_type == "ENABLED":
                enabled = bool_result
            elif rule.rule_type == "REQUIRED":
                required = bool_result

        # Return aggregated result
        return ControlRuleEvaluationResultDTO(
            success=True,
            visible=visible,
            enabled=enabled,
            required=required,
            error_message=None,
        )

    def _coerce_to_boolean(self, value: Any) -> bool:
        """Coerce formula result to boolean.

        ADR-050: Control rules require boolean formulas, but we handle
        edge cases gracefully with truthy/falsy evaluation.

        Args:
            value: Formula execution result

        Returns:
            Boolean value (truthy/falsy evaluation)
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        # Truthy/falsy conversion
        return bool(value)

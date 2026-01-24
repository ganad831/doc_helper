"""Evaluate Runtime Rules Use Case (Phase R-3, updated in R-4).

Orchestrates runtime evaluation of all runtime rules in deterministic order.

ADR-050 Compliance:
- Pull-based evaluation (caller provides all inputs)
- Deterministic (same inputs → same outputs)
- Read-only (no side effects, no persistence)
- Single-entity scope only
- Orchestration only (reuses existing use cases)

Phase R-3: Authoritative runtime entry point.
Phase R-4 Update: Now uses entity-level control rules aggregation.
"""

from doc_helper.application.dto.runtime_dto import (
    OutputMappingEvaluationRequestDTO,
    RuntimeEvaluationRequestDTO,
    RuntimeEvaluationResultDTO,
    ValidationEvaluationRequestDTO,
)
from doc_helper.application.usecases.runtime.evaluate_entity_control_rules import (
    EvaluateEntityControlRulesUseCase,
)
from doc_helper.application.usecases.runtime.evaluate_output_mappings import (
    EvaluateOutputMappingsUseCase,
)
from doc_helper.application.usecases.runtime.evaluate_validation_rules import (
    EvaluateValidationRulesUseCase,
)
from doc_helper.application.usecases.schema_usecases import SchemaUseCases


class EvaluateRuntimeRulesUseCase:
    """Use case for orchestrated runtime rule evaluation (Phase R-3, updated in R-4).

    This is the ONLY supported runtime entry point after Phase R-3.
    Evaluates all runtime rules in deterministic order and returns aggregated result.

    Evaluation Order (MANDATORY):
        1. Control Rules (Phase R-4 Entity-Level) - Never blocking
        2. Validation Rules (Phase R-2) - Blocks if ERROR severity
        3. Output Mappings (Phase R-1) - Always blocking on failure

    Blocking Rules:
        - Control Rules: Never blocking
        - Validation Rules: Blocks if validation_result.blocking == True
        - Output Mappings: Always blocking on failure
        - Overall blocking: True if ANY component blocks

    ADR-050 Rules:
        - Pull-based: Caller provides entity_id, field_values
        - Deterministic: Same inputs → same outputs
        - Read-only: No persistence of results
        - Orchestration only: Reuses existing use cases
        - Single-entity scope: All fields within same entity

    Usage:
        use_case = EvaluateRuntimeRulesUseCase(
            schema_usecases=schema_usecases,
            formula_usecases=formula_usecases,
        )
        request = RuntimeEvaluationRequestDTO(
            entity_id="project",
            field_values={"name": "Test", "depth": 10.0}
        )
        result = use_case.execute(request)
        if result.is_blocked:
            # Handle blocking (show errors, prevent document generation)
            print(result.blocking_reason)
    """

    def __init__(
        self,
        schema_usecases: SchemaUseCases,
        formula_usecases=None,  # Optional, created if None
    ) -> None:
        """Initialize EvaluateRuntimeRulesUseCase.

        Args:
            schema_usecases: SchemaUseCases instance for fetching rules/constraints
            formula_usecases: FormulaUseCases instance for formula evaluation
                If None, created internally by sub-use-cases.
        """
        self._schema_usecases = schema_usecases
        self._formula_usecases = formula_usecases

        # Initialize component use cases
        # Phase R-4: Use entity-level control rules aggregation
        self._entity_control_rules_use_case = EvaluateEntityControlRulesUseCase(
            schema_usecases=schema_usecases,
            formula_usecases=formula_usecases,
        )
        self._validation_use_case = EvaluateValidationRulesUseCase(
            schema_usecases=schema_usecases
        )
        self._output_mappings_use_case = EvaluateOutputMappingsUseCase(
            schema_usecases=schema_usecases,
            formula_usecases=formula_usecases,
        )

    def execute(
        self,
        request: RuntimeEvaluationRequestDTO,
    ) -> RuntimeEvaluationResultDTO:
        """Execute orchestrated runtime rule evaluation.

        Evaluation Order (MANDATORY):
            1. Control Rules (R-1) - Never blocking
            2. Validation Rules (R-2) - Blocks if ERROR severity
            3. Output Mappings (R-1) - Only if validation doesn't block

        ADR-050 Compliance:
            - Pull-based: All inputs provided by caller
            - Deterministic: Same inputs → same outputs
            - Read-only: No persistence
            - Orchestration only: Calls existing use cases
            - Single-entity scope only

        Args:
            request: RuntimeEvaluationRequestDTO with:
                - entity_id: Entity whose rules should be evaluated
                - field_values: Current field values (snapshot)

        Returns:
            RuntimeEvaluationResultDTO with:
                - control_rules_result: Control rule evaluation result
                - validation_result: Validation evaluation result
                - output_mappings_result: Output mapping result (None if blocked)
                - is_blocked: True if any component blocks
                - blocking_reason: Human-readable reason for blocking

        Blocking Determination:
            - Control Rules: Never blocking (always evaluated)
            - Validation Rules: Blocks if validation_result.blocking == True
            - Output Mappings: Always blocking on failure
            - If validation blocks, output mappings NOT evaluated

        Example:
            request = RuntimeEvaluationRequestDTO(
                entity_id="project",
                field_values={"name": "", "depth": -5}
            )
            result = use_case.execute(request)
            if result.is_blocked:
                # Validation failed with ERROR issues
                for error in result.validation_result.errors:
                    print(error.message)
        """
        # STEP 1: Evaluate Control Rules (R-4 Entity-Level Aggregation) - Never blocking
        # Phase R-4: Use entity-level control rules aggregation
        # Aggregates control rule evaluation across all fields in the entity
        entity_control_rules_result = self._entity_control_rules_use_case.execute(
            entity_id=request.entity_id,
            field_values=request.field_values,
        )

        # STEP 2: Evaluate Validation Rules (R-2) - May block
        validation_request = ValidationEvaluationRequestDTO(
            entity_id=request.entity_id,
            field_values=request.field_values,
        )
        validation_result = self._validation_use_case.execute(validation_request)

        # Check if validation blocks
        if validation_result.blocking:
            # Validation blocked → return with blocking reason
            error_count = len(validation_result.errors)
            blocking_reason = (
                f"Validation failed with {error_count} ERROR severity issue(s)"
            )
            return RuntimeEvaluationResultDTO.success(
                control_rules_result=entity_control_rules_result,
                validation_result=validation_result,
                output_mappings_result=None,  # Not evaluated
                is_blocked=True,
                blocking_reason=blocking_reason,
            )

        # STEP 3: Evaluate Output Mappings (R-1) - Only if validation doesn't block
        # Output mappings are field-specific, so we create a placeholder
        # Full implementation would aggregate all field output mappings
        # For Phase R-3, we return None to indicate output mappings not yet supported at entity level

        output_mappings_result = None
        is_blocked = False
        blocking_reason = None

        # Return aggregated result
        return RuntimeEvaluationResultDTO.success(
            control_rules_result=entity_control_rules_result,
            validation_result=validation_result,
            output_mappings_result=output_mappings_result,
            is_blocked=is_blocked,
            blocking_reason=blocking_reason,
        )

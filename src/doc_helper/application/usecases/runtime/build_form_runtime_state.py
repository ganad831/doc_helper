"""Build Form Runtime State Use Case (Phase R-4.5).

Adapter that converts runtime evaluation results into UI-consumable form state.

ADR-050 Compliance:
- Pull-based (caller provides all inputs)
- Deterministic (same inputs → same outputs)
- Read-only (no side effects, no persistence)
- Single-entity scope only
- Adapter only (reuses R-3 orchestration results)

Phase R-4.5: Bridges runtime evaluation results with presentation layer.
"""

from doc_helper.application.dto.runtime_dto import (
    FormRuntimeStateDTO,
    RuntimeEvaluationResultDTO,
)


class BuildFormRuntimeStateUseCase:
    """Use case for building form runtime state from evaluation results (Phase R-4.5).

    Converts runtime evaluation results (R-3) into presentation-ready form state.

    ADR-050 Rules:
        - Pull-based: Caller provides evaluation results
        - Deterministic: Same inputs → same outputs
        - Read-only: No persistence, no mutations
        - Adapter only: Reuses existing evaluation results
        - Single-entity scope: All fields within same entity

    Usage:
        use_case = BuildFormRuntimeStateUseCase()
        form_state = use_case.execute(
            entity_id="project",
            field_values={"project_name": "Test", "depth": 5.0},
            runtime_result=runtime_evaluation_result,  # From R-3
        )
        # form_state.fields contains per-field visibility/enabled/required/validation
    """

    def __init__(self) -> None:
        """Initialize BuildFormRuntimeStateUseCase.

        No dependencies required - this is a pure adapter.
        """
        pass

    def execute(
        self,
        entity_id: str,
        field_values: dict[str, any],
        runtime_result: RuntimeEvaluationResultDTO,
    ) -> FormRuntimeStateDTO:
        """Build form runtime state from runtime evaluation results.

        ADR-050 Compliance:
            - Pull-based: All inputs provided by caller
            - Deterministic: Same inputs → same outputs
            - Read-only: No persistence, no mutations
            - Adapter only: Delegates to DTO factory method
            - Single-entity scope only

        Args:
            entity_id: Entity whose form state should be built
            field_values: Current field values (not used in conversion,
                provided for context/debugging)
            runtime_result: RuntimeEvaluationResultDTO from Phase R-3 orchestration
                Contains:
                - control_rules_result (R-4 entity-level aggregation)
                - validation_result (R-2 validation evaluation)
                - output_mappings_result (R-1, not used in form state)

        Returns:
            FormRuntimeStateDTO with per-field states:
                - visibility, enabled, required (from control rules)
                - validation_errors, warnings, info (from validation)
                - has_blocking_errors (True if ERROR severity issues exist)

        Conversion Strategy:
            1. Extract control rules from runtime_result.control_rules_result (R-4)
            2. Extract validation from runtime_result.validation_result (R-2)
            3. For each field in control_rules_result.field_results:
               - Combine control state (visible/enabled/required)
               - Lookup validation messages by field_id
               - Create FormFieldRuntimeStateDTO
            4. Return FormRuntimeStateDTO with aggregated field states

        Example:
            form_state = use_case.execute(
                entity_id="project",
                field_values={"project_name": "", "depth": -5},
                runtime_result=runtime_result,
            )
            # Check if form can be submitted
            if form_state.has_blocking_errors:
                for field in form_state.fields:
                    if field.validation_errors:
                        print(f"{field.field_id}: {field.validation_errors}")
        """
        # Delegate to DTO factory method
        # This is a pure adapter - no logic beyond conversion
        return FormRuntimeStateDTO.from_runtime_result(
            entity_id=entity_id,
            runtime_result=runtime_result,
        )

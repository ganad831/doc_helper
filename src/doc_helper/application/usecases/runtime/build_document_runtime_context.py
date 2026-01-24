"""Build Document Runtime Context Use Case (Phase R-6).

Bridges runtime evaluation results with document generation context.

ADR-050 Compliance:
- Pull-based evaluation (caller provides all inputs)
- Deterministic (same inputs → same outputs)
- Read-only (no side effects, no persistence)
- Single-entity scope only
- Adapter only (no re-evaluation of rules)

Phase R-6: Creates final document-ready context from runtime evaluation results.
"""

from typing import Any

from doc_helper.application.dto.runtime_dto import (
    DocumentRuntimeContextDTO,
    EntityOutputMappingsEvaluationDTO,
    FormRuntimeStateDTO,
)


class BuildDocumentRuntimeContextUseCase:
    """Use case for building document runtime context (Phase R-6).

    Merges runtime evaluation results into final document-ready context.

    ADR-050 Rules:
        - Pull-based: Caller provides all inputs
        - Deterministic: Same inputs → same outputs
        - Read-only: No persistence, no mutations
        - Adapter only: Delegates to DTO factory method
        - Single-entity scope only

    Blocking Rules:
        - Validation ERRORs → has_blocking_errors = True
        - Output mapping failure → has_blocking_errors = True
        - Warnings/Info → non-blocking

    Usage:
        use_case = BuildDocumentRuntimeContextUseCase()
        context = use_case.execute(
            entity_id="project",
            field_values={"depth": 5.0, "name": "Test"},
            form_state=form_runtime_state,  # From R-4.5
            output_mappings=output_mappings,  # From R-5
        )
        if not context.has_blocking_errors:
            # Document can be generated
            for field in context.fields:
                print(f"{field.field_id} = {field.value}")
    """

    def __init__(self) -> None:
        """Initialize BuildDocumentRuntimeContextUseCase.

        No dependencies required - this is a pure adapter.
        """
        pass

    def execute(
        self,
        entity_id: str,
        field_values: dict[str, Any],
        form_state: FormRuntimeStateDTO,
        output_mappings: EntityOutputMappingsEvaluationDTO,
    ) -> DocumentRuntimeContextDTO:
        """Build document runtime context from runtime evaluation results.

        ADR-050 Compliance:
            - Pull-based: All inputs provided by caller
            - Deterministic: Same inputs → same outputs
            - Read-only: No persistence, no mutations
            - Adapter only: Delegates to DTO factory method
            - Single-entity scope only

        Merges:
            1. Field visibility/enabled/required (from form_state / R-4.5)
            2. Field values (from field_values dict)
            3. Validation messages (from form_state / R-2)
            4. Output mapping values (from output_mappings / R-5)

        Blocking Determination:
            - Validation ERRORs (from form_state.has_blocking_errors)
            - Output mapping failure (from output_mappings.result.success)
            - Result: has_blocking_errors = validation errors OR output failure

        Args:
            entity_id: Entity whose document context should be built
            field_values: Current field values snapshot {field_id → value}
                Provided by caller (same values passed to R-3, R-4.5, R-5)
            form_state: FormRuntimeStateDTO from Phase R-4.5
                Contains: visibility, enabled, required, validation messages
            output_mappings: EntityOutputMappingsEvaluationDTO from Phase R-5
                Contains: {target → value} map for document generation

        Returns:
            DocumentRuntimeContextDTO with:
                - entity_id: Entity ID
                - fields: Per-field document state (visibility, value, validation)
                - output_values: {target → value} map from R-5
                - has_blocking_errors: True if validation errors OR output failure

        Edge Cases:
            - Empty field_values → fields have value=None
            - Empty form_state.fields → empty fields tuple
            - Output mapping failure → empty output_values, has_blocking_errors=True
            - No validation errors → has_blocking_errors depends only on output mapping

        Example:
            context = use_case.execute(
                entity_id="project",
                field_values={"depth": 5.0, "name": "Test"},
                form_state=form_state,
                output_mappings=output_mappings,
            )
            if context.has_blocking_errors:
                # Document generation blocked
                for field in context.fields:
                    if field.validation_errors:
                        print(f"{field.field_id}: {field.validation_errors}")
            else:
                # Document can be generated
                print(f"Output values: {context.output_values}")
        """
        # Delegate to DTO factory method
        # This is a pure adapter - no logic beyond merging
        return DocumentRuntimeContextDTO.from_runtime_results(
            entity_id=entity_id,
            field_values=field_values,
            form_state=form_state,
            output_mappings=output_mappings,
        )

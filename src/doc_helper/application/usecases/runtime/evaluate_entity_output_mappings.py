"""Evaluate Entity Output Mappings Use Case (Phase R-5).

Entity-level aggregation of output mapping evaluations for document generation.

ADR-050 Compliance:
- Pull-based evaluation (caller provides all inputs)
- Deterministic (same inputs → same outputs)
- Read-only (no side effects, no persistence)
- Blocking failures (ANY failure blocks document generation)
- Single-entity scope only
- Reuses Phase R-1 output mapping evaluation

Phase R-5: Aggregates field-level output mappings into document-ready output map.
"""

from typing import Any

from doc_helper.application.dto.runtime_dto import (
    EntityOutputMappingsEvaluationDTO,
    OutputMappingEvaluationRequestDTO,
)
from doc_helper.application.usecases.formula_usecases import FormulaUseCases
from doc_helper.application.usecases.runtime.evaluate_output_mappings import (
    EvaluateOutputMappingsUseCase,
)
from doc_helper.application.usecases.schema_usecases import SchemaUseCases
from doc_helper.domain.schema.schema_ids import EntityDefinitionId


class EvaluateEntityOutputMappingsUseCase:
    """Use case for evaluating entity-level output mappings (Phase R-5).

    Aggregates all output mappings for an entity into document-ready output map.

    ADR-050 Rules:
        - Pull-based: Caller provides entity_id, field_values
        - Deterministic: Same inputs → same outputs
        - Read-only: No persistence of results
        - Blocking: ANY failure BLOCKS document generation
        - Single-entity scope: All fields within same entity
        - Reuses R-1: Delegates to EvaluateOutputMappingsUseCase

    Blocking Rules:
        - Output mapping failure → BLOCK
        - Type mismatch → BLOCK
        - Missing field value → BLOCK
        - Formula error → BLOCK
        - No output mappings → Success (empty result)

    Usage:
        use_case = EvaluateEntityOutputMappingsUseCase(schema_usecases)
        result = use_case.execute(
            entity_id="project",
            field_values={"depth_from": "5.0", "depth_to": "10.0"},
        )
        if result.result.success:
            # result.result.values contains {target → value} map
            for target, value in result.result.values.items():
                print(f"{target} = {value}")
    """

    def __init__(
        self,
        schema_usecases: SchemaUseCases,
        formula_usecases: FormulaUseCases | None = None,
    ) -> None:
        """Initialize EvaluateEntityOutputMappingsUseCase.

        Args:
            schema_usecases: SchemaUseCases instance for fetching entities/fields/mappings
            formula_usecases: FormulaUseCases instance for formula evaluation
                If None, passed to R-1 use case (which creates a new instance).
        """
        self._schema_usecases = schema_usecases
        self._formula_usecases = formula_usecases
        # Create R-1 use case instance for output mapping evaluation
        self._evaluate_output_mappings = EvaluateOutputMappingsUseCase(
            schema_usecases=schema_usecases,
            formula_usecases=formula_usecases,
        )

    def execute(
        self,
        entity_id: str,
        field_values: dict[str, Any],
    ) -> EntityOutputMappingsEvaluationDTO:
        """Execute entity-level output mapping evaluation.

        ADR-050 Compliance:
            - Pull-based: All inputs provided by caller
            - Deterministic: Same inputs → same outputs
            - Read-only: No persistence
            - Blocking: ANY failure BLOCKS document generation
            - Single-entity scope only

        Execution Steps:
            1. Get entity from schema repository
            2. Iterate all fields in entity
            3. For each field, get output mappings
            4. For each mapping, call EvaluateOutputMappingsUseCase (R-1)
            5. If ANY evaluation fails: STOP, return blocked result
            6. Otherwise: Aggregate {target → value}, return success

        Args:
            entity_id: Entity whose output mappings should be evaluated
            field_values: Current field values (snapshot) for the entity

        Returns:
            EntityOutputMappingsEvaluationDTO with:
                - entity_id: Entity ID
                - result.success: True if all evaluations succeeded
                - result.values: {target → value} map for document generation
                - result.error: Error message if ANY evaluation failed

        Edge Cases:
            - Entity not found → Failure
            - Entity has no fields → Success (empty result)
            - Field has no output mappings → Skip field, continue
            - No output mappings in entire entity → Success (empty result)

        Example:
            result = use_case.execute(
                entity_id="project",
                field_values={"depth": 5.0, "name": "Test"},
            )
            if result.result.success:
                # Document can be generated
                assert "{{depth_m}}" in result.result.values
                assert result.result.values["{{depth_m}}"] == "5.0 m"
        """
        # Step 1: Get entity from schema repository
        entity_id_obj = EntityDefinitionId(entity_id.strip())

        # Check if entity exists
        if not self._schema_usecases._schema_repository.exists(entity_id_obj):
            return EntityOutputMappingsEvaluationDTO.failure(
                entity_id=entity_id,
                error=f"Entity '{entity_id}' not found",
            )

        # Load entity
        load_result = self._schema_usecases._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return EntityOutputMappingsEvaluationDTO.failure(
                entity_id=entity_id,
                error=f"Failed to load entity '{entity_id}': {load_result.error}",
            )

        entity = load_result.value

        # Step 2: Initialize output values accumulator
        output_values: dict[str, Any] = {}

        # Step 3: Iterate all fields in entity
        for field_id_obj, field in entity.fields.items():
            field_id = field_id_obj.value

            # Step 4: Get output mappings for this field
            output_mappings = self._schema_usecases.list_output_mappings_for_field(
                entity_id=entity_id,
                field_id=field_id,
            )

            # Skip field if no output mappings
            if not output_mappings:
                continue

            # Step 5: Evaluate each output mapping
            for mapping in output_mappings:
                # Create request DTO for R-1 use case
                request = OutputMappingEvaluationRequestDTO(
                    entity_id=entity_id,
                    field_id=field_id,
                    field_values=field_values,
                )

                # Call R-1 use case
                mapping_result = self._evaluate_output_mappings.execute(request)

                # Step 6: Check for failure (blocking semantics)
                if not mapping_result.success:
                    # ANY failure blocks entire entity evaluation
                    return EntityOutputMappingsEvaluationDTO.failure(
                        entity_id=entity_id,
                        error=f"Output mapping evaluation failed for field '{field_id}': {mapping_result.error_message}",
                    )

                # Step 7: Accumulate successful result
                # Store target → value mapping
                output_values[mapping_result.target] = mapping_result.value

        # Step 8: Return aggregated success result
        # Even if no output mappings found, return success (empty result)
        return EntityOutputMappingsEvaluationDTO.success_result(
            entity_id=entity_id,
            values=output_values,
        )

"""Evaluate Entity Control Rules Use Case (Phase R-4).

Entity-level aggregation of control rule runtime evaluation.

ADR-050 Compliance:
- Pull-based evaluation (caller provides all inputs)
- Deterministic (same inputs → same outputs)
- Read-only (no side effects, no persistence)
- Single-entity scope only
- Aggregation only (reuses Phase R-1 control rule evaluation)

Phase R-4: Bridges field-level control rules (R-1) with entity-level orchestration (R-3).
"""

from doc_helper.application.dto.runtime_dto import (
    ControlRuleEvaluationRequestDTO,
    EntityControlRuleEvaluationDTO,
    EntityControlRulesEvaluationResultDTO,
)
from doc_helper.application.usecases.runtime.evaluate_control_rules import (
    EvaluateControlRulesUseCase,
)
from doc_helper.application.usecases.schema_usecases import SchemaUseCases


class EvaluateEntityControlRulesUseCase:
    """Use case for entity-level control rule aggregation (Phase R-4).

    Aggregates field-level control rule evaluation across all fields in an entity.

    ADR-050 Rules:
        - Pull-based: Caller provides entity_id, field_values
        - Deterministic: Same inputs → same outputs
        - Read-only: No persistence
        - Aggregation only: Reuses EvaluateControlRulesUseCase (R-1)
        - Single-entity scope: All fields within same entity

    Usage:
        use_case = EvaluateEntityControlRulesUseCase(
            schema_usecases=schema_usecases,
            formula_usecases=formula_usecases,
        )
        result = use_case.execute(
            entity_id="project",
            field_values={"project_name": "Test", "depth": 5.0}
        )
        # result.field_results contains per-field control states
    """

    def __init__(
        self,
        schema_usecases: SchemaUseCases,
        formula_usecases=None,
    ) -> None:
        """Initialize EvaluateEntityControlRulesUseCase.

        Args:
            schema_usecases: SchemaUseCases instance for fetching entity fields
            formula_usecases: Optional FormulaUseCases for formula evaluation
        """
        self._schema_usecases = schema_usecases
        self._formula_usecases = formula_usecases

        # Initialize field-level control rules use case
        self._control_rules_use_case = EvaluateControlRulesUseCase(
            schema_usecases=schema_usecases,
            formula_usecases=formula_usecases,
        )

    def execute(
        self,
        entity_id: str,
        field_values: dict[str, any],
    ) -> EntityControlRulesEvaluationResultDTO:
        """Execute entity-level control rule aggregation.

        ADR-050 Compliance:
            - Pull-based: All inputs provided by caller
            - Deterministic: Same inputs → same outputs
            - Read-only: No persistence
            - Aggregation only: Delegates to R-1 control rules use case
            - Single-entity scope only

        Args:
            entity_id: Entity whose control rules should be evaluated
            field_values: Current field values for the entity instance (snapshot)

        Returns:
            EntityControlRulesEvaluationResultDTO with per-field control states

        Evaluation Strategy:
            1. Fetch all fields for the entity
            2. For each field, call EvaluateControlRulesUseCase (R-1)
            3. Collect results into tuple
            4. Return aggregated entity-level result

        Example:
            result = use_case.execute(
                entity_id="project",
                field_values={"project_name": "Test", "depth": 5.0}
            )
            for field_result in result.field_results:
                print(f"{field_result.field_id}: visible={field_result.visibility}")
        """
        # Fetch entity definition to get all fields
        try:
            entities = self._schema_usecases.get_all_entities()
            entity_dto = next((e for e in entities if e.id == entity_id), None)
            if not entity_dto:
                # Entity not found - return default (no fields)
                return EntityControlRulesEvaluationResultDTO.default(entity_id)
        except Exception:
            # Schema fetch failure - return default
            return EntityControlRulesEvaluationResultDTO.default(entity_id)

        # Aggregate control rule results for all fields in entity
        field_results: list[EntityControlRuleEvaluationDTO] = []

        for field_dto in entity_dto.fields:
            # Evaluate control rules for this field
            request = ControlRuleEvaluationRequestDTO(
                entity_id=entity_id,
                field_id=field_dto.id,
                field_values=field_values,
            )
            control_result = self._control_rules_use_case.execute(request)

            # Collect per-field result
            field_result = EntityControlRuleEvaluationDTO(
                field_id=field_dto.id,
                visibility=control_result.visible,
                enabled=control_result.enabled,
                required=control_result.required,
            )
            field_results.append(field_result)

        # Return aggregated entity-level result
        return EntityControlRulesEvaluationResultDTO.from_field_results(
            entity_id=entity_id,
            field_results=tuple(field_results),
        )

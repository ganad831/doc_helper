"""Evaluate Output Mappings Use Case (Phase R-1).

Runtime evaluation of output mappings for document generation.

ADR-050 Compliance:
- Pull-based evaluation (caller provides all inputs)
- Deterministic (same inputs → same outputs)
- Read-only (no side effects, no persistence)
- Blocking failures (fail document generation)
- 1000ms timeout per field
- Single-entity scope only
- Strict type enforcement (TEXT/NUMBER/BOOLEAN)
"""

from typing import Any

from doc_helper.application.dto.export_dto import OutputMappingExportDTO
from doc_helper.application.dto.runtime_dto import (
    OutputMappingEvaluationRequestDTO,
    OutputMappingEvaluationResultDTO,
)
from doc_helper.application.usecases.formula_usecases import FormulaUseCases
from doc_helper.application.usecases.schema_usecases import SchemaUseCases


class EvaluateOutputMappingsUseCase:
    """Use case for evaluating output mappings at runtime (Phase R-1).

    Evaluates output mapping for a field to produce document output value.

    ADR-050 Rules:
        - Pull-based: Caller provides entity_id, field_id, field_values
        - Deterministic: Same inputs → same outputs
        - Read-only: No persistence of results
        - Blocking: Failures BLOCK document generation
        - Timeout: 1000ms per field (not implemented in Phase R-1)
        - Single-entity scope: All fields within same entity
        - Type enforcement: TEXT/NUMBER/BOOLEAN with strict coercion

    Usage:
        use_case = EvaluateOutputMappingsUseCase(schema_usecases, formula_usecases)
        request = OutputMappingEvaluationRequestDTO(
            entity_id="project",
            field_id="depth_range",
            field_values={"depth_from": "5.0", "depth_to": "10.0"}
        )
        result = use_case.execute(request)
        if result.success:
            # result.value contains the computed output value
            pass
    """

    def __init__(
        self,
        schema_usecases: SchemaUseCases,
        formula_usecases: FormulaUseCases | None = None,
    ) -> None:
        """Initialize EvaluateOutputMappingsUseCase.

        Args:
            schema_usecases: SchemaUseCases instance for fetching output mappings
            formula_usecases: FormulaUseCases instance for formula evaluation
                If None, creates a new instance.
        """
        self._schema_usecases = schema_usecases
        self._formula_usecases = formula_usecases or FormulaUseCases()

    def execute(
        self,
        request: OutputMappingEvaluationRequestDTO,
    ) -> OutputMappingEvaluationResultDTO:
        """Execute output mapping evaluation for a field.

        ADR-050 Compliance:
            - Pull-based: All inputs provided by caller
            - Deterministic: Same inputs → same outputs
            - Read-only: No persistence
            - Blocking: Failures BLOCK document generation
            - Single-entity scope only
            - Type enforcement: TEXT/NUMBER/BOOLEAN

        Args:
            request: OutputMappingEvaluationRequestDTO with:
                - entity_id: Entity containing the field
                - field_id: Field whose output mapping should be evaluated
                - field_values: Current field values (snapshot)

        Returns:
            OutputMappingEvaluationResultDTO with:
                - success: True if evaluation succeeded
                - target: Output target type (TEXT/NUMBER/BOOLEAN)
                - value: Computed output value (type matches target)
                - error_message: Error if evaluation failed

        Type Coercion Rules (ADR-050):
            - TEXT: All formula results converted to string representation
            - NUMBER: Only numeric results allowed (int, float); strings fail
            - BOOLEAN: Truthy/falsy conversion

        Example:
            request = OutputMappingEvaluationRequestDTO(
                entity_id="project",
                field_id="depth_range",
                field_values={"depth_from": 5.0, "depth_to": 10.0}
            )
            result = use_case.execute(request)
            if result.success and result.target == "TEXT":
                # result.value == "5.0 - 10.0"
                pass
        """
        # Fetch output mappings for the field from schema
        try:
            output_mappings: tuple[OutputMappingExportDTO, ...] = (
                self._schema_usecases.list_output_mappings_for_field(
                    entity_id=request.entity_id,
                    field_id=request.field_id,
                )
            )
        except Exception as e:
            # Schema fetch failed → return failure
            return OutputMappingEvaluationResultDTO.failure(
                target="UNKNOWN",
                error_message=f"Failed to fetch output mappings: {str(e)}",
            )

        # No output mappings → return failure (no default for output mappings)
        if not output_mappings:
            return OutputMappingEvaluationResultDTO.failure(
                target="UNKNOWN",
                error_message=f"No output mapping defined for field '{request.field_id}'",
            )

        # Phase R-1: Single output mapping per field
        # In current design, each field can have multiple output mappings with different targets
        # For Phase R-1, we evaluate all of them and return the first successful one
        # TODO Phase R-2: Support target-specific evaluation

        errors: list[str] = []
        for mapping in output_mappings:
            # Evaluate formula using FormulaUseCases
            execution_result = self._formula_usecases.execute_formula(
                formula_text=mapping.formula_text,
                field_values=request.field_values,
            )

            # If formula execution failed, this mapping fails
            if not execution_result.success:
                errors.append(
                    f"Target '{mapping.target}': {execution_result.error}"
                )
                continue

            # Apply type coercion based on target type
            coercion_result = self._coerce_to_target_type(
                value=execution_result.value,
                target=mapping.target,
            )

            if coercion_result["success"]:
                # Successful coercion → return result
                if mapping.target == "TEXT":
                    return OutputMappingEvaluationResultDTO.text_result(
                        value=coercion_result["value"]
                    )
                elif mapping.target == "NUMBER":
                    return OutputMappingEvaluationResultDTO.number_result(
                        value=coercion_result["value"]
                    )
                elif mapping.target == "BOOLEAN":
                    return OutputMappingEvaluationResultDTO.boolean_result(
                        value=coercion_result["value"]
                    )
                else:
                    # Unknown target type
                    errors.append(
                        f"Unknown target type: {mapping.target}"
                    )
                    continue
            else:
                # Type coercion failed
                errors.append(
                    f"Target '{mapping.target}': {coercion_result['error']}"
                )
                continue

        # All mappings failed → return failure
        return OutputMappingEvaluationResultDTO.failure(
            target=output_mappings[0].target if output_mappings else "UNKNOWN",
            error_message=f"All output mappings failed: {'; '.join(errors)}",
        )

    def _coerce_to_target_type(
        self, value: Any, target: str
    ) -> dict[str, Any]:
        """Coerce formula result to target type.

        ADR-050 Type Coercion Rules:
            - TEXT: All formula results converted to string representation
            - NUMBER: Only numeric results allowed (int, float); strings fail
            - BOOLEAN: Truthy/falsy conversion

        Args:
            value: Formula execution result
            target: Target type (TEXT, NUMBER, BOOLEAN)

        Returns:
            Dict with:
                - success: True if coercion succeeded
                - value: Coerced value (if success)
                - error: Error message (if failed)
        """
        if target == "TEXT":
            # TEXT: All values converted to string
            try:
                if value is None:
                    return {"success": True, "value": "", "error": None}
                return {"success": True, "value": str(value), "error": None}
            except Exception as e:
                return {
                    "success": False,
                    "value": None,
                    "error": f"Failed to convert to TEXT: {str(e)}",
                }

        elif target == "NUMBER":
            # NUMBER: Only numeric types allowed (int, float)
            if value is None:
                return {
                    "success": False,
                    "value": None,
                    "error": "Cannot convert None to NUMBER",
                }
            if isinstance(value, bool):
                # Booleans are NOT numbers (ADR-050: strict type enforcement)
                return {
                    "success": False,
                    "value": None,
                    "error": "Cannot convert BOOLEAN to NUMBER",
                }
            if isinstance(value, (int, float)):
                return {"success": True, "value": float(value), "error": None}
            if isinstance(value, str):
                # ADR-050: Strings fail for NUMBER target
                return {
                    "success": False,
                    "value": None,
                    "error": "Cannot convert TEXT to NUMBER (strict type enforcement)",
                }
            return {
                "success": False,
                "value": None,
                "error": f"Cannot convert {type(value).__name__} to NUMBER",
            }

        elif target == "BOOLEAN":
            # BOOLEAN: Truthy/falsy conversion
            if value is None:
                return {"success": True, "value": False, "error": None}
            if isinstance(value, bool):
                return {"success": True, "value": value, "error": None}
            # ADR-050: Truthy/falsy conversion
            # 0, empty string, None → False; all else → True
            if isinstance(value, (int, float)) and value == 0:
                return {"success": True, "value": False, "error": None}
            if isinstance(value, str) and value == "":
                return {"success": True, "value": False, "error": None}
            return {"success": True, "value": True, "error": None}

        else:
            return {
                "success": False,
                "value": None,
                "error": f"Unknown target type: {target}",
            }

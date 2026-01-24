"""Unit tests for EvaluateOutputMappingsUseCase (Phase R-1).

Tests runtime output mapping evaluation following ADR-050 requirements:
- Pull-based evaluation
- Deterministic behavior
- Blocking failures
- Strict type enforcement (TEXT/NUMBER/BOOLEAN)
- Type coercion rules
"""

import pytest

from doc_helper.application.dto.export_dto import OutputMappingExportDTO
from doc_helper.application.dto.runtime_dto import (
    OutputMappingEvaluationRequestDTO,
    OutputMappingEvaluationResultDTO,
)
from doc_helper.application.usecases.formula_usecases import FormulaUseCases
from doc_helper.application.usecases.runtime.evaluate_output_mappings import (
    EvaluateOutputMappingsUseCase,
)


class MockSchemaUseCases:
    """Mock SchemaUseCases for testing."""

    def __init__(self, output_mappings: tuple[OutputMappingExportDTO, ...] | None = None):
        self.output_mappings = output_mappings or ()
        self.should_fail = False

    def list_output_mappings_for_field(self, entity_id: str, field_id: str):
        """Mock list_output_mappings_for_field.

        Returns tuple directly (not wrapped in OperationResultDTO).
        Raises exception on failure instead of returning error result.
        """
        if self.should_fail:
            raise RuntimeError("Schema fetch failed")
        return self.output_mappings


# ============================================================================
# ADR-050 Compliance Tests: TEXT Output
# ============================================================================


def test_text_output_with_string_formula():
    """Test: TEXT output with string formula → success.

    ADR-050: TEXT output - all formula results converted to string representation.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="TEXT",
            formula_text="concat(depth_from, ' - ', depth_to)",
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="depth_range",
        field_values={"depth_from": "5.0", "depth_to": "10.0"},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "TEXT"
    assert result.value == "5.0 - 10.0"
    assert result.error_message is None


def test_text_output_with_number_formula():
    """Test: TEXT output with number formula → converted to string.

    ADR-050: TEXT output - all formula results converted to string representation.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="TEXT",
            formula_text="value1 + value2",  # Returns number
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="total",
        field_values={"value1": 10, "value2": 20},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "TEXT"
    assert result.value == "30"  # Number converted to string
    assert result.error_message is None


def test_text_output_with_none_returns_empty_string():
    """Test: TEXT output with None → empty string.

    ADR-050: TEXT output - None converted to empty string.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="TEXT",
            formula_text="nullable_field",  # Field exists but has None value
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="optional_field",
        field_values={"nullable_field": None},  # Field exists with None value
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "TEXT"
    assert result.value == ""  # None → empty string
    assert result.error_message is None


# ============================================================================
# ADR-050 Compliance Tests: NUMBER Output
# ============================================================================


def test_number_output_with_numeric_formula():
    """Test: NUMBER output with numeric formula → success.

    ADR-050: NUMBER output - only numeric results allowed (int, float).
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="NUMBER",
            formula_text="area * density",  # Returns number
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="total_weight",
        field_values={"area": 10.5, "density": 2.0},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "NUMBER"
    assert result.value == 21.0
    assert result.error_message is None


def test_number_output_with_integer_formula():
    """Test: NUMBER output with integer formula → success (converted to float).

    ADR-050: NUMBER output - int converted to float.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="NUMBER",
            formula_text="value1 + value2",  # Returns int
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="count",
        field_values={"value1": 5, "value2": 10},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "NUMBER"
    assert result.value == 15.0  # Int → float
    assert result.error_message is None


def test_number_output_with_string_formula_fails():
    """Test: NUMBER output with string formula → FAILURE.

    ADR-050: NUMBER output - strings fail (strict type enforcement).
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="NUMBER",
            formula_text="text_field",  # Returns string
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="numeric_field",
        field_values={"text_field": "hello"},
    )

    # Act
    result = use_case.execute(request)

    # Assert - Blocking failure
    assert result.success is False
    assert result.target == "NUMBER"
    assert result.value is None
    assert result.error_message is not None
    assert "Cannot convert TEXT to NUMBER" in result.error_message


def test_number_output_with_boolean_formula_fails():
    """Test: NUMBER output with boolean formula → FAILURE.

    ADR-050: NUMBER output - booleans are NOT numbers (strict type enforcement).
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="NUMBER",
            formula_text="is_active == true",  # Returns boolean
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="numeric_field",
        field_values={"is_active": True},
    )

    # Act
    result = use_case.execute(request)

    # Assert - Blocking failure
    assert result.success is False
    assert result.target == "NUMBER"
    assert result.value is None
    assert result.error_message is not None
    assert "Cannot convert BOOLEAN to NUMBER" in result.error_message


def test_number_output_with_none_fails():
    """Test: NUMBER output with None → FAILURE.

    ADR-050: NUMBER output - None cannot be converted to number.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="NUMBER",
            formula_text="nullable_field",  # Field exists but has None value
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="numeric_field",
        field_values={"nullable_field": None},  # Field exists with None value
    )

    # Act
    result = use_case.execute(request)

    # Assert - Blocking failure
    assert result.success is False
    assert result.target == "NUMBER"
    assert result.value is None
    assert result.error_message is not None
    assert "Cannot convert None to NUMBER" in result.error_message


# ============================================================================
# ADR-050 Compliance Tests: BOOLEAN Output
# ============================================================================


def test_boolean_output_with_boolean_formula():
    """Test: BOOLEAN output with boolean formula → success.

    ADR-050: BOOLEAN output - truthy/falsy conversion.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="BOOLEAN",
            formula_text="status == 'active'",  # Returns boolean
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="is_active",
        field_values={"status": "active"},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "BOOLEAN"
    assert result.value is True
    assert result.error_message is None


def test_boolean_output_with_truthy_number():
    """Test: BOOLEAN output with truthy number (>0) → True.

    ADR-050: BOOLEAN output - truthy/falsy conversion.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="BOOLEAN",
            formula_text="count",  # Returns number
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="has_items",
        field_values={"count": 5},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "BOOLEAN"
    assert result.value is True  # 5 → True (truthy)
    assert result.error_message is None


def test_boolean_output_with_falsy_zero():
    """Test: BOOLEAN output with 0 → False.

    ADR-050: BOOLEAN output - 0, empty string, None → False.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="BOOLEAN",
            formula_text="count",  # Returns number
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="has_items",
        field_values={"count": 0},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "BOOLEAN"
    assert result.value is False  # 0 → False
    assert result.error_message is None


def test_boolean_output_with_empty_string():
    """Test: BOOLEAN output with empty string → False.

    ADR-050: BOOLEAN output - 0, empty string, None → False.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="BOOLEAN",
            formula_text="text_field",  # Returns string
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="has_text",
        field_values={"text_field": ""},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "BOOLEAN"
    assert result.value is False  # "" → False
    assert result.error_message is None


def test_boolean_output_with_nonempty_string():
    """Test: BOOLEAN output with non-empty string → True.

    ADR-050: BOOLEAN output - truthy/falsy conversion.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="BOOLEAN",
            formula_text="text_field",  # Returns string
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="has_text",
        field_values={"text_field": "hello"},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "BOOLEAN"
    assert result.value is True  # "hello" → True (truthy)
    assert result.error_message is None


def test_boolean_output_with_none():
    """Test: BOOLEAN output with None → False.

    ADR-050: BOOLEAN output - 0, empty string, None → False.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="BOOLEAN",
            formula_text="nullable_field",  # Field exists but has None value
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="has_value",
        field_values={"nullable_field": None},  # Field exists with None value
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.target == "BOOLEAN"
    assert result.value is False  # None → False
    assert result.error_message is None


# ============================================================================
# ADR-050 Compliance Tests: Failure Scenarios
# ============================================================================


def test_no_output_mapping_returns_failure():
    """Test: No output mapping → FAILURE (blocking).

    ADR-050: Output mapping failures BLOCK document generation.
    """
    # Arrange
    mock_schema = MockSchemaUseCases(output_mappings=())
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={},
    )

    # Act
    result = use_case.execute(request)

    # Assert - Blocking failure
    assert result.success is False
    assert result.target == "UNKNOWN"
    assert result.value is None
    assert result.error_message is not None
    assert "No output mapping defined" in result.error_message


def test_schema_fetch_failure_returns_failure():
    """Test: Schema fetch failure → FAILURE (blocking).

    ADR-050: Output mapping failures BLOCK document generation.
    """
    # Arrange
    mock_schema = MockSchemaUseCases()
    mock_schema.should_fail = True
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={},
    )

    # Act
    result = use_case.execute(request)

    # Assert - Blocking failure
    assert result.success is False
    assert result.target == "UNKNOWN"
    assert result.value is None
    assert result.error_message is not None
    assert "Failed to fetch output mappings" in result.error_message


def test_formula_execution_failure_returns_failure():
    """Test: Formula execution failure → FAILURE (blocking).

    ADR-050: Output mapping failures BLOCK document generation.
    """
    # Arrange - Formula with syntax error
    output_mappings = (
        OutputMappingExportDTO(
            target="TEXT",
            formula_text="invalid syntax {{",
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={},
    )

    # Act
    result = use_case.execute(request)

    # Assert - Blocking failure
    assert result.success is False
    assert result.target == "TEXT"
    assert result.value is None
    assert result.error_message is not None
    assert "All output mappings failed" in result.error_message


# ============================================================================
# ADR-050 Compliance Tests: Determinism
# ============================================================================


def test_determinism_same_inputs_same_outputs():
    """Test: Determinism - same inputs → same outputs.

    ADR-050: Runtime evaluation MUST be deterministic.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="NUMBER",
            formula_text="value1 * value2",
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="product",
        field_values={"value1": 5, "value2": 10},
    )

    # Act - Evaluate multiple times with same inputs
    result1 = use_case.execute(request)
    result2 = use_case.execute(request)
    result3 = use_case.execute(request)

    # Assert - All results identical
    assert result1.success == result2.success == result3.success is True
    assert result1.target == result2.target == result3.target == "NUMBER"
    assert result1.value == result2.value == result3.value == 50.0
    assert result1.error_message == result2.error_message == result3.error_message is None


# ============================================================================
# ADR-050 Compliance Tests: Unknown Target Type
# ============================================================================


def test_unknown_target_type_returns_failure():
    """Test: Unknown target type → FAILURE.

    ADR-050: Only TEXT/NUMBER/BOOLEAN are supported.
    """
    # Arrange
    output_mappings = (
        OutputMappingExportDTO(
            target="UNKNOWN_TYPE",  # Invalid target
            formula_text="value",
        ),
    )
    mock_schema = MockSchemaUseCases(output_mappings=output_mappings)
    use_case = EvaluateOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = OutputMappingEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={"value": 42},
    )

    # Act
    result = use_case.execute(request)

    # Assert - Blocking failure
    assert result.success is False
    assert result.target == "UNKNOWN_TYPE"
    assert result.value is None
    assert result.error_message is not None
    assert "Unknown target type" in result.error_message

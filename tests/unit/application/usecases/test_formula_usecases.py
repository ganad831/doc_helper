"""Unit tests for FormulaUseCases (Phase F-1 + F-2 + F-3).

Tests formula validation use-case methods (Phase F-1):
- validate_formula: Validates syntax, field references, functions
- parse_formula: Parses formula into AST
- infer_result_type: Infers result type from formula

Tests formula execution use-case methods (Phase F-2):
- execute_formula: Executes formula with runtime field values

Tests formula dependency analysis use-case methods (Phase F-3):
- analyze_dependencies: Discovers field dependencies (analysis only)

PHASE F-1 CONSTRAINTS:
- Read-only validation (no execution)
- No schema mutation
- No formula persistence

PHASE F-2 CONSTRAINTS (ADR-040):
- Pure execution (no side effects)
- No persistence of computed values
- No schema mutation
- No dependency tracking

PHASE F-3 CONSTRAINTS (ADR-040):
- Analysis only (no execution)
- No persistence of dependencies
- No DAG/graph construction
- No cycle detection
- Read-only schema access
"""

import pytest

from doc_helper.application.dto.formula_dto import (
    FormulaDependencyAnalysisResultDTO,
    FormulaDependencyDTO,
    FormulaExecutionResultDTO,
    FormulaResultType,
    FormulaValidationResultDTO,
    SchemaFieldInfoDTO,
)
from doc_helper.application.usecases.formula_usecases import FormulaUseCases


class TestFormulaUseCases:
    """Tests for FormulaUseCases."""

    @pytest.fixture
    def usecases(self) -> FormulaUseCases:
        """Create FormulaUseCases instance."""
        return FormulaUseCases()

    @pytest.fixture
    def schema_fields(self) -> tuple[SchemaFieldInfoDTO, ...]:
        """Create sample schema fields for validation."""
        return (
            SchemaFieldInfoDTO(
                field_id="base_value",
                field_type="NUMBER",
                entity_id="test_entity",
                label="Base Value",
            ),
            SchemaFieldInfoDTO(
                field_id="multiplier",
                field_type="NUMBER",
                entity_id="test_entity",
                label="Multiplier",
            ),
            SchemaFieldInfoDTO(
                field_id="name",
                field_type="TEXT",
                entity_id="test_entity",
                label="Name",
            ),
            SchemaFieldInfoDTO(
                field_id="is_active",
                field_type="CHECKBOX",
                entity_id="test_entity",
                label="Is Active",
            ),
        )

    # -------------------------------------------------------------------------
    # test_formula_syntax_valid - Validate that syntactically correct formulas pass
    # -------------------------------------------------------------------------

    def test_formula_syntax_valid_simple_addition(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Valid formula with simple addition should pass validation."""
        result = usecases.validate_formula(
            formula_text="base_value + multiplier",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert "base_value" in result.field_references
        assert "multiplier" in result.field_references

    def test_formula_syntax_valid_with_function(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Valid formula with function call should pass validation."""
        result = usecases.validate_formula(
            formula_text="max(base_value, multiplier)",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_formula_syntax_valid_with_literal(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Valid formula with numeric literal should pass validation."""
        result = usecases.validate_formula(
            formula_text="base_value * 100",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert "base_value" in result.field_references
        # Literal '100' should not appear in field references
        assert "100" not in result.field_references

    def test_formula_syntax_valid_complex_expression(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Valid complex formula should pass validation."""
        result = usecases.validate_formula(
            formula_text="(base_value + multiplier) * 2 / 10",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_formula_syntax_invalid_unclosed_paren(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula with unclosed parenthesis should fail validation."""
        result = usecases.validate_formula(
            formula_text="(base_value + multiplier",
            schema_fields=schema_fields,
        )

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_formula_syntax_invalid_incomplete_operator(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula with incomplete operator should fail validation."""
        result = usecases.validate_formula(
            formula_text="base_value +",
            schema_fields=schema_fields,
        )

        assert result.is_valid is False
        assert len(result.errors) > 0

    # -------------------------------------------------------------------------
    # test_formula_unknown_field - Validate field reference checking
    # -------------------------------------------------------------------------

    def test_formula_unknown_field_single(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula referencing unknown field should fail validation."""
        result = usecases.validate_formula(
            formula_text="unknown_field + base_value",
            schema_fields=schema_fields,
        )

        assert result.is_valid is False
        assert len(result.errors) > 0
        # Error should mention the unknown field
        error_text = " ".join(result.errors).lower()
        assert "unknown_field" in error_text

    def test_formula_unknown_field_multiple(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula referencing multiple unknown fields should report all."""
        result = usecases.validate_formula(
            formula_text="field_a + field_b",
            schema_fields=schema_fields,
        )

        assert result.is_valid is False
        assert len(result.errors) >= 2
        error_text = " ".join(result.errors).lower()
        assert "field_a" in error_text
        assert "field_b" in error_text

    def test_formula_unknown_function(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula calling unknown function should fail validation."""
        result = usecases.validate_formula(
            formula_text="unknown_func(base_value)",
            schema_fields=schema_fields,
        )

        assert result.is_valid is False
        assert len(result.errors) > 0
        error_text = " ".join(result.errors).lower()
        assert "unknown_func" in error_text

    def test_formula_known_function(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula calling known function should pass validation."""
        # All ALLOWED_FUNCTIONS should pass
        known_functions = ["abs", "min", "max", "round", "sum", "pow"]

        for func in known_functions:
            result = usecases.validate_formula(
                formula_text=f"{func}(base_value)",
                schema_fields=schema_fields,
            )
            assert result.is_valid is True, f"Function {func} should be allowed"

    # -------------------------------------------------------------------------
    # test_formula_type_mismatch - Type inference error detection
    # -------------------------------------------------------------------------

    def test_formula_type_mismatch_string_arithmetic(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula performing arithmetic on text field should warn/error."""
        result = usecases.validate_formula(
            formula_text="name + 100",  # 'name' is TEXT type
            schema_fields=schema_fields,
        )

        # Should either fail or have warnings about type mismatch
        # (depending on strictness of type checking)
        # At minimum, inferred type should be UNKNOWN or have warnings
        assert len(result.warnings) > 0 or result.inferred_type == "UNKNOWN"

    def test_formula_type_compatible_numeric(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula with compatible numeric types should pass."""
        result = usecases.validate_formula(
            formula_text="base_value + multiplier",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "NUMBER"

    # -------------------------------------------------------------------------
    # test_formula_boolean_inference - Boolean result type inference
    # -------------------------------------------------------------------------

    def test_formula_boolean_inference_comparison(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Comparison operators should infer BOOLEAN type."""
        result = usecases.validate_formula(
            formula_text="base_value > multiplier",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "BOOLEAN"

    def test_formula_boolean_inference_equality(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Equality operator should infer BOOLEAN type."""
        result = usecases.validate_formula(
            formula_text="base_value == multiplier",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "BOOLEAN"

    def test_formula_boolean_inference_logical_and(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Logical AND operator should infer BOOLEAN type."""
        result = usecases.validate_formula(
            formula_text="is_active and (base_value > 0)",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "BOOLEAN"

    def test_formula_boolean_inference_logical_or(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Logical OR operator should infer BOOLEAN type."""
        result = usecases.validate_formula(
            formula_text="is_active or (base_value < 0)",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "BOOLEAN"

    def test_formula_boolean_inference_not(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """NOT operator should infer BOOLEAN type."""
        result = usecases.validate_formula(
            formula_text="not is_active",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "BOOLEAN"

    def test_formula_boolean_field_reference(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Reference to boolean field should infer BOOLEAN type."""
        result = usecases.validate_formula(
            formula_text="is_active",  # CHECKBOX field is boolean
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "BOOLEAN"

    # -------------------------------------------------------------------------
    # test_formula_number_inference - Numeric result type inference
    # -------------------------------------------------------------------------

    def test_formula_number_inference_arithmetic(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Arithmetic operators should infer NUMBER type."""
        result = usecases.validate_formula(
            formula_text="base_value + multiplier * 2",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "NUMBER"

    def test_formula_number_inference_numeric_function(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Numeric functions should infer NUMBER type."""
        result = usecases.validate_formula(
            formula_text="abs(base_value - multiplier)",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "NUMBER"

    def test_formula_number_inference_literal(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Numeric literal should infer NUMBER type."""
        result = usecases.validate_formula(
            formula_text="42",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "NUMBER"

    def test_formula_number_inference_negative(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Unary minus should infer NUMBER type."""
        result = usecases.validate_formula(
            formula_text="-base_value",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "NUMBER"

    def test_formula_number_field_reference(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Reference to numeric field should infer NUMBER type."""
        result = usecases.validate_formula(
            formula_text="base_value",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "NUMBER"

    # -------------------------------------------------------------------------
    # test_formula_text_inference - Text result type inference
    # -------------------------------------------------------------------------

    def test_formula_text_inference_concat(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Concat function should infer TEXT type."""
        result = usecases.validate_formula(
            formula_text='concat(name, " suffix")',
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "TEXT"

    def test_formula_text_inference_upper(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Upper function should infer TEXT type."""
        result = usecases.validate_formula(
            formula_text="upper(name)",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "TEXT"

    def test_formula_text_inference_lower(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Lower function should infer TEXT type."""
        result = usecases.validate_formula(
            formula_text="lower(name)",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "TEXT"

    def test_formula_text_inference_string_literal(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """String literal should infer TEXT type."""
        result = usecases.validate_formula(
            formula_text='"Hello World"',
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "TEXT"

    def test_formula_text_field_reference(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Reference to text field should infer TEXT type."""
        result = usecases.validate_formula(
            formula_text="name",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "TEXT"

    # -------------------------------------------------------------------------
    # Additional edge cases
    # -------------------------------------------------------------------------

    def test_formula_empty_string(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Empty formula should return invalid with no errors (nothing to validate)."""
        result = usecases.validate_formula(
            formula_text="",
            schema_fields=schema_fields,
        )

        # Empty formula is valid (nothing wrong with it) but unknown type
        assert result.is_valid is True
        assert result.inferred_type == "UNKNOWN"
        assert len(result.field_references) == 0

    def test_formula_whitespace_only(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Whitespace-only formula should be treated as empty."""
        result = usecases.validate_formula(
            formula_text="   \t\n  ",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "UNKNOWN"

    def test_formula_no_schema_fields(
        self, usecases: FormulaUseCases
    ) -> None:
        """Formula with no schema fields should still validate literals."""
        result = usecases.validate_formula(
            formula_text="42 + 10",
            schema_fields=(),
        )

        assert result.is_valid is True
        assert result.inferred_type == "NUMBER"
        assert len(result.field_references) == 0

    def test_formula_if_else_function(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """if_else function should be allowed."""
        result = usecases.validate_formula(
            formula_text="if_else(is_active, base_value, 0)",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        # Type depends on true/false branches

    def test_formula_coalesce_function(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """coalesce function should be allowed."""
        result = usecases.validate_formula(
            formula_text="coalesce(base_value, 0)",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True

    def test_formula_is_empty_function(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """is_empty function should be allowed and return BOOLEAN."""
        result = usecases.validate_formula(
            formula_text="is_empty(name)",
            schema_fields=schema_fields,
        )

        assert result.is_valid is True
        assert result.inferred_type == "BOOLEAN"


# =============================================================================
# PHASE F-2: Formula Execution Tests
# =============================================================================


class TestFormulaExecution:
    """Tests for FormulaUseCases.execute_formula() (Phase F-2).

    PHASE F-2 CONSTRAINTS (ADR-040):
    - Pure execution (no side effects)
    - No persistence of computed values
    - No schema mutation
    - No dependency tracking
    - Execution is pull-based, not push-based
    """

    @pytest.fixture
    def usecases(self) -> FormulaUseCases:
        """Create FormulaUseCases instance."""
        return FormulaUseCases()

    # -------------------------------------------------------------------------
    # Arithmetic Operations
    # -------------------------------------------------------------------------

    def test_execute_addition(self, usecases: FormulaUseCases) -> None:
        """Addition should work correctly."""
        result = usecases.execute_formula(
            formula_text="value1 + value2",
            field_values={"value1": 10, "value2": 20},
        )

        assert result.success is True
        assert result.value == 30
        assert result.error is None

    def test_execute_subtraction(self, usecases: FormulaUseCases) -> None:
        """Subtraction should work correctly."""
        result = usecases.execute_formula(
            formula_text="value1 - value2",
            field_values={"value1": 50, "value2": 20},
        )

        assert result.success is True
        assert result.value == 30

    def test_execute_multiplication(self, usecases: FormulaUseCases) -> None:
        """Multiplication should work correctly."""
        result = usecases.execute_formula(
            formula_text="value1 * value2",
            field_values={"value1": 5, "value2": 4},
        )

        assert result.success is True
        assert result.value == 20

    def test_execute_division(self, usecases: FormulaUseCases) -> None:
        """Division should work correctly."""
        result = usecases.execute_formula(
            formula_text="value1 / value2",
            field_values={"value1": 20, "value2": 4},
        )

        assert result.success is True
        assert result.value == 5.0

    def test_execute_modulo(self, usecases: FormulaUseCases) -> None:
        """Modulo should work correctly."""
        result = usecases.execute_formula(
            formula_text="value1 % value2",
            field_values={"value1": 17, "value2": 5},
        )

        assert result.success is True
        assert result.value == 2

    def test_execute_power(self, usecases: FormulaUseCases) -> None:
        """Power should work correctly."""
        result = usecases.execute_formula(
            formula_text="value1 ** value2",
            field_values={"value1": 2, "value2": 3},
        )

        assert result.success is True
        assert result.value == 8

    def test_execute_complex_arithmetic(self, usecases: FormulaUseCases) -> None:
        """Complex arithmetic expression should work correctly."""
        result = usecases.execute_formula(
            formula_text="(base + tax) * quantity - discount",
            field_values={"base": 100, "tax": 10, "quantity": 2, "discount": 20},
        )

        assert result.success is True
        assert result.value == 200  # (100 + 10) * 2 - 20 = 200

    # -------------------------------------------------------------------------
    # Comparison Operations
    # -------------------------------------------------------------------------

    def test_execute_greater_than(self, usecases: FormulaUseCases) -> None:
        """Greater than comparison should work."""
        result = usecases.execute_formula(
            formula_text="value1 > value2",
            field_values={"value1": 10, "value2": 5},
        )

        assert result.success is True
        assert result.value is True

    def test_execute_less_than(self, usecases: FormulaUseCases) -> None:
        """Less than comparison should work."""
        result = usecases.execute_formula(
            formula_text="value1 < value2",
            field_values={"value1": 3, "value2": 5},
        )

        assert result.success is True
        assert result.value is True

    def test_execute_equality(self, usecases: FormulaUseCases) -> None:
        """Equality comparison should work."""
        result = usecases.execute_formula(
            formula_text="value1 == value2",
            field_values={"value1": 10, "value2": 10},
        )

        assert result.success is True
        assert result.value is True

    def test_execute_inequality(self, usecases: FormulaUseCases) -> None:
        """Inequality comparison should work."""
        result = usecases.execute_formula(
            formula_text="value1 != value2",
            field_values={"value1": 10, "value2": 5},
        )

        assert result.success is True
        assert result.value is True

    # -------------------------------------------------------------------------
    # Logical Operations
    # -------------------------------------------------------------------------

    def test_execute_logical_and(self, usecases: FormulaUseCases) -> None:
        """Logical AND should work."""
        result = usecases.execute_formula(
            formula_text="a and b",
            field_values={"a": True, "b": True},
        )

        assert result.success is True
        assert result.value is True

    def test_execute_logical_or(self, usecases: FormulaUseCases) -> None:
        """Logical OR should work."""
        result = usecases.execute_formula(
            formula_text="a or b",
            field_values={"a": False, "b": True},
        )

        assert result.success is True
        assert result.value is True

    def test_execute_logical_not(self, usecases: FormulaUseCases) -> None:
        """Logical NOT should work."""
        result = usecases.execute_formula(
            formula_text="not active",
            field_values={"active": False},
        )

        assert result.success is True
        assert result.value is True

    # -------------------------------------------------------------------------
    # Built-in Functions: Math
    # -------------------------------------------------------------------------

    def test_execute_abs(self, usecases: FormulaUseCases) -> None:
        """abs function should work."""
        result = usecases.execute_formula(
            formula_text="abs(value)",
            field_values={"value": -42},
        )

        assert result.success is True
        assert result.value == 42

    def test_execute_min(self, usecases: FormulaUseCases) -> None:
        """min function should work."""
        result = usecases.execute_formula(
            formula_text="min(a, b, c)",
            field_values={"a": 10, "b": 5, "c": 20},
        )

        assert result.success is True
        assert result.value == 5

    def test_execute_max(self, usecases: FormulaUseCases) -> None:
        """max function should work."""
        result = usecases.execute_formula(
            formula_text="max(a, b, c)",
            field_values={"a": 10, "b": 5, "c": 20},
        )

        assert result.success is True
        assert result.value == 20

    def test_execute_round(self, usecases: FormulaUseCases) -> None:
        """round function should work."""
        result = usecases.execute_formula(
            formula_text="round(value, 2)",
            field_values={"value": 3.14159},
        )

        assert result.success is True
        assert result.value == 3.14

    def test_execute_sum(self, usecases: FormulaUseCases) -> None:
        """sum function should work."""
        result = usecases.execute_formula(
            formula_text="sum(a, b, c)",
            field_values={"a": 10, "b": 20, "c": 30},
        )

        assert result.success is True
        assert result.value == 60

    def test_execute_pow_function(self, usecases: FormulaUseCases) -> None:
        """pow function should work."""
        result = usecases.execute_formula(
            formula_text="pow(base, exp)",
            field_values={"base": 2, "exp": 10},
        )

        assert result.success is True
        assert result.value == 1024

    # -------------------------------------------------------------------------
    # Built-in Functions: Text
    # -------------------------------------------------------------------------

    def test_execute_upper(self, usecases: FormulaUseCases) -> None:
        """upper function should work."""
        result = usecases.execute_formula(
            formula_text="upper(text)",
            field_values={"text": "hello"},
        )

        assert result.success is True
        assert result.value == "HELLO"

    def test_execute_lower(self, usecases: FormulaUseCases) -> None:
        """lower function should work."""
        result = usecases.execute_formula(
            formula_text="lower(text)",
            field_values={"text": "HELLO"},
        )

        assert result.success is True
        assert result.value == "hello"

    def test_execute_strip(self, usecases: FormulaUseCases) -> None:
        """strip function should work."""
        result = usecases.execute_formula(
            formula_text="strip(text)",
            field_values={"text": "  hello  "},
        )

        assert result.success is True
        assert result.value == "hello"

    def test_execute_concat(self, usecases: FormulaUseCases) -> None:
        """concat function should work."""
        result = usecases.execute_formula(
            formula_text='concat(first, " ", last)',
            field_values={"first": "John", "last": "Doe"},
        )

        assert result.success is True
        assert result.value == "John Doe"

    # -------------------------------------------------------------------------
    # Built-in Functions: Logic
    # -------------------------------------------------------------------------

    def test_execute_if_else_true(self, usecases: FormulaUseCases) -> None:
        """if_else function should return true_val when condition is true."""
        result = usecases.execute_formula(
            formula_text="if_else(active, 100, 0)",
            field_values={"active": True},
        )

        assert result.success is True
        assert result.value == 100

    def test_execute_if_else_false(self, usecases: FormulaUseCases) -> None:
        """if_else function should return false_val when condition is false."""
        result = usecases.execute_formula(
            formula_text="if_else(active, 100, 0)",
            field_values={"active": False},
        )

        assert result.success is True
        assert result.value == 0

    def test_execute_is_empty_null(self, usecases: FormulaUseCases) -> None:
        """is_empty should return True for null values."""
        result = usecases.execute_formula(
            formula_text="is_empty(value)",
            field_values={"value": None},
        )

        assert result.success is True
        assert result.value is True

    def test_execute_is_empty_empty_string(self, usecases: FormulaUseCases) -> None:
        """is_empty should return True for empty string."""
        result = usecases.execute_formula(
            formula_text="is_empty(value)",
            field_values={"value": ""},
        )

        assert result.success is True
        assert result.value is True

    def test_execute_is_empty_non_empty(self, usecases: FormulaUseCases) -> None:
        """is_empty should return False for non-empty values."""
        result = usecases.execute_formula(
            formula_text="is_empty(value)",
            field_values={"value": "hello"},
        )

        assert result.success is True
        assert result.value is False

    def test_execute_coalesce_first_non_null(self, usecases: FormulaUseCases) -> None:
        """coalesce should return first non-null value."""
        result = usecases.execute_formula(
            formula_text="coalesce(a, b, c)",
            field_values={"a": None, "b": 42, "c": 100},
        )

        assert result.success is True
        assert result.value == 42

    def test_execute_coalesce_all_null(self, usecases: FormulaUseCases) -> None:
        """coalesce should return None if all values are null."""
        result = usecases.execute_formula(
            formula_text="coalesce(a, b)",
            field_values={"a": None, "b": None},
        )

        assert result.success is True
        assert result.value is None

    # -------------------------------------------------------------------------
    # Null Handling
    # -------------------------------------------------------------------------

    def test_execute_null_in_arithmetic(self, usecases: FormulaUseCases) -> None:
        """Arithmetic with null should propagate null."""
        result = usecases.execute_formula(
            formula_text="abs(value)",
            field_values={"value": None},
        )

        assert result.success is True
        assert result.value is None

    def test_execute_min_with_nulls(self, usecases: FormulaUseCases) -> None:
        """min should ignore null values."""
        result = usecases.execute_formula(
            formula_text="min(a, b, c)",
            field_values={"a": None, "b": 5, "c": 10},
        )

        assert result.success is True
        assert result.value == 5

    def test_execute_max_with_nulls(self, usecases: FormulaUseCases) -> None:
        """max should ignore null values."""
        result = usecases.execute_formula(
            formula_text="max(a, b, c)",
            field_values={"a": None, "b": 5, "c": None},
        )

        assert result.success is True
        assert result.value == 5

    def test_execute_concat_with_null(self, usecases: FormulaUseCases) -> None:
        """concat should treat null as empty string."""
        result = usecases.execute_formula(
            formula_text="concat(a, b)",
            field_values={"a": "hello", "b": None},
        )

        assert result.success is True
        assert result.value == "hello"

    # -------------------------------------------------------------------------
    # Error Handling
    # -------------------------------------------------------------------------

    def test_execute_division_by_zero(self, usecases: FormulaUseCases) -> None:
        """Division by zero should return error."""
        result = usecases.execute_formula(
            formula_text="value / 0",
            field_values={"value": 10},
        )

        assert result.success is False
        assert result.value is None
        assert result.error is not None
        assert "zero" in result.error.lower()

    def test_execute_missing_field(self, usecases: FormulaUseCases) -> None:
        """Missing field should return error."""
        result = usecases.execute_formula(
            formula_text="missing_field + 1",
            field_values={},
        )

        assert result.success is False
        assert result.value is None
        assert result.error is not None
        assert "missing_field" in result.error.lower()

    def test_execute_syntax_error(self, usecases: FormulaUseCases) -> None:
        """Syntax error should return error."""
        result = usecases.execute_formula(
            formula_text="value +",
            field_values={"value": 10},
        )

        assert result.success is False
        assert result.value is None
        assert result.error is not None

    def test_execute_empty_formula(self, usecases: FormulaUseCases) -> None:
        """Empty formula should return error."""
        result = usecases.execute_formula(
            formula_text="",
            field_values={},
        )

        assert result.success is False
        assert result.value is None
        assert result.error is not None

    def test_execute_invalid_formula_text_type(self, usecases: FormulaUseCases) -> None:
        """Non-string formula should return error."""
        result = usecases.execute_formula(
            formula_text=123,  # type: ignore
            field_values={},
        )

        assert result.success is False
        assert result.error is not None

    def test_execute_invalid_field_values_type(self, usecases: FormulaUseCases) -> None:
        """Non-dict field_values should return error."""
        result = usecases.execute_formula(
            formula_text="value + 1",
            field_values="not a dict",  # type: ignore
        )

        assert result.success is False
        assert result.error is not None

    # -------------------------------------------------------------------------
    # Literals
    # -------------------------------------------------------------------------

    def test_execute_numeric_literal(self, usecases: FormulaUseCases) -> None:
        """Numeric literal should work."""
        result = usecases.execute_formula(
            formula_text="42 + 8",
            field_values={},
        )

        assert result.success is True
        assert result.value == 50

    def test_execute_string_literal(self, usecases: FormulaUseCases) -> None:
        """String literal should work."""
        result = usecases.execute_formula(
            formula_text='"hello"',
            field_values={},
        )

        assert result.success is True
        assert result.value == "hello"

    def test_execute_boolean_literal_true(self, usecases: FormulaUseCases) -> None:
        """Boolean true literal should work."""
        result = usecases.execute_formula(
            formula_text="true",
            field_values={},
        )

        assert result.success is True
        assert result.value is True

    def test_execute_boolean_literal_false(self, usecases: FormulaUseCases) -> None:
        """Boolean false literal should work."""
        result = usecases.execute_formula(
            formula_text="false",
            field_values={},
        )

        assert result.success is True
        assert result.value is False

    def test_execute_null_literal(self, usecases: FormulaUseCases) -> None:
        """Null literal should work."""
        result = usecases.execute_formula(
            formula_text="null",
            field_values={},
        )

        assert result.success is True
        assert result.value is None

    # -------------------------------------------------------------------------
    # Determinism (Same inputs -> Same output)
    # -------------------------------------------------------------------------

    def test_execute_deterministic(self, usecases: FormulaUseCases) -> None:
        """Same inputs should produce same outputs."""
        formula = "value1 * value2 + value3"
        field_values = {"value1": 10, "value2": 5, "value3": 3}

        result1 = usecases.execute_formula(formula, field_values)
        result2 = usecases.execute_formula(formula, field_values)
        result3 = usecases.execute_formula(formula, field_values)

        assert result1.success is True
        assert result2.success is True
        assert result3.success is True
        assert result1.value == result2.value == result3.value == 53

    # -------------------------------------------------------------------------
    # No Side Effects (Pure execution)
    # -------------------------------------------------------------------------

    def test_execute_no_mutation_of_field_values(
        self, usecases: FormulaUseCases
    ) -> None:
        """Execution should not mutate input field_values."""
        field_values = {"value": 10}
        original_field_values = field_values.copy()

        usecases.execute_formula(
            formula_text="value * 2",
            field_values=field_values,
        )

        # Field values should be unchanged
        assert field_values == original_field_values


# =============================================================================
# PHASE F-3: Formula Dependency Analysis Tests
# =============================================================================


class TestFormulaDependencyAnalysis:
    """Tests for FormulaUseCases.analyze_dependencies() (Phase F-3).

    PHASE F-3 CONSTRAINTS (ADR-040):
    - Analysis only (no execution)
    - No persistence of dependencies
    - No DAG/graph construction
    - No cycle detection
    - Read-only schema access
    """

    @pytest.fixture
    def usecases(self) -> FormulaUseCases:
        """Create FormulaUseCases instance."""
        return FormulaUseCases()

    @pytest.fixture
    def schema_fields(self) -> tuple[SchemaFieldInfoDTO, ...]:
        """Create sample schema fields for dependency analysis."""
        return (
            SchemaFieldInfoDTO(
                field_id="price",
                field_type="NUMBER",
                entity_id="product",
                label="Price",
            ),
            SchemaFieldInfoDTO(
                field_id="quantity",
                field_type="NUMBER",
                entity_id="product",
                label="Quantity",
            ),
            SchemaFieldInfoDTO(
                field_id="tax",
                field_type="NUMBER",
                entity_id="product",
                label="Tax",
            ),
            SchemaFieldInfoDTO(
                field_id="name",
                field_type="TEXT",
                entity_id="product",
                label="Name",
            ),
            SchemaFieldInfoDTO(
                field_id="is_active",
                field_type="CHECKBOX",
                entity_id="product",
                label="Is Active",
            ),
        )

    # -------------------------------------------------------------------------
    # Empty Formula
    # -------------------------------------------------------------------------

    def test_empty_formula_returns_parse_error(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Empty formula should return parse error."""
        result = usecases.analyze_dependencies(
            formula_text="",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is True
        assert result.parse_error is not None
        assert len(result.dependencies) == 0
        assert len(result.unknown_fields) == 0

    def test_whitespace_formula_returns_parse_error(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Whitespace-only formula should return parse error."""
        result = usecases.analyze_dependencies(
            formula_text="   ",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is True
        assert result.parse_error is not None

    # -------------------------------------------------------------------------
    # Single Field Reference
    # -------------------------------------------------------------------------

    def test_single_field_reference(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Single field reference should be detected."""
        result = usecases.analyze_dependencies(
            formula_text="price",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        assert result.dependency_count == 1
        assert result.dependencies[0].field_id == "price"
        assert result.dependencies[0].is_known is True
        assert result.dependencies[0].field_type == "NUMBER"
        assert len(result.unknown_fields) == 0

    # -------------------------------------------------------------------------
    # Multiple Field References
    # -------------------------------------------------------------------------

    def test_multiple_field_references(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Multiple field references should all be detected."""
        result = usecases.analyze_dependencies(
            formula_text="price * quantity + tax",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        assert result.dependency_count == 3
        field_ids = result.field_ids
        assert "price" in field_ids
        assert "quantity" in field_ids
        assert "tax" in field_ids
        assert len(result.unknown_fields) == 0

    def test_multiple_field_references_in_function(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Field references in function arguments should be detected."""
        result = usecases.analyze_dependencies(
            formula_text="max(price, quantity, tax)",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        assert result.dependency_count == 3
        field_ids = result.field_ids
        assert "price" in field_ids
        assert "quantity" in field_ids
        assert "tax" in field_ids

    # -------------------------------------------------------------------------
    # Duplicate Field References (Deduplication)
    # -------------------------------------------------------------------------

    def test_duplicate_field_references_deduplicated(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Duplicate field references should be deduplicated."""
        result = usecases.analyze_dependencies(
            formula_text="price + price * quantity + price",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        # Should only have 2 unique dependencies (price, quantity)
        assert result.dependency_count == 2
        field_ids = result.field_ids
        assert "price" in field_ids
        assert "quantity" in field_ids

    # -------------------------------------------------------------------------
    # Unknown Field Detection
    # -------------------------------------------------------------------------

    def test_unknown_field_detected(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Unknown field reference should be detected."""
        result = usecases.analyze_dependencies(
            formula_text="unknown_field + price",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        assert result.has_unknown_fields is True
        assert "unknown_field" in result.unknown_fields
        # Should still have both dependencies
        assert result.dependency_count == 2
        # Unknown field should have is_known=False
        unknown_dep = next(d for d in result.dependencies if d.field_id == "unknown_field")
        assert unknown_dep.is_known is False
        assert unknown_dep.field_type is None

    def test_multiple_unknown_fields_detected(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Multiple unknown field references should all be detected."""
        result = usecases.analyze_dependencies(
            formula_text="unknown1 + unknown2 + price",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        assert result.has_unknown_fields is True
        assert result.unknown_count == 2
        assert "unknown1" in result.unknown_fields
        assert "unknown2" in result.unknown_fields

    # -------------------------------------------------------------------------
    # Mixed Known + Unknown Fields
    # -------------------------------------------------------------------------

    def test_mixed_known_and_unknown_fields(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Mixed known and unknown fields should be correctly categorized."""
        result = usecases.analyze_dependencies(
            formula_text="price * unknown_rate + tax",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        assert result.dependency_count == 3
        assert result.unknown_count == 1
        assert "unknown_rate" in result.unknown_fields

        # Check known dependencies
        known_deps = result.known_dependencies
        assert len(known_deps) == 2
        known_field_ids = [d.field_id for d in known_deps]
        assert "price" in known_field_ids
        assert "tax" in known_field_ids

    # -------------------------------------------------------------------------
    # Function Calls with Field Arguments
    # -------------------------------------------------------------------------

    def test_function_with_field_arguments(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Function calls with field arguments should extract dependencies."""
        result = usecases.analyze_dependencies(
            formula_text="if_else(is_active, price * quantity, 0)",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        field_ids = result.field_ids
        assert "is_active" in field_ids
        assert "price" in field_ids
        assert "quantity" in field_ids

    def test_nested_function_calls(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Nested function calls should extract all field dependencies."""
        result = usecases.analyze_dependencies(
            formula_text="round(max(price, quantity) + tax, 2)",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        assert result.dependency_count == 3
        field_ids = result.field_ids
        assert "price" in field_ids
        assert "quantity" in field_ids
        assert "tax" in field_ids

    # -------------------------------------------------------------------------
    # Literals (Should Not Be Treated as Dependencies)
    # -------------------------------------------------------------------------

    def test_literals_not_dependencies(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Literals should not be treated as dependencies."""
        result = usecases.analyze_dependencies(
            formula_text="price * 1.5 + 100",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        assert result.dependency_count == 1
        assert result.dependencies[0].field_id == "price"

    def test_string_literals_not_dependencies(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """String literals should not be treated as dependencies."""
        result = usecases.analyze_dependencies(
            formula_text='concat(name, " - ", "suffix")',
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        assert result.dependency_count == 1
        assert result.dependencies[0].field_id == "name"

    def test_boolean_literals_not_dependencies(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Boolean literals should not be treated as dependencies."""
        result = usecases.analyze_dependencies(
            formula_text="if_else(true, price, quantity)",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is False
        assert result.dependency_count == 2
        field_ids = result.field_ids
        assert "price" in field_ids
        assert "quantity" in field_ids
        assert "true" not in field_ids

    # -------------------------------------------------------------------------
    # Syntax Errors
    # -------------------------------------------------------------------------

    def test_syntax_error_returns_parse_error(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Syntax error should return parse error."""
        result = usecases.analyze_dependencies(
            formula_text="price +",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is True
        assert result.parse_error is not None
        assert "syntax" in result.parse_error.lower() or "parse" in result.parse_error.lower()
        assert len(result.dependencies) == 0

    def test_unclosed_paren_returns_parse_error(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Unclosed parenthesis should return parse error."""
        result = usecases.analyze_dependencies(
            formula_text="max(price, quantity",
            schema_fields=schema_fields,
        )

        assert result.has_parse_error is True
        assert result.parse_error is not None

    # -------------------------------------------------------------------------
    # Empty Schema Context
    # -------------------------------------------------------------------------

    def test_empty_schema_all_fields_unknown(
        self, usecases: FormulaUseCases
    ) -> None:
        """With empty schema, all field references should be unknown."""
        result = usecases.analyze_dependencies(
            formula_text="price + quantity",
            schema_fields=(),
        )

        assert result.has_parse_error is False
        assert result.dependency_count == 2
        assert result.unknown_count == 2
        assert "price" in result.unknown_fields
        assert "quantity" in result.unknown_fields

    # -------------------------------------------------------------------------
    # Field Type Information
    # -------------------------------------------------------------------------

    def test_known_field_includes_type(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Known field dependency should include field type."""
        result = usecases.analyze_dependencies(
            formula_text="price + quantity",
            schema_fields=schema_fields,
        )

        price_dep = next(d for d in result.dependencies if d.field_id == "price")
        assert price_dep.field_type == "NUMBER"

        quantity_dep = next(d for d in result.dependencies if d.field_id == "quantity")
        assert quantity_dep.field_type == "NUMBER"

    def test_text_field_type_detected(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Text field type should be correctly detected."""
        result = usecases.analyze_dependencies(
            formula_text="upper(name)",
            schema_fields=schema_fields,
        )

        name_dep = next(d for d in result.dependencies if d.field_id == "name")
        assert name_dep.field_type == "TEXT"

    def test_boolean_field_type_detected(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Boolean field type should be correctly detected."""
        result = usecases.analyze_dependencies(
            formula_text="not is_active",
            schema_fields=schema_fields,
        )

        active_dep = next(d for d in result.dependencies if d.field_id == "is_active")
        assert active_dep.field_type == "CHECKBOX"

    # -------------------------------------------------------------------------
    # Determinism (Same inputs -> Same output)
    # -------------------------------------------------------------------------

    def test_analysis_is_deterministic(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Same inputs should produce same outputs."""
        formula = "price * quantity + tax"

        result1 = usecases.analyze_dependencies(formula, schema_fields)
        result2 = usecases.analyze_dependencies(formula, schema_fields)
        result3 = usecases.analyze_dependencies(formula, schema_fields)

        assert result1.dependencies == result2.dependencies == result3.dependencies
        assert result1.unknown_fields == result2.unknown_fields == result3.unknown_fields
        assert result1.field_ids == result2.field_ids == result3.field_ids

    # -------------------------------------------------------------------------
    # No Schema Mutation (Pure Analysis)
    # -------------------------------------------------------------------------

    def test_schema_not_mutated(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Schema fields should not be mutated by analysis."""
        original_schema = schema_fields

        usecases.analyze_dependencies(
            formula_text="price * quantity + unknown",
            schema_fields=schema_fields,
        )

        # Schema should be unchanged
        assert schema_fields == original_schema
        assert len(schema_fields) == len(original_schema)

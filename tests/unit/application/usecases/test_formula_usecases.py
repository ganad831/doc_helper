"""Unit tests for FormulaUseCases (Phase F-1 + F-2 + F-3 + F-4 + F-6 + F-7).

Tests formula validation use-case methods (Phase F-1):
- validate_formula: Validates syntax, field references, functions
- parse_formula: Parses formula into AST
- infer_result_type: Infers result type from formula

Tests formula execution use-case methods (Phase F-2):
- execute_formula: Executes formula with runtime field values

Tests formula dependency analysis use-case methods (Phase F-3):
- analyze_dependencies: Discovers field dependencies (analysis only)

Tests formula cycle detection use-case methods (Phase F-4):
- detect_cycles: Detects circular dependencies in formula fields

Tests formula governance use-case methods (Phase F-6):
- evaluate_governance: Evaluates governance status from existing diagnostics

Tests formula binding use-case methods (Phase F-7):
- can_bind_formula: Checks if binding is allowed
- bind_formula: Attempts to bind formula to target
- unbind_formula: Clears/unbinds formula from target

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

PHASE F-4 CONSTRAINTS (ADR-041):
- Analysis only (design-time cycle detection)
- No DAG execution or topological sorting
- No persistence of cycle results
- No blocking of saves/edits
- Same-entity scope only
- Deterministic output

PHASE F-6 CONSTRAINTS (Governance & Enforcement):
- Policy evaluation only (no new analysis)
- Deterministic: same input -> same output
- No execution
- No persistence
- No schema mutation
- Non-blocking (informational only)

PHASE F-7 CONSTRAINTS (Formula Binding & Persistence Rules):
- Policy & wiring only (no persistence)
- Pure deterministic binding evaluation
- No schema mutation
- No auto-execution
- No observers/listeners
"""

import pytest

from doc_helper.application.dto.formula_dto import (
    # Phase F-4
    FormulaCycleAnalysisResultDTO,
    FormulaCycleDTO,
    # Phase F-3
    FormulaDependencyAnalysisResultDTO,
    FormulaDependencyDTO,
    # Phase F-2
    FormulaExecutionResultDTO,
    # Phase F-6
    FormulaGovernanceResultDTO,
    FormulaGovernanceStatus,
    # Phase F-1
    FormulaResultType,
    FormulaValidationResultDTO,
    SchemaFieldInfoDTO,
    # Phase F-7: Formula Binding
    FormulaBindingDTO,
    FormulaBindingResultDTO,
    FormulaBindingStatus,
    FormulaBindingTarget,
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


# =============================================================================
# PHASE F-4: Formula Cycle Detection Tests
# =============================================================================


class TestFormulaCycleDetection:
    """Tests for FormulaUseCases.detect_cycles() (Phase F-4).

    PHASE F-4 CONSTRAINTS (ADR-041):
    - Analysis only (design-time cycle detection)
    - No DAG execution or topological sorting
    - No persistence of cycle results
    - No blocking of saves/edits
    - Same-entity scope only
    - Deterministic output
    """

    @pytest.fixture
    def usecases(self) -> FormulaUseCases:
        """Create FormulaUseCases instance."""
        return FormulaUseCases()

    # -------------------------------------------------------------------------
    # Empty Input
    # -------------------------------------------------------------------------

    def test_empty_dependencies_no_cycles(self, usecases: FormulaUseCases) -> None:
        """Empty formula dependencies should report no cycles."""
        result = usecases.detect_cycles(formula_dependencies={})

        assert result.has_cycles is False
        assert result.cycle_count == 0
        assert len(result.cycles) == 0
        assert result.analyzed_field_count == 0

    # -------------------------------------------------------------------------
    # No Cycles (Linear Chain)
    # -------------------------------------------------------------------------

    def test_single_field_no_dependencies_no_cycle(
        self, usecases: FormulaUseCases
    ) -> None:
        """Single formula field with no dependencies should have no cycles."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "total": (),  # No dependencies
            }
        )

        assert result.has_cycles is False
        assert result.cycle_count == 0
        assert result.analyzed_field_count == 1

    def test_linear_chain_no_cycle(self, usecases: FormulaUseCases) -> None:
        """Linear chain A → B → C should have no cycles."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_c": ("field_b",),  # C depends on B
                "field_b": ("field_a",),  # B depends on A
                "field_a": (),  # A has no dependencies
            }
        )

        assert result.has_cycles is False
        assert result.cycle_count == 0
        assert result.analyzed_field_count == 3

    def test_diamond_dependency_no_cycle(self, usecases: FormulaUseCases) -> None:
        """Diamond dependency (A→B, A→C, B→D, C→D) should have no cycles."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_d": ("field_b", "field_c"),  # D depends on B and C
                "field_b": ("field_a",),  # B depends on A
                "field_c": ("field_a",),  # C depends on A
                "field_a": (),  # A has no dependencies
            }
        )

        assert result.has_cycles is False
        assert result.cycle_count == 0
        assert result.analyzed_field_count == 4

    def test_multiple_independent_chains_no_cycle(
        self, usecases: FormulaUseCases
    ) -> None:
        """Multiple independent chains should have no cycles."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "chain1_b": ("chain1_a",),
                "chain1_a": (),
                "chain2_b": ("chain2_a",),
                "chain2_a": (),
            }
        )

        assert result.has_cycles is False
        assert result.cycle_count == 0
        assert result.analyzed_field_count == 4

    # -------------------------------------------------------------------------
    # Self-Reference Cycle (A → A)
    # -------------------------------------------------------------------------

    def test_self_reference_cycle(self, usecases: FormulaUseCases) -> None:
        """Self-referential formula (A → A) should be detected as a cycle."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_a": ("field_a",),  # A references itself
            }
        )

        assert result.has_cycles is True
        assert result.cycle_count == 1
        assert len(result.cycles) == 1

        cycle = result.cycles[0]
        assert cycle.field_ids == ("field_a",)
        assert cycle.is_self_reference is True
        assert cycle.cycle_length == 1
        assert cycle.severity == "ERROR"
        assert "field_a" in cycle.cycle_path

    # -------------------------------------------------------------------------
    # Simple 2-Node Cycle (A → B → A)
    # -------------------------------------------------------------------------

    def test_two_node_cycle(self, usecases: FormulaUseCases) -> None:
        """Two-node cycle (A → B → A) should be detected."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_a": ("field_b",),  # A depends on B
                "field_b": ("field_a",),  # B depends on A
            }
        )

        assert result.has_cycles is True
        assert result.cycle_count == 1
        assert len(result.cycles) == 1

        cycle = result.cycles[0]
        assert set(cycle.field_ids) == {"field_a", "field_b"}
        assert cycle.cycle_length == 2
        assert cycle.is_self_reference is False
        assert cycle.severity == "ERROR"
        # Cycle path should show the loop
        assert "→" in cycle.cycle_path

    # -------------------------------------------------------------------------
    # Multi-Node Cycle (A → B → C → A)
    # -------------------------------------------------------------------------

    def test_three_node_cycle(self, usecases: FormulaUseCases) -> None:
        """Three-node cycle (A → B → C → A) should be detected."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_a": ("field_c",),  # A depends on C
                "field_b": ("field_a",),  # B depends on A
                "field_c": ("field_b",),  # C depends on B
            }
        )

        assert result.has_cycles is True
        assert result.cycle_count == 1
        assert len(result.cycles) == 1

        cycle = result.cycles[0]
        assert set(cycle.field_ids) == {"field_a", "field_b", "field_c"}
        assert cycle.cycle_length == 3
        assert cycle.severity == "ERROR"

    def test_four_node_cycle(self, usecases: FormulaUseCases) -> None:
        """Four-node cycle (A → B → C → D → A) should be detected."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_a": ("field_d",),  # A depends on D
                "field_b": ("field_a",),  # B depends on A
                "field_c": ("field_b",),  # C depends on B
                "field_d": ("field_c",),  # D depends on C
            }
        )

        assert result.has_cycles is True
        assert result.cycle_count == 1

        cycle = result.cycles[0]
        assert set(cycle.field_ids) == {"field_a", "field_b", "field_c", "field_d"}
        assert cycle.cycle_length == 4

    # -------------------------------------------------------------------------
    # Multiple Independent Cycles
    # -------------------------------------------------------------------------

    def test_multiple_independent_cycles(self, usecases: FormulaUseCases) -> None:
        """Multiple independent cycles should all be detected."""
        result = usecases.detect_cycles(
            formula_dependencies={
                # Cycle 1: X → Y → X
                "field_x": ("field_y",),
                "field_y": ("field_x",),
                # Cycle 2: P → Q → P
                "field_p": ("field_q",),
                "field_q": ("field_p",),
            }
        )

        assert result.has_cycles is True
        assert result.cycle_count == 2
        assert len(result.cycles) == 2

        # Both cycles should be ERROR severity
        for cycle in result.cycles:
            assert cycle.severity == "ERROR"
            assert cycle.cycle_length == 2

        # Check that all_cycle_field_ids contains all fields from all cycles
        all_ids = set(result.all_cycle_field_ids)
        assert all_ids == {"field_x", "field_y", "field_p", "field_q"}

    def test_self_reference_and_two_node_cycle(self, usecases: FormulaUseCases) -> None:
        """Self-reference and 2-node cycle should both be detected."""
        result = usecases.detect_cycles(
            formula_dependencies={
                # Self-reference
                "field_self": ("field_self",),
                # 2-node cycle
                "field_a": ("field_b",),
                "field_b": ("field_a",),
            }
        )

        assert result.has_cycles is True
        assert result.cycle_count == 2
        assert len(result.cycles) == 2

        # One should be self-reference
        self_refs = [c for c in result.cycles if c.is_self_reference]
        assert len(self_refs) == 1
        assert self_refs[0].field_ids == ("field_self",)

    # -------------------------------------------------------------------------
    # Mixed: Cyclic and Non-Cyclic Fields
    # -------------------------------------------------------------------------

    def test_mixed_cyclic_and_acyclic_fields(self, usecases: FormulaUseCases) -> None:
        """Mix of cyclic and non-cyclic fields should only report cycles."""
        result = usecases.detect_cycles(
            formula_dependencies={
                # Non-cyclic chain
                "total": ("subtotal", "tax"),
                "subtotal": ("price", "quantity"),
                "tax": ("subtotal",),
                "price": (),
                "quantity": (),
                # Cyclic pair
                "cyclic_a": ("cyclic_b",),
                "cyclic_b": ("cyclic_a",),
            }
        )

        assert result.has_cycles is True
        assert result.cycle_count == 1
        assert result.analyzed_field_count == 7

        # Only the cyclic fields should be in cycles
        cycle = result.cycles[0]
        assert set(cycle.field_ids) == {"cyclic_a", "cyclic_b"}

        # Non-cyclic fields should not be in cycle_field_ids
        all_cycle_ids = set(result.all_cycle_field_ids)
        assert "total" not in all_cycle_ids
        assert "subtotal" not in all_cycle_ids
        assert "tax" not in all_cycle_ids

    def test_cycle_in_larger_graph(self, usecases: FormulaUseCases) -> None:
        """Cycle embedded in larger dependency graph should be found."""
        result = usecases.detect_cycles(
            formula_dependencies={
                # Entry point
                "result": ("calc1", "calc2"),
                # calc1 has no issues
                "calc1": ("input1",),
                "input1": (),
                # calc2 leads to a cycle
                "calc2": ("intermediate",),
                "intermediate": ("cyclic_start",),
                "cyclic_start": ("cyclic_end",),
                "cyclic_end": ("cyclic_start",),  # Cycle!
            }
        )

        assert result.has_cycles is True
        assert result.cycle_count == 1

        cycle = result.cycles[0]
        assert set(cycle.field_ids) == {"cyclic_start", "cyclic_end"}

    # -------------------------------------------------------------------------
    # Dependency on Non-Formula Fields
    # -------------------------------------------------------------------------

    def test_dependency_on_non_formula_field(self, usecases: FormulaUseCases) -> None:
        """Dependencies on fields not in the formula set should not cause issues."""
        result = usecases.detect_cycles(
            formula_dependencies={
                # Formula field depends on non-formula fields (not in dict keys)
                "calculated_total": ("raw_price", "raw_quantity"),
            }
        )

        # raw_price and raw_quantity are not formula fields (not in keys)
        # So no cycles possible
        assert result.has_cycles is False
        assert result.cycle_count == 0
        assert result.analyzed_field_count == 1

    # -------------------------------------------------------------------------
    # Determinism (Same inputs -> Same output)
    # -------------------------------------------------------------------------

    def test_cycle_detection_is_deterministic(self, usecases: FormulaUseCases) -> None:
        """Same inputs should produce same outputs."""
        dependencies = {
            "field_a": ("field_b",),
            "field_b": ("field_c",),
            "field_c": ("field_a",),
        }

        result1 = usecases.detect_cycles(dependencies)
        result2 = usecases.detect_cycles(dependencies)
        result3 = usecases.detect_cycles(dependencies)

        # All results should be identical
        assert result1.has_cycles == result2.has_cycles == result3.has_cycles
        assert result1.cycle_count == result2.cycle_count == result3.cycle_count
        assert result1.cycles == result2.cycles == result3.cycles
        assert (
            result1.all_cycle_field_ids
            == result2.all_cycle_field_ids
            == result3.all_cycle_field_ids
        )

    def test_cycle_path_is_deterministic(self, usecases: FormulaUseCases) -> None:
        """Cycle path should be deterministic regardless of input order."""
        # Same cycle described with different key ordering
        deps1 = {
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        }
        deps2 = {
            "field_b": ("field_a",),
            "field_a": ("field_b",),
        }

        result1 = usecases.detect_cycles(deps1)
        result2 = usecases.detect_cycles(deps2)

        # Both should find the same cycle with same path
        assert result1.has_cycles is True
        assert result2.has_cycles is True
        assert result1.cycles[0].cycle_path == result2.cycles[0].cycle_path
        assert result1.cycles[0].field_ids == result2.cycles[0].field_ids

    # -------------------------------------------------------------------------
    # DTO Immutability
    # -------------------------------------------------------------------------

    def test_result_dto_is_frozen(self, usecases: FormulaUseCases) -> None:
        """FormulaCycleAnalysisResultDTO should be frozen (immutable)."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_a": ("field_b",),
                "field_b": ("field_a",),
            }
        )

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            result.has_cycles = False  # type: ignore

        with pytest.raises(AttributeError):
            result.cycles = ()  # type: ignore

    def test_cycle_dto_is_frozen(self, usecases: FormulaUseCases) -> None:
        """FormulaCycleDTO should be frozen (immutable)."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_a": ("field_a",),
            }
        )

        cycle = result.cycles[0]

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            cycle.field_ids = ("other",)  # type: ignore

        with pytest.raises(AttributeError):
            cycle.severity = "WARNING"  # type: ignore

    # -------------------------------------------------------------------------
    # Cycle Error Messages
    # -------------------------------------------------------------------------

    def test_cycle_errors_property(self, usecases: FormulaUseCases) -> None:
        """cycle_errors should provide human-readable error messages."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_a": ("field_b",),
                "field_b": ("field_a",),
            }
        )

        assert len(result.cycle_errors) == 1
        error_msg = result.cycle_errors[0]
        assert "Circular dependency" in error_msg
        assert "→" in error_msg

    def test_multiple_cycle_errors(self, usecases: FormulaUseCases) -> None:
        """Multiple cycles should produce multiple error messages."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_a": ("field_a",),  # Self-reference
                "field_x": ("field_y",),
                "field_y": ("field_x",),  # 2-node cycle
            }
        )

        assert len(result.cycle_errors) == 2
        for error_msg in result.cycle_errors:
            assert "Circular dependency" in error_msg

    # -------------------------------------------------------------------------
    # No Side Effects (Pure Analysis)
    # -------------------------------------------------------------------------

    def test_input_not_mutated(self, usecases: FormulaUseCases) -> None:
        """Input dependencies dict should not be mutated."""
        dependencies = {
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        }
        original_deps = {k: v for k, v in dependencies.items()}

        usecases.detect_cycles(dependencies)

        # Input should be unchanged
        assert dependencies == original_deps

    # -------------------------------------------------------------------------
    # Edge Cases
    # -------------------------------------------------------------------------

    def test_field_depends_on_itself_and_others(
        self, usecases: FormulaUseCases
    ) -> None:
        """Field depending on itself and others should still detect self-cycle."""
        result = usecases.detect_cycles(
            formula_dependencies={
                "field_a": ("field_a", "field_b"),  # Self-ref + external dep
                "field_b": (),
            }
        )

        assert result.has_cycles is True
        # Should find self-reference
        self_refs = [c for c in result.cycles if c.is_self_reference]
        assert len(self_refs) == 1

    def test_complex_interconnected_cycles(self, usecases: FormulaUseCases) -> None:
        """Complex graph with multiple interconnected cycles."""
        result = usecases.detect_cycles(
            formula_dependencies={
                # Two overlapping cycles sharing a node
                # Cycle 1: A → B → C → A
                # Cycle 2: C → D → C
                "field_a": ("field_c",),
                "field_b": ("field_a",),
                "field_c": ("field_b", "field_d"),
                "field_d": ("field_c",),
            }
        )

        assert result.has_cycles is True
        # Should find cycles
        assert result.cycle_count >= 1


# =============================================================================
# PHASE F-6: Formula Governance Tests
# =============================================================================


class TestFormulaGovernance:
    """Tests for FormulaUseCases.evaluate_governance() (Phase F-6).

    PHASE F-6 CONSTRAINTS:
    - Policy evaluation only (no new analysis)
    - Deterministic: same input -> same output
    - No execution
    - No persistence
    - No schema mutation
    - Non-blocking (informational only)
    """

    @pytest.fixture
    def usecases(self) -> FormulaUseCases:
        """Create FormulaUseCases instance."""
        return FormulaUseCases()

    @pytest.fixture
    def schema_fields(self) -> tuple[SchemaFieldInfoDTO, ...]:
        """Create sample schema fields for governance tests."""
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
        )

    # -------------------------------------------------------------------------
    # EMPTY Status (No Formula Text)
    # -------------------------------------------------------------------------

    def test_empty_formula_returns_empty_status(
        self, usecases: FormulaUseCases
    ) -> None:
        """Empty formula text should return EMPTY governance status."""
        result = usecases.evaluate_governance(
            formula_text="",
            validation_result=None,
            cycle_result=None,
        )

        assert result.status == FormulaGovernanceStatus.EMPTY
        assert result.is_allowed is True
        assert result.is_blocked is False
        assert result.is_empty is True
        assert len(result.blocking_reasons) == 0
        assert len(result.warning_reasons) == 0

    def test_whitespace_formula_returns_empty_status(
        self, usecases: FormulaUseCases
    ) -> None:
        """Whitespace-only formula text should return EMPTY governance status."""
        result = usecases.evaluate_governance(
            formula_text="   \t\n  ",
            validation_result=None,
            cycle_result=None,
        )

        assert result.status == FormulaGovernanceStatus.EMPTY
        assert result.is_allowed is True
        assert result.is_blocked is False

    def test_none_formula_returns_empty_status(
        self, usecases: FormulaUseCases
    ) -> None:
        """None formula text should return EMPTY governance status."""
        result = usecases.evaluate_governance(
            formula_text=None,
            validation_result=None,
            cycle_result=None,
        )

        assert result.status == FormulaGovernanceStatus.EMPTY
        assert result.is_allowed is True

    # -------------------------------------------------------------------------
    # INVALID Status (Syntax Errors)
    # -------------------------------------------------------------------------

    def test_syntax_error_returns_invalid_status(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Syntax errors in validation should return INVALID governance status."""
        # Create a validation result with syntax errors
        validation_result = FormulaValidationResultDTO(
            is_valid=False,
            errors=("Syntax error: unexpected token",),
            warnings=(),
            inferred_type="UNKNOWN",
            field_references=(),
        )

        result = usecases.evaluate_governance(
            formula_text="price +",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert result.status == FormulaGovernanceStatus.INVALID
        assert result.is_allowed is False
        assert result.is_blocked is True
        assert len(result.blocking_reasons) == 1
        assert "Syntax error" in result.blocking_reasons[0]

    def test_multiple_syntax_errors_all_captured(
        self, usecases: FormulaUseCases
    ) -> None:
        """Multiple syntax errors should all be captured as blocking reasons."""
        validation_result = FormulaValidationResultDTO(
            is_valid=False,
            errors=(
                "Syntax error: unexpected token",
                "Syntax error: missing operand",
            ),
            warnings=(),
            inferred_type="UNKNOWN",
            field_references=(),
        )

        result = usecases.evaluate_governance(
            formula_text="price + * quantity",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert result.status == FormulaGovernanceStatus.INVALID
        assert result.blocking_count == 2

    # -------------------------------------------------------------------------
    # INVALID Status (Unknown Fields)
    # -------------------------------------------------------------------------

    def test_unknown_field_returns_invalid_status(
        self, usecases: FormulaUseCases
    ) -> None:
        """Unknown field references should return INVALID governance status."""
        validation_result = FormulaValidationResultDTO(
            is_valid=False,
            errors=("Unknown field: 'unknown_field'",),
            warnings=(),
            inferred_type="UNKNOWN",
            field_references=("unknown_field",),
        )

        result = usecases.evaluate_governance(
            formula_text="unknown_field + 1",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert result.status == FormulaGovernanceStatus.INVALID
        assert result.is_blocked is True
        assert len(result.blocking_reasons) == 1
        assert "unknown_field" in result.blocking_reasons[0].lower()

    # -------------------------------------------------------------------------
    # INVALID Status (Cycles)
    # -------------------------------------------------------------------------

    def test_cycles_return_invalid_status(
        self, usecases: FormulaUseCases
    ) -> None:
        """Cycles in formula dependencies should return INVALID governance status."""
        # Valid formula but with cycles detected
        validation_result = FormulaValidationResultDTO(
            is_valid=True,
            errors=(),
            warnings=(),
            inferred_type="NUMBER",
            field_references=("field_a", "field_b"),
        )

        # Phase H-3: Provide all pre-computed fields
        cycle_result = FormulaCycleAnalysisResultDTO(
            has_cycles=True,
            cycles=(
                FormulaCycleDTO(
                    field_ids=("field_a", "field_b"),
                    cycle_path="field_a → field_b → field_a",
                    severity="ERROR",
                ),
            ),
            analyzed_field_count=2,
            _cycle_count=1,
            _all_cycle_field_ids=("field_a", "field_b"),
            _cycle_errors=("Circular dependency: field_a → field_b → field_a",),
        )

        result = usecases.evaluate_governance(
            formula_text="field_a + field_b",
            validation_result=validation_result,
            cycle_result=cycle_result,
        )

        assert result.status == FormulaGovernanceStatus.INVALID
        assert result.is_blocked is True
        assert len(result.blocking_reasons) == 1
        assert "Circular dependency" in result.blocking_reasons[0]
        assert "field_a → field_b → field_a" in result.blocking_reasons[0]

    def test_multiple_cycles_all_captured(
        self, usecases: FormulaUseCases
    ) -> None:
        """Multiple cycles should all be captured as blocking reasons."""
        validation_result = FormulaValidationResultDTO(
            is_valid=True,
            errors=(),
            warnings=(),
            inferred_type="NUMBER",
            field_references=(),
        )

        # Phase H-3: Provide all pre-computed fields
        cycle_result = FormulaCycleAnalysisResultDTO(
            has_cycles=True,
            cycles=(
                FormulaCycleDTO(
                    field_ids=("a",),
                    cycle_path="a → a",
                    severity="ERROR",
                ),
                FormulaCycleDTO(
                    field_ids=("x", "y"),
                    cycle_path="x → y → x",
                    severity="ERROR",
                ),
            ),
            analyzed_field_count=3,
            _cycle_count=2,
            _all_cycle_field_ids=("a", "x", "y"),
            _cycle_errors=(
                "Circular dependency: a → a",
                "Circular dependency: x → y → x",
            ),
        )

        result = usecases.evaluate_governance(
            formula_text="a + x",
            validation_result=validation_result,
            cycle_result=cycle_result,
        )

        assert result.status == FormulaGovernanceStatus.INVALID
        assert result.blocking_count == 2

    # -------------------------------------------------------------------------
    # INVALID Status (Combined: Syntax + Cycles)
    # -------------------------------------------------------------------------

    def test_combined_errors_all_captured(
        self, usecases: FormulaUseCases
    ) -> None:
        """Syntax errors and cycles should all be captured as blocking reasons."""
        validation_result = FormulaValidationResultDTO(
            is_valid=False,
            errors=("Unknown field: 'missing'",),
            warnings=(),
            inferred_type="UNKNOWN",
            field_references=(),
        )

        # Phase H-3: Provide all pre-computed fields
        cycle_result = FormulaCycleAnalysisResultDTO(
            has_cycles=True,
            cycles=(
                FormulaCycleDTO(
                    field_ids=("a", "b"),
                    cycle_path="a → b → a",
                    severity="ERROR",
                ),
            ),
            analyzed_field_count=2,
            _cycle_count=1,
            _all_cycle_field_ids=("a", "b"),
            _cycle_errors=("Circular dependency: a → b → a",),
        )

        result = usecases.evaluate_governance(
            formula_text="missing + a",
            validation_result=validation_result,
            cycle_result=cycle_result,
        )

        assert result.status == FormulaGovernanceStatus.INVALID
        assert result.blocking_count == 2

    # -------------------------------------------------------------------------
    # VALID_WITH_WARNINGS Status (Type Warnings)
    # -------------------------------------------------------------------------

    def test_type_warnings_return_valid_with_warnings(
        self, usecases: FormulaUseCases
    ) -> None:
        """Type warnings should return VALID_WITH_WARNINGS governance status."""
        validation_result = FormulaValidationResultDTO(
            is_valid=True,
            errors=(),
            warnings=("Arithmetic operation '*' on TEXT type may fail",),
            inferred_type="NUMBER",
            field_references=("price",),
        )

        result = usecases.evaluate_governance(
            formula_text="price * 2",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert result.status == FormulaGovernanceStatus.VALID_WITH_WARNINGS
        assert result.is_allowed is True
        assert result.is_blocked is False
        assert result.has_warnings is True
        assert len(result.warning_reasons) == 1

    def test_unknown_inferred_type_returns_valid_with_warnings(
        self, usecases: FormulaUseCases
    ) -> None:
        """UNKNOWN inferred type should return VALID_WITH_WARNINGS governance status."""
        validation_result = FormulaValidationResultDTO(
            is_valid=True,
            errors=(),
            warnings=(),
            inferred_type="UNKNOWN",
            field_references=("price",),
        )

        result = usecases.evaluate_governance(
            formula_text="if_else(price > 0, price, null)",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert result.status == FormulaGovernanceStatus.VALID_WITH_WARNINGS
        assert result.is_allowed is True
        assert result.has_warnings is True
        assert any(
            "type cannot be determined" in w.lower() for w in result.warning_reasons
        )

    # -------------------------------------------------------------------------
    # VALID Status (No Issues)
    # -------------------------------------------------------------------------

    def test_valid_formula_returns_valid_status(
        self, usecases: FormulaUseCases
    ) -> None:
        """Valid formula with no issues should return VALID governance status."""
        validation_result = FormulaValidationResultDTO(
            is_valid=True,
            errors=(),
            warnings=(),
            inferred_type="NUMBER",
            field_references=("price", "quantity"),
        )

        # Phase H-3: Provide all pre-computed fields
        cycle_result = FormulaCycleAnalysisResultDTO(
            has_cycles=False,
            cycles=(),
            analyzed_field_count=2,
            _cycle_count=0,
            _all_cycle_field_ids=(),
            _cycle_errors=(),
        )

        result = usecases.evaluate_governance(
            formula_text="price * quantity",
            validation_result=validation_result,
            cycle_result=cycle_result,
        )

        assert result.status == FormulaGovernanceStatus.VALID
        assert result.is_allowed is True
        assert result.is_blocked is False
        assert result.is_valid is True
        assert len(result.blocking_reasons) == 0
        assert len(result.warning_reasons) == 0

    def test_valid_formula_without_cycle_result(
        self, usecases: FormulaUseCases
    ) -> None:
        """Valid formula without cycle analysis should return VALID if no errors."""
        validation_result = FormulaValidationResultDTO(
            is_valid=True,
            errors=(),
            warnings=(),
            inferred_type="NUMBER",
            field_references=("price",),
        )

        result = usecases.evaluate_governance(
            formula_text="price * 2",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert result.status == FormulaGovernanceStatus.VALID
        assert result.is_allowed is True

    # -------------------------------------------------------------------------
    # Summary Message
    # -------------------------------------------------------------------------

    def test_empty_summary_message(
        self, usecases: FormulaUseCases
    ) -> None:
        """EMPTY status should return empty summary message."""
        result = usecases.evaluate_governance(
            formula_text="",
            validation_result=None,
            cycle_result=None,
        )

        assert result.summary_message == ""

    def test_invalid_summary_message(
        self, usecases: FormulaUseCases
    ) -> None:
        """INVALID status should return blocking issue count in summary."""
        validation_result = FormulaValidationResultDTO(
            is_valid=False,
            errors=("Error 1", "Error 2"),
            warnings=(),
            inferred_type="UNKNOWN",
            field_references=(),
        )

        result = usecases.evaluate_governance(
            formula_text="bad formula",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert "blocked" in result.summary_message.lower()
        assert "2" in result.summary_message

    def test_valid_with_warnings_summary_message(
        self, usecases: FormulaUseCases
    ) -> None:
        """VALID_WITH_WARNINGS status should return warning count in summary."""
        validation_result = FormulaValidationResultDTO(
            is_valid=True,
            errors=(),
            warnings=("Warning 1",),
            inferred_type="NUMBER",
            field_references=(),
        )

        result = usecases.evaluate_governance(
            formula_text="price * 2",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert "warning" in result.summary_message.lower()
        assert "1" in result.summary_message

    def test_valid_summary_message(
        self, usecases: FormulaUseCases
    ) -> None:
        """VALID status should return 'valid' in summary."""
        validation_result = FormulaValidationResultDTO(
            is_valid=True,
            errors=(),
            warnings=(),
            inferred_type="NUMBER",
            field_references=(),
        )

        result = usecases.evaluate_governance(
            formula_text="price * 2",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert "valid" in result.summary_message.lower()

    # -------------------------------------------------------------------------
    # Determinism (Same inputs -> Same output)
    # -------------------------------------------------------------------------

    def test_governance_is_deterministic(
        self, usecases: FormulaUseCases
    ) -> None:
        """Same inputs should produce same governance outputs."""
        validation_result = FormulaValidationResultDTO(
            is_valid=True,
            errors=(),
            warnings=("Type warning",),
            inferred_type="NUMBER",
            field_references=("price",),
        )

        result1 = usecases.evaluate_governance(
            formula_text="price * 2",
            validation_result=validation_result,
            cycle_result=None,
        )
        result2 = usecases.evaluate_governance(
            formula_text="price * 2",
            validation_result=validation_result,
            cycle_result=None,
        )
        result3 = usecases.evaluate_governance(
            formula_text="price * 2",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert result1.status == result2.status == result3.status
        assert result1.blocking_reasons == result2.blocking_reasons == result3.blocking_reasons
        assert result1.warning_reasons == result2.warning_reasons == result3.warning_reasons

    # -------------------------------------------------------------------------
    # DTO Immutability
    # -------------------------------------------------------------------------

    def test_governance_result_is_frozen(
        self, usecases: FormulaUseCases
    ) -> None:
        """FormulaGovernanceResultDTO should be frozen (immutable)."""
        result = usecases.evaluate_governance(
            formula_text="price * 2",
            validation_result=FormulaValidationResultDTO(
                is_valid=True,
                errors=(),
                warnings=(),
                inferred_type="NUMBER",
                field_references=(),
            ),
            cycle_result=None,
        )

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            result.status = FormulaGovernanceStatus.INVALID  # type: ignore

        with pytest.raises(AttributeError):
            result.blocking_reasons = ("new reason",)  # type: ignore

    # -------------------------------------------------------------------------
    # Integration: Full Validation + Governance Flow
    # -------------------------------------------------------------------------

    def test_full_flow_valid_formula(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Full flow: validate formula, then evaluate governance."""
        # Step 1: Validate
        validation_result = usecases.validate_formula(
            formula_text="price * quantity",
            schema_fields=schema_fields,
        )

        # Step 2: Evaluate governance
        governance_result = usecases.evaluate_governance(
            formula_text="price * quantity",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert governance_result.status == FormulaGovernanceStatus.VALID
        assert governance_result.is_allowed is True

    def test_full_flow_invalid_formula(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Full flow: validate invalid formula, then evaluate governance."""
        # Step 1: Validate (unknown field)
        validation_result = usecases.validate_formula(
            formula_text="unknown_field * 2",
            schema_fields=schema_fields,
        )

        # Step 2: Evaluate governance
        governance_result = usecases.evaluate_governance(
            formula_text="unknown_field * 2",
            validation_result=validation_result,
            cycle_result=None,
        )

        assert governance_result.status == FormulaGovernanceStatus.INVALID
        assert governance_result.is_blocked is True

    def test_full_flow_with_cycles(
        self, usecases: FormulaUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Full flow: validate formula, detect cycles, then evaluate governance."""
        # Step 1: Validate
        validation_result = usecases.validate_formula(
            formula_text="price * quantity",
            schema_fields=schema_fields,
        )

        # Step 2: Detect cycles (simulate cyclic dependencies)
        cycle_result = usecases.detect_cycles(
            formula_dependencies={
                "price": ("quantity",),
                "quantity": ("price",),
            }
        )

        # Step 3: Evaluate governance
        governance_result = usecases.evaluate_governance(
            formula_text="price * quantity",
            validation_result=validation_result,
            cycle_result=cycle_result,
        )

        assert governance_result.status == FormulaGovernanceStatus.INVALID
        assert governance_result.is_blocked is True
        assert any("Circular dependency" in r for r in governance_result.blocking_reasons)


# =============================================================================
# PHASE F-7: Formula Binding Tests
# =============================================================================


class TestFormulaBinding:
    """Tests for FormulaUseCases binding methods (Phase F-7).

    PHASE F-7 CONSTRAINTS:
    - Policy & wiring only (no persistence)
    - Pure deterministic binding evaluation
    - No schema mutation
    - No auto-execution
    - No observers/listeners
    """

    @pytest.fixture
    def usecases(self) -> FormulaUseCases:
        """Create FormulaUseCases instance."""
        return FormulaUseCases()

    @pytest.fixture
    def valid_governance(self) -> FormulaGovernanceResultDTO:
        """Create a valid governance result."""
        return FormulaGovernanceResultDTO(
            status=FormulaGovernanceStatus.VALID,
            blocking_reasons=(),
            warning_reasons=(),
        )

    @pytest.fixture
    def valid_with_warnings_governance(self) -> FormulaGovernanceResultDTO:
        """Create a valid-with-warnings governance result."""
        return FormulaGovernanceResultDTO(
            status=FormulaGovernanceStatus.VALID_WITH_WARNINGS,
            blocking_reasons=(),
            warning_reasons=("Type warning: result type cannot be determined",),
        )

    @pytest.fixture
    def invalid_governance(self) -> FormulaGovernanceResultDTO:
        """Create an invalid governance result."""
        return FormulaGovernanceResultDTO(
            status=FormulaGovernanceStatus.INVALID,
            blocking_reasons=("Unknown field: 'missing_field'",),
            warning_reasons=(),
        )

    @pytest.fixture
    def empty_governance(self) -> FormulaGovernanceResultDTO:
        """Create an empty governance result."""
        return FormulaGovernanceResultDTO(
            status=FormulaGovernanceStatus.EMPTY,
            blocking_reasons=(),
            warning_reasons=(),
        )

    # -------------------------------------------------------------------------
    # can_bind_formula: Target Type Support
    # -------------------------------------------------------------------------

    def test_can_bind_calculated_field_allowed(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """CALCULATED_FIELD target should be allowed with valid governance."""
        result = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            governance_result=valid_governance,
        )

        assert result.status == FormulaBindingStatus.ALLOWED
        assert result.is_allowed is True
        assert result.is_blocked is False
        assert result.block_reason is None

    def test_can_bind_validation_rule_blocked(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """VALIDATION_RULE target should be blocked in Phase F-7."""
        result = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.VALIDATION_RULE,
            governance_result=valid_governance,
        )

        assert result.status == FormulaBindingStatus.BLOCKED_UNSUPPORTED_TARGET
        assert result.is_allowed is False
        assert result.is_blocked is True
        assert result.block_reason is not None
        assert "not supported" in result.block_reason.lower()

    def test_can_bind_output_mapping_blocked(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """OUTPUT_MAPPING target should be blocked in Phase F-7."""
        result = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.OUTPUT_MAPPING,
            governance_result=valid_governance,
        )

        assert result.status == FormulaBindingStatus.BLOCKED_UNSUPPORTED_TARGET
        assert result.is_allowed is False
        assert result.is_blocked is True

    # -------------------------------------------------------------------------
    # can_bind_formula: Governance Enforcement
    # -------------------------------------------------------------------------

    def test_can_bind_empty_governance_returns_cleared(
        self,
        usecases: FormulaUseCases,
        empty_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """Empty governance status should return CLEARED binding status."""
        result = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            governance_result=empty_governance,
        )

        assert result.status == FormulaBindingStatus.CLEARED
        assert result.is_allowed is True
        assert result.is_cleared is True
        assert result.block_reason is None

    def test_can_bind_valid_governance_allowed(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """VALID governance status should allow binding."""
        result = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            governance_result=valid_governance,
        )

        assert result.status == FormulaBindingStatus.ALLOWED
        assert result.is_allowed is True

    def test_can_bind_valid_with_warnings_allowed(
        self,
        usecases: FormulaUseCases,
        valid_with_warnings_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """VALID_WITH_WARNINGS governance status should allow binding."""
        result = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            governance_result=valid_with_warnings_governance,
        )

        assert result.status == FormulaBindingStatus.ALLOWED
        assert result.is_allowed is True

    def test_can_bind_invalid_governance_blocked(
        self,
        usecases: FormulaUseCases,
        invalid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """INVALID governance status should block binding."""
        result = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            governance_result=invalid_governance,
        )

        assert result.status == FormulaBindingStatus.BLOCKED_INVALID_FORMULA
        assert result.is_allowed is False
        assert result.is_blocked is True
        assert result.block_reason is not None
        assert "missing_field" in result.block_reason.lower()

    # -------------------------------------------------------------------------
    # bind_formula: Success Cases
    # -------------------------------------------------------------------------

    def test_bind_formula_valid_creates_binding(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """Valid bind_formula should create FormulaBindingDTO."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total_cost",
            formula_text="price * quantity",
            governance_result=valid_governance,
        )

        assert result.status == FormulaBindingStatus.ALLOWED
        assert result.is_allowed is True
        assert result.binding is not None

        binding = result.binding
        assert binding.target_type == FormulaBindingTarget.CALCULATED_FIELD
        assert binding.target_id == "total_cost"
        assert binding.formula_text == "price * quantity"
        assert binding.governance_status == FormulaGovernanceStatus.VALID

    def test_bind_formula_valid_with_warnings_creates_binding(
        self,
        usecases: FormulaUseCases,
        valid_with_warnings_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """VALID_WITH_WARNINGS governance should create binding."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="result",
            formula_text="if_else(a, b, c)",
            governance_result=valid_with_warnings_governance,
        )

        assert result.status == FormulaBindingStatus.ALLOWED
        assert result.binding is not None
        assert result.binding.governance_status == FormulaGovernanceStatus.VALID_WITH_WARNINGS

    # -------------------------------------------------------------------------
    # bind_formula: Blocked Cases
    # -------------------------------------------------------------------------

    def test_bind_formula_invalid_governance_no_binding(
        self,
        usecases: FormulaUseCases,
        invalid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """Invalid governance should not create binding."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="missing_field + 1",
            governance_result=invalid_governance,
        )

        assert result.status == FormulaBindingStatus.BLOCKED_INVALID_FORMULA
        assert result.binding is None
        assert result.block_reason is not None

    def test_bind_formula_unsupported_target_no_binding(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """Unsupported target should not create binding."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.VALIDATION_RULE,
            target_id="rule_1",
            formula_text="price > 0",
            governance_result=valid_governance,
        )

        assert result.status == FormulaBindingStatus.BLOCKED_UNSUPPORTED_TARGET
        assert result.binding is None
        assert result.block_reason is not None

    # -------------------------------------------------------------------------
    # bind_formula: CLEARED Status (Empty Formula)
    # -------------------------------------------------------------------------

    def test_bind_formula_empty_governance_returns_cleared(
        self,
        usecases: FormulaUseCases,
        empty_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """Empty governance should return CLEARED with no binding."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="",
            governance_result=empty_governance,
        )

        assert result.status == FormulaBindingStatus.CLEARED
        assert result.is_cleared is True
        assert result.binding is None
        assert result.block_reason is None

    # -------------------------------------------------------------------------
    # unbind_formula
    # -------------------------------------------------------------------------

    def test_unbind_formula_returns_cleared(
        self,
        usecases: FormulaUseCases,
    ) -> None:
        """unbind_formula should always return CLEARED status."""
        result = usecases.unbind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
        )

        assert result.status == FormulaBindingStatus.CLEARED
        assert result.is_cleared is True
        assert result.binding is None
        assert result.block_reason is None

    def test_unbind_formula_any_target(
        self,
        usecases: FormulaUseCases,
    ) -> None:
        """unbind_formula should work for any target type."""
        for target in FormulaBindingTarget:
            result = usecases.unbind_formula(
                target_type=target,
                target_id="any_id",
            )

            assert result.status == FormulaBindingStatus.CLEARED
            assert result.is_cleared is True

    # -------------------------------------------------------------------------
    # FormulaBindingDTO Properties
    # -------------------------------------------------------------------------

    def test_binding_dto_is_bound_true(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """FormulaBindingDTO.is_bound should be True for non-empty formula."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="price * quantity",
            governance_result=valid_governance,
        )

        assert result.binding is not None
        assert result.binding.is_bound is True
        assert result.binding.is_empty is False

    def test_binding_dto_is_valid_binding_true(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """FormulaBindingDTO.is_valid_binding should be True for VALID governance."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="price * quantity",
            governance_result=valid_governance,
        )

        assert result.binding is not None
        assert result.binding.is_valid_binding is True

    # -------------------------------------------------------------------------
    # FormulaBindingResultDTO Properties
    # -------------------------------------------------------------------------

    def test_binding_result_dto_status_message(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """FormulaBindingResultDTO.status_message should be human-readable."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="price * quantity",
            governance_result=valid_governance,
        )

        assert result.status_message != ""
        assert "allowed" in result.status_message.lower() or "ready" in result.status_message.lower()

    def test_binding_result_blocked_status_message(
        self,
        usecases: FormulaUseCases,
        invalid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """Blocked binding should have informative status message."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="invalid",
            governance_result=invalid_governance,
        )

        assert result.status_message != ""
        assert "blocked" in result.status_message.lower() or "error" in result.status_message.lower()

    # -------------------------------------------------------------------------
    # Determinism (Same inputs -> Same output)
    # -------------------------------------------------------------------------

    def test_can_bind_is_deterministic(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """can_bind_formula should be deterministic."""
        result1 = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            governance_result=valid_governance,
        )
        result2 = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            governance_result=valid_governance,
        )
        result3 = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            governance_result=valid_governance,
        )

        assert result1.status == result2.status == result3.status
        assert result1.is_allowed == result2.is_allowed == result3.is_allowed

    def test_bind_formula_is_deterministic(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """bind_formula should be deterministic."""
        result1 = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="price * quantity",
            governance_result=valid_governance,
        )
        result2 = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="price * quantity",
            governance_result=valid_governance,
        )

        assert result1.status == result2.status
        assert result1.binding == result2.binding

    # -------------------------------------------------------------------------
    # DTO Immutability
    # -------------------------------------------------------------------------

    def test_binding_result_dto_is_frozen(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """FormulaBindingResultDTO should be frozen (immutable)."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="price * quantity",
            governance_result=valid_governance,
        )

        with pytest.raises(AttributeError):
            result.status = FormulaBindingStatus.BLOCKED_INVALID_FORMULA  # type: ignore

        with pytest.raises(AttributeError):
            result.binding = None  # type: ignore

    def test_binding_dto_is_frozen(
        self,
        usecases: FormulaUseCases,
        valid_governance: FormulaGovernanceResultDTO,
    ) -> None:
        """FormulaBindingDTO should be frozen (immutable)."""
        result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="price * quantity",
            governance_result=valid_governance,
        )

        assert result.binding is not None
        with pytest.raises(AttributeError):
            result.binding.target_id = "other"  # type: ignore

        with pytest.raises(AttributeError):
            result.binding.formula_text = "different"  # type: ignore

    # -------------------------------------------------------------------------
    # Integration: Full Binding Flow
    # -------------------------------------------------------------------------

    def test_full_flow_valid_formula_binding(
        self,
        usecases: FormulaUseCases,
    ) -> None:
        """Full flow: validate, governance, then bind formula."""
        schema_fields = (
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
        )

        # Step 1: Validate formula
        validation_result = usecases.validate_formula(
            formula_text="price * quantity",
            schema_fields=schema_fields,
        )
        assert validation_result.is_valid is True

        # Step 2: Evaluate governance
        governance_result = usecases.evaluate_governance(
            formula_text="price * quantity",
            validation_result=validation_result,
            cycle_result=None,
        )
        assert governance_result.status == FormulaGovernanceStatus.VALID

        # Step 3: Check if can bind
        can_bind_result = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            governance_result=governance_result,
        )
        assert can_bind_result.is_allowed is True

        # Step 4: Bind formula
        bind_result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total_cost",
            formula_text="price * quantity",
            governance_result=governance_result,
        )
        assert bind_result.is_allowed is True
        assert bind_result.binding is not None
        assert bind_result.binding.target_id == "total_cost"
        assert bind_result.binding.formula_text == "price * quantity"

    def test_full_flow_invalid_formula_binding_blocked(
        self,
        usecases: FormulaUseCases,
    ) -> None:
        """Full flow: invalid formula should block binding."""
        schema_fields = (
            SchemaFieldInfoDTO(
                field_id="price",
                field_type="NUMBER",
                entity_id="product",
                label="Price",
            ),
        )

        # Step 1: Validate formula (unknown field)
        validation_result = usecases.validate_formula(
            formula_text="unknown_field * 2",
            schema_fields=schema_fields,
        )
        assert validation_result.is_valid is False

        # Step 2: Evaluate governance
        governance_result = usecases.evaluate_governance(
            formula_text="unknown_field * 2",
            validation_result=validation_result,
            cycle_result=None,
        )
        assert governance_result.status == FormulaGovernanceStatus.INVALID

        # Step 3: Check if can bind
        can_bind_result = usecases.can_bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            governance_result=governance_result,
        )
        assert can_bind_result.is_allowed is False
        assert can_bind_result.is_blocked is True

        # Step 4: Attempt to bind (should fail)
        bind_result = usecases.bind_formula(
            target_type=FormulaBindingTarget.CALCULATED_FIELD,
            target_id="total",
            formula_text="unknown_field * 2",
            governance_result=governance_result,
        )
        assert bind_result.is_allowed is False
        assert bind_result.binding is None
        assert bind_result.block_reason is not None

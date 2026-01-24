"""Unit tests for FormulaUseCases (Phase F-1).

Tests formula validation use-case methods:
- validate_formula: Validates syntax, field references, functions
- parse_formula: Parses formula into AST
- infer_result_type: Infers result type from formula

PHASE F-1 CONSTRAINTS:
- Read-only validation (no execution)
- No schema mutation
- No formula persistence
"""

import pytest

from doc_helper.application.dto.formula_dto import (
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
                label="Base Value",
            ),
            SchemaFieldInfoDTO(
                field_id="multiplier",
                field_type="NUMBER",
                label="Multiplier",
            ),
            SchemaFieldInfoDTO(
                field_id="name",
                field_type="TEXT",
                label="Name",
            ),
            SchemaFieldInfoDTO(
                field_id="is_active",
                field_type="CHECKBOX",
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

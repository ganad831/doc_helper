"""Unit tests for FormulaEditorViewModel (Phase F-1).

Tests formula editor ViewModel behavior:
- Formula editor shows error on invalid input
- Formula editor updates result type live
- Formula editor does NOT modify schema

PHASE F-1 CONSTRAINTS:
- Read-only validation (no execution)
- No schema mutation
- No formula persistence
"""

import pytest

from doc_helper.application.dto.formula_dto import SchemaFieldInfoDTO
from doc_helper.application.usecases.formula_usecases import FormulaUseCases
from doc_helper.presentation.viewmodels.formula_editor_viewmodel import (
    FormulaEditorViewModel,
)


class TestFormulaEditorViewModel:
    """Tests for FormulaEditorViewModel."""

    @pytest.fixture
    def formula_usecases(self) -> FormulaUseCases:
        """Create FormulaUseCases instance."""
        return FormulaUseCases()

    @pytest.fixture
    def viewmodel(self, formula_usecases: FormulaUseCases) -> FormulaEditorViewModel:
        """Create FormulaEditorViewModel instance."""
        return FormulaEditorViewModel(formula_usecases)

    @pytest.fixture
    def schema_fields(self) -> tuple[SchemaFieldInfoDTO, ...]:
        """Create sample schema fields."""
        return (
            SchemaFieldInfoDTO(
                field_id="value1",
                field_type="NUMBER",
                label="Value 1",
            ),
            SchemaFieldInfoDTO(
                field_id="value2",
                field_type="NUMBER",
                label="Value 2",
            ),
            SchemaFieldInfoDTO(
                field_id="name",
                field_type="TEXT",
                label="Name",
            ),
        )

    # -------------------------------------------------------------------------
    # Test: Formula editor shows error on invalid input
    # -------------------------------------------------------------------------

    def test_invalid_formula_shows_error(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Invalid formula syntax should show errors."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 +")  # Incomplete operator

        assert viewmodel.is_valid is False
        assert len(viewmodel.errors) > 0

    def test_unknown_field_shows_error(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Unknown field reference should show error."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field + value1")

        assert viewmodel.is_valid is False
        assert len(viewmodel.errors) > 0
        error_text = " ".join(viewmodel.errors).lower()
        assert "unknown_field" in error_text

    def test_unknown_function_shows_error(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Unknown function should show error."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("bad_func(value1)")

        assert viewmodel.is_valid is False
        assert len(viewmodel.errors) > 0
        error_text = " ".join(viewmodel.errors).lower()
        assert "bad_func" in error_text

    def test_valid_formula_no_errors(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Valid formula should have no errors."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        assert viewmodel.is_valid is True
        assert len(viewmodel.errors) == 0

    # -------------------------------------------------------------------------
    # Test: Formula editor updates result type live
    # -------------------------------------------------------------------------

    def test_type_updates_on_formula_change(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Inferred type should update when formula changes."""
        viewmodel.set_schema_context(schema_fields)

        # Set numeric formula
        viewmodel.set_formula("value1 + value2")
        assert viewmodel.inferred_type == "NUMBER"

        # Change to comparison (boolean)
        viewmodel.set_formula("value1 > value2")
        assert viewmodel.inferred_type == "BOOLEAN"

        # Change to text function
        viewmodel.set_formula("upper(name)")
        assert viewmodel.inferred_type == "TEXT"

    def test_numeric_arithmetic_infers_number(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Numeric arithmetic should infer NUMBER type."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 * value2 + 100")

        assert viewmodel.inferred_type == "NUMBER"

    def test_comparison_infers_boolean(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Comparison should infer BOOLEAN type."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 >= value2")

        assert viewmodel.inferred_type == "BOOLEAN"

    def test_text_function_infers_text(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Text function should infer TEXT type."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("lower(name)")

        assert viewmodel.inferred_type == "TEXT"

    def test_empty_formula_type_unknown(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Empty formula should have UNKNOWN type."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("")

        assert viewmodel.inferred_type == "UNKNOWN"

    # -------------------------------------------------------------------------
    # Test: Formula editor does NOT modify schema
    # -------------------------------------------------------------------------

    def test_schema_not_modified_by_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Setting formula should not modify schema fields."""
        viewmodel.set_schema_context(schema_fields)

        # Original schema
        original_fields = viewmodel.available_fields

        # Set formula (should not change schema)
        viewmodel.set_formula("value1 + value2")

        # Schema should be unchanged
        assert viewmodel.available_fields == original_fields

    def test_clear_formula_preserves_schema(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Clearing formula should preserve schema context."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        # Clear formula
        viewmodel.clear_formula()

        # Schema should still be available
        assert len(viewmodel.available_fields) > 0
        assert viewmodel.inferred_type == "UNKNOWN"

    def test_invalid_formula_does_not_affect_schema(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Invalid formula should not affect schema state."""
        viewmodel.set_schema_context(schema_fields)
        original_fields = viewmodel.available_fields

        # Set invalid formula
        viewmodel.set_formula("definitely_invalid +++ syntax")

        # Schema unchanged
        assert viewmodel.available_fields == original_fields

    # -------------------------------------------------------------------------
    # Test: Field references tracking
    # -------------------------------------------------------------------------

    def test_field_references_tracked(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Formula field references should be tracked."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2 * 100")

        refs = viewmodel.field_references
        assert "value1" in refs
        assert "value2" in refs
        assert len(refs) == 2

    def test_field_references_cleared_on_empty_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Empty formula should have no field references."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        # Clear
        viewmodel.clear_formula()

        assert len(viewmodel.field_references) == 0

    # -------------------------------------------------------------------------
    # Test: Observable property notifications
    # -------------------------------------------------------------------------

    def test_validation_result_notifies_subscribers(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Setting formula should notify validation_result subscribers."""
        viewmodel.set_schema_context(schema_fields)

        notifications = []
        viewmodel.subscribe("validation_result", lambda: notifications.append("notified"))

        viewmodel.set_formula("value1 + value2")

        assert len(notifications) > 0

    def test_has_formula_property(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """has_formula should reflect formula state."""
        viewmodel.set_schema_context(schema_fields)

        assert viewmodel.has_formula is False

        viewmodel.set_formula("value1")
        assert viewmodel.has_formula is True

        viewmodel.clear_formula()
        assert viewmodel.has_formula is False

    # -------------------------------------------------------------------------
    # Test: Available functions
    # -------------------------------------------------------------------------

    def test_available_functions_exposed(
        self,
        viewmodel: FormulaEditorViewModel,
    ) -> None:
        """ViewModel should expose list of available functions."""
        functions = viewmodel.available_functions

        assert len(functions) > 0
        assert "abs" in functions
        assert "min" in functions
        assert "max" in functions

    # -------------------------------------------------------------------------
    # Test: Dispose
    # -------------------------------------------------------------------------

    def test_dispose_clears_state(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Dispose should clear viewmodel state."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        viewmodel.dispose()

        # State should be cleared
        assert viewmodel.has_formula is False
        assert len(viewmodel.available_fields) == 0

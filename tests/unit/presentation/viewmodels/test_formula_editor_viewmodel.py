"""Unit tests for FormulaEditorViewModel (Phase F-1, F-3).

Tests formula editor ViewModel behavior:
- Formula editor shows error on invalid input
- Formula editor updates result type live
- Formula editor does NOT modify schema
- Formula editor exposes dependencies (Phase F-3)
- Formula editor exposes unknown_fields (Phase F-3)

PHASE F-1 CONSTRAINTS:
- Read-only validation (no execution)
- No schema mutation
- No formula persistence

PHASE F-3 CONSTRAINTS (ADR-040):
- Read-only dependency analysis
- Deterministic: same inputs → same output
- No DAG/graph construction
- No cycle detection
- No execution logic
"""

import pytest

from doc_helper.application.dto.formula_dto import (
    FormulaDependencyDTO,
    SchemaFieldInfoDTO,
)
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
                entity_id="test_entity",
                label="Value 1",
            ),
            SchemaFieldInfoDTO(
                field_id="value2",
                field_type="NUMBER",
                entity_id="test_entity",
                label="Value 2",
            ),
            SchemaFieldInfoDTO(
                field_id="name",
                field_type="TEXT",
                entity_id="test_entity",
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

    # =========================================================================
    # Phase F-3: Formula Dependency Analysis (Read-Only)
    # =========================================================================

    def test_dependencies_empty_for_empty_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Empty formula should have no dependencies (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("")

        assert viewmodel.dependencies == ()
        assert viewmodel.dependency_count == 0

    def test_dependencies_for_single_field(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Single field formula should have one dependency (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1")

        assert viewmodel.dependency_count == 1
        assert len(viewmodel.dependencies) == 1

        dep = viewmodel.dependencies[0]
        assert dep.field_id == "value1"
        assert dep.is_known is True
        assert dep.field_type == "NUMBER"

    def test_dependencies_for_multiple_fields(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Multiple fields in formula should all appear in dependencies (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2 * 100")

        assert viewmodel.dependency_count == 2

        field_ids = [d.field_id for d in viewmodel.dependencies]
        assert "value1" in field_ids
        assert "value2" in field_ids

    def test_unknown_field_detected(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Unknown field should be detected in dependencies (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field + value1")

        # Should have 2 dependencies
        assert viewmodel.dependency_count == 2

        # One unknown field
        assert viewmodel.has_unknown_fields is True
        assert viewmodel.unknown_count == 1
        assert "unknown_field" in viewmodel.unknown_fields

    def test_unknown_field_in_dependencies_marked_not_known(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Unknown field in dependencies should have is_known=False (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("missing_field")

        deps = viewmodel.dependencies
        assert len(deps) == 1

        dep = deps[0]
        assert dep.field_id == "missing_field"
        assert dep.is_known is False
        assert dep.field_type is None

    def test_known_dependencies_filter(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """known_dependencies should only return known fields (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + unknown_field + value2")

        # All dependencies
        assert viewmodel.dependency_count == 3

        # Only known
        known = viewmodel.known_dependencies
        assert len(known) == 2

        known_ids = [d.field_id for d in known]
        assert "value1" in known_ids
        assert "value2" in known_ids
        assert "unknown_field" not in known_ids

    def test_dependency_analysis_result_exposed(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """dependency_analysis_result should be exposed (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        result = viewmodel.dependency_analysis_result
        assert result is not None
        assert result.has_parse_error is False
        assert len(result.dependencies) == 2

    def test_dependencies_cleared_on_clear_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Clearing formula should clear dependencies (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        assert viewmodel.dependency_count > 0

        viewmodel.clear_formula()

        assert viewmodel.dependencies == ()
        assert viewmodel.dependency_count == 0
        assert viewmodel.has_unknown_fields is False

    def test_dependencies_update_on_formula_change(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Dependencies should update when formula changes (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)

        # First formula
        viewmodel.set_formula("value1")
        assert viewmodel.dependency_count == 1
        assert viewmodel.dependencies[0].field_id == "value1"

        # Change formula
        viewmodel.set_formula("value2 + name")
        assert viewmodel.dependency_count == 2
        field_ids = [d.field_id for d in viewmodel.dependencies]
        assert "value1" not in field_ids
        assert "value2" in field_ids
        assert "name" in field_ids

    def test_dependency_includes_field_type(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Known dependencies should include field type (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("name")

        deps = viewmodel.dependencies
        assert len(deps) == 1
        assert deps[0].field_type == "TEXT"

    def test_function_arguments_included_in_dependencies(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Field references in function calls should be in dependencies (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("max(value1, value2)")

        assert viewmodel.dependency_count == 2
        field_ids = [d.field_id for d in viewmodel.dependencies]
        assert "value1" in field_ids
        assert "value2" in field_ids

    def test_dependency_notifications_triggered(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Setting formula should notify dependency subscribers (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)

        notifications = []
        viewmodel.subscribe("dependencies", lambda: notifications.append("deps"))
        viewmodel.subscribe("unknown_fields", lambda: notifications.append("unknown"))
        viewmodel.subscribe("has_unknown_fields", lambda: notifications.append("has_unknown"))

        viewmodel.set_formula("value1 + unknown_field")

        assert "deps" in notifications
        assert "unknown" in notifications
        assert "has_unknown" in notifications

    def test_dispose_clears_dependency_state(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Dispose should clear dependency state (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + unknown_field")

        assert viewmodel.dependency_count > 0
        assert viewmodel.has_unknown_fields is True

        viewmodel.dispose()

        assert viewmodel.dependencies == ()
        assert viewmodel.unknown_fields == ()
        assert viewmodel.has_unknown_fields is False
        assert viewmodel.dependency_analysis_result is None

    def test_syntax_error_no_dependencies(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Syntax errors should result in no dependencies (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 +++")

        # Parse error
        result = viewmodel.dependency_analysis_result
        assert result is not None
        assert result.has_parse_error is True

        # No dependencies on parse error
        assert viewmodel.dependencies == ()
        assert viewmodel.dependency_count == 0

    def test_dependencies_deterministic(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Same formula should produce same dependencies (Phase F-3)."""
        viewmodel.set_schema_context(schema_fields)

        formula = "value2 + value1 + name"

        # First time
        viewmodel.set_formula(formula)
        deps1 = viewmodel.dependencies

        # Clear and re-set
        viewmodel.clear_formula()
        viewmodel.set_formula(formula)
        deps2 = viewmodel.dependencies

        # Should be identical
        assert deps1 == deps2

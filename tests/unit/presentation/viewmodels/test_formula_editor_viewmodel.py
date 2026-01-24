"""Unit tests for FormulaEditorViewModel (Phase F-1, F-3, F-4, F-5, F-6, F-7).

Tests formula editor ViewModel behavior:
- Formula editor shows error on invalid input
- Formula editor updates result type live
- Formula editor does NOT modify schema
- Formula editor exposes dependencies (Phase F-3)
- Formula editor exposes unknown_fields (Phase F-3)
- Formula editor exposes cycle detection results (Phase F-4)
- Formula editor aggregates diagnostics for display (Phase F-5)
- Formula editor exposes governance state (Phase F-6)
- Formula editor exposes binding state (Phase F-7)

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

PHASE F-4 CONSTRAINTS (ADR-041):
- Read-only cycle analysis
- Deterministic: same inputs → same output
- No DAG execution or topological sorting
- No cycle prevention (analysis-only)
- Same-entity scope only

PHASE F-5 CONSTRAINTS:
- Presentation/ViewModel UX-only (no new business logic)
- Aggregates existing F-1 to F-4 diagnostic info for display
- Human-readable messages (Presentation formatting)
- No new DTOs, no FormulaUseCases modifications

PHASE F-6 CONSTRAINTS:
- Policy evaluation only (no new analysis)
- Deterministic: same diagnostics → same status
- No execution
- No persistence
- No schema mutation

PHASE F-7 CONSTRAINTS:
- Policy and wiring only
- Binding rules: CALCULATED_FIELD allowed, others forbidden
- Governance enforcement: INVALID → blocked
- No persistence
- No execution
- No schema mutation
"""

import pytest

from doc_helper.application.dto.formula_dto import (
    FormulaCycleDTO,
    FormulaDependencyDTO,
    FormulaGovernanceStatus,
    SchemaFieldInfoDTO,
    # Phase F-7: Formula Binding
    FormulaBindingTarget,
    FormulaBindingStatus,
    FormulaBindingDTO,
    FormulaBindingResultDTO,
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

    # =========================================================================
    # Phase F-4: Formula Cycle Detection (Read-Only)
    # =========================================================================

    def test_no_cycle_analysis_by_default(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """No cycle analysis result by default (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        # Cycle analysis is entity-wide, not per-formula
        # Should be None until analyze_entity_cycles is called
        assert viewmodel.cycle_analysis_result is None
        assert viewmodel.has_cycles is False
        assert viewmodel.cycles == ()
        assert viewmodel.cycle_count == 0

    def test_analyze_entity_cycles_no_cycles(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """analyze_entity_cycles should report no cycles for acyclic graph (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        # Linear chain: total → subtotal → base
        result = viewmodel.analyze_entity_cycles({
            "total": ("subtotal",),
            "subtotal": ("base",),
            "base": (),
        })

        assert result.has_cycles is False
        assert viewmodel.has_cycles is False
        assert viewmodel.cycle_count == 0
        assert viewmodel.cycles == ()
        assert viewmodel.analyzed_field_count == 3

    def test_analyze_entity_cycles_detects_simple_cycle(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """analyze_entity_cycles should detect A → B → A cycle (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        result = viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        assert result.has_cycles is True
        assert viewmodel.has_cycles is True
        assert viewmodel.cycle_count == 1

        cycle = viewmodel.cycles[0]
        assert set(cycle.field_ids) == {"field_a", "field_b"}
        assert cycle.severity == "ERROR"

    def test_analyze_entity_cycles_detects_self_reference(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """analyze_entity_cycles should detect self-referential cycle (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        result = viewmodel.analyze_entity_cycles({
            "field_a": ("field_a",),  # Self-reference
        })

        assert result.has_cycles is True
        assert viewmodel.has_cycles is True
        assert viewmodel.cycle_count == 1

        cycle = viewmodel.cycles[0]
        assert cycle.field_ids == ("field_a",)
        assert cycle.is_self_reference is True

    def test_analyze_entity_cycles_detects_multi_node_cycle(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """analyze_entity_cycles should detect A → B → C → A cycle (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        result = viewmodel.analyze_entity_cycles({
            "field_a": ("field_c",),
            "field_b": ("field_a",),
            "field_c": ("field_b",),
        })

        assert result.has_cycles is True
        assert viewmodel.has_cycles is True
        assert viewmodel.cycle_count == 1

        cycle = viewmodel.cycles[0]
        assert set(cycle.field_ids) == {"field_a", "field_b", "field_c"}

    def test_analyze_entity_cycles_detects_multiple_cycles(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """analyze_entity_cycles should detect multiple independent cycles (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        result = viewmodel.analyze_entity_cycles({
            "cycle1_a": ("cycle1_b",),
            "cycle1_b": ("cycle1_a",),
            "cycle2_x": ("cycle2_y",),
            "cycle2_y": ("cycle2_x",),
        })

        assert result.has_cycles is True
        assert viewmodel.cycle_count == 2

        all_ids = set(viewmodel.all_cycle_field_ids)
        assert all_ids == {"cycle1_a", "cycle1_b", "cycle2_x", "cycle2_y"}

    def test_cycle_errors_property(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """cycle_errors should provide human-readable messages (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        errors = viewmodel.cycle_errors
        assert len(errors) == 1
        assert "Circular dependency" in errors[0]
        assert "→" in errors[0]

    def test_all_cycle_field_ids_property(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """all_cycle_field_ids should return all fields in cycles (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        viewmodel.analyze_entity_cycles({
            "normal_field": (),
            "cyclic_a": ("cyclic_b",),
            "cyclic_b": ("cyclic_a",),
        })

        all_ids = set(viewmodel.all_cycle_field_ids)
        assert "cyclic_a" in all_ids
        assert "cyclic_b" in all_ids
        assert "normal_field" not in all_ids

    def test_clear_cycle_analysis(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """clear_cycle_analysis should reset cycle state (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        assert viewmodel.has_cycles is True

        viewmodel.clear_cycle_analysis()

        assert viewmodel.cycle_analysis_result is None
        assert viewmodel.has_cycles is False
        assert viewmodel.cycles == ()
        assert viewmodel.cycle_count == 0

    def test_clear_formula_clears_cycle_analysis(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """clear_formula should also clear cycle analysis (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1")

        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        assert viewmodel.has_cycles is True

        viewmodel.clear_formula()

        assert viewmodel.cycle_analysis_result is None
        assert viewmodel.has_cycles is False

    def test_dispose_clears_cycle_state(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """dispose should clear cycle state (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        assert viewmodel.has_cycles is True

        viewmodel.dispose()

        assert viewmodel.cycle_analysis_result is None
        assert viewmodel.has_cycles is False

    def test_cycle_analysis_deterministic(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Same dependencies should produce same cycle results (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        deps = {
            "field_a": ("field_b",),
            "field_b": ("field_c",),
            "field_c": ("field_a",),
        }

        # First analysis
        result1 = viewmodel.analyze_entity_cycles(deps)

        # Clear and re-analyze
        viewmodel.clear_cycle_analysis()
        result2 = viewmodel.analyze_entity_cycles(deps)

        assert result1.has_cycles == result2.has_cycles
        assert result1.cycles == result2.cycles
        assert result1.all_cycle_field_ids == result2.all_cycle_field_ids

    def test_cycle_notifications_triggered(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """analyze_entity_cycles should notify cycle subscribers (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        notifications = []
        viewmodel.subscribe("has_cycles", lambda: notifications.append("has_cycles"))
        viewmodel.subscribe("cycles", lambda: notifications.append("cycles"))
        viewmodel.subscribe("cycle_count", lambda: notifications.append("cycle_count"))

        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        assert "has_cycles" in notifications
        assert "cycles" in notifications
        assert "cycle_count" in notifications

    def test_empty_dependencies_no_cycles(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Empty dependencies should report no cycles (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        result = viewmodel.analyze_entity_cycles({})

        assert result.has_cycles is False
        assert viewmodel.cycle_count == 0
        assert viewmodel.analyzed_field_count == 0

    def test_cycle_analysis_returns_dto(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """analyze_entity_cycles should return DTO result (Phase F-4)."""
        viewmodel.set_schema_context(schema_fields)

        result = viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        # Should return the same result that's stored
        assert result is viewmodel.cycle_analysis_result
        assert result.has_cycles is True

    # =========================================================================
    # Phase F-5: Diagnostic Aggregation for Display (Presentation-Only)
    # =========================================================================

    def test_no_diagnostics_for_empty_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Empty formula should have no diagnostics (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("")

        assert viewmodel.all_diagnostic_errors == ()
        assert viewmodel.all_diagnostic_warnings == ()
        assert viewmodel.all_diagnostic_info == ()
        assert viewmodel.has_diagnostics is False
        assert viewmodel.diagnostic_status == "empty"
        assert viewmodel.status_message == ""

    def test_diagnostic_status_error_for_invalid_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Invalid formula should have error diagnostic status (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 +++")  # Syntax error

        assert viewmodel.diagnostic_status == "error"
        assert viewmodel.diagnostic_error_count > 0
        assert "error" in viewmodel.status_message.lower()

    def test_diagnostic_status_valid_for_correct_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Valid formula should have valid diagnostic status (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        assert viewmodel.diagnostic_status == "valid"
        assert viewmodel.diagnostic_error_count == 0
        assert "valid" in viewmodel.status_message.lower()

    def test_errors_aggregated_from_validation(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Validation errors should appear in all_diagnostic_errors (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 +")  # Incomplete expression

        errors = viewmodel.all_diagnostic_errors
        assert len(errors) > 0
        # Errors should be prefixed with "Syntax:"
        assert any("Syntax:" in e for e in errors)

    def test_errors_aggregated_from_unknown_fields(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Unknown fields should appear in all_diagnostic_errors (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field + value1")

        errors = viewmodel.all_diagnostic_errors
        assert len(errors) > 0
        # Unknown fields should be prefixed
        assert any("Unknown field:" in e and "unknown_field" in e for e in errors)

    def test_errors_aggregated_from_cycles(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Cycle errors should appear in all_diagnostic_errors (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1")

        # Trigger cycle analysis with a cycle
        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        errors = viewmodel.all_diagnostic_errors
        assert len(errors) > 0
        # Cycle errors should be prefixed
        assert any("Circular dependency:" in e for e in errors)

    def test_warnings_aggregated_from_validation(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Type warnings should appear in all_diagnostic_warnings (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        # Mixing types may produce warnings depending on implementation
        viewmodel.set_formula("value1 + name")  # NUMBER + TEXT

        warnings = viewmodel.all_diagnostic_warnings
        # Warnings may or may not be present depending on type checking
        # This test verifies the property exists and returns a tuple
        assert isinstance(warnings, tuple)

    def test_info_shows_result_type(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Result type should appear in all_diagnostic_info (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        info = viewmodel.all_diagnostic_info
        assert len(info) > 0
        # Should include result type
        assert any("Result type:" in i for i in info)

    def test_info_shows_dependencies(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Dependencies should appear in all_diagnostic_info (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        info = viewmodel.all_diagnostic_info
        assert len(info) > 0
        # Should include dependencies
        assert any("Depends on:" in i for i in info)

    def test_info_shows_analyzed_field_count(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Analyzed field count should appear in all_diagnostic_info (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1")

        viewmodel.analyze_entity_cycles({
            "field_a": (),
            "field_b": (),
        })

        info = viewmodel.all_diagnostic_info
        # Should include analysis count
        assert any("Analyzed" in i and "field" in i for i in info)

    def test_has_diagnostics_true_when_errors_present(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """has_diagnostics should be True when errors exist (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("invalid +++")

        assert viewmodel.has_diagnostics is True

    def test_has_diagnostics_true_when_info_present(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """has_diagnostics should be True when info exists (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")  # Valid formula with info

        assert viewmodel.has_diagnostics is True
        assert len(viewmodel.all_diagnostic_info) > 0

    def test_diagnostic_error_count_matches_errors(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """diagnostic_error_count should match length of errors (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown1 + unknown2")  # Two unknown fields

        count = viewmodel.diagnostic_error_count
        errors = viewmodel.all_diagnostic_errors

        assert count == len(errors)

    def test_diagnostic_warning_count_matches_warnings(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """diagnostic_warning_count should match length of warnings (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        count = viewmodel.diagnostic_warning_count
        warnings = viewmodel.all_diagnostic_warnings

        assert count == len(warnings)

    def test_status_message_shows_error_count(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Status message should show error count when errors exist (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field")

        message = viewmodel.status_message
        # Should mention error(s)
        assert "error" in message.lower()

    def test_diagnostic_properties_clear_on_clear_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Clearing formula should clear diagnostic properties (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field + value1")

        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        assert viewmodel.has_diagnostics is True

        viewmodel.clear_formula()

        assert viewmodel.diagnostic_status == "empty"
        assert viewmodel.all_diagnostic_errors == ()
        assert viewmodel.all_diagnostic_info == ()

    def test_diagnostic_notifications_triggered(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Setting formula should notify diagnostic subscribers (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)

        notifications = []
        viewmodel.subscribe(
            "all_diagnostic_errors", lambda: notifications.append("errors")
        )
        viewmodel.subscribe(
            "diagnostic_status", lambda: notifications.append("status")
        )
        viewmodel.subscribe(
            "status_message", lambda: notifications.append("message")
        )

        viewmodel.set_formula("value1 + value2")

        assert "errors" in notifications
        assert "status" in notifications
        assert "message" in notifications

    def test_dispose_clears_diagnostic_state(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Dispose should clear diagnostic state (Phase F-5)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field")

        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        assert viewmodel.has_diagnostics is True

        viewmodel.dispose()

        assert viewmodel.diagnostic_status == "empty"
        assert viewmodel.has_diagnostics is False
        assert viewmodel.all_diagnostic_errors == ()
        assert viewmodel.all_diagnostic_warnings == ()
        assert viewmodel.all_diagnostic_info == ()

    # =========================================================================
    # Phase F-6: Formula Governance & Enforcement (Policy-Only)
    # =========================================================================

    def test_governance_empty_for_no_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Empty formula should have EMPTY governance status (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("")

        assert viewmodel.governance_status == FormulaGovernanceStatus.EMPTY
        assert viewmodel.is_formula_allowed is True
        assert viewmodel.is_formula_blocked is False
        assert viewmodel.governance_message == ""
        assert viewmodel.governance_blocking_reasons == ()
        assert viewmodel.governance_warning_reasons == ()

    def test_governance_empty_for_whitespace_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Whitespace-only formula should have EMPTY governance status (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("   ")

        assert viewmodel.governance_status == FormulaGovernanceStatus.EMPTY
        assert viewmodel.is_formula_allowed is True

    def test_governance_valid_for_correct_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Valid formula should have VALID governance status (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        assert viewmodel.governance_status == FormulaGovernanceStatus.VALID
        assert viewmodel.is_formula_allowed is True
        assert viewmodel.is_formula_blocked is False
        assert viewmodel.governance_blocking_reasons == ()
        # May have warnings from validation (type inference)
        assert "valid" in viewmodel.governance_message.lower()

    def test_governance_invalid_for_syntax_error(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Syntax error should result in INVALID governance status (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 +++")

        assert viewmodel.governance_status == FormulaGovernanceStatus.INVALID
        assert viewmodel.is_formula_allowed is False
        assert viewmodel.is_formula_blocked is True
        assert len(viewmodel.governance_blocking_reasons) > 0
        assert "blocked" in viewmodel.governance_message.lower()

    def test_governance_invalid_for_unknown_field(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Unknown field should result in INVALID governance status (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field + value1")

        assert viewmodel.governance_status == FormulaGovernanceStatus.INVALID
        assert viewmodel.is_formula_blocked is True
        assert len(viewmodel.governance_blocking_reasons) > 0

    def test_governance_invalid_for_cycles(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Cycles should result in INVALID governance status (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1")  # Valid formula initially

        assert viewmodel.governance_status == FormulaGovernanceStatus.VALID

        # Trigger cycle analysis with a cycle
        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        assert viewmodel.governance_status == FormulaGovernanceStatus.INVALID
        assert viewmodel.is_formula_blocked is True
        # Should include cycle error
        reasons = " ".join(viewmodel.governance_blocking_reasons)
        assert "circular" in reasons.lower() or "cycle" in reasons.lower()

    def test_governance_result_dto_exposed(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """governance_result should expose the DTO (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        result = viewmodel.governance_result
        assert result is not None
        assert result.status == FormulaGovernanceStatus.VALID
        assert result.is_allowed is True

    def test_governance_none_before_formula_set(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """governance_result should be None before formula is set (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)

        # No formula set yet
        assert viewmodel.governance_result is None
        # Default status should be EMPTY
        assert viewmodel.governance_status == FormulaGovernanceStatus.EMPTY
        assert viewmodel.is_formula_allowed is True

    def test_governance_updates_on_formula_change(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Governance should update when formula changes (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)

        # Valid formula
        viewmodel.set_formula("value1")
        assert viewmodel.governance_status == FormulaGovernanceStatus.VALID

        # Invalid formula
        viewmodel.set_formula("unknown_field")
        assert viewmodel.governance_status == FormulaGovernanceStatus.INVALID

        # Empty formula
        viewmodel.set_formula("")
        assert viewmodel.governance_status == FormulaGovernanceStatus.EMPTY

    def test_governance_updates_on_cycle_analysis(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Governance should update when cycle analysis changes (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1")

        assert viewmodel.governance_status == FormulaGovernanceStatus.VALID

        # Add cycles
        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })
        assert viewmodel.governance_status == FormulaGovernanceStatus.INVALID

        # Clear cycles
        viewmodel.clear_cycle_analysis()
        assert viewmodel.governance_status == FormulaGovernanceStatus.VALID

    def test_governance_cleared_on_clear_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Clearing formula should reset governance state (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field")

        assert viewmodel.governance_status == FormulaGovernanceStatus.INVALID

        viewmodel.clear_formula()

        assert viewmodel.governance_status == FormulaGovernanceStatus.EMPTY
        assert viewmodel.governance_result is None
        assert viewmodel.governance_blocking_reasons == ()
        assert viewmodel.governance_warning_reasons == ()

    def test_governance_cleared_on_dispose(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Dispose should reset governance state (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field")

        assert viewmodel.governance_status == FormulaGovernanceStatus.INVALID

        viewmodel.dispose()

        assert viewmodel.governance_status == FormulaGovernanceStatus.EMPTY
        assert viewmodel.governance_result is None

    def test_governance_notifications_triggered(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Setting formula should notify governance subscribers (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)

        notifications = []
        viewmodel.subscribe(
            "governance_result", lambda: notifications.append("result")
        )
        viewmodel.subscribe(
            "governance_status", lambda: notifications.append("status")
        )
        viewmodel.subscribe(
            "is_formula_allowed", lambda: notifications.append("allowed")
        )
        viewmodel.subscribe(
            "is_formula_blocked", lambda: notifications.append("blocked")
        )
        viewmodel.subscribe(
            "governance_message", lambda: notifications.append("message")
        )

        viewmodel.set_formula("value1 + value2")

        assert "result" in notifications
        assert "status" in notifications
        assert "allowed" in notifications
        assert "blocked" in notifications
        assert "message" in notifications

    def test_governance_blocking_reasons_from_combined_errors(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Blocking reasons should include both validation and cycle errors (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field")  # Validation error

        # Also add cycles
        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        reasons = viewmodel.governance_blocking_reasons
        # Should have both unknown field error and cycle error
        assert len(reasons) >= 2

    def test_governance_is_allowed_semantic(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """is_formula_allowed should be inverse of is_formula_blocked (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)

        # Valid formula
        viewmodel.set_formula("value1")
        assert viewmodel.is_formula_allowed is True
        assert viewmodel.is_formula_blocked is False

        # Invalid formula
        viewmodel.set_formula("unknown_field")
        assert viewmodel.is_formula_allowed is False
        assert viewmodel.is_formula_blocked is True

        # Empty formula (allowed)
        viewmodel.set_formula("")
        assert viewmodel.is_formula_allowed is True
        assert viewmodel.is_formula_blocked is False

    def test_governance_deterministic(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Same formula should produce same governance result (Phase F-6)."""
        viewmodel.set_schema_context(schema_fields)

        formula = "value1 + value2"

        # First time
        viewmodel.set_formula(formula)
        result1 = viewmodel.governance_result
        status1 = viewmodel.governance_status

        # Clear and re-set
        viewmodel.clear_formula()
        viewmodel.set_formula(formula)
        result2 = viewmodel.governance_result
        status2 = viewmodel.governance_status

        assert result1 is not None
        assert result2 is not None
        assert result1.status == result2.status
        assert result1.blocking_reasons == result2.blocking_reasons
        assert result1.warning_reasons == result2.warning_reasons
        assert status1 == status2

    # =========================================================================
    # Phase F-7: Formula Binding State (Policy & Wiring Only)
    # =========================================================================

    def test_binding_target_none_by_default(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Binding target should be None by default (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)

        assert viewmodel.binding_target is None
        assert viewmodel.binding_target_id == ""

    def test_set_binding_target_calculated_field(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Setting CALCULATED_FIELD binding target should succeed (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)

        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_field_id",
        )

        assert viewmodel.binding_target == FormulaBindingTarget.CALCULATED_FIELD
        assert viewmodel.binding_target_id == "target_field_id"

    def test_set_binding_target_validation_rule_recorded(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Setting VALIDATION_RULE binding target should be recorded (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)

        viewmodel.set_binding_target(
            FormulaBindingTarget.VALIDATION_RULE,
            "rule_id",
        )

        # Target is recorded but will be blocked
        assert viewmodel.binding_target == FormulaBindingTarget.VALIDATION_RULE
        assert viewmodel.binding_target_id == "rule_id"

    def test_set_binding_target_output_mapping_recorded(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Setting OUTPUT_MAPPING binding target should be recorded (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)

        viewmodel.set_binding_target(
            FormulaBindingTarget.OUTPUT_MAPPING,
            "mapping_id",
        )

        # Target is recorded but will be blocked
        assert viewmodel.binding_target == FormulaBindingTarget.OUTPUT_MAPPING
        assert viewmodel.binding_target_id == "mapping_id"

    def test_clear_binding_target(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """clear_binding_target should reset binding state (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        viewmodel.clear_binding_target()

        assert viewmodel.binding_target is None
        assert viewmodel.binding_target_id == ""

    def test_is_binding_allowed_no_target(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """No binding target should result in is_binding_allowed=False (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        # No target set
        assert viewmodel.binding_target is None
        assert viewmodel.is_binding_allowed is False

    def test_is_binding_allowed_calculated_field_valid_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """CALCULATED_FIELD with valid formula should allow binding (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.governance_status == FormulaGovernanceStatus.VALID
        assert viewmodel.is_binding_allowed is True
        assert viewmodel.binding_block_reason is None

    def test_is_binding_allowed_calculated_field_empty_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """CALCULATED_FIELD with empty formula should allow binding (clears) (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.governance_status == FormulaGovernanceStatus.EMPTY
        assert viewmodel.is_binding_allowed is True
        assert viewmodel.binding_block_reason is None

    def test_is_binding_blocked_invalid_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Invalid formula should block binding (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.governance_status == FormulaGovernanceStatus.INVALID
        assert viewmodel.is_binding_allowed is False
        assert viewmodel.binding_block_reason is not None
        # Block reason contains error information
        assert "error" in viewmodel.binding_block_reason.lower()

    def test_is_binding_blocked_unsupported_target_validation_rule(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """VALIDATION_RULE target should block binding in F-7 (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")  # Valid formula
        viewmodel.set_binding_target(
            FormulaBindingTarget.VALIDATION_RULE,
            "rule_id",
        )

        assert viewmodel.governance_status == FormulaGovernanceStatus.VALID
        assert viewmodel.is_binding_allowed is False
        assert viewmodel.binding_block_reason is not None
        assert "not supported" in viewmodel.binding_block_reason.lower()

    def test_is_binding_blocked_unsupported_target_output_mapping(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """OUTPUT_MAPPING target should block binding in F-7 (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")  # Valid formula
        viewmodel.set_binding_target(
            FormulaBindingTarget.OUTPUT_MAPPING,
            "mapping_id",
        )

        assert viewmodel.governance_status == FormulaGovernanceStatus.VALID
        assert viewmodel.is_binding_allowed is False
        assert viewmodel.binding_block_reason is not None
        assert "not supported" in viewmodel.binding_block_reason.lower()

    def test_binding_status_allowed_for_valid_calculated_field(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """binding_status should be ALLOWED for valid CALCULATED_FIELD binding (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.binding_status == FormulaBindingStatus.ALLOWED

    def test_binding_status_cleared_for_empty_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """binding_status should be CLEARED for empty formula (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.binding_status == FormulaBindingStatus.CLEARED

    def test_binding_status_blocked_invalid_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """binding_status should be BLOCKED_INVALID_FORMULA for invalid formula (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.binding_status == FormulaBindingStatus.BLOCKED_INVALID_FORMULA

    def test_binding_status_blocked_unsupported_target(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """binding_status should be BLOCKED_UNSUPPORTED_TARGET for forbidden targets (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.VALIDATION_RULE,
            "rule_id",
        )

        assert viewmodel.binding_status == FormulaBindingStatus.BLOCKED_UNSUPPORTED_TARGET

    def test_binding_status_message_for_allowed(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """binding_status_message should describe allowed status (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        message = viewmodel.binding_status_message
        assert "allowed" in message.lower()

    def test_binding_status_message_for_blocked(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """binding_status_message should describe blocked status (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        message = viewmodel.binding_status_message
        assert "cannot" in message.lower() or "blocked" in message.lower()

    def test_binding_status_message_for_no_target(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """binding_status_message should indicate no target set (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        # No target set
        message = viewmodel.binding_status_message
        # Message contains "target" and "configured" (e.g., "No binding target configured")
        assert "target" in message.lower() and "configured" in message.lower()

    def test_can_save_binding_true_for_allowed(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """can_save_binding should be True when binding is allowed (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.can_save_binding is True

    def test_can_save_binding_true_for_cleared(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """can_save_binding should be True when formula is empty (clear binding) (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.can_save_binding is True

    def test_can_save_binding_false_for_blocked(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """can_save_binding should be False when binding is blocked (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.can_save_binding is False

    def test_can_save_binding_false_for_no_target(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """can_save_binding should be False when no target is set (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        # No target
        assert viewmodel.can_save_binding is False

    def test_get_binding_result_returns_dto(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """get_binding_result should return FormulaBindingResultDTO (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        result = viewmodel.get_binding_result()

        assert isinstance(result, FormulaBindingResultDTO)
        assert result.status == FormulaBindingStatus.ALLOWED
        assert result.binding is not None
        assert result.binding.target_type == FormulaBindingTarget.CALCULATED_FIELD
        assert result.binding.target_id == "target_id"
        assert result.binding.formula_text == "value1 + value2"

    def test_get_binding_result_blocked_for_invalid(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """get_binding_result should return blocked result for invalid formula (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        result = viewmodel.get_binding_result()

        assert result.status == FormulaBindingStatus.BLOCKED_INVALID_FORMULA
        assert result.is_blocked is True
        assert result.block_reason is not None

    def test_binding_updates_on_formula_change(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Binding state should update when formula changes (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        # Valid formula
        viewmodel.set_formula("value1 + value2")
        assert viewmodel.is_binding_allowed is True
        assert viewmodel.binding_status == FormulaBindingStatus.ALLOWED

        # Invalid formula
        viewmodel.set_formula("unknown_field")
        assert viewmodel.is_binding_allowed is False
        assert viewmodel.binding_status == FormulaBindingStatus.BLOCKED_INVALID_FORMULA

        # Empty formula
        viewmodel.set_formula("")
        assert viewmodel.is_binding_allowed is True
        assert viewmodel.binding_status == FormulaBindingStatus.CLEARED

    def test_binding_updates_on_target_change(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Binding state should update when target changes (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        # CALCULATED_FIELD - allowed
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )
        assert viewmodel.is_binding_allowed is True

        # VALIDATION_RULE - blocked
        viewmodel.set_binding_target(
            FormulaBindingTarget.VALIDATION_RULE,
            "rule_id",
        )
        assert viewmodel.is_binding_allowed is False
        assert viewmodel.binding_status == FormulaBindingStatus.BLOCKED_UNSUPPORTED_TARGET

    def test_binding_cleared_on_clear_formula(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """clear_formula should preserve binding target but update status (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.binding_status == FormulaBindingStatus.ALLOWED

        viewmodel.clear_formula()

        # Target preserved, but status is CLEARED
        assert viewmodel.binding_target == FormulaBindingTarget.CALCULATED_FIELD
        assert viewmodel.binding_target_id == "target_id"
        assert viewmodel.binding_status == FormulaBindingStatus.CLEARED

    def test_binding_cleared_on_dispose(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """dispose should clear binding target (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        viewmodel.dispose()

        assert viewmodel.binding_target is None
        assert viewmodel.binding_target_id == ""

    def test_binding_notifications_triggered_on_set_target(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """set_binding_target should notify binding subscribers (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")

        notifications = []
        viewmodel.subscribe(
            "binding_target", lambda: notifications.append("target")
        )
        viewmodel.subscribe(
            "binding_target_id", lambda: notifications.append("target_id")
        )
        viewmodel.subscribe(
            "is_binding_allowed", lambda: notifications.append("allowed")
        )
        viewmodel.subscribe(
            "binding_status", lambda: notifications.append("status")
        )
        viewmodel.subscribe(
            "binding_status_message", lambda: notifications.append("message")
        )

        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert "target" in notifications
        assert "target_id" in notifications
        assert "allowed" in notifications
        assert "status" in notifications
        assert "message" in notifications

    def test_binding_notifications_triggered_on_clear_target(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """clear_binding_target should notify binding subscribers (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        notifications = []
        viewmodel.subscribe(
            "binding_target", lambda: notifications.append("target")
        )

        viewmodel.clear_binding_target()

        assert "target" in notifications

    def test_binding_deterministic(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Same inputs should produce same binding result (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)

        # First evaluation
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )
        result1 = viewmodel.get_binding_result()
        status1 = viewmodel.binding_status

        # Clear and re-evaluate
        viewmodel.clear_binding_target()
        viewmodel.clear_formula()
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )
        result2 = viewmodel.get_binding_result()
        status2 = viewmodel.binding_status

        assert result1.status == result2.status
        assert status1 == status2

    def test_binding_with_cycles_blocked(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Formula with cycles should be blocked from binding (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1")  # Valid formula initially
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        assert viewmodel.is_binding_allowed is True

        # Add cycles - should block binding
        viewmodel.analyze_entity_cycles({
            "field_a": ("field_b",),
            "field_b": ("field_a",),
        })

        assert viewmodel.governance_status == FormulaGovernanceStatus.INVALID
        assert viewmodel.is_binding_allowed is False
        assert viewmodel.binding_status == FormulaBindingStatus.BLOCKED_INVALID_FORMULA

    def test_binding_valid_with_warnings(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Formula with warnings should still allow binding (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        # This formula is valid (may have type warnings but no errors)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        # Even with potential warnings, VALID and VALID_WITH_WARNINGS allow binding
        assert viewmodel.governance_status in (
            FormulaGovernanceStatus.VALID,
            FormulaGovernanceStatus.VALID_WITH_WARNINGS,
        )
        assert viewmodel.is_binding_allowed is True

    def test_binding_result_includes_governance_status(
        self,
        viewmodel: FormulaEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Binding result should include governance status (Phase F-7)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("value1 + value2")
        viewmodel.set_binding_target(
            FormulaBindingTarget.CALCULATED_FIELD,
            "target_id",
        )

        result = viewmodel.get_binding_result()

        assert result.binding is not None
        assert result.binding.governance_status == FormulaGovernanceStatus.VALID

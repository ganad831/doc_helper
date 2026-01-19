"""Tests for formula dependency tracking."""

import pytest

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.formula.dependency_tracker import DependencyTracker, DependencyGraph
from doc_helper.domain.formula.parser import FormulaParser


class TestDependencyGraph:
    """Tests for DependencyGraph."""

    def test_create_graph(self) -> None:
        """DependencyGraph should be created with dependencies."""
        graph = DependencyGraph(dependencies={"a": {"b", "c"}, "b": {"c"}})
        assert graph.dependencies == {"a": {"b", "c"}, "b": {"c"}}

    def test_get_dependencies(self) -> None:
        """DependencyGraph should return field dependencies."""
        graph = DependencyGraph(dependencies={"a": {"b", "c"}})
        deps = graph.get_dependencies("a")
        assert deps == {"b", "c"}

    def test_get_dependencies_no_deps(self) -> None:
        """DependencyGraph should return empty set for field with no dependencies."""
        graph = DependencyGraph(dependencies={"a": set()})
        deps = graph.get_dependencies("a")
        assert deps == set()

    def test_get_dependencies_unknown_field(self) -> None:
        """DependencyGraph should return empty set for unknown field."""
        graph = DependencyGraph(dependencies={})
        deps = graph.get_dependencies("unknown")
        assert deps == set()

    def test_has_field(self) -> None:
        """DependencyGraph should check field existence."""
        graph = DependencyGraph(dependencies={"a": set()})
        assert graph.has_field("a")
        assert not graph.has_field("b")

    def test_graph_requires_dict(self) -> None:
        """DependencyGraph should require dict for dependencies."""
        with pytest.raises(TypeError, match="dependencies must be a dict"):
            DependencyGraph(dependencies=[])  # type: ignore


class TestDependencyTracker:
    """Tests for DependencyTracker."""

    def test_extract_dependencies_no_references(self) -> None:
        """Tracker should extract no dependencies from literals."""
        parser = FormulaParser("42")
        ast = parser.parse()
        tracker = DependencyTracker()
        deps = tracker.extract_dependencies(ast)
        assert deps == set()

    def test_extract_dependencies_single_reference(self) -> None:
        """Tracker should extract single field reference."""
        parser = FormulaParser("field1")
        ast = parser.parse()
        tracker = DependencyTracker()
        deps = tracker.extract_dependencies(ast)
        assert deps == {"field1"}

    def test_extract_dependencies_multiple_references(self) -> None:
        """Tracker should extract multiple field references."""
        parser = FormulaParser("field1 + field2")
        ast = parser.parse()
        tracker = DependencyTracker()
        deps = tracker.extract_dependencies(ast)
        assert deps == {"field1", "field2"}

    def test_extract_dependencies_duplicate_references(self) -> None:
        """Tracker should deduplicate field references."""
        parser = FormulaParser("field1 + field1 * 2")
        ast = parser.parse()
        tracker = DependencyTracker()
        deps = tracker.extract_dependencies(ast)
        assert deps == {"field1"}

    def test_extract_dependencies_from_function_call(self) -> None:
        """Tracker should extract dependencies from function arguments."""
        parser = FormulaParser("min(field1, field2)")
        ast = parser.parse()
        tracker = DependencyTracker()
        deps = tracker.extract_dependencies(ast)
        assert deps == {"field1", "field2"}

    def test_extract_dependencies_nested_expressions(self) -> None:
        """Tracker should extract dependencies from nested expressions."""
        parser = FormulaParser("(field1 + field2) * field3")
        ast = parser.parse()
        tracker = DependencyTracker()
        deps = tracker.extract_dependencies(ast)
        assert deps == {"field1", "field2", "field3"}

    def test_build_graph_from_string_formulas(self) -> None:
        """Tracker should build graph from string formulas."""
        tracker = DependencyTracker()
        formulas = {"total": "field1 + field2", "double": "total * 2"}
        graph = tracker.build_graph(formulas)
        assert graph.get_dependencies("total") == {"field1", "field2"}
        assert graph.get_dependencies("double") == {"total"}

    def test_build_graph_from_ast_nodes(self) -> None:
        """Tracker should build graph from AST nodes."""
        parser1 = FormulaParser("field1 + field2")
        ast1 = parser1.parse()
        tracker = DependencyTracker()
        formulas = {"total": ast1}
        graph = tracker.build_graph(formulas)
        assert graph.get_dependencies("total") == {"field1", "field2"}

    def test_find_circular_dependencies_none(self) -> None:
        """Tracker should return Success when no cycles exist."""
        tracker = DependencyTracker()
        formulas = {"total": "field1 + field2", "double": "total * 2"}
        graph = tracker.build_graph(formulas)
        result = tracker.find_circular_dependencies(graph)
        assert isinstance(result, Success)

    def test_find_circular_dependencies_self_reference(self) -> None:
        """Tracker should detect self-referencing cycles."""
        tracker = DependencyTracker()
        parser = FormulaParser("field1 + 1")
        ast = parser.parse()
        graph = DependencyGraph(dependencies={"field1": {"field1"}})
        result = tracker.find_circular_dependencies(graph)
        assert isinstance(result, Failure)
        assert len(result.error) > 0
        assert "field1 -> field1" in result.error[0]

    def test_find_circular_dependencies_two_fields(self) -> None:
        """Tracker should detect two-field cycles."""
        tracker = DependencyTracker()
        graph = DependencyGraph(dependencies={"a": {"b"}, "b": {"a"}})
        result = tracker.find_circular_dependencies(graph)
        assert isinstance(result, Failure)
        assert len(result.error) > 0

    def test_find_circular_dependencies_three_fields(self) -> None:
        """Tracker should detect three-field cycles."""
        tracker = DependencyTracker()
        graph = DependencyGraph(dependencies={"a": {"b"}, "b": {"c"}, "c": {"a"}})
        result = tracker.find_circular_dependencies(graph)
        assert isinstance(result, Failure)

    def test_topological_sort_no_dependencies(self) -> None:
        """Tracker should handle fields with no dependencies."""
        tracker = DependencyTracker()
        graph = DependencyGraph(dependencies={"a": set(), "b": set()})
        result = tracker.topological_sort(graph)
        assert isinstance(result, Success)
        assert set(result.value) == {"a", "b"}

    def test_topological_sort_linear_dependency(self) -> None:
        """Tracker should sort linear dependencies."""
        tracker = DependencyTracker()
        graph = DependencyGraph(dependencies={"a": set(), "b": {"a"}, "c": {"b"}})
        result = tracker.topological_sort(graph)
        assert isinstance(result, Success)
        # c depends on b, b depends on a, so order should be: a, b, c
        order = result.value
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_topological_sort_branching_dependency(self) -> None:
        """Tracker should sort branching dependencies."""
        tracker = DependencyTracker()
        # total depends on both field1 and field2
        # double depends on total
        graph = DependencyGraph(
            dependencies={
                "field1": set(),
                "field2": set(),
                "total": {"field1", "field2"},
                "double": {"total"},
            }
        )
        result = tracker.topological_sort(graph)
        assert isinstance(result, Success)
        order = result.value
        # field1 and field2 must come before total
        assert order.index("field1") < order.index("total")
        assert order.index("field2") < order.index("total")
        # total must come before double
        assert order.index("total") < order.index("double")

    def test_topological_sort_with_cycle_returns_failure(self) -> None:
        """Tracker should return Failure for cyclic dependencies."""
        tracker = DependencyTracker()
        graph = DependencyGraph(dependencies={"a": {"b"}, "b": {"a"}})
        result = tracker.topological_sort(graph)
        assert isinstance(result, Failure)
        assert "Circular dependencies detected" in result.error

    def test_build_graph_invalid_formula_type_raises(self) -> None:
        """Tracker should reject invalid formula types."""
        tracker = DependencyTracker()
        with pytest.raises(TypeError, match="must be string or ASTNode"):
            tracker.build_graph({"field1": 123})  # type: ignore

"""Dependency tracking for formulas.

Analyzes formulas to find field dependencies and detect circular references.
"""

from dataclasses import dataclass
from typing import Any

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.formula.ast_nodes import (
    ASTNode,
    BinaryOp,
    UnaryOp,
    Literal,
    FieldReference,
    FunctionCall,
)


@dataclass(frozen=True)
class DependencyGraph:
    """Graph of field dependencies.

    Each field can depend on other fields through formulas.
    """

    dependencies: dict  # Dict[str, set[str]] - field -> set of fields it depends on

    def __post_init__(self) -> None:
        """Validate dependency graph."""
        if not isinstance(self.dependencies, dict):
            raise TypeError("dependencies must be a dict")

    def get_dependencies(self, field_name: str) -> set:
        """Get direct dependencies of a field.

        Args:
            field_name: Field name

        Returns:
            Set of field names this field depends on
        """
        return self.dependencies.get(field_name, set())

    def has_field(self, field_name: str) -> bool:
        """Check if field is in the graph.

        Args:
            field_name: Field name

        Returns:
            True if field exists in graph
        """
        return field_name in self.dependencies

    def add_dependency(self, field_name: str, depends_on: str) -> None:
        """Add a dependency edge.

        Args:
            field_name: Field that depends on another
            depends_on: Field being depended upon
        """
        if field_name not in self.dependencies:
            object.__setattr__(
                self, "dependencies", {**self.dependencies, field_name: set()}
            )
        self.dependencies[field_name].add(depends_on)


class DependencyTracker:
    """Tracks field dependencies in formulas.

    Can:
    - Extract field references from AST
    - Build dependency graph
    - Detect circular dependencies
    - Compute evaluation order (topological sort)

    Example:
        tracker = DependencyTracker()
        deps = tracker.extract_dependencies(ast)
        # Returns: {'field1', 'field2', ...}

        graph = tracker.build_graph({"total": "field1 + field2", ...})
        circular = tracker.find_circular_dependencies(graph)
        # Returns: Success(None) or Failure(["field1 -> field2 -> field1"])
    """

    def extract_dependencies(self, node: ASTNode) -> set:
        """Extract all field references from an AST.

        Args:
            node: AST node to analyze

        Returns:
            Set of field names referenced in the AST
        """
        dependencies = set()
        self._collect_field_references(node, dependencies)
        return dependencies

    def _collect_field_references(self, node: ASTNode, dependencies: set) -> None:
        """Recursively collect field references (internal).

        Args:
            node: AST node
            dependencies: Set to collect field names into
        """
        if isinstance(node, FieldReference):
            dependencies.add(node.field_name)

        elif isinstance(node, BinaryOp):
            self._collect_field_references(node.left, dependencies)
            self._collect_field_references(node.right, dependencies)

        elif isinstance(node, UnaryOp):
            self._collect_field_references(node.operand, dependencies)

        elif isinstance(node, FunctionCall):
            for arg in node.arguments:
                self._collect_field_references(arg, dependencies)

        # Literals have no dependencies

    def build_graph(self, formulas: dict) -> DependencyGraph:
        """Build dependency graph from field formulas.

        Args:
            formulas: Dict mapping field names to AST nodes

        Returns:
            DependencyGraph showing field dependencies
        """
        from doc_helper.domain.formula.parser import FormulaParser

        dependencies = {}

        for field_name, formula_value in formulas.items():
            # Parse formula if it's a string
            if isinstance(formula_value, str):
                parser = FormulaParser(formula_value)
                ast = parser.parse()
            elif isinstance(formula_value, ASTNode):
                ast = formula_value
            else:
                raise TypeError(f"Formula for '{field_name}' must be string or ASTNode")

            # Extract dependencies
            field_deps = self.extract_dependencies(ast)
            dependencies[field_name] = field_deps

        return DependencyGraph(dependencies=dependencies)

    def find_circular_dependencies(self, graph: DependencyGraph) -> Result[None, list]:
        """Find circular dependencies in a dependency graph.

        Args:
            graph: Dependency graph to check

        Returns:
            Success(None) if no cycles found, Failure(list of cycles) if cycles exist
        """
        cycles = []

        # Track visited nodes during DFS
        visited = set()
        rec_stack = set()  # Recursion stack for cycle detection
        path = []  # Current path for cycle reporting

        def dfs(field_name: str) -> bool:
            """DFS to detect cycles.

            Returns:
                True if cycle detected
            """
            visited.add(field_name)
            rec_stack.add(field_name)
            path.append(field_name)

            # Check all dependencies
            for dep in graph.get_dependencies(field_name):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    cycle_str = " -> ".join(cycle)
                    cycles.append(cycle_str)
                    return True

            path.pop()
            rec_stack.remove(field_name)
            return False

        # Check each field
        for field_name in graph.dependencies:
            if field_name not in visited:
                dfs(field_name)

        if cycles:
            return Failure(cycles)
        return Success(None)

    def topological_sort(self, graph: DependencyGraph) -> Result[list, str]:
        """Compute evaluation order for fields (topological sort).

        Fields with no dependencies come first.
        Fields are ordered so that dependencies are evaluated before dependents.

        Args:
            graph: Dependency graph

        Returns:
            Success(list of field names in evaluation order) or Failure(error)
        """
        # Check for cycles first
        cycle_result = self.find_circular_dependencies(graph)
        if isinstance(cycle_result, Failure):
            return Failure(f"Circular dependencies detected: {cycle_result.error}")

        # Kahn's algorithm for topological sort
        # Calculate in-degrees (number of fields this field depends on)
        in_degree = {}
        for field in graph.dependencies:
            # In-degree is the number of dependencies this field has
            in_degree[field] = len(graph.get_dependencies(field))

        # Queue of fields with no dependencies (in-degree 0)
        queue = [field for field, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Process field with no remaining dependencies
            field = queue.pop(0)
            result.append(field)

            # Find fields that depend on this field and reduce their in-degree
            for other_field in graph.dependencies:
                if field in graph.get_dependencies(other_field):
                    in_degree[other_field] -= 1
                    if in_degree[other_field] == 0:
                        queue.append(other_field)

        return Success(result)

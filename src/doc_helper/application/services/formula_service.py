"""Formula service for coordinating formula evaluation."""

from typing import Any

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.formula.dependency_tracker import DependencyTracker
from doc_helper.domain.formula.evaluator import EvaluationContext, FormulaEvaluator
from doc_helper.domain.formula.parser import FormulaParser
from doc_helper.domain.project.project import Project
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class FormulaService:
    """Service for evaluating formulas and managing dependencies.

    Coordinates formula evaluation across project fields,
    tracking dependencies and detecting circular references.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Service is stateless (no instance state beyond parser/evaluator)
    - Service coordinates domain logic, doesn't contain it
    - Returns Result monad for error handling

    Example:
        service = FormulaService()
        result = service.evaluate_formula(
            formula="field1 + field2",
            field_values={"field1": 10, "field2": 20}
        )
        if isinstance(result, Success):
            print(result.value)  # 30
    """

    def evaluate_formula(
        self,
        formula: str,
        field_values: dict[str, Any],
        functions: dict[str, Any] | None = None,
    ) -> Result[Any, str]:
        """Evaluate a formula expression.

        Args:
            formula: Formula expression to evaluate
            field_values: Field values to use in evaluation
            functions: Optional functions to use in evaluation

        Returns:
            Success(value) if evaluation succeeded, Failure(error) otherwise
        """
        if not isinstance(formula, str):
            return Failure("formula must be a string")
        if not isinstance(field_values, dict):
            return Failure("field_values must be a dictionary")

        try:
            # Parse formula
            parser = FormulaParser(formula)
            ast = parser.parse()

            # Evaluate formula
            context = EvaluationContext(
                field_values=field_values,
                functions=functions or {},
            )
            evaluator = FormulaEvaluator(context)
            return evaluator.evaluate(ast)
        except Exception as e:
            return Failure(str(e))

    def evaluate_project_formulas(
        self,
        project: Project,
        entity_definition: EntityDefinition,
    ) -> Result[dict[FieldDefinitionId, Any], str]:
        """Evaluate all formulas in a project.

        Args:
            project: Project to evaluate formulas for
            entity_definition: Entity definition with field formulas

        Returns:
            Success(dict of field_id -> computed value) if successful,
            Failure(error) otherwise
        """
        if not isinstance(project, Project):
            return Failure("project must be a Project instance")
        if not isinstance(entity_definition, EntityDefinition):
            return Failure("entity_definition must be an EntityDefinition")

        # Build field values dict for evaluation context
        field_values = {
            field_id.value: field_value.value
            for field_id, field_value in project.field_values.items()
        }

        # Find all calculated fields
        calculated_fields = {
            field_id: field_def
            for field_id, field_def in entity_definition.fields.items()
            if field_def.formula is not None
        }

        # Check for circular dependencies
        dep_result = self._check_dependencies(calculated_fields)
        if isinstance(dep_result, Failure):
            return dep_result

        # Evaluate formulas in dependency order
        evaluation_order = dep_result.value
        computed_values = {}

        for field_id in evaluation_order:
            field_def = calculated_fields[field_id]
            if field_def.formula is None:
                continue

            # Evaluate formula
            result = self.evaluate_formula(
                formula=field_def.formula,
                field_values=field_values,
            )

            if isinstance(result, Failure):
                return Failure(
                    f"Error evaluating formula for field '{field_id.value}': {result.error}"
                )

            # Store computed value
            computed_values[field_id] = result.value
            # Update field values for subsequent evaluations
            field_values[field_id.value] = result.value

        return Success(computed_values)

    def get_field_dependencies(
        self,
        formula: str,
    ) -> Result[set[str], str]:
        """Get field dependencies from a formula.

        Args:
            formula: Formula expression

        Returns:
            Success(set of field names) if successful, Failure(error) otherwise
        """
        if not isinstance(formula, str):
            return Failure("formula must be a string")

        if not formula.strip():
            return Success(set())

        try:
            # Parse formula
            parser = FormulaParser(formula)
            ast = parser.parse()

            # Extract field references from AST
            dependencies = self._extract_field_references(ast)
            return Success(dependencies)
        except Exception as e:
            return Failure(str(e))

    def _check_dependencies(
        self,
        calculated_fields: dict[FieldDefinitionId, FieldDefinition],
    ) -> Result[list[FieldDefinitionId], str]:
        """Check for circular dependencies and return evaluation order.

        Args:
            calculated_fields: Dictionary of calculated fields

        Returns:
            Success(evaluation order) if no circular dependencies,
            Failure(error) otherwise
        """
        # Build formulas dictionary (field_name -> formula_string)
        formulas = {
            field_id.value: field_def.formula
            for field_id, field_def in calculated_fields.items()
            if field_def.formula is not None
        }

        if not formulas:
            return Success([])

        # Create dependency tracker and build graph
        dependency_tracker = DependencyTracker()
        graph = dependency_tracker.build_graph(formulas)

        # Add all referenced fields to the graph if they're not already there
        # This ensures topological sort works correctly
        all_referenced_fields = set()
        for deps in graph.dependencies.values():
            all_referenced_fields.update(deps)

        # Add missing fields with no dependencies
        for field_name in all_referenced_fields:
            if field_name not in graph.dependencies:
                graph.dependencies[field_name] = set()

        # Check for circular dependencies
        cycle_result = dependency_tracker.find_circular_dependencies(graph)
        if isinstance(cycle_result, Failure):
            return Failure(f"Circular dependencies detected: {cycle_result.error}")

        # Get evaluation order (topological sort)
        sort_result = dependency_tracker.topological_sort(graph)
        if isinstance(sort_result, Failure):
            return sort_result

        # Filter to only include calculated fields in the evaluation order
        calculated_field_names = set(formulas.keys())
        evaluation_order = [
            FieldDefinitionId(field_name)
            for field_name in sort_result.value
            if field_name in calculated_field_names
        ]

        return Success(evaluation_order)

    def _extract_field_references(self, ast_node: Any) -> set[str]:
        """Extract field references from AST node.

        Args:
            ast_node: AST node to extract references from

        Returns:
            Set of field names referenced in the AST
        """
        from doc_helper.domain.formula.ast_nodes import (
            BinaryOp,
            FieldReference,
            FunctionCall,
            Literal,
            UnaryOp,
        )

        if isinstance(ast_node, FieldReference):
            return {ast_node.field_name}

        if isinstance(ast_node, BinaryOp):
            left_refs = self._extract_field_references(ast_node.left)
            right_refs = self._extract_field_references(ast_node.right)
            return left_refs | right_refs

        if isinstance(ast_node, UnaryOp):
            return self._extract_field_references(ast_node.operand)

        if isinstance(ast_node, FunctionCall):
            refs = set()
            for arg in ast_node.arguments:
                refs |= self._extract_field_references(arg)
            return refs

        if isinstance(ast_node, Literal):
            return set()

        return set()

"""Formula evaluator.

Evaluates AST nodes to compute formula results.
"""

from dataclasses import dataclass
from typing import Any, Callable

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.formula.ast_nodes import (
    ASTNode,
    BinaryOp,
    UnaryOp,
    Literal,
    FieldReference,
    FunctionCall,
)


@dataclass
class EvaluationContext:
    """Context for formula evaluation.

    Provides field values and functions for evaluation.
    """

    field_values: dict  # Dict[str, Any] - field name -> value
    functions: dict  # Dict[str, Callable] - function name -> callable

    def __post_init__(self) -> None:
        """Validate evaluation context."""
        if not isinstance(self.field_values, dict):
            raise TypeError("field_values must be a dict")
        if not isinstance(self.functions, dict):
            raise TypeError("functions must be a dict")

    def get_field_value(self, field_name: str) -> Any:
        """Get field value by name.

        Args:
            field_name: Field name

        Returns:
            Field value

        Raises:
            KeyError: If field not found
        """
        if field_name not in self.field_values:
            raise KeyError(f"Field '{field_name}' not found in context")
        return self.field_values[field_name]

    def has_field(self, field_name: str) -> bool:
        """Check if field exists in context.

        Args:
            field_name: Field name

        Returns:
            True if field exists
        """
        return field_name in self.field_values

    def get_function(self, function_name: str) -> Callable:
        """Get function by name.

        Args:
            function_name: Function name

        Returns:
            Callable function

        Raises:
            KeyError: If function not found
        """
        if function_name not in self.functions:
            raise KeyError(f"Function '{function_name}' not found in context")
        return self.functions[function_name]

    def has_function(self, function_name: str) -> bool:
        """Check if function exists in context.

        Args:
            function_name: Function name

        Returns:
            True if function exists
        """
        return function_name in self.functions


class FormulaEvaluator:
    """Evaluates formula AST to compute results.

    Supports:
    - Arithmetic: +, -, *, /, %, **
    - Comparison: ==, !=, <, <=, >, >=
    - Logical: and, or, not
    - Function calls (user-provided functions)
    - Field references

    Example:
        context = EvaluationContext(
            field_values={"field1": 10, "field2": 5},
            functions={"min": min, "max": max}
        )
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        # Returns: Success(value) or Failure(error_message)
    """

    def __init__(self, context: EvaluationContext):
        """Initialize evaluator.

        Args:
            context: Evaluation context with field values and functions
        """
        if not isinstance(context, EvaluationContext):
            raise TypeError("context must be an EvaluationContext")
        self.context = context

    def evaluate(self, node: ASTNode) -> Result[Any, str]:
        """Evaluate an AST node.

        Args:
            node: AST node to evaluate

        Returns:
            Result containing computed value or error message
        """
        try:
            value = self._evaluate_node(node)
            return Success(value)
        except Exception as e:
            return Failure(str(e))

    def _evaluate_node(self, node: ASTNode) -> Any:
        """Evaluate a node (internal).

        Args:
            node: AST node

        Returns:
            Computed value

        Raises:
            Various exceptions for evaluation errors
        """
        if isinstance(node, Literal):
            return node.value

        if isinstance(node, FieldReference):
            return self.context.get_field_value(node.field_name)

        if isinstance(node, BinaryOp):
            return self._evaluate_binary_op(node)

        if isinstance(node, UnaryOp):
            return self._evaluate_unary_op(node)

        if isinstance(node, FunctionCall):
            return self._evaluate_function_call(node)

        raise TypeError(f"Unknown AST node type: {type(node)}")

    def _evaluate_binary_op(self, node: BinaryOp) -> Any:
        """Evaluate binary operation.

        Args:
            node: BinaryOp node

        Returns:
            Result of operation
        """
        left = self._evaluate_node(node.left)
        right = self._evaluate_node(node.right)

        # Arithmetic operators
        if node.operator == "+":
            return left + right
        if node.operator == "-":
            return left - right
        if node.operator == "*":
            return left * right
        if node.operator == "/":
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left / right
        if node.operator == "%":
            if right == 0:
                raise ZeroDivisionError("Modulo by zero")
            return left % right
        if node.operator == "**":
            return left**right

        # Comparison operators
        if node.operator == "==":
            return left == right
        if node.operator == "!=":
            return left != right
        if node.operator == "<":
            return left < right
        if node.operator == "<=":
            return left <= right
        if node.operator == ">":
            return left > right
        if node.operator == ">=":
            return left >= right

        # Logical operators
        if node.operator == "and":
            return left and right
        if node.operator == "or":
            return left or right

        raise ValueError(f"Unknown binary operator: {node.operator}")

    def _evaluate_unary_op(self, node: UnaryOp) -> Any:
        """Evaluate unary operation.

        Args:
            node: UnaryOp node

        Returns:
            Result of operation
        """
        operand = self._evaluate_node(node.operand)

        if node.operator == "-":
            return -operand
        if node.operator == "+":
            return +operand
        if node.operator == "not":
            return not operand

        raise ValueError(f"Unknown unary operator: {node.operator}")

    def _evaluate_function_call(self, node: FunctionCall) -> Any:
        """Evaluate function call.

        Args:
            node: FunctionCall node

        Returns:
            Result of function call
        """
        # Get function
        func = self.context.get_function(node.function_name)

        # Evaluate arguments
        arg_values = [self._evaluate_node(arg) for arg in node.arguments]

        # Call function
        try:
            return func(*arg_values)
        except Exception as e:
            raise RuntimeError(
                f"Error calling function '{node.function_name}': {e}"
            ) from e

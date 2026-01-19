"""Abstract Syntax Tree (AST) nodes for formula expressions.

AST represents the parsed structure of a formula.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class ASTNode(ABC):
    """Base class for all AST nodes."""

    @abstractmethod
    def __repr__(self) -> str:
        """String representation for debugging."""
        pass


@dataclass(frozen=True)
class Literal(ASTNode):
    """Literal value (number, string, boolean, null).

    Example:
        Literal(42)
        Literal(3.14)
        Literal("hello")
        Literal(True)
        Literal(None)
    """

    value: Any

    def __repr__(self) -> str:
        """String representation."""
        return f"Literal({self.value!r})"


@dataclass(frozen=True)
class FieldReference(ASTNode):
    """Reference to a field by name.

    Example:
        FieldReference("field1")
        FieldReference("total_amount")
    """

    field_name: str

    def __post_init__(self) -> None:
        """Validate field reference."""
        if not isinstance(self.field_name, str):
            raise TypeError("field_name must be a string")
        if not self.field_name:
            raise ValueError("field_name cannot be empty")

    def __repr__(self) -> str:
        """String representation."""
        return f"FieldReference({self.field_name!r})"


@dataclass(frozen=True)
class BinaryOp(ASTNode):
    """Binary operation (left operator right).

    Example:
        BinaryOp('+', Literal(1), Literal(2))  # 1 + 2
        BinaryOp('*', FieldReference('a'), Literal(10))  # a * 10
    """

    operator: str
    left: ASTNode
    right: ASTNode

    VALID_OPERATORS = {
        "+",
        "-",
        "*",
        "/",
        "%",
        "**",
        "==",
        "!=",
        "<",
        "<=",
        ">",
        ">=",
        "and",
        "or",
    }

    def __post_init__(self) -> None:
        """Validate binary operation."""
        if not isinstance(self.operator, str):
            raise TypeError("operator must be a string")
        if self.operator not in self.VALID_OPERATORS:
            raise ValueError(f"Invalid operator: {self.operator}")
        if not isinstance(self.left, ASTNode):
            raise TypeError("left operand must be an ASTNode")
        if not isinstance(self.right, ASTNode):
            raise TypeError("right operand must be an ASTNode")

    def __repr__(self) -> str:
        """String representation."""
        return f"BinaryOp({self.operator!r}, {self.left!r}, {self.right!r})"


@dataclass(frozen=True)
class UnaryOp(ASTNode):
    """Unary operation (operator operand).

    Example:
        UnaryOp('-', Literal(5))  # -5
        UnaryOp('not', FieldReference('active'))  # not active
    """

    operator: str
    operand: ASTNode

    VALID_OPERATORS = {"-", "+", "not"}

    def __post_init__(self) -> None:
        """Validate unary operation."""
        if not isinstance(self.operator, str):
            raise TypeError("operator must be a string")
        if self.operator not in self.VALID_OPERATORS:
            raise ValueError(f"Invalid unary operator: {self.operator}")
        if not isinstance(self.operand, ASTNode):
            raise TypeError("operand must be an ASTNode")

    def __repr__(self) -> str:
        """String representation."""
        return f"UnaryOp({self.operator!r}, {self.operand!r})"


@dataclass(frozen=True)
class FunctionCall(ASTNode):
    """Function call with arguments.

    Example:
        FunctionCall('min', [Literal(5), Literal(10)])  # min(5, 10)
        FunctionCall('if', [condition, true_val, false_val])  # if(condition, true_val, false_val)
    """

    function_name: str
    arguments: tuple  # Tuple of ASTNode

    def __post_init__(self) -> None:
        """Validate function call."""
        if not isinstance(self.function_name, str):
            raise TypeError("function_name must be a string")
        if not self.function_name:
            raise ValueError("function_name cannot be empty")
        if not isinstance(self.arguments, tuple):
            raise TypeError("arguments must be a tuple")
        for arg in self.arguments:
            if not isinstance(arg, ASTNode):
                raise TypeError("All arguments must be ASTNode instances")

    def __repr__(self) -> str:
        """String representation."""
        args_repr = ", ".join(repr(arg) for arg in self.arguments)
        return f"FunctionCall({self.function_name!r}, [{args_repr}])"

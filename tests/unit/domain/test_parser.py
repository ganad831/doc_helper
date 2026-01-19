"""Tests for formula parser."""

import pytest

from doc_helper.domain.formula.ast_nodes import (
    Literal,
    FieldReference,
    BinaryOp,
    UnaryOp,
    FunctionCall,
)
from doc_helper.domain.formula.parser import FormulaParser


class TestFormulaParser:
    """Tests for FormulaParser."""

    def test_parse_literal_number(self) -> None:
        """Parser should parse number literals."""
        parser = FormulaParser("42")
        ast = parser.parse()
        assert isinstance(ast, Literal)
        assert ast.value == 42

    def test_parse_literal_float(self) -> None:
        """Parser should parse float literals."""
        parser = FormulaParser("3.14")
        ast = parser.parse()
        assert isinstance(ast, Literal)
        assert ast.value == 3.14

    def test_parse_literal_string(self) -> None:
        """Parser should parse string literals."""
        parser = FormulaParser('"hello"')
        ast = parser.parse()
        assert isinstance(ast, Literal)
        assert ast.value == "hello"

    def test_parse_literal_true(self) -> None:
        """Parser should parse true literal."""
        parser = FormulaParser("true")
        ast = parser.parse()
        assert isinstance(ast, Literal)
        assert ast.value is True

    def test_parse_literal_false(self) -> None:
        """Parser should parse false literal."""
        parser = FormulaParser("false")
        ast = parser.parse()
        assert isinstance(ast, Literal)
        assert ast.value is False

    def test_parse_literal_null(self) -> None:
        """Parser should parse null literal."""
        parser = FormulaParser("null")
        ast = parser.parse()
        assert isinstance(ast, Literal)
        assert ast.value is None

    def test_parse_field_reference(self) -> None:
        """Parser should parse field references."""
        parser = FormulaParser("field_name")
        ast = parser.parse()
        assert isinstance(ast, FieldReference)
        assert ast.field_name == "field_name"

    def test_parse_addition(self) -> None:
        """Parser should parse addition."""
        parser = FormulaParser("1 + 2")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "+"
        assert isinstance(ast.left, Literal)
        assert ast.left.value == 1
        assert isinstance(ast.right, Literal)
        assert ast.right.value == 2

    def test_parse_subtraction(self) -> None:
        """Parser should parse subtraction."""
        parser = FormulaParser("10 - 5")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "-"

    def test_parse_multiplication(self) -> None:
        """Parser should parse multiplication."""
        parser = FormulaParser("3 * 4")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "*"

    def test_parse_division(self) -> None:
        """Parser should parse division."""
        parser = FormulaParser("10 / 2")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "/"

    def test_parse_modulo(self) -> None:
        """Parser should parse modulo."""
        parser = FormulaParser("10 % 3")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "%"

    def test_parse_power(self) -> None:
        """Parser should parse power."""
        parser = FormulaParser("2 ** 3")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "**"

    def test_parse_comparison_equal(self) -> None:
        """Parser should parse == comparison."""
        parser = FormulaParser("a == b")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "=="

    def test_parse_comparison_not_equal(self) -> None:
        """Parser should parse != comparison."""
        parser = FormulaParser("a != b")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "!="

    def test_parse_comparison_less_than(self) -> None:
        """Parser should parse < comparison."""
        parser = FormulaParser("a < b")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "<"

    def test_parse_comparison_greater_than(self) -> None:
        """Parser should parse > comparison."""
        parser = FormulaParser("a > b")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == ">"

    def test_parse_logical_and(self) -> None:
        """Parser should parse 'and' operator."""
        parser = FormulaParser("a and b")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "and"

    def test_parse_logical_or(self) -> None:
        """Parser should parse 'or' operator."""
        parser = FormulaParser("a or b")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "or"

    def test_parse_unary_minus(self) -> None:
        """Parser should parse unary minus."""
        parser = FormulaParser("-5")
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "-"
        assert isinstance(ast.operand, Literal)
        assert ast.operand.value == 5

    def test_parse_unary_plus(self) -> None:
        """Parser should parse unary plus."""
        parser = FormulaParser("+5")
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "+"

    def test_parse_not(self) -> None:
        """Parser should parse 'not' operator."""
        parser = FormulaParser("not active")
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "not"
        assert isinstance(ast.operand, FieldReference)

    def test_parse_parentheses(self) -> None:
        """Parser should handle parentheses."""
        parser = FormulaParser("(1 + 2)")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "+"

    def test_parse_operator_precedence(self) -> None:
        """Parser should respect operator precedence."""
        # 1 + 2 * 3 should be 1 + (2 * 3)
        parser = FormulaParser("1 + 2 * 3")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "+"
        assert isinstance(ast.left, Literal)
        assert ast.left.value == 1
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "*"

    def test_parse_parentheses_override_precedence(self) -> None:
        """Parser should allow parentheses to override precedence."""
        # (1 + 2) * 3 should be (1 + 2) * 3
        parser = FormulaParser("(1 + 2) * 3")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "*"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "+"

    def test_parse_function_call_no_args(self) -> None:
        """Parser should parse function calls with no arguments."""
        parser = FormulaParser("now()")
        ast = parser.parse()
        assert isinstance(ast, FunctionCall)
        assert ast.function_name == "now"
        assert len(ast.arguments) == 0

    def test_parse_function_call_one_arg(self) -> None:
        """Parser should parse function calls with one argument."""
        parser = FormulaParser("abs(-5)")
        ast = parser.parse()
        assert isinstance(ast, FunctionCall)
        assert ast.function_name == "abs"
        assert len(ast.arguments) == 1

    def test_parse_function_call_multiple_args(self) -> None:
        """Parser should parse function calls with multiple arguments."""
        parser = FormulaParser("min(a, b, c)")
        ast = parser.parse()
        assert isinstance(ast, FunctionCall)
        assert ast.function_name == "min"
        assert len(ast.arguments) == 3

    def test_parse_nested_function_calls(self) -> None:
        """Parser should parse nested function calls."""
        parser = FormulaParser("max(min(a, b), c)")
        ast = parser.parse()
        assert isinstance(ast, FunctionCall)
        assert ast.function_name == "max"
        assert isinstance(ast.arguments[0], FunctionCall)
        assert ast.arguments[0].function_name == "min"

    def test_parse_complex_expression(self) -> None:
        """Parser should parse complex expressions."""
        parser = FormulaParser("field1 + field2 * 2 - 10 / 5")
        ast = parser.parse()
        # Should be: (field1 + (field2 * 2)) - (10 / 5)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "-"

    def test_parse_empty_formula_raises(self) -> None:
        """Parser should reject empty formulas."""
        parser = FormulaParser("")
        with pytest.raises(ValueError, match="Empty formula"):
            parser.parse()

    def test_parse_unexpected_token_raises(self) -> None:
        """Parser should reject unexpected tokens."""
        parser = FormulaParser("1 2 3")  # Numbers without operators
        with pytest.raises(ValueError, match="Unexpected token"):
            parser.parse()

    def test_parse_missing_closing_paren_raises(self) -> None:
        """Parser should reject missing closing parenthesis."""
        parser = FormulaParser("(1 + 2")
        with pytest.raises(ValueError, match="Expected RPAREN"):
            parser.parse()

    def test_parse_power_right_associative(self) -> None:
        """Parser should treat power as right-associative."""
        # 2 ** 3 ** 2 should be 2 ** (3 ** 2) = 2 ** 9 = 512
        parser = FormulaParser("2 ** 3 ** 2")
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "**"
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "**"

"""Tests for formula evaluator."""

import pytest

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.formula.evaluator import FormulaEvaluator, EvaluationContext
from doc_helper.domain.formula.parser import FormulaParser


class TestEvaluationContext:
    """Tests for EvaluationContext."""

    def test_create_context(self) -> None:
        """EvaluationContext should be created with field values and functions."""
        context = EvaluationContext(
            field_values={"a": 10, "b": 5}, functions={"min": min, "max": max}
        )
        assert context.field_values == {"a": 10, "b": 5}
        assert context.functions == {"min": min, "max": max}

    def test_get_field_value(self) -> None:
        """EvaluationContext should return field values."""
        context = EvaluationContext(field_values={"a": 42}, functions={})
        assert context.get_field_value("a") == 42

    def test_get_field_value_not_found_raises(self) -> None:
        """EvaluationContext should raise KeyError for missing fields."""
        context = EvaluationContext(field_values={}, functions={})
        with pytest.raises(KeyError, match="Field 'unknown' not found"):
            context.get_field_value("unknown")

    def test_has_field(self) -> None:
        """EvaluationContext should check field existence."""
        context = EvaluationContext(field_values={"a": 10}, functions={})
        assert context.has_field("a")
        assert not context.has_field("b")

    def test_get_function(self) -> None:
        """EvaluationContext should return functions."""
        context = EvaluationContext(field_values={}, functions={"min": min})
        func = context.get_function("min")
        assert func is min

    def test_get_function_not_found_raises(self) -> None:
        """EvaluationContext should raise KeyError for missing functions."""
        context = EvaluationContext(field_values={}, functions={})
        with pytest.raises(KeyError, match="Function 'unknown' not found"):
            context.get_function("unknown")

    def test_has_function(self) -> None:
        """EvaluationContext should check function existence."""
        context = EvaluationContext(field_values={}, functions={"min": min})
        assert context.has_function("min")
        assert not context.has_function("max")

    def test_context_requires_dict_field_values(self) -> None:
        """EvaluationContext should require dict for field_values."""
        with pytest.raises(TypeError, match="field_values must be a dict"):
            EvaluationContext(field_values=[], functions={})  # type: ignore

    def test_context_requires_dict_functions(self) -> None:
        """EvaluationContext should require dict for functions."""
        with pytest.raises(TypeError, match="functions must be a dict"):
            EvaluationContext(field_values={}, functions=[])  # type: ignore


class TestFormulaEvaluator:
    """Tests for FormulaEvaluator."""

    def test_evaluate_literal_number(self) -> None:
        """Evaluator should evaluate number literals."""
        parser = FormulaParser("42")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 42

    def test_evaluate_literal_string(self) -> None:
        """Evaluator should evaluate string literals."""
        parser = FormulaParser('"hello"')
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == "hello"

    def test_evaluate_literal_boolean(self) -> None:
        """Evaluator should evaluate boolean literals."""
        parser = FormulaParser("true")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value is True

    def test_evaluate_field_reference(self) -> None:
        """Evaluator should resolve field references."""
        parser = FormulaParser("field1")
        ast = parser.parse()
        context = EvaluationContext(field_values={"field1": 100}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 100

    def test_evaluate_addition(self) -> None:
        """Evaluator should evaluate addition."""
        parser = FormulaParser("10 + 5")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 15

    def test_evaluate_subtraction(self) -> None:
        """Evaluator should evaluate subtraction."""
        parser = FormulaParser("10 - 3")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 7

    def test_evaluate_multiplication(self) -> None:
        """Evaluator should evaluate multiplication."""
        parser = FormulaParser("6 * 7")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 42

    def test_evaluate_division(self) -> None:
        """Evaluator should evaluate division."""
        parser = FormulaParser("10 / 2")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 5.0

    def test_evaluate_modulo(self) -> None:
        """Evaluator should evaluate modulo."""
        parser = FormulaParser("10 % 3")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 1

    def test_evaluate_power(self) -> None:
        """Evaluator should evaluate power."""
        parser = FormulaParser("2 ** 3")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 8

    def test_evaluate_comparison_equal(self) -> None:
        """Evaluator should evaluate == comparison."""
        parser = FormulaParser("5 == 5")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value is True

    def test_evaluate_comparison_not_equal(self) -> None:
        """Evaluator should evaluate != comparison."""
        parser = FormulaParser("5 != 3")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value is True

    def test_evaluate_comparison_less_than(self) -> None:
        """Evaluator should evaluate < comparison."""
        parser = FormulaParser("3 < 5")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value is True

    def test_evaluate_comparison_greater_than(self) -> None:
        """Evaluator should evaluate > comparison."""
        parser = FormulaParser("5 > 3")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value is True

    def test_evaluate_logical_and(self) -> None:
        """Evaluator should evaluate 'and' operator."""
        parser = FormulaParser("true and false")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value is False

    def test_evaluate_logical_or(self) -> None:
        """Evaluator should evaluate 'or' operator."""
        parser = FormulaParser("true or false")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value is True

    def test_evaluate_unary_minus(self) -> None:
        """Evaluator should evaluate unary minus."""
        parser = FormulaParser("-5")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == -5

    def test_evaluate_not(self) -> None:
        """Evaluator should evaluate 'not' operator."""
        parser = FormulaParser("not true")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value is False

    def test_evaluate_complex_expression(self) -> None:
        """Evaluator should evaluate complex expressions."""
        parser = FormulaParser("field1 + field2 * 2")
        ast = parser.parse()
        context = EvaluationContext(field_values={"field1": 10, "field2": 5}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 20  # 10 + (5 * 2)

    def test_evaluate_function_call(self) -> None:
        """Evaluator should evaluate function calls."""
        parser = FormulaParser("min(10, 5)")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={"min": min})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 5

    def test_evaluate_function_with_field_references(self) -> None:
        """Evaluator should evaluate functions with field references."""
        parser = FormulaParser("max(field1, field2)")
        ast = parser.parse()
        context = EvaluationContext(
            field_values={"field1": 10, "field2": 20}, functions={"max": max}
        )
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Success)
        assert result.value == 20

    def test_evaluate_division_by_zero_returns_failure(self) -> None:
        """Evaluator should return Failure for division by zero."""
        parser = FormulaParser("10 / 0")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Failure)
        assert "Division by zero" in result.error

    def test_evaluate_missing_field_returns_failure(self) -> None:
        """Evaluator should return Failure for missing field."""
        parser = FormulaParser("unknown_field")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Failure)
        assert "Field 'unknown_field' not found" in result.error

    def test_evaluate_missing_function_returns_failure(self) -> None:
        """Evaluator should return Failure for missing function."""
        parser = FormulaParser("unknown()")
        ast = parser.parse()
        context = EvaluationContext(field_values={}, functions={})
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)
        assert isinstance(result, Failure)
        assert "Function 'unknown' not found" in result.error

    def test_evaluator_requires_context(self) -> None:
        """FormulaEvaluator should require EvaluationContext."""
        with pytest.raises(TypeError, match="context must be an EvaluationContext"):
            FormulaEvaluator({})  # type: ignore

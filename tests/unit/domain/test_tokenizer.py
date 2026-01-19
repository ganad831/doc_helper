"""Tests for formula tokenizer."""

import pytest

from doc_helper.domain.formula.tokenizer import FormulaTokenizer, Token, TokenType


class TestFormulaTokenizer:
    """Tests for FormulaTokenizer."""

    def test_tokenize_integer(self) -> None:
        """Tokenizer should tokenize integers."""
        tokenizer = FormulaTokenizer("42")
        tokens = tokenizer.tokenize()
        assert len(tokens) == 2  # NUMBER + EOF
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == 42
        assert tokens[1].type == TokenType.EOF

    def test_tokenize_float(self) -> None:
        """Tokenizer should tokenize floats."""
        tokenizer = FormulaTokenizer("3.14")
        tokens = tokenizer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == 3.14

    def test_tokenize_string_double_quotes(self) -> None:
        """Tokenizer should tokenize double-quoted strings."""
        tokenizer = FormulaTokenizer('"hello world"')
        tokens = tokenizer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"

    def test_tokenize_string_single_quotes(self) -> None:
        """Tokenizer should tokenize single-quoted strings."""
        tokenizer = FormulaTokenizer("'hello'")
        tokens = tokenizer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello"

    def test_tokenize_string_with_escapes(self) -> None:
        """Tokenizer should handle escape sequences in strings."""
        tokenizer = FormulaTokenizer(r'"hello\nworld\ttab"')
        tokens = tokenizer.tokenize()
        assert tokens[0].value == "hello\nworld\ttab"

    def test_tokenize_identifier(self) -> None:
        """Tokenizer should tokenize identifiers."""
        tokenizer = FormulaTokenizer("field_name123")
        tokens = tokenizer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "field_name123"

    def test_tokenize_keywords(self) -> None:
        """Tokenizer should recognize keywords."""
        tokenizer = FormulaTokenizer("true false null and or not")
        tokens = tokenizer.tokenize()
        assert tokens[0].type == TokenType.TRUE
        assert tokens[1].type == TokenType.FALSE
        assert tokens[2].type == TokenType.NULL
        assert tokens[3].type == TokenType.AND
        assert tokens[4].type == TokenType.OR
        assert tokens[5].type == TokenType.NOT

    def test_tokenize_arithmetic_operators(self) -> None:
        """Tokenizer should tokenize arithmetic operators."""
        tokenizer = FormulaTokenizer("+ - * / % **")
        tokens = tokenizer.tokenize()
        assert tokens[0].type == TokenType.PLUS
        assert tokens[1].type == TokenType.MINUS
        assert tokens[2].type == TokenType.MULTIPLY
        assert tokens[3].type == TokenType.DIVIDE
        assert tokens[4].type == TokenType.MODULO
        assert tokens[5].type == TokenType.POWER

    def test_tokenize_comparison_operators(self) -> None:
        """Tokenizer should tokenize comparison operators."""
        tokenizer = FormulaTokenizer("== != < <= > >=")
        tokens = tokenizer.tokenize()
        assert tokens[0].type == TokenType.EQUAL
        assert tokens[1].type == TokenType.NOT_EQUAL
        assert tokens[2].type == TokenType.LESS_THAN
        assert tokens[3].type == TokenType.LESS_EQUAL
        assert tokens[4].type == TokenType.GREATER_THAN
        assert tokens[5].type == TokenType.GREATER_EQUAL

    def test_tokenize_delimiters(self) -> None:
        """Tokenizer should tokenize delimiters."""
        tokenizer = FormulaTokenizer("( ) ,")
        tokens = tokenizer.tokenize()
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.RPAREN
        assert tokens[2].type == TokenType.COMMA

    def test_tokenize_complex_expression(self) -> None:
        """Tokenizer should tokenize complex expressions."""
        tokenizer = FormulaTokenizer("field1 + field2 * 2")
        tokens = tokenizer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "field1"
        assert tokens[1].type == TokenType.PLUS
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "field2"
        assert tokens[3].type == TokenType.MULTIPLY
        assert tokens[4].type == TokenType.NUMBER
        assert tokens[4].value == 2

    def test_tokenize_function_call(self) -> None:
        """Tokenizer should tokenize function calls."""
        tokenizer = FormulaTokenizer("min(a, b)")
        tokens = tokenizer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "min"
        assert tokens[1].type == TokenType.LPAREN
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "a"
        assert tokens[3].type == TokenType.COMMA
        assert tokens[4].type == TokenType.IDENTIFIER
        assert tokens[4].value == "b"
        assert tokens[5].type == TokenType.RPAREN

    def test_tokenize_with_whitespace(self) -> None:
        """Tokenizer should skip whitespace."""
        tokenizer = FormulaTokenizer("  field1   +   field2  ")
        tokens = tokenizer.tokenize()
        assert len(tokens) == 4  # 3 tokens + EOF
        assert tokens[0].value == "field1"
        assert tokens[1].type == TokenType.PLUS
        assert tokens[2].value == "field2"

    def test_tokenize_unterminated_string_raises(self) -> None:
        """Tokenizer should reject unterminated strings."""
        tokenizer = FormulaTokenizer('"unterminated')
        with pytest.raises(ValueError, match="Unterminated string"):
            tokenizer.tokenize()

    def test_tokenize_invalid_character_raises(self) -> None:
        """Tokenizer should reject invalid characters."""
        tokenizer = FormulaTokenizer("field1 @ field2")
        with pytest.raises(ValueError, match="Unexpected character '@'"):
            tokenizer.tokenize()

    def test_tokenize_empty_string(self) -> None:
        """Tokenizer should handle empty formula."""
        tokenizer = FormulaTokenizer("")
        tokens = tokenizer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_token_position_tracking(self) -> None:
        """Tokenizer should track token positions."""
        tokenizer = FormulaTokenizer("abc + 123")
        tokens = tokenizer.tokenize()
        assert tokens[0].position == 0  # abc at position 0
        assert tokens[1].position == 4  # + at position 4
        assert tokens[2].position == 6  # 123 at position 6

    def test_tokenizer_requires_string(self) -> None:
        """Tokenizer should require string formula."""
        with pytest.raises(TypeError, match="formula must be a string"):
            FormulaTokenizer(123)  # type: ignore

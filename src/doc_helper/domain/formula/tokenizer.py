"""Formula tokenizer.

Converts formula strings into tokens for parsing.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class TokenType(str, Enum):
    """Token types for formula expressions."""

    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    TRUE = "TRUE"
    FALSE = "FALSE"
    NULL = "NULL"

    # Identifiers (field names)
    IDENTIFIER = "IDENTIFIER"

    # Operators
    PLUS = "PLUS"  # +
    MINUS = "MINUS"  # -
    MULTIPLY = "MULTIPLY"  # *
    DIVIDE = "DIVIDE"  # /
    MODULO = "MODULO"  # %
    POWER = "POWER"  # **

    # Comparison
    EQUAL = "EQUAL"  # ==
    NOT_EQUAL = "NOT_EQUAL"  # !=
    LESS_THAN = "LESS_THAN"  # <
    LESS_EQUAL = "LESS_EQUAL"  # <=
    GREATER_THAN = "GREATER_THAN"  # >
    GREATER_EQUAL = "GREATER_EQUAL"  # >=

    # Logical
    AND = "AND"  # and
    OR = "OR"  # or
    NOT = "NOT"  # not

    # Delimiters
    LPAREN = "LPAREN"  # (
    RPAREN = "RPAREN"  # )
    COMMA = "COMMA"  # ,

    # Special
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    """A token in a formula expression."""

    type: TokenType
    value: Any
    position: int

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Token({self.type.name}, {self.value!r}, pos={self.position})"


class FormulaTokenizer:
    """Tokenizes formula expressions into tokens.

    Supports:
    - Numbers (int and float)
    - Strings (single and double quoted)
    - Identifiers (field names)
    - Operators (+, -, *, /, %, **)
    - Comparison (==, !=, <, <=, >, >=)
    - Logical (and, or, not)
    - Function calls
    - Parentheses

    Example:
        tokenizer = FormulaTokenizer("field1 + field2 * 2")
        tokens = tokenizer.tokenize()
        # [Token(IDENTIFIER, 'field1', 0), Token(PLUS, '+', 7), ...]
    """

    # Keywords
    KEYWORDS = {
        "true": TokenType.TRUE,
        "false": TokenType.FALSE,
        "null": TokenType.NULL,
        "and": TokenType.AND,
        "or": TokenType.OR,
        "not": TokenType.NOT,
    }

    # Two-character operators
    TWO_CHAR_OPERATORS = {
        "**": TokenType.POWER,
        "==": TokenType.EQUAL,
        "!=": TokenType.NOT_EQUAL,
        "<=": TokenType.LESS_EQUAL,
        ">=": TokenType.GREATER_EQUAL,
    }

    # Single-character operators
    SINGLE_CHAR_OPERATORS = {
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.MULTIPLY,
        "/": TokenType.DIVIDE,
        "%": TokenType.MODULO,
        "<": TokenType.LESS_THAN,
        ">": TokenType.GREATER_THAN,
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        ",": TokenType.COMMA,
    }

    def __init__(self, formula: str):
        """Initialize tokenizer.

        Args:
            formula: Formula string to tokenize
        """
        if not isinstance(formula, str):
            raise TypeError("formula must be a string")

        self.formula = formula
        self.position = 0
        self.current_char = self.formula[0] if formula else None

    def advance(self) -> None:
        """Move to next character."""
        self.position += 1
        if self.position >= len(self.formula):
            self.current_char = None
        else:
            self.current_char = self.formula[self.position]

    def peek(self, offset: int = 1) -> str | None:
        """Look ahead at next character(s)."""
        peek_pos = self.position + offset
        if peek_pos >= len(self.formula):
            return None
        return self.formula[peek_pos]

    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def read_number(self) -> Token:
        """Read a number token (int or float)."""
        start_pos = self.position
        num_str = ""

        # Read digits before decimal point
        while self.current_char is not None and self.current_char.isdigit():
            num_str += self.current_char
            self.advance()

        # Check for decimal point
        if self.current_char == "." and self.peek() is not None and self.peek().isdigit():
            num_str += self.current_char
            self.advance()

            # Read digits after decimal point
            while self.current_char is not None and self.current_char.isdigit():
                num_str += self.current_char
                self.advance()

            return Token(TokenType.NUMBER, float(num_str), start_pos)
        else:
            return Token(TokenType.NUMBER, int(num_str), start_pos)

    def read_string(self, quote_char: str) -> Token:
        """Read a string token."""
        start_pos = self.position
        self.advance()  # Skip opening quote

        result = ""
        while self.current_char is not None and self.current_char != quote_char:
            if self.current_char == "\\":
                self.advance()
                if self.current_char is None:
                    raise ValueError(f"Unterminated string at position {start_pos}")
                # Handle escape sequences
                escape_chars = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", quote_char: quote_char}
                result += escape_chars.get(self.current_char, self.current_char)
            else:
                result += self.current_char
            self.advance()

        if self.current_char is None:
            raise ValueError(f"Unterminated string at position {start_pos}")

        self.advance()  # Skip closing quote
        return Token(TokenType.STRING, result, start_pos)

    def read_identifier(self) -> Token:
        """Read an identifier or keyword token."""
        start_pos = self.position
        result = ""

        # First character must be letter or underscore
        if not (self.current_char.isalpha() or self.current_char == "_"):
            raise ValueError(f"Invalid identifier at position {start_pos}")

        # Read alphanumeric characters and underscores
        while self.current_char is not None and (
            self.current_char.isalnum() or self.current_char == "_"
        ):
            result += self.current_char
            self.advance()

        # Check if it's a keyword
        lower_result = result.lower()
        if lower_result in self.KEYWORDS:
            return Token(self.KEYWORDS[lower_result], lower_result, start_pos)

        return Token(TokenType.IDENTIFIER, result, start_pos)

    def tokenize(self) -> list[Token]:
        """Tokenize the formula into a list of tokens.

        Returns:
            List of tokens

        Raises:
            ValueError: If formula contains invalid syntax
        """
        tokens = []

        while self.current_char is not None:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Numbers
            if self.current_char.isdigit():
                tokens.append(self.read_number())
                continue

            # Strings
            if self.current_char in ('"', "'"):
                tokens.append(self.read_string(self.current_char))
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == "_":
                tokens.append(self.read_identifier())
                continue

            # Two-character operators
            two_char = self.formula[self.position : self.position + 2]
            if two_char in self.TWO_CHAR_OPERATORS:
                tokens.append(Token(self.TWO_CHAR_OPERATORS[two_char], two_char, self.position))
                self.advance()
                self.advance()
                continue

            # Single-character operators
            if self.current_char in self.SINGLE_CHAR_OPERATORS:
                tokens.append(
                    Token(
                        self.SINGLE_CHAR_OPERATORS[self.current_char],
                        self.current_char,
                        self.position,
                    )
                )
                self.advance()
                continue

            # Unknown character
            raise ValueError(
                f"Unexpected character '{self.current_char}' at position {self.position}"
            )

        # Add EOF token
        tokens.append(Token(TokenType.EOF, None, self.position))
        return tokens

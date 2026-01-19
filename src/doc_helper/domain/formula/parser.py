"""Formula parser.

Parses tokens into an Abstract Syntax Tree (AST).
Uses recursive descent parsing with operator precedence.
"""

from doc_helper.domain.formula.ast_nodes import (
    ASTNode,
    BinaryOp,
    UnaryOp,
    Literal,
    FieldReference,
    FunctionCall,
)
from doc_helper.domain.formula.tokenizer import Token, TokenType, FormulaTokenizer


class FormulaParser:
    """Parses formula tokens into an AST.

    Operator precedence (lowest to highest):
    1. or
    2. and
    3. not
    4. ==, !=, <, <=, >, >=
    5. +, -
    6. *, /, %
    7. **
    8. unary -, +
    9. function calls, field references, literals, parentheses

    Example:
        parser = FormulaParser("field1 + field2 * 2")
        ast = parser.parse()
        # Returns: BinaryOp('+', FieldReference('field1'),
        #                        BinaryOp('*', FieldReference('field2'), Literal(2)))
    """

    def __init__(self, formula: str):
        """Initialize parser.

        Args:
            formula: Formula string to parse
        """
        tokenizer = FormulaTokenizer(formula)
        self.tokens = tokenizer.tokenize()
        self.position = 0
        self.current_token = self.tokens[0] if self.tokens else None

    def advance(self) -> None:
        """Move to next token."""
        self.position += 1
        if self.position >= len(self.tokens):
            self.current_token = None
        else:
            self.current_token = self.tokens[self.position]

    def expect(self, token_type: TokenType) -> Token:
        """Expect current token to be of given type.

        Args:
            token_type: Expected token type

        Returns:
            Current token

        Raises:
            ValueError: If current token is not of expected type
        """
        if self.current_token is None:
            raise ValueError(f"Expected {token_type.name}, got EOF")
        if self.current_token.type != token_type:
            raise ValueError(
                f"Expected {token_type.name}, got {self.current_token.type.name} "
                f"at position {self.current_token.position}"
            )
        token = self.current_token
        self.advance()
        return token

    def parse(self) -> ASTNode:
        """Parse the formula into an AST.

        Returns:
            Root AST node

        Raises:
            ValueError: If formula contains syntax errors
        """
        if not self.tokens or self.current_token.type == TokenType.EOF:
            raise ValueError("Empty formula")

        ast = self.parse_or()

        # Ensure we've consumed all tokens except EOF
        if self.current_token.type != TokenType.EOF:
            raise ValueError(
                f"Unexpected token {self.current_token.type.name} "
                f"at position {self.current_token.position}"
            )

        return ast

    def parse_or(self) -> ASTNode:
        """Parse OR expression (lowest precedence)."""
        left = self.parse_and()

        while self.current_token and self.current_token.type == TokenType.OR:
            self.advance()
            right = self.parse_and()
            left = BinaryOp("or", left, right)

        return left

    def parse_and(self) -> ASTNode:
        """Parse AND expression."""
        left = self.parse_not()

        while self.current_token and self.current_token.type == TokenType.AND:
            self.advance()
            right = self.parse_not()
            left = BinaryOp("and", left, right)

        return left

    def parse_not(self) -> ASTNode:
        """Parse NOT expression."""
        if self.current_token and self.current_token.type == TokenType.NOT:
            self.advance()
            operand = self.parse_not()  # NOT is right-associative
            return UnaryOp("not", operand)

        return self.parse_comparison()

    def parse_comparison(self) -> ASTNode:
        """Parse comparison expression (==, !=, <, <=, >, >=)."""
        left = self.parse_addition()

        comparison_ops = {
            TokenType.EQUAL: "==",
            TokenType.NOT_EQUAL: "!=",
            TokenType.LESS_THAN: "<",
            TokenType.LESS_EQUAL: "<=",
            TokenType.GREATER_THAN: ">",
            TokenType.GREATER_EQUAL: ">=",
        }

        while self.current_token and self.current_token.type in comparison_ops:
            op_token = self.current_token
            operator = comparison_ops[op_token.type]
            self.advance()
            right = self.parse_addition()
            left = BinaryOp(operator, left, right)

        return left

    def parse_addition(self) -> ASTNode:
        """Parse addition/subtraction expression."""
        left = self.parse_multiplication()

        while self.current_token and self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.current_token
            operator = "+" if op_token.type == TokenType.PLUS else "-"
            self.advance()
            right = self.parse_multiplication()
            left = BinaryOp(operator, left, right)

        return left

    def parse_multiplication(self) -> ASTNode:
        """Parse multiplication/division/modulo expression."""
        left = self.parse_power()

        while self.current_token and self.current_token.type in (
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
            TokenType.MODULO,
        ):
            op_token = self.current_token
            if op_token.type == TokenType.MULTIPLY:
                operator = "*"
            elif op_token.type == TokenType.DIVIDE:
                operator = "/"
            else:  # MODULO
                operator = "%"
            self.advance()
            right = self.parse_power()
            left = BinaryOp(operator, left, right)

        return left

    def parse_power(self) -> ASTNode:
        """Parse power expression (right-associative)."""
        left = self.parse_unary()

        if self.current_token and self.current_token.type == TokenType.POWER:
            self.advance()
            right = self.parse_power()  # Right-associative
            return BinaryOp("**", left, right)

        return left

    def parse_unary(self) -> ASTNode:
        """Parse unary +/- expression."""
        if self.current_token and self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.current_token
            operator = "+" if op_token.type == TokenType.PLUS else "-"
            self.advance()
            operand = self.parse_unary()  # Unary operators are right-associative
            return UnaryOp(operator, operand)

        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        """Parse primary expression (literals, identifiers, function calls, parentheses)."""
        # Numbers
        if self.current_token.type == TokenType.NUMBER:
            value = self.current_token.value
            self.advance()
            return Literal(value)

        # Strings
        if self.current_token.type == TokenType.STRING:
            value = self.current_token.value
            self.advance()
            return Literal(value)

        # Booleans
        if self.current_token.type == TokenType.TRUE:
            self.advance()
            return Literal(True)

        if self.current_token.type == TokenType.FALSE:
            self.advance()
            return Literal(False)

        # Null
        if self.current_token.type == TokenType.NULL:
            self.advance()
            return Literal(None)

        # Identifiers (field references or function calls)
        if self.current_token.type == TokenType.IDENTIFIER:
            name = self.current_token.value
            self.advance()

            # Check for function call
            if self.current_token and self.current_token.type == TokenType.LPAREN:
                return self.parse_function_call(name)

            # Field reference
            return FieldReference(name)

        # Parenthesized expression
        if self.current_token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_or()  # Parse full expression inside parens
            self.expect(TokenType.RPAREN)
            return expr

        # Unexpected token
        raise ValueError(
            f"Unexpected token {self.current_token.type.name} "
            f"at position {self.current_token.position}"
        )

    def parse_function_call(self, function_name: str) -> FunctionCall:
        """Parse function call.

        Args:
            function_name: Name of the function

        Returns:
            FunctionCall AST node
        """
        self.expect(TokenType.LPAREN)

        arguments = []

        # Empty argument list
        if self.current_token.type == TokenType.RPAREN:
            self.advance()
            return FunctionCall(function_name, tuple(arguments))

        # Parse arguments
        while True:
            arg = self.parse_or()  # Parse full expression as argument
            arguments.append(arg)

            if self.current_token.type == TokenType.COMMA:
                self.advance()
                continue
            elif self.current_token.type == TokenType.RPAREN:
                self.advance()
                break
            else:
                raise ValueError(
                    f"Expected ',' or ')' in function call, got {self.current_token.type.name} "
                    f"at position {self.current_token.position}"
                )

        return FunctionCall(function_name, tuple(arguments))

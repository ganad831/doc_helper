"""Formula domain.

Formulas are string expressions that compute field values dynamically.
Used for CALCULATED field types.
"""

from doc_helper.domain.formula.ast_nodes import (
    ASTNode,
    BinaryOp,
    UnaryOp,
    Literal,
    FieldReference,
    FunctionCall,
)
from doc_helper.domain.formula.evaluator import FormulaEvaluator, EvaluationContext
from doc_helper.domain.formula.parser import FormulaParser
from doc_helper.domain.formula.tokenizer import FormulaTokenizer, Token, TokenType
from doc_helper.domain.formula.dependency_tracker import DependencyTracker

__all__ = [
    # AST
    "ASTNode",
    "BinaryOp",
    "UnaryOp",
    "Literal",
    "FieldReference",
    "FunctionCall",
    # Tokenizer
    "FormulaTokenizer",
    "Token",
    "TokenType",
    # Parser
    "FormulaParser",
    # Evaluator
    "FormulaEvaluator",
    "EvaluationContext",
    # Dependency tracking
    "DependencyTracker",
]

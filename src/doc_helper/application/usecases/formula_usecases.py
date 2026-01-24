"""Formula Use Cases (Phase F-1: Formula Editor - Read-Only, Design-Time).

Application layer use-case class for formula validation operations.
Presentation layer MUST use this class instead of directly accessing
the domain formula parser.

PHASE F-1 CONSTRAINTS:
- Read-only with respect to schema
- Validates expressions against schema snapshot (DTOs only)
- Infers result type (BOOLEAN / NUMBER / TEXT / UNKNOWN)
- Returns FormulaValidationResultDTO
- NO formula execution
- NO schema mutation
- NO persistence

ARCHITECTURE COMPLIANCE:
- FormulaUseCases is the composition root for formula validation
- ViewModel calls ONLY use-case methods
- All domain parser access happens HERE
- Schema snapshot passed as DTOs (read-only)
- Returns DTOs to Presentation
"""

from typing import Any

from doc_helper.application.dto.formula_dto import (
    FormulaResultType,
    FormulaValidationResultDTO,
    SchemaFieldInfoDTO,
)
from doc_helper.domain.formula.ast_nodes import (
    ASTNode,
    BinaryOp,
    FieldReference,
    FunctionCall,
    Literal,
    UnaryOp,
)
from doc_helper.domain.formula.parser import FormulaParser


# Allowed functions in formulas (from plan.md)
ALLOWED_FUNCTIONS = frozenset({
    "abs",
    "min",
    "max",
    "round",
    "sum",
    "pow",
    "upper",
    "lower",
    "strip",
    "concat",
    "if_else",
    "is_empty",
    "coalesce",
})

# Function return types (for type inference)
FUNCTION_RETURN_TYPES: dict[str, FormulaResultType] = {
    "abs": FormulaResultType.NUMBER,
    "min": FormulaResultType.NUMBER,
    "max": FormulaResultType.NUMBER,
    "round": FormulaResultType.NUMBER,
    "sum": FormulaResultType.NUMBER,
    "pow": FormulaResultType.NUMBER,
    "upper": FormulaResultType.TEXT,
    "lower": FormulaResultType.TEXT,
    "strip": FormulaResultType.TEXT,
    "concat": FormulaResultType.TEXT,
    "if_else": FormulaResultType.UNKNOWN,  # Depends on arguments
    "is_empty": FormulaResultType.BOOLEAN,
    "coalesce": FormulaResultType.UNKNOWN,  # Depends on arguments
}

# Field type to result type mapping
FIELD_TYPE_TO_RESULT_TYPE: dict[str, FormulaResultType] = {
    "TEXT": FormulaResultType.TEXT,
    "TEXTAREA": FormulaResultType.TEXT,
    "NUMBER": FormulaResultType.NUMBER,
    "DATE": FormulaResultType.TEXT,  # Dates as text for formulas
    "DROPDOWN": FormulaResultType.TEXT,
    "CHECKBOX": FormulaResultType.BOOLEAN,
    "RADIO": FormulaResultType.TEXT,
    "CALCULATED": FormulaResultType.UNKNOWN,  # Depends on formula
    "LOOKUP": FormulaResultType.UNKNOWN,
    "FILE": FormulaResultType.TEXT,
    "IMAGE": FormulaResultType.TEXT,
    "TABLE": FormulaResultType.UNKNOWN,
}


class FormulaUseCases:
    """Use-case class for formula validation operations.

    Provides formula parsing, validation, and type inference
    for the Formula Editor UI (Phase F-1).

    PHASE F-1 SCOPE:
    - parse_formula(): Parse formula text into AST (internal)
    - validate_formula(): Validate formula against schema snapshot
    - infer_result_type(): Infer result type from AST

    FORBIDDEN OPERATIONS:
    - Schema mutation
    - Formula execution
    - Persistence
    - Domain object exposure to Presentation

    Usage in ViewModel:
        usecases = FormulaUseCases()
        schema_fields = [...list of SchemaFieldInfoDTO...]
        result = usecases.validate_formula(formula_text, schema_fields)
        # result is FormulaValidationResultDTO
    """

    def validate_formula(
        self,
        formula_text: str,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> FormulaValidationResultDTO:
        """Validate a formula expression against the schema.

        Performs:
        1. Syntax validation (parsing)
        2. Reference validation (field existence)
        3. Function validation (allowed functions)
        4. Type inference

        Args:
            formula_text: Formula expression to validate
            schema_fields: Read-only schema field snapshot (DTOs)

        Returns:
            FormulaValidationResultDTO with validation results

        Phase F-1 Compliance:
        - Read-only schema access (DTOs)
        - No schema mutation
        - No formula execution
        - Returns DTO only
        """
        errors: list[str] = []
        warnings: list[str] = []
        field_references: set[str] = set()

        # Handle empty formula
        if not formula_text or not formula_text.strip():
            return FormulaValidationResultDTO(
                is_valid=False,
                errors=("Formula cannot be empty",),
                warnings=(),
                inferred_type=FormulaResultType.UNKNOWN.value,
                field_references=(),
            )

        # Step 1: Parse formula (syntax validation)
        try:
            parser = FormulaParser(formula_text)
            ast = parser.parse()
        except ValueError as e:
            return FormulaValidationResultDTO(
                is_valid=False,
                errors=(f"Syntax error: {str(e)}",),
                warnings=(),
                inferred_type=FormulaResultType.UNKNOWN.value,
                field_references=(),
            )
        except Exception as e:
            return FormulaValidationResultDTO(
                is_valid=False,
                errors=(f"Parse error: {str(e)}",),
                warnings=(),
                inferred_type=FormulaResultType.UNKNOWN.value,
                field_references=(),
            )

        # Build field lookup dictionary
        field_lookup = {f.field_id: f for f in schema_fields}

        # Step 2: Extract and validate field references
        field_references = self._extract_field_references(ast)
        for field_ref in field_references:
            if field_ref not in field_lookup:
                errors.append(f"Unknown field: '{field_ref}'")

        # Step 3: Validate function calls
        function_errors = self._validate_functions(ast)
        errors.extend(function_errors)

        # Step 4: Infer result type
        inferred_type = self._infer_type(ast, field_lookup)

        # Step 5: Add warnings for potential issues
        type_warnings = self._check_type_compatibility(ast, field_lookup)
        warnings.extend(type_warnings)

        return FormulaValidationResultDTO(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
            inferred_type=inferred_type.value,
            field_references=tuple(sorted(field_references)),
        )

    def parse_formula(
        self,
        formula_text: str,
    ) -> tuple[bool, str | None, tuple[str, ...]]:
        """Parse formula text (syntax validation only).

        Args:
            formula_text: Formula expression to parse

        Returns:
            Tuple of (is_valid, error_message, field_references)

        Note:
            This is a simpler method for quick syntax checks.
            Use validate_formula() for full validation against schema.
        """
        if not formula_text or not formula_text.strip():
            return (False, "Formula cannot be empty", ())

        try:
            parser = FormulaParser(formula_text)
            ast = parser.parse()
            field_refs = self._extract_field_references(ast)
            return (True, None, tuple(sorted(field_refs)))
        except ValueError as e:
            return (False, f"Syntax error: {str(e)}", ())
        except Exception as e:
            return (False, f"Parse error: {str(e)}", ())

    def infer_result_type(
        self,
        formula_text: str,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> FormulaResultType:
        """Infer the result type of a formula expression.

        Args:
            formula_text: Formula expression
            schema_fields: Read-only schema field snapshot

        Returns:
            Inferred FormulaResultType
        """
        if not formula_text or not formula_text.strip():
            return FormulaResultType.UNKNOWN

        try:
            parser = FormulaParser(formula_text)
            ast = parser.parse()
            field_lookup = {f.field_id: f for f in schema_fields}
            return self._infer_type(ast, field_lookup)
        except Exception:
            return FormulaResultType.UNKNOWN

    def get_available_functions(self) -> tuple[str, ...]:
        """Get list of available formula functions.

        Returns:
            Tuple of allowed function names
        """
        return tuple(sorted(ALLOWED_FUNCTIONS))

    # =========================================================================
    # Internal Methods (Domain Logic Coordination)
    # =========================================================================

    def _extract_field_references(self, node: ASTNode) -> set[str]:
        """Extract all field references from AST.

        Args:
            node: AST root node

        Returns:
            Set of field names referenced in formula
        """
        if isinstance(node, FieldReference):
            return {node.field_name}

        if isinstance(node, BinaryOp):
            left = self._extract_field_references(node.left)
            right = self._extract_field_references(node.right)
            return left | right

        if isinstance(node, UnaryOp):
            return self._extract_field_references(node.operand)

        if isinstance(node, FunctionCall):
            refs: set[str] = set()
            for arg in node.arguments:
                refs |= self._extract_field_references(arg)
            return refs

        if isinstance(node, Literal):
            return set()

        return set()

    def _validate_functions(self, node: ASTNode) -> list[str]:
        """Validate function calls in AST.

        Args:
            node: AST root node

        Returns:
            List of error messages for invalid functions
        """
        errors: list[str] = []

        if isinstance(node, FunctionCall):
            if node.function_name not in ALLOWED_FUNCTIONS:
                errors.append(
                    f"Unknown function: '{node.function_name}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_FUNCTIONS))}"
                )
            # Validate arguments recursively
            for arg in node.arguments:
                errors.extend(self._validate_functions(arg))

        elif isinstance(node, BinaryOp):
            errors.extend(self._validate_functions(node.left))
            errors.extend(self._validate_functions(node.right))

        elif isinstance(node, UnaryOp):
            errors.extend(self._validate_functions(node.operand))

        return errors

    def _infer_type(
        self,
        node: ASTNode,
        field_lookup: dict[str, SchemaFieldInfoDTO],
    ) -> FormulaResultType:
        """Infer result type from AST node.

        Args:
            node: AST node
            field_lookup: Field ID -> SchemaFieldInfoDTO mapping

        Returns:
            Inferred FormulaResultType
        """
        if isinstance(node, Literal):
            return self._infer_literal_type(node.value)

        if isinstance(node, FieldReference):
            if node.field_name in field_lookup:
                field_info = field_lookup[node.field_name]
                return FIELD_TYPE_TO_RESULT_TYPE.get(
                    field_info.field_type, FormulaResultType.UNKNOWN
                )
            return FormulaResultType.UNKNOWN

        if isinstance(node, BinaryOp):
            return self._infer_binary_op_type(node, field_lookup)

        if isinstance(node, UnaryOp):
            return self._infer_unary_op_type(node, field_lookup)

        if isinstance(node, FunctionCall):
            return FUNCTION_RETURN_TYPES.get(
                node.function_name, FormulaResultType.UNKNOWN
            )

        return FormulaResultType.UNKNOWN

    def _infer_literal_type(self, value: Any) -> FormulaResultType:
        """Infer type from literal value.

        Args:
            value: Literal value

        Returns:
            Inferred FormulaResultType
        """
        if isinstance(value, bool):
            return FormulaResultType.BOOLEAN
        if isinstance(value, (int, float)):
            return FormulaResultType.NUMBER
        if isinstance(value, str):
            return FormulaResultType.TEXT
        if value is None:
            return FormulaResultType.UNKNOWN
        return FormulaResultType.UNKNOWN

    def _infer_binary_op_type(
        self,
        node: BinaryOp,
        field_lookup: dict[str, SchemaFieldInfoDTO],
    ) -> FormulaResultType:
        """Infer type from binary operation.

        Args:
            node: BinaryOp node
            field_lookup: Field lookup dictionary

        Returns:
            Inferred FormulaResultType
        """
        # Comparison operators always return boolean
        if node.operator in ("==", "!=", "<", "<=", ">", ">="):
            return FormulaResultType.BOOLEAN

        # Logical operators always return boolean
        if node.operator in ("and", "or"):
            return FormulaResultType.BOOLEAN

        # Arithmetic operators
        if node.operator in ("+", "-", "*", "/", "%", "**"):
            left_type = self._infer_type(node.left, field_lookup)
            right_type = self._infer_type(node.right, field_lookup)

            # String concatenation with +
            if node.operator == "+":
                if left_type == FormulaResultType.TEXT or right_type == FormulaResultType.TEXT:
                    return FormulaResultType.TEXT

            # Default to number for arithmetic
            return FormulaResultType.NUMBER

        return FormulaResultType.UNKNOWN

    def _infer_unary_op_type(
        self,
        node: UnaryOp,
        field_lookup: dict[str, SchemaFieldInfoDTO],
    ) -> FormulaResultType:
        """Infer type from unary operation.

        Args:
            node: UnaryOp node
            field_lookup: Field lookup dictionary

        Returns:
            Inferred FormulaResultType
        """
        if node.operator == "not":
            return FormulaResultType.BOOLEAN

        if node.operator in ("+", "-"):
            return FormulaResultType.NUMBER

        return FormulaResultType.UNKNOWN

    def _check_type_compatibility(
        self,
        node: ASTNode,
        field_lookup: dict[str, SchemaFieldInfoDTO],
    ) -> list[str]:
        """Check for potential type compatibility issues.

        Args:
            node: AST root node
            field_lookup: Field lookup dictionary

        Returns:
            List of warning messages
        """
        warnings: list[str] = []

        if isinstance(node, BinaryOp):
            # Check arithmetic on non-numeric types
            if node.operator in ("-", "*", "/", "%", "**"):
                left_type = self._infer_type(node.left, field_lookup)
                right_type = self._infer_type(node.right, field_lookup)

                if left_type == FormulaResultType.TEXT:
                    warnings.append(
                        f"Arithmetic operation '{node.operator}' on TEXT type may fail"
                    )
                if right_type == FormulaResultType.TEXT:
                    warnings.append(
                        f"Arithmetic operation '{node.operator}' on TEXT type may fail"
                    )

            # Recurse into children
            warnings.extend(self._check_type_compatibility(node.left, field_lookup))
            warnings.extend(self._check_type_compatibility(node.right, field_lookup))

        elif isinstance(node, UnaryOp):
            if node.operator in ("+", "-"):
                operand_type = self._infer_type(node.operand, field_lookup)
                if operand_type == FormulaResultType.TEXT:
                    warnings.append(
                        f"Unary '{node.operator}' on TEXT type may fail"
                    )
            warnings.extend(self._check_type_compatibility(node.operand, field_lookup))

        elif isinstance(node, FunctionCall):
            for arg in node.arguments:
                warnings.extend(self._check_type_compatibility(arg, field_lookup))

        return warnings

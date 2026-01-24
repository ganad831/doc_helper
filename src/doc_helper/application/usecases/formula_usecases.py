"""Formula Use Cases (Phase F-1 + F-2 + F-3 + F-4).

Application layer use-case class for formula operations.
Presentation layer MUST use this class instead of directly accessing
the domain formula parser or evaluator.

PHASE F-1 CONSTRAINTS (Design-Time Validation):
- Read-only with respect to schema
- Validates expressions against schema snapshot (DTOs only)
- Infers result type (BOOLEAN / NUMBER / TEXT / UNKNOWN)
- Returns FormulaValidationResultDTO
- NO schema mutation
- NO persistence

PHASE F-2 CONSTRAINTS (Runtime Execution - ADR-040):
- Pure execution (no side effects)
- No persistence of computed values
- No schema mutation
- No dependency tracking
- Execution is pull-based, not push-based
- Returns FormulaExecutionResultDTO

PHASE F-3 CONSTRAINTS (Dependency Discovery - ADR-040):
- Analysis only (no execution)
- No persistence of dependencies
- No DAG/graph construction
- No cycle detection
- Read-only schema access
- Returns FormulaDependencyAnalysisResultDTO

PHASE F-4 CONSTRAINTS (Cycle Detection - ADR-041):
- Analysis only (no execution)
- No persistence of cycle results
- No schema mutation
- Non-blocking (informs, does not prevent)
- Deterministic: same input -> same output
- Same-entity scope only
- Returns FormulaCycleAnalysisResultDTO

ARCHITECTURE COMPLIANCE:
- FormulaUseCases is the composition root for formula operations
- ViewModel calls ONLY use-case methods
- All domain parser/evaluator access happens HERE
- Schema snapshot passed as DTOs (read-only)
- Returns DTOs to Presentation
"""

from typing import Any, Callable

from doc_helper.application.dto.formula_dto import (
    FormulaCycleAnalysisResultDTO,
    FormulaCycleDTO,
    FormulaDependencyAnalysisResultDTO,
    FormulaDependencyDTO,
    FormulaExecutionResultDTO,
    FormulaResultType,
    FormulaValidationResultDTO,
    SchemaFieldInfoDTO,
)
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.formula.ast_nodes import (
    ASTNode,
    BinaryOp,
    FieldReference,
    FunctionCall,
    Literal,
    UnaryOp,
)
from doc_helper.domain.formula.evaluator import EvaluationContext, FormulaEvaluator
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


# =========================================================================
# PHASE F-2: Built-in function implementations for formula execution
# =========================================================================


def _builtin_abs(x: Any) -> Any:
    """Absolute value."""
    if x is None:
        return None
    return abs(x)


def _builtin_min(*args: Any) -> Any:
    """Minimum of values (null-safe)."""
    non_null = [a for a in args if a is not None]
    if not non_null:
        return None
    return min(non_null)


def _builtin_max(*args: Any) -> Any:
    """Maximum of values (null-safe)."""
    non_null = [a for a in args if a is not None]
    if not non_null:
        return None
    return max(non_null)


def _builtin_round(x: Any, digits: int = 0) -> Any:
    """Round to specified digits."""
    if x is None:
        return None
    return round(x, digits)


def _builtin_sum(*args: Any) -> Any:
    """Sum of values (null-safe)."""
    non_null = [a for a in args if a is not None]
    if not non_null:
        return 0
    return sum(non_null)


def _builtin_pow(base: Any, exp: Any) -> Any:
    """Power function."""
    if base is None or exp is None:
        return None
    return base ** exp


def _builtin_upper(s: Any) -> Any:
    """Convert to uppercase."""
    if s is None:
        return None
    return str(s).upper()


def _builtin_lower(s: Any) -> Any:
    """Convert to lowercase."""
    if s is None:
        return None
    return str(s).lower()


def _builtin_strip(s: Any) -> Any:
    """Strip whitespace."""
    if s is None:
        return None
    return str(s).strip()


def _builtin_concat(*args: Any) -> str:
    """Concatenate values as strings."""
    return "".join(str(a) if a is not None else "" for a in args)


def _builtin_if_else(condition: Any, true_val: Any, false_val: Any) -> Any:
    """Conditional expression."""
    return true_val if condition else false_val


def _builtin_is_empty(x: Any) -> bool:
    """Check if value is empty/null."""
    if x is None:
        return True
    if isinstance(x, str) and x.strip() == "":
        return True
    return False


def _builtin_coalesce(*args: Any) -> Any:
    """Return first non-null value."""
    for a in args:
        if a is not None:
            return a
    return None


# Dictionary of built-in functions for formula execution
BUILTIN_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "abs": _builtin_abs,
    "min": _builtin_min,
    "max": _builtin_max,
    "round": _builtin_round,
    "sum": _builtin_sum,
    "pow": _builtin_pow,
    "upper": _builtin_upper,
    "lower": _builtin_lower,
    "strip": _builtin_strip,
    "concat": _builtin_concat,
    "if_else": _builtin_if_else,
    "is_empty": _builtin_is_empty,
    "coalesce": _builtin_coalesce,
}


class FormulaUseCases:
    """Use-case class for formula validation, execution, dependency discovery, and cycle detection.

    Provides formula parsing, validation, type inference (Phase F-1),
    runtime execution (Phase F-2), dependency discovery (Phase F-3),
    and cycle detection (Phase F-4).

    PHASE F-1 SCOPE (Design-Time):
    - parse_formula(): Parse formula text into AST (internal)
    - validate_formula(): Validate formula against schema snapshot
    - infer_result_type(): Infer result type from AST

    PHASE F-2 SCOPE (Runtime Execution - ADR-040):
    - execute_formula(): Execute formula with runtime field values

    PHASE F-3 SCOPE (Dependency Discovery - ADR-040):
    - analyze_dependencies(): Discover field dependencies (analysis only)

    PHASE F-4 SCOPE (Cycle Detection - ADR-041):
    - detect_cycles(): Detect circular dependencies (analysis only)

    FORBIDDEN OPERATIONS:
    - Schema mutation
    - Persistence of computed values or cycle results
    - Dependency tracking / auto-recompute
    - Domain object exposure to Presentation
    - DAG schedulers or topological sorting
    - Blocking of saves or edits

    Usage in ViewModel (Validation):
        usecases = FormulaUseCases()
        schema_fields = [...list of SchemaFieldInfoDTO...]
        result = usecases.validate_formula(formula_text, schema_fields)
        # result is FormulaValidationResultDTO

    Usage in ViewModel (Execution):
        usecases = FormulaUseCases()
        result = usecases.execute_formula(
            formula_text="value1 + value2",
            field_values={"value1": 10, "value2": 20}
        )
        # result is FormulaExecutionResultDTO
        # result.value == 30

    Usage in ViewModel (Dependency Analysis):
        usecases = FormulaUseCases()
        result = usecases.analyze_dependencies(
            formula_text="price * quantity + tax",
            schema_fields=[...list of SchemaFieldInfoDTO...]
        )
        # result is FormulaDependencyAnalysisResultDTO
        # result.dependencies == (price_dep, quantity_dep, tax_dep)

    Usage in ViewModel (Cycle Detection):
        usecases = FormulaUseCases()
        result = usecases.detect_cycles(
            formula_dependencies={
                "total": ("subtotal", "tax"),
                "subtotal": ("price", "quantity"),
            }
        )
        # result is FormulaCycleAnalysisResultDTO
        # result.has_cycles == False
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
    # PHASE F-2: Runtime Execution
    # =========================================================================

    def execute_formula(
        self,
        formula_text: str,
        field_values: dict[str, Any],
    ) -> FormulaExecutionResultDTO:
        """Execute a formula expression with runtime field values.

        PHASE F-2 (ADR-040) - Pure, deterministic execution:
        - No persistence of computed values
        - No schema mutation
        - No dependency tracking
        - No caching
        - Execution is pull-based

        Args:
            formula_text: Formula expression to execute
            field_values: Runtime field values as primitives (field_id -> value)

        Returns:
            FormulaExecutionResultDTO with:
            - success: True if execution succeeded
            - value: Computed primitive value (int, float, str, bool, None)
            - error: Error message if execution failed

        Example:
            result = usecases.execute_formula(
                formula_text="value1 + value2 * 2",
                field_values={"value1": 10, "value2": 5}
            )
            # result.success == True
            # result.value == 20

        Null Handling:
            - Arithmetic with null → null
            - is_empty(null) → True
            - coalesce(null, x) → x
        """
        # Validate inputs
        if not isinstance(formula_text, str):
            return FormulaExecutionResultDTO(
                success=False,
                value=None,
                error="formula_text must be a string",
            )

        if not isinstance(field_values, dict):
            return FormulaExecutionResultDTO(
                success=False,
                value=None,
                error="field_values must be a dictionary",
            )

        # Handle empty formula
        if not formula_text or not formula_text.strip():
            return FormulaExecutionResultDTO(
                success=False,
                value=None,
                error="Formula cannot be empty",
            )

        # Step 1: Parse formula
        try:
            parser = FormulaParser(formula_text)
            ast = parser.parse()
        except ValueError as e:
            return FormulaExecutionResultDTO(
                success=False,
                value=None,
                error=f"Syntax error: {str(e)}",
            )
        except Exception as e:
            return FormulaExecutionResultDTO(
                success=False,
                value=None,
                error=f"Parse error: {str(e)}",
            )

        # Step 2: Create evaluation context with field values and built-in functions
        context = EvaluationContext(
            field_values=field_values,
            functions=BUILTIN_FUNCTIONS,
        )

        # Step 3: Evaluate formula
        evaluator = FormulaEvaluator(context)
        result = evaluator.evaluate(ast)

        # Step 4: Convert Result to DTO
        if isinstance(result, Success):
            return FormulaExecutionResultDTO(
                success=True,
                value=result.value,
                error=None,
            )
        else:
            # result is Failure
            return FormulaExecutionResultDTO(
                success=False,
                value=None,
                error=str(result.error),
            )

    # =========================================================================
    # PHASE F-3: Dependency Discovery (Analysis-Only)
    # =========================================================================

    def analyze_dependencies(
        self,
        formula_text: str,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> FormulaDependencyAnalysisResultDTO:
        """Analyze formula dependencies (field references).

        PHASE F-3 (ADR-040) - Pure, deterministic analysis:
        - No execution
        - No persistence of dependencies
        - No DAG/graph construction
        - No cycle detection
        - Read-only schema access

        This method extracts all field references from a formula expression
        and validates them against the provided schema context.

        Args:
            formula_text: Formula expression to analyze
            schema_fields: Read-only schema field snapshot (DTOs)

        Returns:
            FormulaDependencyAnalysisResultDTO with:
            - dependencies: All discovered field dependencies
            - unknown_fields: Fields not found in schema
            - has_parse_error: Whether formula failed to parse
            - parse_error: Parse error message if any

        Example:
            result = usecases.analyze_dependencies(
                formula_text="price * quantity + tax",
                schema_fields=[price_field, quantity_field, tax_field]
            )
            # result.dependencies contains 3 FormulaDependencyDTO objects
            # result.unknown_fields == ()
            # result.has_parse_error == False

        Phase F-3 Compliance:
            - Read-only schema access (DTOs)
            - No schema mutation
            - No formula execution
            - No persistence
            - No graph construction
            - Returns DTO only
        """
        # Handle empty formula
        if not formula_text or not formula_text.strip():
            return FormulaDependencyAnalysisResultDTO(
                dependencies=(),
                unknown_fields=(),
                has_parse_error=True,
                parse_error="Formula cannot be empty",
            )

        # Step 1: Parse formula (syntax validation)
        try:
            parser = FormulaParser(formula_text)
            ast = parser.parse()
        except ValueError as e:
            return FormulaDependencyAnalysisResultDTO(
                dependencies=(),
                unknown_fields=(),
                has_parse_error=True,
                parse_error=f"Syntax error: {str(e)}",
            )
        except Exception as e:
            return FormulaDependencyAnalysisResultDTO(
                dependencies=(),
                unknown_fields=(),
                has_parse_error=True,
                parse_error=f"Parse error: {str(e)}",
            )

        # Step 2: Build field lookup dictionary
        field_lookup = {f.field_id: f for f in schema_fields}

        # Step 3: Extract field references from AST
        field_refs = self._extract_field_references(ast)

        # Step 4: Build dependency DTOs and track unknown fields
        dependencies: list[FormulaDependencyDTO] = []
        unknown_fields: list[str] = []

        for field_id in sorted(field_refs):  # Sort for deterministic order
            if field_id in field_lookup:
                field_info = field_lookup[field_id]
                dependencies.append(
                    FormulaDependencyDTO(
                        field_id=field_id,
                        is_known=True,
                        field_type=field_info.field_type,
                    )
                )
            else:
                dependencies.append(
                    FormulaDependencyDTO(
                        field_id=field_id,
                        is_known=False,
                        field_type=None,
                    )
                )
                unknown_fields.append(field_id)

        return FormulaDependencyAnalysisResultDTO(
            dependencies=tuple(dependencies),
            unknown_fields=tuple(unknown_fields),
            has_parse_error=False,
            parse_error=None,
        )

    # =========================================================================
    # PHASE F-4: Cycle Detection (Design-Time Analysis)
    # =========================================================================

    def detect_cycles(
        self,
        formula_dependencies: dict[str, tuple[str, ...]],
    ) -> FormulaCycleAnalysisResultDTO:
        """Detect circular dependencies in formula fields.

        PHASE F-4 (ADR-041) - Pure, deterministic analysis:
        - No execution
        - No persistence of cycle results
        - No schema mutation
        - Non-blocking (informs, does not prevent saves/edits)
        - Same-entity scope only

        This method analyzes formula field dependencies to detect cycles.
        A cycle exists when field A depends on field B, B depends on C,
        and C depends on A (or any similar circular chain).

        Args:
            formula_dependencies: Mapping from formula field ID to dependency field IDs.
                Key: field_id of the formula field
                Value: tuple of field IDs that this formula depends on

        Returns:
            FormulaCycleAnalysisResultDTO with:
            - has_cycles: Whether any cycle was detected
            - cycles: All detected cycles as FormulaCycleDTO
            - analyzed_field_count: Number of formula fields analyzed

        Example:
            result = usecases.detect_cycles({
                "total": ("subtotal", "tax"),
                "subtotal": ("price", "quantity"),
            })
            # result.has_cycles == False (no cycles)

            result = usecases.detect_cycles({
                "a": ("b",),
                "b": ("a",),  # Cycle: a → b → a
            })
            # result.has_cycles == True
            # result.cycles[0].cycle_path == "a → b → a"

        Phase F-4 Compliance (ADR-041):
            - Read-only analysis (no mutation)
            - No schema modification
            - No blocking behavior
            - Deterministic: same input → same output
            - Returns DTO only
        """
        # Handle empty input
        if not formula_dependencies:
            return FormulaCycleAnalysisResultDTO(
                has_cycles=False,
                cycles=(),
                analyzed_field_count=0,
            )

        # Detect all cycles using DFS
        detected_cycles = self._find_all_cycles(formula_dependencies)

        # Build cycle DTOs
        cycle_dtos: list[FormulaCycleDTO] = []
        for cycle_fields in detected_cycles:
            # Build human-readable path (A → B → C → A)
            cycle_path = " → ".join(cycle_fields) + " → " + cycle_fields[0]
            cycle_dtos.append(
                FormulaCycleDTO(
                    field_ids=tuple(cycle_fields),
                    cycle_path=cycle_path,
                    severity="ERROR",
                )
            )

        # Sort cycles for deterministic output
        cycle_dtos.sort(key=lambda c: c.cycle_path)

        return FormulaCycleAnalysisResultDTO(
            has_cycles=len(cycle_dtos) > 0,
            cycles=tuple(cycle_dtos),
            analyzed_field_count=len(formula_dependencies),
        )

    def _find_all_cycles(
        self,
        dependencies: dict[str, tuple[str, ...]],
    ) -> list[list[str]]:
        """Find all cycles in the dependency graph using DFS.

        Args:
            dependencies: Mapping from field to its dependencies

        Returns:
            List of cycles, where each cycle is a list of field IDs in order
        """
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            """DFS to find cycles."""
            if node in rec_stack:
                # Found a cycle - extract the cycle from path
                cycle_start = path.index(node)
                cycle = path[cycle_start:]
                # Normalize cycle to start with smallest field_id for determinism
                if cycle:
                    min_idx = cycle.index(min(cycle))
                    normalized = cycle[min_idx:] + cycle[:min_idx]
                    # Avoid duplicates (same cycle found from different starting points)
                    if normalized not in cycles:
                        cycles.append(normalized)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Get dependencies, filtering to only formula fields in our graph
            node_deps = dependencies.get(node, ())
            for dep in node_deps:
                # Only traverse to nodes that are formula fields (in our dependency map)
                # or to nodes that would create a back-edge to our current path
                if dep in dependencies or dep in rec_stack:
                    dfs(dep)

            path.pop()
            rec_stack.remove(node)

        # Start DFS from each formula field
        for field_id in sorted(dependencies.keys()):  # Sort for determinism
            if field_id not in visited:
                dfs(field_id)

        return cycles

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

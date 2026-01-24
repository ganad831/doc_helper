# ADR-040: Formula Semantics, Validation, Storage, and Execution Lifecycle

## Status

PROPOSED

## Context

Doc Helper supports CALCULATED field types that derive their values from formulas referencing other fields. We need to formalize:

1. What a "formula" is (pure expressions, not scripts)
2. Where formulas live (in schema vs project)
3. When formulas are validated (design-time) vs executed (runtime)
4. What references are allowed (same-entity only for v1)
5. How types are inferred and validated
6. The phased implementation approach

This ADR documents decisions made during Phase F-1 (Formula Editor) implementation and establishes rules for subsequent phases.

## Decision

### 1. Formula Category

**Formulas are pure, side-effect-free expressions.**

- No variable assignment
- No control flow (if/else/loops)
- No function definitions
- No external calls (API, file system, etc.)
- Deterministic: same inputs always produce same output

This is an expression language, not a scripting language.

### 2. Where Formulas Live

**Formulas are stored in `FieldDefinition.formula` for CALCULATED field types.**

```python
@dataclass(frozen=True)
class FieldDefinition:
    id: FieldDefinitionId
    label_key: TranslationKey
    field_type: FieldType
    constraints: tuple[Constraint, ...]
    formula: str | None = None  # Only for CALCULATED fields
```

- Formula is part of **schema definition**, not project data
- Formula text is stored, not pre-parsed AST
- All projects using the schema share the same formula definitions

### 3. Formula Lifecycle: Design-Time vs Runtime

| Phase | When | What Happens |
|-------|------|--------------|
| **Design-Time (Schema Editor)** | Editing schema | Parse, validate syntax, validate field references, infer types, report errors |
| **Runtime (Project Editing)** | Field value changes | Parse, evaluate with current field values, produce result |

**Phase F-1 (Implemented)**: Design-time validation only. No execution.

### 4. Execution Model

**Formulas use an interpreter (AST walker), not compilation or scripting engine.**

```
Formula Text → Parser → AST → [Validator | Evaluator]
                              ↓           ↓
                       Errors/Warnings  Result Value
```

- Parser produces immutable AST nodes
- Validator walks AST to check references and types (design-time)
- Evaluator walks AST to compute result (runtime, future phase)

### 5. Allowed References (v1 Scope)

**Same-Entity Only**: Formulas can only reference fields within the same entity.

```
✅ value1 + value2           # Both fields in same entity
✅ base_value * multiplier   # Both fields in same entity
❌ other_entity.some_field   # Cross-entity reference (v2+)
❌ @parent.field             # Parent entity reference (v2+)
```

This simplifies dependency resolution and avoids complex cross-entity calculations in v1.

### 6. Dependency Rules

**Circular Dependencies are FORBIDDEN.**

```
❌ A = B + 1
   B = A + 1  # Circular: A → B → A

✅ A = B + 1
   B = C + 1
   C = 10     # Linear chain: A → B → C (no cycle)
```

- Dependency graph must be a DAG (Directed Acyclic Graph)
- Parser/validator detects cycles at design-time
- Error message indicates the cycle path

### 7. Type System

**Supported Types**:

| Type | Description | Examples |
|------|-------------|----------|
| `NUMBER` | Numeric values | `10`, `3.14`, `value1 + value2` |
| `TEXT` | String values | `"hello"`, `upper(name)`, `concat(a, b)` |
| `BOOLEAN` | Boolean values | `true`, `value1 > value2`, `is_empty(field)` |
| `DATE` | Date values | `today()`, `add_days(date1, 30)` |
| `UNKNOWN` | Cannot determine | Empty formula, invalid formula |

**Type Inference Rules**:

- Arithmetic operators (`+`, `-`, `*`, `/`, `%`) → `NUMBER`
- Comparison operators (`>`, `<`, `>=`, `<=`, `==`, `!=`) → `BOOLEAN`
- Logical operators (`and`, `or`, `not`) → `BOOLEAN`
- String functions (`upper`, `lower`, `concat`, `trim`) → `TEXT`
- Math functions (`abs`, `min`, `max`, `round`, `sum`, `pow`) → `NUMBER`
- Date functions (`today`, `add_days`, `date_diff`) → `DATE` or `NUMBER`
- Conditional (`if_else`) → type of then/else branches
- Field reference → type of referenced field

**Type Errors**:

```
❌ "hello" + 5           # TEXT + NUMBER mismatch
❌ upper(10)             # NUMBER passed to TEXT function
❌ value1 > "text"       # NUMBER compared to TEXT
```

### 8. Allowed Functions (v1)

```python
ALLOWED_FUNCTIONS = {
    # Math
    "abs", "min", "max", "round", "sum", "pow", "sqrt", "floor", "ceil",
    # Text
    "upper", "lower", "trim", "concat", "length", "left", "right", "mid",
    # Logic
    "if_else", "is_empty", "coalesce",
    # Date (v1 basic)
    "today", "year", "month", "day",
}
```

Additional functions may be added in later phases.

### 9. Phased Implementation

| Phase | Name | Scope | Status |
|-------|------|-------|--------|
| **F-1** | Formula Editor (Read-Only) | Design-time validation, type inference, no execution | ✅ Complete |
| **F-2** | Formula Execution | Runtime evaluation with field values | Planned |
| **F-3** | Dependency Tracking | Auto-recompute on dependency changes | Planned |
| **F-4** | Circular Detection | DAG validation at design-time | Planned |
| **F-5** | Advanced Functions | Date arithmetic, cross-entity (v2+) | Future |

## Consequences

### Positive

1. **Clear separation**: Design-time validation vs runtime execution are distinct phases
2. **Pure expressions**: No side effects simplifies reasoning and testing
3. **Type safety**: Early detection of type mismatches in Schema Editor
4. **Predictable**: Same inputs always produce same outputs
5. **Phased delivery**: Each phase builds on previous, allows incremental delivery

### Negative

1. **Limited expressiveness**: No scripting means some complex calculations need workarounds
2. **Same-entity only**: Cross-entity formulas require v2+ platform work
3. **No control flow**: Complex conditional logic must use nested `if_else`

### Neutral

1. **AST approach**: Interpreter is simpler than compilation but may be slower for complex formulas
2. **Schema storage**: Formulas in schema (not project) means all projects share same formulas

## Implementation Notes

### F-1 Implementation (Complete)

Files created:
- `src/doc_helper/application/dto/formula_dto.py` - FormulaValidationResultDTO, SchemaFieldInfoDTO
- `src/doc_helper/application/usecases/formula_usecases.py` - FormulaUseCases
- `src/doc_helper/presentation/viewmodels/formula_editor_viewmodel.py` - FormulaEditorViewModel
- `src/doc_helper/presentation/widgets/formula_editor_widget.py` - FormulaEditorWidget

Files modified:
- `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py` - Added formula editor integration
- `src/doc_helper/presentation/views/schema_designer_view.py` - Added formula editor panel

### Architecture Compliance

- ✅ Clean Architecture: Domain parser used via Application layer (FormulaUseCases)
- ✅ DTO-only MVVM: Schema context passed as DTOs (SchemaFieldInfoDTO)
- ✅ No domain imports in Presentation layer
- ✅ Immutable DTOs (frozen dataclasses)

## Related ADRs

- ADR-002: Clean Architecture with DDD
- ADR-003: Framework-Independent Domain Layer
- ADR-005: MVVM Pattern for Presentation Layer
- ADR-020: DTO-Only MVVM

## References

- Phase F-1 Implementation: Formula Editor in Schema Designer
- Domain FormulaParser: `src/doc_helper/domain/formula/parser.py`
- Domain FormulaEvaluator: `src/doc_helper/domain/formula/evaluator.py`

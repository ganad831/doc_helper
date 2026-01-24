# ADR-050: Phase R-1 Runtime Rules Application

## Status

**Proposed**

## Context

The system currently supports design-time rule authoring and schema persistence:

- **Formula System (F-1 → F-6)**: Formula authoring, validation, dependency analysis, governance checks
- **Control Rules (F-11 → F-12)**: Inter-field dependencies (VISIBILITY, ENABLED, REQUIRED) persisted in schema
- **Output Mappings (F-12.5 → F-13)**: Field value transformations for document generation, persisted in schema
- **Schema Import/Export (SD-1, Phase 7)**: Full schema persistence and portability

All existing functionality is **design-time only**. Rules are defined, validated, and stored in the schema, but they have **no runtime effect** on form behavior or document generation.

Phase R-1 introduces the **first runtime behavior**: applying persisted rules to live project data during form interaction and document generation.

This ADR defines:
- What "runtime" means in this system
- When and how rules are evaluated at runtime
- What rules are allowed to affect
- Safety and determinism constraints
- Explicit non-goals and deferred decisions

## Decision

We will implement **pull-based, deterministic runtime rule evaluation** for Control Rules and Output Mappings.

Runtime evaluation:
- **MUST** be deterministic (same inputs → same outputs)
- **MUST** be pull-based (caller requests evaluation, no observers)
- **MUST** be read-only (no side effects on data or schema)
- **MUST** fail explicitly (no silent coercion or defaults)
- **MUST NOT** persist computed values
- **MUST NOT** trigger cascading re-evaluations automatically
- **MUST NOT** mutate schema at runtime

## Runtime Rule Semantics

### Control Rules (VISIBILITY / ENABLED / REQUIRED)

**Purpose**: Control UI field state based on other field values at runtime.

**Evaluation Trigger**: User interaction (field value change, tab navigation, record selection).

**Rule Types**:

1. **VISIBILITY**
   - Formula evaluates to boolean
   - `true` → target field visible
   - `false` → target field hidden
   - Hidden fields MUST NOT be editable
   - Hidden fields MUST be excluded from validation

2. **ENABLED**
   - Formula evaluates to boolean
   - `true` → target field enabled
   - `false` → target field disabled (read-only)
   - Disabled fields MUST NOT accept user input
   - Disabled fields MUST retain current value

3. **REQUIRED**
   - Formula evaluates to boolean
   - `true` → target field required (empty value fails validation)
   - `false` → target field optional (empty value allowed)
   - Required status affects validation only, not editability

**Evaluation Scope**:
- Control rules evaluate within a **single entity instance** (one record)
- Source field and target field MUST belong to the same entity
- Cross-entity control rules are **explicitly deferred** to Phase R-3

**Failure Handling**:
- Formula evaluation failure → rule does NOT apply (target field uses default state)
- Default state: visible, enabled, not required (unless schema default differs)
- Evaluation errors logged but do NOT block form interaction

**Chain Evaluation**:
- If Field A controls Field B, and Field B controls Field C, the chain MAY propagate
- Chain depth MUST be bounded (max depth: 10, consistent with design-time validation)
- Circular dependencies MUST be detected and blocked (no evaluation)

### Output Mappings (Formula-Driven Transformations)

**Purpose**: Derive output values from field data at document generation time.

**Evaluation Trigger**: Document generation request (explicit user action).

**Rule Types**:
- **TEXT output**: Formula result converted to string
- **NUMBER output**: Formula result must be numeric (int or float)
- **BOOLEAN output**: Formula result converted to boolean

**Evaluation Scope**:
- Output mappings evaluate within a **single entity instance** (one record)
- Formula MAY reference any field in the same entity instance
- Cross-entity references are **explicitly deferred** to Phase R-3

**Failure Handling**:
- Formula evaluation failure → output mapping FAILS
- Failed output mapping → document generation FAILS
- No silent fallback or coercion
- Error message MUST identify field and formula

**Type Coercion**:
- TEXT: All formula results converted to string representation
- NUMBER: Only numeric results allowed (int, float); strings fail
- BOOLEAN: Truthy/falsy conversion (0, empty string, None → false; all else → true)

**No Persistence**:
- Computed output values MUST NOT be saved to project database
- Output values exist only in generated document
- Re-generation MUST re-evaluate formulas (no caching across generations)

## Execution Model

### When Evaluation Happens

**Control Rules**:
- On field value change (user edit)
- On record selection (navigating to different entity instance)
- On tab navigation (switching between entity forms)
- On explicit refresh request (reload form state)

**Output Mappings**:
- On document generation request only
- NOT on field value change
- NOT on form load

### Pull-Based Evaluation (REQUIRED)

Runtime rule evaluation MUST be **pull-based**:

- Caller explicitly requests evaluation (e.g., `evaluate_control_rules(entity_id, field_id, current_values)`)
- No automatic re-evaluation on data change
- No observers, listeners, or signals
- No reactive DAG engines
- No background threads

**Rationale**: Pull-based evaluation ensures predictable timing, testability, and no hidden side effects.

### Evaluation Context

**Input**:
- Entity ID (schema reference)
- Field ID (schema reference)
- Current field values (runtime data snapshot)

**Output**:
- Control rule: Boolean result (visible/enabled/required)
- Output mapping: Typed result (string, number, boolean)
- OR evaluation error (with diagnostic message)

**Constraints**:
- Evaluation MUST be pure (same inputs → same outputs)
- Evaluation MUST NOT read from database (all data passed explicitly)
- Evaluation MUST NOT write to database
- Evaluation MUST NOT mutate input values
- Evaluation MUST NOT trigger other evaluations

## Governance & Safety

### Blocking vs Non-Blocking

**Control Rules** (Non-Blocking):
- Evaluation failure does NOT block form interaction
- Failed rule → target field uses default state
- User can continue editing other fields

**Output Mappings** (Blocking):
- Evaluation failure BLOCKS document generation
- User MUST fix formula or data before generating document
- No partial document generation

### Error Handling

**Control Rule Errors**:
- Log error with field ID, formula, and exception message
- Display warning indicator in UI (optional)
- Do NOT block user workflow

**Output Mapping Errors**:
- Display error dialog with field ID, formula, and exception message
- User MUST acknowledge error
- Cancel document generation

### Determinism

Runtime evaluation MUST be deterministic:

- No random values
- No timestamps (unless explicitly passed as input)
- No external API calls
- No file system access
- No global mutable state

**Allowed Functions** (same as design-time):
- Arithmetic: `+`, `-`, `*`, `/`, `%`, `**`
- Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Logical: `and`, `or`, `not`
- Functions: `abs()`, `min()`, `max()`, `round()`, `sum()`, `len()`, `upper()`, `lower()`, `strip()`, `concat()`, `if_else()`, `is_empty()`, `coalesce()`

**Forbidden Functions**:
- `random()`, `uuid()`, `now()`, `today()`
- `open()`, `read()`, `write()`
- `eval()`, `exec()`, `compile()`
- Any function with side effects

### Performance

**Control Rule Evaluation**:
- Evaluation MUST complete within 100ms per rule
- Timeout after 100ms → treat as evaluation failure
- Max chain depth: 10 (prevents infinite loops)

**Output Mapping Evaluation**:
- Evaluation MUST complete within 1000ms per field
- Timeout after 1000ms → fail document generation
- No caching between fields (each field evaluated independently)

## Non-Goals

Phase R-1 explicitly does NOT include:

1. **Cross-Entity Rules**: Control rules or output mappings that reference fields from different entities (deferred to Phase R-3)

2. **Auto-Recompute**: Automatic re-evaluation when dependent fields change (pull-based only)

3. **Computed Field Storage**: Persisting formula results to database (runtime values are ephemeral)

4. **Reactive DAG**: Dependency graph with automatic propagation (explicit chain evaluation only)

5. **Conditional Validation**: Dynamic validation rules based on other field values (Phase R-2)

6. **Runtime Schema Mutation**: Creating/deleting fields based on runtime data (never allowed)

7. **Background Evaluation**: Evaluating rules in worker threads or async tasks (synchronous only)

8. **Value Coercion**: Silently converting invalid types (fail explicitly)

9. **Default Fallbacks**: Using fallback values when formulas fail (fail explicitly, except control rules)

10. **Partial Evaluation**: Evaluating subset of rules (all applicable rules evaluated or none)

## Deferred Decisions

The following decisions are **explicitly deferred** to future phases:

### Phase R-2: Advanced Runtime Features
- Conditional validation rules (validation based on other field values)
- Dynamic field options (dropdown options filtered by other field values)
- Multi-step form workflows (navigation control based on data)

### Phase R-3: Cross-Entity Runtime Rules
- Control rules referencing fields from related entities
- Output mappings aggregating data from child records
- Lookup field runtime resolution (resolve foreign key to display value)

### Phase R-4: Performance Optimization
- Caching evaluated results within a session
- Incremental re-evaluation (dirty tracking)
- Batch evaluation for table fields

### Unknown / Future
- Formula debugging tools (step-through evaluation)
- Runtime formula editing (hot-reload formulas without restart)
- A/B testing formulas (evaluate multiple versions)

## Consequences

### Positive

1. **Deterministic Behavior**: Pull-based evaluation ensures predictable, testable runtime behavior.

2. **Explicit Control**: Caller controls when evaluation happens (no surprises).

3. **No Hidden Side Effects**: Evaluation is pure (read-only, no persistence).

4. **Graceful Degradation**: Control rule failures do NOT block user workflow.

5. **Type Safety**: Output mappings enforce type constraints (fail fast on mismatch).

6. **Performance Bounded**: Timeouts prevent runaway formulas from freezing UI.

7. **Schema Independence**: Runtime evaluation does NOT mutate schema (schema remains source of truth).

8. **Testability**: Pure functions with explicit inputs enable unit testing without mocking.

### Negative

1. **Manual Refresh**: User may need to manually refresh form to see control rule effects (no auto-recompute).

2. **Verbose API**: Pull-based evaluation requires explicit calls (more code in presentation layer).

3. **No Cross-Entity Rules**: Phase R-1 limited to single-entity rules (common use cases deferred).

4. **No Caching**: Re-evaluation on every call may be slower than reactive approach (deferred to Phase R-4).

### Neutral

1. **Consistency with Design-Time**: Runtime uses same formula engine, functions, and validation as design-time.

2. **Foundation for Future Phases**: Pull-based model can be optimized later (caching, incremental eval) without breaking contract.

## Future Phases (Placeholders)

### Phase R-2: Advanced Runtime Features
- Conditional validation (e.g., "if owner_type == 'company', require tax_id")
- Dynamic field options (e.g., filter states by selected country)
- Multi-step workflows (e.g., disable "Submit" until required steps complete)

### Phase R-3: Cross-Entity Runtime Rules
- Control rules referencing related entities (e.g., "if project.status == 'closed', disable all borehole fields")
- Output mappings aggregating child data (e.g., "total_depth = SUM(boreholes.depth)")
- Lookup field resolution (e.g., "owner_name = LOOKUP(owner_id, 'owners', 'name')")

### Phase R-4: Performance Optimization
- Caching evaluated results within session
- Dirty tracking for incremental re-evaluation
- Batch evaluation for table fields (evaluate all rows at once)

## Compliance Checklist

- [x] **Design-Time Untouched**: No changes to F-1 → F-13 design-time behavior
- [x] **No Schema Changes**: Schema structure (entities, fields, rules) unchanged
- [x] **No Persistence Changes**: Output mappings and control rule results NOT persisted
- [x] **No Execution Side Effects**: Evaluation is pure (read-only, no mutations)
- [x] **No Reactive Systems**: Pull-based only (no observers, listeners, signals)
- [x] **No UI Framework References**: ADR describes behavior, not PyQt6 implementation
- [x] **No Persistence Layer References**: ADR describes behavior, not SQLite queries
- [x] **Explicit Non-Goals**: Clearly deferred cross-entity rules, auto-recompute, caching
- [x] **Explicit Failure Modes**: Control rules degrade gracefully, output mappings fail fast
- [x] **Bounded Performance**: Timeouts (100ms control rules, 1000ms output mappings)
- [x] **Deterministic Semantics**: No random, no timestamps, no external calls
- [x] **Type Safety**: Output mappings enforce type constraints (TEXT/NUMBER/BOOLEAN)

---

**Decision Authority**: Architecture Team
**Approval Required**: Yes (blocking for Phase R-1 implementation)
**Implementation Phase**: R-1 (Runtime Rules Application)

# ADR-041: Formula Dependency Cycle Detection

## Status

PROPOSED

## Context

Doc Helper's formula system allows CALCULATED fields to reference other fields within the same entity. When a formula references another formula field, a dependency chain forms. If these chains form cycles (e.g., A depends on B, B depends on C, C depends on A), the formula system cannot compute values—each field would wait indefinitely for the others.

ADR-040 established that "Circular Dependencies are FORBIDDEN" and that the "dependency graph must be a DAG (Directed Acyclic Graph)." However, ADR-040 did not specify:
1. How cycles are detected
2. When detection occurs (design-time vs runtime)
3. What information is reported when a cycle is found
4. How cycle detection integrates with the existing Formula Editor UI
5. What is explicitly out of scope for cycle detection

Phase F-3 (Formula Dependency Discovery) provides the foundation: given a formula, we can extract all field references and validate them against the schema. Phase F-4 builds on this to detect when those dependencies form cycles.

This ADR defines the scope, constraints, and architectural placement of cycle detection for v1.

## Decision

### 1. Cycle Detection is Design-Time Analysis Only

Cycle detection occurs exclusively in the Schema Editor when formulas are created or modified. It is a **read-only analysis** that produces a result DTO—nothing more.

**Timing**: Cycle detection runs when:
- A formula is entered or modified in the Formula Editor
- The user validates the schema (batch validation)

**Not timing**: Cycle detection does NOT run when:
- Projects are opened
- Field values change at runtime
- Documents are generated

### 2. Cycle Detection is Analysis-Only, Not Preventive

Cycle detection **reports** cycles; it does not **prevent** them. The system produces a result indicating whether cycles exist and what fields are involved. The UI may display warnings, but:

- Saving a schema with cycles is **allowed**
- Cycle presence does not auto-block any operation
- The user decides how to respond to cycle warnings

**Rationale**: Design-time tooling should inform, not restrict. Users may be mid-edit with temporary cycles that will be resolved. Blocking saves would create a poor editing experience.

### 3. Architectural Placement

Cycle detection follows the same pattern as Phase F-1 (validation) and Phase F-3 (dependency discovery):

```
Presentation Layer (FormulaEditorViewModel)
         │
         ▼
Application Layer (FormulaUseCases.detect_cycles())
         │
         ▼
Domain Layer (FormulaParser, existing AST infrastructure)
```

**Application Layer Owns Cycle Detection Logic**:
- `FormulaUseCases.detect_cycles()` performs the analysis
- Returns `FormulaCycleAnalysisResultDTO` (immutable, frozen dataclass)
- No domain changes required—reuses existing parser and AST

**Presentation Layer Displays Results**:
- `FormulaEditorViewModel` exposes cycle information as read-only properties
- ViewModel calls use-case; does not implement detection logic
- UI binds to ViewModel properties for display

### 4. Detection Scope: Same-Entity Only

Per ADR-040, v1 formulas can only reference fields within the same entity. Therefore, cycle detection is scoped to **single-entity formula graphs**.

Detection analyzes: All CALCULATED fields within one entity and their intra-entity dependencies.

Detection does NOT analyze: Cross-entity references (v2+), control system dependencies, or runtime values.

### 5. Result DTO Structure

Cycle detection produces an immutable result DTO:

```
FormulaCycleAnalysisResultDTO
├── has_cycle: bool              # Whether any cycle was detected
├── cycles: tuple[FormulaCycleDTO, ...]   # All detected cycles
└── analyzed_field_count: int    # Number of formula fields analyzed

FormulaCycleDTO
├── field_ids: tuple[str, ...]   # Fields forming the cycle, in order
├── cycle_path: str              # Human-readable path (e.g., "A → B → C → A")
└── severity: str                # Always "ERROR" for cycles
```

**DTO Rules** (per AGENT_RULES.md Section 4):
- DTOs are frozen dataclasses
- DTOs contain no behavior (except read-only computed properties)
- DTOs use primitive types only (str, bool, int, tuple)
- No domain types cross the Application boundary

### 6. Determinism and Purity

Cycle detection is **deterministic** and **pure**:
- Same formula set always produces same result
- No side effects
- No state mutation
- No external dependencies (network, filesystem, random)
- No caching of results (each call is independent)

### 7. Severity Classification

Cycles are always classified as **ERROR severity**:
- Cyclic formulas cannot be evaluated
- This is a structural problem, not a data problem
- ERROR classification aligns with ADR-025 severity model

However, per Section 2, cycle errors are **non-blocking** for schema saves.

## Scope

### In Scope (Phase F-4)

1. **Detect cycles** within same-entity formula dependencies
2. **Report all cycles** found (not just the first)
3. **Provide cycle paths** for user understanding
4. **Integrate with FormulaEditorViewModel** for UI display
5. **Unit tests** for cycle detection logic

### Out of Scope (Explicitly Forbidden)

The following are **NOT part of Phase F-4** and must NOT be implemented:

| Forbidden Item | Reason |
|---------------|--------|
| **Formula execution** | F-4 is analysis-only; execution is Phase F-2 |
| **Automatic recalculation** | No runtime behavior in F-4 |
| **DAG schedulers or topological sort** | Beyond analysis scope |
| **Observers or reactive updates** | No pub/sub infrastructure |
| **Persistence of cycle results** | Results are transient, per-request |
| **Auto-blocking schema saves** | User decides response to warnings |
| **Schema mutation** | Read-only analysis |
| **Cross-entity cycle detection** | v2+ scope per ADR-040 |
| **Control system cycle detection** | Separate concern |
| **Cycle resolution suggestions** | Beyond v1 scope |
| **Graph visualization** | UI enhancement, not core detection |

## Non-Goals

1. **Preventing cyclic schemas from being saved**: The system informs; the user decides.
2. **Runtime cycle detection**: Cycles are detected at design-time only.
3. **Automatic cycle breaking**: No automated resolution of cycles.
4. **Dependency graph persistence**: No storing of computed graphs.
5. **Incremental detection**: Each detection is a complete analysis.
6. **Performance optimization via caching**: Simplicity over optimization.

## Architecture Impact

### Domain Layer
- **No changes required**
- Existing `FormulaParser` and AST are sufficient
- No new domain entities, value objects, or services

### Application Layer
- **Add**: `FormulaCycleDTO` and `FormulaCycleAnalysisResultDTO` in `dto/formula_dto.py`
- **Add**: `detect_cycles()` method in `FormulaUseCases`
- No new services, commands, or queries

### Presentation Layer
- **Add**: Cycle-related properties to `FormulaEditorViewModel`
- **No new widgets or dialogs**
- Cycle information displayed in existing Formula Editor panel

### Infrastructure Layer
- **No changes required**
- No persistence of cycle analysis results

## Consequences

### Positive

1. **Clear scope boundary**: Analysis-only with explicit forbidden list prevents scope creep
2. **Reuses existing infrastructure**: No new domain types or services
3. **Non-blocking UX**: Users can save mid-edit without cycle errors blocking them
4. **Deterministic**: Predictable, testable behavior
5. **Aligned with ADR-040**: Implements the "Circular Detection" phase as specified

### Negative

1. **Cycles can exist in saved schemas**: Runtime evaluation will fail for cyclic formulas
2. **No automatic prevention**: Users must manually resolve cycles
3. **Repeated analysis**: No caching means repeated work if formulas unchanged

### Neutral

1. **ERROR severity always**: No nuance in cycle severity (acceptable for v1)
2. **Same-entity only**: Scope limitation from ADR-040, not this ADR

## Alternatives Considered

### 1. Block Schema Save on Cycle Detection

**Rejected**: Poor UX for mid-edit scenarios. Users may have temporary cycles while restructuring formulas. Blocking saves creates friction.

### 2. Runtime Cycle Detection

**Rejected**: Cycles are structural problems that should be caught at design-time. Runtime detection adds complexity and latency with no benefit—the cycle exists either way.

### 3. Domain-Layer Cycle Detection Service

**Rejected**: Unnecessary domain complexity. Cycle detection is algorithmic analysis of formula ASTs, which the Application layer can perform using existing domain parser. No new domain concepts needed.

### 4. Persist Dependency Graph

**Rejected**: Over-engineering for v1. Dependency discovery and cycle detection are fast operations that can run on-demand. Persistence adds storage and synchronization complexity.

### 5. Incremental Cycle Detection

**Rejected**: Complexity not justified for v1. Full analysis on each change is simple and sufficient for the expected schema sizes.

## Related ADRs

- **ADR-040**: Formula Semantics, Validation, Storage, and Execution Lifecycle (parent ADR defining formula phases)
- **ADR-003**: Framework-Independent Domain Layer (domain purity)
- **ADR-005**: MVVM Pattern for Presentation Layer (ViewModel responsibilities)
- **ADR-010**: Immutable Value Objects (DTO immutability)
- **ADR-020**: DTO-Only MVVM (no domain types in presentation)
- **ADR-025**: Validation Severity Levels (ERROR severity classification)

## Implementation Phases

This ADR covers **Phase F-4** of the formula system:

| Phase | Name | Status |
|-------|------|--------|
| F-1 | Formula Editor (Read-Only) | ✅ Complete |
| F-2 | Formula Execution | Planned |
| F-3 | Dependency Discovery | ✅ Complete |
| **F-4** | **Cycle Detection** | **This ADR** |
| F-5 | Advanced Functions | Future (v2+) |

## Testing Requirements

Phase F-4 implementation must include:

1. **Unit tests for cycle detection algorithm**:
   - No cycles in linear chain
   - Simple 2-node cycle (A → B → A)
   - Multi-node cycle (A → B → C → A)
   - Multiple independent cycles
   - Mixed: some formulas cyclic, others not
   - Self-referential cycle (A → A)
   - Empty formula set (no cycles)

2. **ViewModel tests**:
   - Cycle properties reflect detection results
   - Properties return empty/false when no analysis performed

3. **DTO immutability tests**:
   - DTOs are frozen
   - DTOs contain only primitives

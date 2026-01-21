# Architectural Decision Records (ADRs) - Index

This document provides a centralized index of all ADRs for the Doc Helper project.

**Last Updated**: 2026-01-21
**Total ADRs**: 17 (13 Accepted, 3 Proposed, 1 gap)

---

## Quick Reference

| ADR | Title | Status | Category |
|-----|-------|--------|----------|
| [ADR-001](adrs/ADR-001-controlled-big-bang-rewrite.md) | Controlled Big Bang Rewrite Strategy | Accepted | Strategy |
| [ADR-002](adrs/ADR-002-clean-architecture-ddd.md) | Clean Architecture with Domain-Driven Design | Accepted | Architecture |
| [ADR-003](adrs/ADR-003-framework-independent-domain.md) | Framework-Independent Domain Layer | Accepted | Architecture |
| [ADR-004](adrs/ADR-004-cqrs-pattern.md) | CQRS for Read/Write Separation | Accepted | Patterns |
| [ADR-005](adrs/ADR-005-mvvm-pattern.md) | MVVM Pattern for Presentation Layer | Accepted | Patterns |
| [ADR-006](adrs/ADR-006-event-bus.md) | In-Memory Event Bus Over PyQt Signals | Accepted | Patterns |
| [ADR-007](adrs/ADR-007-repository-pattern.md) | Repository Pattern with Raw SQL Mappers | Accepted | Patterns |
| [ADR-008](adrs/ADR-008-result-monad.md) | Result Monad for Error Handling | Accepted | Patterns |
| [ADR-009](adrs/ADR-009-strongly-typed-ids.md) | Strongly Typed Identifiers | Accepted | Domain Design |
| [ADR-010](adrs/ADR-010-immutable-value-objects.md) | Immutable Value Objects | Accepted | Domain Design |
| [ADR-011](adrs/ADR-011-unit-of-work.md) | Unit of Work for Transaction Management | Accepted | Patterns |
| [ADR-012](adrs/ADR-012-registry-based-factory.md) | Registry-Based Factory for Extensibility | Accepted | Patterns |
| [ADR-013](adrs/ADR-013-multi-app-type-platform-vision.md) | Multi-Document-Type Platform Vision | Proposed | Vision (v2+) |
| [ADR-017](adrs/ADR-017-command-based-undo.md) | Command-Based Undo Model | Accepted | Undo System |
| [ADR-020](adrs/ADR-020-dto-only-mvvm.md) | DTO-Only MVVM Enforcement | Proposed | Compliance |
| [ADR-021](adrs/ADR-021-undo-state-dto-isolation.md) | UndoState DTO Isolation | Accepted | Undo System |
| [ADR-024](adrs/ADR-024-architectural-compliance-scanning.md) | Architectural Compliance Scanning | Proposed | Compliance |

---

## ADR Summaries

### ADR-001: Controlled Big Bang Rewrite Strategy
**Status**: Accepted
**Decision**: Perform a controlled big-bang rewrite of the legacy application rather than incremental refactoring, due to severe coupling, lack of tests, and clear functional requirements.
**Rationale**: The legacy codebase has extreme coupling (domain depends on PyQt6), no test coverage, and unclear boundaries. Incremental refactoring would take longer and risk introducing more technical debt. A clean rewrite with proper architecture allows test-first development and clear separation of concerns.

### ADR-002: Clean Architecture with Domain-Driven Design
**Status**: Accepted
**Decision**: Adopt Clean Architecture with DDD tactical patterns (aggregates, entities, value objects, domain services) as the primary architectural style.
**Rationale**: Enforces dependency rule (dependencies point inward), keeps business logic isolated in domain layer, enables testability, and provides clear boundaries between layers. DDD tactical patterns model complex business logic effectively.

### ADR-003: Framework-Independent Domain Layer
**Status**: Accepted
**Decision**: The domain layer must have ZERO external dependencies. No PyQt6, SQLite, file system, or network dependencies.
**Rationale**: Enables pure unit testing without mocking frameworks, allows porting to different UI frameworks (web, mobile), prevents framework upgrades from breaking business logic, and enforces clean separation of concerns.

### ADR-004: CQRS for Read/Write Separation
**Status**: Accepted
**Decision**: Separate Commands (write operations) from Queries (read operations) in the application layer.
**Rationale**: Simplifies application services, enables independent optimization of reads and writes, makes code more predictable (commands change state, queries don't), and prepares for future event sourcing if needed.

### ADR-005: MVVM Pattern for Presentation Layer
**Status**: Accepted
**Decision**: Use Model-View-ViewModel pattern for the PyQt6 presentation layer, with ViewModels mediating between domain and views.
**Rationale**: Decouples UI from domain logic, enables unit testing of presentation logic without UI framework, allows views to be thin (no business logic), and provides clear data flow: View → ViewModel → Application Service → Domain.

### ADR-006: In-Memory Event Bus Over PyQt Signals
**Status**: Accepted
**Decision**: Use a framework-independent in-memory event bus for domain events instead of PyQt signals.
**Rationale**: Keeps domain layer pure (no PyQt6 dependency), enables publish/subscribe decoupling (e.g., formula recalc when field changes), and allows future migration to different event infrastructure (Redis pub/sub, message queues).

### ADR-007: Repository Pattern with Raw SQL Mappers
**Status**: Accepted
**Decision**: Implement repository pattern with interfaces in domain layer and SQLite implementations in infrastructure layer. Use raw SQL with mappers instead of ORM.
**Rationale**: Explicit SQL provides full control over queries, no magic behavior from ORM, simpler debugging, and better performance. Mappers handle entity ↔ row conversion cleanly.

### ADR-008: Result Monad for Error Handling
**Status**: Accepted
**Decision**: Use Result[T, E] monad for explicit error handling instead of exceptions in domain and application layers.
**Rationale**: Makes errors explicit in type signatures, forces caller to handle errors, enables functional composition, and avoids hidden control flow (exceptions). Exceptions reserved for truly unexpected bugs.

### ADR-009: Strongly Typed Identifiers
**Status**: Accepted
**Decision**: Use strongly typed ID classes (FieldId, EntityId, ProjectId) instead of raw strings or UUIDs.
**Rationale**: Prevents ID mixing errors (passing EntityId where FieldId expected), self-documenting code, type checker catches mistakes, and enables ID-specific behavior (validation, formatting).

### ADR-010: Immutable Value Objects
**Status**: Accepted
**Decision**: All value objects must be frozen dataclasses (immutable after creation).
**Rationale**: Thread-safe by design, prevents accidental mutation, enables value equality, simplifies reasoning about code, and aligns with functional programming principles.

### ADR-011: Unit of Work for Transaction Management
**Status**: Accepted
**Decision**: Use Unit of Work pattern to manage transactions across multiple repository operations.
**Rationale**: Ensures atomicity (all changes committed or none), explicit transaction boundaries, prevents partial failures, and coordinates multiple repository saves in a single transaction.

### ADR-012: Registry-Based Factory for Extensibility
**Status**: Accepted
**Decision**: Use registry-based factories for creating widgets, transformers, and validators instead of hardcoded if/else chains.
**Rationale**: Enables extension without modifying factory code (Open/Closed Principle), supports plugin architecture, simplifies adding new types, and makes code more maintainable.

### ADR-013: Multi-Document-Type Platform Vision
**Status**: Proposed (v2+)
**Decision**: Transform Doc Helper into a universal document generation platform supporting multiple document types without code modification.
**Rationale**: Provides extensibility for future document types (structural reports, environmental assessments), enables app-type discovery from manifest files, and supports custom transformers per document type. Deferred to v2+ to maintain v1 focus.

### ADR-017: Command-Based Undo Model
**Status**: Accepted
**Decision**: Implement undo/redo using command pattern with explicit state capture specification.
**Rationale**: Provides clear undo semantics (what state to restore), enables selective undo (future), supports command composition, and makes undo logic testable. Commands capture state explicitly rather than relying on implicit diffs.

### ADR-020: DTO-Only MVVM Enforcement
**Status**: Proposed
**Decision**: Enforce that ViewModels work exclusively with DTOs, never directly with domain entities.
**Rationale**: Prevents domain pollution with UI concerns, enables independent DTO evolution, simplifies serialization, provides explicit presentation models, and maintains clean architecture boundaries. Currently enforced by convention and scanning tool (ADR-024).

### ADR-021: UndoState DTO Isolation
**Status**: Accepted
**Decision**: Separate UndoState DTOs from UI DTOs. UndoState DTOs are internal to application layer and not exposed to presentation.
**Rationale**: Undo state needs different data than UI display (e.g., formula dependencies, validation context), prevents UI coupling to undo internals, and allows independent evolution of undo and presentation models.

### ADR-024: Architectural Compliance Scanning
**Status**: Proposed
**Decision**: Implement automated compliance scanning tool to detect architectural violations (layer violations, DTO usage, import rules).
**Rationale**: Enforces architectural boundaries automatically, prevents drift over time, provides fast feedback (CI integration), and documents rules as code. Tool checks: domain purity (no PyQt6/SQLite imports), DTO-only MVVM, repository pattern compliance.

---

## ADR Gaps

**Reserved Number Ranges**:
- ADR-014 through ADR-019: Reserved for future architectural decisions
- ADR-022 through ADR-023: Reserved for future compliance/undo extensions

These gaps allow for inserting related ADRs without renumbering existing ones.

---

## Implementation Status

### Phase A (Current Scope - U1-U12): Implemented
- ✅ ADR-001: Controlled Big Bang Rewrite Strategy
- ✅ ADR-002: Clean Architecture with DDD
- ✅ ADR-003: Framework-Independent Domain Layer
- ✅ ADR-004: CQRS Pattern
- ✅ ADR-005: MVVM Pattern
- ✅ ADR-006: Event Bus
- ✅ ADR-007: Repository Pattern
- ✅ ADR-008: Result Monad
- ✅ ADR-009: Strongly Typed IDs
- ✅ ADR-010: Immutable Value Objects
- ✅ ADR-011: Unit of Work (partial - SQLite UoW exists, full multi-repo coordination in progress)
- ✅ ADR-012: Registry-Based Factory
- ✅ ADR-017: Command-Based Undo Model
- ✅ ADR-021: UndoState DTO Isolation
- ✅ ADR-020: DTO-Only MVVM Enforcement (compliance scanning implemented)
- ✅ ADR-024: Architectural Compliance Scanning (tool implemented)

### Near-Term Expansion: Planned
- ADR-013: Multi-Document-Type Platform Vision (deferred to v2+)
- Additional ADRs for validation severity, search architecture, field history, etc. (planned)

### Long-Term Expansion: Vision
- ADRs for plugin architecture, performance/scaling, advanced features (planned)

---

## Decision Precedence

When conflicts arise between documents, the following precedence order applies (from [CONTINUOUS_TECHNICAL_ROADMAP.md Section 7.3](CONTINUOUS_TECHNICAL_ROADMAP.md)):

1. **AGENT_RULES.md** (highest priority - non-negotiable execution rules)
2. **CONTINUOUS_TECHNICAL_ROADMAP.md** (current scope and status)
3. **unified_upgrade_plan_FINAL.md** (historical requirements reference)
4. **Referenced ADRs** (architectural decisions)
5. **Deprecated plans** (historical only, no authority)

---

## Adding New ADRs

When creating new ADRs:

1. **Choose Next Available Number**: Use the next unused number in sequence (ADR-025, ADR-026, etc.)
2. **Use Standard Template**: Status, Context, Decision, Consequences sections
3. **File Naming**: `ADR-XXX-kebab-case-title.md`
4. **Update This Index**: Add entry to Quick Reference table and Summaries section
5. **Mark Status**: Proposed (for review) or Accepted (if approved)
6. **Link from Roadmap**: Reference in relevant CONTINUOUS_TECHNICAL_ROADMAP.md sections

---

**END OF ADR INDEX**

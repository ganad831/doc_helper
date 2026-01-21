# ADR-027: Field History Storage

**Status**: Accepted

**Context**:

The application tracks field values at a point in time but provides no mechanism to view historical values. Users can see current values and use undo/redo for recent changes within a session, but once undo history is cleared (session end, save, or undo stack limit), all knowledge of previous values is lost.

This creates several architectural problems:

### 1. Audit Gap

No mechanism exists to answer "what was this field's value last week?" or "who changed this field and when?" Users cannot audit field changes for compliance, quality assurance, or troubleshooting. When issues arise, no record exists of how the current state was reached.

Regulatory requirements, quality control processes, or collaborative workflows may demand change tracking. The architecture provides no foundation for audit capabilities.

### 2. Undo/History Conflation

The undo system (ADR-017) serves two distinct purposes: reversing recent mistakes and viewing historical state. These are separate concerns with different lifecycles:

**Undo** is session-scoped and ephemeral. Undo enables short-term reversal of accidental changes. Undo history clears on save, application restart, or stack depth limit.

**History** is project-scoped and persistent. History enables long-term investigation and audit. History must survive indefinitely within the project.

Conflating these concerns in a single undo stack creates architectural tension. Undo stack depth limits conflict with unbounded history needs. Undo's ephemeral nature conflicts with history's persistence requirement.

### 3. Loss of Context

When investigating issues ("why does this calculation seem wrong?"), users cannot see how values evolved over time. If a field changed from X to Y to Z, only Z is visible. The path to Z is invisible.

Understanding causality requires seeing change sequences. Did a formula recalculate and change this value? Did a user override it? When did the transition occur? Without history, these questions are unanswerable.

### 4. Change Tracking Absence

No architectural component treats field mutations as a permanent record. Field changes happen in isolation. Domain events are emitted but not captured for long-term storage. Once an event is processed, the knowledge of what changed is lost.

The architecture lacks a conceptual home for "things that happened in the past."

**Decision**:

Introduce field history as a persistent, append-only record of field value changes, architecturally distinct from the undo system.

### 1. History Scope

**Field-Level Granularity**: History tracks changes at the individual field level. Each history entry records one field's value transition at a specific moment.

**Project-Scoped Persistence**: History is stored persistently within the project boundary. History survives session closure, application restart, and undo stack clearing. History is part of the project's permanent state.

**Append-Only Semantics**: History entries are never modified or deleted once written. History is an immutable ledger of changes.

### 2. What Constitutes a Field Change

**Value Transitions Only**: A history entry is created when a field's resolved value changes from one distinct value to another. Setting a field to its current value creates no history entry.

**User-Initiated Changes**: Direct user edits to field values create history entries with user attribution.

**Formula Recomputation**: When a formula field's computed value changes due to dependency changes, a history entry is created with formula attribution.

**Override Acceptance**: When an override is accepted and changes a field's resolved value, a history entry is created with override attribution.

**Control Effects**: When a control rule changes a field's value (VALUE_SET effect), a history entry is created with control attribution.

**No Intermediate States**: Failed validation, abandoned edits, or uncommitted changes do not create history entries. Only successful value transitions that persist to the project state are recorded.

### 3. Relationship to Undo System

**Distinct Architectural Concerns**: History and undo are separate systems with different purposes and lifecycles.

**Undo is Ephemeral**: Undo enables short-term reversal of recent actions. Undo stack is session-scoped and cleared on save, session end, or stack depth limit.

**History is Persistent**: History enables long-term audit and investigation. History survives indefinitely within the project.

**Undo Commands May Create History**: When an undo command executes successfully and changes a field's value, that change creates a history entry like any other value change. Undoing a change is itself a change.

**History Does Not Enable Undo**: History is read-only for querying past states. History does not provide revert or restore capabilities. Reverting to a historical value is a new user edit (which itself creates history).

### 4. Architectural Roles

**Domain Events as History Source**: Field value changes emit domain events (FieldValueChanged, FormulaRecomputed, OverrideAccepted). These events are the authoritative source for history entry creation.

**Application Layer Orchestration**: The application layer subscribes to domain events and coordinates history persistence. The application layer determines when a change qualifies for history recording and captures change context.

**Infrastructure Persistence**: The infrastructure layer implements history storage. The storage mechanism is an infrastructure concern addressed through the repository pattern.

**History as Query Operation**: Retrieving history is a read-only query operation within the CQRS pattern. History queries return data transfer objects for presentation consumption.

**Presentation Displays History**: The presentation layer receives history via data transfer objects and interprets for user display. Presentation never directly accesses history storage.

### 5. History Entry Content

Each history entry conceptually contains:

**Field Identity**: Which field changed (field path, entity reference).

**Value Transition**: Previous value and new value.

**Change Metadata**: When the change occurred (timestamp), change source (user edit, formula recomputation, override acceptance, control effect), optional attribution (user identifier).

**No Domain Logic**: History entries are pure data. No validation rules, no business constraints. History records what happened, not what should happen.

### 6. Architectural Rules

**History is Append-Only**: Once written, history entries are immutable and permanent. No updates, no deletions (except full project deletion).

**History Recording is Asynchronous**: History creation does not block the primary operation. If history persistence fails, the field change still succeeds. History is observational, not transactional.

**History is Optional**: The system functions without history. History is an additive audit capability, not a requirement for core workflows. Disabling history does not impair field editing, validation, formula evaluation, or document generation.

**No Circular Dependencies**: History observes domain events but does not emit events or trigger side effects. History is a pure sink. History recording cannot cause further field changes.

**DTO Boundary Respected**: History queries return data transfer objects (ADR-020). Presentation never imports domain history entities or value objects.

**Project Boundary Enforcement**: History belongs to a specific project. No cross-project history queries. When a project is deleted, its history is deleted.

**Alternatives Considered**:

### Alternative 1: No History System
Rely on undo for recent changes and external backups for long-term records.

**Rejected**: Insufficient for audit needs. Undo is ephemeral and session-scoped. External backups are coarse-grained (full project snapshots at backup time). No fine-grained field-level change tracking. Cannot answer "who changed this field and when?" without manual backup comparison across multiple backup files.

### Alternative 2: UI-Only History (Session Memory)
Track changes in presentation layer memory, cleared on application close.

**Rejected**: Violates architectural boundaries. History is a domain/application concern, not a presentation concern. Session-scoped history does not satisfy audit requirements (must survive save and restart). No persistence means no value for long-term investigations or compliance. Cannot be tested independently of UI framework.

### Alternative 3: Database Triggers
Use database-level triggers to automatically log field changes.

**Rejected**: Violates framework-independence (ADR-003). Domain layer would be unaware of history, cannot control what gets logged. Tight coupling to database implementation. History logic embedded in infrastructure rather than application layer. Difficult to test history behavior in isolation. Change source attribution (user vs formula vs override) not available at database level. Violates Clean Architecture dependency rule.

### Alternative 4: Full Event Sourcing
Store all domain events permanently and reconstruct field state from event replay.

**Rejected**: Over-engineering for current scope. Event sourcing requires comprehensive architectural overhaul (event store, read models, projections, snapshotting). High complexity cost. Near-term need is simpler: track field value changes for audit, not rebuild entire domain state from events. Event sourcing introduces eventual consistency complexity unnecessary for current requirements. Event sourcing is a Long-Term Expansion consideration, not Near-Term.

### Alternative 5: Reuse Undo Stack as History
Persist undo commands permanently instead of clearing them, and query undo stack for history.

**Rejected**: Conflates separate concerns. Undo commands contain execution state (how to reverse an operation), not audit state (what changed and why). Undo stack has bounded depth for usability. History needs unbounded append-only storage for audit completeness. Undo commands may contain sensitive temporary state inappropriate for permanent audit trails. Architectural roles fundamentally differ: undo enables reversal, history enables investigation.

### Alternative 6: History as Separate Aggregate Root
Model history as a domain aggregate with business rules and invariants.

**Rejected**: History has no business rules or invariants to enforce. History is pure data recording, not domain behavior. Modeling as aggregate adds unnecessary complexity (aggregate identity management, invariant enforcement, aggregate lifecycle). History entries are independent records with no aggregate consistency boundaries. History is a cross-cutting concern, not a core domain entity.

**Consequences**:

**Positive**:

- (+) **Audit Capability**: Users can answer "what changed, when, and why?" for compliance and investigation
- (+) **Change Transparency**: Full visibility into field value evolution over time
- (+) **Separation of Concerns**: History and undo are distinct systems with clear boundaries (ADR-017 preserved)
- (+) **Domain Event Integration**: History leverages existing event infrastructure without domain changes
- (+) **Architectural Compliance**: Maintains Clean Architecture, DTO-Only MVVM, framework independence
- (+) **Asynchronous Recording**: History does not impact primary operation performance
- (+) **Testability**: History logic testable independently via event subscriptions
- (+) **Investigation Support**: Troubleshooting and debugging aided by full change context

**Costs**:

- (-) **Storage Growth**: History accumulates unbounded over project lifetime
- (-) **New Infrastructure**: Requires history repository interface and implementation
- (-) **Event Subscription Complexity**: Application layer must subscribe to multiple domain events
- (-) **Query Performance**: Large history datasets may require indexing and pagination strategies
- (-) **Attribution Tracking**: Requires capturing change source and user identity at event emission
- (-) **Asynchronous Failure Handling**: History persistence failures must not fail primary operations

**Mitigation**:

- History storage scoped to project (not global), limiting unbounded growth concern per project
- Repository interface in domain, implementation in infrastructure (testable, replaceable)
- Pagination and filtering for history queries (infrastructure optimization)
- Attribution data captured in domain events (application layer passes context)
- History persistence failures logged but do not propagate to user-facing operations
- History queries return DTOs with pagination metadata for large result sets

**Non-Goals**:

This decision does NOT address:

- **History UI Design**: How history is displayed to users (presentation concern)
- **History Export**: Exporting history to external formats (CSV, PDF) for reporting
- **History Retention Policies**: Automatic cleanup, archival, or pruning after time periods
- **Cross-Project History**: Searching or aggregating history across multiple projects
- **History-Based Restore**: Reverting fields to historical values (separate feature using history as data source)
- **Audit Trail Signing**: Cryptographic proof of history integrity or tamper detection
- **History Compression**: Storage optimization techniques for old history entries

**Related**:

- **ADR-017: Command-Based Undo Model**: History is distinct from undo, with separate lifecycles
- **ADR-004: CQRS Pattern**: History retrieval implemented as query operation
- **ADR-006: Event Bus**: History subscribes to domain events for change detection
- **ADR-020: DTO-Only MVVM Enforcement**: History queries return DTOs exclusively
- **ADR-003: Framework-Independent Domain Layer**: History observes domain events without framework coupling
- **ADR-011: Unit of Work**: History persistence may coordinate with UoW for transactional boundaries
- **CONTINUOUS_TECHNICAL_ROADMAP.md Section 4.2**: Near-Term Expansion UX Enhancements

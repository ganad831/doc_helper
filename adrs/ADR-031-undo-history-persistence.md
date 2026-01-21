# ADR-031: Undo History Persistence

**Status**: Accepted

**Context**:

The undo system (ADR-017) enables reversal of recent field value changes through a command-based model. Commands capture sufficient state to reverse operations, allowing users to correct mistakes within a session.

The current undo implementation is session-scoped and ephemeral. When a user closes a project, saves a project, or the application terminates, all undo history is immediately lost. The undo stack exists only in application memory and never persists to storage.

This ephemeral nature creates several architectural and usability tensions:

### 1. User Expectation Mismatch

Users expect undo capability to persist across natural workflow interruptions. When a user saves a project and continues working, they expect to undo changes made before the save. When a user closes the application and reopens the same project minutes later, they expect recent undo history to remain available.

The current session-only undo violates these expectations. Saving a project clears undo history, creating the false impression that save is a "commit forever" operation. Closing and reopening a project eliminates all undo capability, requiring users to keep the application running indefinitely to preserve undo.

This mismatch is particularly acute during long editing sessions. A user working on a project over several days must either keep the application running continuously or accept that each application restart loses all undo history.

### 2. Recovery Gap

Application crashes, system restarts, or forced terminations destroy the undo stack entirely. When the application terminates unexpectedly, users lose both the ability to undo recent changes and the knowledge that those changes occurred (no audit trail exists for session-only undo).

This creates a recovery gap. If the application crashes after a user makes unwanted changes, reopening the project shows the unwanted changes with no undo capability. The user cannot reverse the changes through undo and must manually restore previous values (if remembered) or rely on external backups.

Field history (ADR-027) records that changes occurred but does not enable reversal. History is read-only and observational. Users can see that a field changed from X to Y but cannot use history to restore X. Undo enables reversal; history enables audit. Both serve distinct purposes, but neither substitutes for the other.

### 3. Save Operation Semantics

The current architecture treats "save" as a destructive operation that clears undo history. This creates ambiguity about what "save" means. Does save mean "persist current state to disk" (non-destructive), or does it mean "commit this state permanently and discard undo" (destructive)?

Traditional desktop applications often clear undo on save, establishing the precedent that save commits changes irrevocably. However, modern applications increasingly preserve undo across saves, treating save as routine persistence rather than permanent commitment.

The architectural question is: what semantics should save have in the context of project-based editing? Is save a session boundary (undo cleared) or merely a persistence operation (undo preserved)?

### 4. Undo Scope Ambiguity

ADR-017 defines undo as "session-scoped," but "session" is architecturally ambiguous. Does a session end on save? On project close? On application close? On system restart?

Without clear architectural boundaries, session-scoped undo has inconsistent behavior. If session ends on save, undo is frequently cleared (frustrating). If session ends only on project close, undo survives saves but not reopens (partially useful). If session ends only on application close, undo survives project close/reopen (confusing project boundaries).

This ambiguity creates tension between undo as ephemeral (short-term reversal) and user expectations of undo as project-scoped (available throughout project editing lifecycle).

### 5. Architectural Relationship to History

ADR-027 introduces field history as persistent, project-scoped audit trails. Field history explicitly separates from undo, with different lifecycles and purposes. However, the architectural relationship between undo and history remains unclear when undo does not persist.

If undo is purely ephemeral and history is persistent, what happens during the gap between session end and history recording? When a user undoes a change, that undo operation creates a new history entry (undoing is a change). But if undo history is lost on session end, the architectural record of what was undone disappears, leaving only the history entry with no context.

This creates an architectural inconsistency: history records that a change occurred, but the knowledge that the user undid it (and potentially re-did it) exists only in ephemeral undo, which may be gone by the time history is reviewed.

**Decision**:

Introduce undo history persistence as project-scoped storage of undo stack state, enabling undo capability to survive application lifecycle events while maintaining clear session boundaries.

### 1. Persistence Scope

**Project-Scoped Storage**: Undo history is stored within the project boundary. Undo state belongs to a specific project and persists alongside project data.

**Survives Application Restart**: When a project is reopened after application termination (normal close, crash, system restart), undo history is restored. Users regain the ability to undo recent changes from previous sessions.

**Survives Save Operations**: Saving a project does not clear undo history. Save is a non-destructive persistence operation. Users can undo changes made before a save without distinction from changes made after a save.

**Cleared on Project Close**: When a user explicitly closes a project (File → Close Project), undo history is permanently discarded. Project close is an intentional session boundary. Reopening the same project later begins a new session with empty undo history.

**Independent of Field History**: Undo persistence is architecturally distinct from field history (ADR-027). Undo enables reversal (ephemeral, operation-focused). History enables audit (permanent, record-focused). Both coexist with separate persistence mechanisms.

### 2. What Is Persisted

**Undo Command State**: Only the state necessary to reverse operations is persisted. Execution state, intermediate computations, or transient runtime data is not persisted.

**Redo Capability Preserved**: Both undo and redo stacks persist. If a user undoes three changes, closes the application, and reopens, those three changes remain available for redo.

**Stack Order Maintained**: The sequential order of undo operations is preserved. The most recent change remains at the top of the undo stack across persistence boundaries.

**Bounded Stack Depth**: Undo stack persistence respects stack depth limits. If undo is bounded to 50 operations (architectural policy), persistence does not store more than 50 operations. Old operations are pruned before persistence, not after restoration.

### 3. Lifecycle Boundaries

**Write on Project Save**: Undo history is written to persistent storage during project save operations. Save becomes responsible for persisting both project data and undo state.

**Write on Application Close**: When the application terminates normally (user closes application with project still open), undo history is written before termination. This ensures graceful shutdown preserves undo.

**Restore on Project Open**: When a project is opened, undo history is restored from persistent storage. If no persisted undo exists (new project, or first open after this feature), the undo stack begins empty.

**Discard on Project Close**: When a user explicitly closes a project, persisted undo history is deleted. The act of closing a project signals the end of an editing session. Reopening the same project later does not restore previous undo history.

**No Cross-Project Undo**: Undo history is isolated per project. Switching between projects switches undo contexts. Closing one project and opening another provides separate undo histories.

### 4. Architectural Roles

**Application Layer Orchestration**: The application layer coordinates undo persistence. Commands from the undo system are serialized for storage and deserialized on restoration. The application layer determines when persistence occurs (save, close) and when restoration occurs (open).

**Infrastructure Persistence**: The infrastructure layer implements undo storage. The storage mechanism (file-based, database table, separate file) is an infrastructure concern addressed through repository pattern. The application layer depends on storage abstractions, not concrete implementations.

**Domain Remains Pure**: The domain layer is unaware of undo persistence. Commands are domain concepts, but persistence logic resides in infrastructure. Undo commands do not implement serialization methods or storage logic.

**Presentation Remains Isolated**: The presentation layer is unaware of undo persistence mechanics. Undo/redo operations trigger through view models as before (ADR-020). The fact that undo survives application restart is transparent to the UI.

### 5. Architectural Rules

**Undo Persistence is Synchronous**: Writing undo history during save or close is synchronous. If undo persistence fails, the save or close operation should fail (or warn the user). Undo is not optional background work; it is part of project state.

**Restoration is Best-Effort**: If persisted undo cannot be restored (corrupted file, incompatible format, missing dependencies), the project opens successfully with an empty undo stack. Undo restoration failure does not prevent project access.

**No Version Migration**: Persisted undo is version-specific. If the application version changes in ways that make old undo commands incompatible, restoration is skipped. Old undo is discarded rather than migrated. Undo is a convenience feature, not critical data.

**Undo Does Not Block Save**: If undo persistence fails during save, project data is still saved. Undo persistence failure is logged and reported but does not abort the save operation. Losing undo is acceptable; losing project data is not.

**Bounded Complexity**: Undo persistence introduces minimal architectural complexity. Persistence is an additive feature. The core undo system (ADR-017) functions identically whether persistence is enabled or disabled.

### 6. Relationship to Field History

**Undo and History Serve Different Purposes**: Undo enables reversal of recent mistakes (operational capability). History enables audit of past changes (investigative capability). Undo is user-facing (make this go away). History is analyst-facing (why did this happen?).

**Undo is Temporary, History is Permanent**: Even with persistence, undo has a finite lifespan (cleared on project close, bounded stack depth). History is append-only and permanent (survives indefinitely). Undo is convenience; history is compliance.

**Undo Commands Create History Entries**: When a user executes an undo command, that operation triggers field value changes, which create field history entries (ADR-027). Undoing a change is itself a change. History records the undo operation, preserving the audit trail even if undo history is later cleared.

**History Does Not Enable Undo**: Field history is read-only. Viewing history does not provide "revert to this value" functionality. Reverting to a historical value is a manual user edit (which itself creates history). History and undo are architecturally independent.

**Alternatives Considered**:

### Alternative 1: No Undo Persistence (Status Quo)

Maintain session-only undo. Undo history is lost on save, project close, or application restart.

**Rejected**: Fails to address user expectation mismatch and recovery gap. Users lose undo capability at natural workflow boundaries (saving progress, closing for the night). Application crashes eliminate undo entirely. Frustrating user experience compared to modern application standards.

### Alternative 2: Full Persistence of Undo Commands with Execution State

Persist undo commands including all execution state, intermediate computations, and runtime context. Restore commands with full fidelity, ensuring undo operates identically after restoration as during the original session.

**Rejected**: Over-engineering with high complexity cost. Execution state includes transient data (widget references, computed intermediate results, validation caches) that does not serialize cleanly. Commands would need complex serialization logic, violating domain purity. Restoration would require reconstructing runtime context, creating fragile dependencies. Minimal benefit over persisting only reversal state.

### Alternative 3: Persisting Undo as Field History

Store undo operations as field history entries. Implement undo by querying history and reversing changes. Eliminate separate undo persistence by reusing history infrastructure.

**Rejected**: Conflates two distinct architectural concerns. Undo is operational (reverse this specific change sequence). History is audit (what happened over time). Undo requires sequential reversal (pop from stack). History is append-only and never deleted. Undo is bounded (50 operations). History is unbounded (entire project lifetime). Merging these concerns creates a confused hybrid that serves neither purpose well. ADR-027 explicitly separates undo and history for architectural clarity.

### Alternative 4: Snapshot-Based Restore Instead of Undo Persistence

Instead of persisting undo commands, persist periodic project snapshots. Implement undo by restoring from snapshots. When a user undoes, revert the project to a previous snapshot.

**Rejected**: Creates duplicate state management system. Snapshots are full project state, much larger than undo command state. Frequent snapshots consume significant storage. Restoring snapshots loses changes made after the snapshot (destructive). Undo semantics require incremental reversal (undo one change at a time), not snapshot restoration (revert entire project state). Snapshot-based undo violates command-based undo model (ADR-017).

### Alternative 5: Persist Undo Commands Without Execution State (Minimal Persistence)

Persist only the minimal state necessary to reverse operations. Do not persist execution state, runtime context, or intermediate computations. Commands contain only: field ID, old value, new value (for SetFieldValueCommand).

**Accepted as Part of Decision**: This is not an alternative but the chosen approach. Minimal persistence reduces complexity while preserving undo capability. Commands are data-focused (what changed) rather than execution-focused (how to execute). Restoration reconstructs commands from persisted state without requiring runtime context.

### Alternative 6: Clear Undo on Save (Traditional Desktop App Behavior)

Persist undo across application restarts but clear undo on save. Save becomes a session boundary. Users can undo within a save cycle but not across saves.

**Rejected**: "Save" as session boundary is unintuitive in project-based editing workflows. Users save frequently (every few minutes) for safety. Clearing undo on each save makes undo nearly useless (only available for unsaved work). Modern applications treat save as routine persistence, not commitment. Users expect undo to survive saves, treating save as "write to disk" rather than "lock in changes."

### Alternative 7: Persist Undo Indefinitely (Survives Project Close)

Persist undo across project close/reopen. Undo history remains available indefinitely, surviving all lifecycle events. Users can undo changes from weeks or months ago.

**Rejected**: Violates the architectural distinction between undo and history. Undo is short-term reversal (ephemeral). History is long-term audit (persistent). If undo survives indefinitely, it becomes de facto history, conflating two concerns. Project close is a natural session boundary. When a user closes a project and reopens it days later, changes from the previous session are committed. Undo should not span session boundaries. Use field history (ADR-027) for long-term change tracking.

**Consequences**:

**Positive**:

- (+) **User Expectation Alignment**: Undo survives saves and application restarts, matching modern application behavior
- (+) **Crash Recovery**: Application termination does not destroy undo capability, enabling recovery from mistakes after crashes
- (+) **Save Semantics Clarity**: Save is non-destructive persistence, not permanent commitment
- (+) **Session Boundary Clarity**: Project close is the explicit session boundary, providing clear undo lifecycle
- (+) **Architectural Consistency**: Undo and history remain distinct (ADR-027), with separate persistence lifecycles
- (+) **Command Model Preserved**: Persistence extends command-based undo (ADR-017) without changing core semantics
- (+) **Graceful Degradation**: Restoration failure does not prevent project access (best-effort restoration)
- (+) **Minimal Complexity**: Undo persistence is additive, does not require changes to core undo logic

**Costs**:

- (-) **Storage Overhead**: Undo state persists alongside project data, increasing project file size
- (-) **Serialization Complexity**: Application layer must serialize and deserialize undo command state
- (-) **Version Compatibility Risk**: Persisted undo may become incompatible across application versions
- (-) **Save Performance Impact**: Save operations include undo persistence, potentially slower writes
- (-) **Restoration Failure Handling**: Must handle cases where persisted undo cannot be restored
- (-) **Bounded Stack Management**: Stack depth limits must be enforced before persistence, not after
- (-) **Testing Complexity**: Persistence and restoration add test scenarios (save, close, reopen, crash)

**Mitigation**:

- Storage overhead limited by bounded stack depth (architectural policy: 50 operations max)
- Serialization uses minimal state (field IDs, values) without execution context
- Version incompatibility handled by discarding old undo (best-effort restoration, no migration)
- Undo persistence does not block save (failure logged, project data saved regardless)
- Restoration failure results in empty undo stack (project opens normally)
- Stack pruning occurs during normal operations, before persistence triggered
- Test scenarios cover full lifecycle: save with undo, close/reopen, crash simulation

**Non-Goals**:

This decision does NOT address:

- **Branching Undo**: Tree-based undo with multiple branches (v2+ feature, see CONTINUOUS_TECHNICAL_ROADMAP.md)
- **Selective Undo**: Undo specific operation without undoing later operations (v2+ feature)
- **Undo Timeline UI**: Visual timeline of undo history with timestamps and previews (presentation concern)
- **Undo History Export**: Exporting undo operations for external analysis (not required)
- **Cross-Project Undo**: Undo operations spanning multiple projects (violates project boundary)
- **Undo Compression**: Storage optimization for large undo stacks (premature optimization)
- **Undo Synchronization**: Multi-user undo coordination for collaborative editing (v2+ feature)
- **Checkpoint System**: Named save points in undo history (separate feature, see ADR-033)

**Related**:

- **ADR-017: Command-Based Undo Model**: Undo persistence extends command-based undo with storage
- **ADR-027: Field History Storage**: History is distinct from undo, with separate persistence and lifecycle
- **ADR-011: Unit of Work**: Undo persistence may coordinate with UoW for transactional boundaries
- **ADR-004: CQRS Pattern**: Undo persistence is a write operation coordinated by application layer
- **ADR-020: DTO-Only MVVM Enforcement**: Presentation layer unaware of undo persistence mechanics
- **ADR-003: Framework-Independent Domain Layer**: Undo commands remain pure, persistence in infrastructure
- **CONTINUOUS_TECHNICAL_ROADMAP.md Section 4.5**: Near-Term Expansion Undo/Redo Extensions

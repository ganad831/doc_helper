# Near-Term Implementation Plan

**Status**: Ready for Approval
**Date**: 2026-01-21
**Scope**: Implementation of ADR-025, ADR-026, ADR-027, ADR-031, ADR-039
**Prerequisites**: Phase A complete, all Near-Term ADRs accepted
**Estimated Duration**: 52-67 days (10.5-13.5 weeks)

---

## 1. Implementation Order

### Rationale for Sequencing

The implementation order is designed to:
- Build foundational changes first (validation severity affects all subsequent features)
- Group similar patterns together (history + undo persistence both use append-only patterns)
- Minimize rework by implementing dependencies before dependents
- Enable partial delivery (each phase delivers user value independently)
- Reduce integration risk (export/import last, as it touches entire system)

### Phase Dependencies

```
Phase 1: ADR-025 (Validation Severity)
    ↓
Phase 2: ADR-027 (Field History) + ADR-031 (Undo Persistence)
    ↓                           ↓
Phase 3: ADR-026 (Search) ←─────┘
    ↓
Phase 4: ADR-039 (Import/Export) ← depends on all previous phases
```

### Implementation Sequence

| Phase | ADR | Feature | Duration | Dependencies |
|-------|-----|---------|----------|--------------|
| **1** | ADR-025 | Validation Severity Levels | 7-10 days | None (extends existing validation) |
| **2a** | ADR-027 | Field History Storage | 10-12 days | Phase 1 complete |
| **2b** | ADR-031 | Undo History Persistence | 10-13 days | Phase 1 complete |
| **3** | ADR-026 | Search Architecture | 10-12 days | Phase 1 complete (can parallelize with Phase 2) |
| **4** | ADR-039 | Import/Export Data Format | 15-20 days | Phases 1-3 complete |

**Total**: 52-67 days

**Parallelization Opportunities**:
- Phase 2a and 2b can run in parallel (similar patterns, separate components)
- Phase 3 can start after Phase 1, overlapping with Phase 2

---

## 2. Feature Breakdown by ADR

### 2.1 ADR-025: Validation Severity Levels

**Core Responsibilities**:
- Introduce three-level severity system: ERROR, WARNING, INFO
- Extend validation results to include severity metadata
- Implement workflow control based on severity (ERROR blocks, WARNING allows confirmation, INFO never blocks)
- Maintain backward compatibility (existing constraints default to ERROR)

**Affected Layers**:

**Domain Layer**:
- Define severity value object with three levels: ERROR, WARNING, INFO
- Extend validation result value object to include severity per failure
- Validation constraints declare default severity
- No new aggregates or repositories

**Application Layer**:
- Workflow orchestration interprets severity for generation control
- Generation operations check for ERROR-severity failures before proceeding
- WARNING-severity failures require explicit user confirmation
- Map validation results with severity to data transfer objects

**Infrastructure Layer**:
- No changes required (severity is in-memory concept, not persisted)

**Presentation Layer**:
- Consume severity via data transfer objects (never import domain severity directly)
- Visual differentiation for severity levels
- Pre-generation checklist distinguishes blocking errors from warnings
- Confirmation mechanism for WARNING-level issues before generation

**Required New Components**:
- Severity value object in domain layer
- Extended validation result with severity collection
- Data transfer object for validation results with severity
- Presentation component methods for severity-based filtering and display
- UI components for severity-coded validation indicators

**No New Repositories**: Severity is runtime concept only.

---

### 2.2 ADR-027: Field History Storage

**Core Responsibilities**:
- Introduce append-only field-level change history
- Record history from domain events
- Provide read-only query access to history (no revert capability)
- Persist history within project storage, scoped to project lifecycle
- Handle asynchronous recording (non-blocking to primary operations)

**Affected Layers**:

**Domain Layer**:
- Define history entry value object containing field identifier, old value, new value, timestamp, change source, context
- Define history repository interface with append-only operations
- Domain events remain unchanged (already emit field change events)
- No changes to aggregates (history is observational, not behavioral)

**Application Layer**:
- Event handlers subscribe to domain events and record history entries
- Event handler maps domain events to history entries and coordinates with repository
- Query operation retrieves history for specific field
- History recording is asynchronous and best-effort (failure logged, not blocking)
- Data transfer object exposes history to presentation

**Infrastructure Layer**:
- History persistence implementation with append-only storage
- New storage table for history entries with required indexes
- Indexed for efficient queries by project, field, and timestamp
- Cleanup strategy: history deleted when project deleted (no separate retention policy in v1)

**Presentation Layer**:
- Presentation component displays history timeline for selected field
- Display mechanism showing change history with timestamp, source, values
- No edit capability (read-only display)
- Optional: diff view showing old vs new values

**Required New Components**:
- History entry value object
- History repository interface
- Event handler for history recording
- History query operation
- History data transfer object
- History persistence implementation
- History storage table
- History presentation components

---

### 2.3 ADR-031: Undo History Persistence

**Core Responsibilities**:
- Persist undo stack state within project storage
- Restore undo stack when project reopens
- Clear undo stack on explicit project close (session boundary)
- Survive application restarts and save operations
- Handle version incompatibility and corruption gracefully (best-effort restoration)

**Affected Layers**:

**Domain Layer**:
- No changes (undo commands already exist, domain unaware of persistence)

**Application Layer**:
- Extend undo commands to support serialization of command state
- Persistence operation: persist undo stack before save/close
- Restoration operation: reload undo stack on project open
- Cleanup operation: explicit clear on project close
- Coordinate with Unit of Work for atomic undo persistence

**Infrastructure Layer**:
- Undo persistence implementation stores serialized undo stack
- New storage table for undo stack state
- Serialization strategy: minimal representation of command state, excludes execution context
- Restoration: deserialize to reconstruct command objects and populate undo stack
- Failure handling: corrupted undo data logged, empty stack used, project still accessible

**Presentation Layer**:
- No direct changes (undo/redo interface already exists)
- Transparent to user: undo stack survives restarts automatically
- Optional: visual indicator when restored undo stack available

**Required New Components**:
- Command serialization/deserialization logic in application layer
- Undo persistence operations: save, restore, clear
- Undo persistence implementation
- Undo storage table
- Best-effort restoration error handling

**Critical Distinction**: Undo persistence is architecturally distinct from field history (ADR-027). Undo enables reversal (operational, temporary), history enables audit (investigative, permanent). Undoing a change creates a new history entry.

---

### 2.4 ADR-026: Search Architecture

**Core Responsibilities**:
- Introduce search as read-only CQRS query operation
- Search within current project scope only (no cross-project search)
- Cover field metadata (labels, IDs, entity names) and field values
- Respect domain visibility rules (hidden fields not searchable)
- Return navigation hints (field paths, locations) via data transfer objects

**Affected Layers**:

**Domain Layer**:
- Define search repository interface with query methods for field/value search
- Domain provides searchable data contracts (field definitions, values, visibility)
- No search logic in domain (searching is infrastructure concern)

**Application Layer**:
- Search query operation accepts search term, returns collection of search results
- Orchestrates: fetch visible fields from schema, query repository, map to data transfer objects
- Filtering: apply visibility rules before returning results
- Ranking: optional relevance ordering (infrastructure concern, not architectural requirement)

**Infrastructure Layer**:
- Search implementation executes search strategy with result limits
- Performance optimization: indexing on commonly searched columns
- Caching strategy: optional query cache for repeated searches

**Presentation Layer**:
- Search presentation component manages search state (query, results, selection)
- Search interface with results list showing field paths
- Navigation: consume navigation hints from data transfer objects, use existing navigation service
- No inline editing from search results (navigation only)

**Required New Components**:
- Search repository interface
- Search query operation
- Search result data transfer object containing field path, label, value, entity, location
- Search implementation
- Search presentation component
- Navigation integration consuming navigation hints

---

### 2.5 ADR-039: Import/Export Data Format

**Core Responsibilities**:
- Define standardized, human-readable, machine-parsable interchange format
- Export complete project state (field values, entities, metadata, overrides) excluding history and undo
- Import creates new project from interchange data after full validation
- Backward compatibility guaranteed (newer versions import older exports)
- Version detection and compatibility handling

**Affected Layers**:

**Domain Layer**:
- No changes (domain unaware of interchange format)
- Validation rules apply to imported data (same validation as manual entry)

**Application Layer**:
- Export operation: fetches project data, serializes to interchange format, writes file
- Import operation: parses interchange file, validates data, creates project via existing operations
- Validation: all imported data passes through domain validation before project creation
- Atomic import: entire project created or none (Unit of Work coordination)

**Infrastructure Layer**:
- Export service: serializes project to interchange format
- Import service: parses interchange format, validates schema version
- Interchange format: human-readable, machine-parsable with schema metadata
- Schema inclusion: export includes schema metadata for validation
- Version handling: detect version mismatches, apply compatibility rules
- Error reporting: specific feedback on validation failures during import

**Presentation Layer**:
- Export interface for destination selection and confirmation
- Import interface for file selection, data preview, and confirmation
- Export presentation component manages export workflow
- Import presentation component manages import workflow
- Progress indication: export/import operations may take time for large projects
- Error display: show validation errors from import with actionable feedback

**Required New Components**:
- Export and import operations in application layer
- Export and import services in infrastructure layer
- Interchange format specification
- Version compatibility matrix
- Validation error mapping (domain errors to user-friendly messages)
- Export and import presentation components
- Export and import interfaces with progress indicators

**Critical Considerations**:
- Export excludes: field history (ADR-027), undo stack (ADR-031) - these are internal audit/session data
- Import validation: same rigor as manual data entry (no validation bypass)
- Atomic operations: import uses Unit of Work for transactional integrity
- Backward compatibility: schema evolution must not break older exports
- Forward compatibility: not guaranteed (older versions may not import newer exports)

---

## 3. Risk & Complexity Assessment

### 3.1 High-Risk Areas

**ADR-025 (Validation Severity)**:
- **Risk**: Breaking change to validation result structure affects all validation consumers
- **Mitigation**: Migrate domain first, then application, then presentation (phased rollout)
- **Risk**: Existing validation constraints must be migrated to declare severity
- **Mitigation**: Default to ERROR for all existing constraints (backward compatible behavior)

**ADR-026 (Search)**:
- **Risk**: Performance degradation with large projects (hundreds of entities, thousands of fields)
- **Mitigation**: Result limits, indexing on searchable columns, query optimization
- **Risk**: Search bypassing visibility rules (security concern)
- **Mitigation**: Application layer filters results through domain visibility logic before returning

**ADR-027 (Field History)**:
- **Risk**: Unbounded history growth (large projects, long lifetimes)
- **Mitigation**: No retention policy in v1 (history grows indefinitely), consider pagination for display
- **Risk**: Asynchronous recording failures silently drop history entries
- **Mitigation**: Log failures, no retry mechanism in v1 (best-effort recording)

**ADR-031 (Undo Persistence)**:
- **Risk**: Serialized undo stack incompatible with newer command versions
- **Mitigation**: Best-effort restoration, fallback to empty stack, project still accessible
- **Risk**: Corrupted undo data prevents project open
- **Mitigation**: Undo restoration failure is non-fatal (log error, clear undo, continue)

**ADR-039 (Import/Export)**:
- **Risk**: Data loss during export (incomplete serialization)
- **Mitigation**: Export validation (verify export contains all expected data before write)
- **Risk**: Validation bypass during import (malicious or malformed data)
- **Mitigation**: All imported data passes through domain validation, atomic import (all or nothing)

---

### 3.2 Data Migration Concerns

**ADR-025**:
- No database migration (severity is in-memory concept)
- Code migration: all validation result construction sites must specify severity
- Test migration: validation tests must verify severity behavior

**ADR-027**:
- New storage table for history (requires database migration script)
- Existing projects: empty history initially (no backfill from existing data)
- Backward compatibility: older application versions ignore new storage table

**ADR-031**:
- New storage table for undo stack (requires database migration script)
- Existing projects: empty undo stack initially (no reconstruction of pre-persistence undo state)
- Backward compatibility: older application versions ignore new storage table

**ADR-026**:
- No new storage tables (search queries existing schema and project data)
- Optional: add indexes on frequently searched columns (performance optimization, not required)

**ADR-039**:
- No database migration (import/export operates on files, not database schema)
- Schema version tracking: exports include version metadata for compatibility checking

---

### 3.3 Performance-Sensitive Points

**ADR-025**:
- Negligible performance impact (severity is lightweight enumeration, no additional queries)

**ADR-026**:
- **Query Performance**: Text search queries can be slow without indexes
- **Result Limits**: Large result sets (hundreds of matches) degrade UI responsiveness
- **Mitigation**: Limit results to 50-100 matches, add indexes on searchable columns, consider query cache

**ADR-027**:
- **Write Amplification**: Every field change generates a history entry
- **Query Performance**: History queries for long-lived fields (hundreds of changes) may be slow
- **Mitigation**: Asynchronous recording (non-blocking), indexed queries, pagination in display

**ADR-031**:
- **Serialization Overhead**: Serializing undo stack on every save adds latency
- **Restoration Time**: Deserializing large undo stacks (100+ commands) may be slow
- **Mitigation**: Minimal serialization (command state only), cap undo stack size (100 commands max), async restoration

**ADR-039**:
- **Export Time**: Serializing large projects (1000+ fields, 100+ entities) may take seconds
- **Import Validation**: Validating all imported data before project creation adds latency
- **File Size**: Large projects may generate multi-megabyte export files
- **Mitigation**: Progress indicators, async export/import operations, file compression (optional v2+)

---

### 3.4 Recovery and Failure Scenarios

**ADR-025**:
- **Scenario**: Migration to severity system incomplete (some validators not updated)
- **Recovery**: Validation errors (missing severity parameter) fail fast during development, tests catch missing severity

**ADR-026**:
- **Scenario**: Search query performance degrades with large projects
- **Recovery**: Result limits prevent UI freeze, user sees results truncation indication

**ADR-027**:
- **Scenario**: History recording fails (database write error)
- **Recovery**: Log error, continue primary operation (history recording is best-effort, not critical)
- **Scenario**: History storage corrupted
- **Recovery**: History queries fail gracefully, no impact on project access or editing

**ADR-031**:
- **Scenario**: Undo stack restoration fails (corrupted data, version incompatibility)
- **Recovery**: Clear undo stack, log error, allow project to open with empty undo history
- **Scenario**: Undo persistence fails during save
- **Recovery**: Log error, save continues (undo persistence is best-effort), undo stack lost on next restart

**ADR-039**:
- **Scenario**: Export fails midway (disk full, write permission error)
- **Recovery**: Delete partial export file, show error to user, allow retry
- **Scenario**: Import validation fails (malformed data, constraint violations)
- **Recovery**: No project created (atomic import), show specific validation errors to user, allow correction
- **Scenario**: Import succeeds but project is corrupted (validation missed edge case)
- **Recovery**: User deletes imported project, reports bug, developers fix validation logic

---

## 4. Testing Strategy

### 4.1 Test Categories

**Unit Tests**:
- Domain layer: All new value objects, validation logic, repository interfaces
- Application layer: Operation handlers, event handlers, mapping logic
- Infrastructure layer: Repository implementations with isolated persistence layer
- Presentation layer: Presentation components with mocked application services

**Integration Tests**:
- Repository operations with persistence layer
- Event handler coordination (domain event to history recording)
- Search queries across schema and project data
- Import/export round-trip (export project, import, verify equivalence)

**Property-Based Tests**:
- Validation severity: all constraints produce valid severity values
- Search: all searchable fields discoverable via search
- History: all domain events produce corresponding history entries
- Undo persistence: serialize, deserialize, equivalence
- Import/export: export, import, data equivalence

**Migration Tests**:
- ADR-027: Verify history storage table creation on old project open
- ADR-031: Verify undo storage table creation on old project open
- Backward compatibility: Old application ignores new storage tables, no errors

---

### 4.2 Critical Edge Cases per ADR

**ADR-025 (Validation Severity)**:
- Multiple ERROR-severity failures block generation
- WARNING-only failures allow generation after confirmation
- Mixed ERROR and WARNING failures block generation (ERROR takes precedence)
- INFO-only validation results never block or require confirmation
- Pre-generation checklist correctly categorizes failures by severity

**ADR-026 (Search)**:
- Search respects field visibility (hidden fields not in results)
- Search handles special characters in query (quotes, wildcards)
- Search result navigation to deeply nested fields (entity collections)
- Empty search results (no matches found)
- Result truncation (more than 100 matches)

**ADR-027 (Field History)**:
- History entries created for: user edits, formula recomputation, override acceptance, control effects, undo/redo
- History survives project save/reopen
- History cleared when project deleted
- History queries for fields with zero changes (empty result)
- History queries for fields with 100+ changes (pagination)
- Asynchronous recording failure does not block primary operation

**ADR-031 (Undo Persistence)**:
- Undo stack survives application restart
- Undo stack survives project save/reopen
- Undo stack cleared on explicit project close
- Undo restoration failure does not prevent project open
- Undo stack with 100 commands serializes/deserializes correctly
- Version incompatibility handled gracefully (empty stack fallback)

**ADR-039 (Import/Export)**:
- Export includes all field values, entities, metadata, overrides
- Export excludes field history and undo stack
- Import creates new project (not modifying existing)
- Import validation catches: invalid field types, constraint violations, missing required fields
- Backward compatibility: newer application imports older export
- Forward compatibility warning: older application detects newer export version, shows error
- Atomic import: validation failure prevents project creation (no partial import)
- Round-trip equivalence: export, import, verify data matches original

---

### 4.3 Validation of Backward Compatibility

**ADR-025**:
- Test: Existing validation tests pass without modification (severity defaults to ERROR)
- Test: Pre-severity validation results can coexist with severity-aware results

**ADR-027**:
- Test: Old projects open successfully (history storage table created automatically)
- Test: Old application version opens project with history storage table (ignores it, no errors)

**ADR-031**:
- Test: Old projects open successfully (undo storage table created automatically)
- Test: Old application version opens project with undo storage table (ignores it, no errors)

**ADR-026**:
- No backward compatibility concerns (search is new feature, no migration)

**ADR-039**:
- Test: Current version imports exports from Phase A (pre-Near-Term features)
- Test: Current version detects incompatible future exports, shows version error
- Test: Graceful degradation: import from older version with missing fields (defaults applied)

---

## 5. Completion Criteria

### 5.1 ADR-025 (Validation Severity Levels)

**Observable Behaviors**:
- [ ] Pre-generation checklist visually distinguishes ERROR, WARNING, INFO validation results
- [ ] Document generation blocked if any ERROR-severity failures exist
- [ ] Document generation allowed after user confirmation if only WARNING-severity failures exist
- [ ] Document generation proceeds without confirmation if only INFO-severity notifications exist
- [ ] Validation result messages show severity indicator
- [ ] All existing validation tests pass with severity support

**Technical Verification**:
- [ ] Domain layer: severity value object defined with three levels
- [ ] Domain layer: validation result includes severity per failure
- [ ] Application layer: generation operations check severity before proceeding
- [ ] Presentation layer: data transfer object exposes severity
- [ ] Zero architectural violations (ADR-024 scan passes)

---

### 5.2 ADR-027 (Field History Storage)

**Observable Behaviors**:
- [ ] User can view change history for any field (timestamp, old value, new value, change source)
- [ ] History includes: manual edits, formula recomputation, override acceptance, control effects, undo/redo
- [ ] History survives project save and reopen
- [ ] History cleared when project deleted (no orphaned history)
- [ ] History display shows indication for fields with zero history
- [ ] History recording does not block or slow down primary field operations

**Technical Verification**:
- [ ] Domain layer: history entry value object defined
- [ ] Domain layer: history repository interface defined
- [ ] Application layer: event handlers record history from domain events
- [ ] Infrastructure layer: history storage table exists with indexes
- [ ] Infrastructure layer: history persistence implementation with append-only storage
- [ ] Presentation layer: history presentation components display history
- [ ] Zero architectural violations (ADR-024 scan passes)

---

### 5.3 ADR-031 (Undo History Persistence)

**Observable Behaviors**:
- [ ] Undo stack survives application restart (user can undo after closing and reopening application)
- [ ] Undo stack survives project save (user can undo after saving)
- [ ] Undo stack cleared on explicit project close (new session starts with empty stack)
- [ ] Undo restoration failure does not prevent project open (user sees error, empty stack)
- [ ] Undo/redo interface works identically before and after undo persistence (transparent to user)

**Technical Verification**:
- [ ] Application layer: undo persistence operations implemented (save, restore, clear)
- [ ] Application layer: undo commands support serialization/deserialization
- [ ] Infrastructure layer: undo storage table exists
- [ ] Infrastructure layer: undo persistence implementation
- [ ] Best-effort restoration: corrupted undo data handled gracefully (logged, empty stack)
- [ ] Zero architectural violations (ADR-024 scan passes)

---

### 5.4 ADR-026 (Search Architecture)

**Observable Behaviors**:
- [ ] User can search for fields by label, ID, or entity name
- [ ] Search results show field path, label, current value, location (tab/entity)
- [ ] Clicking search result navigates to that field in interface
- [ ] Search respects field visibility (hidden fields not in results)
- [ ] Search limited to current project (no cross-project search)
- [ ] Empty search query shows no results
- [ ] Search with no matches shows indication

**Technical Verification**:
- [ ] Domain layer: search repository interface defined
- [ ] Application layer: search query operation implemented
- [ ] Application layer: visibility filtering applied before returning results
- [ ] Infrastructure layer: search implementation
- [ ] Presentation layer: search presentation component
- [ ] Navigation integration: search results trigger tab/field navigation
- [ ] Zero architectural violations (ADR-024 scan passes)

---

### 5.5 ADR-039 (Import/Export Data Format)

**Observable Behaviors**:
- [ ] User can export project to file
- [ ] Export file is human-readable (can open in text editor, understand structure)
- [ ] Export file includes all field values, entities, metadata, overrides
- [ ] Export file excludes field history and undo stack
- [ ] User can import project from file
- [ ] Import creates new project (not modifying existing project)
- [ ] Import validation shows specific errors if data invalid
- [ ] Import succeeds only if all data valid (atomic: all or nothing)
- [ ] Backward compatibility: current version imports Phase A exports successfully

**Technical Verification**:
- [ ] Application layer: export and import operations implemented
- [ ] Infrastructure layer: export and import services implemented
- [ ] Interchange format includes schema metadata and version
- [ ] Validation: imported data passes through domain validation before project creation
- [ ] Unit of Work: import uses transactional coordination for atomic project creation
- [ ] Presentation layer: export and import presentation components
- [ ] Round-trip test: export, import, data equivalence verified
- [ ] Zero architectural violations (ADR-024 scan passes)

---

## 6. Cross-Cutting Concerns

### 6.1 DTO-Only MVVM Enforcement (ADR-020)

**Mandatory for All Features**:
- Presentation layer imports only from application data transfer object packages
- No direct domain imports in presentation components or views
- All data transfer via data transfer objects for validation results, history, search results, export/import results
- Mappers are one-way: Domain to DTO (never DTO to Domain)

**Verification**:
- ADR-024 architectural compliance scan passes (zero violations)
- No domain imports in presentation layer

---

### 6.2 Domain Purity (ADR-003)

**Mandatory for All Features**:
- Domain layer has ZERO external dependencies
- No framework, database, file system, or network imports in domain
- Domain defines repository interfaces, infrastructure implements
- Domain validation logic agnostic to where data comes from (manual entry, import, etc.)

**Verification**:
- ADR-024 architectural compliance scan passes (zero violations)
- Domain tests run without external dependencies (in-memory fakes)

---

### 6.3 Unit of Work Coordination (ADR-011)

**Required for**:
- ADR-027: History recording coordinated with primary operation (single transaction)
- ADR-031: Undo persistence coordinated with project save (single transaction)
- ADR-039: Import creates project atomically (all data or none)

**Pattern**:
```
with unit_of_work:
    # Primary operation
    # Append history entry
    # Save undo stack
    unit_of_work.commit()  # All or nothing
```

**Verification**:
- Transactional tests: primary operation plus history/undo persistence atomic
- Rollback tests: failure in one operation rolls back all

---

### 6.4 CQRS Pattern Compliance (ADR-004)

**Commands (Write Operations)**:
- ADR-025: No new commands (extends validation in existing commands)
- ADR-027: Event handler for history recording (not command)
- ADR-031: Undo persistence operations (save, restore, clear)
- ADR-039: Export and import operations

**Queries (Read Operations)**:
- ADR-026: Search query operation (read-only, no side effects)
- ADR-027: History query operation (read-only)

**Verification**:
- Commands modify state, queries do not
- No command returns data (void or status only)
- No query modifies state

---

## 7. Dependencies Summary

### 7.1 External Dependencies

**No New External Libraries Required**:
- All features implemented using existing Python standard library and project dependencies

### 7.2 Internal Dependencies

**ADR-025** depends on:
- Existing validation infrastructure (extends validation result structure)

**ADR-027** depends on:
- ADR-006 (Event Bus) - history recorded from domain events
- ADR-025 (optional) - history entries may include validation context

**ADR-031** depends on:
- ADR-017 (Command-Based Undo) - persistence extends existing undo commands
- ADR-011 (Unit of Work) - atomic undo persistence

**ADR-026** depends on:
- ADR-003 (Framework-Independent Domain) - search respects domain visibility
- ADR-004 (CQRS) - search as read-only query

**ADR-039** depends on:
- All domain entities and validation (export serializes, import validates)
- ADR-011 (Unit of Work) - atomic import
- ADR-007 (Repository Pattern) - repositories provide data for export

---

### 7.3 Implementation Dependencies

| Feature | Depends On | Reason |
|---------|------------|--------|
| ADR-025 | None | Extends existing validation, no new dependencies |
| ADR-027 | ADR-025 | History may include validation context |
| ADR-031 | ADR-025 | Undo commands may interact with validation |
| ADR-026 | ADR-025 | Search may filter by validation state |
| ADR-039 | ADR-025, ADR-027, ADR-031, ADR-026 | Export/import integrates entire system |

**Critical Path**: ADR-025 → (ADR-027, ADR-031, ADR-026) → ADR-039

---

## 8. Approval Gate

**This plan requires explicit approval before implementation begins.**

Upon approval, implementation will proceed in the defined order:
1. ADR-025 (Validation Severity)
2. ADR-027 (Field History)
3. ADR-031 (Undo Persistence)
4. ADR-026 (Search)
5. ADR-039 (Import/Export)

**Checkpoints**:
- After each phase: verify completion criteria met, run ADR-024 compliance scan
- Before next phase: confirm previous phase complete, no architectural violations

**Stop Conditions**:
- Any ADR-024 scan failure: stop, fix violations, re-scan
- Any completion criterion unmet: stop, implement missing behavior, re-verify
- Any high-severity bug discovered: stop, fix bug, add regression test

**Final Approval Required Before Proceeding to Implementation.**

---

**END OF NEAR-TERM IMPLEMENTATION PLAN**

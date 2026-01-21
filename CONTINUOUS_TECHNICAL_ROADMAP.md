# Doc Helper: Continuous Technical Roadmap

**Document Type**: Living Technical Roadmap
**Foundation**: unified_upgrade_plan_FINAL.md
**Date**: 2026-01-21
**Version**: CTR-1.0

---

## 1. CURRENT CAPABILITY MAP

This section describes the current state of U1-U12 capabilities as of 2026-01-21.

**Evidence Sources**:
- unified_upgrade_plan_FINAL.md (normative requirements)
- V1_VERIFIED_STATUS_REPORT.md (implementation evidence)
- Compliance checklists: U1-U12

**Status Terminology**:
- **Implemented**: Capability exists in code, works at least once, may have improvement potential
- **Partially Implemented**: Core exists, some requirements missing/unverified/fragile
- **Planned**: Not implemented yet, explicitly intended

---

### U1: Dependency Injection & Composition Root
**Status**: Implemented
**Provides**: All services resolve via DI container, constructor injection throughout, no service locator pattern in business logic
**Tests**: 32 (15 unit + 17 integration)
**Evidence**: [U1_COMPLIANCE_CHECKLIST.md](U1_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]

### U1.5: DTO Definitions & Mapping
**Status**: Implemented
**Provides**: 13 DTOs defined, DTO-only MVVM enforced, presentation imports only from `application/dto/ui/`
**Tests**: ADR-024 scan (0 violations)
**Evidence**: Code inspection
**Scope**: [Current Scope]
**Note**: ADR-020 and ADR-024 files missing (referenced but not written)

### U2: i18n Service Implementation
**Status**: Implemented
**Provides**: English/Arabic translation loading, dynamic language switching without restart
**Tests**: 22 unit
**Evidence**: [U2_COMPLIANCE_CHECKLIST.md](U2_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]

### U3: Project View Completion
**Status**: Implemented
**Provides**: Dynamic form rendering from schema, no domain imports in presentation, tab navigation
**Tests**: 16 unit
**Evidence**: [U3_COMPLIANCE_CHECKLIST.md](U3_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]

### U4: Widget Factory Pattern
**Status**: Implemented
**Provides**: Registry-based factory for all 12 field types (TEXT, TEXTAREA, NUMBER, DATE, DROPDOWN, CHECKBOX, RADIO, CALCULATED, LOOKUP, FILE, IMAGE, TABLE)
**Tests**: 16 (merged into U3)
**Evidence**: [U4_COMPLIANCE_CHECKLIST.md](U4_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]

### U5: Recent Projects & Settings
**Status**: Implemented
**Provides**: Recent projects tracking (last 5), settings dialog with language selector, persistence across sessions
**Tests**: 18 unit
**Evidence**: [U5_COMPLIANCE_CHECKLIST.md](U5_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]

### U6: Undo/Redo System
**Status**: Implemented
**Provides**: Command-based undo for field edits and override operations, temporal tests T1-T5 pass, explicit state capture, computed values recomputed on undo, stack cleared on project close/open (NOT on save)
**Tests**: 103 total
**Evidence**: [U6_UNDO_SYSTEM_COMPLETE.md](U6_UNDO_SYSTEM_COMPLETE.md)
**Scope**: [Current Scope]
**Improvement Potential**: Undo for schema changes, override bulk operations, control rule edits

### U7: Tab Navigation & Menu Bar
**Status**: Implemented
**Provides**: Tab history (back/forward), menu bar (File/Edit/View/Help), keyboard shortcuts
**Tests**: 64 automated + 13 manual
**Evidence**: [U7_COMPLIANCE_CHECKLIST.md](U7_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]

### U8: Legacy Behavior Parity
**Status**: Implemented
**Provides**: Auto-save before document generation, override cleanup (SYNCED state deleted, SYNCED_FORMULA preserved), cross-tab formula references
**Tests**: 16 automated
**Evidence**: [U8_COMPLIANCE_CHECKLIST.md](U8_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]
**Note**: Manual side-by-side comparison with legacy app recommended (4-6 hours, LOW risk)

### U9: File Context & Figure Numbering
**Status**: Implemented
**Provides**: File upload/preview, figure numbering with customizable formats, caption generation (Figure, Image, Plan, Section, Table, Chart, Appendix), drag-to-reorder
**Tests**: ~150 automated + 16 manual
**Evidence**: [U9_COMPLIANCE_CHECKLIST.md](U9_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]

### U10: RTL Layout & i18n Polish
**Status**: Implemented
**Provides**: Arabic UI mirroring, right-to-left text alignment, complete translation coverage for all UI strings, layout direction updates immediately on language change
**Tests**: 41 (26 unit + 15 integration)
**Evidence**: [U10_COMPLIANCE_CHECKLIST.md](U10_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]

### U11: Missing Dialogs
**Status**: Implemented
**Provides**: 4 dialogs (Template Selection, Override Management, Conflict Resolution, Pre-Generation Checklist)
**Tests**: 53 unit
**Evidence**: [U11_COMPLIANCE_CHECKLIST.md](U11_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]

### U12: Integration & Testing
**Status**: Implemented
**Provides**: End-to-end workflows, legacy parity verification, integration test suite, DTO-only MVVM verified
**Tests**: 1,088+ total (894 unit + 178 integration + 16 E2E)
**Evidence**: [U12_COMPLIANCE_CHECKLIST.md](U12_COMPLIANCE_CHECKLIST.md)
**Scope**: [Current Scope]

---

### Summary Metrics

- **Total Tests**: 1,088+ (894 unit + 178 integration + 16 E2E)
- **Overall Coverage**: 82% (exceeds 80% target)
- **Domain Layer Coverage**: 90%+ (exceeds 90% target)
- **Architectural Violations**: 0 (ADR-024 scan)

### Functional Capabilities (Implemented)

- Project CRUD (create/open/save/close)
- 12 field types rendering and validation
- Dynamic form generation from schema
- Validation system (required, numeric, text, date constraints)
- Formula system (template syntax, cross-tab references, dependency tracking)
- Control system (VALUE_SET, VISIBILITY, ENABLE)
- Override system (state machine: PENDING → ACCEPTED → SYNCED)
- File management (upload, preview, figure numbering, captions)
- Document generation (Word/Excel/PDF, 18+ transformers)
- Undo/Redo (field edits + override operations, T1-T5 verified)
- Internationalization (English/Arabic, RTL layout, dynamic switching)
- Recent projects tracking (last 5)
- Tab navigation (back/forward history)
- Menu bar (File/Edit/View/Help with keyboard shortcuts)

### Architectural Patterns (Implemented)

**DTO-Only MVVM**:
- Presentation imports ONLY from `application/dto/ui/`
- Zero domain imports in presentation (verified by ADR-024 scan)
- UndoState DTOs isolated in `application/undo/` (internal only)

**Command-Based Undo**:
- Explicit UndoCommand pattern with `execute()` and `undo()`
- State captured BEFORE operations
- Computed values RECOMPUTED on undo (not restored)
- Stack cleared on project close/open, NOT on save

**Clean Architecture**:
- Domain has zero external dependencies
- Dependencies point inward: Presentation → Application → Domain ← Infrastructure
- 0 layer violations (ADR-024 scan)

**One-Way Mappers**:
- Mappers: Domain → DTO only
- NO DTO → Domain mapping

---

## 2. INTERNAL BASELINE: POST PHASE A (2026-01-21)

**Status**: Architecture Stabilized

This marker represents the completion of Phase A (U1-U12) and establishes a stable internal baseline before Near-Term Expansion. This is NOT a release.

**Achievements**:
- All 12 upgrade units implemented and tested
- 1,088+ tests passing (894 unit + 178 integration + 16 E2E)
- 82% overall coverage, 90%+ domain layer coverage
- Zero architectural violations (ADR-024 verified)
- SqliteOverrideRepository implemented (persistent override storage)
- Core services hardened (control_service 100%, validation_service 100%, formula_service 97%)

**Architecture State**:
- Clean Architecture with DDD patterns established (ADR-002, ADR-003)
- Framework-independent domain layer verified (no PyQt6/SQLite imports in domain)
- DTO-Only MVVM pattern enforced (ADR-020, 0 violations detected)
- Repository pattern with SQLite persistence (ADR-007)
- Command-based undo system implemented (ADR-017, ADR-021)
- All 13 foundational ADRs accepted and implemented

**Functional Capabilities**:
- All 12 field types working (TEXT, TEXTAREA, NUMBER, DATE, DROPDOWN, CHECKBOX, RADIO, CALCULATED, LOOKUP, FILE, IMAGE, TABLE)
- 5 core systems functional (validation, formula, control, override, file management)
- Full i18n support (English/Arabic with RTL layout)
- Undo/Redo for field value changes (T1-T5 temporal tests verified)
- Recent projects tracking (last 5 projects)
- Dynamic form rendering from schema
- Document generation (Word/Excel/PDF with 18+ transformers)
- Tab navigation with back/forward history
- Menu bar with keyboard shortcuts (File/Edit/View/Help)

**Recent Completions** (Post-U12):
- **ADR-020: DTO-Only MVVM Enforcement** (file created, formalizes existing practice)
- **ADR-024: Architectural Compliance Scanning** (file created, documents scan tool)
- **SqliteOverrideRepository** (persistent storage, replaces FakeOverrideRepository)
- **Test Coverage Hardening** (control_service 100%, validation_service 100%, formula_service 97%)

**Next Phase**: Near-Term Expansion (awaiting authorization)

---

## 3. ACTIVE IMPROVEMENT BACKLOG

This section lists enhancements, gaps, and refinements for existing U1-U12 capabilities.

**Rule**: If it improves or completes something that already exists, it belongs here.

---

### 3.1 Missing/Incomplete Implementations

**CLOSED: SqliteOverrideRepository** (Completed 2026-01-21):
- ✅ Implemented persistent SQLite-based override repository
- ✅ Replaced in-memory `FakeOverrideRepository`
- ✅ All 7 interface methods implemented with 100% test coverage
- ✅ Database schema with proper indexes created
- ✅ Override state now persists across application restarts
- **Evidence**: [sqlite_override_repository.py](src/doc_helper/infrastructure/persistence/sqlite_override_repository.py), [test_sqlite_override_repository.py](tests/unit/infrastructure/persistence/test_sqlite_override_repository.py)

**CLOSED: Missing ADR Documentation** (Completed 2026-01-21):
- ✅ **ADR-020: DTO-Only MVVM Enforcement**: File created, formalizes presentation layer import restrictions
- ✅ **ADR-024: Architectural Compliance Scanning**: File created, documents static analysis for layer violations
- **Status**: Both ADRs written and referenced, marked as "Proposed" (pending formal acceptance review)
- **Evidence**: [ADR-020](adrs/ADR-020-dto-only-mvvm.md), [ADR-024](adrs/ADR-024-architectural-compliance-scanning.md)

---

### 3.2 Test Coverage Gaps

**CLOSED: Test Coverage Hardening** (Completed 2026-01-21):

**control_service.py: 61% → 100% coverage** ✅:
- ✅ Added 14 new tests covering evaluate_by_project_id, ENABLE effects, VALUE_SET effects
- ✅ All error paths, type validation, and edge cases covered
- ✅ 21 total tests passing (7 original + 14 new)
- **Evidence**: [test_control_service_extended.py](tests/unit/application/services/test_control_service_extended.py)

**validation_service.py: 65% → 100% coverage** ✅:
- ✅ Added 14 new tests covering validate_by_project_id, orphaned fields, type validation
- ✅ All error paths and edge cases covered
- ✅ 22 total tests passing (8 original + 14 new)
- **Evidence**: [test_validation_service_extended.py](tests/unit/application/services/test_validation_service_extended.py)

**formula_service.py: 78% → 97% coverage** ✅:
- ✅ Added 16 new tests covering type validation, circular dependencies, AST node extraction
- ✅ Edge cases and error propagation covered
- ✅ 25 total tests passing (9 original + 16 new)
- **Evidence**: [test_formula_service_extended.py](tests/unit/application/services/test_formula_service_extended.py)

**Result**: All three services EXCEED 85% target (97-100% coverage achieved)

---

### 3.3 Verification & Hardening

**U8 Legacy Comparison**:
- **Task**: Manual side-by-side comparison with legacy app
- **Focus**: Auto-save behavior, override cleanup, cross-tab formula edge cases
- **Risk**: LOW (high confidence from 16 automated tests)
- **Priority**: Recommended but not blocking
- **Effort**: 4-6 hours

**Undo Edge Cases**:
- **Task**: Strengthen undo for complex formula chains
- **Task**: Test undo with concurrent control effects
- **Task**: Verify undo with FILE/IMAGE fields
- **Priority**: Low
- **Effort**: ~2 days

---

### 3.4 Performance & Polish

**Formula Evaluation Performance**:
- **Task**: Profile formula evaluation with large dependency graphs
- **Task**: Optimize recomputation strategy (incremental vs full)
- **Priority**: Low (no reported issues yet)
- **Effort**: ~3-5 days

**UI Responsiveness**:
- **Task**: Audit long-running operations for async execution
- **Task**: Add progress indicators for document generation
- **Priority**: Low
- **Effort**: ~2-3 days

**Translation Coverage Audit**:
- **Task**: Native Arabic speaker review of translations
- **Task**: RTL layout edge case testing (nested components)
- **Priority**: Low
- **Effort**: ~1-2 days

---

### 3.5 Refactoring Opportunities

**Service Layer Simplification**:
- Some services have overlapping responsibilities
- Candidate: Split `ValidationService` batch vs single validation
- Candidate: Extract common formula dependency resolution
- **Priority**: Very Low
- **Effort**: ~5-7 days

**DTO Consistency**:
- Some DTOs have inconsistent naming (`DTO` suffix vs no suffix)
- Some DTOs duplicate fields across UI/Undo boundaries
- **Priority**: Very Low
- **Effort**: ~2-3 days

---

## 4. NEAR-TERM EXPANSION

This section lists new capabilities not defined in U1-U12, conceptually close to current scope.

**Source**: Features explicitly marked as "v2" or "future work" in unified_upgrade_plan_FINAL.md

**Rule**: If it introduces a fundamentally new concept, it belongs here.

**Scope**: [Near-Term Expansion]

---

### 4.1 Infrastructure Extensions

**Unit of Work Pattern Implementation**:
- Finalize transaction boundaries (ADR-011)
- Multi-repository atomic commits
- Rollback support for complex operations
- **Priority**: High
- **Effort**: ~5-7 days

**SqliteOverrideRepository** (moved from Improvement):
- If treated as new persistence capability rather than completion
- Could include: query optimization, indexing, migration support
- **Priority**: High
- **Effort**: ~7-10 days (extended implementation)

---

### 4.2 UX Enhancements

**Validation Severity Levels**:
- ERROR / WARNING / INFO distinction
- UI color-coded indicators (red/yellow/blue)
- Pre-generation checklist distinguishes errors (blocking) from warnings (can proceed)
- **ADR Required**: ADR-025
- **Priority**: High
- **Effort**: ~7-10 days

**Quick Search (Ctrl+F)**:
- Global search across all fields
- Search field labels and values
- Jump to matching fields in UI
- Search history
- **ADR Required**: ADR-026
- **Priority**: High
- **Effort**: ~5-7 days

**Field History Viewing UI**:
- Per-field change history popover
- Display: timestamp, old value, new value, source (user/formula/control)
- Revert to previous value option
- **ADR Required**: ADR-027
- **Priority**: Medium
- **Effort**: ~7-10 days

**Dark Mode / Theme Switching**:
- `IThemeProvider` interface with light/dark implementations
- Theme preference persisted in user settings
- Dynamic stylesheet switching
- All custom widgets support both themes
- **Priority**: Medium
- **Effort**: ~10-15 days

**Auto-Save Recovery Mechanism**:
- Periodic auto-save to temp storage
- Crash recovery on restart
- Configurable auto-save interval (default: 30 seconds)
- **Priority**: Medium
- **Effort**: ~5-7 days

**Full Keyboard Navigation Adapter**:
- Alt+[letter] shortcuts for all menu items
- Ctrl+Tab to switch between entities
- Arrow keys for field navigation within entity
- **Priority**: Low
- **Effort**: ~3-5 days

---

### 4.3 Data Operations

**Import from Excel**:
- Map Excel columns to field definitions
- Column mapping UI with preview
- Bulk create projects from spreadsheet rows
- Validation before import
- **ADR Required**: ADR-039
- **Priority**: High
- **Effort**: ~10-15 days

**Export Project Data**:
- Serialize project to JSON/Excel/CSV
- User selects entities and fields to export
- Export template saved for reuse
- Useful for data analysis, reporting, backup
- **ADR Required**: ADR-039
- **Priority**: High
- **Effort**: ~7-10 days

**Clone Project**:
- Create deep copy of project
- Option to clone with/without document outputs
- Useful for creating similar projects (e.g., adjacent sites)
- **Priority**: Medium
- **Effort**: ~5-7 days

---

### 4.4 Document Features

**Document Version History Tracking**:
- Track: timestamp, template version, output path, transformer config
- List all versions for a project
- Regenerate from previous version
- Compare outputs between versions
- **Priority**: High
- **Effort**: ~10-15 days

**Smart Output Naming with Tokens**:
- `{project_name}`, `{date}`, `{version}`, `{entity:field_name}`
- Example: `{project_name}_SoilReport_{date:YYYY-MM-DD}_v{version}.docx`
- UI for editing naming patterns per app type
- **Priority**: Medium
- **Effort**: ~5-7 days

**Template Variables**:
- Calculated template variables (beyond simple field mapping)
- Example: `total_samples = COUNT(borehole_records)`
- Template expressions evaluated at generation time
- **Priority**: Low
- **Effort**: ~7-10 days

**Conditional Document Sections**:
- Show/hide document sections based on field values
- Example: Only include "Contamination Analysis" if contamination detected
- Defined in template metadata or app type manifest
- **Priority**: Low
- **Effort**: ~7-10 days

---

### 4.5 Undo/Redo Extensions

**Undo for Schema Changes**:
- Add/remove fields
- Modify field properties
- Add/remove entities
- **Priority**: Medium
- **Effort**: ~10-15 days

**Undo for Override Bulk Operations**:
- Accept/reject multiple overrides at once
- Undo entire batch as one operation
- **Priority**: Medium
- **Effort**: ~5-7 days

**Undo for Control Rule Edits**:
- Add/modify/delete control rules
- Undo rule changes
- **Priority**: Low
- **Effort**: ~5-7 days

**Undo History Persistence**:
- Save/restore undo stack with project
- Undo survives project close/reopen
- **ADR Required**: ADR-031
- **Priority**: Medium
- **Effort**: ~7-10 days

**Undo History Visualization**:
- Timeline view of changes
- Branch visualization for complex undo trees
- **ADR Required**: ADR-031
- **Priority**: Low
- **Effort**: ~10-15 days

**Named Checkpoints**:
- "Save checkpoint before major edit"
- Jump to named checkpoints in undo history
- **ADR Required**: ADR-033
- **Priority**: Low
- **Effort**: ~5-7 days

**Selective Undo**:
- Undo specific change without undoing later changes
- Conflict detection and resolution
- **ADR Required**: ADR-032
- **Priority**: Low
- **Effort**: ~15-20 days

---

### 4.6 Test Coverage Improvements

**Deep Chain Control Propagation Tests**:
- Test control chains with depth > 5
- Verify cycle detection at extreme depths
- **Priority**: Medium
- **Effort**: ~3-5 days

**Batch Validation Tests**:
- Validate multiple fields/entities at once
- Test validation performance with large batches
- **Priority**: Medium
- **Effort**: ~2-3 days

**Circular Dependency Edge Case Tests**:
- Complex circular formula scenarios
- Multiple overlapping cycles
- **Priority**: Medium
- **Effort**: ~2-3 days

---

## 5. LONG-TERM EXPANSION

This section lists architectural leaps and capabilities significantly beyond current scope.

**Source**: Features NOT explicitly mentioned in unified_upgrade_plan_FINAL.md

**Scope**: [Long-Term Expansion]

---

### 5.1 Multi-App-Type Platform

**Vision**: Transform Doc Helper from single-purpose to universal document generation platform.

**Components**:
- `AppTypeInfo` aggregate (app type metadata)
- `IAppTypeRegistry` (register/query available types)
- `AppTypeDiscoveryService` (scan `app_types/` for manifest.json)
- Extension loading for custom transformers
- App type selection UI (welcome screen cards)
- Project metadata: `app_type_id` field

**ADRs Required**:
- ADR-028: Multi-App-Type Architecture (expand ADR-013)
- ADR-029: Manifest Schema Specification
- ADR-030: Extension Loading Protocol

**Estimated Effort**: 40-50 days

---

### 5.2 Plugin Architecture

**Components**:
- Plugin manifest schema
- Plugin discovery & loading
- Extension points (custom transformers, validators, field types)
- Plugin SDK & documentation
- Security (sandboxing, permissions, code signing)

**ADRs Required**:
- ADR-034: Plugin Architecture
- ADR-035: Extension Point Protocol
- ADR-036: Plugin Security Model

**Estimated Effort**: 50-70 days

---

### 5.3 Performance & Scaling

**Features**:
- Lazy loading for large projects (>1000 fields)
- Incremental formula evaluation (only changed dependencies)
- Virtual scrolling for large collections
- Background computation for expensive operations
- Memory usage optimization
- Support projects with 10,000+ fields

**ADRs Required**:
- ADR-037: Lazy Loading Strategy
- ADR-038: Unit of Work Implementation (finalize ADR-011)

**Estimated Effort**: 30-40 days

---

### 5.4 Advanced Document Features

**Features**:
- Hierarchical figure numbering (Figure 1.1, 1.2)
- Per-section numbering reset
- Rich text captions
- Caption field references
- File versioning
- File compression
- Cloud storage integration

**Estimated Effort**: 20-30 days per feature cluster

---

### 5.5 Advanced Navigation

**Features**:
- Tree-based history (branching)
- Jump to tab by name
- Navigation bookmarks
- Customizable keyboard shortcuts

**Estimated Effort**: 20-30 days

---

## 6. ADR PIPELINE

This section lists architectural decisions that need formalization.

---

### 6.1 Existing ADRs (15 total)

| ADR | Title | Status | Notes |
|-----|-------|--------|-------|
| ADR-001 | Controlled Big Bang Rewrite Strategy | Accepted | Strategy decision |
| ADR-002 | Clean Architecture + DDD | Accepted | Layer architecture |
| ADR-003 | Framework-Independent Domain Layer | Accepted | Domain purity |
| ADR-004 | CQRS Pattern | Accepted | Command/Query separation |
| ADR-005 | MVVM Pattern | Accepted | Presentation pattern |
| ADR-006 | Event Bus | Accepted | Pub/sub decoupling |
| ADR-007 | Repository Pattern | Accepted | Data access abstraction |
| ADR-008 | Result Monad | Accepted | Error handling |
| ADR-009 | Strongly Typed IDs | Accepted | Type safety |
| ADR-010 | Immutable Value Objects | Accepted | Immutability |
| ADR-011 | Unit of Work | Accepted | Transaction management |
| ADR-012 | Registry-Based Factory | Accepted | Extensibility pattern |
| ADR-013 | Multi-Document-Type Platform Vision | Proposed | Vision (for long-term) |
| ADR-017 | Command-Based Undo | Accepted | Undo system |
| ADR-021 | UndoState DTO Isolation | Accepted | DTO separation |

---

### 6.2 Missing ADRs (Immediate Need)

**CLOSED: ADR-020 and ADR-024** (Completed 2026-01-21):

**ADR-020: DTO-Only MVVM Enforcement** ✅:
- **Status**: File created, marked as "Proposed" (pending formal acceptance review)
- **Decision Scope**: Formalize presentation layer import restrictions
- **Content**: Documents DTO-Only MVVM pattern, presentation imports only from `application/dto/ui/`, enforcement via ADR-024 scan
- **Evidence**: [ADR-020-dto-only-mvvm.md](adrs/ADR-020-dto-only-mvvm.md)

**ADR-024: Architectural Compliance Scanning** ✅:
- **Status**: File created, marked as "Proposed" (pending formal acceptance review)
- **Decision Scope**: Static analysis for layer violations
- **Content**: Documents compliance scanning tool, checks domain purity, DTO-only MVVM, repository pattern compliance
- **Evidence**: [ADR-024-architectural-compliance-scanning.md](adrs/ADR-024-architectural-compliance-scanning.md)

**Note**: Both ADRs are functionally complete and enforced in practice. Status update from "Proposed" to "Accepted" requires explicit approval.

---

### 6.3 Required ADRs - Near-Term Expansion

**ADR-025: Validation Severity Levels** ✅:
- **Status**: Accepted (2026-01-21)
- **Decision Scope**: ERROR/WARNING/INFO distinction
- **Priority**: High
- **Depends On**: -
- **Next Step**: Implementation pending

**ADR-026: Search Architecture** ✅:
- **Status**: Accepted (2026-01-21)
- **Decision Scope**: Global search across fields (read-only CQRS query)
- **Priority**: High
- **Depends On**: -
- **Next Step**: Implementation pending

**ADR-027: Field History Storage** ✅:
- **Status**: Accepted (2026-01-21)
- **Decision Scope**: Per-field change tracking
- **Priority**: Medium
- **Depends On**: ADR-011
- **Next Step**: Implementation pending

**ADR-039: Import/Export Data Format** ✅:
- **Status**: Accepted (2026-01-21)
- **Decision Scope**: Standardized data interchange format
- **Priority**: High
- **Depends On**: ADR-007, ADR-011, ADR-004
- **Next Step**: Implementation pending

**ADR-031: Undo History Persistence** ✅:
- **Status**: Accepted (2026-01-21)
- **Decision Scope**: Save/restore undo stack with project
- **Priority**: Medium
- **Depends On**: ADR-017, ADR-011
- **Next Step**: Implementation pending

**ADR-032: Selective Undo Algorithm**:
- **Decision Scope**: Undo specific change without undoing later
- **Priority**: Low
- **Depends On**: ADR-017
- **Timing**: Before implementing selective undo

**ADR-033: Checkpoint System**:
- **Decision Scope**: Named save points in undo history
- **Priority**: Low
- **Depends On**: ADR-031
- **Timing**: Before implementing checkpoints

---

### 6.4 Required ADRs - Long-Term Expansion

**ADR-028: Multi-App-Type Architecture**:
- **Decision Scope**: Expand ADR-013 with implementation
- **Priority**: Medium
- **Depends On**: ADR-013
- **Timing**: Before implementing multi-app platform

**ADR-029: Manifest Schema Specification**:
- **Decision Scope**: manifest.json structure
- **Priority**: Medium
- **Depends On**: ADR-028
- **Timing**: Before implementing app type discovery

**ADR-030: Extension Loading Protocol**:
- **Decision Scope**: Custom transformer/validator loading
- **Priority**: Medium
- **Depends On**: ADR-028
- **Timing**: Before implementing extensions

**ADR-034: Plugin Architecture**:
- **Decision Scope**: Plugin discovery, loading, lifecycle
- **Priority**: Low
- **Depends On**: ADR-028
- **Timing**: Before implementing plugins

**ADR-035: Extension Point Protocol**:
- **Decision Scope**: Plugin component registration
- **Priority**: Low
- **Depends On**: ADR-034
- **Timing**: Before implementing extension points

**ADR-036: Plugin Security Model**:
- **Decision Scope**: Sandboxing, permissions, code signing
- **Priority**: Low
- **Depends On**: ADR-034
- **Timing**: Before implementing plugin security

**ADR-037: Lazy Loading Strategy**:
- **Decision Scope**: Load data on-demand for large projects
- **Priority**: Low
- **Depends On**: -
- **Timing**: Before implementing performance optimizations

**ADR-038: Unit of Work Implementation**:
- **Decision Scope**: Finalize transaction boundaries
- **Priority**: Medium
- **Depends On**: ADR-011
- **Timing**: Before implementing UoW pattern

---

### 6.5 ADR Writing Priority

**Immediate** (Critical for current scope):
1. ADR-020: DTO-Only MVVM Enforcement
2. ADR-024: Architectural Compliance Scanning

**Before Near-Term Expansion**:
3. ADR-025: Validation Severity Levels
4. ADR-026: Search Architecture
5. ADR-039: Import/Export Data Format
6. ADR-027: Field History Storage
7. ADR-031: Undo History Persistence

**Before Long-Term Expansion**:
8. ADR-028-030: Multi-App-Type Platform
9. ADR-034-036: Plugin Architecture
10. ADR-037-038: Performance & Scaling
11. ADR-032-033: Advanced Undo Features

---

## 7. EXECUTION RULES

**Authoritative Source**: [AGENT_RULES.md](AGENT_RULES.md)

All development work MUST comply with AGENT_RULES.md execution discipline.

---

### 7.1 Architectural Constraints (Reference Only)

See AGENT_RULES.md for full rules. Key constraints:

**DTO-Only MVVM**:
- Presentation imports ONLY from `application/dto/ui/`
- NO domain imports in presentation layer
- ADR-024 scan enforces this rule

**Command-Based Undo**:
- Explicit state capture at command creation
- Computed values RECOMPUTED on undo
- Stack cleared on project close/open, NOT on save

**Clean Architecture**:
- Domain has ZERO external dependencies
- Dependencies point inward only
- 0 layer violations required

**Mapper Responsibility**:
- Mappers are one-way: Domain → DTO
- NO DTO → Domain mapping

---

### 7.2 Development Workflow

**Before Implementation**:
- Identify scope: [Current Scope] / [Near-Term Expansion] / [Long-Term Expansion]
- List affected layers: Domain / Application / Infrastructure / Presentation
- Verify no AGENT_RULES.md violations
- Check if ADR exists or needs to be written

**During Implementation**:
- Follow all architectural constraints
- Write tests for all new code
- Maintain compliance with ADRs

**After Implementation**:
- Run full test suite: `.venv/Scripts/python -m pytest tests/ -v`
- Check coverage: `.venv/Scripts/python -m pytest tests/ --cov=src/doc_helper --cov-report=term-missing`
- Run architectural compliance: `.venv/Scripts/python scripts/check_architecture.py`
- Update this roadmap if scope/priorities change

---

### 7.3 Decision Precedence

If conflicts exist, the following order applies (highest to lowest priority):

1. **AGENT_RULES.md** (execution discipline)
2. **This document** (CONTINUOUS_TECHNICAL_ROADMAP.md)
3. **unified_upgrade_plan_FINAL.md** (historical requirements reference)
4. **ADRs referenced in this roadmap**
5. **Deprecated plans** (historical reference only)

**If unclear**: STOP and ask for clarification. Do not guess or infer.

---

## 8. DOCUMENT EVOLUTION

**This document**:
- Is a living technical roadmap
- Evolves continuously as development progresses
- Reflects current state, active work, and planned expansions
- Is NOT a release plan, user manual, or marketing roadmap

**Update Triggers**:
- Capability status changes (new implementations, discovered gaps)
- Priority shifts (urgent needs, user feedback)
- New expansion ideas (architectural discoveries, technology changes)
- ADR completion (new decisions formalized)

**Versioning**:
- CTR-1.0, CTR-1.1, CTR-1.2, etc.
- Version updated when significant scope/priority changes occur
- Minor edits (typos, clarifications) do not trigger version bump

**Authority**:
- Changes require project lead approval
- Changes committed with clear rationale
- This document supersedes all previous plans (MASTER_DEVELOPMENT_PLAN.md, etc.)

---

**Roadmap Version**: CTR-1.0
**Date**: 2026-01-21
**Last Updated**: 2026-01-21 (initial continuous roadmap)
**Next Review**: As needed (continuous evolution)

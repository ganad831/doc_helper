# AGENT_RULES.md

## Purpose
This document defines **non-negotiable execution rules** for any AI or human agent working on the Doc Helper codebase.

If a rule here conflicts with any other instruction, **this file wins**.

---

## 1. VERSION & SCOPE LOCK

- Target version: **Doc Helper v1 (stable) + v2 Platform Work (in progress)**
- v1 Source of truth: **unified_upgrade_plan_FINAL.md**
- v2 Source of truth: **V2_PLATFORM_IMPLEMENTATION_PLAN.md** + v2 ADRs

**v1 Behavior Lock**: All v1 implemented behavior is LOCKED. Changes to v1 behavior require explicit justification via v2 ADR.

**v2 Platform Work**: Authorized as of 2026-01-21. See Section 16 for v2 Platform Work Rules.

---

## 2. ARCHITECTURAL LAYERS (HARD BOUNDARIES)

The system consists of these layers:

- Domain
- Application
- Infrastructure
- Presentation

### Dependency Rules

- Presentation → Application only
- Application → Domain only
- Infrastructure → Domain + Application
- Domain → NOTHING

Any violation is a blocking error.

---

## 3. DTO-ONLY MVVM (NON-NEGOTIABLE)

### Allowed in Presentation

- Application services
- Application DTOs
- UI-specific state models

### Forbidden in Presentation

- Domain entities
- Domain value objects
- Domain enums
- Domain services
- Domain repositories

Domain objects must **never** cross the Application boundary.

---

## 4. DTO RULES

- DTOs are owned by the Application layer
- DTOs are immutable
- DTOs contain **no behavior**
- DTOs are UI-facing data only
- DTOs are NOT persistence models

Two categories of DTOs exist:

1. **UI DTOs** – may be consumed by Presentation
2. **Undo-state DTOs** – internal to Application only

Undo-state DTOs must never reach Presentation.

---

## 5. MAPPING RULES

- Domain → DTO mapping happens ONLY in the Application layer
- Mapping is one-way
- Reverse mapping is forbidden
- DTOs must not be used to rehydrate Domain state

Undo/Redo operates via **application commands**, not DTO reversal.

---

## 6. UNDO / REDO RULES (V1)

### Supported

- Field value edits
- Override state transitions (ACCEPT, REJECT, SYNC)

### Undo Model

- Command-based undo
- Each command captures its own minimal previous state
- Commands push inverse commands onto undo stack

### NOT Supported

- Full project snapshot undo
- Field history UI
- Autosave-based undo

Undo stack behavior:

- Cleared on project open
- Cleared on project close
- NOT cleared on save

---

## 7. COMPUTED VALUES & FORMULAS

- Computed values are NOT stored for undo
- On undo/redo, computed values are recomputed via normal cascades
- Resulting state must match the pre-action state

---

## 8. LEGACY PARITY (MANDATORY)

- All legacy_app behaviors must exist in v1 unless explicitly rejected
- No legacy behavior may leak into Presentation
- Legacy quirks must be normalized in Application or Domain

Parity is verified via automated parity tests.

---

## 9. TESTING REQUIREMENTS (V1)

The following test categories are mandatory:

- DTO mapping unit tests
- Legacy parity tests
- Formula regression tests
- Temporal undo tests, including:
  - Override accept → Undo → Redo
  - Override + field edit → Undo override
  - Override affecting formulas → Undo → recompute

No milestone is complete without passing tests.

---

## 10. NEAR-TERM EXPANSION EXCEPTIONS

The following features are FORBIDDEN in v1 foundation but are
EXPLICITLY AUTHORIZED during Near-Term Expansion when governed
by accepted ADRs and the approved Near-Term Implementation Plan.

Authorized exceptions:
- Validation severity levels (ADR-025)
- Search functionality (ADR-026)
- Field history storage and UI (ADR-027)
- Undo history persistence (ADR-031)
- Import/export data interchange (ADR-039)

Rules:
- These features MUST be implemented strictly according to their ADRs
- No expansion beyond ADR scope is allowed
- v2+ features remain forbidden
- Any feature not listed here is still forbidden


## 11. FORBIDDEN IN V1 (OUTSIDE NEAR-TERM SCOPE)

The following are explicitly forbidden:

- Plugin or extension loading
- App type discovery
- Auto-save or recovery
- Project snapshots or version history
- DTO persistence or API exposure
- Theme switching
- Validation severity levels
- Import/export features

---

## 12. DECISION PRECEDENCE

If a conflict exists:

1. AGENT_RULES.md
2. unified_upgrade_plan_FINAL.md
3. ADRs referenced in the FINAL plan
4. Deprecated plan versions or historical discussions

If unclear, STOP and ask for clarification.

---

## 13. EXECUTION DISCIPLINE

Before implementing any change, the agent MUST:

- Identify the v1 milestone it belongs to
- List affected layers
- Verify no forbidden rule is violated

After implementation, the agent MUST:

- Provide a compliance checklist
- Confirm no v2 features were introduced

---

## 14. ARCHITECTURE FREEZE STATUS

**Status**: INACTIVE (Unfrozen for v2 Platform Work)
**Date Declared**: 2026-01-21
**Date Unfrozen**: 2026-01-21
**Reason**: Begin v2 Platform: Multi-App Support

### Previously Frozen Scope (Now v1 Baseline)

The following architectural decisions were **FROZEN** during v1 development and are now the **v1 BASELINE**:

**Phase A Foundational ADRs** (16 total):
- ADR-001 through ADR-012 (excluding gaps)
- ADR-017, ADR-020, ADR-021, ADR-024

**Near-Term Expansion ADRs** (5 total):
- ADR-025: Validation Severity Levels
- ADR-026: Search Architecture
- ADR-027: Field History Storage
- ADR-031: Undo History Persistence
- ADR-039: Import/Export Data Format

### v1 Baseline Rules (STILL ENFORCED)

**ABSOLUTELY FORBIDDEN** (v1 behavior protection):
- ❌ Modifying decisions in any v1 ADR (ADR-001 through ADR-039)
- ❌ Removing architectural constraints defined in v1 ADRs
- ❌ Weakening DTO-only MVVM, Clean Architecture, or layer boundaries
- ❌ Breaking existing v1 tests or behavior
- ❌ "Temporary" violations with intent to refactor later

**ALLOWED** (v1 maintenance):
- ✅ Bug fixes maintaining v1 ADR compliance
- ✅ Performance optimizations within v1 constraints
- ✅ Documentation clarifications
- ✅ Test coverage improvements
- ✅ Implementation details not specified in v1 ADRs

**ALLOWED** (v2 Platform Work - see Section 16):
- ✅ Creating new v2 ADRs (ADR-V2-XXX series)
- ✅ Platform boundary design and interfaces
- ✅ New composition root planning for multi-app
- ✅ Extending interfaces (not breaking them)

### Freeze History

| Date | Status | Reason |
|------|--------|--------|
| 2026-01-21 | ACTIVE | Phase A + Near-Term Expansion complete |
| 2026-01-21 | INACTIVE | Begin v2 Platform: Multi-App Support |

---

## 15. COMPLETED MILESTONES

### 15.1 U8: Legacy Behavior Parity (✅ COMPLETE - 2026-01-20)

**Goal**: Implement hidden behaviors from legacy app for document generation workflow.

**Implemented**:
1. **Auto-save before document generation**
   - Modified: `GenerateDocumentCommand`
   - Behavior: Project automatically saves before generating document
   - Location: [generate_document_command.py](src/doc_helper/application/commands/generate_document_command.py)

2. **Override cleanup post-generation**
   - Added: `INVALID` and `SYNCED_FORMULA` states to `OverrideState` enum
   - Added: `IOverrideRepository` interface in domain layer
   - Implemented: `cleanup_synced_overrides()` in `OverrideService`
   - Behavior: SYNCED (non-formula) overrides deleted after successful generation, SYNCED_FORMULA overrides preserved
   - Location: [override_service.py](src/doc_helper/application/services/override_service.py)

**Tests**:
- ✅ 8/8 tests passing for OverrideService cleanup ([test_override_service_cleanup.py](tests/unit/application/services/test_override_service_cleanup.py))
- ✅ 8/8 tests passing for GenerateDocumentCommand U8 behavior ([test_generate_document_command_u8.py](tests/unit/application/commands/test_generate_document_command_u8.py))
- ✅ 758/758 domain & application tests passing (no regressions)

**Compliance**:
- ✅ No v2 features introduced
- ✅ Clean Architecture layers respected
- ✅ DTO-only MVVM maintained
- ✅ All new code tested

---

### 15.2 ADR-025: Validation Severity Levels (✅ COMPLETE - 2026-01-21)

**Goal**: Implement three-level validation severity system (ERROR/WARNING/INFO) to distinguish blocking errors from non-blocking warnings and informational messages.

**Status**: COMPLETE - Domain, Application, and Presentation layers implemented

**Implemented (Domain & Application)**:
1. **Severity value object** ([severity.py](src/doc_helper/domain/validation/severity.py))
   - Three levels: ERROR (blocks), WARNING (user confirmation), INFO (informational)
   - Helper methods: `blocks_workflow()`, `requires_confirmation()`, `is_informational()`
   - Default: ERROR for backward compatibility

2. **ValidationError extended** ([validation_result.py](src/doc_helper/domain/validation/validation_result.py))
   - Added `severity: Severity` field with default ERROR
   - Validation rejects invalid severity types

3. **ValidationResult extended** ([validation_result.py](src/doc_helper/domain/validation/validation_result.py))
   - Added methods: `has_blocking_errors()`, `has_warnings()`, `has_info()`, `get_errors_by_severity()`, `blocks_workflow()`
   - ERROR-level errors block workflows unconditionally

4. **Constraint classes updated** ([constraints.py](src/doc_helper/domain/validation/constraints.py))
   - All 8 constraint classes declare `severity: Severity = Severity.ERROR` as last field
   - Constraints: Required, MinLength, MaxLength, MinValue, MaxValue, Pattern, AllowedValues, FileExtension, MaxFileSize

5. **Validators updated** ([validators.py](src/doc_helper/domain/validation/validators.py))
   - All validators propagate severity from constraints to ValidationErrors
   - Severity preserved through validation chain

6. **ValidationResultDTO extended** ([validation_dto.py](src/doc_helper/application/dto/validation_dto.py))
   - Added `severity: str` field (primitive string for DTOs)
   - Added methods: `has_blocking_errors()`, `has_warnings()`, `has_info()`, `blocks_workflow()`

7. **ValidationMapper updated** ([validation_mapper.py](src/doc_helper/application/mappers/validation_mapper.py))
   - Converts `error.severity.value` enum to string for DTOs

8. **GenerateDocumentCommand updated** ([generate_document_command.py](src/doc_helper/application/commands/generate_document_command.py))
   - Added `validation_service` dependency
   - Validates project before generation
   - Blocks generation if ERROR-level validation failures exist
   - WARNING/INFO failures do not block (user confirmation handled in presentation)

**Implemented (Presentation Layer)**:
9. **PreGenerationChecklistDialog updated** ([pre_generation_checklist_dialog.py](src/doc_helper/presentation/dialogs/pre_generation_checklist_dialog.py))
   - Severity-based grouping: ERROR, WARNING, INFO sections
   - Visual differentiation: ERROR (red), WARNING (orange), INFO (blue)
   - Blocking behavior: ERROR blocks generation, shows "Close" button only
   - Confirmation flow: WARNING shows "Continue Anyway" button
   - Informational display: INFO shown without blocking

10. **DocumentGenerationViewModel updated** ([document_generation_viewmodel.py](src/doc_helper/presentation/viewmodels/document_generation_viewmodel.py))
    - `can_generate` property uses `blocks_workflow()` instead of `is_valid`
    - Added severity-aware properties: `has_blocking_errors()`, `has_warnings()`, `has_info()`
    - WARNING/INFO failures do not prevent generation

11. **IFieldWidget interface extended** ([field_widget.py](src/doc_helper/presentation/widgets/field_widget.py))
    - Added `set_validation_error_dtos()` method accepting ValidationErrorDTO with severity
    - Added `validation_error_dtos` property for severity-aware display
    - Legacy `set_validation_errors()` method maintained for backward compatibility
    - Updated `_update_validation_display()` documentation for severity-aware implementations

**Tests**:
- ✅ 19 Severity value object tests ([test_severity.py](tests/unit/domain/test_severity.py))
- ✅ 12 ValidationError/ValidationResult severity tests ([test_validation_result.py](tests/unit/domain/test_validation_result.py))
- ✅ 5 integration tests for severity-based workflow control ([test_severity_workflow.py](tests/integration/workflows/test_severity_workflow.py))
- ✅ 11 new presentation layer severity tests ([test_pre_generation_checklist_dialog.py](tests/unit/presentation/dialogs/test_pre_generation_checklist_dialog.py))
- ✅ Updated GenerateDocumentCommand U8 tests to include validation_service
- ✅ 1,421 total tests passing (29/29 pre-generation dialog tests, 2 pre-existing failures unrelated)
- ✅ No regressions

**Compliance**:
- ✅ No v2 features introduced
- ✅ Clean Architecture layers respected (domain → application → presentation)
- ✅ DTO-only MVVM maintained (severity enum → string in DTOs, no domain imports in presentation)
- ✅ All new code tested (47 total ADR-025 tests)
- ✅ ADR-024 compliance: No new violations introduced

**Authorization**: Explicitly authorized in AGENT_RULES.md Section 10 (Near-Term Expansion Exceptions)

---

---

## 16. V2 PLATFORM WORK RULES

**Status**: ACTIVE
**Date Authorized**: 2026-01-21
**Objective**: Multi-App Support (Multi-AppType Platform)

### 16.1 Scope of v2 Platform Work

**ALLOWED** (v2 Platform Development):
- ✅ Creating new v2 ADRs (ADR-V2-001, ADR-V2-002, ADR-V2-003, etc.)
- ✅ Defining platform host responsibilities and interfaces
- ✅ Designing AppType boundary contracts
- ✅ Planning new composition root architecture
- ✅ Creating new modules/packages for platform infrastructure
- ✅ Adding new interfaces that AppTypes must implement
- ✅ Extending existing interfaces (additive changes only)
- ✅ Creating platform-level services for AppType discovery/registry

**FORBIDDEN** (v1 Protection):
- ❌ Changing existing implemented behavior of v1 code
- ❌ Breaking Clean Architecture layer boundaries (Section 2)
- ❌ Weakening DTO-only MVVM (Section 3)
- ❌ Retroactively editing v1 ADR decisions (ADR-001 through ADR-039)
- ❌ Breaking existing v1 tests
- ❌ Removing v1 functionality
- ❌ Coupling AppTypes to each other (cross-app imports)
- ❌ Platform host depending on specific AppType internals

### 16.2 v2 ADR Governance

**New v2 ADRs**:
- Use ADR-V2-XXX numbering series
- MUST document: Context, Decision, Options, Consequences, Migration Plan
- MUST specify: Non-goals, v1 impact assessment
- Status: DRAFT → ACCEPTED (requires explicit approval)

**v1 Behavior Changes**:
- Any change to existing v1 behavior MUST be proposed via v2 ADR
- v2 ADR MUST include explicit justification
- v2 ADR MUST include backward compatibility analysis
- v2 ADR MUST include migration path from v1

### 16.3 Platform-AppType Dependency Rules

```
Platform Host (doc_helper.platform)
    ├── Owns: AppType registry, discovery, lifecycle
    ├── Depends on: Domain layer, Application interfaces
    └── DOES NOT depend on: Specific AppType implementations

AppType Module (doc_helper.app_types.{name})
    ├── Implements: Platform contracts (IAppType, IAppTypeSchema, etc.)
    ├── Depends on: Platform contracts, Domain layer
    └── DOES NOT depend on: Other AppType modules

Cross-AppType Imports: FORBIDDEN
```

### 16.4 v2 Execution Discipline

**Before implementing any v2 change**:
1. Verify it aligns with accepted v2 ADRs
2. Confirm no v1 behavior is modified
3. Check Clean Architecture compliance
4. Check DTO-only MVVM compliance

**After implementing any v2 change**:
1. Run full test suite (v1 tests MUST still pass)
2. Run architectural compliance scan
3. Update v2 implementation documentation
4. Confirm no v1 regressions

### 16.5 v2 Implementation Phases

**Phase 1**: Platform Host + AppType Registry (infrastructure only, no second app)
**Phase 2**: Extract v1 as First AppType (Soil Investigation becomes an AppType module)
**Phase 3**: Add Second AppType (proof of isolation, may be minimal/stub)
**Phase 4**: UI Updates (AppType selection, project-to-AppType mapping)

Each phase requires explicit authorization before implementation.

---

## FINAL NOTE

This document exists to **prevent architectural drift**.

Correctness and discipline take priority over speed or convenience.


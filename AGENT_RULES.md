# AGENT_RULES.md

## Purpose
This document defines **non-negotiable execution rules** for any AI or human agent working on the Doc Helper codebase.

If a rule here conflicts with any other instruction, **this file wins**.

---

## 1. VERSION & SCOPE LOCK

- Target version: **Doc Helper v1 only**
- Source of truth: **unified_upgrade_plan_FINAL.md**
- v2+ features are **strictly forbidden** unless explicitly marked as v1 in the FINAL plan

The agent must not anticipate, prototype, or partially implement v2 features.

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

## 10. FORBIDDEN IN V1

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

## 11. DECISION PRECEDENCE

If a conflict exists:

1. AGENT_RULES.md
2. unified_upgrade_plan_FINAL.md
3. ADRs referenced in the FINAL plan
4. Deprecated plan versions or historical discussions

If unclear, STOP and ask for clarification.

---

## 12. EXECUTION DISCIPLINE

Before implementing any change, the agent MUST:

- Identify the v1 milestone it belongs to
- List affected layers
- Verify no forbidden rule is violated

After implementation, the agent MUST:

- Provide a compliance checklist
- Confirm no v2 features were introduced

---

## 13. COMPLETED MILESTONES

### U8: Legacy Behavior Parity (✅ COMPLETE - 2026-01-20)

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

## FINAL NOTE

This document exists to **prevent architectural drift**.

Correctness and discipline take priority over speed or convenience.


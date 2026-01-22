# Doc Helper: Unified Upgrade Plan

**Document Version**: FINAL
**Date**: 2026-01-20
**Status**: APPROVED - Canonical Reference
**Author**: Architecture Review (AI-Assisted)
**Supersedes**: v1.0, v1.1, v1.2, v1.3, v1.3.1

---

## Executive Summary

This document is the **single authoritative upgrade plan** for doc_helper v1 completion. It consolidates all previous plan versions (v1.0-v1.3.1) into one canonical reference.

**Key Findings**:
- doc_helper v1 is **65% complete** with solid domain layer but critical gaps in assembly/presentation
- **5 critical blockers** prevent v1 completion: DI container, i18n service, project view TODOs, widget factory, recent projects persistence
- Legacy app has **290 Python files** with features that must be preserved
- Current plan.md is authoritative and correctly scopes v1 vs v2+

**FINAL Version Consolidation**:
- [v1.0] Base implementation inventory and legacy parity audit
- [v1.1] Gate 0 verification, MVVM rules, v2+ executable upgrade path, ADRs 014-019
- [v1.2] DTO-only MVVM (HARD RULE), Milestone U1.5, ADR-020
- [v1.3] Hardening H1-H5, command-based undo model, ADR-021, temporal undo tests
- [v1.3.1] Undo stack clearing rules, computed values wording fix
- [FINAL] U1.5 marked DONE, all content merged

---

# HARDENING CHANGES (H1-H5)

> **Source**: v1.3 with v1.3.1 patches applied

## H1: COMMAND-BASED UNDO MODEL (Explicit Choice)

**Decision**: The undo system uses a **command-based model**, NOT snapshot-based.

**What this means**:
- Each undoable operation creates an explicit `UndoCommand` with:
  - `execute()` - performs the action
  - `undo()` - reverses the action
  - State captured at command creation time
- Undo/Redo operates on a stack of commands
- No automatic state snapshots taken

**Why command-based**:
1. **Explicit state capture** - developer must specify what to capture
2. **Memory efficient** - only changed data stored, not full snapshots
3. **Predictable** - no hidden behavior, each command is self-contained
4. **Testable** - each command can be unit tested in isolation

**Implementation requirement**:
```python
# Every undoable operation MUST create a command like this:
@dataclass(frozen=True)
class SetFieldValueCommand:
    field_id: str
    old_value: Any  # Captured BEFORE the change
    new_value: Any  # The new value being set
    old_validation_state: ValidationStateDTO  # Captured BEFORE

    def execute(self, field_service: IFieldService) -> None:
        field_service.set_value(self.field_id, self.new_value)
        # Note: Dependent computed fields are RECOMPUTED, not restored

    def undo(self, field_service: IFieldService) -> None:
        field_service.set_value(self.field_id, self.old_value)
        # Note: Dependent computed fields are RECOMPUTED, not restored
```

**Undo Stack Management [v1.3.1 PATCH]**:
- Undo stack is **cleared on project close/open** (NOT on save)
- Rationale: Save is a persistence operation, not an edit boundary
- User expectation: "I saved, but I can still undo my recent edits"
- Project close/open IS an edit boundary - starts fresh editing session

---

## H2: UNDO-STATE DTOs vs UI DTOs (Strict Separation)

**Problem solved**: Prevent confusion between DTOs for display and DTOs for undo state capture.

**Rule**: UndoState DTOs are **internal to the application layer** and NEVER cross into presentation.

**DTO Hierarchy**:
```
application/dto/
├── ui/                          # For presentation layer consumption
│   ├── project_dto.py           # ProjectDTO, ProjectSummaryDTO
│   ├── field_dto.py             # FieldValueDTO, FieldDefinitionDTO
│   ├── validation_dto.py        # ValidationResultDTO
│   └── override_dto.py          # OverrideDTO
│
└── undo/                        # INTERNAL to application layer ONLY
    ├── field_undo_state.py      # FieldUndoStateDTO
    ├── override_undo_state.py   # OverrideUndoStateDTO
    └── validation_undo_state.py # ValidationUndoStateDTO
```

**Naming Convention**:
- UI DTOs: `{Name}DTO` (e.g., `FieldValueDTO`)
- UndoState DTOs: `{Name}UndoStateDTO` (e.g., `FieldUndoStateDTO`)

**Access Rules**:
| DTO Type | Presentation Can Import? | Application Uses Internally? |
|----------|-------------------------|------------------------------|
| UI DTOs | ✅ YES | ✅ YES |
| UndoState DTOs | ❌ NO (FORBIDDEN) | ✅ YES |

**Example**:
```python
# ✅ ALLOWED: Presentation imports UI DTO
from doc_helper.application.dto.ui.field_dto import FieldValueDTO

# ❌ FORBIDDEN: Presentation imports UndoState DTO
from doc_helper.application.dto.undo.field_undo_state import FieldUndoStateDTO  # VIOLATION!
```

**Rationale**:
- UI DTOs are optimized for display (may have computed/formatted fields)
- UndoState DTOs are optimized for state restoration (raw values, no formatting)
- Mixing them causes confusion about which DTO to use where

---

## H3: MAPPER RESPONSIBILITY (Clarified for Undo)

**Rule**: Mappers are **one-way only**: Domain → DTO. There are NO DTO → Domain mappers.

**Why no reverse mappers?**
1. **Commands accept primitives**, not DTOs
2. **Undo commands store primitives** (old_value, new_value), not DTOs
3. **Domain objects are created via factories**, not mapped from DTOs

**Data Flow**:
```
User Input (primitives)
    ↓
Command (stores primitives)
    ↓
Domain Operation (creates/modifies domain objects)
    ↓
Mapper (Domain → DTO)
    ↓
ViewModel (receives DTO)
    ↓
View (displays DTO properties)
```

**For Undo**:
```
Command Created:
    - Captures field_id (string)
    - Captures old_value (primitive/JSON-serializable)
    - Captures new_value (primitive/JSON-serializable)

On Undo:
    - Uses captured primitives directly
    - Calls domain service with primitives
    - Domain service performs operation
    - New state mapped to DTOs for UI update
```

**Forbidden Pattern**:
```python
# ❌ WRONG: Creating domain object from DTO
def undo(self):
    # WRONG - no DTO → Domain mapping
    field_value = FieldValueMapper.from_dto(self.old_state_dto)
    self.repository.save(field_value)

# ✅ CORRECT: Using captured primitives
def undo(self, field_service: IFieldService):
    # CORRECT - primitives passed to domain service
    field_service.set_value(self.field_id, self.old_value)
```

---

## H4: TEMPORAL UNDO TEST SCENARIOS (Mandatory)

**Requirement**: The following test scenarios MUST pass before U6 is complete.

### T1: Basic Field Edit Undo
```python
def test_undo_field_edit():
    """User edits a field, then undoes."""
    # Setup
    field_id = "project_name"
    original_value = "Original"
    new_value = "Modified"

    # User edits field
    vm.set_field_value(field_id, new_value)
    assert vm.get_field_value(field_id) == new_value

    # User presses Ctrl+Z
    vm.undo()
    assert vm.get_field_value(field_id) == original_value
```

### T2: Undo with Computed Field Dependency
```python
def test_undo_recomputes_dependent_fields():
    """Undo triggers recomputation of computed fields."""
    # Setup: field_a is raw, field_b = field_a * 2 (computed)
    field_a_id = "quantity"
    field_b_id = "total"  # formula: {{quantity}} * 2

    original_a = 5
    original_b = 10  # computed from original_a

    # User changes field_a
    vm.set_field_value(field_a_id, 10)
    assert vm.get_field_value(field_b_id) == 20  # recomputed

    # User undoes
    vm.undo()
    assert vm.get_field_value(field_a_id) == original_a
    assert vm.get_field_value(field_b_id) == original_b  # RECOMPUTED, not restored
```

### T3: Override Accept Undo
```python
def test_undo_override_accept():
    """Undo restores override to PENDING state."""
    # Setup: override exists in PENDING state
    override_id = "override_1"
    field_id = "borehole_depth"
    system_value = 100
    report_value = 150

    # Initial state
    assert vm.get_override_state(override_id) == "PENDING"
    assert vm.get_field_value(field_id) == system_value

    # User accepts override
    vm.accept_override(override_id)
    assert vm.get_override_state(override_id) == "ACCEPTED"
    assert vm.get_field_value(field_id) == report_value

    # User undoes
    vm.undo()
    assert vm.get_override_state(override_id) == "PENDING"
    assert vm.get_field_value(field_id) == system_value  # restored
```

### T4: Multiple Undo/Redo Sequence
```python
def test_undo_redo_sequence():
    """Multiple undo/redo operations maintain correct state."""
    field_id = "sample_count"

    # Initial: value = 1
    assert vm.get_field_value(field_id) == 1

    # Edit 1: value = 2
    vm.set_field_value(field_id, 2)

    # Edit 2: value = 3
    vm.set_field_value(field_id, 3)

    # Edit 3: value = 4
    vm.set_field_value(field_id, 4)

    # Undo back to 2
    vm.undo()  # 4 → 3
    vm.undo()  # 3 → 2
    assert vm.get_field_value(field_id) == 2

    # Redo to 3
    vm.redo()  # 2 → 3
    assert vm.get_field_value(field_id) == 3

    # New edit clears redo stack
    vm.set_field_value(field_id, 5)
    assert not vm.can_redo()

    # Can still undo to 3, then 2, then 1
    vm.undo()  # 5 → 3
    assert vm.get_field_value(field_id) == 3
```

### T5: Undo Stack Cleared on Project Close/Open [v1.3.1]
```python
def test_undo_stack_cleared_on_project_close():
    """Undo stack is cleared when project is closed."""
    # Make some edits
    vm.set_field_value("field_1", "value_1")
    vm.set_field_value("field_2", "value_2")
    assert vm.can_undo()

    # Close project
    vm.close_project()

    # Undo stack should be cleared
    assert not vm.can_undo()
    assert not vm.can_redo()

def test_undo_stack_cleared_on_project_open():
    """Opening a different project clears undo stack."""
    # Make some edits in project A
    vm.set_field_value("field_1", "value_1")
    assert vm.can_undo()

    # Open project B
    vm.open_project("project_b_path")

    # Undo stack should be cleared
    assert not vm.can_undo()
    assert not vm.can_redo()

def test_undo_stack_NOT_cleared_on_save():
    """Saving does NOT clear undo stack."""
    # Make some edits
    vm.set_field_value("field_1", "value_1")
    vm.set_field_value("field_2", "value_2")
    assert vm.can_undo()

    # Save project
    vm.save_project()

    # Undo stack should STILL be available
    assert vm.can_undo()
    vm.undo()
    assert vm.get_field_value("field_2") != "value_2"  # undone
```

---

## H5: STATE CAPTURE SPECIFICATION

**Requirement**: Every undoable command MUST explicitly specify what state it captures.

**State Capture Table**:

| Command | Captures Before | Captures After | Restores On Undo |
|---------|-----------------|----------------|------------------|
| SetFieldValueCommand | old_value, old_validation_state | new_value | old_value (validation recomputed) |
| AcceptOverrideCommand | override_state (PENDING), field_value | - | override_state, field_value |
| RejectOverrideCommand | override_state (PENDING) | - | override_state |

**What is NOT captured (recomputed instead)**:
- Computed field values (they're recomputed from dependencies)
- Control effects (VISIBILITY, ENABLE states are recomputed)
- Validation states (recomputed after undo)

**Rationale**: Capturing computed state leads to inconsistency. If field A changes and field B depends on A, undoing A should recompute B, not restore a stale captured value.

---

# PHASE 0: CURRENT IMPLEMENTATION VERIFICATION (Gate 0)

> **[Source: v1.1]** This mandatory phase must complete before any U1-U12 work begins.

## 0.1 Purpose

Gate 0 ensures the upgrade plan is based on **verified facts**, not assumptions. The agent must scan the actual codebase and produce evidence of what exists.

## 0.2 Verification Procedure

### Step 1: Domain Layer Scan

```bash
.venv/Scripts/python -c "
import os
DOMAIN_CONTEXTS = [
    'common', 'schema', 'project', 'validation',
    'formula', 'control', 'override', 'document', 'file'
]
for ctx in DOMAIN_CONTEXTS:
    path = f'src/doc_helper/domain/{ctx}'
    if os.path.exists(path):
        files = [f for f in os.listdir(path) if f.endswith('.py')]
        print(f'✅ {ctx}: {len(files)} files')
    else:
        print(f'❌ {ctx}: MISSING')
"
```

### Step 2: Application Layer Scan

```bash
.venv/Scripts/python -c "
import os
cmd_path = 'src/doc_helper/application/commands'
if os.path.exists(cmd_path):
    for root, dirs, files in os.walk(cmd_path):
        for f in files:
            if f.endswith('.py') and not f.startswith('__'):
                print(f'Command: {f}')
"
```

### Step 3: Infrastructure Layer Scan

```bash
.venv/Scripts/python -c "
import os
CRITICAL = [
    ('DI Container', 'src/doc_helper/infrastructure/di/container.py'),
    ('i18n Service', 'src/doc_helper/infrastructure/i18n/json_translation_service.py'),
    ('Recent Projects', 'src/doc_helper/infrastructure/filesystem/recent_projects_storage.py'),
    ('Event Bus', 'src/doc_helper/infrastructure/events/in_memory_bus.py'),
]
for name, path in CRITICAL:
    status = '✅' if os.path.exists(path) else '❌'
    print(f'{status} {name}: {path}')
"
```

### Step 4: Presentation Layer Scan

```bash
.venv/Scripts/python -c "
FIELD_TYPES = [
    'TEXT', 'TEXTAREA', 'NUMBER', 'DATE', 'DROPDOWN',
    'CHECKBOX', 'RADIO', 'CALCULATED', 'LOOKUP',
    'FILE', 'IMAGE', 'TABLE'
]
import os
widget_path = 'src/doc_helper/presentation/widgets'
if os.path.exists(widget_path):
    files = os.listdir(widget_path)
    for ft in FIELD_TYPES:
        found = any(ft.lower() in f.lower() for f in files)
        status = '✅' if found else '❌'
        print(f'{status} {ft} widget')
"
```

### Step 5: Test Suite Verification

```bash
.venv/Scripts/python -m pytest tests/ --collect-only -q 2>/dev/null | tail -20
.venv/Scripts/python -m pytest tests/ -v --tb=no 2>&1 | tail -30
```

### Step 6: Translation File Verification

```bash
.venv/Scripts/python -c "
import json
import os
for lang in ['en', 'ar']:
    path = f'translations/{lang}.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f'✅ {lang}.json: {len(data)} keys')
    else:
        print(f'❌ {lang}.json: MISSING')
"
```

## 0.3 Gate 0 Acceptance Criteria

**Gate 0 PASSES if ALL conditions met:**

| # | Criterion | Required | Verification |
|---|-----------|----------|--------------|
| G0.1 | Domain contexts common, schema, project, validation, formula, control, override, document exist | All 8 present | File scan |
| G0.2 | At least 3 application commands implemented | ≥3 commands | File scan |
| G0.3 | SQLite repositories exist for schema and project | Both present | File scan |
| G0.4 | All 12 field type widgets exist | 12/12 | File scan |
| G0.5 | Translation files en.json and ar.json exist | Both present | File scan |
| G0.6 | Existing tests pass | ≥90% pass rate | pytest run |
| G0.7 | No circular imports in domain layer | 0 errors | Import test |

**Gate 0 FAILS if ANY condition unmet.** Agent must fix issues before proceeding to U1.

**Note**: DTO-only enforcement is NOT checked at Gate 0 (starts after U1.5).

---

# PHASE 1: CURRENT STATE AUDIT

## 1.1 Implementation Inventory

### Domain Layer (95% Complete)

| Context | Status | Files | Notes |
|---------|--------|-------|-------|
| **common/** | ✅ Complete | entity.py, value_object.py, result.py, events.py, i18n.py, translation.py | Solid foundation |
| **schema/** | ✅ Complete | field_type.py, schema_ids.py, field_definition.py, entity_definition.py, schema_repository.py | All 12 field types |
| **project/** | ✅ Complete | project_ids.py, project.py, field_value.py, project_repository.py | Aggregate root pattern |
| **validation/** | ✅ Complete | constraints.py, validation_result.py, validators.py | Simple pass/fail |
| **formula/** | ✅ Complete | tokenizer.py, parser.py, ast_nodes.py, evaluator.py, dependency_tracker.py | Full formula system |
| **control/** | ✅ Complete | control_effect.py, control_rule.py, effect_evaluator.py | VALUE_SET, VISIBILITY, ENABLE |
| **override/** | ✅ Complete | override_state.py, override_entity.py, override_ids.py, conflict_detector.py | 3-state machine |
| **document/** | ✅ Complete | document_adapter.py, document_format.py, transformer.py, transformers.py | 17+ transformers |
| **file/** | ❌ Missing | N/A | Figure numbering NOT implemented |

### Application Layer (85% Complete)

| Component | Status | Files | Notes |
|-----------|--------|-------|-------|
| **commands/** | ✅ Complete | create, save, update, delete, generate | All v1 commands |
| **queries/** | ✅ Complete | get_project, get_entity_fields, get_validation_result | 10+ queries |
| **services/** | ✅ Complete | validation, formula, control services | Core orchestration |
| **document/** | ✅ Complete | document_generation_service.py | Document orchestration |
| **dto/** | ✅ DONE (U1.5) | All DTOs defined | [v1.2] DTO-only complete |
| **events/** | ⚠️ Skeleton | handlers/ | Event handlers skeleton |

### Infrastructure Layer (60% Complete)

| Component | Status | Files | Notes |
|-----------|--------|-------|-------|
| **persistence/** | ⚠️ Partial | sqlite_base, sqlite_schema_repo, sqlite_project_repo | No Unit of Work |
| **document/** | ✅ Complete | word, excel, pdf adapters | All 3 working |
| **filesystem/** | ⚠️ Partial | file_project_storage.py | No recent projects |
| **di/** | ❌ MISSING | EMPTY | **CRITICAL BLOCKER** |
| **i18n/** | ❌ MISSING | N/A | **CRITICAL BLOCKER** |
| **events/** | ❌ Missing | N/A | No event bus |

### Presentation Layer (45% Complete)

| Component | Status | Notes |
|-----------|--------|-------|
| **viewmodels/** | ⚠️ Partial | Welcome complete, others stubs |
| **views/** | ⚠️ Partial | project_view.py has TODOs |
| **widgets/** | ✅ Complete | All 12 field type widgets |
| **dialogs/** | ❌ Missing | Settings, override, template missing |
| **factories/** | ❌ Missing | **CRITICAL** - No widget factory |
| **adapters/** | ❌ Missing | No history, translation adapters |

## 1.2 Feature Mapping to v1 Definition of Done

| v1 Requirement | Implemented | Gap |
|----------------|-------------|-----|
| Create/Open/Save/Close project | ⚠️ Partial | UI incomplete |
| Dynamic form rendering | ⚠️ Partial | Factory missing |
| All 12 field types | ✅ Yes | Complete |
| Formula evaluation | ✅ Yes | Complete |
| Control system | ✅ Yes | Complete |
| Override system | ✅ Yes | Complete |
| Document generation | ✅ Yes | All adapters |
| Transformers (15+) | ✅ Yes | 17+ transformers |
| Undo/Redo | ❌ No | **NOT IMPLEMENTED** |
| Recent projects | ❌ No | **NOT IMPLEMENTED** |
| i18n (EN/AR + RTL) | ⚠️ Partial | Service missing |
| **[v1.2] DTO-only presentation** | ✅ DONE | U1.5 complete |

## 1.3 Critical Gaps Summary

| Priority | Gap | Impact | Effort |
|----------|-----|--------|--------|
| **P0** | DI Container Missing | Cannot assemble | 2-3 days |
| **P0** | i18n Service Missing | Translations unusable | 3-4 days |
| **P0** | Project View TODOs | Cannot render forms | 5-7 days |
| **P0** | **[v1.2] DTO Definitions** | DTO-only blocked | **DONE (U1.5)** |
| **P1** | Widget Factory Missing | No dynamic widgets | 2-3 days |
| **P1** | Recent Projects | Core UX missing | 2-3 days |
| **P1** | Undo/Redo System | v1 scope required | 3-5 days |

---

# PHASE 2: LEGACY FEATURE PARITY AUDIT

## 2.1 Legacy Parity Matrix

| Legacy Feature | v1 Status | Action |
|----------------|-----------|--------|
| Project CRUD | ✅ | - |
| 12 field types | ✅ | - |
| Validation system | ✅ | - |
| Formula system | ✅ | - |
| Control system | ✅ | - |
| Override system | ✅ | - |
| Transformers (16+) | ✅ | - |
| Word/Excel/PDF | ✅ | - |
| Recent projects | ❌ | **MUST ADD** |
| Undo/Redo | ❌ | **MUST ADD** |
| Tab navigation history | ❌ | **MUST ADD** |
| Figure numbering | ❌ | **MUST ADD** |
| Settings dialog | ❌ | **MUST ADD** |
| Menu bar | ❌ | **MUST ADD** |
| Auto-save before generate | ❌ | **MUST ADD** |
| Override cleanup post-gen | ❌ | **MUST ADD** |

---

# PHASE 4: AUTHORITATIVE UNIFIED PLAN

## 4.1 Scope Separation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        v1 IMPLEMENTED (65%)                             │
├─────────────────────────────────────────────────────────────────────────┤
│  Domain: validation, schema, formula, control, override, transformer    │
│  Application: commands, queries, services, DTOs (U1.5 DONE)             │
│  Infrastructure: SQLite repos, document adapters                        │
│  Presentation: All 12 field type widgets                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    v1 MISSING BUT REQUIRED (35%)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  Critical: DI container, i18n service, project view, widget factory     │
│  Important: Recent projects, undo/redo, tab history, settings dialog    │
│  Parity: Menu bar, auto-save before gen, override cleanup               │
│  Polish: Figure numbering, RTL layout                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         v2 UPGRADE (Deferred)                           │
├─────────────────────────────────────────────────────────────────────────┤
│  Platform: Multi-app-type, discovery, extensions, app type cards        │
│  UX: Dark mode, auto-save recovery, search, keyboard nav                │
│  Data: Import/export, clone project, document versioning                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4.2 Upgrade Milestones (v1 Completion)

### Milestone U1: Assembly Layer (P0 Critical)
**Goal**: Enable application to run by implementing DI container

**Scope**:
- Implement `infrastructure/di/container.py` with service registration
- Create composition root in `main.py`
- Wire all existing services through DI

**Files Affected**:
- `src/doc_helper/infrastructure/di/__init__.py` (create)
- `src/doc_helper/infrastructure/di/container.py` (create)
- `src/doc_helper/main.py` (update)

**Verification**:
- [ ] Application starts without manual wiring
- [ ] All services resolve correctly
- [ ] Integration tests pass with DI

**Estimated Effort**: 2-3 days

---

### Milestone U1.5: DTO Definitions & Mapping ✅ DONE

> **[v1.2 NEW]** This milestone is a PREREQUISITE for DTO-only enforcement.
> **Status**: COMPLETED

**Goal**: Define all DTOs and mappers required for DTO-only presentation layer

**13 Required DTOs**:

| # | DTO | Location | Purpose |
|---|-----|----------|---------|
| 1 | ProjectDTO | dto/ui/project_dto.py | Project display data |
| 2 | ProjectSummaryDTO | dto/ui/project_dto.py | Recent projects list |
| 3 | EntityDefinitionDTO | dto/ui/entity_dto.py | Entity metadata |
| 4 | FieldDefinitionDTO | dto/ui/field_dto.py | Field schema |
| 5 | FieldValueDTO | dto/ui/field_dto.py | Field current value |
| 6 | FieldTypeDTO | dto/ui/field_dto.py | Field type enum mirror |
| 7 | ValidationResultDTO | dto/ui/validation_dto.py | Validation state |
| 8 | ControlEffectDTO | dto/ui/control_dto.py | Control effects |
| 9 | OverrideDTO | dto/ui/override_dto.py | Override state |
| 10 | TemplateDTO | dto/ui/document_dto.py | Template info |
| 11 | FieldUndoStateDTO | dto/undo/field_undo_state.py | Undo state capture |
| 12 | OverrideUndoStateDTO | dto/undo/override_undo_state.py | Override undo state |
| 13 | ValidationUndoStateDTO | dto/undo/validation_undo_state.py | Validation undo state |

**Mappers Required**:
- `ProjectMapper.to_dto()`, `to_summary_dto()`
- `FieldMapper.to_definition_dto()`, `to_value_dto()`
- `ValidationMapper.to_dto()`
- `OverrideMapper.to_dto()`
- `ControlMapper.to_effect_dto()`

**DTO Design Rules**:
```python
# ✅ CORRECT: DTO with primitives only
@dataclass(frozen=True)
class FieldValueDTO:
    field_id: str           # String, not FieldId
    value: Any              # Primitive or JSON-serializable
    display_value: str      # Pre-formatted for display
    is_valid: bool          # Pre-computed
    validation_message: str # Pre-computed

# ❌ WRONG: DTO containing domain types
@dataclass(frozen=True)
class FieldValueDTO:
    field_id: FieldId       # Domain type - FORBIDDEN
```

**Verification**: ✅ COMPLETE
- [x] All 13 DTOs defined with frozen dataclasses
- [x] All mappers implemented with unit tests
- [x] DTO compliance check script passes

---

### Milestone U2: i18n Service Implementation (P0 Critical)
**Goal**: Enable translation system to work

**Scope**:
- Implement `JsonTranslationService` in `infrastructure/i18n/`
- Load translations from `translations/en.json` and `translations/ar.json`
- Implement `QtTranslationAdapter` for presentation layer

**Files Affected**:
- `src/doc_helper/infrastructure/i18n/__init__.py` (create)
- `src/doc_helper/infrastructure/i18n/json_translation_service.py` (create)
- `src/doc_helper/presentation/adapters/qt_translation_adapter.py` (create)

**Verification**:
- [ ] English translations load and display
- [ ] Arabic translations load and display
- [ ] Language switch works without restart

**Estimated Effort**: 3-4 days

---

### Milestone U3: Project View Completion (P0 Critical)
**Goal**: Resolve all TODOs in project_view.py

**Scope**:
- Implement dynamic field widget creation
- Implement tab navigation
- Connect validation indicators

**Files Affected**:
- `src/doc_helper/presentation/views/project_view.py` (update)
- `src/doc_helper/presentation/viewmodels/project_viewmodel.py` (update)
- `src/doc_helper/presentation/viewmodels/entity_viewmodel.py` (create)
- `src/doc_helper/presentation/viewmodels/field_viewmodel.py` (create)

**Verification**:
- [ ] Dynamic forms render from schema
- [ ] Tab navigation works
- [ ] Field values save correctly
- [ ] **[v1.2]** No domain imports in view/viewmodel files

**Estimated Effort**: 5-7 days

---

### Milestone U4: Widget Factory Pattern (P1 Important)
**Goal**: Implement registry-based widget factory

**Scope**:
- Create `FieldWidgetFactory` using registry pattern
- Register all 12 field type widgets

**Files Affected**:
- `src/doc_helper/presentation/factories/field_widget_factory.py` (create)

**Verification**:
- [ ] All 12 field types create correct widgets
- [ ] Factory is used by project view

**Estimated Effort**: 2-3 days

---

### Milestone U5: Recent Projects & Settings (P1 Important)
**Goal**: Implement recent projects tracking and settings dialog

**Scope**:
- Create `RecentProjectsStorage` in infrastructure
- Create settings dialog with language selector

**Files Affected**:
- `src/doc_helper/infrastructure/filesystem/recent_projects_storage.py` (create)
- `src/doc_helper/presentation/dialogs/settings_dialog.py` (create)

**Verification**:
- [ ] Recent projects persist across sessions
- [ ] Language change works

**Estimated Effort**: 4-5 days

---

### Milestone U6: Undo/Redo System (P1 Important)

> **[v1.2]** Override operations NOW INCLUDED in undo/redo
> **[v1.3]** Command-based model with explicit state capture (H1-H5)
> **[v1.3.1]** Undo stack cleared on project close/open, NOT on save

**Goal**: Implement command-based undo/redo with hardened specification

**INCLUDED in undo/redo**:

| Operation | Command | Undoable |
|-----------|---------|----------|
| User edits field | SetFieldValueCommand | ✅ Yes |
| Accept formula result | AcceptFormulaValueCommand | ✅ Yes |
| **Accept override** | AcceptOverrideCommand | ✅ Yes |
| **Reject override** | RejectOverrideCommand | ✅ Yes |
| **Sync override** | SyncOverrideCommand | ✅ Yes |

**EXCLUDED from undo/redo**:

| Operation | Reason |
|-----------|--------|
| Save project | Persistence, not editing |
| Open project | Navigation, not editing |
| Close project | Navigation, not editing |
| Generate document | External output |

**Command Implementation (H1)**:

```python
@dataclass(frozen=True)
class SetFieldValueCommand:
    field_id: str
    old_value: Any  # Captured BEFORE the change
    new_value: Any

    def execute(self, field_service: IFieldService) -> None:
        field_service.set_value(self.field_id, self.new_value)
        # Dependent computed fields are RECOMPUTED, not restored

    def undo(self, field_service: IFieldService) -> None:
        field_service.set_value(self.field_id, self.old_value)
        # Dependent computed fields are RECOMPUTED, not restored
```

**Undo Stack Rules [v1.3.1]**:
- Stack **cleared on project close/open**
- Stack **NOT cleared on save** (user can still undo after saving)

**Undo Cascade Effects**:
When undoing:
1. Field/override state restores to captured value
2. Dependent formulas **RECOMPUTE** (not restore captured values)
3. Dependent controls **re-evaluate**
4. Validation states **recompute**

**Files Affected**:
- `src/doc_helper/presentation/adapters/history_adapter.py` (create)
- `src/doc_helper/application/commands/history/field_commands.py` (create)
- `src/doc_helper/application/commands/history/override_commands.py` (create)
- `src/doc_helper/application/dto/undo/` (create - internal DTOs)

**Verification** (Temporal Tests T1-T5 MUST PASS):
- [ ] T1: Basic field edit undo works
- [ ] T2: Undo recomputes dependent fields (not restore)
- [ ] T3: Override accept undo restores PENDING state
- [ ] T4: Multiple undo/redo sequence works
- [ ] T5: Stack cleared on close/open, NOT on save

**Estimated Effort**: 3-5 days

---

### Milestone U7: Tab Navigation & Menu Bar (P1 Important)
**Goal**: Implement legacy parity for navigation and menus

**Scope**:
- Implement tab history (back/forward)
- Create menu bar structure

**Verification**:
- [ ] Tab history tracks navigation
- [ ] All menus functional

**Estimated Effort**: 3-4 days

---

### Milestone U8: Legacy Behavior Parity (P2 Polish)
**Goal**: Implement hidden behaviors from legacy app

**Scope**:
- Auto-save before document generation
- Override cleanup post-generation
- Cross-tab formula context provider

**Verification**:
- [ ] Project saves before generation
- [ ] Overrides cleaned up after generation
- [ ] Cross-tab formulas work

**Estimated Effort**: 3-4 days

---

### Milestone U9: File Context & Figure Numbering (P2 Polish)
**Goal**: Implement file management domain context

**Scope**:
- Create `domain/file/` bounded context
- Implement figure numbering

**Verification**:
- [ ] Figure numbers auto-assign
- [ ] Captions generate correctly

**Estimated Effort**: 3-5 days

---

### Milestone U10: RTL Layout & i18n Polish (P2 Polish)
**Goal**: Complete i18n implementation with RTL support

**Verification**:
- [ ] Arabic UI mirrors correctly
- [ ] All strings translated

**Estimated Effort**: 3-4 days

---

### Milestone U11: Missing Dialogs (P2 Polish)
**Goal**: Implement remaining v1 dialogs

**Scope**:
- Template selection dialog
- Override management dialog
- Conflict resolution dialog
- Pre-generation checklist dialog

**Estimated Effort**: 4-5 days

---

### Milestone U12: Integration & Testing (P2 Polish)
**Goal**: Complete testing and integration verification

**Scope**:
- Integration tests for all new features
- E2E workflow tests
- Legacy parity verification
- **[v1.2]** Final DTO-only compliance verification

**Verification**:
- [ ] All integration tests pass
- [ ] E2E workflow completes
- [ ] Legacy parity checklist complete
- [ ] **[v1.2]** DTO-only compliance verified

**Estimated Effort**: 5-7 days

---

## 4.3 Architecture Diagrams

### Target v1 Architecture (100% Complete)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       PRESENTATION (100% Complete)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  MainWindow │  │   Dialogs   │  │   Widgets   │  │ ViewModels  │    │
│  │  + Menus    │  │  Settings   │  │   Factory   │  │   + Field   │    │
│  │  + Nav      │  │  Override   │  │   Pattern   │  │   + Entity  │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         └────────────────┴────────────────┴────────────────┘            │
│                                    │                                     │
│                   ┌────────────────┼────────────────┐                    │
│                   │                │                │                    │
│              [History]       [Navigation]    [Translation]               │
│               Adapter          Adapter         Adapter                   │
│                                    │                                     │
│         ════════════════DTO BOUNDARY═══════════════════ [v1.2]          │
│                                    ▼                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                       APPLICATION (100% Complete)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Commands      │  │   Queries       │  │  Services       │         │
│  │  + History      │  │   (return DTOs) │  │  + Pre-gen save │         │
│  │  + Override     │  │                 │  │  + Override     │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           │                    │                    │                   │
│  ┌─────────────────┐  ┌─────────────────┐                               │
│  │      DTOs       │  │    Mappers      │  [v1.2]                       │
│  │  ui/ + undo/    │  │ (Domain→DTO)   │                               │
│  └────────┬────────┘  └────────┬────────┘                               │
│           └────────────────────┴────────────────────┘                   │
│                                │                                         │
│                                ▼                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                        DOMAIN (100% Complete)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   schema     │  │  validation  │  │   formula    │  │  control   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   project    │  │   override   │  │   document   │  │    file    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE (100% Complete)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   SQLite    │  │    File     │  │   Document  │  │     DI      │    │
│  │    Repos    │  │   Storage   │  │  Adapters   │  │  Container  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐                                      │
│  │    i18n     │  │   Events    │                                      │
│  │  JSON Svc   │  │  In-Memory  │                                      │
│  └─────────────┘  └─────────────┘                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# PHASE 5: SAFETY AND NON-REGRESSION RULES

## 5.1 Architectural Constraints (MANDATORY)

### 5.1.1 Layer Violations (FORBIDDEN)

```python
# ❌ FORBIDDEN: Domain importing PyQt6
from PyQt6.QtCore import QObject  # NEVER in domain/

# ❌ FORBIDDEN: Domain importing SQLite
import sqlite3  # NEVER in domain/

# ❌ FORBIDDEN [v1.2]: Presentation importing domain ANYTHING
from doc_helper.domain.project.project import Project  # NEVER in presentation/
from doc_helper.domain.schema.field_type import FieldType  # NEVER in presentation/

# ✅ ALLOWED: Presentation using application layer DTOs
from doc_helper.application.dto.ui.project_dto import ProjectDTO
from doc_helper.application.dto.ui.field_dto import FieldTypeDTO
```

### 5.1.2 DTO-Only MVVM (v1.2 HARD RULE)

**Presentation layer MUST NEVER import from `doc_helper.domain`**

```
Presentation → Application → Domain ← Infrastructure
     ↓              ↓           ↑           ↑
   Uses          Uses      Implements   Implements
  (DTOs)      (Commands)
```

**Data Flow**:

| Direction | What Flows |
|-----------|------------|
| View → ViewModel | User input (primitives) |
| ViewModel → View | Display data (primitives from DTOs) |
| ViewModel → Application | Command parameters (primitives, IDs) |
| Application → ViewModel | **DTOs only** |
| Application → Domain | Domain operations |
| Domain → Application | Domain objects (mapped to DTOs) |

### 5.1.3 DTO-Only Compliance Verification

**Static Import Check Script**:

```python
# scripts/check_dto_compliance.py
import ast
import sys
from pathlib import Path

PRESENTATION_PATH = Path("src/doc_helper/presentation")
FORBIDDEN_IMPORT_PREFIX = "doc_helper.domain"

def check_file(filepath: Path) -> list[str]:
    violations = []
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(FORBIDDEN_IMPORT_PREFIX):
                    violations.append(f"{filepath}:{node.lineno}: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith(FORBIDDEN_IMPORT_PREFIX):
                violations.append(f"{filepath}:{node.lineno}: from {node.module}")

    return violations

def main():
    all_violations = []
    for py_file in PRESENTATION_PATH.rglob("*.py"):
        all_violations.extend(check_file(py_file))

    if all_violations:
        print("❌ DTO-ONLY COMPLIANCE CHECK FAILED")
        for v in all_violations:
            print(v)
        sys.exit(1)
    else:
        print("✅ DTO-ONLY COMPLIANCE CHECK PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## 5.2 Testing Strategy

### 5.2.1 Temporal Undo Test Scenarios (MANDATORY)

Tests T1-T5 from H4 **MUST PASS** before U6 is complete. See H4 section for full test specifications.

### 5.2.2 Required Behaviors Checklist

Before any release, verify:

- [ ] Project creates correctly
- [ ] Project opens and restores state
- [ ] All 12 field types render and save
- [ ] Validation shows errors in real-time
- [ ] Formulas compute with dependencies
- [ ] Controls (VALUE_SET, VISIBILITY, ENABLE) work
- [ ] Override state machine transitions correctly
- [ ] **[v1.2]** Undo/Redo works for override operations
- [ ] Word document generates with content controls
- [ ] Recent projects track last 5
- [ ] Undo/Redo works for field changes
- [ ] Translations display correctly (EN/AR)
- [ ] RTL layout works for Arabic
- [ ] **[v1.2]** Zero domain imports in presentation

---

# PHASE 6: EXECUTION ROADMAP

## 6.1 Priority Order

```
GATE 0:    Current Implementation Verification (mandatory)
           ↓ Must pass before any work
           ↓ (DTO-only NOT enforced here)
Week 1-2:  U1 (DI Container) + U1.5 (DTOs) ✅ DONE
           ↓ DTO-only enforcement STARTS after U1.5
Week 2-3:  U2 (i18n Service)
           ↓ Unblocks translations
Week 3-4:  U3 (Project View) + U4 (Widget Factory)
           ↓ Forms become functional
Week 5:    U5 (Recent Projects + Settings)
           ↓ Core UX complete
Week 6:    U6 (Undo/Redo) [includes overrides, H1-H5 spec]
           ↓ Edit experience complete
Week 7:    U7 (Tab Navigation + Menu Bar)
           ↓ Navigation complete
Week 8:    U8 (Legacy Behavior Parity)
           ↓ Hidden behaviors work
Week 9:    U9 (File Context + Figure Numbering)
           ↓ File management works
Week 10:   U10 (RTL Layout + i18n Polish)
           ↓ i18n complete
Week 11:   U11 (Missing Dialogs)
           ↓ All dialogs present
Week 12:   U12 (Integration + Testing)
           ↓ v1 COMPLETE
```

## 6.2 Verification Gates

### Gate 0: Implementation Verification (Before U1)
- [ ] All Gate 0 acceptance criteria met
- [ ] (DTO-only NOT checked at Gate 0)

### Gate 1: Assembly (After U1-U1.5)
- [ ] Application starts successfully
- [ ] DI resolves all services
- [x] **[v1.2]** All DTOs defined ✅
- [x] **[v1.2]** All mappers implemented ✅
- [ ] **[v1.2]** DTO-only compliance check passes

### Gate 2: Forms (After U3-U4)
- [ ] Dynamic forms render
- [ ] All field types work
- [ ] **[v1.2]** No domain imports in view/viewmodel files

### Gate 3: UX (After U5-U7)
- [ ] Recent projects track
- [ ] Undo/redo works (fields AND overrides)
- [ ] Temporal tests T1-T5 pass

### Gate 4: Parity (After U8-U9)
- [ ] Auto-save before generate
- [ ] Override cleanup works

### Gate 5: Complete (After U10-U12)
- [ ] RTL layout works
- [ ] All tests pass
- [ ] **[v1.2]** Final DTO-only compliance verified

## 6.3 Success Criteria

v1 is **COMPLETE** when:

1. ✅ Gate 0 passed
2. ✅ All 13 milestones (U1, U1.5, U2-U12) verified
3. ✅ All regression tests pass
4. ✅ Temporal undo tests T1-T5 pass
5. ✅ No P0/P1 bugs open
6. ✅ **[v1.2]** DTO-only compliance verified
7. ✅ User can complete full workflow:
   - Create project
   - Fill all field types
   - Generate Word document
   - Export to PDF
   - Save and reopen
   - Undo/redo changes (including override operations)
   - Switch language

---

# SECTION 7: ARCHITECTURE DECISION RECORDS

## ADR-017: Command-Based Undo Model

**Status**: Accepted
**Updated**: v1.3.1

**Context**:
Plan specifies undo/redo for field changes. v1.2 REQUIRES override operations to also be undoable. Need to choose between snapshot-based and command-based models.

**Decision**:
**Command-based undo model** with explicit state capture.

**Key Rules**:
1. Each undoable operation creates an explicit command with `execute()` and `undo()`
2. Commands capture state BEFORE the operation
3. Computed values are RECOMPUTED on undo, not restored from captured state
4. Undo stack cleared on project close/open, NOT on save

**Consequences**:
- (+) Explicit, predictable behavior
- (+) Memory efficient
- (+) Each command testable in isolation
- (-) Developer must explicitly specify captured state

---

## ADR-020: DTO-Only Presentation Layer

**Status**: Accepted

**Context**:
Need to enforce strict decoupling between presentation and domain layers.

**Decision**:
**DTO-ONLY is a HARD RULE for v1.2 and beyond.**

1. Presentation layer MUST NEVER import from `doc_helper.domain`
2. All data flowing to presentation MUST be DTOs
3. Domain→DTO mapping MUST happen in Application layer
4. Static import analysis enforces this rule

**Consequences**:
- (+) Strict decoupling
- (+) Easier testing
- (+) Domain can evolve independently
- (-) More code (DTOs + mappers)

---

## ADR-021: UndoState DTO Isolation

**Status**: Accepted

**Context**:
Need to distinguish between DTOs for UI display and DTOs for undo state capture.

**Decision**:
**Separate UndoState DTOs from UI DTOs.**

```
application/dto/
├── ui/          # For presentation layer
└── undo/        # INTERNAL to application layer ONLY
```

**Rules**:
- UI DTOs: `{Name}DTO` - can be imported by presentation
- UndoState DTOs: `{Name}UndoStateDTO` - NEVER imported by presentation

**Consequences**:
- (+) Clear separation of concerns
- (+) UndoState DTOs can evolve independently
- (+) Prevents misuse of internal undo state

---

# Appendix A: File Index

### Files to Create

```
src/doc_helper/infrastructure/di/__init__.py
src/doc_helper/infrastructure/di/container.py
src/doc_helper/application/dto/ui/__init__.py
src/doc_helper/application/dto/ui/project_dto.py
src/doc_helper/application/dto/ui/entity_dto.py
src/doc_helper/application/dto/ui/field_dto.py
src/doc_helper/application/dto/ui/validation_dto.py
src/doc_helper/application/dto/ui/control_dto.py
src/doc_helper/application/dto/ui/override_dto.py
src/doc_helper/application/dto/ui/document_dto.py
src/doc_helper/application/dto/undo/__init__.py
src/doc_helper/application/dto/undo/field_undo_state.py
src/doc_helper/application/dto/undo/override_undo_state.py
src/doc_helper/application/dto/undo/validation_undo_state.py
src/doc_helper/application/mappers/__init__.py
src/doc_helper/application/mappers/project_mapper.py
src/doc_helper/application/mappers/field_mapper.py
src/doc_helper/application/mappers/validation_mapper.py
src/doc_helper/application/mappers/override_mapper.py
src/doc_helper/infrastructure/i18n/__init__.py
src/doc_helper/infrastructure/i18n/json_translation_service.py
src/doc_helper/infrastructure/filesystem/recent_projects_storage.py
src/doc_helper/infrastructure/events/in_memory_bus.py
src/doc_helper/domain/file/__init__.py
src/doc_helper/domain/file/entities/attachment.py
src/doc_helper/domain/file/value_objects/figure_number.py
src/doc_helper/presentation/factories/field_widget_factory.py
src/doc_helper/presentation/adapters/qt_translation_adapter.py
src/doc_helper/presentation/adapters/history_adapter.py
src/doc_helper/presentation/adapters/navigation_adapter.py
src/doc_helper/presentation/dialogs/settings_dialog.py
src/doc_helper/presentation/dialogs/template_dialog.py
src/doc_helper/presentation/dialogs/override_dialog.py
src/doc_helper/presentation/dialogs/conflict_dialog.py
src/doc_helper/presentation/dialogs/figure_numbering_dialog.py
src/doc_helper/application/commands/history/field_commands.py
src/doc_helper/application/commands/history/override_commands.py
scripts/check_dto_compliance.py
```

---

# Appendix B: Reference Documents

- **plan.md**: Authoritative v1 plan (FROZEN)
- **CLAUDE.md**: Implementation rules reference
- **AGENT_RULES.md**: Execution rules
- **adrs/**: Architecture Decision Records

---

# Appendix C: Change Log

## FINAL (2026-01-20)

| Source | Content Merged |
|--------|----------------|
| v1.0 | Implementation inventory, legacy parity matrix |
| v1.1 | Gate 0, MVVM rules, v2+ upgrade path, ADRs 014-019 |
| v1.2 | DTO-only HARD RULE, U1.5 milestone, ADR-020 |
| v1.3 | H1-H5 hardening, command-based undo, ADR-021, temporal tests |
| v1.3.1 | Undo stack clearing rules (close/open, not save), computed values wording |

**U1.5 Status**: Marked as DONE

---

# DEPRECATED VERSIONS

The following versions are **SUPERSEDED** by this FINAL document and should no longer be referenced:

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| v1.0 | 2026-01-20 | **DEPRECATED** | Initial inventory, no Gate 0 |
| v1.1 | 2026-01-20 | **DEPRECATED** | Added Gate 0, MVVM rules |
| v1.2 | 2026-01-20 | **DEPRECATED** | Added DTO-only, U1.5 |
| v1.3 | 2026-01-20 | **DEPRECATED** | Added H1-H5 hardening |
| v1.3.1 | 2026-01-20 | **DEPRECATED** | Patched undo stack rules |

**This FINAL version is the single source of truth.**

---

*End of Unified Upgrade Plan FINAL*

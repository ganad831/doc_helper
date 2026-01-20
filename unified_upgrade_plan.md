# Doc Helper: Unified Upgrade Plan v1.3 (Hardened)

**Document Version**: 1.3.1
**Date**: 2026-01-20
**Status**: FINAL HARDENED REVISION (Patched)
**Author**: Architecture Review (AI-Assisted)

---

## v1.3 Hardening Summary

This revision is a **precision hardening pass** - NO new features, NO scope changes. Only clarifications to remove ambiguity and execution risk.

### Changes from v1.2:

| # | Area | Change | Rationale |
|---|------|--------|-----------|
| H1 | ADR-017 | **Explicit COMMAND-BASED undo model** | Removes ambiguity between command vs snapshot |
| H2 | Milestone U6 | **Separate UndoStateDTOs from UI DTOs** | Undo data must not pollute UI contracts |
| H3 | Milestone U1.5 | **Mapper responsibility clarified** | Mappers do NOT reverse-map for undo |
| H4 | Section 5.2 | **Temporal undo test scenarios** | Mandatory test coverage for undo edge cases |
| H5 | ADR-017 | **Explicit state capture specification** | What is/isn't captured at each boundary |
| H6 | ADR-021 | **NEW: UndoState DTO Isolation** | Formal ADR for undo state separation |

---

## H1: COMMAND-BASED UNDO MODEL (Explicit Choice)

> **[v1.3 HARDENING]** The undo/redo system uses **COMMAND-BASED** model, NOT snapshot-based.

### Why Command-Based (Not Snapshot)

| Factor | Command-Based | Snapshot-Based |
|--------|--------------|----------------|
| Memory | O(n) per change | O(n) × state_size per change |
| Precision | Captures exactly what changed | Captures entire state |
| Debugging | Clear: "what command was executed?" | Opaque: "what diff exists?" |
| Cascade support | Natural: command triggers recalc | Complex: must diff and replay |
| Partial undo | Supported: undo specific command | Not supported: all-or-nothing |

**Decision**: Command-based undo is the ONLY supported model for v1.

### Undo Model Specification

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMMAND-BASED UNDO MODEL                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  USER ACTION                                                             │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────┐                                                         │
│  │ Create      │ ◄── UndoableCommand captures:                          │
│  │ Undoable    │     • field_id (what field?)                           │
│  │ Command     │     • previous_value (what was it before?)             │
│  │             │     • new_value (what is it now?)                       │
│  │             │     • command_type (field_edit | override_accept | ...) │
│  └──────┬──────┘                                                         │
│         │                                                                │
│         ▼                                                                │
│  ┌─────────────┐                                                         │
│  │ Execute     │ ◄── Applies change to domain via Application layer     │
│  │ Command     │     Domain services triggered (formula, control)       │
│  └──────┬──────┘     Event bus propagates side effects                   │
│         │                                                                │
│         ▼                                                                │
│  ┌─────────────┐                                                         │
│  │ Push to     │ ◄── UndoStack (LIFO)                                   │
│  │ Undo Stack  │     • Max depth: 100 (configurable)                    │
│  └─────────────┘     • Cleared on: project close, project open           │
│                      • NOT cleared on: project save                      │
│                                                                          │
│  UNDO (Ctrl+Z):                                                          │
│  1. Pop command from UndoStack                                           │
│  2. Call command.undo(services) → restores previous_value               │
│  3. Push command to RedoStack                                            │
│  4. Side effects cascade via event bus                                   │
│                                                                          │
│  REDO (Ctrl+Y):                                                          │
│  1. Pop command from RedoStack                                           │
│  2. Call command.redo(services) → reapplies new_value                   │
│  3. Push command to UndoStack                                            │
│  4. Side effects cascade via event bus                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## H2: UNDO-STATE DTOs vs UI DTOs (Strict Separation)

> **[v1.3 HARDENING]** Internal undo-state DTOs are SEPARATE from UI-facing DTOs.

### Why Separate?

| Concern | UI DTOs | UndoState DTOs |
|---------|---------|----------------|
| **Purpose** | Display data to user | Capture state for reversal |
| **Audience** | ViewModels, Widgets | Undo engine only |
| **Mutability** | Immutable (frozen) | Immutable (frozen) |
| **Content** | User-friendly display values | Raw values for restoration |
| **Lifetime** | Request/response | Stored in undo stack |
| **Location** | `application/dto/` | `application/undo/` |

### DTO Hierarchy (v1.3)

```
application/
├── dto/                          # UI-FACING DTOs (Presentation can import)
│   ├── __init__.py
│   ├── project_dto.py            # ProjectDTO, ProjectSummaryDTO
│   ├── field_dto.py              # FieldDefinitionDTO, FieldValueDTO
│   ├── validation_dto.py         # ValidationResultDTO
│   ├── override_dto.py           # OverrideDTO, OverrideStateDTO
│   └── ...
│
├── undo/                         # UNDO-STATE DTOs (Internal to Application)
│   ├── __init__.py
│   ├── undo_state_dto.py         # UndoFieldState, UndoOverrideState
│   ├── undo_command.py           # UndoableCommand interface
│   ├── field_undo_command.py     # SetFieldValueCommand
│   └── override_undo_command.py  # AcceptOverrideCommand, RejectOverrideCommand
│
└── mappers/                      # Domain → DTO mappers
    └── ...
```

### UI DTO Example (Presentation can import)

```python
# application/dto/override_dto.py
# This DTO is for DISPLAY purposes only

@dataclass(frozen=True)
class OverrideDTO:
    """UI-facing override data for display in dialogs/lists."""
    id: str                    # Override ID as string
    field_id: str              # Field ID as string
    field_label: str           # Human-readable field name
    system_value: str          # Display-formatted system value
    report_value: str          # Display-formatted report value
    state: str                 # "PENDING" | "ACCEPTED" | "SYNCED" | "INVALID"
    can_accept: bool           # Pre-computed: is accept action available?
    can_reject: bool           # Pre-computed: is reject action available?

# ❌ FORBIDDEN in UI DTO:
#    - Previous values for undo
#    - Raw domain types
#    - Internal state for restoration
```

### UndoState DTO Example (Internal to Application)

```python
# application/undo/undo_state_dto.py
# This DTO is for UNDO ENGINE only - NEVER crosses to Presentation

@dataclass(frozen=True)
class UndoOverrideState:
    """Internal state captured for override undo. NOT for UI display."""
    override_id: str
    field_id: str
    previous_override_state: str      # "PENDING" - state before action
    previous_field_value: Any         # Raw value before override accepted
    accepted_value: Any               # Raw value after override accepted
    affected_formula_fields: tuple[str, ...]  # Field IDs that may need recalc
    timestamp: str                    # ISO timestamp for debugging

# ❌ FORBIDDEN:
#    - This DTO must NEVER be imported in presentation/
#    - This DTO must NEVER be returned from queries
#    - This DTO is internal to the undo engine


@dataclass(frozen=True)
class UndoFieldState:
    """Internal state captured for field value undo. NOT for UI display."""
    field_id: str
    previous_value: Any               # Raw value before change
    new_value: Any                    # Raw value after change
    was_formula_computed: bool        # Was previous value from formula?
    timestamp: str
```

### Enforcement Rules

| Rule | UI DTOs | UndoState DTOs |
|------|---------|----------------|
| Import in `presentation/` | ✅ ALLOWED | ❌ FORBIDDEN |
| Returned by queries | ✅ ALLOWED | ❌ FORBIDDEN |
| Contains `previous_*` fields | ❌ FORBIDDEN | ✅ REQUIRED |
| Contains display formatting | ✅ REQUIRED | ❌ FORBIDDEN |
| Stored in undo stack | ❌ FORBIDDEN | ✅ REQUIRED |

### Static Check (Extended for v1.3)

```python
# scripts/check_dto_compliance.py (v1.3 extension)

# Add check for undo DTO leakage
FORBIDDEN_UNDO_IMPORTS = [
    "doc_helper.application.undo",      # Entire undo module
    "UndoFieldState",                   # Specific undo DTOs
    "UndoOverrideState",
]

def check_undo_leakage(filepath: Path) -> list[str]:
    """Check that presentation does not import undo-state DTOs."""
    violations = []
    # ... check for FORBIDDEN_UNDO_IMPORTS in presentation/ files
    return violations
```

---

## H3: MAPPER RESPONSIBILITY (Clarified for Undo)

> **[v1.3 HARDENING]** Mappers are ONE-WAY (Domain → DTO). They do NOT reconstruct domain state from DTOs.

### What Mappers DO

```python
# application/mappers/override_mapper.py

class OverrideMapper:
    """Maps Override domain aggregate to OverrideDTO for UI display."""

    @staticmethod
    def to_dto(override: Override, field_label: str) -> OverrideDTO:
        """Domain → DTO (ONE WAY)"""
        return OverrideDTO(
            id=str(override.id.value),
            field_id=str(override.field_id.value),
            field_label=field_label,
            system_value=format_for_display(override.system_value),
            report_value=format_for_display(override.report_value),
            state=override.state.value,
            can_accept=override.can_accept(),
            can_reject=override.can_reject(),
        )

    # ❌ FORBIDDEN: No to_domain() method
    # ❌ FORBIDDEN: No from_dto() method
    # ❌ FORBIDDEN: No reverse mapping
```

### What Mappers DO NOT DO

```python
# ❌ FORBIDDEN: Reverse mapping for undo
class OverrideMapper:
    @staticmethod
    def to_domain(dto: OverrideDTO) -> Override:  # ❌ FORBIDDEN
        """This method must NOT exist."""
        # DTOs are not persistence/rehydration mechanism
        # Undo works via commands, not DTO reverse-mapping
        raise NotImplementedError("Mappers are one-way only")
```

### How Undo Actually Works (Without Reverse Mapping)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    UNDO FLOW (Command-Based)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ACCEPT OVERRIDE:                                                        │
│  1. AcceptOverrideCommand created with:                                  │
│     - override_id (from UI selection)                                    │
│     - UndoOverrideState captured BEFORE execution                        │
│                                                                          │
│  2. Command executes:                                                    │
│     override_service.accept(override_id)                                 │
│     → Domain state changes (Override.state = ACCEPTED)                   │
│     → Field value changes (field gets override value)                    │
│     → Event published (FormulaService recalculates dependents)           │
│                                                                          │
│  3. Command pushed to UndoStack                                          │
│                                                                          │
│  UNDO ACCEPT OVERRIDE:                                                   │
│  1. Pop command from UndoStack                                           │
│                                                                          │
│  2. Command.undo() executes:                                             │
│     override_service.restore_to_pending(override_id)                     │
│     → Domain state changes (Override.state = PENDING)                    │
│                                                                          │
│     field_service.set_value(field_id, previous_field_value)              │
│     → Field value restored                                               │
│     → Event published (FormulaService recalculates dependents)           │
│                                                                          │
│  NOTE: At no point is a DTO reverse-mapped to reconstruct domain state.  │
│        The UndoOverrideState contains raw values and IDs, not DTOs.      │
│        The domain is restored via service method calls, not DTO parsing. │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## H4: TEMPORAL UNDO TEST SCENARIOS (Mandatory)

> **[v1.3 HARDENING]** These test scenarios are REQUIRED for v1 completion.

### Test Category: Override Undo Temporal Sequences

```python
# tests/unit/application/undo/test_override_undo_temporal.py

class TestOverrideUndoTemporalSequences:
    """
    Temporal undo tests ensure correct behavior across
    sequences of operations, not just single undo/redo.
    """

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SCENARIO T1: Accept → Undo → Redo
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_accept_undo_redo_sequence(self):
        """
        T1: Accept override → Undo → Redo

        GIVEN: Field F1 has system value "100", override suggests "150"
        WHEN:  User accepts override
        THEN:  F1 = "150", override state = ACCEPTED

        WHEN:  User presses Ctrl+Z (undo)
        THEN:  F1 = "100", override state = PENDING

        WHEN:  User presses Ctrl+Y (redo)
        THEN:  F1 = "150", override state = ACCEPTED (restored exactly)
        """
        # Arrange
        project = create_project_with_override(
            field_id="F1",
            system_value="100",
            override_value="150"
        )
        undo_manager = UndoManager()
        override_service = OverrideService(project)
        field_service = FieldService(project)

        # Act 1: Accept override
        accept_command = AcceptOverrideCommand(
            override_id="override-1",
            services=ServiceBundle(override_service, field_service)
        )
        undo_manager.execute(accept_command)

        # Assert 1: Override accepted
        assert project.get_field_value("F1") == "150"
        assert project.get_override("override-1").state == OverrideState.ACCEPTED

        # Act 2: Undo
        undo_manager.undo()

        # Assert 2: Restored to before accept
        assert project.get_field_value("F1") == "100"
        assert project.get_override("override-1").state == OverrideState.PENDING

        # Act 3: Redo
        undo_manager.redo()

        # Assert 3: Re-applied exactly
        assert project.get_field_value("F1") == "150"
        assert project.get_override("override-1").state == OverrideState.ACCEPTED

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SCENARIO T2: Accept → Field Edit → Undo Override
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_accept_field_edit_undo_override(self):
        """
        T2: Accept override → Field edit → Undo just the override

        GIVEN: Field F1 has system value "100", override suggests "150"
        WHEN:  User accepts override (F1 = "150")
        AND:   User edits F1 to "200" (separate action)
        AND:   User undoes TWICE

        THEN:  First undo: F1 = "150" (reverts field edit)
        THEN:  Second undo: F1 = "100", override = PENDING (reverts accept)

        This tests that undo stack correctly separates:
        - Override accept command
        - Field edit command
        """
        # Arrange
        project = create_project_with_override("F1", "100", "150")
        undo_manager = UndoManager()

        # Act 1: Accept override
        undo_manager.execute(AcceptOverrideCommand("override-1", ...))
        assert project.get_field_value("F1") == "150"

        # Act 2: User edits field (separate command)
        undo_manager.execute(SetFieldValueCommand("F1", "150", "200", ...))
        assert project.get_field_value("F1") == "200"

        # Act 3: First undo (reverts field edit)
        undo_manager.undo()
        assert project.get_field_value("F1") == "150"
        assert project.get_override("override-1").state == OverrideState.ACCEPTED

        # Act 4: Second undo (reverts override accept)
        undo_manager.undo()
        assert project.get_field_value("F1") == "100"
        assert project.get_override("override-1").state == OverrideState.PENDING

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SCENARIO T3: Override + Formula Cascade → Undo → Recompute Consistency
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_override_formula_cascade_undo(self):
        """
        T3: Accept override on field that affects formula → Undo → Verify recompute

        GIVEN: Field F1 (NUMBER) = 10
               Field F2 (CALCULATED) = {{F1}} * 2 = 20
               Override on F1 suggests "50"

        WHEN:  User accepts override on F1
        THEN:  F1 = 50, F2 = 100 (formula recomputed)

        WHEN:  User undoes accept
        THEN:  F1 = 10, F2 = 20 (formula recomputed back)

        This tests that formula cascade is correctly handled during undo.
        """
        # Arrange
        project = create_project_with_formula(
            field_f1=FieldDefinition(id="F1", type=FieldType.NUMBER),
            field_f2=FieldDefinition(id="F2", type=FieldType.CALCULATED, formula="{{F1}} * 2"),
            initial_f1=10
        )
        # F2 should be 20
        assert project.get_field_value("F2") == 20

        # Add override suggesting F1 = 50
        project.add_override("F1", system_value=10, report_value=50)

        undo_manager = UndoManager()

        # Act 1: Accept override
        undo_manager.execute(AcceptOverrideCommand("override-f1", ...))

        # Assert 1: Formula cascaded
        assert project.get_field_value("F1") == 50
        assert project.get_field_value("F2") == 100  # 50 * 2

        # Act 2: Undo
        undo_manager.undo()

        # Assert 2: Formula re-cascaded
        assert project.get_field_value("F1") == 10
        assert project.get_field_value("F2") == 20  # 10 * 2 (recomputed)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SCENARIO T4: Multiple Overrides → Interleaved Undos
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_multiple_overrides_interleaved_undo(self):
        """
        T4: Accept multiple overrides → Undo in reverse order

        GIVEN: F1 = 10 (override: 15)
               F2 = 20 (override: 25)

        WHEN:  Accept F1 override, then accept F2 override
        THEN:  F1 = 15, F2 = 25

        WHEN:  Undo once
        THEN:  F1 = 15, F2 = 20 (F2 override reverted)

        WHEN:  Undo again
        THEN:  F1 = 10, F2 = 20 (F1 override reverted)
        """
        pass  # Implementation follows pattern from T1-T3

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SCENARIO T5: Undo Clears Redo Stack on New Action
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_new_action_clears_redo_stack(self):
        """
        T5: Undo → New action → Redo should not work

        GIVEN: User accepts override (F1 = 150)
        WHEN:  User undoes (F1 = 100)
        AND:   User edits F1 to "175" (NEW action, not redo)
        THEN:  Redo stack is CLEARED

        WHEN:  User tries to redo
        THEN:  Nothing happens (redo stack empty)
        """
        pass  # Standard undo/redo semantics
```

### Test Category: Undo State Isolation

```python
# tests/unit/application/undo/test_undo_state_isolation.py

class TestUndoStateIsolation:
    """Tests that UndoState DTOs don't leak into UI layer."""

    def test_ui_dto_does_not_contain_undo_data(self):
        """OverrideDTO must not contain previous_* fields."""
        dto = OverrideDTO(
            id="override-1",
            field_id="F1",
            field_label="Field 1",
            system_value="100",
            report_value="150",
            state="PENDING",
            can_accept=True,
            can_reject=True,
        )

        # Assert: No undo-related fields
        assert not hasattr(dto, "previous_state")
        assert not hasattr(dto, "previous_field_value")
        assert not hasattr(dto, "undo_data")

    def test_undo_state_dto_not_importable_from_presentation(self):
        """Verify static analysis catches undo import in presentation."""
        # This is verified by check_dto_compliance.py script
        pass

    def test_query_returns_ui_dto_not_undo_state(self):
        """GetOverrideQuery returns OverrideDTO, not UndoOverrideState."""
        query = GetOverrideQuery(repository, mapper)
        result = query.execute("override-1")

        assert isinstance(result.unwrap(), OverrideDTO)
        assert not isinstance(result.unwrap(), UndoOverrideState)
```

---

## H5: STATE CAPTURE SPECIFICATION

> **[v1.3 HARDENING]** Explicit specification of what IS and IS NOT captured at each boundary.

### Field Value Change - State Captured

| Captured | Value | Purpose |
|----------|-------|---------|
| `field_id` | `"F1"` | Identify target field |
| `previous_value` | `"100"` (raw) | Value to restore on undo |
| `new_value` | `"150"` (raw) | Value to restore on redo |
| `was_formula_computed` | `true/false` | Know if previous was formula result |
| `timestamp` | ISO string | Debugging, ordering |

| NOT Captured | Reason |
|--------------|--------|
| Dependent formula results | Recomputed via event cascade |
| Validation state | Recomputed after value change |
| UI display format | UI layer concern |
| Widget state | Presentation layer concern |

### Override Accept - State Captured

| Captured | Value | Purpose |
|----------|-------|---------|
| `override_id` | `"override-1"` | Identify target override |
| `field_id` | `"F1"` | Know which field affected |
| `previous_override_state` | `"PENDING"` | State to restore on undo |
| `previous_field_value` | `"100"` (raw) | Field value to restore on undo |
| `accepted_value` | `"150"` (raw) | Value to restore on redo |
| `affected_formula_fields` | `["F2", "F5"]` | Fields that depend on this (for debugging) |
| `timestamp` | ISO string | Debugging, ordering |

| NOT Captured | Reason |
|--------------|--------|
| Formula recomputation results | Recomputed via event cascade |
| Control visibility changes | Recomputed via event cascade |
| Override DTO display formatting | UI layer concern |
| Conflict state changes | Recomputed from override states |

---

## ADR-021: UndoState DTO Isolation (NEW in v1.3)

**Status**: Accepted

**Context**:
v1.2 added undo/redo for override operations but didn't specify how undo state data should be stored without polluting UI-facing DTOs.

**Decision**:
Create a separate `application/undo/` module with internal DTOs that:
1. Are NEVER returned from queries
2. Are NEVER imported in presentation layer
3. Contain raw values for state restoration, not display-formatted values
4. Are stored only in the undo stack

**Rationale**:
- UI DTOs should be minimal and focused on display
- Undo state needs previous values which are irrelevant to UI
- Separation enables independent evolution of UI vs undo concerns
- Static analysis can enforce the boundary

**Consequences**:
- (+) Clean separation of concerns
- (+) UI DTOs stay minimal
- (+) Undo logic can evolve independently
- (-) Two DTO hierarchies to maintain
- (-) Some duplication (field_id appears in both)

---

## Milestone U6 (Updated for v1.3)

### Milestone U6: Undo/Redo System (P1 Important)

> **[CHANGED in v1.3]** Explicit command-based model, separate UndoState DTOs

**Goal**: Implement command-based undo/redo for field changes AND override operations

**Model**: COMMAND-BASED (not snapshot)

**Scope**:
- Create undo command infrastructure in `application/undo/`
- Create UndoState DTOs (internal, NOT for UI)
- Implement field value change commands
- Implement override state transition commands
- Connect Ctrl+Z/Ctrl+Y shortcuts

**Directory Structure**:
```
application/
├── dto/                          # UI-facing DTOs (existing)
│   └── override_dto.py           # OverrideDTO (for display)
│
├── undo/                         # [v1.3] Undo engine (internal)
│   ├── __init__.py
│   ├── undo_manager.py           # UndoStack, RedoStack, execute/undo/redo
│   ├── undo_state_dto.py         # UndoFieldState, UndoOverrideState
│   ├── undoable_command.py       # UndoableCommand interface
│   ├── field_undo_command.py     # SetFieldValueCommand
│   └── override_undo_command.py  # AcceptOverrideCommand, RejectOverrideCommand
```

**Verification** (v1.3 expanded):
- [ ] Ctrl+Z undoes field changes
- [ ] Ctrl+Y redoes field changes
- [ ] Ctrl+Z undoes override accept/reject/sync
- [ ] Ctrl+Y redoes override accept/reject/sync
- [ ] Undoing override triggers recomputation of dependent formulas (values match pre-action state)
- [ ] History clears on project close and project open (NOT on save)
- [ ] Menu shows undo/redo state
- [ ] **[v1.3]** T1 test passes: Accept → Undo → Redo
- [ ] **[v1.3]** T2 test passes: Accept → Field Edit → Undo Override
- [ ] **[v1.3]** T3 test passes: Override + Formula Cascade → Undo → Recompute
- [ ] **[v1.3]** UndoState DTOs not importable in presentation (static check)

**Estimated Effort**: 4-6 days

---

## Milestone U1.5 (Updated for v1.3)

### Milestone U1.5: DTO Definitions & Mapping (P0 Critical)

> **[CLARIFIED in v1.3]** Mappers are one-way only. No reverse mapping for undo.

**Mapping Rules (v1.3 Clarified)**:
1. Mappers live ONLY in `application/mappers/`
2. Mappers are ONE-WAY: Domain → DTO only
3. **[v1.3]** NO `to_domain()` or `from_dto()` methods
4. **[v1.3]** Undo does NOT use reverse mapping
5. **[v1.3]** UndoState DTOs are separate from UI DTOs
6. All mappers have unit tests
7. DTOs are frozen dataclasses (immutable)
8. Domain objects NEVER leak past Application layer boundary

**Files Affected (v1.3 addition)**:
```
src/doc_helper/application/undo/__init__.py           # [v1.3]
src/doc_helper/application/undo/undo_manager.py       # [v1.3]
src/doc_helper/application/undo/undo_state_dto.py     # [v1.3]
src/doc_helper/application/undo/undoable_command.py   # [v1.3]
tests/unit/application/undo/                          # [v1.3]
tests/unit/application/undo/test_override_undo_temporal.py  # [v1.3]
```

---

## Section 5.2: Testing Strategy (v1.3 Addition)

### 5.2.7 Temporal Undo Test Requirements (v1.3)

> **[NEW in v1.3]** Mandatory test scenarios for undo/redo edge cases.

**Required Test Scenarios**:

| ID | Scenario | Description | Required |
|----|----------|-------------|----------|
| T1 | Accept → Undo → Redo | Full cycle through undo/redo | ✅ MANDATORY |
| T2 | Accept → Edit → Undo × 2 | Interleaved undo of different command types | ✅ MANDATORY |
| T3 | Override → Formula Cascade → Undo | Formula recomputes correctly after undo | ✅ MANDATORY |
| T4 | Multiple Overrides → Interleaved Undo | Correct LIFO order with multiple overrides | ✅ MANDATORY |
| T5 | New Action Clears Redo | Standard undo semantics verification | ✅ MANDATORY |
| T6 | UndoState DTO Isolation | Static analysis of import boundaries | ✅ MANDATORY |

**Test Execution Order**:
These tests must pass before U6 milestone is considered complete.

```bash
# Run temporal undo tests
.venv/Scripts/python -m pytest tests/unit/application/undo/test_override_undo_temporal.py -v

# Expected output:
# test_accept_undo_redo_sequence PASSED
# test_accept_field_edit_undo_override PASSED
# test_override_formula_cascade_undo PASSED
# test_multiple_overrides_interleaved_undo PASSED
# test_new_action_clears_redo_stack PASSED
```

---

## Appendix C: Change Log (v1.3)

### v1.3.1 (2026-01-20) - Micro-Revision Patch

| Section | Change Type | Description |
|---------|-------------|-------------|
| H1 | PATCH | Undo stack cleared on project close/open, NOT on save |
| U6 | PATCH | Computed values wording aligned: recomputed, not restored |

### v1.3 (2026-01-20) - Hardening Pass

| Section | Change Type | Description |
|---------|-------------|-------------|
| H1 | HARDENED | Explicit COMMAND-BASED undo model chosen |
| H2 | HARDENED | Separate UndoState DTOs from UI DTOs |
| H3 | HARDENED | Mapper responsibility clarified (one-way only) |
| H4 | HARDENED | Temporal undo test scenarios mandatory |
| H5 | HARDENED | State capture specification explicit |
| ADR-017 | HARDENED | Full command-based model specification |
| ADR-021 | NEW | UndoState DTO Isolation |
| U1.5 | CLARIFIED | No reverse mapping for undo |
| U6 | EXPANDED | UndoState DTO structure, temporal tests |
| 5.2.7 | NEW | Temporal undo test requirements |

---

*End of Unified Upgrade Plan v1.3 (Hardened)*

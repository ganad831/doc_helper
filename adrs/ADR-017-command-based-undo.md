# ADR-017: Command-Based Undo Model

**Status**: Accepted

**Context**:
The undo/redo system needs a clear model for capturing and restoring state. Two primary options exist:
1. **Snapshot-based**: Capture entire state before each change
2. **Command-based**: Capture only what changed via command objects

The legacy application had implicit undo behavior, and v1 requires explicit specification.

**Decision**:
Use **COMMAND-BASED** undo model exclusively for v1. Each undoable operation creates an `UndoableCommand` that captures:
- `field_id` - what field was changed
- `previous_value` - value before change (raw)
- `new_value` - value after change (raw)
- `command_type` - field_edit, override_accept, override_reject, etc.
- `timestamp` - ISO string for debugging/ordering

**Rationale**:

| Factor | Command-Based | Snapshot-Based |
|--------|--------------|----------------|
| Memory | O(n) per change | O(n) × state_size per change |
| Precision | Captures exactly what changed | Captures entire state |
| Debugging | Clear: "what command was executed?" | Opaque: "what diff exists?" |
| Cascade support | Natural: command triggers recalc | Complex: must diff and replay |
| Partial undo | Supported: undo specific command | Not supported: all-or-nothing |

**Undo Stack Behavior**:
- Max depth: 100 (configurable)
- Cleared on: project close, project open
- NOT cleared on: project save
- New action clears redo stack

**State Capture Specification**:

### Field Value Change - Captured:
| Field | Purpose |
|-------|---------|
| `field_id` | Identify target field |
| `previous_value` | Value to restore on undo |
| `new_value` | Value to restore on redo |
| `was_formula_computed` | Know if previous was formula result |
| `timestamp` | Debugging, ordering |

### Field Value Change - NOT Captured:
| Field | Reason |
|-------|--------|
| Dependent formula results | Recomputed via event cascade |
| Validation state | Recomputed after value change |
| UI display format | UI layer concern |
| Widget state | Presentation layer concern |

### Override Accept - Captured:
| Field | Purpose |
|-------|---------|
| `override_id` | Identify target override |
| `field_id` | Know which field affected |
| `previous_override_state` | State to restore on undo |
| `previous_field_value` | Field value to restore on undo |
| `accepted_value` | Value to restore on redo |
| `affected_formula_fields` | Fields that depend on this (debugging) |
| `timestamp` | Debugging, ordering |

### Override Accept - NOT Captured:
| Field | Reason |
|-------|--------|
| Formula recomputation results | Recomputed via event cascade |
| Control visibility changes | Recomputed via event cascade |
| Override DTO display formatting | UI layer concern |
| Conflict state changes | Recomputed from override states |

**Undo/Redo Flow**:
```
UNDO (Ctrl+Z):
1. Pop command from UndoStack
2. Call command.undo(services) -> restores previous_value
3. Push command to RedoStack
4. Side effects cascade via event bus (formulas recompute)

REDO (Ctrl+Y):
1. Pop command from RedoStack
2. Call command.redo(services) -> reapplies new_value
3. Push command to UndoStack
4. Side effects cascade via event bus
```

**Consequences**:
- (+) Memory efficient - only store what changed
- (+) Precise debugging - know exactly what command was executed
- (+) Natural cascade support - formula recomputation happens automatically
- (+) Supports partial undo for specific operations
- (-) More complex command classes required
- (-) Each undoable operation needs its own command implementation

**Related**:
- ADR-021: UndoState DTO Isolation (separates undo state from UI DTOs)
- AGENT_RULES.md Section 6: Undo/Redo Rules
- unified_upgrade_plan.md H1, H5: Command-based model specification

# ADR-021: UndoState DTO Isolation

**Status**: Accepted

**Context**:
v1.2 added undo/redo for override operations but didn't specify how undo state data should be stored without polluting UI-facing DTOs. The undo system needs to capture previous values, but these values are irrelevant to the UI layer and should not appear in UI-facing DTOs.

**Decision**:
Create a separate `application/undo/` module with internal DTOs that:
1. Are NEVER returned from queries
2. Are NEVER imported in presentation layer
3. Contain raw values for state restoration, not display-formatted values
4. Are stored only in the undo stack

**DTO Hierarchy**:
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
└── mappers/                      # Domain → DTO mappers (one-way only)
    └── ...
```

**Enforcement Rules**:

| Rule | UI DTOs | UndoState DTOs |
|------|---------|----------------|
| Import in `presentation/` | ALLOWED | FORBIDDEN |
| Returned by queries | ALLOWED | FORBIDDEN |
| Contains `previous_*` fields | FORBIDDEN | REQUIRED |
| Contains display formatting | REQUIRED | FORBIDDEN |
| Stored in undo stack | FORBIDDEN | REQUIRED |

**UI DTO Example** (Presentation can import):
```python
@dataclass(frozen=True)
class OverrideDTO:
    """UI-facing override data for display in dialogs/lists."""
    id: str
    field_id: str
    field_label: str           # Human-readable
    system_value: str          # Display-formatted
    report_value: str          # Display-formatted
    state: str                 # "PENDING" | "ACCEPTED" | "SYNCED" | "INVALID"
    can_accept: bool
    can_reject: bool

# FORBIDDEN in UI DTO:
#    - Previous values for undo
#    - Raw domain types
#    - Internal state for restoration
```

**UndoState DTO Example** (Internal to Application):
```python
@dataclass(frozen=True)
class UndoOverrideState:
    """Internal state captured for override undo. NOT for UI display."""
    override_id: str
    field_id: str
    previous_override_state: str      # "PENDING" - state before action
    previous_field_value: Any         # Raw value before override accepted
    accepted_value: Any               # Raw value after override accepted
    affected_formula_fields: tuple[str, ...]
    timestamp: str

# FORBIDDEN:
#    - This DTO must NEVER be imported in presentation/
#    - This DTO must NEVER be returned from queries
#    - This DTO is internal to the undo engine
```

**Static Analysis Check**:
```python
# scripts/check_dto_compliance.py
FORBIDDEN_UNDO_IMPORTS = [
    "doc_helper.application.undo",
    "UndoFieldState",
    "UndoOverrideState",
]

def check_undo_leakage(filepath: Path) -> list[str]:
    """Check that presentation does not import undo-state DTOs."""
    violations = []
    # ... check for FORBIDDEN_UNDO_IMPORTS in presentation/ files
    return violations
```

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

**Related**:
- ADR-017: Command-Based Undo Model (defines the undo approach)
- AGENT_RULES.md Section 4: DTO Rules
- unified_upgrade_plan.md H2: Undo-State DTOs vs UI DTOs

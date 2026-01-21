# ADR-020: DTO-Only MVVM Enforcement

**Status**: Proposed

**Context**:

ADR-005 established MVVM pattern for testability and separation of concerns. However, it did not specify strict boundaries for what data structures may cross the Application→Presentation boundary.

Without explicit rules, presentation code could:
- Import domain entities directly
- Expose domain types in ViewModels
- Bind UI widgets to domain value objects
- Create tight coupling between UI and domain

This creates several risks:
1. **Domain leakage**: UI changes force domain changes (violates dependency inversion)
2. **Testability loss**: Domain tests require UI framework (violates clean architecture)
3. **Refactoring brittleness**: Domain model changes cascade to all UI code
4. **Framework lock-in**: Domain layer becomes coupled to PyQt6

Observed in legacy app:
- `ProjectContext` (domain) inherited `QObject` (PyQt6)
- `DataBinder` (domain) used `QTimer` (PyQt6)
- `HistoryManager` (domain) wrapped `QUndoStack` (PyQt6)

Result: Domain layer untestable without Qt, non-portable to web/mobile.

**Decision**:

Enforce **DTO-Only MVVM** with strict layer boundaries:

### 1. Presentation Layer Import Rules

**ALLOWED**:
```python
from doc_helper.application.dto import *        # UI-facing DTOs only
from doc_helper.application.commands import *   # Command interfaces
from doc_helper.application.queries import *    # Query interfaces
from doc_helper.application.services import *   # Application services
```

**FORBIDDEN**:
```python
from doc_helper.domain.*                        # NO domain imports
from doc_helper.application.undo.*             # NO undo-state DTOs
```

Domain types (entities, value objects, enums, services, repositories) must **never** be imported by presentation code.

### 2. DTO Categories

**UI DTOs** (`application/dto/`):
- May be consumed by presentation layer
- Contain display-ready data (formatted strings, boolean flags)
- Examples: `OverrideDTO`, `FieldValueDTO`, `ProjectDTO`

**Undo-State DTOs** (`application/undo/`):
- Internal to application layer ONLY
- Contain raw state for undo/redo operations
- FORBIDDEN in presentation layer
- Examples: `UndoFieldState`, `UndoOverrideState`

### 3. DTO Properties

All DTOs must be:
- **Immutable** (`@dataclass(frozen=True)`)
- **Behavior-free** (no methods except properties)
- **Serialization-ready** (primitive types or nested DTOs only)

DTOs are NOT:
- Domain entities (no business rules)
- Persistence models (no database mapping)
- View models (presentation has separate ViewModels that consume DTOs)

### 4. Mapping Responsibility

**One-Way Only**: Domain → DTO

```python
# ALLOWED (Application layer)
class OverrideMapper:
    @staticmethod
    def to_dto(override: Override) -> OverrideDTO:
        return OverrideDTO(
            id=str(override.id.value),
            state=override.state.value,
            # ...
        )
```

**FORBIDDEN**: DTO → Domain

```python
# FORBIDDEN
def from_dto(dto: OverrideDTO) -> Override:
    # NO reverse mapping - commands rehydrate domain via repositories
```

Commands operate on domain entities fetched from repositories, NOT rehydrated from DTOs.

### 5. Enforcement Strategy

**Static Analysis** (ADR-024):
- Scan presentation files for forbidden imports
- Check DTO import paths (must be `application.dto`, not `application.undo`)
- Verify no domain types in presentation signatures

**Code Review Checklist**:
- [ ] Presentation imports only from `application.dto`
- [ ] No `from doc_helper.domain.*` in presentation
- [ ] No `from doc_helper.application.undo.*` in presentation
- [ ] All DTO classes are `@dataclass(frozen=True)`
- [ ] DTOs contain no methods (except `__post_init__` if needed)

**Test Requirements**:
- DTO mapping tests (domain → DTO, assert equality)
- No domain imports in presentation test files
- ViewModels testable without domain layer

**Consequences**:

**Positive**:
- (+) **Domain layer 100% pure**: Zero external dependencies, fully portable
- (+) **Testability**: Domain tests run without PyQt6, fast and isolated
- (+) **Refactoring safety**: Domain changes isolated behind DTO boundary
- (+) **Framework independence**: Can port to web/mobile by replacing presentation+DTOs
- (+) **Clear contracts**: DTO structure defines presentation API
- (+) **Type safety**: Presentation cannot accidentally access domain internals

**Costs**:
- (-) **Boilerplate**: Every domain type needs corresponding DTO + mapper
- (-) **Duplication**: Some field names repeated in domain entity and DTO
- (-) **Coordination**: Domain + DTO + mapper must stay synchronized
- (-) **Learning curve**: Developers must understand DTO boundary purpose

**Non-Goals**:

This ADR does NOT cover:
- ViewModel design patterns (separate concern)
- DTO versioning or API compatibility (deferred to v2+ API exposure)
- DTO serialization formats (JSON, protobuf, etc.)
- DTO validation (DTOs are data bags, validation happens in domain/application)

**Related**:
- ADR-005: MVVM Pattern (establishes pattern, this ADR adds strict boundaries)
- ADR-021: UndoState DTO Isolation (defines undo-state DTO category)
- ADR-024: Architectural Compliance Scanning (enforcement tooling)
- AGENT_RULES.md Section 3-4: DTO-Only MVVM rules (binding execution rules)

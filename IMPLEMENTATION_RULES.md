# Doc Helper v1 Implementation Rules

**Status**: Mandatory for all implementation work

This document provides actionable rules for implementing the Doc Helper rebuild according to [plan.md](plan.md). These rules are derived from the architectural decisions, ADRs, and anti-pattern analysis.

---

## 1. SCOPE ENFORCEMENT (v1 Only)

### 1.1 What's IN v1

✅ **IMPLEMENT THESE**:
- Single app type: Soil Investigation (hardcoded path)
- 12 field types (TEXT, TEXTAREA, NUMBER, DATE, DROPDOWN, CHECKBOX, RADIO, CALCULATED, LOOKUP, FILE, IMAGE, TABLE)
- All validation constraints (simple pass/fail, no severity levels)
- Formula system with dependency tracking
- Control system (VALUE_SET, VISIBILITY, ENABLE)
- Override state machine (PENDING → ACCEPTED → SYNCED)
- Document generation (Word/Excel/PDF adapters)
- All 15+ built-in transformers
- Undo/Redo for field value changes only
- Recent projects tracking (simple list, last 5 projects)
- Schema editor for Soil Investigation schema
- Minimal keyboard shortcuts (Ctrl+S, Ctrl+Z/Y)
- Light theme only
- Internationalization (English/Arabic with RTL support)

### 1.2 What's OUT (v2+ Only)

❌ **DO NOT IMPLEMENT THESE**:
- Multiple app types
- App type selection UI
- `AppTypeInfo` aggregate
- `AppTypeDiscoveryService`
- `ExtensionLoader` for custom transformers
- `manifest.json` parsing
- `ValidationSeverity` (ERROR/WARNING/INFO levels)
- Dark mode / theme switching
- Auto-save mechanism
- Field history tracking (`FieldHistoryEntry`)
- Quick search (Ctrl+F)
- Full keyboard navigation adapter
- Import/Export/Clone commands
- Document version history
- Smart output naming with tokens ({YYYY}, {MM}, etc.)

### 1.3 Verification Command

Before submitting ANY code:
```bash
# Check for v2+ features that shouldn't be in v1
grep -r "AppTypeInfo" src/doc_helper/domain/  # Should return nothing
grep -r "ValidationSeverity" src/doc_helper/domain/  # Should return nothing
grep -r "FieldHistoryEntry" src/doc_helper/domain/  # Should return nothing
grep -r "AutoSaveService" src/doc_helper/application/  # Should return nothing
grep -r "manifest.json" src/doc_helper/  # Should return nothing
```

---

## 2. ARCHITECTURE RULES (Mandatory)

### 2.1 Layer Isolation

**Rule**: Dependencies ONLY point inward: Presentation → Application → Domain ← Infrastructure

```
✅ ALLOWED:
presentation/viewmodels/project_vm.py  →  application/commands/create_project.py
application/commands/create_project.py  →  domain/project/entities/project.py
infrastructure/persistence/sqlite/project_repository.py  →  domain/project/repositories.py

❌ FORBIDDEN:
domain/project/entities/project.py  →  infrastructure/persistence/...  # Domain depends on infra
domain/validation/services/validator.py  →  PyQt6.QtCore  # Domain depends on UI framework
application/commands/create_project.py  →  presentation/viewmodels/...  # App depends on UI
```

**Enforcement**:
- NO imports from outer layers in inner layers
- NO `PyQt6` imports in `domain/` or `application/` layers
- NO `sqlite3` imports in `domain/` layer
- Infrastructure implements domain interfaces, never the reverse

### 2.2 Domain Purity (Zero External Dependencies)

**Rule**: Domain layer has ZERO external dependencies (no frameworks, no databases, no filesystem)

```python
# ✅ ALLOWED in domain/
from dataclasses import dataclass
from typing import Protocol, Optional
from enum import Enum
from abc import ABC, abstractmethod

# ❌ FORBIDDEN in domain/
from PyQt6.QtCore import QObject, pyqtSignal  # UI framework
import sqlite3  # Database
import json  # File operations
from pathlib import Path  # Filesystem
```

**Test**: Every domain module should be importable without installing PyQt6, xlwings, or any infrastructure library.

### 2.3 Dependency Injection (No Self-Creation)

**Rule**: Classes NEVER create their own dependencies. All dependencies injected via constructor.

```python
# ❌ BAD: Self-creating dependency
class ProjectService:
    def __init__(self):
        self.repo = SqliteProjectRepository()  # Creating concrete dependency

# ✅ GOOD: Dependency injected
class ProjectService:
    def __init__(self, repo: IProjectRepository):  # Interface injected
        self._repo = repo
```

**Corollary**: No `ServiceContainer.get()` calls outside composition root (`main.py`).

### 2.4 No Hidden Side Effects

**Rule**: Functions/methods do ONLY what their name implies. No unexpected mutations, logging, persistence, or external calls.

```python
# ❌ BAD: Hidden side effects
def get_project(self, project_id: ProjectId) -> Project:
    project = self._repo.get(project_id)
    project.last_accessed = datetime.now()  # Unexpected mutation
    self._repo.save(project)  # Unexpected persistence
    self._logger.info(f"Project {project_id} accessed")  # Hidden logging
    return project

# ✅ GOOD: Does only what name implies
def get_project(self, project_id: ProjectId) -> Project:
    return self._repo.get(project_id)
```

### 2.5 No Logic in Constructors

**Rule**: `__init__` methods ONLY assign dependencies or data. No calculations, decisions, database access, file access, or network calls.

```python
# ❌ BAD: Logic in constructor
class Project:
    def __init__(self, name: str, schema_repo: ISchemaRepository):
        self.name = name
        self.schema = schema_repo.get_default()  # IO in constructor!
        self.created_at = datetime.now()  # Business logic in constructor

# ✅ GOOD: Only assignment
class Project:
    def __init__(self, project_id: ProjectId, name: str, created_at: datetime):
        self._project_id = project_id
        self._name = name
        self._created_at = created_at
```

---

## 3. DOMAIN MODELING RULES

### 3.1 Rich Domain Model (No Anemic Entities)

**Rule**: Entities have behavior methods, not just getters/setters. Business logic lives in entities, not services.

```python
# ❌ BAD: Anemic entity
@dataclass
class Override:
    state: str
    value: Any

# Service does all the work
class OverrideService:
    def accept_override(self, override: Override) -> None:
        if override.state == "PENDING":
            override.state = "ACCEPTED"

# ✅ GOOD: Rich entity
class Override:
    def __init__(self, state: OverrideState, value: Any):
        self._state = state
        self._value = value

    def accept(self) -> Result[None, str]:
        if not self._state.can_transition_to(OverrideState.ACCEPTED):
            return Result.failure("Cannot accept override in current state")
        self._state = OverrideState.ACCEPTED
        return Result.success(None)
```

### 3.2 Strongly Typed Identifiers

**Rule**: Use strongly typed IDs, never raw strings or ints.

```python
# ❌ BAD: Primitive obsession
def get_project(project_id: str) -> Project: ...
def get_field(field_id: str) -> Field: ...
# Can accidentally mix: get_project(field_id)  # Bug!

# ✅ GOOD: Strongly typed
@dataclass(frozen=True)
class ProjectId:
    value: str

@dataclass(frozen=True)
class FieldId:
    value: str

def get_project(project_id: ProjectId) -> Project: ...
def get_field(field_id: FieldId) -> Field: ...
# Cannot mix: get_project(field_id)  # Type error caught by IDE/mypy
```

### 3.3 Immutable Value Objects

**Rule**: All value objects are frozen dataclasses. Updates return new instances.

```python
# ❌ BAD: Mutable value object
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]

result.errors.append("new error")  # Mutation!

# ✅ GOOD: Immutable value object
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: Tuple[str, ...]  # Immutable tuple

# Updates return new instance
def with_error(self, error: str) -> ValidationResult:
    return ValidationResult(
        is_valid=False,
        errors=self.errors + (error,)
    )
```

### 3.4 Explicit State Machines

**Rule**: Use explicit state enums with transition validation, not implicit strings.

```python
# ❌ BAD: Implicit state machine
class Override:
    def __init__(self):
        self.state = "PENDING"  # Magic string

    def accept(self):
        self.state = "ACCEPTED"  # No validation

# ✅ GOOD: Explicit state machine
class OverrideState(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    INVALID = "invalid"
    SYNCED = "synced"

    def can_transition_to(self, target: 'OverrideState') -> bool:
        transitions = {
            OverrideState.PENDING: {OverrideState.ACCEPTED, OverrideState.INVALID},
            OverrideState.ACCEPTED: {OverrideState.SYNCED},
            OverrideState.SYNCED: set(),  # Terminal state
            OverrideState.INVALID: set(),  # Terminal state
        }
        return target in transitions.get(self, set())
```

### 3.5 Result Monad (No Exceptions for Business Logic)

**Rule**: Use `Result[T, E]` for expected failures (business rule violations). Reserve exceptions for bugs.

```python
# ❌ BAD: Exceptions for control flow
def set_value(self, value: str) -> None:
    if not self.validate(value):
        raise ValidationError("Invalid value")  # Expected failure as exception

# ✅ GOOD: Result monad
def set_value(self, value: str) -> Result[None, ValidationError]:
    validation = self.validate(value)
    if validation.is_failure:
        return Result.failure(validation.error)
    self._value = value
    return Result.success(None)
```

---

## 4. TESTING RULES

### 4.1 Test Coverage Requirements

**Minimum coverage**:
- Domain layer: **90%+** (pure logic, easy to test)
- Application layer: **80%+** (orchestration)
- Infrastructure layer: Integration tests for all repositories
- Presentation layer: UI smoke tests for all 12 field types

### 4.2 Test Isolation

**Rule**: Tests NEVER share state. Each test creates its own fixtures.

```python
# ❌ BAD: Shared state
project = Project(...)  # Module-level

def test_add_field():
    project.add_field(...)  # Modifies shared state

def test_remove_field():
    project.remove_field(...)  # Depends on previous test

# ✅ GOOD: Isolated tests
@pytest.fixture
def project():
    return Project(...)

def test_add_field(project):
    project.add_field(...)  # Fresh instance

def test_remove_field(project):
    project.remove_field(...)  # Fresh instance
```

### 4.3 No Real I/O in Unit Tests

**Rule**: Unit tests use fakes/mocks, not real databases, files, or network.

```python
# ❌ BAD: Real database in unit test
def test_create_project():
    repo = SqliteProjectRepository("test.db")  # Real database!
    service = ProjectService(repo)
    ...

# ✅ GOOD: Fake repository
class FakeProjectRepository(IProjectRepository):
    def __init__(self):
        self._projects = {}

    def save(self, project: Project) -> None:
        self._projects[project.id] = project

def test_create_project():
    repo = FakeProjectRepository()  # In-memory fake
    service = ProjectService(repo)
    ...
```

---

## 5. CODE ORGANIZATION RULES

### 5.1 File Size Limits

**Hard limits**:
- Maximum **300 lines** per class
- Maximum **500 lines** per file
- Maximum **10 public methods** per class

**If exceeded**: Violates Single Responsibility Principle. Split the class.

### 5.2 One Class Per File

**Rule**: One primary class per file (except nested classes or tiny helper classes).

```
# ❌ BAD: Multiple classes in one file
transformers.py (1605 LOC, 16 classes)

# ✅ GOOD: One class per file
transformer/implementations/suffix.py
transformer/implementations/prefix.py
transformer/implementations/map.py
...
```

### 5.3 Package Structure

**Rule**: Follow the prescribed folder structure from Section 11 of plan.md exactly.

```
doc_helper/
├── src/doc_helper/
│   ├── domain/           # Pure Python, zero external deps
│   ├── application/      # Commands, queries, services
│   ├── infrastructure/   # SQLite, file system, document adapters
│   └── presentation/     # PyQt6 views, viewmodels, widgets
```

---

## 6. NAMING CONVENTIONS

### 6.1 Standard Vocabulary

| Concept | Use | Avoid |
|---------|-----|-------|
| Retrieve single | `get_*` | `fetch_*`, `retrieve_*`, `find_*` |
| Retrieve multiple | `list_*` | `get_all_*`, `fetch_all_*` |
| Check existence | `exists()` | `has()`, `contains()` |
| Create new | `create_*` | `make_*`, `build_*`, `new_*` |
| Update existing | `update_*` | `modify_*`, `change_*` |
| Delete | `delete_*` | `remove_*`, `destroy_*` |
| Convert | `to_*` | `as_*`, `convert_to_*` |
| Parse from | `from_*` | `parse_*`, `read_*` |

### 6.2 Interface Naming

**Rule**: Interfaces start with `I`, implementations describe the implementation.

```python
# Domain (interface)
class IProjectRepository(Protocol):
    def get(self, project_id: ProjectId) -> Optional[Project]: ...

# Infrastructure (implementation)
class SqliteProjectRepository:  # Implementation name
    def get(self, project_id: ProjectId) -> Optional[Project]: ...
```

---

## 7. ERROR HANDLING RULES

### 7.1 When to Use Result vs Exception

**Use `Result[T, E]` for**:
- Business rule violations (validation failures, invalid state transitions)
- Expected failures (entity not found, file already exists)
- Domain logic failures

**Use Exceptions for**:
- Programming errors (bugs)
- Infrastructure failures (database connection lost, disk full)
- Unexpected failures

```python
# ✅ Result for expected failures
def accept_override(self) -> Result[None, str]:
    if self._state != OverrideState.PENDING:
        return Result.failure("Cannot accept non-pending override")
    ...

# ✅ Exception for bugs
def get_field(self, field_id: FieldId) -> Field:
    if field_id not in self._fields:
        raise ValueError(f"Field {field_id} not found")  # Should never happen
    ...
```

### 7.2 No Bare Except

**Rule**: Never use bare `except:` or `except Exception:`. Catch specific exceptions.

```python
# ❌ BAD: Bare except
try:
    result = operation()
except:  # Catches everything, even KeyboardInterrupt!
    pass

# ✅ GOOD: Specific exception
try:
    result = operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    return Result.failure(str(e))
```

---

## 8. PERSISTENCE RULES

### 8.1 SQL Only in Repositories

**Rule**: SQL queries live ONLY in `infrastructure/persistence/`. Domain and application layers use repository interfaces.

```python
# ❌ BAD: SQL in application service
class ProjectService:
    def get_project(self, project_id: str):
        conn = sqlite3.connect("project.db")
        cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        ...

# ✅ GOOD: SQL in repository
class SqliteProjectRepository:
    def get(self, project_id: ProjectId) -> Optional[Project]:
        cursor = self._conn.execute("SELECT * FROM projects WHERE id = ?", (project_id.value,))
        ...

class ProjectService:
    def __init__(self, repo: IProjectRepository):
        self._repo = repo

    def get_project(self, project_id: ProjectId) -> Project:
        return self._repo.get(project_id)
```

### 8.2 Unit of Work for Transactions

**Rule**: Multi-step operations use Unit of Work pattern for atomicity.

```python
# ❌ BAD: Manual transaction management
def update_project(self, project: Project):
    self._project_repo.save(project)
    self._field_repo.save_all(project.fields)
    # If second save fails, first save is committed!

# ✅ GOOD: Unit of Work
def update_project(self, project: Project):
    with self._uow:
        self._uow.projects.save(project)
        self._uow.fields.save_all(project.fields)
        self._uow.commit()  # Atomic commit
```

---

## 9. UI RULES (Presentation Layer)

### 9.1 No Business Logic in Views

**Rule**: Views contain ONLY UI code. All logic flows through ViewModels.

```python
# ❌ BAD: Logic in view
class ProjectView(QWidget):
    def on_field_changed(self, value: str):
        if self.field.is_required() and not value:  # Business logic in view!
            self.show_error("Field is required")

# ✅ GOOD: Logic in ViewModel
class FieldViewModel:
    def set_value(self, value: str) -> ValidationResult:
        result = self._field.validate(value)  # Logic in ViewModel
        return result

class ProjectView(QWidget):
    def on_field_changed(self, value: str):
        result = self.view_model.set_value(value)
        if result.is_failure:
            self.show_error(result.error)
```

### 9.2 Views Don't Import Domain/Application

**Rule**: Views import only from `presentation/viewmodels/` and `presentation/widgets/`. Never import domain or application.

```python
# ❌ BAD: View imports domain
from doc_helper.domain.project.entities.project import Project  # Direct domain access

class ProjectView(QWidget):
    def __init__(self, project: Project):  # View depends on domain entity
        ...

# ✅ GOOD: View imports ViewModel
from doc_helper.presentation.viewmodels.project_vm import ProjectViewModel

class ProjectView(QWidget):
    def __init__(self, view_model: ProjectViewModel):  # View depends on ViewModel
        ...
```

---

## 10. INTERNATIONALIZATION (i18n) RULES

### 10.1 No Hardcoded UI Strings

**Rule**: All user-facing strings must use translation keys from `ITranslationService`.

```python
# ❌ BAD: Hardcoded English string
button.setText("Save Project")

# ✅ GOOD: Translation key
button.setText(self._translation_service.translate("ui.button.save_project"))
```

### 10.2 RTL Layout Support

**Rule**: All layouts must support RTL (right-to-left) for Arabic.

```python
# ✅ Correct: Use layout direction from translation service
layout.setDirection(
    Qt.LayoutDirection.RightToLeft if self._i18n.is_rtl()
    else Qt.LayoutDirection.LeftToRight
)
```

### 10.3 Translation File Structure

**Rule**: Translation keys follow hierarchical dot notation.

```json
{
  "ui": {
    "button": {
      "save_project": "Save Project",
      "open_project": "Open Project"
    },
    "label": {
      "project_name": "Project Name"
    }
  },
  "error": {
    "validation": {
      "required_field": "This field is required"
    }
  }
}
```

---

## 11. CODE REVIEW CHECKLIST

Before submitting any PR, verify ALL of these:

### Architecture
- [ ] No layer violations (check imports at top of files)
- [ ] No class > 300 LOC
- [ ] All dependencies injected via constructor
- [ ] No v2+ features implemented

### Domain Purity
- [ ] No `PyQt6` imports in `domain/`
- [ ] No `sqlite3` imports in `domain/`
- [ ] No file system operations in `domain/`
- [ ] Entities have behavior methods (not anemic)
- [ ] Value objects are frozen dataclasses

### State Management
- [ ] No global mutable singletons
- [ ] Explicit state machines with transition validation
- [ ] No hidden behavior flags (`_suppress_*`, `_loading`)

### Error Handling
- [ ] `Result[T, E]` for expected failures
- [ ] No bare `except:` clauses
- [ ] Specific exceptions caught

### Testing
- [ ] New domain code has unit tests
- [ ] Tests are isolated (no shared state)
- [ ] No real I/O in unit tests

### UI
- [ ] Views have no business logic
- [ ] Views don't import domain/application
- [ ] State in ViewModels only
- [ ] All UI strings use translation keys

### Persistence
- [ ] SQL only in repositories
- [ ] Multi-step ops use Unit of Work
- [ ] Entities are persistence-ignorant

### Internationalization
- [ ] No hardcoded UI strings
- [ ] All text uses `ITranslationService`
- [ ] RTL layout support implemented

### Legacy App
- [ ] No imports from `legacy_app/`
- [ ] No copied code from `legacy_app/`
- [ ] Legacy app used as behavioral reference only

---

## 12. MILESTONE EXECUTION RULES

### 12.1 Milestone Order

**Rule**: Implement milestones in sequence: M1 → M2 → ... → M12. Do NOT skip ahead.

**Rationale**: Each milestone builds on previous milestones. M8 (Infrastructure) depends on M2-M7 domain interfaces. M11 (Presentation) depends on M10 (Application).

### 12.2 Milestone Definition of Done

**Rule**: A milestone is complete when:
1. All deliverables implemented
2. Unit tests written (90%+ coverage for domain)
3. Integration tests passing (for infrastructure milestones)
4. Code review checklist passes
5. No v2+ features included

### 12.3 Legacy App as Reference Only

**Rule**: Legacy app (`legacy_app/`) is READ-ONLY. Behavior reference only.

**Process**:
1. Inspect `legacy_app/` to understand behavior
2. Describe behavior in plain language
3. Reimplement cleanly in `doc_helper/` following architecture

**Forbidden**:
- ❌ Copying code from `legacy_app/`
- ❌ Importing from `legacy_app/`
- ❌ Modifying `legacy_app/`

---

## 13. CONTINUOUS VALIDATION

### 13.1 Pre-Commit Checks

Run before EVERY commit:

```bash
# Type checking
mypy src/doc_helper/

# Linting
ruff check src/doc_helper/

# Tests
pytest tests/unit/ -v

# Import validation (no domain layer violations)
python scripts/validate_imports.py
```

### 13.2 Import Validation Script

Create `scripts/validate_imports.py`:

```python
#!/usr/bin/env python3
"""Validate that domain layer has no external dependencies."""

import ast
import sys
from pathlib import Path

FORBIDDEN_IN_DOMAIN = [
    "PyQt6", "sqlite3", "xlwings", "docx", "fitz",
    "json", "pathlib.Path", "os.path"
]

def check_imports(file_path: Path) -> list[str]:
    """Return list of forbidden imports found."""
    with open(file_path) as f:
        tree = ast.parse(f.read())

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in FORBIDDEN_IN_DOMAIN:
                    if alias.name.startswith(forbidden):
                        violations.append(f"{file_path}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for forbidden in FORBIDDEN_IN_DOMAIN:
                    if node.module.startswith(forbidden):
                        violations.append(f"{file_path}:{node.lineno}: from {node.module}")

    return violations

def main():
    domain_dir = Path("src/doc_helper/domain")
    violations = []

    for py_file in domain_dir.rglob("*.py"):
        violations.extend(check_imports(py_file))

    if violations:
        print("❌ Domain layer violations found:")
        for v in violations:
            print(f"  {v}")
        sys.exit(1)
    else:
        print("✅ Domain layer is pure (no external dependencies)")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## 14. WHEN IN DOUBT

### 14.1 Decision Tree

```
Question: "Should I implement this feature?"
├─ Is it listed in v1 Definition of Done (Section 2)?
│  ├─ YES → Implement it
│  └─ NO → Is it explicitly marked v2+?
│     ├─ YES → DO NOT implement (defer to v2+)
│     └─ NO → Ask for clarification
│
Question: "Where should this code live?"
├─ Does it have business rules?
│  └─ YES → Domain layer
├─ Does it orchestrate domain operations?
│  └─ YES → Application layer
├─ Does it talk to database/files/external services?
│  └─ YES → Infrastructure layer
├─ Does it display UI or handle user input?
│  └─ YES → Presentation layer
│
Question: "Should I use Result or Exception?"
├─ Is this failure expected (business rule violation)?
│  └─ YES → Use Result[T, E]
├─ Is this a programming error (bug)?
│  └─ YES → Use Exception
│
Question: "Can I use this library in domain layer?"
├─ Is it from Python standard library (typing, enum, dataclasses, abc)?
│  └─ YES → OK to use
├─ Is it an external library?
│  └─ YES → DO NOT use in domain
```

### 14.2 Ask Before

**STOP and ask if**:
- You need to implement a v2+ feature to make v1 work
- You're tempted to violate layer boundaries "just this once"
- You can't figure out where a class should live
- You need to import PyQt6 in domain layer
- A class exceeds 300 lines and you can't see how to split it

---

## 15. QUICK REFERENCE CARD

```
┌─────────────────────────────────────────────────────────────────────┐
│                   DOC HELPER v1 IMPLEMENTATION RULES                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYERS           Domain ← Application ← Presentation               │
│                      ↑                                              │
│                   Infrastructure                                    │
│                                                                     │
│  DOMAIN PURITY    Zero external dependencies                       │
│                   No PyQt6, SQLite, filesystem                      │
│                                                                     │
│  DI               All deps injected via constructor                 │
│                   No ServiceContainer.get() in code                 │
│                                                                     │
│  ERRORS           Result[T, E] for business logic                   │
│                   Exceptions for bugs only                          │
│                                                                     │
│  STATE            Immutable value objects (frozen)                  │
│                   Explicit state machines                           │
│                                                                     │
│  TESTING          90%+ domain coverage                              │
│                   Isolated tests, no shared state                   │
│                                                                     │
│  SIZE LIMITS      300 LOC per class max                             │
│                   10 public methods per class max                   │
│                                                                     │
│  v1 SCOPE         Single app type only                              │
│                   No app type selection                             │
│                   No auto-save, no dark mode                        │
│                   Simple validation (no severity)                   │
│                   English + Arabic i18n                             │
│                                                                     │
│  MILESTONES       Execute in order: M1 → M2 → ... → M12            │
│                   Complete + test before moving on                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Summary

These rules are **mandatory** and **non-negotiable**. They exist to:
1. Prevent regression into legacy app anti-patterns
2. Ensure v1 scope is respected (no feature creep)
3. Maintain architectural integrity
4. Enable long-term maintainability
5. Support clean migration to v2+ features

**Every PR must pass the code review checklist (Section 11) before merge.**

For the reasoning behind these rules, see:
- [plan.md](plan.md) - Complete rebuild plan with architecture
- [adrs/](adrs/) - Architectural Decision Records
- Section 16 of [plan.md](plan.md) - Anti-Pattern Checklist

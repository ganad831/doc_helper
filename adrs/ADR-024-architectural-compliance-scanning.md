# ADR-024: Architectural Compliance Scanning

**Status**: Proposed

**Context**:

Clean Architecture and DTO-Only MVVM (ADR-002, ADR-003, ADR-020) define strict layer boundaries:

```
Presentation → Application only
Application → Domain only
Infrastructure → Domain + Application
Domain → NOTHING (zero external dependencies)
```

Without automated enforcement, these rules degrade over time:
- Developers accidentally import domain types in presentation
- Presentation code imports undo-state DTOs (ADR-021 violation)
- Domain layer imports external frameworks (PyQt6, sqlite3, etc.)
- Reverse dependencies creep in (application imports presentation)

Manual code review catches some violations, but is:
- **Error-prone**: Easy to miss imports in large PRs
- **Inconsistent**: Different reviewers apply rules differently
- **Late feedback**: Violations discovered after implementation complete

Observed in legacy app:
- `core/history/field_commands.py` imported `QUndoCommand` (domain → PyQt6)
- `core/state/project_context.py` imported `pyqtSignal` (domain → PyQt6)
- `core/state/data_binder.py` imported `QTimer` (domain → PyQt6)

Result: Domain layer untestable without Qt, massive refactoring required.

**Decision**:

Implement **Architectural Compliance Scanning** with automated static analysis.

### 1. What Is Scanned

**Check 1: DTO-Only MVVM (ADR-020)**
- **Rule**: Presentation layer MUST NOT have MODULE-LEVEL imports from `doc_helper.domain.*`
- **Allowed**: Function-scope imports (for command parameter conversion only)
- **Rationale**: Module-level imports pollute namespace, function-scope imports are temporary

**Check 2: Undo-State DTO Isolation (ADR-021)**
- **Rule**: Presentation layer MUST NOT import from `doc_helper.application.undo.*`
- **Forbidden types**: `UndoFieldState`, `UndoOverrideState`, any undo-state DTOs
- **Rationale**: Undo-state DTOs are internal to application layer

**Check 3: Domain Layer Purity (ADR-003)**
- **Rule**: Domain layer (`doc_helper.domain.*`) MUST NOT import external frameworks
- **Forbidden imports**: `PyQt6.*`, `sqlite3`, `requests`, file system libraries
- **Allowed imports**: Standard library (typing, dataclasses, abc, etc.)
- **Rationale**: Domain must be framework-independent and testable

**Check 4: Layer Dependency Direction (ADR-002)**
- **Rule**: Dependencies must point inward only
- **Forbidden**:
  - Application imports Presentation
  - Domain imports Application
  - Domain imports Infrastructure
- **Allowed**:
  - Presentation imports Application
  - Application imports Domain
  - Infrastructure imports Domain + Application

### 2. Where It Runs

**Manual Execution**:
```bash
python scripts/check_architecture.py
```
Developer runs before committing changes.

**Pre-Commit Hook (Optional)**:
```bash
# .git/hooks/pre-commit
#!/bin/sh
python scripts/check_architecture.py
if [ $? -ne 0 ]; then
    echo "❌ Architectural compliance check failed"
    echo "Fix violations before committing"
    exit 1
fi
```
Prevents commits with violations (opt-in via `git config`).

**CI Pipeline (Mandatory)**:
```yaml
# .github/workflows/ci.yml or equivalent
- name: Architectural Compliance
  run: python scripts/check_architecture.py
```
Blocks PR merge if violations exist.

**Testing**:
```bash
pytest tests/static_analysis/test_architecture_compliance.py
```
Verify scanner itself works correctly (meta-tests).

### 3. Failure Conditions

**Exit Code 0 (Pass)**:
- No violations found
- All layer boundaries respected
- DTO-only MVVM enforced

**Exit Code 1 (Fail)**:
- Domain imports found in presentation (module-level)
- Undo-state DTO imports found in presentation
- External framework imports found in domain
- Reverse dependency detected (e.g., domain imports application)

**Exit Code 2 (Scanner Error)**:
- Syntax errors in scanned files (report, continue scanning)
- Missing source directories (fail fast)
- Invalid configuration

### 4. False-Positive Handling

**Legitimate Function-Scope Imports**:
```python
# ALLOWED: Function-scope import for command parameter conversion
class ProjectViewModel:
    def create_project(self, name: str) -> None:
        from doc_helper.domain.project.project_ids import ProjectId
        project_id = ProjectId(uuid4())
        self._command_service.create_project(project_id, name)
```
Scanner checks only module-level (`tree.body`), not nested scopes.

**Exemption Mechanism**:
```python
# src/doc_helper/presentation/legacy_compat.py
# EXEMPTION: Legacy compatibility layer (to be removed in v2)
from doc_helper.domain.project import Project  # compliance: exempt (legacy-compat)
```
Inline comment `# compliance: exempt (reason)` allows specific violations.

**Exemption Review**:
- All exemptions logged in scanner output
- Exemptions must include justification
- Exemptions reviewed quarterly (reduce over time)

**Common False Positives**:
- Type hints in comments (not parsed as imports)
- Docstring examples (not executed)
- Test fixtures importing domain (test files exempt from scan)

### 5. Scanner Implementation

**Language**: Python (matches codebase language)

**Approach**: AST parsing (not regex)
```python
import ast

def check_module_level_imports(filepath: Path) -> list[str]:
    tree = ast.parse(filepath.read_text())
    violations = []

    for node in tree.body:  # Only module-level
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("doc_helper.domain"):
                violations.append(f"{filepath}:{node.lineno}")

    return violations
```

**Performance**:
- Scan completes in <5 seconds for entire codebase
- Parallelizable (per-file checks independent)

**Output Format**:
```
================================================================================
ARCHITECTURAL COMPLIANCE SCAN
================================================================================
Checking presentation layer: src/doc_helper/presentation
Forbidden imports: doc_helper.domain.*

Scanning 42 files...

❌ COMPLIANCE CHECK FAILED

Found 2 violation(s):

  src/doc_helper/presentation/views/main_window.py:15: from doc_helper.domain.project import Project
  src/doc_helper/presentation/dialogs/schema_editor.py:8: import doc_helper.domain.schema

RULE VIOLATED:
  Presentation layer MUST NOT have MODULE-LEVEL imports from doc_helper.domain
  (ADR-020: DTO-Only MVVM Enforcement)

FIX:
  1. Remove MODULE-LEVEL domain imports
  2. Use DTOs from doc_helper.application.dto
  3. For command parameters, use function-scope imports

================================================================================
```

### 6. Integration Points

**Development Workflow**:
1. Developer runs `python scripts/check_architecture.py` before commit
2. If violations found, fix before committing
3. If function-scope import needed, ensure it's inside function/method

**CI/CD Pipeline**:
1. Automated scan runs on every PR
2. PR blocked if violations exist
3. Reviewer verifies exemptions (if any)

**Documentation**:
- Scanner usage documented in CONTRIBUTING.md
- Violation fixes documented in ADR-020
- Exemption process documented in this ADR

**Consequences**:

**Positive**:
- (+) **Immediate feedback**: Violations caught before code review
- (+) **Consistent enforcement**: Rules applied uniformly across codebase
- (+) **Prevents regression**: Architectural boundaries maintained over time
- (+) **Educational**: Error messages teach developers the rules
- (+) **Confidence**: Team can refactor knowing boundaries are protected
- (+) **Automation**: Reduces manual review burden

**Costs**:
- (-) **Scanner maintenance**: Keep scanner updated with new rules
- (-) **False positives**: Exemption mechanism adds process overhead
- (-) **Build time**: Adds ~5 seconds to CI pipeline
- (-) **Learning curve**: Developers must understand scan output

**Non-Goals**:

This ADR does NOT cover:
- Code style linting (Black, Ruff handle this)
- Type checking (mypy handles this)
- Security scanning (separate tooling)
- Test coverage enforcement (pytest-cov handles this)
- Runtime behavior validation (tests handle this)
- Performance profiling (separate tooling)

**Related**:
- ADR-002: Clean Architecture + DDD (defines layer boundaries)
- ADR-003: Framework-Independent Domain Layer (defines domain purity rule)
- ADR-020: DTO-Only MVVM Enforcement (defines presentation import rules)
- ADR-021: UndoState DTO Isolation (defines undo-state DTO boundaries)
- AGENT_RULES.md Section 2-3: Architectural layer rules (binding execution rules)

**Implementation Notes**:

Current state (as of 2026-01-21):
- `scripts/check_dto_compliance.py` implements Check 1 (DTO-Only MVVM)
- Other checks (2-4) not yet implemented
- Scanner not yet integrated into CI pipeline
- Exemption mechanism not yet implemented

Future work (Phase A - Active Improvement Backlog):
- Implement remaining checks (2-4)
- Rename script to `scripts/check_architecture.py` (align with documentation)
- Add exemption mechanism
- Integrate into CI pipeline
- Add meta-tests for scanner

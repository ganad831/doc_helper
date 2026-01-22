# V2 Platform Architectural Enforcement Gaps Analysis

**Date**: 2026-01-22
**Phase**: v2 Platform Stabilization and Hardening
**Scope**: Review of app_type_id validation enforcement across all entry points

---

## Executive Summary

Reviewed all architectural entry points where projects are created or loaded. Found **ONE CRITICAL ENFORCEMENT GAP** in the import workflow that allows projects with invalid app_type_id values to bypass registry validation.

### Overall Status
- ✅ **CreateProjectCommand**: Properly enforces AppType validation
- ✅ **OpenProjectCommand**: Properly enforces AppType validation
- ❌ **ImportProjectCommand**: **CRITICAL GAP** - No AppType validation
- ✅ **SqliteProjectRepository**: Correct behavior (dumb persistence, no validation)
- ✅ **Project Domain Entity**: Correct validation scope (non-empty string only)

---

## 1. Enforcement Gap: ImportProjectCommand

### Location
**File**: `src/doc_helper/application/commands/import_project_command.py`
**Lines**: 173-291

### Problem Description

`ImportProjectCommand` accepts projects from `JsonProjectImporter` without validating that `app_type_id` exists in the AppType registry.

**Attack Vector**:
1. User creates JSON interchange file with `app_type_id: "deleted_app"`
2. Imports project using Import dialog
3. `JsonProjectImporter.import_from_file()` creates Project object with unvalidated app_type_id (line 245-250 in `json_project_importer.py`)
4. `ImportProjectCommand` validates field-level data using `ValidationService` (line 217)
5. **BUT** ValidationService does NOT check if app_type_id exists in registry
6. Project is saved to repository with invalid app_type_id (line 264)
7. **Result**: Corrupted project in database that cannot be opened

**Evidence**:
```python
# json_project_importer.py:221
app_type_id = metadata.get("app_type_id", self.DEFAULT_APP_TYPE_ID)

# json_project_importer.py:245-250
project = Project(
    id=new_project_id,
    name=project_name,
    app_type_id=app_type_id,  # ❌ NOT VALIDATED against registry
    entity_definition_id=entity_definition_id,
)

# import_project_command.py:217
validation_result = self._validation_service.validate_project(project)
# ❌ ValidationService validates FIELDS, not project-level app_type_id constraint

# import_project_command.py:264
save_result = self._project_repository.save(project)
# ❌ Project with invalid app_type_id is saved
```

### Impact

**Severity**: **CRITICAL**

- **Data Integrity**: Projects with invalid app_type_id can be created, violating the platform invariant
- **User Experience**: User imports project successfully, but cannot open it later (OpenProjectCommand will fail)
- **Inconsistent Enforcement**: Create/Open enforce AppType validation, Import does not
- **Attack Surface**: Malicious or corrupted JSON files can bypass AppType constraints

### Recommended Fix

**Option A (RECOMMENDED)**: Add AppType validation to ImportProjectCommand

```python
class ImportProjectCommand:
    def __init__(
        self,
        project_repository: IProjectRepository,
        schema_repository: ISchemaRepository,
        project_importer: "IProjectImporter",
        validation_service: ValidationService,
        app_type_registry: IAppTypeRegistry,  # ← ADD THIS
    ) -> None:
        # ...
        self._app_type_registry = app_type_registry

    def execute(self, input_file_path: str | Path) -> Result[ImportResultDTO, str]:
        # ... (existing code: parse file, load schema, import project) ...

        project = import_data.get("project")

        # ← ADD THIS VALIDATION
        # v2 PHASE 4: Validate project's AppType exists in registry
        if not self._app_type_registry.exists(project.app_type_id):
            available = self._app_type_registry.list_app_type_ids()
            available_str = ", ".join(sorted(available)) if available else "none"
            return Success(
                ImportResultDTO(
                    success=False,
                    project_id=None,
                    project_name=project_name,
                    error_message=(
                        f"Cannot import project: AppType '{project.app_type_id}' not found. "
                        f"Available AppTypes: {available_str}. "
                        f"The imported project requires AppType '{project.app_type_id}' which is not installed."
                    ),
                    validation_errors=(),
                    format_version=format_version,
                    source_app_version=source_app_version,
                    warnings=warnings,
                )
            )

        # ... (existing code: validate fields, save project) ...
```

**Rationale**:
- **Consistent with existing pattern**: CreateProjectCommand and OpenProjectCommand validate app_type_id at application layer
- **Separation of concerns**: Infrastructure layer (JsonProjectImporter) remains unaware of AppType registry
- **Clear error message**: User understands why import failed and which AppType is missing
- **Atomic validation**: All validation (format, schema, app_type_id, fields) happens before save

---

## 2. Correctly Enforced Entry Points

### 2.1 CreateProjectCommand ✅

**File**: `src/doc_helper/application/commands/create_project_command.py`
**Lines**: 104-110

**Enforcement**:
```python
# v2 PHASE 3: Validate AppType exists in registry
if not self._app_type_registry.exists(effective_app_type_id):
    available = self._app_type_registry.list_app_type_ids()
    available_str = ", ".join(sorted(available)) if available else "none"
    return Failure(
        f"AppType '{effective_app_type_id}' not found. "
        f"Available AppTypes: {available_str}"
    )
```

**Status**: ✅ **CORRECT** - Validates before creating Project object

---

### 2.2 OpenProjectCommand ✅

**File**: `src/doc_helper/application/commands/open_project_command.py`
**Lines**: 119-126

**Enforcement**:
```python
# v2 PHASE 3: Validate project's AppType exists in registry
if not self._app_type_registry.exists(project.app_type_id):
    available = self._app_type_registry.list_app_type_ids()
    available_str = ", ".join(sorted(available)) if available else "none"
    return Failure(
        f"Cannot open project: AppType '{project.app_type_id}' not found. "
        f"Available AppTypes: {available_str}. "
        f"The project requires AppType '{project.app_type_id}' which is not installed or registered."
    )
```

**Status**: ✅ **CORRECT** - Validates after loading Project from database

---

### 2.3 SqliteProjectRepository ✅

**File**: `src/doc_helper/infrastructure/persistence/sqlite_project_repository.py`

**Behavior**:
- `save()` method (lines 49-144): Saves Project without validation
- `get_by_id()` method (lines 146-229): Reconstructs Project from database without validation

**Status**: ✅ **CORRECT** - Repository is dumb persistence layer

**Rationale**:
- Repositories should NOT enforce business rules
- Repositories trust that domain objects passed to them are valid
- Validation happens at application layer (commands)
- This follows Clean Architecture dependency rule

---

### 2.4 Project Domain Entity ✅

**File**: `src/doc_helper/domain/project/project.py`
**Lines**: 77-80

**Validation**:
```python
if not isinstance(self.app_type_id, str):
    raise TypeError("app_type_id must be a string")
if not self.app_type_id.strip():
    raise ValueError("app_type_id cannot be empty")
```

**Status**: ✅ **CORRECT** - Domain validates type and non-empty, NOT registry existence

**Rationale**:
- Domain layer should NOT know about AppTypeRegistry (platform infrastructure)
- Domain validates basic constraints (type, non-empty)
- Application layer validates external dependencies (registry lookup)
- This maintains domain purity (ADR-003)

---

## 3. Additional Observations

### 3.1 JsonProjectImporter Design

**File**: `src/doc_helper/infrastructure/interchange/json_project_importer.py`

**Current Design**:
- Infrastructure layer concern (JSON deserialization)
- Creates Project objects directly from JSON
- Does NOT validate app_type_id against registry
- Has default app_type_id for backward compatibility (line 193)

**Status**: ✅ **ACCEPTABLE** - Infrastructure should be dumb

**Rationale**:
- Importer's job is deserialization, not validation
- Validation should happen at command layer
- Keeps infrastructure decoupled from platform concerns

**Recommendation**: No changes needed to JsonProjectImporter. Fix ImportProjectCommand instead.

---

### 3.2 Negative Test Coverage

**File**: `tests/unit/platform/test_platform_stability.py`

**Coverage**: 55 tests covering:
- ✅ Missing AppType at project open
- ✅ Corrupt app_type_id values (SQL injection, path traversal)
- ✅ Project creation with invalid app_type_id
- ✅ Platform with no AppTypes
- ✅ AppType unregistration while in use
- ✅ app_type_id format constraints
- ✅ Semantic version constraints

**Gap**: No test for import with invalid app_type_id

**Recommendation**: Add test after fixing ImportProjectCommand:

```python
def test_import_project_with_invalid_apptype_fails():
    """Test: Importing project with non-existent app_type_id fails gracefully."""
    # Create JSON file with app_type_id="nonexistent_app"
    # Execute ImportProjectCommand
    # Assert: success=False, clear error message
    # Assert: Project NOT saved to repository
```

---

## 4. Enforcement Recommendations

### Priority 1: Fix ImportProjectCommand (CRITICAL)

**Action**: Add IAppTypeRegistry dependency to ImportProjectCommand
**Validation Point**: After JsonProjectImporter returns project, before ValidationService
**Error Handling**: Return ImportResultDTO with success=False and clear error message
**Testing**: Add negative test for import with invalid app_type_id

**Estimated Effort**: 1-2 hours (implementation + test + full suite validation)

---

### Priority 2: Document AppType Validation Contract (HIGH)

**Action**: Add architectural rule to AGENT_RULES.md or ADR
**Content**:
```markdown
## AppType Validation Contract

**Invariant**: All Project objects must have valid app_type_id that exists in AppTypeRegistry.

**Enforcement Points** (application layer only):
1. CreateProjectCommand: Validates before creating Project
2. OpenProjectCommand: Validates after loading Project from repository
3. ImportProjectCommand: Validates after importing Project from JSON
4. Any future commands that create/load projects

**Non-Enforcement Points** (correct behavior):
- Domain entities (Project): Only validate type and non-empty
- Repositories: Trust domain objects, no validation
- Infrastructure (JsonProjectImporter): Deserialization only, no validation

**Rationale**:
- Domain layer must remain pure (no platform dependencies)
- Application layer orchestrates and enforces invariants
- Infrastructure layer is dumb (no business rules)
```

---

### Priority 3: Add Integration Test (MEDIUM)

**Action**: Create integration test for full import workflow
**Coverage**:
- Import JSON with valid app_type_id → Success
- Import JSON with invalid app_type_id → Failure with clear message
- Import JSON with missing app_type_id (defaults to "soil_investigation") → Success if registered

**Location**: `tests/integration/workflows/test_import_with_invalid_apptype.py`

---

## 5. Summary

**Total Gaps Found**: 1 CRITICAL

**Overall Assessment**: Platform enforcement is **MOSTLY SOLID** with one critical gap in import workflow.

**Next Steps**:
1. ✅ Document findings (this document)
2. ⏳ Fix ImportProjectCommand (add app_type_id validation)
3. ⏳ Add negative test for import with invalid app_type_id
4. ⏳ Update AGENT_RULES.md with AppType validation contract
5. ⏳ Run full test suite (1432+ tests) to ensure no regressions

**Platform Readiness for AppType #3**: **BLOCKED until ImportProjectCommand gap is fixed**

---

## Appendix: Full Validation Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PROJECT CREATION FLOWS                         │
└─────────────────────────────────────────────────────────────────────┘

1. NEW PROJECT FLOW (via UI)
   User → NewProjectDialog
       → MainWindowViewModel.create_project()
       → CreateProjectCommand.execute()
           → ✅ VALIDATES app_type_id against registry
           → Creates Project domain object
           → SqliteProjectRepository.save()
       → Success

2. OPEN PROJECT FLOW (via UI)
   User → Open dialog
       → MainWindowViewModel.open_project()
       → OpenProjectCommand.execute()
           → SqliteProjectRepository.get_by_id()
           → ✅ VALIDATES app_type_id against registry
       → Success or Failure

3. IMPORT PROJECT FLOW (via UI) ⚠️ GAP DETECTED
   User → Import dialog
       → ProjectViewModel.import_project()
       → ImportProjectCommand.execute()
           → JsonProjectImporter.import_from_file()
               → Creates Project from JSON (app_type_id from file)
           → ❌ NO VALIDATION of app_type_id against registry
           → ValidationService.validate_project() (fields only)
           → SqliteProjectRepository.save()
       → Success (even with invalid app_type_id!)

4. RECOMMENDED FIX: Add validation step
   ImportProjectCommand.execute()
       → JsonProjectImporter.import_from_file()
       → ✅ VALIDATE app_type_id against registry  ← ADD THIS
       → ValidationService.validate_project()
       → SqliteProjectRepository.save()
```

---

**End of Analysis**

# TEST COVERAGE AUDIT REPORT

**Date**: 2026-01-23
**Trigger**: Runtime TypeError revealed missing abstract method implementations in `SqliteSchemaRepository`

---

## 1. AppTypes vs Test Coverage

| AppType | Unit Tests | Integration Tests | Instantiated in Tests | Repository Constructed | Interface Compliance |
|---------|-----------|-------------------|----------------------|----------------------|---------------------|
| **SoilInvestigationAppType** | ❌ None | ✅ 1 (multi-apptype) | ✅ Yes (line 114) | ✅ Yes (line 94) | ✅ Implements IAppType |
| **TestReportAppType** | ❌ None | ✅ 1 (multi-apptype) | ✅ Yes (line 115) | ✅ Yes | ✅ Implements IAppType |

### Repository Implementation Coverage

| Repository | Interface | Unit Tests | Integration Tests | Contract Verified |
|------------|-----------|-----------|-------------------|-------------------|
| `SqliteSchemaRepository` (main) | `ISchemaRepository` | ❌ | ✅ 2 files | ⚠️ **PARTIAL** - missing 5 abstract methods until fix |
| `SqliteSchemaRepository` (sqlite/repositories/) | `ISchemaRepository` | ❌ | ✅ 1 file | ✅ Full |
| `SqliteProjectRepository` | `IProjectRepository` | ❌ | ✅ 1 file | ✅ Full |
| `SqliteOverrideRepository` | `IOverrideRepository` | ✅ 1 file | ❌ | ✅ Full |
| `SqliteFieldHistoryRepository` | `IFieldHistoryRepository` | ❌ | ✅ 1 file | ✅ Full |

### Platform Bootstrapping Coverage

| Component | Unit Tests | Integration Tests | Coverage |
|-----------|-----------|-------------------|----------|
| `configure_container()` | ❌ | ✅ 1 file | ⚠️ Indirect only |
| `AppTypeRegistry` | ✅ 1 file | ✅ 1 file | ✅ Good |
| `AppTypeRouter` | ✅ 1 file | ❌ | ✅ Good |
| `AppTypeDiscoveryService` | ✅ 1 file | ✅ 1 file | ✅ Good |

---

## 2. Confirmed Blind Spots

### Critical (caused runtime failure)

| # | Blind Spot | Impact | Root Cause |
|---|------------|--------|------------|
| **B1** | `SqliteSchemaRepository` (main) never instantiated in tests | Runtime TypeError on app startup | Two implementations exist; tests covered wrong one |
| **B2** | No test validates `ISchemaRepository` abstract method compliance | Missing methods went undetected | Interface contract not enforced at test time |

### High Priority

| # | Blind Spot | Impact |
|---|------------|--------|
| **B3** | No unit tests for `SoilInvestigationAppType` directly | Cannot catch AppType-specific bugs in isolation |
| **B4** | No unit tests for `TestReportAppType` directly | Same as above |
| **B5** | `configure_container()` not unit tested | Bootstrap failures only caught at runtime |

### Medium Priority

| # | Blind Spot | Impact |
|---|------------|--------|
| **B6** | AppType `get_schema_repository()` return value not validated against interface | Can return non-compliant repository |
| **B7** | No test for AppType initialization with missing `config.db` | Graceful degradation untested |
| **B8** | Duplicate `SqliteSchemaRepository` implementations not detected | Maintenance confusion, inconsistent behavior |

---

## 3. Recommended Missing Tests

### Minimal Set to Close Critical Gaps

| # | Test Purpose | Type | Closes Blind Spot |
|---|--------------|------|-------------------|
| **T1** | **AppType Repository Contract Smoke Test** - Instantiate each AppType, call `get_schema_repository()`, verify returned object implements all `ISchemaRepository` abstract methods | Integration | B1, B2, B6 |
| **T2** | **SoilInvestigationAppType Unit Test** - Direct instantiation, verify `app_type_id`, `metadata`, all interface methods callable | Unit | B3 |
| **T3** | **TestReportAppType Unit Test** - Same as T2 | Unit | B4 |
| **T4** | **configure_container() Smoke Test** - Call function, verify it returns a Container with all required services registered, no exceptions | Unit | B5 |
| **T5** | **AppType Missing Config Graceful Handling** - Instantiate AppType with non-existent `config.db` path, verify appropriate error or fallback | Integration | B7 |

### Test Specifications

**T1: AppType Repository Contract Smoke Test**
- Location: `tests/integration/platform/test_apptype_repository_contracts.py`
- For each registered AppType:
  1. Create instance
  2. Call `get_schema_repository()`
  3. Assert returned object is instance of `ISchemaRepository`
  4. Assert all abstract methods exist and are callable (not abstract)
  5. Optionally call `get_all()` to verify basic operation

**T2/T3: AppType Unit Tests**
- Location: `tests/unit/platform/test_soil_investigation_apptype.py`
- Tests:
  - `test_instantiation_succeeds()`
  - `test_app_type_id_returns_expected_value()`
  - `test_metadata_returns_valid_object()`
  - `test_implements_iapptype_interface()`

**T4: configure_container() Smoke Test**
- Location: `tests/unit/infrastructure/test_configure_container_smoke.py`
- Tests:
  - `test_returns_container_instance()`
  - `test_registers_apptype_registry()`
  - `test_registers_apptype_router()`
  - `test_handles_missing_config_db_gracefully()`

**T5: Graceful Degradation Test**
- Location: `tests/integration/platform/test_apptype_missing_resources.py`
- Tests:
  - `test_apptype_with_missing_config_db_raises_clear_error()`
  - `test_apptype_with_missing_templates_dir_handled()`

---

## 4. Summary

| Metric | Value |
|--------|-------|
| Total AppTypes | 2 |
| AppTypes with direct unit tests | 0 |
| AppTypes instantiated in integration tests | 2 |
| Repository interfaces | 5 |
| Repository implementations tested | 4 of 5 (main SqliteSchemaRepository had gap) |
| Critical blind spots | 2 |
| Recommended new tests | 5 |

### Key Finding

The runtime failure occurred because:
1. **Two `SqliteSchemaRepository` implementations exist** in different locations
2. Tests covered `sqlite/repositories/schema_repository.py` (complete)
3. Production code imported `sqlite_schema_repository.py` (incomplete)
4. No test ever instantiated the actual AppType → repository path used at runtime

### Remediation Priority

1. **Immediate**: Add T1 (Repository Contract Smoke Test) - prevents this class of bug
2. **Short-term**: Add T2, T3, T4 (AppType and bootstrap unit tests)
3. **Medium-term**: Add T5 and consolidate duplicate repository implementations

---

## 5. File References

### AppType Implementations
- `src/doc_helper/app_types/soil_investigation/__init__.py`
- `src/doc_helper/app_types/test_report/__init__.py`

### Duplicate Repository Files (Technical Debt)
- `src/doc_helper/infrastructure/persistence/sqlite_schema_repository.py` ← **Production import**
- `src/doc_helper/infrastructure/persistence/sqlite/repositories/schema_repository.py` ← **Tested file**

### Key Test Files
- `tests/integration/platform/test_multi_apptype_discovery.py` (AppType instantiation)
- `tests/integration/test_composition_root.py` (DI container tests)

---

**Audit Complete.** Awaiting approval before implementing recommended tests.

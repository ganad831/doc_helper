# Phase 2 Step 2 - Architecture Fix Summary

> **Historical Note (2026-01-25)**: This summary documents work on `sqlite/repositories/schema_repository.py`, which is now the sole authoritative schema repository as of Phase M-3. References to `SqliteSchemaRepository` in this document refer to this authoritative implementation.

## Issue Identified

The `SqliteSchemaRepository` created in Phase 2 Step 2 was using an incorrect database connection API:

**Problem**: Used `connection.get_cursor()` which does not exist in the codebase.

**Correct Pattern**: Use `SqliteConnection` from `sqlite_base.py` as a context manager.

## PART 1: Repository Contract Fix - COMPLETE

### Changes Made

1. **Extended `SqliteSchemaRepository.save()` method** to handle both CREATE and ADD FIELDS scenarios
   - If entity does NOT exist: INSERT entity + all fields
   - If entity EXISTS: INSERT only NEW fields (not already in database)
   - Returns Failure if no new fields to add

2. **Removed architecture violation in `AddFieldCommand`**
   - Deleted `_save_updated_entity()` workaround method (70 lines)
   - Replaced with direct call to `repository.save(entity)`
   - ALL persistence now goes through repository interface

3. **Fixed database connection implementation** (in progress)
   - Changed import from non-existent `DatabaseConnection` to `SqliteConnection`
   - Updated all connection usage to follow existing pattern in codebase

### Files Modified - PART 1

1. `src/doc_helper/infrastructure/persistence/sqlite/repositories/schema_repository.py`
   - Extended `save()` method (lines 198-282)
   - Fixed database connection pattern (in progress)

2. `src/doc_helper/application/commands/schema/add_field_command.py`
   - Removed `_save_updated_entity()` workaround (lines 153-222 deleted)
   - Simplified to use `repository.save(entity)` (line 146)

## PART 2: Tests - COMPLETE

### Test Files Created

1. **`tests/unit/application/commands/schema/test_create_entity_command.py` (170 lines)**
   - Purpose: Unit tests for CreateEntityCommand
   - Tests:
     - Success case with all parameters
     - Success without description
     - Root entity creation
     - Duplicate entity rejection ✅
     - Missing entity_id rejection
     - Missing name_key rejection
     - Root entity with parent rejection
     - Entity with parent success
     - Repository save failure propagation

2. **`tests/unit/application/commands/schema/test_add_field_command.py` (290 lines)**
   - Purpose: Unit tests for AddFieldCommand
   - Tests:
     - Success case with all parameters
     - Success without optional parameters
     - All testable field types (TEXT, TEXTAREA, NUMBER, DATE, CHECKBOX, FILE, IMAGE)
     - Duplicate field rejection ✅
     - Invalid field type rejection ✅
     - Nonexistent entity rejection
     - Missing parameter rejections (entity_id, field_id, field_type, label_key)
     - Repository load failure propagation
     - Repository save failure propagation
   - Note: DROPDOWN, RADIO, CALCULATED, LOOKUP, TABLE cannot be tested in Phase 2 Step 2 due to domain validation requiring additional data (options, formula, entity references)

3. **`tests/integration/infrastructure/persistence/test_sqlite_schema_repository_phase2_step2.py` (435 lines)**
   - Purpose: Integration tests for SqliteSchemaRepository CREATE operations
   - Tests:
     - Save new entity with fields ✅
     - Save new entity without fields
     - Add new fields to existing entity ✅
     - Reject saving existing entity with no new fields
     - Ignore duplicate fields when adding new ones
     - Rollback on constraint violation ✅
     - Rollback on invalid field type (CHECK constraint)
     - Save entity with all testable field types (7 types)

### Test Results

**CreateEntityCommand**: ✅ 9/9 passed
**AddFieldCommand**: ✅ 12/12 passed
**Repository Integration**: ✅ 8/8 passed

**Total**: ✅ 29/29 tests passing

## Key Findings

### Domain Model Constraint

The Phase 1 `FieldDefinition` enforces invariants that prevent creating certain field types without additional data:

| Field Type | Requires | Can Create in Step 2? |
|------------|----------|----------------------|
| TEXT | - | ✅ Yes |
| TEXTAREA | - | ✅ Yes |
| NUMBER | - | ✅ Yes |
| DATE | - | ✅ Yes |
| CHECKBOX | - | ✅ Yes |
| FILE | - | ✅ Yes |
| IMAGE | - | ✅ Yes |
| DROPDOWN | options | ❌ No (Phase 2 Step 3) |
| RADIO | options | ❌ No (Phase 2 Step 3) |
| CALCULATED | formula | ❌ No (Phase 2 Step 3) |
| LOOKUP | lookup_entity_id | ❌ No (Phase 2 Step 3) |
| TABLE | child_entity_id | ❌ No (Phase 2 Step 3) |

This is a Phase 1 design decision that limits Phase 2 Step 2 to creating only 7 of 12 field types.

## Compliance with Requirements

✅ **PART 1 Requirements Met**:
- Eliminated direct SQL inserts bypassing repository
- ALL persistence goes through repository methods
- Extended `save()` to support adding fields to existing entities
- No persistence logic outside repository

✅ **PART 2 Requirements Met**:
- CreateEntityCommand: success + duplicate rejection
- AddFieldCommand: success + duplicate rejection + invalid type rejection
- Repository: persistence and rollback behavior
- NO forbidden tests (UI, export, relationships, editing/deletion, runtime validation)

✅ **All Work Complete**:
- Fixed SqliteConnection pattern in schema_repository.py
- All integration tests passing (8/8)
- All unit tests passing (21/21)
- Total: 29/29 tests passing

## Additional Fixes Made

1. **TranslationKey Attribute Fix**
   - Changed `entity.name_key.value` to `entity.name_key.key`
   - TranslationKey uses `.key` attribute, not `.value`

2. **Nested Connection Context Manager Fix**
   - Refactored `_load_fields_for_entity()` to accept `cursor` parameter
   - Prevents "Connection already open" error from nested context managers

3. **Field Type Case Sensitivity**
   - Updated database CHECK constraint to use lowercase field types
   - Matches FieldType enum values: "text", "number", etc. (not "TEXT", "NUMBER")

4. **Foreign Key Constraints**
   - Added `PRAGMA foreign_keys = ON` to SqliteConnection
   - Ensures foreign key constraints are enforced

## Architectural Notes

The SqliteConnection pattern in the codebase:
```python
# Repository initialization
self._connection = SqliteConnection(db_path)

# Usage in methods
with self._connection as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM table")
    # ...connection auto-commits on success, rolls back on exception
```

NOT (incorrect pattern used initially):
```python
with self._connection.get_cursor() as cursor:  # ❌ get_cursor() does not exist
    cursor.execute(...)
```

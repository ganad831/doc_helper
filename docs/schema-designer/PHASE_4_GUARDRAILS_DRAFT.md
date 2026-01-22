# Phase 4: Schema Import and Compatibility Enforcement

## Status: DRAFT - AWAITING APPROVAL

**Prerequisites**: Phases 1-3 COMPLETE and STABLE
- Phase 1: Schema Designer Domain (entity/field definitions)
- Phase 2: Schema Export (JSON serialization)
- Phase 3: Schema Versioning and Compatibility (analysis)

---

## 1. PHASE 4 SCOPE

### 1.1 What Phase 4 WILL Include

1. **Import Command**: Read exported JSON file and populate schema repository
2. **Pre-Import Validation**: Validate JSON structure and content before import
3. **Compatibility Check**: Use Phase 3 comparison service before import
4. **Import Result**: Success/failure with detailed diagnostics
5. **Compatibility Enforcement Policy**: Configurable strictness level

### 1.2 What Phase 4 will NOT Include

1. **NO Automatic Migration**: Import does not transform data
2. **NO Data Migration**: Only schema structure, not project data
3. **NO Merge Logic**: Import is all-or-nothing (no partial merge)
4. **NO UI Components**: Command/service layer only
5. **NO Rollback Mechanism**: User must re-import previous version manually
6. **NO Schema Mutation Beyond Import**: Import replaces, does not transform
7. **NO Circular Import/Export**: No re-export of imported schema in same operation

---

## 2. INVARIANTS (NON-NEGOTIABLE)

### 2.1 Inherited from Phase 1

- Entity IDs must be unique within schema
- Field IDs must be unique within entity
- Field types must be valid FieldType enum values
- Translation keys must be non-empty strings

### 2.2 Inherited from Phase 2

- Exported JSON format is the canonical import format
- Schema identifier required in import file
- All structural data must be present (no partial schemas)

### 2.3 Inherited from Phase 3

- Phase 3 `SchemaComparisonService` is the SINGLE source of truth for compatibility
- Compatibility levels: IDENTICAL / COMPATIBLE / INCOMPATIBLE
- Breaking change classification follows Phase 3 Decision 3 (Moderate policy)

### 2.4 New Phase 4 Invariants

- **I4.1**: Import MUST validate JSON structure before any repository writes
- **I4.2**: Import MUST check compatibility with existing schema (if any)
- **I4.3**: Import MUST be atomic (all-or-nothing, no partial import)
- **I4.4**: Import MUST NOT modify the source JSON file
- **I4.5**: Import result MUST include all compatibility warnings regardless of outcome
- **I4.6**: Import MUST preserve all structural data from source file
- **I4.7**: Import of incompatible schema requires explicit user confirmation (enforcement policy)

---

## 3. IMPORT SCENARIOS

### 3.1 Scenario A: Import to Empty Schema

**Condition**: Target repository has no entities
**Behavior**: Import all entities and fields from file
**Compatibility**: N/A (no existing schema to compare)
**Expected Outcome**: Success

### 3.2 Scenario B: Import Identical Schema

**Condition**: Target schema exists and is IDENTICAL to import file
**Behavior**: No-op or replace (Decision Point 1)
**Compatibility**: IDENTICAL
**Expected Outcome**: Success (with optional warning)

### 3.3 Scenario C: Import Compatible Schema

**Condition**: Target schema exists with COMPATIBLE changes (non-breaking)
**Behavior**: Replace existing schema (Decision Point 2)
**Compatibility**: COMPATIBLE
**Expected Outcome**: Success (with warnings listing changes)

### 3.4 Scenario D: Import Incompatible Schema

**Condition**: Target schema exists with INCOMPATIBLE changes (breaking)
**Behavior**: Depends on enforcement policy (Decision Point 3)
**Compatibility**: INCOMPATIBLE
**Expected Outcome**: Fail by default, or success with force flag

### 3.5 Scenario E: Invalid Import File

**Condition**: JSON is malformed, missing required fields, or invalid values
**Behavior**: Fail immediately with validation errors
**Compatibility**: N/A (never reaches comparison)
**Expected Outcome**: Failure with detailed error messages

---

## 4. COMPATIBILITY ENFORCEMENT POLICIES

Phase 3 established compatibility as "informational only". Phase 4 introduces **optional enforcement** for import operations.

### 4.1 Policy Options

| Policy | IDENTICAL | COMPATIBLE | INCOMPATIBLE |
|--------|-----------|------------|--------------|
| **STRICT** | Allow | Allow | **Block** |
| **WARN** | Allow | Allow | Allow + Warning |
| **NONE** | Allow | Allow | Allow |

### 4.2 Default Policy

**Decision Point 4**: What should be the default enforcement policy?

### 4.3 Force Override

Regardless of policy, a `force` flag should allow import of incompatible schemas when the user explicitly requests it.

---

## 5. VALIDATION LAYERS

### 5.1 Layer 1: JSON Structure Validation

- Valid JSON syntax
- Required top-level keys present (`schema_id`, `entities`)
- Array/object types correct

### 5.2 Layer 2: Schema Content Validation

- All entity IDs are non-empty strings
- All field IDs are non-empty strings within each entity
- All field types are valid FieldType values
- All translation keys are non-empty strings
- Constraint types are recognized
- Option values are valid for choice fields

### 5.3 Layer 3: Compatibility Validation

- Compare import schema against existing schema (if any)
- Use Phase 3 `SchemaComparisonService.compare()`
- Generate `CompatibilityResult` with all changes
- Apply enforcement policy

### 5.4 Layer 4: Repository Constraints

- Entity IDs unique (may conflict with existing non-imported entities)
- Field IDs unique within entity
- Referential integrity (if any cross-references exist)

---

## 6. IMPORT RESULT STRUCTURE

The import result MUST include:

1. **Success/Failure Status**: Boolean
2. **Imported Schema ID**: From source file
3. **Imported Version**: If present in source file
4. **Compatibility Result**: Full Phase 3 comparison result (if existing schema)
5. **Validation Errors**: List of all validation failures
6. **Warnings**: List of non-blocking issues
7. **Entity Count**: Number of entities imported
8. **Field Count**: Total fields imported

---

## 7. FORBIDDEN BEHAVIORS

### 7.1 Absolutely Forbidden

- **F4.1**: NO automatic data migration (field values, project data)
- **F4.2**: NO schema transformation during import (normalize, dedupe, etc.)
- **F4.3**: NO partial import (some entities succeed, others fail)
- **F4.4**: NO silent overwrite without compatibility check
- **F4.5**: NO modification of source file
- **F4.6**: NO import of non-JSON formats
- **F4.7**: NO bypassing Phase 3 compatibility analysis

### 7.2 Out of Scope

- UI dialogs for import
- Drag-and-drop import
- Import from URL
- Import from database directly
- Multi-file import
- Import with transformation rules

---

## 8. DECISION POINTS REQUIRING APPROVAL

### Decision 1: Identical Schema Behavior

When importing a schema that is IDENTICAL to existing:

**Option A**: No-op (skip import, return success)
- Pro: Faster, no unnecessary writes
- Con: User may expect "refresh" behavior

**Option B**: Replace anyway (overwrite with identical data)
- Pro: Consistent behavior, timestamps updated
- Con: Unnecessary I/O

**Option C**: User choice via parameter
- Pro: Flexible
- Con: More complex API

---

### Decision 2: Compatible Schema Behavior

When importing a schema with COMPATIBLE (non-breaking) changes:

**Option A**: Auto-replace without confirmation
- Pro: Non-breaking means safe
- Con: User may not realize changes occurred

**Option B**: Require explicit flag for any changes
- Pro: User always in control
- Con: Friction for safe operations

**Option C**: Replace but return detailed change list
- Pro: Balance of convenience and transparency
- Con: User must check result

---

### Decision 3: Incompatible Schema Default Behavior

When importing a schema with INCOMPATIBLE (breaking) changes and no force flag:

**Option A**: Fail immediately (STRICT default)
- Pro: Safest, prevents accidental data loss
- Con: May frustrate users who know what they're doing

**Option B**: Warn but allow (WARN default)
- Pro: Flexible, user-friendly
- Con: May cause accidental breaking changes

**Option C**: Configurable default via settings
- Pro: Adapts to user preference
- Con: Inconsistent behavior across environments

---

### Decision 4: Default Enforcement Policy

What should be the default enforcement policy for import?

**Option A**: STRICT (block incompatible by default)
- Pro: Safest default, prevents accidents
- Con: Requires force flag for intentional breaking changes

**Option B**: WARN (allow with warnings by default)
- Pro: More permissive, less friction
- Con: Breaking changes may go unnoticed

**Option C**: NONE (no enforcement by default)
- Pro: Maximum flexibility
- Con: Compatibility analysis becomes meaningless

---

### Decision 5: Version Field Handling

How to handle the optional `version` field during import:

**Option A**: Ignore version field entirely
- Pro: Simple, version is metadata only
- Con: Loses version tracking benefit

**Option B**: Store version but don't enforce
- Pro: Preserves metadata for display/logging
- Con: No version-based validation

**Option C**: Validate version progression
- Pro: Ensures version discipline
- Con: Complex, may reject valid imports

**Option D**: Warn if version goes backward
- Pro: Catches likely mistakes
- Con: May have legitimate use cases for downgrade

---

### Decision 6: Empty Entity Handling

Should import allow entities with zero fields?

**Option A**: Allow (matches Phase 2 export behavior)
- Pro: Consistent with export
- Con: May import incomplete schemas

**Option B**: Warn but allow
- Pro: User informed of potential issue
- Con: Warning fatigue

**Option C**: Reject entities with no fields
- Pro: Ensures meaningful schemas
- Con: May block valid intermediate states

---

### Decision 7: Unknown Constraint Type Handling

If import file contains an unrecognized constraint type:

**Option A**: Fail import (strict validation)
- Pro: Catches version mismatches, prevents data loss
- Con: Forward compatibility broken

**Option B**: Skip unknown constraint with warning
- Pro: Forward compatible
- Con: Silent data loss

**Option C**: Preserve as generic/raw constraint
- Pro: No data loss
- Con: Complex implementation, may cause issues later

---

## 9. TESTING REQUIREMENTS

### 9.1 Unit Tests Required

- JSON parsing and validation
- All validation layer error cases
- Compatibility enforcement policy application
- Import result structure completeness

### 9.2 Integration Tests Required

- Import to empty repository
- Import identical schema
- Import compatible schema
- Import incompatible schema (with and without force)
- Import with validation errors
- Import with unknown fields (forward compatibility)
- Round-trip: Export → Import → Export produces identical output

### 9.3 Edge Cases to Test

- Empty entities array
- Entity with no fields
- Field with no constraints
- Choice field with no options
- Very large schema (performance)
- Unicode in all text fields
- Maximum nesting depth

---

## 10. SUCCESS CRITERIA

Phase 4 is complete when:

1. Import command accepts exported JSON and populates repository
2. All validation layers catch appropriate errors
3. Compatibility enforcement works per approved policy
4. All 7 decision points have approved answers
5. Unit tests cover all validation scenarios
6. Integration tests cover all import scenarios
7. Round-trip (export → import → export) produces identical output
8. Documentation updated with import usage

---

## 11. APPROVAL REQUIRED

Before implementation begins, the following decisions must be approved:

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | Identical Schema Behavior | A/B/C | **C** (User choice) |
| 2 | Compatible Schema Behavior | A/B/C | **C** (Replace with change list) |
| 3 | Incompatible Schema Default | A/B/C | **A** (Fail by default) |
| 4 | Default Enforcement Policy | A/B/C | **A** (STRICT) |
| 5 | Version Field Handling | A/B/C/D | **D** (Warn on backward) |
| 6 | Empty Entity Handling | A/B/C | **B** (Warn but allow) |
| 7 | Unknown Constraint Type | A/B/C | **A** (Fail import) |

**Please approve or modify each decision before implementation proceeds.**

---

## CHANGELOG

| Date | Change |
|------|--------|
| 2026-01-23 | Initial draft created |

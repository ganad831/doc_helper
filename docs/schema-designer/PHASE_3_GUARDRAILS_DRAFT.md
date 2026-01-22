# Phase 3: Schema Versioning and Compatibility
## Guardrails & Plan Document (APPROVED)

**Status**: APPROVED - Implementation in Progress
**Date**: 2026-01-23
**Prerequisite**: Phase 2 COMPLETE and CLOSED

**CLARIFICATION**: Phase 3 is analysis-only. Compatibility classification is informational and MUST NOT block export or schema changes.

---

## 1. What Phase 3 IS Allowed to Include

### 1.1 Version Identification
- Schema version identifier (format TBD - see Decision 1)
- Version assignment to schema snapshots
- Version inclusion in export files
- Version metadata storage

### 1.2 Change Detection
- Detect additions (new entities, new fields)
- Detect removals (deleted entities, deleted fields)
- Detect modifications (changed field type, changed constraints)
- Detect renames (if identifiable - see Decision 2)

### 1.3 Compatibility Classification
- Classify changes as breaking or non-breaking
- Define what constitutes a breaking change (see Decision 3)
- Compatibility level determination between two versions
- Compatibility report generation

### 1.4 Version Comparison
- Compare two schema versions
- Generate diff summary
- Identify specific changes between versions

### 1.5 Export Enhancement
- Include version identifier in export (per Phase 2 Step 4 Decision 7)
- Include compatibility metadata in export (optional - see Decision 4)

---

## 2. What Phase 3 is Explicitly FORBIDDEN

### 2.1 Migration Execution
- **NO** automatic data migration
- **NO** migration script generation
- **NO** migration script execution
- **NO** data transformation between versions

### 2.2 Import Functionality
- **NO** import from export files
- **NO** schema loading from external sources
- **NO** version upgrade/downgrade execution

### 2.3 Version Control Features
- **NO** git-like branching
- **NO** merge conflict resolution
- **NO** version rollback execution
- **NO** version history persistence beyond current session

### 2.4 UI Components
- **NO** version management dialogs
- **NO** diff visualization
- **NO** compatibility warning dialogs
- **NO** version selection UI

### 2.5 Runtime Behavior Changes
- **NO** changes to validation execution
- **NO** changes to formula evaluation
- **NO** changes to control evaluation
- **NO** changes to export file format structure (only add version field)

---

## 3. Breaking vs Non-Breaking Change Definitions

### 3.1 Candidate Breaking Changes
The following changes MAY be classified as breaking (final classification per Decision 3):

| Change Type | Category | Rationale |
|-------------|----------|-----------|
| Entity deleted | Structural | Existing data references lost |
| Field deleted | Structural | Existing data values lost |
| Field type changed | Structural | Existing values may be invalid |
| Field made required (was optional) | Constraint | Existing records may fail validation |
| Constraint made stricter | Constraint | Existing values may fail validation |
| Option removed from choice field | Constraint | Existing selections may be invalid |

### 3.2 Candidate Non-Breaking Changes
The following changes MAY be classified as non-breaking:

| Change Type | Category | Rationale |
|-------------|----------|-----------|
| Entity added | Additive | No impact on existing data |
| Field added (optional) | Additive | No impact on existing data |
| Field made optional (was required) | Relaxing | Existing data still valid |
| Constraint relaxed | Relaxing | Existing values still valid |
| Option added to choice field | Additive | Existing selections still valid |
| Translation key changed | Metadata | No data impact |
| Help text key changed | Metadata | No data impact |
| Description key changed | Metadata | No data impact |
| Default value changed | Metadata | Only affects new records |

### 3.3 Ambiguous Changes
The following changes require policy decision (see Decision 3):

| Change Type | Consideration |
|-------------|---------------|
| Field added (required) | Breaking if existing records exist, non-breaking if schema-only |
| Entity renamed | Breaking or rename-tracking? |
| Field renamed | Breaking or rename-tracking? |
| Constraint parameters changed | Depends on direction (stricter vs looser) |

---

## 4. Version Identifier Options

### 4.1 Option A: Semantic Versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes
- MINOR: Non-breaking additions
- PATCH: Metadata-only changes
- Example: "2.1.0"

### 4.2 Option B: Sequential Integer
- Simple incrementing number
- No semantic meaning
- Example: "42"

### 4.3 Option C: Timestamp-Based
- ISO 8601 timestamp of schema state
- Example: "2026-01-23T14:30:00Z"

### 4.4 Option D: Content Hash
- Hash of schema content
- Automatically unique per state
- Example: "sha256:a1b2c3..."

---

## 5. Compatibility Levels

### 5.1 Proposed Compatibility Levels

| Level | Meaning |
|-------|---------|
| **IDENTICAL** | No changes detected |
| **COMPATIBLE** | Non-breaking changes only |
| **INCOMPATIBLE** | At least one breaking change |

### 5.2 Alternative: Granular Levels

| Level | Meaning |
|-------|---------|
| **IDENTICAL** | No changes detected |
| **METADATA_ONLY** | Only translation/description changes |
| **ADDITIVE** | Only additions, no modifications/deletions |
| **RELAXING** | Constraints relaxed, no deletions |
| **BREAKING** | Contains breaking changes |

---

## 6. Required Validations

### 6.1 Version Identifier Validation
- Version identifier must be non-empty
- Version identifier must match chosen format (per Decision 1)
- Version identifier must be unique within comparison context

### 6.2 Comparison Validation
- Both schemas must be valid (pass Phase 1/2 invariants)
- Comparison must be deterministic (same inputs = same output)

---

## 7. Failure vs Success Rules

### 7.1 Version Assignment MUST Fail When:
| Condition | Reason |
|-----------|--------|
| Schema fails Phase 1/2 invariants | Invalid schema cannot be versioned |
| Version identifier format invalid | Per chosen format rules |

### 7.2 Comparison MUST Fail When:
| Condition | Reason |
|-----------|--------|
| Either schema fails Phase 1/2 invariants | Cannot compare invalid schemas |
| Schemas are from incompatible contexts | Comparison not meaningful |

### 7.3 Operations MUST Succeed When:
| Condition | Result |
|-----------|--------|
| Valid schemas compared | Compatibility result returned |
| Version assigned to valid schema | Version identifier returned |

---

## 8. How Phase 1 and Phase 2 Invariants Are Preserved

### 8.1 Preservation Principle
Phase 3 is **read-only analysis**. No schema mutation occurs during versioning or comparison. All Phase 1 and Phase 2 invariants that were valid before versioning remain valid after.

### 8.2 No New Invariants
Phase 3 does not introduce new invariants that constrain schema design. Version compatibility is **informational only** - it does not block schema changes.

### 8.3 Export Compatibility
Phase 2 Step 4 export format is extended minimally:
- Add version identifier field (optional or required per Decision 5)
- No other structural changes to export format

---

## 9. Required Tests

### 9.1 Unit Tests (REQUIRED)
- **Version format validation**: Tests for each supported version format
- **Change detection**: Tests for each change type (add/remove/modify)
- **Breaking classification**: Tests for each breaking change type
- **Non-breaking classification**: Tests for each non-breaking change type
- **Compatibility level determination**: Tests for level assignment logic
- **Edge cases**: Empty schema comparison, identical schema comparison

### 9.2 Integration Tests (REQUIRED)
- **Export with version**: Verify version included in export
- **Round-trip version preservation**: Version survives export/parse cycle

### 9.3 Test Coverage Requirements
- All change types must have detection tests
- All breaking/non-breaking classifications must have tests
- All compatibility levels must have determination tests

---

## 10. Explicitly Forbidden Tests

### 10.1 Migration Tests (FORBIDDEN)
- No tests for data migration
- No tests for migration script generation
- No tests for upgrade/downgrade paths

### 10.2 Import Tests (FORBIDDEN)
- No tests for schema import
- No tests for version loading from files

### 10.3 UI Tests (FORBIDDEN)
- No tests for version UI components
- No tests for diff visualization
- No tests for compatibility dialogs

### 10.4 Persistence Tests (FORBIDDEN)
- No tests for version history storage
- No tests for version database operations

---

## 11. Risks Introduced by Versioning

### 11.1 Scope Creep Risks
| Risk | Mitigation |
|------|------------|
| Pressure to add migration | Strict forbidden list, defer to Phase 4 |
| Demand for import functionality | Defer to Phase 4, document boundary |
| Request for version UI | Defer to later phase, document boundary |

### 11.2 Complexity Risks
| Risk | Mitigation |
|------|------------|
| Over-complicated version format | Choose simplest format that meets needs |
| Ambiguous breaking change rules | Clear policy decisions documented |
| False compatibility signals | Conservative classification (when in doubt, mark breaking) |

### 11.3 User Expectation Risks
| Risk | Mitigation |
|------|------------|
| User expects automatic migration | Document that migration is Phase 4 |
| User expects version rollback | Document that versioning is informational |
| User expects version history | Document session-only scope |

---

## 12. Approved Decisions

**All decisions approved on 2026-01-23.**

---

**Decision 1: Version Identifier Format**

**APPROVED: A) Semantic versioning (MAJOR.MINOR.PATCH)**

---

**Decision 2: Rename Detection**

**APPROVED: A) No rename detection (rename = delete + add)**

---

**Decision 3: Breaking Change Policy**

**APPROVED: B) Moderate (only data-losing changes are breaking)**

Breaking changes:
- Entity deleted
- Field deleted
- Field type changed
- Option removed from choice field

Non-breaking changes:
- Entity added
- Field added (required or optional)
- Field made required/optional
- Constraint added/removed/changed
- Option added to choice field
- Metadata changes (translation keys, help text, descriptions)
- Default value changes

---

**Decision 4: Compatibility Metadata in Export**

**APPROVED: A) No compatibility metadata (version only)**

---

**Decision 5: Version Field in Export**

**APPROVED: B) Optional field (version included if assigned)**

---

**Decision 6: Compatibility Granularity**

**APPROVED: B) Three-level (IDENTICAL / COMPATIBLE / INCOMPATIBLE)**

---

**Decision 7: Comparison Scope**

**APPROVED: B) Structural comparison only (entities, fields, types, constraints)**

Excludes from comparison:
- Translation keys
- Help text keys
- Description keys
- Default values

---

## Document Status

- [x] Decision 1 approved
- [x] Decision 2 approved
- [x] Decision 3 approved
- [x] Decision 4 approved
- [x] Decision 5 approved
- [x] Decision 6 approved
- [x] Decision 7 approved
- [x] Guardrails reviewed and accepted
- [x] Test plan reviewed and accepted

**End of Phase 3 Guardrails Document**

# Phase 2 Step 4: Basic Schema Export
## Guardrails & Plan Document (REVISED)

**Status**: APPROVED - Implementation in Progress
**Date**: 2026-01-23
**Prerequisite**: Phase 2 Step 3 COMPLETE and CLOSED

---

## 1. What Export IS Allowed to Include

### 1.1 Entities (EntityDefinition)
- Entity identifier
- Entity name key (translation reference)
- Entity description key (translation reference)
- Entity type (SINGLETON/COLLECTION)
- Root entity flag
- Display order

### 1.2 Fields (FieldDefinition)
- Field identifier
- Field type (from platform-defined 12-type set)
- Label key (translation reference)
- Help text key (translation reference)
- Required flag
- Default value (raw value only)
- Display order
- Options for choice fields (DROPDOWN/RADIO):
  - Option value
  - Option label key

### 1.3 Validation Rules (Constraint Metadata Only)
- Constraint type (from platform-defined set)
- Constraint parameters (raw values only)
- Field association

### 1.4 Structural Metadata Only
- Entity-to-field containment (which fields belong to which entity)
- No behavioral metadata
- No runtime configuration

---

## 2. What Export is Explicitly FORBIDDEN

### 2.1 Excluded Entities
- **RelationshipDefinition** - Phase 2.1 scope
- **FormulaDefinition** - Phase 2.2 scope
- **ControlRule** - Phase 2.2 scope
- **OutputMapping** - Phase 2.3 scope

### 2.2 Excluded Field Properties
- Formula expressions
- Control rule associations
- Lookup entity references (behavioral)
- Child entity references (behavioral)
- Output mapping tags

### 2.3 Excluded Capabilities
- Import functionality (Phase 4)
- Schema semantic versioning (Phase 3)
- Export format versioning (Phase 3)
- Compatibility validation (Phase 3)
- Migration path generation
- Diff/merge capabilities
- Incremental export
- Selective entity export

### 2.4 Excluded Runtime Semantics
- Validation execution behavior
- Constraint interpretation
- Default value evaluation
- Translation resolution (keys only, not resolved values)
- Platform-specific rendering hints

### 2.5 Excluded Technical Features
- Compression
- Encryption
- Signing
- Checksums
- Multi-file export

---

## 3. Required Validations Before Export

### 3.1 Phase 1 Invariants (MUST Pass - Hard Failure)
All Phase 1 invariants as defined in Phase 1 documentation must pass before export proceeds. Export must not proceed if Phase 1 storage validation would reject the current schema state.

### 3.2 Phase 2 Invariants (MUST Pass - Hard Failure)
All Phase 2 invariants as defined in Phase 2 Step 1-3 documentation must pass before export proceeds. This includes field type immutability, constraint type validity, and option uniqueness rules.

### 3.3 Quality Checks (MAY Warn - Soft Warning)
- Entities with zero fields
- Fields with no description key
- Fields with no help text key
- Choice fields (DROPDOWN/RADIO) with zero options
- Excluded data exists in schema (relationships, formulas, etc.)

---

## 4. Failure vs Success Rules

### 4.1 Export MUST Fail When:
| Condition | Reason |
|-----------|--------|
| Any Phase 1 invariant violated | Data integrity compromised |
| Any Phase 2 invariant violated | Schema consistency broken |
| File system write fails | Export incomplete |

### 4.2 Export MUST Succeed (with Warnings) When:
| Condition | Warning Type |
|-----------|--------------|
| Quality checks fail | Informational warning |
| Missing optional metadata | Completeness warning |
| Excluded entities exist in schema | Scope warning |

### 4.3 Export Result Contract
- **Success**: File written, all invariants passed, zero or more warnings
- **Failure**: No file written, at least one invariant failed, error message returned
- **Partial export is FORBIDDEN**: Export completes fully or not at all

### 4.4 Warning Behavior
- Warnings are collected but do not prevent export completion
- All warnings are returned to caller alongside success status

---

## 5. Risks Introduced by Export

### 5.1 Data Integrity Risks
| Risk | Mitigation |
|------|------------|
| Export contains inconsistent data | All invariants validated before export |
| Export affected by concurrent changes | Export must operate on consistent state |
| Export partially written on failure | Export must complete fully or not at all |

### 5.2 Scope Creep Risks
| Risk | Mitigation |
|------|------------|
| Pressure to add excluded data | Strict forbidden list, code review |
| Demand for relationships export | Defer to Phase 2.1, document boundary |
| Request for format versioning | Defer to Phase 3, document boundary |

### 5.3 User Expectation Risks
| Risk | Mitigation |
|------|------------|
| User expects exported schema to work immediately | Document manual import responsibility |
| User expects all schema data exported | Clear indication of what's included/excluded |
| User expects round-trip capability | Document import is Phase 4 |

### 5.4 Platform Impact Risks
| Risk | Mitigation |
|------|------------|
| Malformed export used in target AppType | Target AppType's validation is enforcement point |
| Export format changes break manual imports | No format versioning = no compatibility promise |
| Users build tooling around export format | Document format is unstable until Phase 3 |

---

## 6. How Phase 1 and Phase 2 Invariants Are Preserved

### 6.1 Preservation Principle
Export is a **read-only** operation. No schema mutation occurs during export. All Phase 1 and Phase 2 invariants that were valid before export remain valid after export.

### 6.2 Validation Timing
All invariants are validated before export begins. If validation fails, export does not proceed.

### 6.3 Export Guarantees
- Export must not modify schema state
- Export must produce consistent output
- Same schema state must produce equivalent export

---

## 7. Required Tests

### 7.1 Unit Tests (REQUIRED)
- **Invariant validation coverage**: Tests must verify that Phase 1 and Phase 2 invariant violations are detected and cause export failure
- **Quality warning coverage**: Tests must verify that quality check failures produce warnings without blocking export
- **Export content coverage**: Tests must verify that all allowed fields are exported correctly
- **Exclusion coverage**: Tests must verify that forbidden data is not present in export
- **Failure behavior coverage**: Tests must verify that invariant failures result in no file written

### 7.2 Integration Tests (REQUIRED)
- **File system coverage**: Tests must verify export creates files and handles file system errors gracefully
- **Content validation coverage**: Tests must verify exported content can be parsed and matches source schema

### 7.3 Test Coverage Requirements
- All invariant checks must have test coverage
- All included fields must have export verification
- All excluded fields must have exclusion verification
- All failure conditions must have explicit tests

---

## 8. Explicitly Forbidden Tests

### 8.1 UI Tests (FORBIDDEN in Step 4)
- No tests for export button behavior
- No tests for export dialog rendering
- No tests for warning display UI
- No screenshot tests
- No visual regression tests

### 8.2 E2E Tests (FORBIDDEN in Step 4)
- No full workflow tests (create → export → import)
- No cross-AppType tests
- No platform integration tests
- No performance/load tests

### 8.3 Import Tests (FORBIDDEN - Phase 4)
- No tests verifying import of exported file
- No tests verifying target AppType loads export
- No round-trip behavioral tests

### 8.4 Format Tests (FORBIDDEN - Phase 3)
- No format version compatibility tests
- No schema migration tests
- No backward compatibility tests

---

## 9. Approved Decisions

**All decisions approved on 2026-01-23.**

---

**Decision 1: Export File Behavior on Existing File**

**APPROVED: B) Fail if file exists**

---

**Decision 2: Empty Schema Handling**

**APPROVED: A) Fail export with error**

---

**Decision 3: Translation Key Validation Strictness**

**APPROVED: A) Validate key format only (non-empty string)**

---

**Decision 4: Excluded Data Warning Granularity**

**APPROVED: B) Category warnings: "N relationships, M formulas not exported"**

---

**Decision 5: Export Location Restrictions**

**APPROVED: A) Any user-selected path**

---

**Decision 6: Timestamp Inclusion**

**APPROVED: B) No timestamp (content only)**

---

**Decision 7: Schema Identifier in Export**

**APPROVED: A) Include source schema/project identifier**

---

**Decision 8: Root Entity Requirement**

**APPROVED: B) Export allows zero root entities**
Export must not enforce or introduce root entity requirements. It reflects existing Phase 1/Phase 2 invariants only.

---

**Decision 9: Circular Reference Handling**

**APPROVED: C) Not checked (out of scope for Step 4)**
No failure and no warnings. Export must not introduce new semantic validation.

---

## Document Status

- [x] Decision 1 approved
- [x] Decision 2 approved
- [x] Decision 3 approved
- [x] Decision 4 approved
- [x] Decision 5 approved
- [x] Decision 6 approved
- [x] Decision 7 approved
- [x] Decision 8 approved
- [x] Decision 9 approved
- [x] Guardrails reviewed and accepted
- [x] Test plan reviewed and accepted

**End of Phase 2 Step 4 Guardrails Document**

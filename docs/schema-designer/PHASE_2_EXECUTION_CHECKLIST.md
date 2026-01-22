# Schema Designer Phase 2 Execution Checklist (DRAFT)

**Status**: DRAFT - Not yet approved for execution

**Date**: 2026-01-22

**Related Documents**:
- [Phase 1 Execution Checklist](PHASE_1_EXECUTION_CHECKLIST.md) (COMPLETE and CLOSED)
- [Schema Designer Implementation Plan](IMPLEMENTATION_PLAN.md)
- [ADR-V2-SCHEMA-DESIGNER](../../adrs/ADR-V2-SCHEMA-DESIGNER.md)

---

## Phase 2 Objectives

**Goal**: Build the simplest possible UI that allows AppType authors to create and edit schemas visually, then export them for use in target AppTypes.

**What Phase 2 Delivers**:
- User-facing schema editor UI for entities and fields
- Entity creation/editing interface (name, type, description)
- Field creation/editing interface (name, type, description, required flag, ordering)
- Basic validation rule creation via UI (constraint type, constraint parameters - metadata only)
- Manual schema export to JSON file
- Export quality checks (warnings for incomplete schema definitions)
- Schema preview mode (UI structure preview, not runtime data execution)

**Important Phase 2 Scope Boundaries**:
- **Export format**: JSON only (no SQLite export in Phase 2)
- **Export does NOT re-validate Phase 1 rules**: Export assumes storage validation passed; only warns about Phase 2 quality issues
- **Preview is UI structure only**: No runtime data entry, no runtime validation execution; preview verifies form rendering completeness
- **ValidationRule UI is metadata only**: Constraint type and parameters editing; no semantic interpretation, no runtime validation behavior
- **Manual import is out-of-band**: Schema Designer exports JSON; manual copying into target AppType's config.db is AppType author's responsibility
- **Testing ownership**: Schema Designer validates export correctness only; target AppType behavior validation is outside Phase 2 scope

**What Phase 2 Does NOT Deliver**:
- No FormulaDefinition, ControlRule, or OutputMapping entities or UI
- No relationships UI (RelationshipDefinition entity exists from Phase 1 but NO UI until Phase 2.1)
- No cascade rule configuration
- No validation severity indicators (ERROR/WARNING/INFO)
- No export format versioning or schema semantic versioning
- No import functionality (Phase 4)
- No automatic schema deployment

---

## Phase 1 Recap (CLOSED)

**Phase 1 Status**: COMPLETE and CLOSED. No changes allowed.

**What Phase 1 Delivered**:
- ✅ 4 meta-schema entities: EntityDefinition, FieldDefinition, ValidationRule, RelationshipDefinition
- ✅ Platform-defined constrained sets (field types, constraint types, entity types, cardinality)
- ✅ Meta-schema validation (name uniqueness, type constraints, referential integrity)
- ✅ AppType registration for `schema_designer`
- ✅ Project lifecycle support (create/open/save)
- ✅ Platform integration (dynamic form rendering for all 4 entities)

---

## Build Checklist (Ordered Steps)

### Step 1: Schema Editor UI Foundation

**Task**: Create the basic UI shell for the schema editor.

**What to Build**:
- [ ] **Schema project view**: Main window for editing schemas
- [ ] **Entity list panel**: Display all entities in current schema
- [ ] **Field list panel**: Display fields for selected entity
- [ ] **Validation rules panel**: Display validation rules for selected field
- [ ] **Navigation**: Select entity → view fields → select field → view validation rules

**Guarantees Required**:
- UI renders when Schema Designer project is opened
- Can navigate between entities and fields
- UI is read-only at this stage (Step 2 adds editing)

**Do NOT Build**:
- ❌ NO relationships panel (Phase 2.1)
- ❌ NO formulas panel (Phase 2.2)
- ❌ NO controls panel (Phase 2.2)
- ❌ NO output mappings panel (Phase 2.3)

---

### Step 2: Entity and Field Creation UI

**Task**: Add UI for creating and editing entities and fields.

**What to Build**:
- [ ] **"Add Entity" button**: Opens entity creation form
- [ ] **Entity creation form**: Input fields for name, type (SINGLETON/COLLECTION), description
- [ ] **Entity editing form**: Edit existing entity properties
- [ ] **"Add Field" button**: Opens field creation form (for selected entity)
- [ ] **Field creation form**: Input fields for name, type (from platform-defined set), description, required flag
- [ ] **Field editing form**: Edit existing field properties
- [ ] **Field ordering controls**: Move field up/down in display order

**Guarantees Required**:
- Entity names validated as unique before saving
- Field names validated as unique within entity before saving
- Field types validated against platform-defined set
- Entity types validated against platform-defined set
- Forms display validation errors clearly

**Do NOT Build**:
- ❌ NO relationship creation UI (Phase 2.1)
- ❌ NO formula expression editor (Phase 2.2)
- ❌ NO control rule editor (Phase 2.2)

---

### Step 3: Validation Rule Creation UI

**Task**: Add UI for creating and editing validation rules (constraint metadata only).

**What to Build**:
- [ ] **"Add Validation Rule" button**: Opens validation rule creation form (for selected field)
- [ ] **Validation rule form**: Select constraint type, provide constraint parameters (metadata only)
- [ ] **Constraint type dropdown**: Shows only constraint types applicable to field's type (applicability filtering, not semantic interpretation)
- [ ] **Parameter inputs**: Dynamic form inputs based on selected constraint type (metadata entry, not runtime validation preview)
- [ ] **Validation rule editing**: Edit existing validation rules

**Guarantees Required**:
- Constraint type dropdown filtered by field type (e.g., numeric constraints only for numeric fields)
- Constraint parameters validated for correct data type before saving (e.g., min_value must be numeric)
- Inapplicable constraint types are not shown
- UI DOES NOT execute runtime validation behavior (no preview of what "min_value=5" would reject)

**Do NOT Build**:
- ❌ NO validation severity selection (Phase 3)
- ❌ NO advanced constraint types beyond platform-defined set (Phase 2.1+)
- ❌ NO runtime validation preview (Phase 2 UI edits constraint metadata only)

---

### Step 4: Basic Export Functionality

**Task**: Add manual export to JSON file.

**What to Build**:
- [ ] **"Export Schema" button**: Opens export dialog
- [ ] **Export dialog**: Select output file path (.json extension)
- [ ] **Export quality checks**: Warn about incomplete schema definitions (entities with no fields, fields with no description, missing validation rules where expected)
- [ ] **Export format**: JSON file with structure matching platform's schema format (entities, fields, validation_rules arrays)
- [ ] **Export includes**: All entities, fields, validation rules from current project
- [ ] **Export warnings**: Display quality warnings before export (incomplete definitions, missing descriptions)

**Guarantees Required**:
- Export file is valid JSON (Phase 1 storage validation already passed, JSON serialization is correct)
- Export warns about Phase 2 quality issues (incomplete definitions, not Phase 1 correctness)
- Export file can be used by AppType authors for manual import (Schema Designer provides JSON output only)

**Manual Import Responsibility (OUT OF SCOPE)**:
- Manual copying of JSON data into target AppType's config.db is AppType author's responsibility
- Schema Designer does NOT provide import tooling or guidance beyond documentation
- Schema Designer does NOT guarantee correctness of manual import process
- Target AppType's Phase 1 storage validation will enforce correctness when data is manually inserted

**Do NOT Build**:
- ❌ NO export format versioning (Phase 3)
- ❌ NO schema semantic versioning (Phase 3)
- ❌ NO compatibility validation (Phase 3)
- ❌ NO automatic import tooling (Phase 4)
- ❌ NO automatic deployment to target AppType (Phase 4+)
- ❌ NO SQLite export (JSON only in Phase 2)
- ❌ NO manual import helper scripts or UI (Phase 4)

---

### Step 5: Internal Testing Support

**Task**: Verify schema definition completeness via UI preview (export correctness only).

**What to Build**:
- [ ] **Schema preview mode**: Authors can preview how schema will render in target AppType UI
- [ ] **Dynamic form preview**: Platform renders read-only form preview based on schema definition
- [ ] **Preview workflow**: Create entity → add fields → add validation rules → preview form rendering → verify schema definition is complete

**Guarantees Required**:
- Form previews render correctly for all defined field types (verifies export will contain valid field type values)
- Preview shows field labels, types, required indicators, validation constraint hints (metadata display only)
- Authors can verify schema definition is complete before export (no missing required metadata)

**Testing Ownership Boundary**:
- Schema Designer validates export correctness only (JSON structure, field type validity, metadata completeness)
- Target AppType behavior validation is OUT OF SCOPE (whether validation rules work correctly at runtime is target AppType's responsibility)
- Preview verifies "Can this schema be exported?" NOT "Will this schema work correctly in target AppType?"

**Do NOT Build**:
- ❌ NO runtime data entry in preview mode (preview is UI structure only, not business data)
- ❌ NO runtime validation execution in preview (preview shows constraints, does not execute them)
- ❌ NO test data persistence (Phase 3+)
- ❌ NO target AppType behavior testing (Phase 2 tests export correctness only)

---

## Validation Checklist

### UI Completeness

- [ ] Can open Schema Designer project and see schema editor UI
- [ ] Can create new entity via UI
- [ ] Can edit entity properties via UI
- [ ] Can create new field via UI
- [ ] Can edit field properties via UI
- [ ] Can reorder fields via UI
- [ ] Can create validation rule via UI
- [ ] Can edit validation rule via UI

### Export Functionality

- [ ] Can export schema to JSON file
- [ ] Export quality checks warn about incomplete definitions (missing descriptions, entities with no fields)
- [ ] Exported JSON file contains all entities, fields, validation rules
- [ ] Exported JSON structure matches platform's schema format

### Integration Testing (Manual Import Verification - OUT OF BAND)

**Note**: These tests verify manual import process, NOT automated by Schema Designer.

- [ ] Exported JSON can be manually copied into target AppType's config.db (manual process documented)
- [ ] Target AppType loads manually imported schema successfully (target AppType's Phase 1 validation enforces correctness)
- [ ] Dynamic forms render correctly in target AppType (target AppType behavior, not Schema Designer responsibility)

---

## "Do NOT Build" List (Forbidden in Phase 2)

**These features are EXPLICITLY forbidden in Phase 2. Building them will violate the phase scope.**

### Forbidden Entities (Same as Phase 1)
- ❌ FormulaDefinition entity (Phase 2.2)
- ❌ ControlRule entity (Phase 2.2)
- ❌ OutputMapping entity (Phase 2.3)

### Forbidden UI Features
- ❌ Relationships UI (Phase 2.1 - entity exists in meta-schema but NO UI)
- ❌ Formula expression editor (Phase 2.2)
- ❌ Control rule editor (Phase 2.2)
- ❌ Output mapping editor (Phase 2.3)
- ❌ Validation severity indicators (ERROR/WARNING/INFO) (Phase 3)
- ❌ Template selection UI (Phase 2.3)

### Forbidden Export/Import Features
- ❌ Export format versioning (Phase 3)
- ❌ Schema semantic versioning (Phase 3)
- ❌ Compatibility validation (Phase 3)
- ❌ Import functionality (Phase 4)
- ❌ Automatic deployment to target AppType (Phase 4+)
- ❌ Re-validation of Phase 1 rules during export (storage validation already passed)
- ❌ SQLite export (JSON only in Phase 2)
- ❌ Multiple export formats (JSON only in Phase 2)
- ❌ Manual import helper scripts or UI (Phase 4)
- ❌ Import guidance beyond documentation (Phase 4)

### Forbidden ValidationRule UI Features
- ❌ Runtime validation preview (ValidationRule UI is metadata editing only)
- ❌ Semantic constraint interpretation (e.g., checking if min < max makes business sense)
- ❌ Constraint applicability semantic checks beyond type matching (Phase 2.1+)

### Forbidden Testing Features
- ❌ Runtime data entry in preview mode (preview is UI structure only)
- ❌ Runtime validation execution in preview mode (preview shows constraints, does not execute them)
- ❌ Test data persistence (Phase 3+)
- ❌ Target AppType behavior testing (Phase 2 tests export correctness only)
- ❌ Validation rule correctness testing at runtime (target AppType responsibility)

### Forbidden Advanced Features
- ❌ Circular dependency detection for formulas (Phase 2.2)
- ❌ Control chain depth validation (Phase 2.2)
- ❌ Cascade rule safety checks (Phase 2.1)
- ❌ Advanced constraint types beyond platform-defined set (Phase 2.1+)

---

## Phase 2 Completion Criteria

Phase 2 is complete when ALL of the following are true (24 criteria):

### Functional Criteria
1. ✅ AppType author can create new Schema Designer project
2. ✅ Author can add entities via UI
3. ✅ Author can edit entity properties via UI
4. ✅ Author can add fields to entities via UI
5. ✅ Author can edit field properties via UI
6. ✅ Author can reorder fields via UI
7. ✅ Author can add validation rules to fields via UI
8. ✅ Author can edit validation rules via UI

### Export Criteria
9. ✅ Author can export schema to JSON file
10. ✅ Export quality checks warn about incomplete definitions (not Phase 1 correctness)
11. ✅ Exported JSON file contains all entities, fields, validation rules
12. ✅ Exported JSON structure matches platform's schema format

### Integration Criteria (Manual Import - OUT OF BAND)
13. ✅ Exported JSON can be manually copied into target AppType's config.db (manual process documented)
14. ✅ Target AppType loads manually imported schema successfully (target AppType Phase 1 validation enforces correctness)
15. ✅ Dynamic forms render correctly in target AppType (target AppType behavior validation, not Schema Designer responsibility)

### Testing Criteria
16. ✅ Unit tests for UI validation logic
17. ✅ Integration tests for export functionality
18. ✅ End-to-end test: create schema → export → manually import → verify target AppType works

### Documentation Criteria
19. ✅ Phase 2 completion documented
20. ✅ User guide for schema editor UI
21. ✅ JSON export workflow documentation (JSON structure, quality checks)
22. ✅ Manual import process documented (AppType author's responsibility, out-of-band)
23. ✅ Known limitations documented (no automated import, no relationships UI, no formulas/controls, JSON export only)
24. ✅ Testing ownership documented (Schema Designer validates export correctness; target AppType validates runtime behavior)

---

## Success Indicators

**How to know Phase 2 succeeded:**

1. **Can create schema via UI**:
   - Open Schema Designer project
   - Add entity "Customer" (SINGLETON)
   - Add field "name" (TEXT, required)
   - Add field "email" (TEXT, required)
   - Add validation rule "email must match pattern"
   - Save successfully

2. **Can export schema to JSON**:
   - Click "Export Schema"
   - Select output file path (.json extension)
   - Export quality checks show warnings if schema incomplete (or pass if complete)
   - JSON file created with valid structure

3. **Can manually import exported schema (OUT OF BAND)**:
   - Open exported JSON file
   - Open target AppType's config.db
   - Manually copy JSON data into config.db tables (AppType author's responsibility, not automated)
   - Target AppType's Phase 1 storage validation enforces correctness when data is inserted
   - Restart application
   - Create new project with target AppType
   - Forms render correctly (Customer entity, name/email fields) - target AppType behavior validation
   - Validation rules work at runtime (email pattern validation) - target AppType responsibility, not Schema Designer

---

## Boundary Between Phase 1 and Phase 2

| Concern | Phase 1 (CLOSED) | Phase 2 (DRAFT) |
|---------|------------------|-----------------|
| **Meta-schema entities** | Exist, can be stored/retrieved | Can be created/edited via UI |
| **Validation** | Enforced at storage layer | Storage validation still enforced; UI adds input feedback for metadata correctness |
| **ValidationRule UI** | Internal rendering only | User-facing constraint metadata editing (no semantic interpretation, no runtime preview) |
| **Forms** | Internal rendering for testing | User-facing schema editor UI |
| **Export** | Does not exist | JSON export only with quality checks (export correctness validation) |
| **Import** | Does not exist | Still does not exist (manual import out-of-band, Phase 4 for automated import) |
| **Testing Ownership** | Phase 1 validates storage correctness | Phase 2 validates export correctness; target AppType behavior is out of scope |
| **Relationships** | Stored in meta-schema (no UI) | Still no UI (Phase 2.1) |
| **Formulas/Controls** | Do not exist | Still do not exist (Phase 2.2) |
| **Validation Severity** | Simple pass/fail | Still simple pass/fail (Phase 3) |

---

## Risks and Mitigations

### Risk 1: Export Format Confusion
**Risk**: Developer implements multiple export formats (JSON and SQLite) causing scope creep.

**Mitigation**:
- **STOP**: JSON export only in Phase 2
- No SQLite export (Phase 3+)
- Export format versioning is Phase 3

### Risk 1a: Manual Import Assumptions
**Risk**: Developer builds import helper tooling or UI because "users need help with manual import."

**Mitigation**:
- **STOP**: Manual import is out-of-band (AppType author's responsibility)
- Schema Designer provides JSON output only
- No helper scripts, no import UI, no import guidance beyond documentation
- Automated import tooling is Phase 4

### Risk 2: Scope Creep (Relationships UI)
**Risk**: Developer adds relationships UI because RelationshipDefinition entity exists.

**Mitigation**:
- **STOP**: Relationships UI is Phase 2.1
- Phase 2 only builds entity/field/validation rule UI
- RelationshipDefinition entity can be stored (from Phase 1) but NO UI

### Risk 3: Export Validation Scope Creep
**Risk**: Developer adds re-validation of Phase 1 rules during export (duplicate names, invalid types, referential integrity).

**Mitigation**:
- **STOP**: Export must NOT re-validate Phase 1 rules
- Phase 1 storage validation already guarantees correctness (name uniqueness, type constraints, referential integrity)
- Export may only warn about Phase 2 quality issues (incomplete definitions, missing descriptions)
- If data is in storage, Phase 1 validation already passed

### Risk 4: Export Infrastructure Complexity
**Risk**: Developer adds export versioning, compatibility checks, or automatic deployment.

**Mitigation**:
- **STOP**: Export is MANUAL in Phase 2
- No versioning (Phase 3), no compatibility checks (Phase 3), no automatic import (Phase 4)
- Phase 2 export is "save to file, author manually copies to target AppType"

### Risk 5: UI Complexity
**Risk**: Developer builds advanced UI features (validation severity, formula editor, etc.).

**Mitigation**:
- **STOP**: Refer to "Do NOT Build" list
- Phase 2 UI is SIMPLE: forms for entity/field/validation rule creation only
- No severity indicators, no formula editor, no control editor

### Risk 6: ValidationRule Semantic Interpretation
**Risk**: Developer adds runtime validation preview or semantic checks in ValidationRule UI.

**Mitigation**:
- **STOP**: ValidationRule UI is constraint metadata editing only
- No semantic interpretation (e.g., no checking if min_value < max_value makes business sense)
- No runtime validation preview (e.g., no showing what "min_value=5" would reject)
- UI validates constraint parameter data types only (e.g., min_value must be numeric)

### Risk 7: Internal Testing Scope Creep
**Risk**: Developer implements runtime data entry and validation execution in "testing" mode.

**Mitigation**:
- **STOP**: Internal testing is UI PREVIEW only
- Preview shows form structure, field types, constraint hints (not runtime validation execution)
- No business data entry, no runtime validation semantics
- Preview verifies schema definition completeness, not runtime behavior

### Risk 8: Testing Ownership Confusion
**Risk**: Developer adds tests for target AppType behavior (e.g., "validation rules work correctly at runtime").

**Mitigation**:
- **STOP**: Phase 2 tests export correctness only
- Schema Designer validates: JSON structure, field type validity, metadata completeness
- Schema Designer does NOT validate: target AppType runtime behavior, validation rule correctness, form rendering in target AppType
- Target AppType behavior is target AppType's testing responsibility

---

## Next Steps After Phase 2

Once Phase 2 is complete and validated:

1. **Review Phase 2 deliverables** with stakeholders
2. **Document export workflow** for AppType authors
3. **Create Phase 2.1 execution checklist** (Relationships UI)
4. **Begin Phase 2.1 implementation**:
   - Build relationships UI
   - Add cascade rule configuration
   - Add relationship validation

---

**End of Phase 2 Execution Checklist (DRAFT)**

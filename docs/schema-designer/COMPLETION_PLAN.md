# SCHEMA DESIGNER COMPLETION PLAN

**Status**: APPROVED
**Date Approved**: 2026-01-24
**Authority**: AGENT_RULES.md, ADR-022, ADR-039, IMPLEMENTATION_PLAN.md

---

## 1. BASELINE CONFIRMATION

| Baseline Element | Status | Evidence |
|------------------|--------|----------|
| **All tests pass** | ✅ CONFIRMED | 2351 passed, 7 skipped, 0 failed |
| **Clean Architecture enforced** | ✅ CONFIRMED | Presentation → Application (SchemaUseCases) → Domain |
| **DTO-only MVVM** | ✅ CONFIRMED | ViewModel uses only DTOs (EntityDefinitionDTO, FieldDefinitionDTO, RelationshipDTO) |
| **No facades** | ✅ CONFIRMED | SchemaUseCases is a use-case class, not a facade |
| **Relationships ADD-ONLY** | ✅ CONFIRMED | ADR-022 Section 3: No UPDATE/DELETE methods |
| **Architecture freeze active** | ✅ CONFIRMED | AGENT_RULES.md Section 14: v2 Platform Work active |

---

## 2. GAP ANALYSIS (Schema Designer Only)

### Category A: Export UI Status

| Component | Status | Details |
|-----------|--------|---------|
| Export button in toolbar | ✅ DONE | schema_designer_view.py:186-193 |
| ExportSchemaDialog | ✅ DONE | export_schema_dialog.py |
| ViewModel export method | ✅ DONE | schema_designer_viewmodel.py:397-422 |
| SchemaUseCases.export_schema() | ✅ DONE | schema_usecases.py:277-305 |
| Export warnings display | ✅ DONE | schema_designer_view.py:1097-1123 |

**Export UI Verdict**: COMPLETE ✅

---

### Category B: Import UI Status

| Component | Status | Details |
|-----------|--------|---------|
| ImportSchemaCommand | ✅ EXISTS | import_schema_command.py |
| SchemaComparisonService | ✅ EXISTS | schema_comparison_service.py |
| SchemaImportValidationService | ✅ EXISTS | schema_import_validation_service.py |
| SchemaUseCases.import_schema() | ❌ MISSING | Not exposed in use-case class |
| Import button in toolbar | ❌ MISSING | No button |
| ImportSchemaDialog | ❌ MISSING | No dialog |
| ViewModel import method | ❌ MISSING | No method |
| Compatibility display | ❌ MISSING | No UI to show compatibility analysis |
| Import warnings display | ❌ MISSING | No UI |

**Import UI Verdict**: Backend COMPLETE, UI NOT STARTED ❌

---

### Category C: Validation Rules UI Breadth

| Constraint Type | Domain | Export/Import | Create via UI |
|-----------------|--------|---------------|---------------|
| RequiredConstraint | ✅ | ✅ | ❌ |
| MinLengthConstraint | ✅ | ✅ | ❌ |
| MaxLengthConstraint | ✅ | ✅ | ❌ |
| MinValueConstraint | ✅ | ✅ | ❌ |
| MaxValueConstraint | ✅ | ✅ | ❌ |
| PatternConstraint | ✅ | ✅ | ❌ |
| AllowedValuesConstraint | ✅ | ✅ | ❌ |
| FileExtensionConstraint | ✅ | ✅ | ❌ |
| MaxFileSizeConstraint | ✅ | ✅ | ❌ |

| Component | Status | Details |
|-----------|--------|---------|
| AddFieldConstraintCommand | ✅ EXISTS | add_field_constraint_command.py |
| SchemaUseCases.add_constraint() | ❌ MISSING | Not exposed in use-case class |
| Validation rules panel | ✅ READ-ONLY | Shows constraints, no creation |
| Add Constraint button | ❌ MISSING | No button |
| AddConstraintDialog | ❌ MISSING | No dialog |
| ViewModel add_constraint method | ❌ MISSING | No method |

**Validation Rules UI Verdict**: Backend EXISTS, UI NOT STARTED ❌

---

### Category D: Relationship Visualization/Management

| Component | Status | Details |
|-----------|--------|---------|
| Relationship panel | ✅ DONE | schema_designer_view.py:445-525 |
| Relationship list | ✅ DONE | Shows relationships for selected entity |
| Add Relationship button | ✅ DONE | Opens AddRelationshipDialog |
| AddRelationshipDialog | ✅ DONE | add_relationship_dialog.py |
| ViewModel create_relationship() | ✅ DONE | schema_designer_viewmodel.py:342-383 |
| Edit Relationship | ❌ FORBIDDEN | ADR-022: ADD-ONLY |
| Delete Relationship | ❌ FORBIDDEN | ADR-022: ADD-ONLY |

**Relationship Management Verdict**: COMPLETE per ADR-022 ✅

---

### Category E: Edit/Delete Entity/Field Operations

| Operation | Command Exists | In SchemaUseCases | ViewModel Method | UI Button/Dialog |
|-----------|----------------|-------------------|------------------|------------------|
| Edit Entity | ✅ UpdateEntityCommand | ❌ MISSING | ❌ MISSING | ❌ MISSING |
| Delete Entity | ✅ DeleteEntityCommand | ❌ MISSING | ❌ MISSING | ❌ MISSING |
| Edit Field | ✅ UpdateFieldCommand | ❌ MISSING | ❌ MISSING | ❌ MISSING |
| Delete Field | ✅ DeleteFieldCommand | ❌ MISSING | ❌ MISSING | ❌ MISSING |

**Edit/Delete Verdict**: Backend EXISTS, Not Wired to UI ❌

---

## 3. MISSING / PARTIAL FEATURES

### Feature 1: Import Schema UI
- **Layer**: Presentation (UI only)
- **Backend exists**: YES (ImportSchemaCommand, comparison/validation services)
- **Requires ADR**: NO (ADR-039 already authorizes import/export)
- **Gap**:
  - SchemaUseCases needs `import_schema()` method
  - Need ImportSchemaDialog with file picker
  - Need compatibility analysis display
  - Need confirmation for incompatible imports

### Feature 2: Add Constraint UI
- **Layer**: Presentation (UI only) + SchemaUseCases method
- **Backend exists**: YES (AddFieldConstraintCommand)
- **Requires ADR**: NO (validation rules are v1 core per plan.md Section 3.3)
- **Gap**:
  - SchemaUseCases needs `add_constraint()` method
  - Need AddConstraintDialog with constraint type selector
  - Need dynamic form based on constraint type

### Feature 3: Edit Entity UI
- **Layer**: Presentation (UI only) + SchemaUseCases method
- **Backend exists**: YES (UpdateEntityCommand)
- **Requires ADR**: NO (schema editing is core v1 functionality)
- **Gap**:
  - SchemaUseCases needs `update_entity()` method
  - Need EditEntityDialog (or reuse AddEntityDialog with pre-fill)
  - Need Edit button in entity panel

### Feature 4: Delete Entity UI
- **Layer**: Presentation (UI only) + SchemaUseCases method
- **Backend exists**: YES (DeleteEntityCommand)
- **Requires ADR**: NO (schema editing is core v1 functionality)
- **Gap**:
  - SchemaUseCases needs `delete_entity()` method
  - Need confirmation dialog with dependency warning
  - Need Delete button in entity panel

### Feature 5: Edit Field UI
- **Layer**: Presentation (UI only) + SchemaUseCases method
- **Backend exists**: YES (UpdateFieldCommand)
- **Requires ADR**: NO
- **Gap**:
  - SchemaUseCases needs `update_field()` method
  - Need EditFieldDialog (or reuse AddFieldDialog with pre-fill)
  - Need Edit button in field panel

### Feature 6: Delete Field UI
- **Layer**: Presentation (UI only) + SchemaUseCases method
- **Backend exists**: YES (DeleteFieldCommand)
- **Requires ADR**: NO
- **Gap**:
  - SchemaUseCases needs `delete_field()` method
  - Need confirmation dialog with dependency warning
  - Need Delete button in field panel

---

## 4. APPROVED COMPLETION PHASES

### Phase SD-1: Import Schema UI

**Goal**: Allow users to import schema from JSON file through UI

**Scope (ONLY)**:
- Add `import_schema()` method to SchemaUseCases
- Create ImportSchemaDialog with file picker
- Add "Import Schema" button to toolbar
- Display compatibility analysis before import
- Display import warnings/errors after import
- Confirm before force-importing incompatible schemas

**Allowed Actions**:
- Modify: `src/doc_helper/application/usecases/schema_usecases.py`
- Create: `src/doc_helper/presentation/dialogs/import_schema_dialog.py`
- Modify: `src/doc_helper/presentation/views/schema_designer_view.py`
- Modify: `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py`

**Forbidden Actions**:
- ❌ Modify ImportSchemaCommand
- ❌ Modify SchemaComparisonService
- ❌ Modify SchemaImportValidationService
- ❌ Modify any domain layer code
- ❌ Modify any infrastructure code
- ❌ Change import behavior or compatibility rules

**Stop Conditions**:
- If import command behavior is insufficient → STOP and report
- If compatibility display requires new DTOs → STOP and report
- If any domain change needed → STOP and report

**Required Tests**:
- Unit test for SchemaUseCases.import_schema()
- Unit test for ImportSchemaDialog input validation
- Integration test for import round-trip via UI

---

### Phase SD-2: Add Constraint UI

**Goal**: Allow users to add validation constraints to fields

**Scope (ONLY)**:
- Add `add_constraint()` method to SchemaUseCases
- Create AddConstraintDialog with constraint type dropdown
- Add "Add Constraint" button to validation rules panel
- Support Required, MinValue, MaxValue, MinLength, MaxLength constraints
- Refresh validation rules display after adding

**Allowed Actions**:
- Modify: `src/doc_helper/application/usecases/schema_usecases.py`
- Create: `src/doc_helper/presentation/dialogs/add_constraint_dialog.py`
- Modify: `src/doc_helper/presentation/views/schema_designer_view.py`
- Modify: `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py`

**Forbidden Actions**:
- ❌ Modify AddFieldConstraintCommand
- ❌ Modify constraint domain classes
- ❌ Add new constraint types
- ❌ Modify constraint serialization

**Stop Conditions**:
- If constraint command requires parameters not documented → STOP and report
- If domain changes needed → STOP and report

**Required Tests**:
- Unit test for SchemaUseCases.add_constraint()
- Unit test for AddConstraintDialog validation
- Integration test for constraint round-trip (export/import)

---

### Phase SD-3: Edit/Delete Entity UI

**Goal**: Allow users to edit and delete entities

**Scope (ONLY)**:
- Add `update_entity()` and `delete_entity()` methods to SchemaUseCases
- Create EditEntityDialog (may reuse AddEntityDialog with mode flag)
- Add Edit/Delete buttons to entity panel
- Show confirmation with dependency warning before delete

**Allowed Actions**:
- Modify: `src/doc_helper/application/usecases/schema_usecases.py`
- Create or modify: entity editing dialog
- Modify: `src/doc_helper/presentation/views/schema_designer_view.py`
- Modify: `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py`

**Forbidden Actions**:
- ❌ Modify UpdateEntityCommand
- ❌ Modify DeleteEntityCommand
- ❌ Modify domain entity classes

**Stop Conditions**:
- If commands are insufficient → STOP and report

**Required Tests**:
- Unit tests for update_entity(), delete_entity()
- UI test for edit flow
- UI test for delete confirmation

---

### Phase SD-4: Edit/Delete Field UI

**Goal**: Allow users to edit and delete fields

**Scope (ONLY)**:
- Add `update_field()` and `delete_field()` methods to SchemaUseCases
- Create EditFieldDialog (may reuse AddFieldDialog with mode flag)
- Add Edit/Delete buttons to field panel
- Show confirmation with dependency warning before delete

**Allowed Actions**:
- Modify: `src/doc_helper/application/usecases/schema_usecases.py`
- Create or modify: field editing dialog
- Modify: `src/doc_helper/presentation/views/schema_designer_view.py`
- Modify: `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py`

**Forbidden Actions**:
- ❌ Modify UpdateFieldCommand
- ❌ Modify DeleteFieldCommand
- ❌ Modify domain field classes

**Stop Conditions**:
- If commands are insufficient → STOP and report

**Required Tests**:
- Unit tests for update_field(), delete_field()
- UI test for edit flow
- UI test for delete confirmation

---

### Phase SD-5: Test Coverage

**Goal**: Ensure Schema Designer has adequate test coverage

**Scope (ONLY)**:
- Add missing ViewModel unit tests
- Add missing dialog unit tests
- Add integration tests for full workflows

**Allowed Actions**:
- Modify/create files in `tests/` only

**Forbidden Actions**:
- ❌ Any production code changes

**Required Tests**:
- All ViewModel methods have unit tests
- All dialogs have input validation tests
- Import/export round-trip integration test

---

## 5. EXECUTION ORDER (MANDATORY)

```
Phase SD-1 (Import UI)
    ↓
Phase SD-2 (Add Constraint UI)
    ↓
Phase SD-3 (Edit/Delete Entity UI)
    ↓
Phase SD-4 (Edit/Delete Field UI)
    ↓
Phase SD-5 (Test Coverage)
```

### Why This Order

| Order | Reason |
|-------|--------|
| **SD-1 first** | Import/Export is the primary deliverable per IMPLEMENTATION_PLAN.md Phase 3-4. Cannot test round-trip without import. |
| **SD-2 before SD-3/4** | Constraints are core validation functionality. Edit/Delete are convenience features. |
| **SD-3 before SD-4** | Entity operations establish UI pattern. Field operations reuse pattern. |
| **SD-5 last** | Tests verify completed implementation. Writing tests for incomplete features is wasteful. |

---

## 6. COMPLIANCE CHECKLIST (AGENT_RULES.md)

| Rule | Compliant | Evidence |
|------|-----------|----------|
| Section 2: Presentation → Application only | ✅ | All phases modify only Presentation calling SchemaUseCases |
| Section 3: DTO-only in Presentation | ✅ | No domain imports proposed |
| Section 4: DTOs are immutable, no behavior | ✅ | No DTO changes proposed |
| Section 10: Near-Term authorized | ✅ | Import/Export authorized via ADR-039 |
| Section 12: Decision precedence | ✅ | Plan follows AGENT_RULES.md, ADR-022, ADR-039 |
| Section 13: Execution discipline | ✅ | Each phase defines exact scope, forbidden actions, stop conditions |
| ADR-022: Relationships ADD-ONLY | ✅ | No edit/delete relationship features proposed |

---

## 7. DEFINITION OF "SCHEMA DESIGNER DONE"

### Mandatory Features (Must Have)

- [x] Create entities (✅ DONE)
- [x] Create fields (✅ DONE)
- [x] Create relationships (✅ DONE - ADD-ONLY)
- [x] View entities, fields, validation rules, relationships (✅ DONE)
- [x] Export schema to file from UI (✅ DONE)
- [ ] Import schema from file from UI
- [ ] Edit entity metadata from UI
- [ ] Delete entity from UI (with confirmation)
- [ ] Edit field metadata from UI
- [ ] Delete field from UI (with confirmation)
- [ ] Add validation constraints from UI (required, min/max value, min/max length)
- [ ] Test coverage for ViewModel and dialogs

### Optional Features (Nice to Have)

- [ ] Pattern constraint UI
- [ ] Reorder fields UI
- [ ] Reorder field options UI
- [ ] Constraint severity selection in UI

### Explicitly Deferred (NOT in "Done")

- Edit/delete relationships (ADD-ONLY per ADR-022)
- Formula editor
- Control rule editor
- Output mapping editor
- Cardinality selection for relationships
- Cascade behavior selection
- Visual graph editor
- Schema diffing
- All Phase 5 deferred features from IMPLEMENTATION_PLAN.md

---

## 8. RISK WARNINGS

### Top 3 Architectural Risks If Phases Are Rushed

| Risk | Description | Mitigation |
|------|-------------|------------|
| **A1: Domain layer pollution** | Adding UI convenience methods to Domain or Application commands | Strict file boundary enforcement per phase. ViewModel must not access Domain directly. |
| **A2: DTO-to-Domain reverse mapping** | Creating DTOs that try to rehydrate Domain state | All creation/update goes through Commands. DTOs are read-only data carriers. |
| **A3: Breaking Import/Export contract** | Changing export format to support new UI features | Export format is locked. UI must adapt to existing format, not vice versa. |

### Top 3 UX Risks If UI Is Added Incorrectly

| Risk | Description | Mitigation |
|------|-------------|------------|
| **U1: Inconsistent button placement** | Edit/Delete buttons in different locations for entities vs fields | Define button placement pattern in Phase SD-3, reuse in SD-4. |
| **U2: Missing confirmation dialogs** | Delete operations without warning | All destructive operations (delete, import-overwrite) must show confirmation. |
| **U3: Silent failures** | Operations fail without user feedback | All Command results must be displayed (success toast, error dialog). |

### Top 3 Scope Creep Traps to Avoid

| Trap | Description | Rule |
|------|-------------|------|
| **S1: "While we're here" refactoring** | Temptation to refactor existing dialogs while adding new ones | Only change files explicitly listed in phase scope. |
| **S2: Formula/Control editor creep** | Requests to add formula editor "since we're doing field editing" | Formula/Control editors are Phase 2.2 features. Not in current scope. |
| **S3: Advanced validation UI** | Requests for pattern builder, regex tester, conditional validation | Basic constraint UI only. Validation Rule Wizard is deferred. |

---

## APPROVAL RECORD

**Approved by**: User (2026-01-24)
**Supersedes**: COMPLETION_PLAN_DRAFT.md

---

**End of Approved Plan**

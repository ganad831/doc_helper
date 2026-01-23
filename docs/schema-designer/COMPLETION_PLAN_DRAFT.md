# SCHEMA DESIGNER COMPLETION PLAN

**Status**: DRAFT

**Date**: 2026-01-23

**Purpose**: Safe, ordered completion plan for Schema Designer

**Authority**: Gap Analysis (2026-01-23), AGENT_RULES.md, IMPLEMENTATION_PLAN.md

---

## 1️⃣ CURRENT STATE CONFIRMATION

### What Schema Designer CAN Do Today

- ✅ Create new entities (AddEntityDialog)
- ✅ Add fields to entities (AddFieldDialog, all 12 field types)
- ✅ Create relationships (AddRelationshipDialog, ADD-ONLY per ADR-022)
- ✅ View entity list
- ✅ View field list for selected entity
- ✅ View validation rules for selected field (READ-ONLY)
- ✅ View relationships for selected entity (READ-ONLY)
- ✅ Export schema programmatically (ExportSchemaCommand exists)
- ✅ Import schema programmatically (ImportSchemaCommand exists)
- ✅ UX polish: Welcome dialog, Help dialog, Unsaved changes warning

### What Schema Designer CANNOT Do Today

- ❌ Export schema from UI (no button, no dialog)
- ❌ Import schema from UI (no button, no dialog)
- ❌ Edit existing entities (backend exists, no UI)
- ❌ Delete entities (backend exists, no UI)
- ❌ Edit existing fields (backend exists, no UI)
- ❌ Delete fields (backend exists, no UI)
- ❌ Create validation rules/constraints (backend exists, no UI)
- ❌ Edit validation rules/constraints
- ❌ Create formulas in Schema Designer
- ❌ Create control rules in Schema Designer
- ❌ Create output mappings (not started)
- ❌ Set field display order explicitly

---

## 2️⃣ MISSING FEATURES BY CATEGORY

### Category A: UI Missing But Backend Exists

| Feature | Backend Location | UI Gap |
|---------|------------------|--------|
| Export Schema | ExportSchemaCommand | No button in toolbar, no file dialog |
| Import Schema | ImportSchemaCommand | No button in toolbar, no file dialog, no error display |
| Delete Entity | DeleteEntityCommand | No button in entity panel |
| Delete Field | DeleteFieldCommand | No button in field panel |
| Update Entity | UpdateEntityCommand | No edit button, no edit dialog |
| Update Field | UpdateFieldCommand | No edit button, no edit dialog |
| Add Constraint | AddFieldConstraintCommand | No button, no dialog |
| Update Field Option | UpdateFieldOptionCommand | No UI |
| Reorder Field Options | ReorderFieldOptionsCommand | No UI |

### Category B: Backend Missing Entirely

| Feature | Domain | Application | Infrastructure |
|---------|--------|-------------|----------------|
| OutputMapping entity | ❌ | ❌ | ❌ |
| Capability declarations | ❌ | ❌ | ❌ |

### Category C: Partial Backend (Domain Exists, No Schema Designer Commands)

| Feature | Domain Status | Application Gap |
|---------|---------------|-----------------|
| ControlRule | ✅ control_rule.py | No Schema Designer commands for CRUD |
| Formula | ✅ formula property on FieldDefinition | No Schema Designer command to set formula |

### Category D: Validation Rules Missing UI

| Constraint Type | Domain | Can Export | Can Create via UI |
|-----------------|--------|------------|-------------------|
| RequiredConstraint | ✅ | ✅ | ❌ |
| MinLengthConstraint | ✅ | ✅ | ❌ |
| MaxLengthConstraint | ✅ | ✅ | ❌ |
| MinValueConstraint | ✅ | ✅ | ❌ |
| MaxValueConstraint | ✅ | ✅ | ❌ |
| PatternConstraint | ✅ | ✅ | ❌ |
| AllowedValuesConstraint | ✅ | ✅ | ❌ |
| FileExtensionConstraint | ✅ | ✅ | ❌ |
| MaxFileSizeConstraint | ✅ | ✅ | ❌ |

### Category E: Formula / Control Rules Missing

| Feature | Domain | Application | UI |
|---------|--------|-------------|-----|
| Set field as calculated | ✅ formula property | ❌ No SetFieldFormulaCommand | ❌ |
| Formula expression editor | ✅ parser exists | ❌ | ❌ |
| Create control rule | ✅ ControlRule entity | ❌ No CreateControlRuleCommand for Schema Designer | ❌ |
| Control rule editor | ✅ | ❌ | ❌ |

### Category F: Import / Export UX Missing

| Component | Backend | UI |
|-----------|---------|-----|
| Export button | ✅ | ❌ |
| Export file picker | N/A | ❌ |
| Export warnings display | ✅ ExportWarning | ❌ |
| Export success feedback | ✅ ExportResult | ❌ |
| Import button | ✅ | ❌ |
| Import file picker | N/A | ❌ |
| Import compatibility display | ✅ CompatibilityResult | ❌ |
| Import error display | ✅ ImportValidationError | ❌ |
| Import success feedback | ✅ ImportResult | ❌ |

### Category G: Edit / Delete UX Missing

| Operation | Backend Command | Dialog Exists | Button Exists |
|-----------|-----------------|---------------|---------------|
| Edit Entity | UpdateEntityCommand | ❌ | ❌ |
| Delete Entity | DeleteEntityCommand | ❌ (need confirmation) | ❌ |
| Edit Field | UpdateFieldCommand | ❌ | ❌ |
| Delete Field | DeleteFieldCommand | ❌ (need confirmation) | ❌ |

### Category H: Explicitly Deferred (Out of Scope)

Per IMPLEMENTATION_PLAN.md Phase 5 (Deferred Features):

- ❌ Visual Graph Editor
- ❌ Live AppType Editing
- ❌ Schema Migrations
- ❌ Real-Time Collaboration
- ❌ Code Generation
- ❌ Template Designer Integration
- ❌ Schema Diffing Tool
- ❌ Schema Composition
- ❌ AI-Assisted Schema Generation
- ❌ Validation Rule Wizard (advanced)

Per ADR-022:

- ❌ Edit Relationships (ADD-ONLY)
- ❌ Delete Relationships (ADD-ONLY)

---

## 3️⃣ REQUIRED PHASES TO FINISH SCHEMA DESIGNER

### Phase 7: Export UI

**Objective**: Allow users to export schema from Schema Designer UI

| Attribute | Value |
|-----------|-------|
| Backend already exists | Yes - ExportSchemaCommand |
| UI missing | Yes |
| Scope | UI only (Presentation layer) |
| Forbidden | Domain changes, Application logic changes |

**Exact Scope**:
- Add "Export Schema" button to Schema Designer toolbar
- Create ExportSchemaDialog with file picker
- Display export warnings after export
- Display export success/failure feedback

**Files Allowed to Change**:
- `src/doc_helper/presentation/views/schema_designer_view.py`
- `src/doc_helper/presentation/dialogs/` (new dialog)
- `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py` (add export method)

**Files Forbidden**:
- `src/doc_helper/domain/**/*`
- `src/doc_helper/application/commands/schema/export_schema_command.py`
- `src/doc_helper/infrastructure/**/*`

**Prerequisites**:
- ExportSchemaCommand must exist (✅ exists)
- SchemaDesignerViewModel must exist (✅ exists)

---

### Phase 8: Import UI

**Objective**: Allow users to import schema from Schema Designer UI

| Attribute | Value |
|-----------|-------|
| Backend already exists | Yes - ImportSchemaCommand |
| UI missing | Yes |
| Scope | UI only (Presentation layer) |
| Forbidden | Domain changes, Application logic changes |

**Exact Scope**:
- Add "Import Schema" button to Schema Designer toolbar
- Create ImportSchemaDialog with file picker
- Display compatibility analysis before import
- Display import warnings/errors
- Display import success feedback
- Confirm before destructive import (incompatible schema)

**Files Allowed to Change**:
- `src/doc_helper/presentation/views/schema_designer_view.py`
- `src/doc_helper/presentation/dialogs/` (new dialog)
- `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py` (add import method)

**Files Forbidden**:
- `src/doc_helper/domain/**/*`
- `src/doc_helper/application/commands/schema/import_schema_command.py`
- `src/doc_helper/application/services/schema_comparison_service.py`
- `src/doc_helper/application/services/schema_import_validation_service.py`
- `src/doc_helper/infrastructure/**/*`

**Prerequisites**:
- ImportSchemaCommand must exist (✅ exists)
- SchemaComparisonService must exist (✅ exists)
- SchemaImportValidationService must exist (✅ exists)
- Phase 7 (Export UI) should be complete (for testing round-trip)

---

### Phase 9: Edit Entity UI

**Objective**: Allow users to edit existing entity metadata

| Attribute | Value |
|-----------|-------|
| Backend already exists | Yes - UpdateEntityCommand |
| UI missing | Yes |
| Scope | UI only (Presentation layer) |
| Forbidden | Domain changes, Application logic changes |

**Exact Scope**:
- Add "Edit" button to entity panel (or context menu)
- Create EditEntityDialog (reuse AddEntityDialog pattern with pre-fill)
- Wire to UpdateEntityCommand via ViewModel

**Files Allowed to Change**:
- `src/doc_helper/presentation/views/schema_designer_view.py`
- `src/doc_helper/presentation/dialogs/` (new or modified dialog)
- `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py` (add update_entity method)

**Files Forbidden**:
- `src/doc_helper/domain/**/*`
- `src/doc_helper/application/commands/schema/update_entity_command.py`
- `src/doc_helper/infrastructure/**/*`

**Prerequisites**:
- UpdateEntityCommand must exist (✅ exists)

---

### Phase 10: Delete Entity UI

**Objective**: Allow users to delete entities with confirmation

| Attribute | Value |
|-----------|-------|
| Backend already exists | Yes - DeleteEntityCommand |
| UI missing | Yes |
| Scope | UI only (Presentation layer) |
| Forbidden | Domain changes, Application logic changes |

**Exact Scope**:
- Add "Delete" button to entity panel (or context menu)
- Show confirmation dialog with dependency warning
- Wire to DeleteEntityCommand via ViewModel
- Refresh entity list after deletion

**Files Allowed to Change**:
- `src/doc_helper/presentation/views/schema_designer_view.py`
- `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py` (add delete_entity method)

**Files Forbidden**:
- `src/doc_helper/domain/**/*`
- `src/doc_helper/application/commands/schema/delete_entity_command.py`
- `src/doc_helper/infrastructure/**/*`

**Prerequisites**:
- DeleteEntityCommand must exist (✅ exists)
- Phase 9 (Edit Entity) recommended first (consistent UI pattern)

---

### Phase 11: Edit Field UI

**Objective**: Allow users to edit existing field metadata

| Attribute | Value |
|-----------|-------|
| Backend already exists | Yes - UpdateFieldCommand |
| UI missing | Yes |
| Scope | UI only (Presentation layer) |
| Forbidden | Domain changes, Application logic changes |

**Exact Scope**:
- Add "Edit" button to field panel (or context menu)
- Create EditFieldDialog (reuse AddFieldDialog pattern with pre-fill)
- Wire to UpdateFieldCommand via ViewModel

**Files Allowed to Change**:
- `src/doc_helper/presentation/views/schema_designer_view.py`
- `src/doc_helper/presentation/dialogs/` (new or modified dialog)
- `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py` (add update_field method)

**Files Forbidden**:
- `src/doc_helper/domain/**/*`
- `src/doc_helper/application/commands/schema/update_field_command.py`
- `src/doc_helper/infrastructure/**/*`

**Prerequisites**:
- UpdateFieldCommand must exist (✅ exists)

---

### Phase 12: Delete Field UI

**Objective**: Allow users to delete fields with confirmation

| Attribute | Value |
|-----------|-------|
| Backend already exists | Yes - DeleteFieldCommand |
| UI missing | Yes |
| Scope | UI only (Presentation layer) |
| Forbidden | Domain changes, Application logic changes |

**Exact Scope**:
- Add "Delete" button to field panel (or context menu)
- Show confirmation dialog with dependency warning
- Wire to DeleteFieldCommand via ViewModel
- Refresh field list after deletion

**Files Allowed to Change**:
- `src/doc_helper/presentation/views/schema_designer_view.py`
- `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py` (add delete_field method)

**Files Forbidden**:
- `src/doc_helper/domain/**/*`
- `src/doc_helper/application/commands/schema/delete_field_command.py`
- `src/doc_helper/infrastructure/**/*`

**Prerequisites**:
- DeleteFieldCommand must exist (✅ exists)
- Phase 11 (Edit Field) recommended first (consistent UI pattern)

---

### Phase 13: Add Constraint UI

**Objective**: Allow users to add validation constraints to fields

| Attribute | Value |
|-----------|-------|
| Backend already exists | Yes - AddFieldConstraintCommand |
| UI missing | Yes |
| Scope | UI only (Presentation layer) |
| Forbidden | Domain changes, Application logic changes |

**Exact Scope**:
- Add "Add Constraint" button to validation rules panel
- Create AddConstraintDialog with constraint type selector
- Dynamic form based on constraint type (required, min/max, pattern, etc.)
- Wire to AddFieldConstraintCommand via ViewModel
- Refresh validation rules after adding

**Files Allowed to Change**:
- `src/doc_helper/presentation/views/schema_designer_view.py`
- `src/doc_helper/presentation/dialogs/` (new dialog)
- `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py` (add add_constraint method)

**Files Forbidden**:
- `src/doc_helper/domain/validation/constraints.py`
- `src/doc_helper/application/commands/schema/add_field_constraint_command.py`
- `src/doc_helper/infrastructure/**/*`

**Prerequisites**:
- AddFieldConstraintCommand must exist (✅ exists)
- Phase 11 (Edit Field) should be complete (constraint UI is child of field editing)

---

### Phase 14: Tests for Schema Designer

**Objective**: Ensure test coverage for all Schema Designer components

| Attribute | Value |
|-----------|-------|
| Scope | Tests only |
| Forbidden | Production code changes |

**Exact Scope**:
- Unit tests for SchemaDesignerViewModel (all methods)
- Unit tests for all Schema Designer dialogs
- Integration tests for export/import round-trip
- Smoke tests for UI interactions

**Files Allowed to Change**:
- `tests/unit/presentation/viewmodels/test_schema_designer_viewmodel*.py`
- `tests/unit/presentation/dialogs/test_*.py` (Schema Designer dialogs)
- `tests/integration/schema_designer/` (new)

**Files Forbidden**:
- `src/**/*` (no production code)

**Prerequisites**:
- Phases 7-13 complete

---

## 4️⃣ EXECUTION ORDER (CRITICAL)

### Required Order

```
Phase 7 (Export UI)
    ↓
Phase 8 (Import UI)
    ↓
Phase 9 (Edit Entity UI)
    ↓
Phase 10 (Delete Entity UI)
    ↓
Phase 11 (Edit Field UI)
    ↓
Phase 12 (Delete Field UI)
    ↓
Phase 13 (Add Constraint UI)
    ↓
Phase 14 (Tests)
```

### Why This Order

| Order | Reason |
|-------|--------|
| **7 before 8** | Export must work before Import can be tested. Import validation depends on comparing imported schema against existing. Cannot verify import works without export. |
| **8 before 9-12** | Import/Export is the primary deliverable per IMPLEMENTATION_PLAN.md Phase 3-4. Edit/Delete are Phase 2 Step 3 features. |
| **9 before 10** | Edit establishes UI pattern (dialog, button placement). Delete reuses pattern. Deleting without ability to edit is poor UX. |
| **11 before 12** | Same reasoning as 9→10. Edit fields before delete fields. |
| **11 before 13** | Constraints belong to fields. Edit field UI should exist before constraint UI. Constraint dialog may be accessed from Edit Field dialog. |
| **14 last** | Tests verify completed implementation. Writing tests for incomplete features is wasteful. |

### What Breaks If Order Is Violated

| Violation | Consequence |
|-----------|-------------|
| Import before Export | Cannot test import (no files to import) |
| Delete before Edit | Inconsistent UI patterns, users cannot recover from accidental intent to delete |
| Constraints before Edit Field | No context for constraint UI, unclear which field constraint applies to |
| Tests before implementation | Tests will fail, require constant rewriting |

---

## 5️⃣ VALIDATION RULE STRATEGY

### Question: First-Class Entity vs. Embedded Constraints?

**Current State**: Validation rules are embedded as `constraints` tuple in `FieldDefinition`. They are NOT first-class entities with their own IDs.

**Recommendation**: **Keep as embedded constraints** (do NOT change to first-class entity)

**Rationale**:
1. Domain layer already defines constraints as value objects (immutable, no ID)
2. Changing to first-class entity would require Domain changes (FORBIDDEN per AGENT_RULES.md v1 behavior lock)
3. AddFieldConstraintCommand already exists and works with current architecture
4. Export/Import already handles constraints correctly
5. No business requirement for constraint versioning or cross-field constraint sharing

### Minimum UI for Phase 2 Completion

Per IMPLEMENTATION_PLAN.md Phase 2:

| Requirement | Current Status | Needed |
|-------------|----------------|--------|
| Add "required" constraint | Backend ✅, UI ❌ | AddConstraintDialog |
| Add min/max constraints (number) | Backend ✅, UI ❌ | AddConstraintDialog |
| Add min_length/max_length (text) | Backend ✅, UI ❌ | AddConstraintDialog |

**Minimum**: One dialog (AddConstraintDialog) that supports:
- Required constraint (checkbox or dedicated button)
- Min/Max value constraints (number inputs)
- Min/Max length constraints (number inputs)

**Pattern constraint**: Can be included but is lower priority (Phase 2.1 per plan)

### Explicitly Deferred

- Edit existing constraints (no backend command exists)
- Delete constraints (no backend command exists)
- Constraint severity selection in UI (severity exists in domain, but UI can default to ERROR)
- Validation Rule Wizard (per IMPLEMENTATION_PLAN.md Phase 5 deferred)

---

## 6️⃣ DEFINITION OF "SCHEMA DESIGNER DONE"

### Mandatory Features (Must Have)

- [ ] Create entities (✅ DONE)
- [ ] Create fields (✅ DONE)
- [ ] Create relationships (✅ DONE - ADD-ONLY)
- [ ] View entities, fields, validation rules, relationships (✅ DONE)
- [ ] Export schema to file from UI
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

### "Done" Checklist

Schema Designer is **DONE** when a user can:

1. Open Schema Designer
2. Create a new entity
3. Add fields to that entity
4. Add validation constraints to fields
5. Create relationships between entities
6. Edit entity/field metadata if they make a mistake
7. Delete entities/fields they no longer need
8. Export the schema to a JSON file
9. Import a schema from a JSON file (with compatibility warnings)
10. Close Schema Designer with unsaved changes warning

---

## 7️⃣ RISK WARNINGS

### Top 3 Architectural Risks If Phases Are Rushed

| Risk | Description | Mitigation |
|------|-------------|------------|
| **A1: Domain layer pollution** | Adding UI convenience methods to Domain or Application commands | Strict file boundary enforcement per phase. ViewModel must not access Domain directly. |
| **A2: DTO-to-Domain reverse mapping** | Creating DTOs that try to rehydrate Domain state | All creation/update goes through Commands. DTOs are read-only data carriers. |
| **A3: Breaking Import/Export contract** | Changing export format to support new UI features | Export format is locked. UI must adapt to existing format, not vice versa. |

### Top 3 UX Risks If UI Is Added Incorrectly

| Risk | Description | Mitigation |
|------|-------------|------------|
| **U1: Inconsistent button placement** | Edit/Delete buttons in different locations for entities vs fields | Define button placement pattern in Phase 9, reuse in 10-12. |
| **U2: Missing confirmation dialogs** | Delete operations without warning | All destructive operations (delete, import-overwrite) must show confirmation. |
| **U3: Silent failures** | Operations fail without user feedback | All Command results must be displayed (success toast, error dialog). |

### Top 3 Scope Creep Traps to Avoid

| Trap | Description | Rule |
|------|-------------|------|
| **S1: "While we're here" refactoring** | Temptation to refactor existing dialogs while adding new ones | Only change files explicitly listed in phase scope. |
| **S2: Formula/Control editor creep** | Requests to add formula editor "since we're doing field editing" | Formula/Control editors are Phase 2.2 features. Not in current scope. |
| **S3: Advanced validation UI** | Requests for pattern builder, regex tester, conditional validation | Basic constraint UI only. Validation Rule Wizard is deferred (Phase 5). |

---

## STOP CONDITIONS ENCOUNTERED

**None encountered.** All missing features can be implemented with:
- UI-only changes (Presentation layer)
- Existing backend commands (Application layer)
- No Domain changes required
- No new ADRs required
- No AGENT_RULES.md conflicts

---

**Plan Complete. No code written. No features proposed beyond gap analysis scope.**

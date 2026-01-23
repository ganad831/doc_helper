# SCHEMA DESIGNER GAP ANALYSIS

**Date**: 2026-01-23

**Purpose**: Comprehensive audit of Schema Designer implementation status against IMPLEMENTATION_PLAN.md

**Reference Documents**:
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- [AGENT_RULES.md](../../AGENT_RULES.md)
- Completed Phases: 1, 2, 2.1 (partial), 3 (partial), 4 (partial), 5, 6A, 6B

---

## EXECUTIVE SUMMARY

**Overall Completeness Estimate**: ~60-65% for Phase 2 goals, ~40% for full IMPLEMENTATION_PLAN.md scope

**Major Missing Areas**:
1. **UI - Import/Export**: Backend complete, NO export/import buttons in Schema Designer UI
2. **UI - Validation Rule Creation**: Domain constraints complete, NO UI to create/edit validation rules
3. **UI - Edit/Delete Operations**: Only CREATE operations implemented (Phase 2 Step 2 complete, Step 3 not done)
4. **Advanced Schema Features**: Formula editor, Control rule editor, Output mapping editor - NOT STARTED
5. **Tests**: Minimal test coverage for Schema Designer components

---

## DETAILED GAP ANALYSIS (By Phase from IMPLEMENTATION_PLAN.md)

### Phase 1: Core Meta-Schema

| Feature | Planned | Domain | Application | Infrastructure | UI | Status | Notes |
|---------|---------|--------|-------------|----------------|----|----|-------|
| EntityDefinition entity | Yes | Yes - entity_definition.py | Yes - DTO, Query, Commands | Yes - SqliteSchemaRepository | Yes | **IMPLEMENTED** | Complete aggregate root |
| FieldDefinition entity | Yes | Yes - field_definition.py | Yes - DTO, Commands | Yes | Yes | **IMPLEMENTED** | Value object in EntityDefinition |
| RelationshipDefinition entity | Yes | Yes - relationship_definition.py | Yes - DTO, Query, Command | Yes - SqliteRelationshipRepository | Yes | **IMPLEMENTED** | ADD-ONLY per ADR-022 |
| ValidationRule entity | Yes | Partial - Constraints only | Partial - Embedded in FieldDTO | Yes | Partial - READ-ONLY | **PARTIAL** | Not first-class entity; constraints embedded in FieldDefinition |
| FormulaDefinition entity | Yes | Partial - `formula` property only | No | No | No | **PARTIAL** | Formula is a property on FieldDefinition, not a separate entity |
| ControlRule entity | Yes | Yes - control_rule.py | No Schema Designer commands | No | No | **PARTIAL** | Domain exists but NOT in Schema Designer |
| OutputMapping entity | Phase 2.3 | No | No | No | No | **NOT STARTED** | Deferred per plan |

---

### Phase 2: Minimum Viable Schema Designer

| Feature | Planned | Backend | UI | Status | Notes |
|---------|---------|---------|----|----|-------|
| Create entities | Yes | Yes - CreateEntityCommand | Yes - AddEntityDialog | **IMPLEMENTED** | |
| Add entity, name it, choose singleton/collection | Yes | Yes | Yes | **IMPLEMENTED** | |
| See list of entities | Yes | Yes - GetSchemaEntitiesQuery | Yes - Entity panel | **IMPLEMENTED** | |
| Delete entities | Yes | Yes - DeleteEntityCommand | No | **PARTIAL** | Backend exists, NO UI button |
| Create fields | Yes | Yes - AddFieldCommand | Yes - AddFieldDialog | **IMPLEMENTED** | |
| Add field to entity, choose type | Yes | Yes | Yes | **IMPLEMENTED** | 12 field types |
| Mark field required/optional | Yes | Yes | Yes | **IMPLEMENTED** | |
| Set display order | Yes | Partial | No | **PARTIAL** | No explicit UI for ordering |
| Add "required" constraint | Yes | Yes - RequiredConstraint | No | **PARTIAL** | Domain exists, NO creation UI |
| Add min/max constraints (number) | Yes | Yes - Min/MaxValueConstraint | No | **PARTIAL** | Domain exists, NO creation UI |
| Add min_length/max_length (text) | Yes | Yes - Min/MaxLengthConstraint | No | **PARTIAL** | Domain exists, NO creation UI |
| Add min_date/max_date (date) | Yes | Partial - Uses Min/MaxValueConstraint | No | **PARTIAL** | No explicit date constraint |
| Export schema | Yes | Yes - ExportSchemaCommand | No | **PARTIAL** | **Backend exists, NO UI button** |
| Export validation results | Yes | Yes - Export with warnings | No | **PARTIAL** | Backend handles it |

---

### Phase 2.1: Relationships and Advanced Validation

| Feature | Planned | Backend | UI | Status | Notes |
|---------|---------|---------|----|----|-------|
| Define relationships | Yes | Yes - CreateRelationshipCommand | Yes - AddRelationshipDialog | **IMPLEMENTED** | |
| Specify cardinality | Partial | No | No | **NOT IMPLEMENTED** | ADR-022 uses CONTAINS/REFERENCES/ASSOCIATES, not cardinality |
| Choose cascade behavior | Partial | No | No | **NOT IMPLEMENTED** | Not in ADR-022 |
| Name inverse relationship | Yes | Yes - inverse_name_key | Yes | **IMPLEMENTED** | |
| Pattern/regex validation | Yes | Yes - PatternConstraint | No | **PARTIAL** | Domain exists, NO creation UI |

---

### Phase 2.2: Formulas and Controls

| Feature | Planned | Backend | UI | Status | Notes |
|---------|---------|---------|----|----|-------|
| Mark field as calculated | Yes | Partial - Formula property exists | No | **PARTIAL** | No Schema Designer UI |
| Enter formula expression | Yes | Partial - Formula parser exists | No | **NOT STARTED** | No formula editor in Schema Designer |
| Validate field references exist | Yes | Yes - In formula parser | No | **PARTIAL** | No UI feedback |
| Detect circular dependencies | Yes | Yes - dependency_tracker.py | No | **PARTIAL** | No UI feedback |
| Define "If Field A = X, hide Field B" | Yes | Yes - ControlRule domain | No | **NOT STARTED** | No control rule editor |
| Specify control chains | Yes | Yes - effect_evaluator.py | No | **NOT STARTED** | |
| Max chain depth (10) | Yes | Yes | No | **PARTIAL** | Implemented in evaluator |

---

### Phase 2.3: Output Mappings

| Feature | Planned | Backend | UI | Status | Notes |
|---------|---------|---------|----|----|-------|
| Map fields to Word template tags | No | No | No | **NOT STARTED** | Deferred |
| Choose transformers | No | No | No | **NOT STARTED** | Deferred |
| Excel cell references | No | No | No | **NOT STARTED** | Deferred |
| Template reference guide | No | No | No | **NOT STARTED** | Deferred |

---

### Phase 3: Validation & Export

| Feature | Planned | Backend | UI | Status | Notes |
|---------|---------|---------|----|----|-------|
| Continuous validation | Yes | Partial | No | **PARTIAL** | No real-time UI feedback |
| Export-time validation | Yes | Yes - ExportSchemaCommand | No | **PARTIAL** | No UI trigger |
| ERROR-level blocking | Yes | Yes | No | **PARTIAL** | Backend logic exists |
| WARNING-level warnings | Yes | Yes - ExportWarning | No | **PARTIAL** | Backend logic exists |
| Export metadata (version, schema_id) | Yes | Yes | No | **PARTIAL** | Backend complete |
| Capability declarations | Yes | No | No | **NOT STARTED** | |

---

### Phase 4: Import & Platform Integration

| Feature | Planned | Backend | UI | Status | Notes |
|---------|---------|---------|----|----|-------|
| Import tool | Yes | Yes - ImportSchemaCommand | No | **PARTIAL** | **Backend complete, NO UI** |
| Compatibility check (format version) | Yes | Yes - SchemaImportValidationService | No | **PARTIAL** | |
| Compatibility check (semantic version) | Yes | Yes - SchemaComparisonService | No | **PARTIAL** | |
| Platform version minimum | Yes | Partial | No | **PARTIAL** | |
| Import success feedback | Yes | Yes - ImportResult | No | **PARTIAL** | Backend returns warnings |
| Import failure feedback | Yes | Yes - ImportResult with errors | No | **PARTIAL** | |

---

## VALIDATION RULE SUPPORT MATRIX

| Validation Rule | Exists in Domain? | Exists in Application Logic? | Exposed in UI (Create)? | Exposed in UI (View)? |
|-----------------|-------------------|------------------------------|-------------------------|----------------------|
| **required** | Yes - RequiredConstraint | Yes - Export handles | No | Yes - READ-ONLY display |
| **min_value (number)** | Yes - MinValueConstraint | Yes - Export handles | No | Yes - READ-ONLY display |
| **max_value (number)** | Yes - MaxValueConstraint | Yes - Export handles | No | Yes - READ-ONLY display |
| **min_length (text)** | Yes - MinLengthConstraint | Yes - Export handles | No | Yes - READ-ONLY display |
| **max_length (text)** | Yes - MaxLengthConstraint | Yes - Export handles | No | Yes - READ-ONLY display |
| **min_date (date)** | Partial - Uses MinValueConstraint | Partial | No | Partial |
| **max_date (date)** | Partial - Uses MaxValueConstraint | Partial | No | Partial |
| **pattern / regex** | Yes - PatternConstraint | Yes - Export handles | No | Yes - READ-ONLY display |
| **allowed_values** | Yes - AllowedValuesConstraint | Yes - Export handles | No | Yes |
| **file_extension** | Yes - FileExtensionConstraint | Yes - Export handles | No | Yes |
| **max_file_size** | Yes - MaxFileSizeConstraint | Yes - Export handles | No | Yes |

**Summary**: All validation constraints exist in domain layer. All can be exported. **NONE can be created through Schema Designer UI**.

---

## IMPORT / EXPORT UX STATUS

| Component | Backend Status | UI Status | Overall Status |
|-----------|----------------|-----------|----------------|
| **ExportSchemaCommand** | COMPLETE | NO BUTTON | **Backend exists, UI MISSING** |
| **ImportSchemaCommand** | COMPLETE | NO DIALOG | **Backend exists, UI MISSING** |
| **Export button** | N/A | NOT IN schema_designer_view.py | **MISSING** |
| **Import button** | N/A | NOT IN schema_designer_view.py | **MISSING** |
| **Export file picker** | N/A | Missing | **MISSING** |
| **Import file picker** | N/A | Missing | **MISSING** |
| **Export warnings display** | Backend returns warnings | Missing | **MISSING** |
| **Import errors display** | Backend returns errors | Missing | **MISSING** |
| **Import success feedback** | Backend returns ImportResult | Missing | **MISSING** |

**Note**: `import_export_dialog.py` exists but is for **PROJECT DATA** interchange (ADR-039), NOT for Schema Designer schema export/import.

---

## FEATURES PRESENT IN BACKEND BUT NOT EXPOSED IN UI

| Feature | Backend Location | UI Exposure | Gap |
|---------|------------------|-------------|-----|
| **Export Schema** | ExportSchemaCommand | NONE | No button, no dialog |
| **Import Schema** | ImportSchemaCommand | NONE | No button, no dialog |
| **Delete Entity** | DeleteEntityCommand | NONE | Backend exists, no UI button |
| **Delete Field** | DeleteFieldCommand | NONE | Backend exists, no UI button |
| **Update Entity** | UpdateEntityCommand | NONE | Backend exists, no UI button |
| **Update Field** | UpdateFieldCommand | NONE | Backend exists, no UI button |
| **Add Field Constraint** | AddFieldConstraintCommand | NONE | Backend exists, no UI |
| **Update Field Option** | UpdateFieldOptionCommand | NONE | Backend exists |
| **Reorder Field Options** | ReorderFieldOptionsCommand | NONE | Backend exists |
| **Schema Comparison** | SchemaComparisonService | NONE | For import validation, not exposed |
| **Validation Rules** | READ-ONLY in UI | CREATE/EDIT missing | Can view but not create |

---

## FEATURES NOT STARTED AT ALL

| Feature | Phase | Domain | Application | Infrastructure | UI |
|---------|-------|--------|-------------|----------------|----|-
| **OutputMapping entity** | 2.3 | No | No | No | No |
| **Formula editor UI** | 2.2 | Partial (Property) | No Commands | No | No |
| **Control rule editor UI** | 2.2 | Yes (Entity) | No Schema commands | No | No |
| **Cardinality selection** | 2.1 | No | No | No | No |
| **Cascade behavior options** | 2.1 | No | No | No | No |
| **Capability declarations** | 3 | No | No | No | No |
| **Template reference guide** | 2.3 | No | No | No | No |

---

## FINAL COMPLETENESS MATRIX

| Feature | Planned Phase | Backend | UI | Status | Notes |
|---------|--------------|---------|----|----|-------|
| EntityDefinition CRUD | 1-2 | Yes | Partial - CREATE only | **PARTIAL** | No edit/delete UI |
| FieldDefinition CRUD | 2 | Yes | Partial - CREATE only | **PARTIAL** | No edit/delete UI |
| RelationshipDefinition | 2.1, 6A/6B | Yes | Yes - ADD-ONLY | **IMPLEMENTED** | Per ADR-022 |
| ValidationRule | 2 | Yes (as constraints) | No | **PARTIAL** | View only, no create |
| FormulaDefinition | 2.2 | Partial | No | **NOT STARTED** | |
| ControlRule | 2.2 | Yes (Domain) | No | **NOT STARTED** | |
| OutputMapping | 2.3 | No | No | **NOT STARTED** | |
| Schema Export | 2-3 | Yes | No | **PARTIAL** | No UI |
| Schema Import | 4 | Yes | No | **PARTIAL** | No UI |
| Schema Comparison | 3 | Yes | No | **PARTIAL** | |
| Continuous Validation | 3 | Partial | No | **NOT STARTED** | |
| UX Polish (Phase 5) | 5 | N/A | Yes | **IMPLEMENTED** | Welcome, help, unsaved warning |

---

## TEST COVERAGE STATUS

| Component | Tests Exist? | Location |
|-----------|--------------|----------|
| SchemaDesignerViewModel | Partial - Relationships only | tests/unit/presentation/viewmodels/test_schema_designer_viewmodel_relationships.py |
| SchemaDesignerView | No | None found |
| CreateEntityCommand | No | None found |
| AddFieldCommand | No | None found |
| ExportSchemaCommand | Unknown | Need to verify |
| ImportSchemaCommand | Unknown | Need to verify |
| SqliteSchemaRepository | Unknown | Need to verify |

---

## NEXT STEP READINESS

**Status**: :warning: **USABLE FOR BASIC SCHEMAS ONLY**

### What Works:
- Create entities
- Add fields to entities (all 12 field types)
- Create relationships (ADD-ONLY)
- View validation rules (read-only)
- Backend export command (programmatic use)
- Backend import command (programmatic use)

### What Does NOT Work for End Users:
- Cannot export schema from UI (must call command programmatically)
- Cannot import schema from UI
- Cannot edit existing entities/fields
- Cannot delete entities/fields
- Cannot create validation rules through UI
- Cannot edit formulas
- Cannot create control rules
- No output mappings

### Recommended Priority for Phase 2 Completion:
1. Add Export button + dialog to Schema Designer UI
2. Add Import button + dialog to Schema Designer UI
3. Add Edit/Delete buttons for entities and fields
4. Add validation rule creation UI

---

## KEY FILE REFERENCES

### Domain Layer
- `src/doc_helper/domain/schema/entity_definition.py` - EntityDefinition aggregate
- `src/doc_helper/domain/schema/field_definition.py` - FieldDefinition value object
- `src/doc_helper/domain/schema/relationship_definition.py` - RelationshipDefinition (ADR-022)
- `src/doc_helper/domain/validation/constraints.py` - All validation constraints

### Application Layer
- `src/doc_helper/application/commands/schema/export_schema_command.py` - Export logic
- `src/doc_helper/application/commands/schema/import_schema_command.py` - Import logic
- `src/doc_helper/application/commands/schema/create_entity_command.py` - Entity creation
- `src/doc_helper/application/commands/schema/add_field_command.py` - Field creation
- `src/doc_helper/application/commands/schema/create_relationship_command.py` - Relationship creation

### Presentation Layer
- `src/doc_helper/presentation/views/schema_designer_view.py` - Main view
- `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py` - ViewModel
- `src/doc_helper/presentation/dialogs/add_entity_dialog.py` - Entity creation dialog
- `src/doc_helper/presentation/dialogs/add_field_dialog.py` - Field creation dialog
- `src/doc_helper/presentation/dialogs/add_relationship_dialog.py` - Relationship creation dialog

---

**Report Complete. No code written. No features proposed.**

# Schema Designer - Implementation Status & Gap Analysis

**Date:** 2026-01-24
**Status:** 85-90% Complete
**Critical Gap:** Field Option Management

---

## Executive Summary

The Schema Designer is **85-90% complete** with comprehensive functionality for managing entities, fields, constraints, relationships, control rules, and output mappings. All backend application layer use cases are implemented and tested. The UI integration is complete for all major features.

**Critical Gap:** Field option management (DROPDOWN/RADIO fields) - the commands exist but are not integrated into `SchemaUseCases` or the UI.

**Total Remaining Work:** ~20-30 days (3-4 weeks) to complete all identified gaps.

**Minimum Viable Completion:** 3-4 days to implement field option management would make the schema designer fully usable for all 12 field types.

---

## ✅ Implemented & Complete Features

### Backend (Application Layer - `SchemaUseCases`)

#### Entity Operations
- ✅ **Create entity** - `create_entity(entity_id, name_key, description_key, is_root_entity)`
- ✅ **Update entity metadata** - `update_entity(entity_id, name_key, description_key, is_root_entity, parent_entity_id)`
- ✅ **Delete entity** - `delete_entity(entity_id)` with dependency checking (TABLE fields, LOOKUP fields, child entities)
- ✅ **Get all entities** - `get_all_entities()` returns tuple of EntityDefinitionDTO

#### Field Operations
- ✅ **Add field** - `add_field(entity_id, field_id, field_type, label_key, help_text_key, required, default_value)`
  - Supports all 12 field types: TEXT, TEXTAREA, NUMBER, DATE, DROPDOWN, CHECKBOX, RADIO, CALCULATED, LOOKUP, FILE, IMAGE, TABLE
- ✅ **Update field metadata** - `update_field(entity_id, field_id, label_key, help_text_key, required, default_value, formula, lookup_entity_id, lookup_display_field, child_entity_id)`
- ✅ **Delete field** - `delete_field(entity_id, field_id)` with dependency checking
  - Checks for: formula dependencies, control rule references, LOOKUP display field references
- ✅ **Get fields for entity** - via `get_all_entities()` (fields included in EntityDefinitionDTO)

#### Constraint Operations
- ✅ **Add constraint** - `add_constraint(entity_id, field_id, constraint_type, value, severity, ...)`
  - Supports 9 constraint types:
    1. `REQUIRED` - Field value must not be empty
    2. `MIN_VALUE` - Numeric field minimum value
    3. `MAX_VALUE` - Numeric field maximum value
    4. `MIN_LENGTH` - Text field minimum length
    5. `MAX_LENGTH` - Text field maximum length
    6. `PATTERN` - Regex pattern validation (Phase SD-6)
    7. `ALLOWED_VALUES` - Whitelist of allowed values (Phase SD-6)
    8. `FILE_EXTENSION` - Allowed file extensions (Phase SD-6)
    9. `MAX_FILE_SIZE` - Maximum file size in bytes (Phase SD-6)
  - Supports 3 severity levels: ERROR (blocking), WARNING (non-blocking), INFO (informational)
- ✅ **List constraints for field** - `list_constraints_for_field(entity_id, field_id)` returns tuple of ConstraintExportDTO

#### Control Rule Operations (Phase F-10, F-12)
- ✅ **Add control rule** - `add_control_rule(entity_id, field_id, rule_type, formula_text)`
  - Supports 3 rule types: VISIBILITY, ENABLED, REQUIRED
  - Formula governance validation (F-6)
  - Boolean type enforcement (F-8)
  - Prevents duplicate rule types on same field
- ✅ **Update control rule** - `update_control_rule(entity_id, field_id, rule_type, formula_text)`
  - Re-validates with governance + boolean enforcement
  - Empty formula triggers deletion
- ✅ **Delete control rule** - `delete_control_rule(entity_id, field_id, rule_type)`
- ✅ **List control rules for field** - `list_control_rules_for_field(entity_id, field_id)` returns tuple of ControlRuleExportDTO

#### Output Mapping Operations (Phase F-12.5, F-13)
- ✅ **Add output mapping** - `add_output_mapping(entity_id, field_id, target, formula_text)`
  - Supports 3 target types: TEXT, NUMBER, BOOLEAN
  - Prevents duplicate target types on same field
- ✅ **Update output mapping** - `update_output_mapping(entity_id, field_id, target, formula_text)`
  - Validates non-empty formula
- ✅ **Delete output mapping** - `delete_output_mapping(entity_id, field_id, target)`
- ✅ **List output mappings for field** - `list_output_mappings_for_field(entity_id, field_id)` returns tuple of OutputMappingExportDTO

#### Relationship Operations (Phase 6B - ADR-022)
- ✅ **Create relationship** - `create_relationship(relationship_id, source_entity_id, target_entity_id, relationship_type, name_key, description_key, inverse_name_key)`
  - Supports 3 relationship types: CONTAINS, REFERENCES, ASSOCIATES
  - **ADD-ONLY semantics** (no update/delete per ADR-022)
- ✅ **Get all relationships** - `get_all_relationships()` returns tuple of RelationshipDTO

#### Import/Export Operations (Phase 7, SD-1)
- ✅ **Export schema** - `export_schema(schema_id, file_path, version)`
  - Exports entities, fields, constraints, control rules, output mappings, relationships to JSON
  - Returns export warnings (e.g., missing translations, orphaned references)
- ✅ **Import schema** - `import_schema(file_path, enforcement_policy, identical_action, force)`
  - Supports 3 enforcement policies: STRICT (block incompatible), WARN (allow with warnings), NONE (no checking)
  - Supports 2 identical actions: SKIP (do nothing), REPLACE (replace anyway)
  - Compatibility analysis (version checking, breaking changes detection)
  - Returns ImportResult with counts, warnings, errors

---

### Frontend (Presentation Layer)

#### Schema Designer UI (`schema_designer_view.py`)

**Phase 2: Entity & Field Display (COMPLETE)**
- ✅ READ-ONLY display of entities, fields, validation rules
- ✅ Entity list panel with selection
- ✅ Field list panel for selected entity
- ✅ Validation rules panel for selected field
- ✅ "Add Entity" button and dialog
- ✅ "Add Field" button and dialog

**Phase 5: UX Polish & Onboarding (COMPLETE)**
- ✅ Persistent header subtitle (dismissible per session)
- ✅ Empty state messaging for entity and field lists
- ✅ Tooltips for toolbar buttons
- ✅ First-launch welcome dialog (permanently dismissible)
- ✅ "What is this?" help access point
- ✅ Static help dialog
- ✅ Unsaved changes indicator (asterisk in title)
- ✅ Close warning for unsaved changes

**Phase 6B: Relationship UI (ADR-022) (COMPLETE)**
- ✅ Relationships panel showing entity relationships
- ✅ "Add Relationship" button and dialog
- ✅ ADD-ONLY semantics (no edit/delete)
- ✅ Clear messaging about immutability

**Phase 7: Export UI (COMPLETE)**
- ✅ "Export Schema" button in toolbar
- ✅ Export dialog with file picker
- ✅ Display export warnings

**Phase SD-1: Import UI (COMPLETE)**
- ✅ "Import Schema" button in toolbar
- ✅ Import dialog with file picker and options
- ✅ Enforcement policy selector (STRICT/WARN/NONE)
- ✅ Identical schema action selector (SKIP/REPLACE)
- ✅ Display compatibility analysis
- ✅ Display import warnings/errors

**Phase SD-2: Add Constraint UI (COMPLETE)**
- ✅ "Add Constraint" button in validation rules panel
- ✅ Add constraint dialog with type selector
- ✅ Support all 9 constraint types
- ✅ Severity selector (ERROR/WARNING/INFO)
- ✅ Refresh validation rules after adding

**Phase SD-3: Entity Edit/Delete UI (COMPLETE)**
- ✅ Edit button to update entity metadata
- ✅ Delete button with confirmation dialog
- ✅ Dependency warning before delete

**Phase SD-4: Field Edit/Delete UI (COMPLETE)**
- ✅ Edit button to update field metadata
- ✅ Delete button with confirmation dialog
- ✅ Dependency warning before delete (formulas, controls, lookup references)

**Phase F-1: Formula Editor UI (COMPLETE)**
- ✅ Formula Editor panel (5th panel)
- ✅ Live syntax validation
- ✅ Field reference validation against schema
- ✅ Inferred result type display
- ✅ Error/warning display
- ✅ NO formula execution (design-time only)

**Phase F-9: Control Rules Preview UI (COMPLETE)**
- ✅ Control Rules Preview panel (6th panel)
- ✅ Toggle preview mode ON/OFF
- ✅ Enter temporary field values for preview
- ✅ Define control rules (VISIBILITY, ENABLED, REQUIRED)
- ✅ Evaluate rules via use-cases
- ✅ Apply rule effects to UI only (no persistence)
- ✅ Display blocked rules with reasons
- ✅ NO schema mutation

**Phase F-12: Control Rules UI (Persisted) (COMPLETE)**
- ✅ Control Rules section in validation panel
- ✅ Add/Edit/Delete persisted control rules
- ✅ Display rule type, target field, formula
- ✅ Route all operations through SchemaDesignerViewModel

**Phase F-13: Output Mapping Formula UI (Persisted) (COMPLETE)**
- ✅ Output Mappings section in validation panel
- ✅ Add/Edit/Delete persisted output mappings
- ✅ Display target type (TEXT/NUMBER/BOOLEAN), formula
- ✅ Route all operations through SchemaDesignerViewModel

#### Schema Designer ViewModel (`schema_designer_viewmodel.py`)
- ✅ All phases implemented matching view
- ✅ **Rule 0 compliant** - ONLY uses SchemaUseCases (no command/query/repository reach-through)
- ✅ Entity/field/constraint/relationship/control rule/output mapping operations
- ✅ Import/export orchestration
- ✅ Formula validation integration
- ✅ Control rule preview integration

---

### Testing Coverage

**Unit Tests:**
- ✅ **169 command tests** covering all schema commands
  - Entity: Create, Update, Delete
  - Field: Add, Update, Delete, AddOption, UpdateOption, ReorderOptions
  - Constraint: AddConstraint
  - Relationship: CreateRelationship
  - Import/Export: ExportSchema, ImportSchema
- ✅ **49 SchemaUseCases tests** covering:
  - Entity CRUD operations
  - Field CRUD operations
  - Constraint operations (add, list)
  - Output mapping CRUD operations (add, update, delete, list)
- ✅ **Integration tests** for import/export workflows

**Test Results:**
- All tests passing (116+ runtime tests + 169 schema command tests)
- 100% success rate
- No regressions

---

## ❌ Missing Features & Gaps

### 1. Field Option Management (CRITICAL GAP) 🔴

**Status:** Commands exist but NOT integrated into SchemaUseCases or UI

**Existing Commands:**
- ✅ `AddFieldOptionCommand` - exists, tested
- ✅ `UpdateFieldOptionCommand` - exists, tested
- ✅ `ReorderFieldOptionsCommand` - exists, tested
- ❌ `DeleteFieldOptionCommand` - **DOES NOT EXIST**

**Missing in SchemaUseCases (0/5 methods implemented):**
- ❌ `add_field_option(entity_id, field_id, option_id, label_key, value, order)` - NOT IMPLEMENTED
- ❌ `update_field_option(entity_id, field_id, option_id, label_key, value)` - NOT IMPLEMENTED
- ❌ `delete_field_option(entity_id, field_id, option_id)` - NOT IMPLEMENTED
- ❌ `reorder_field_options(entity_id, field_id, ordered_option_ids)` - NOT IMPLEMENTED
- ❌ `list_field_options(entity_id, field_id)` - NOT IMPLEMENTED

**Missing in UI:**
- ❌ Field option management panel/dialog
- ❌ Add/Edit/Delete option buttons
- ❌ Drag-to-reorder options

**Impact:**
- Cannot manage DROPDOWN/RADIO field options through schema designer
- Users must manually edit database or use legacy tools
- Makes DROPDOWN/RADIO fields unusable in schema designer

**Required Work:**
1. Create `DeleteFieldOptionCommand` (~1 day)
   - Add field option existence check
   - Delete from entity.fields[field_id].options
   - Save entity via repository
   - Tests
2. Add 5 methods to `SchemaUseCases` (~1 day)
   - Implement all CRUD + reorder operations
   - Route to appropriate commands
   - Return OperationResult with unwrapped domain IDs
   - Tests
3. Update `SchemaDesignerViewModel` (~0.5 day)
   - Add field option methods
   - Expose to UI layer
   - Handle option list state
4. Add field option management UI (~1.5 days)
   - Option list panel (similar to constraint list)
   - Add/Edit/Delete option dialogs
   - Drag-to-reorder functionality
   - Integration with field selection
5. Testing (~0.5 day)
   - UI smoke tests
   - Integration tests for option workflows

**Total Estimate:** 3-4 days

---

### 2. Constraint Management (MEDIUM GAP) 🟡

**Current State:**
- ✅ Can ADD constraints via `add_constraint()`
- ❌ Cannot UPDATE constraints (must delete + re-add)
- ❌ Cannot DELETE constraints

**Missing Commands:**
- ❌ `DeleteConstraintCommand` - **DOES NOT EXIST**
- ❌ `UpdateConstraintCommand` - **DOES NOT EXIST**

**Missing in SchemaUseCases:**
- ❌ `delete_constraint(entity_id, field_id, constraint_index_or_type)`
- ❌ `update_constraint(entity_id, field_id, constraint_index_or_type, new_constraint)`

**Impact:**
- Cannot remove validation constraints once added
- Cannot modify constraint parameters (e.g., change MIN_VALUE from 5 to 10)
- Must delete entire field and recreate to fix constraint mistakes

**Required Work:**
1. Create `DeleteConstraintCommand` (~1 day)
   - Identify constraint by type or index
   - Remove from entity.fields[field_id].constraints
   - Save entity via repository
   - Tests
2. Create `UpdateConstraintCommand` (~1 day)
   - Alternative: use delete + add pattern
   - Replace constraint at index
   - Save entity via repository
   - Tests
3. Add methods to `SchemaUseCases` (~0.5 day)
   - `delete_constraint()` method
   - `update_constraint()` method (optional)
   - Tests
4. Add Edit/Delete buttons to constraint list UI (~0.5 day)
   - Edit button opens constraint dialog with current values
   - Delete button with confirmation
   - Refresh constraint list after operations
5. Testing (~0.5 day)
   - Command tests
   - UI integration tests

**Total Estimate:** 2-3 days

---

### 3. Relationship Management (INTENTIONAL LIMITATION) ⚪

**Current State (ADR-022):**
- ✅ Can CREATE relationships
- ❌ Cannot UPDATE relationships (immutable by design)
- ❌ Cannot DELETE relationships (ADD-ONLY semantics)

**Reason:**
- ADR-022 specifies ADD-ONLY semantics for Phase 6B to avoid cascade complexity
- Deleting relationships would require:
  - Cascade delete logic for dependent TABLE/LOOKUP fields
  - Relationship dependency analysis
  - Breaking change detection

**Future Work (if needed):**
- Would require careful design of cascade behavior
- Would need relationship dependency analyzer
- Deferred to future phase (not blocking MVP)

**Estimate:** 5-7 days (requires careful design)

---

### 4. Translation Key Management (MAJOR GAP) 🟠

**Current State:**
- ✅ Schema uses translation keys for all labels/descriptions
- ✅ Translation keys follow pattern: `entity.<entity_id>.<field>`, `field.<entity_id>.<field_id>`
- ❌ No UI to create/edit/delete translation entries
- ❌ No API in SchemaUseCases for translation management
- ❌ Translation files (`translations/en.json`, `translations/ar.json`) edited manually

**Impact:**
- Schema designer creates entities/fields with translation keys (`"entity.project.name"`), but user must manually edit JSON files to add actual translations
- No validation of translation key existence
- No way to see untranslated keys
- Breaks user workflow (schema designer → manual file edit → restart app)

**Required Work:**
1. Create `TranslationUseCases` (~2 days)
   - Separate from SchemaUseCases (different bounded context)
   - Commands: AddTranslation, UpdateTranslation, DeleteTranslation
   - Queries: GetTranslation, ListAllTranslations, FindMissingKeys
   - Repository: JSON file-based translation store
2. Translation editor UI (~2 days)
   - Translation list view (key, English value, Arabic value)
   - Add/Edit translation dialog
   - Delete translation with confirmation
   - Search/filter translations
3. Integration with schema designer (~1-2 days)
   - Inline translation editor when creating entity/field
   - "Edit Translation" button next to translation key fields
   - Preview translated label/description
   - Validation: warn if translation key not found
4. Schema diagnostics (~1 day)
   - List all used translation keys
   - Highlight missing translations
   - "Generate missing translations" helper
5. Testing (~1 day)
   - Translation CRUD tests
   - UI integration tests
   - Missing key detection tests

**Total Estimate:** 5-7 days

---

### 5. Schema-Wide Validation (MEDIUM GAP) 🟡

**Missing Diagnostics:**
- ❌ Orphaned field references (formula references deleted field)
- ❌ Circular dependency detection across entire schema
- ❌ Unused translation keys
- ❌ Missing translation keys
- ❌ Invalid lookup configurations (lookup_entity_id or lookup_display_field not found)
- ❌ Schema health check

**Impact:**
- Schema errors only discovered at runtime
- No way to validate entire schema before deployment
- Hard to identify broken references after refactoring

**Required Work:**
1. Create `ValidateSchemaCommand` (~2 days)
   - Schema-wide dependency graph analysis
   - Circular dependency detection
   - Orphaned reference detection
   - Translation key validation
   - Lookup configuration validation
2. Schema analysis service (~2 days)
   - Build dependency graph from all formulas/control rules
   - Detect cycles using topological sort
   - Find unused/missing translation keys
   - Validate lookup entity/field existence
3. Diagnostics panel UI (~1 day)
   - Show warnings/errors grouped by severity
   - Click to navigate to problem location
   - "Fix" actions for common issues (e.g., remove orphaned reference)
4. Testing (~1 day)
   - Schema validation tests
   - Circular dependency tests
   - Translation key tests

**Total Estimate:** 4-5 days

---

### 6. Field Type-Specific Configuration UI (LOW-MEDIUM GAP) 🟡

**CALCULATED Fields:**
- ✅ Formula editor exists (Phase F-1)
- ✅ Live validation
- ✅ Can bind formula via `update_field(formula=...)`

**LOOKUP Fields:**
- ✅ Backend exists (`update_field(lookup_entity_id=..., lookup_display_field=...)`)
- ❌ No dedicated lookup configuration dialog
- ❌ Must know field IDs, no entity/field picker
- ❌ Hard to configure without documentation

**TABLE Fields:**
- ✅ Backend exists (`update_field(child_entity_id=...)`)
- ❌ No dedicated child entity selector
- ❌ Must know entity ID

**FILE/IMAGE Fields:**
- ✅ Backend supports file extension and size constraints
- ❌ No dedicated file field configuration UI

**Impact:**
- LOOKUP/TABLE fields are hard to configure
- Users need to know internal entity/field IDs
- Error-prone (typos in IDs)

**Required Work:**
1. Enhanced field edit dialog with type-specific tabs (~2 days)
   - General tab (label, help text, required, default)
   - Type-specific tab (formula, lookup, table, file config)
   - Conditional display based on field type
2. Entity picker component (~1 day)
   - Dropdown showing all entities
   - Used for LOOKUP (lookup_entity_id) and TABLE (child_entity_id)
3. Field picker component (~1 day)
   - Dropdown showing fields from selected entity
   - Used for LOOKUP (lookup_display_field)
4. Preview of configured lookups (~0.5 day)
   - Show "Lookup: Entity.Field" in field list
5. Testing (~0.5 day)
   - UI smoke tests
   - Configuration save/load tests

**Total Estimate:** 3-4 days

---

### 7. Testing Gaps (ONGOING) 🟡

**Unit Tests:**
- ✅ All commands have tests (169 tests)
- ✅ SchemaUseCases has tests (49 tests)
- ❌ No tests for missing operations (field options, constraint delete)

**Integration Tests:**
- ✅ Import/export integration tests
- ❌ No end-to-end schema designer workflow tests
- ❌ No UI tests for schema designer view

**Required Work:**
1. Tests for missing features (~ongoing with implementation)
   - Field option CRUD tests (when implemented)
   - Constraint delete/update tests (when implemented)
   - Translation management tests (when implemented)
2. E2E workflow tests (~2 days)
   - Create entity → add fields → add constraints → add control rules → export
   - Import schema → modify → export again
   - Create DROPDOWN field → add options → reorder → delete option
3. UI smoke tests (~1 day)
   - PyQt6 UI tests for schema designer view
   - Button click tests
   - Dialog open/close tests

**Total Estimate:** 2-3 days (ongoing)

---

## Prioritized Work Plan

### Priority 1: Critical (Blocks Core Functionality) 🔴

#### 1. Field Option Management
**Why:** Cannot use DROPDOWN/RADIO fields properly without this

**Tasks:**
- Create `DeleteFieldOptionCommand`
- Add 5 methods to `SchemaUseCases` (add, update, delete, reorder, list)
- Update `SchemaDesignerViewModel` with option operations
- Add UI panel for option management (list, add, edit, delete, reorder)
- Tests (command, use case, UI integration)

**Estimate:** 3-4 days

**Dependencies:** None

---

### Priority 2: High (Improves Usability) 🟠

#### 2. Constraint Delete/Update
**Why:** Cannot fix mistakes in constraints, must delete entire field

**Tasks:**
- Create `DeleteConstraintCommand`
- Create `UpdateConstraintCommand` (or use delete+add pattern)
- Add methods to `SchemaUseCases` (delete_constraint, update_constraint)
- Add Edit/Delete buttons to constraint list UI
- Tests

**Estimate:** 2-3 days

**Dependencies:** None

#### 3. Field Type Configuration UI
**Why:** Hard to configure LOOKUP/TABLE fields without pickers

**Tasks:**
- Enhanced field edit dialog with type-specific tabs
- Entity picker component
- Field picker component
- Preview of configured lookups

**Estimate:** 3-4 days

**Dependencies:** None

---

### Priority 3: Medium (Nice to Have) 🟡

#### 4. Translation Management
**Why:** Currently requires manual JSON editing, breaks workflow

**Tasks:**
- Create `TranslationUseCases` with commands/queries
- Translation editor UI (list, add, edit, delete)
- Integration with schema designer (inline editor)
- Schema diagnostics (missing keys)
- Tests

**Estimate:** 5-7 days

**Dependencies:** None

#### 5. Schema-Wide Validation
**Why:** Catch errors before runtime, validate entire schema

**Tasks:**
- Create `ValidateSchemaCommand`
- Schema analysis service (dependency graph, cycle detection)
- Diagnostics panel UI (warnings/errors with navigation)
- Tests

**Estimate:** 4-5 days

**Dependencies:** None

---

### Priority 4: Low (Future Enhancement) ⚪

#### 6. Relationship Edit/Delete
**Why:** Currently ADD-ONLY per ADR-022, but may be needed in future

**Tasks:**
- Cascade delete logic design
- Dependency analysis for relationships
- Update/delete relationship commands
- Update SchemaUseCases
- Update UI
- Tests

**Estimate:** 5-7 days (requires careful design)

**Dependencies:** None (deferred by design)

---

## Implementation Timeline

### Week 1: Critical Features
- **Days 1-4:** Field option management (CRITICAL)
  - DeleteFieldOptionCommand + SchemaUseCases methods + UI
  - **Deliverable:** Fully functional DROPDOWN/RADIO field support

### Week 2: High Priority Features
- **Days 5-7:** Constraint delete/update
  - DeleteConstraintCommand, UpdateConstraintCommand, UI updates
  - **Deliverable:** Edit/delete constraints in UI
- **Days 8-9:** Field type configuration UI
  - Enhanced field edit dialog, entity/field pickers
  - **Deliverable:** Easy LOOKUP/TABLE configuration

### Week 3-4: Medium Priority Features
- **Days 10-16:** Translation management
  - TranslationUseCases, translation editor UI, schema integration
  - **Deliverable:** Manage translations within app
- **Days 17-21:** Schema-wide validation
  - ValidateSchemaCommand, diagnostics panel
  - **Deliverable:** Schema health checks

### Optional: Low Priority
- **Days 22-28:** Relationship edit/delete (if needed)
  - Cascade logic, dependency analysis
  - **Deliverable:** Full relationship management

**Total:** ~20-30 days (4-6 weeks) for complete implementation

---

## Summary

### Current State
- **Schema Designer:** 85-90% complete
- **Backend:** Fully functional for entities, fields, constraints, control rules, output mappings, relationships, import/export
- **Frontend:** Complete UI for all implemented backend features
- **Testing:** 169 command tests + 49 use case tests, all passing

### Critical Path to Completion
1. **Week 1:** Field option management → Makes schema designer fully usable for all 12 field types
2. **Week 2:** Constraint management + field type UI → Improves usability significantly
3. **Weeks 3-4:** Translation management + schema validation → Polish and production-readiness

### Minimum Viable Schema Designer
**3-4 days** of work on field option management would make the schema designer fully usable for all 12 field types. This is the critical blocker.

### Recommended Next Steps
1. **Immediate:** Implement field option management (Priority 1, 3-4 days)
2. **Short-term:** Constraint delete/update + field type UI (Priority 2, 5-7 days)
3. **Medium-term:** Translation management + schema validation (Priority 3, 9-12 days)
4. **Long-term:** Relationship edit/delete if needed (Priority 4, 5-7 days)

---

## Files Reference

### Backend
- **Use Cases:** `src/doc_helper/application/usecases/schema_usecases.py` (1510 lines)
- **Commands:** `src/doc_helper/application/commands/schema/*.py`
- **DTOs:** `src/doc_helper/application/dto/schema_dto.py`, `export_dto.py`, `import_dto.py`

### Frontend
- **View:** `src/doc_helper/presentation/views/schema_designer_view.py`
- **ViewModel:** `src/doc_helper/presentation/viewmodels/schema_designer_viewmodel.py`

### Tests
- **Command Tests:** `tests/unit/application/commands/schema/*.py` (169 tests)
- **Use Case Tests:** `tests/unit/application/usecases/test_schema_usecases.py` (49 tests)
- **Integration Tests:** `tests/integration/application/commands/schema/*.py`

---

**Document Version:** 1.0
**Last Updated:** 2026-01-24
**Next Review:** After field option management implementation

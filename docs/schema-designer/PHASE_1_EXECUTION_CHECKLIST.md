# Schema Designer Phase 1 Execution Checklist

**Status**: Ready for execution

**Date**: 2026-01-22

**Related Documents**:
- [Schema Designer Implementation Plan](IMPLEMENTATION_PLAN.md)
- [ADR-V2-SCHEMA-DESIGNER](../../adrs/ADR-V2-SCHEMA-DESIGNER.md)

---

## Phase 1 Objectives

**Goal**: Build the meta-schema foundation that allows Schema Designer to describe itself.

**What Phase 1 Delivers**:
- Schema Designer can define entities (EntityDefinition)
- Schema Designer can define fields within entities (FieldDefinition)
- Schema Designer can define basic validation rules (ValidationRule)
- Schema Designer can define relationships (RelationshipDefinition) *in the meta-schema only* - NO UI

**What Phase 1 Does NOT Deliver**:
- No user-facing schema editor UI (internal rendering for validation/testing is allowed)
- No export functionality
- No import functionality
- No formulas, controls, output mappings
- **NO relationships UI** (RelationshipDefinition exists in meta-schema but UI is Phase 2.1)

---

## Build Checklist (Ordered Steps)

### Step 1: Meta-Schema Storage Layer

**Task**: Establish persistent storage for schema definition concepts.

**What to Build**:
- [ ] **EntityDefinition storage**: Persistent storage that enforces entity name uniqueness within a schema and supports entity type classification (singleton vs collection)

- [ ] **FieldDefinition storage**: Persistent storage that enforces field name uniqueness within an entity, tracks field type, and maintains field ordering

- [ ] **RelationshipDefinition storage**: Persistent storage that captures connections between entities with cardinality constraints

- [ ] **ValidationRule storage**: Persistent storage that associates constraint definitions with specific fields

**Guarantees Required**:
- Entity names are unique within a schema
- Field names are unique within an entity
- Relationships reference valid entities
- Validation rules reference valid fields
- Display ordering is preserved

**Do NOT Build**:
- ❌ NO formula storage (Phase 2.2)
- ❌ NO control rule storage (Phase 2.2)
- ❌ NO output mapping storage (Phase 2.3)

---

### Step 2: Meta-Schema Seed Data

**Task**: Populate the meta-schema with minimal seed data representing the four core entities.

**What to Build**:
- [ ] **EntityDefinition entity**: A schema entity describing what an entity is (name, type classification, description, ordering)

- [ ] **FieldDefinition entity**: A schema entity describing what a field is (name, parent entity reference, type, description, required flag, ordering)

- [ ] **ValidationRule entity**: A schema entity describing what a validation rule is (target field reference, constraint type, constraint parameters)

- [ ] **RelationshipDefinition entity**: A schema entity describing what a relationship is (source entity, target entity, cardinality, cascade behavior)

**Guarantees Required**:
- All four entities exist and are accessible
- EntityDefinition describes entities with appropriate field types
- FieldDefinition describes fields with appropriate field types
- ValidationRule describes validation constraints with appropriate field types
- RelationshipDefinition describes relationships with appropriate field types
- Each entity has a minimal set of fields sufficient to be useful

**Do NOT Build**:
- ❌ NO FormulaDefinition entity (Phase 2.2)
- ❌ NO ControlRule entity (Phase 2.2)
- ❌ NO OutputMapping entity (Phase 2.3)

---

### Step 3: Field Type and Constraint Type Constraints

**Task**: Define and enforce the allowed field types and constraint types.

**What to Build**:
- [ ] **Field type constraints**: A platform-defined constrained set of field types, consistently enforced

- [ ] **Constraint type constraints**: A platform-defined constrained set of constraint types for validation rules

- [ ] **Entity type constraints**: A platform-defined constrained set of entity type classifications

- [ ] **Cardinality constraints**: A platform-defined constrained set of relationship cardinality options

**Guarantees Required**:
- Field type values are drawn from the allowed set
- Constraint type values are drawn from the allowed set
- Entity type values are drawn from the allowed set
- Cardinality values are drawn from the allowed set
- Invalid type values are rejected

**Do NOT Build**:
- ❌ NO advanced constraint types (Phase 2.1+)
- ❌ NO formula function types (Phase 2.2)
- ❌ NO control effect types (Phase 2.2)

---

### Step 4: Validation Logic

**Task**: Implement validation rules for the meta-schema entities.

**What to Build**:
- [ ] **Entity name validation**:
  - Must be unique within schema
  - Must follow platform naming conventions
  - Must be within acceptable length bounds

- [ ] **Field name validation**:
  - Must be unique within entity
  - Must follow platform naming conventions
  - Must be within acceptable length bounds

- [ ] **Field type validation**:
  - Must be one of the allowed field types
  - Must remain stable once data exists (future consideration)

- [ ] **Constraint type applicability validation**:
  - Constraint type must be applicable to field's field type (e.g., numeric constraints only apply to numeric fields)

- [ ] **Relationship validation**:
  - Source and target entities must exist and be valid

**Guarantees Required**:
- Invalid entity names are rejected
- Invalid field names are rejected
- Invalid field types are rejected
- Inapplicable constraint types are rejected
- Invalid relationships are rejected

**Do NOT Build**:
- ❌ NO circular dependency detection for formulas (Phase 2.2)
- ❌ NO control chain depth validation (Phase 2.2)
- ❌ NO cascade rule safety checks (Phase 2.1)

---

### Step 5: AppType Registration

**Task**: Establish Schema Designer as a registered AppType within the platform.

**What to Build**:
- [ ] **Schema Designer registration**: Register Schema Designer as an available AppType in the platform registry

- [ ] **AppType metadata**: Provide required AppType metadata

**Guarantees Required**:
- Schema Designer appears in available AppTypes list
- Platform recognizes "schema_designer" as a valid AppType identifier
- Projects can be created with app_type_id="schema_designer"

**Do NOT Build**:
- ❌ NO document templates (Schema Designer doesn't generate documents in Phase 1)
- ❌ NO custom transformers (Phase 2.3+)

---

### Step 6: Platform Integration Verification

**Task**: Verify Schema Designer integrates correctly with platform lifecycle operations.

**What to Build**:
- [ ] **Project creation**: Verify new projects can be created with app_type_id="schema_designer"

- [ ] **Project persistence**: Verify Schema Designer projects can be opened, modified, and saved

- [ ] **Dynamic form rendering**: Verify all four meta-schema entities render correctly in dynamic forms

**Guarantees Required**:
- Can create new Schema Designer project
- Can open existing Schema Designer project
- Can save Schema Designer project
- Can navigate between EntityDefinition, FieldDefinition, ValidationRule, RelationshipDefinition forms

**Do NOT Build**:
- ❌ NO AppType selection UI (separate platform concern)

---

## Validation Checklist

### Meta-Schema Completeness

- [ ] **EntityDefinition entity exists** with fields describing entity properties
- [ ] **FieldDefinition entity exists** with fields describing field properties
- [ ] **ValidationRule entity exists** with fields describing validation constraints
- [ ] **RelationshipDefinition entity exists** with fields describing entity relationships
- [ ] All four entities use appropriate field types for their data
- [ ] All required fields are marked as required
- [ ] Display ordering is defined for all fields

### Data Integrity

- [ ] Entity names are enforced as unique within schema
- [ ] Field names are enforced as unique within entity
- [ ] Field types are validated against allowed set
- [ ] Constraint types are validated against allowed set
- [ ] Foreign references work correctly (field → entity, validation_rule → field, relationship → entities)

### Platform Integration

- [ ] Schema Designer is registered in AppType registry
- [ ] Can create new project with app_type_id="schema_designer"
- [ ] Can open Schema Designer project
- [ ] Can save Schema Designer project
- [ ] Dynamic form rendering works for all four entities

### Negative Testing

- [ ] Cannot create entity with duplicate name
- [ ] Cannot create field with duplicate name within entity
- [ ] Cannot create field with invalid field_type
- [ ] Cannot create validation_rule with invalid constraint_type
- [ ] Cannot create validation_rule referencing non-existent field
- [ ] Cannot create relationship with non-existent source/target entity

---

## "Do NOT Build" List (Forbidden in Phase 1)

**These features are EXPLICITLY forbidden in Phase 1. Building them will violate the phase scope.**

### Forbidden Entities
- ❌ FormulaDefinition entity (Phase 2.2)
- ❌ ControlRule entity (Phase 2.2)
- ❌ OutputMapping entity (Phase 2.3)

### Forbidden UI Features
- ❌ User-facing schema editor UI (Phase 2)
- ❌ Relationships UI (Phase 2.1 - entity exists in meta-schema but NO UI)
- ❌ Export button/dialog (Phase 2)
- ❌ Import functionality (Phase 4)
- ❌ Template selection UI (Phase 2.3)
- ❌ Validation severity indicators (ERROR/WARNING/INFO) (Phase 3)

**Note**: Internal form rendering for validation and testing purposes is allowed in Phase 1.

### Forbidden Validation Features
- ❌ Circular dependency detection for formulas (Phase 2.2)
- ❌ Control chain depth validation (Phase 2.2)
- ❌ Cascade rule safety checks (Phase 2.1)
- ❌ Advanced constraint types beyond the platform-defined set (Phase 2.1+)

### Forbidden Export/Import Features
- ❌ Export schema to external format (Phase 2+)
- ❌ Import schema from external format (Phase 4)
- ❌ Export format version metadata (Phase 3)
- ❌ Schema semantic version metadata (Phase 3)
- ❌ Compatibility checks (Phase 4)

### Forbidden Infrastructure
- ❌ Export tooling (Phase 2+)
- ❌ Import tooling (Phase 4)
- ❌ Validation error/warning/info severity system (Phase 3)
- ❌ Capability registry (Phase 3)

---

## Phase 1 Completion Criteria

Phase 1 is complete when ALL of the following are true:

### Functional Criteria
1. ✅ Schema Designer AppType exists and is registered
2. ✅ Can create new Schema Designer project
3. ✅ Can open/save Schema Designer project
4. ✅ Meta-schema has 4 entities: EntityDefinition, FieldDefinition, ValidationRule, RelationshipDefinition
5. ✅ All 4 entities have appropriate fields with appropriate types
6. ✅ Platform-defined field types are available and enforced
7. ✅ Platform-defined constraint types are available and enforced

### Validation Criteria
8. ✅ Entity names validated as unique
9. ✅ Field names validated as unique within entity
10. ✅ Field types validated against allowed set
11. ✅ Constraint types validated against allowed set
12. ✅ Referential integrity enforced (fields reference entities, rules reference fields, relationships reference entities)

### Export Criteria
13. ✅ **NO export functionality** (Phase 1 does not include export)

### Architecture Criteria
14. ✅ Schema Designer respects AppType isolation (no privileged access)
15. ✅ Schema Designer uses same repository interfaces as other AppTypes
16. ✅ Meta-schema stored using platform-standard persistence mechanisms

### Testing Criteria
17. ✅ Unit tests for meta-schema validation
18. ✅ Integration tests for project creation/open/save
19. ✅ Negative tests for validation rules

### Documentation Criteria
20. ✅ Phase 1 completion documented
21. ✅ Meta-schema structure documented
22. ✅ Known limitations documented (no export, no user-facing editor UI, no relationships UI)

---

## Success Indicators

**How to know Phase 1 succeeded:**

1. **Can create a Schema Designer project**:
   - Create new project with app_type_id="schema_designer"
   - Project opens successfully

2. **Can define an entity**:
   - Navigate to EntityDefinition form
   - Provide entity name, type, and description
   - Save successfully

3. **Can define a field**:
   - Navigate to FieldDefinition form
   - Provide field name, parent entity reference, field type, and required flag
   - Save successfully

4. **Can define a validation rule**:
   - Navigate to ValidationRule form
   - Provide field reference and constraint type
   - Save successfully

5. **Can define a relationship**:
   - RelationshipDefinition entity exists in meta-schema
   - Can store relationship data (source entity, target entity, cardinality)
   - Internal rendering allowed for validation/testing; no user-facing relationships UI (deferred to Phase 2.1)

6. **Validation works**:
   - Attempt to create entity with duplicate name → Validation error
   - Attempt to create field with invalid field_type → Validation error
   - Validation errors are clear and actionable

7. **AppType isolation respected**:
   - Schema Designer has no privileged access to other AppTypes
   - Schema Designer cannot directly modify other AppTypes
   - Schema Designer uses standard platform interfaces

---

## Risks and Mitigations

### Risk 1: Self-Referential Meta-Schema Complexity
**Risk**: EntityDefinition entity contains fields that are themselves defined by FieldDefinition entities. Circular bootstrap problem.

**Mitigation**:
- Accept that Schema Designer's own meta-schema is manually seeded (not created via UI)
- Phase 1 focus: Prove the meta-schema is *sufficient*, not that it's self-hosting
- Self-hosting (using Schema Designer to edit itself) is a v3+ goal, not v1/v2

### Risk 2: Scope Creep
**Risk**: Developer adds "just one more feature" (e.g., export button) because it seems easy.

**Mitigation**:
- **STOP**: Refer to "Do NOT Build" list
- Phase 1 is about proving the meta-schema is correct, NOT about building a usable tool
- Export is Phase 2+, formulas are Phase 2.2, import is Phase 4

### Risk 3: Validation Logic Gaps
**Risk**: Miss a validation rule (e.g., allow duplicate field names).

**Mitigation**:
- Write negative tests FIRST (test that invalid data is rejected)
- Review validation rules against platform contracts
- Test with real-world schema examples

### Risk 4: RelationshipDefinition Confusion
**Risk**: Developer tries to build relationships UI in Phase 1 because entity exists.

**Mitigation**:
- **Phase 1 Note**: RelationshipDefinition exists in meta-schema from Phase 1, but UI support for creating relationships is deferred to Phase 2.1
- Phase 1 only proves relationship entity can be stored/retrieved
- Phase 2.1 adds UI and cascade validation

### Risk 5: Implementation Lock-In
**Risk**: Phase 1 documentation specifies implementation details that constrain future design.

**Mitigation**:
- Phase 1 checklist describes *what* must exist, not *how* it's implemented
- Storage mechanisms, file formats, and UI patterns are implementation choices
- Guarantees are specified, implementations are not

---

## Next Steps After Phase 1

Once Phase 1 is complete and validated:

1. **Review Phase 1 deliverables** with stakeholders
2. **Document meta-schema structure** for Phase 2 developers
3. **Create Phase 2 execution checklist** (Minimum Viable Schema Designer UI)
4. **Begin Phase 2 implementation**:
   - Build schema editor UI
   - Add simple entity/field creation forms
   - Add export functionality with basic validation

---

**End of Phase 1 Execution Checklist**

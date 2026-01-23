# ADR-022: Relationship Definitions in Schema-Driven Platform

**Status**: ACCEPTED
**Date**: 2026-01-23
**Accepted**: 2026-01-23
**Deciders**: Architecture Team
**Context**: Schema Designer Infrastructure

---

## 1. Decision Scope and Non-Goals

### In Scope

- Domain model for relationship definitions
- Persistence strategy for relationships
- Repository interface extensions
- Application-layer commands for relationship creation
- Integration with existing schema versioning
- Integration with existing import/export
- Migration strategy for schemas without relationships

### Non-Goals

- Relationship Editor UI (separate phase)
- Bidirectional relationship auto-generation
- Cascade delete behavior through relationships
- Runtime relationship traversal or query APIs
- Relationship-based validation rules
- Visual relationship diagrams or graph representations

---

## 2. Decision: Relationships as First-Class Domain Entities

### Decision

Relationships SHALL be modeled as **first-class domain entities**, not derived metadata.

### Rationale

| Option | Pros | Cons |
|--------|------|------|
| **First-class entity** | Explicit lifecycle, versionable, exportable, testable | Requires new domain entity, repository, commands |
| Derived metadata | Simpler, inferred from field references | Implicit, not versionable, cannot represent explicit semantics |
| Embedded in EntityDefinition | Co-located with entities | Violates single responsibility, complicates entity versioning |

First-class entity is chosen because:

1. **Explicit semantics**: Relationships carry meaning beyond field references (e.g., "Project contains Boreholes" vs "Borehole references Project")
2. **Independent lifecycle**: Relationships can be added without modifying entities
3. **Versionable**: Relationship changes are trackable schema changes
4. **Exportable**: Relationships must survive import/export cycles
5. **Testable**: Relationships can be validated in isolation

---

## 3. Relationship Immutability Rules

### Decision

Relationships SHALL follow **ADD-ONLY** semantics in the initial implementation.

### Rules

| Operation | Allowed | Rationale |
|-----------|---------|-----------|
| CREATE relationship | YES | Core functionality |
| READ relationships | YES | Core functionality |
| UPDATE relationship | NO | Prevents semantic drift, simplifies versioning |
| DELETE relationship | NO | Prevents orphaned references, maintains schema stability |

### Consequences

- To "change" a relationship, users must author a new schema definition using supported schema authoring mechanisms and import the revised schema
- This matches the existing field immutability pattern (fields cannot be deleted if referenced)
- Future phases MAY relax this constraint with proper dependency checking

### Justification

ADD-ONLY semantics align with:
- Schema versioning (changes are additive)
- Compatibility rules (existing schemas remain valid)
- Safety constraints (no accidental data model breakage)

---

## 4. Required Domain Entities and Fields

### RelationshipDefinition (Aggregate Root)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | RelationshipDefinitionId | YES | Strongly typed unique identifier |
| source_entity_id | EntityDefinitionId | YES | Entity where relationship originates |
| target_entity_id | EntityDefinitionId | YES | Entity where relationship points |
| relationship_type | RelationshipType | YES | Semantic type of relationship |
| name_key | TranslationKey | YES | Human-readable name (i18n) |
| description_key | TranslationKey | NO | Optional description (i18n) |
| inverse_name_key | TranslationKey | NO | Name when traversed in reverse (i18n) |

### RelationshipDefinitionId (Value Object)

- Strongly typed identifier following ADR-009
- Immutable
- String-based with validation (alphanumeric + underscore)

### RelationshipType (Enumeration)

| Value | Semantics |
|-------|-----------|
| CONTAINS | Parent-child containment (1:N) |
| REFERENCES | Loose reference (N:1) |
| ASSOCIATES | Peer association (N:M, logical only) |

**Note**: RelationshipType is **descriptive metadata only**. It does NOT imply runtime traversal, enforcement, cascade behavior, or any data-level operations. The system does not enforce cardinality or navigate relationships at runtime.

### Design Constraints

- RelationshipDefinition is an **aggregate root** (ADR-002)
- All fields are **immutable after creation** (ADR-010)
- IDs are **strongly typed** (ADR-009)
- Errors returned via **Result monad** (ADR-008)

---

## 5. Repository Responsibilities

### IRelationshipRepository Interface

| Method | Signature (Conceptual) | Description |
|--------|------------------------|-------------|
| get_by_id | (RelationshipDefinitionId) → Result[RelationshipDefinition, Error] | Retrieve single relationship |
| get_all | () → Result[Tuple[RelationshipDefinition], Error] | Retrieve all relationships |
| get_by_source_entity | (EntityDefinitionId) → Result[Tuple[RelationshipDefinition], Error] | Relationships originating from entity |
| get_by_target_entity | (EntityDefinitionId) → Result[Tuple[RelationshipDefinition], Error] | Relationships pointing to entity |
| exists | (RelationshipDefinitionId) → bool | Check existence |
| save | (RelationshipDefinition) → Result[None, Error] | Persist new relationship |

### Repository Constraints

- Interface defined in **domain layer** (dependency inversion)
- Implementation in **infrastructure layer**
- NO update method (ADD-ONLY semantics)
- NO delete method (ADD-ONLY semantics)
- Must validate entity references exist before save

### Validation Responsibilities

| Validation | Layer |
|------------|-------|
| ID format valid | Domain (value object) |
| Source entity exists | Repository (on save) |
| Target entity exists | Repository (on save) |
| Duplicate relationship check | Repository (on save) |
| Relationship type valid | Domain (enum) |

---

## 6. Application-Layer Commands Required

### CreateRelationshipCommand

| Parameter | Type | Required |
|-----------|------|----------|
| relationship_id | string | YES |
| source_entity_id | string | YES |
| target_entity_id | string | YES |
| relationship_type | string | YES |
| name_key | string | YES |
| description_key | string | NO |
| inverse_name_key | string | NO |

**Preconditions**:
- Source entity must exist
- Target entity must exist
- Relationship ID must be unique
- Relationship type must be valid

**Postconditions**:
- RelationshipDefinition persisted
- Schema marked as modified (dirty flag)

### GetRelationshipsQuery

| Parameter | Type | Required |
|-----------|------|----------|
| entity_id | string | NO |

**Behavior**:
- If entity_id provided: return relationships involving that entity
- If entity_id omitted: return all relationships

### Commands NOT Required (ADD-ONLY)

- UpdateRelationshipCommand
- DeleteRelationshipCommand

---

## 7. Impact on Schema Versioning and Compatibility

### Version Increment Rules

| Change | Version Impact |
|--------|----------------|
| Add new relationship | MINOR version increment |
| (Future) Modify relationship | MINOR version increment |
| (Future) Remove relationship | MAJOR version increment |

### Compatibility Matrix

| Change Type | Backward Compatible | Forward Compatible |
|-------------|---------------------|-------------------|
| Add relationship | YES | YES |
| (Future) Remove relationship | NO | YES |

### Integration with Existing Versioning

- RelationshipDefinition changes tracked in `SchemaChange` (existing)
- Schema compatibility checker must be extended to include relationships
- Version comparison must consider relationship additions

### Schema Fingerprint

- Relationships MUST be included in schema fingerprint calculation
- Adding a relationship changes the schema fingerprint
- Fingerprint used for compatibility checking

---

## 8. Impact on Import/Export

### Export Format Extension

Schema export (JSON) must include:

```
{
  "entities": [...],
  "fields": [...],
  "relationships": [
    {
      "id": "project_contains_boreholes",
      "source_entity_id": "project",
      "target_entity_id": "borehole",
      "relationship_type": "CONTAINS",
      "name_key": "relationship.project_boreholes",
      "description_key": null,
      "inverse_name_key": "relationship.borehole_project"
    }
  ],
  "version": "1.1.0"
}
```

### Import Behavior

| Scenario | Behavior |
|----------|----------|
| Import schema with relationships | Create all relationships |
| Import schema without relationships | No relationships created (valid) |
| Relationship references non-existent entity | Import FAILS with validation error |
| Duplicate relationship ID | Import FAILS with validation error |

### Export Command Changes

- `ExportSchemaCommand` must include relationships in output
- Relationships serialized after entities (dependency order)

### Import Command Changes

- `ImportSchemaCommand` must deserialize relationships
- Relationships validated after entities imported
- Atomic: all-or-nothing (existing behavior)

---

## 9. Migration Strategy for Existing Schemas

### Principle

Existing schemas without relationships remain **valid and unchanged**.

### Migration Rules

| Scenario | Behavior |
|----------|----------|
| Existing schema, no relationships | Valid, relationships array empty or absent |
| Existing schema, import with relationships | Relationships added, version incremented |
| New schema | May or may not have relationships |

### No Automatic Inference

- System SHALL NOT infer relationships from existing field references
- Relationships are explicit, user-defined
- LOOKUP and TABLE fields do NOT automatically create relationships

### Database Migration

- Add `relationships` table to persistence schema
- Existing databases: table created empty on first access
- No data migration required (ADD-ONLY)

### Persistence Schema Addition

| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY |
| source_entity_id | TEXT | NOT NULL, FK to entities |
| target_entity_id | TEXT | NOT NULL, FK to entities |
| relationship_type | TEXT | NOT NULL, CHECK constraint |
| name_key | TEXT | NOT NULL |
| description_key | TEXT | NULLABLE |
| inverse_name_key | TEXT | NULLABLE |

---

## 10. Consequences

### Positive

1. **Explicit data model**: Relationships are documented, versionable, exportable
2. **Clean Architecture alignment**: Follows existing patterns (aggregate root, repository, commands)
3. **Safe evolution**: ADD-ONLY prevents breaking changes
4. **Import/export integrity**: Relationships survive round-trips
5. **Testability**: Relationships can be unit tested in isolation
6. **i18n ready**: Name keys support translation

### Negative

1. **Implementation effort**: Requires domain entity, repository, command, persistence
2. **ADD-ONLY limitation**: Cannot edit or delete relationships through normal workflow
3. **No automatic inference**: Users must explicitly define relationships
4. **Schema complexity**: Another concept to understand and manage
5. **Version churn**: Adding relationships increments schema version

### Neutral

1. **No runtime behavior**: Relationships are metadata only (no query traversal)
2. **No validation integration**: Relationships do not affect field validation
3. **UI blocked until complete**: Relationship Editor cannot proceed until infrastructure exists

---

## 11. Explicitly Rejected Alternatives

### Alternative 1: Infer Relationships from Field References

**Rejected because**:
- LOOKUP and TABLE fields have technical semantics, not business semantics
- "Borehole has field referencing Project" ≠ "Project contains Boreholes"
- Cannot represent relationship names or descriptions
- Cannot version or export inferred relationships

### Alternative 2: Embed Relationships in EntityDefinition

**Rejected because**:
- Violates single responsibility (entity knows too much)
- Complicates entity versioning
- Cannot represent relationships where neither entity "owns" the relationship
- Makes bidirectional relationships awkward

### Alternative 3: Allow Full CRUD on Relationships

**Rejected because**:
- DELETE creates orphan risk (what if UI depends on relationship?)
- UPDATE allows semantic drift without version tracking
- Complicates compatibility checking
- Inconsistent with field immutability pattern
- Can be reconsidered in future phase with dependency checking

### Alternative 4: Relationship Types as User-Defined

**Rejected because**:
- Unbounded complexity
- No semantic meaning for system
- Complicates validation and compatibility
- Fixed enum is sufficient for v1

### Alternative 5: Store Relationships in Separate Database

**Rejected because**:
- Breaks atomic import/export
- Complicates transaction boundaries
- No benefit over co-located storage
- Violates schema cohesion principle

---

## References

- ADR-002: Clean Architecture with Domain-Driven Design
- ADR-008: Result Monad for Error Handling
- ADR-009: Strongly Typed Identifiers
- ADR-010: Immutable Value Objects
- ADR-007: Repository Pattern with Interface Segregation
- ADR-004: CQRS Pattern for Application Layer

---

**Document Status**: DRAFT
**Requires Approval**: YES
**Blocking**: Relationship Editor UI Phase

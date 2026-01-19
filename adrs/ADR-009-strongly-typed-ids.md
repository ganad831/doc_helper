# ADR-009: Strongly Typed Identifiers

**Status**: Accepted

**Context**: The old system used raw strings for all identifiers (field_id, entity_id, project_id). This led to bugs where IDs of different types were accidentally mixed.

**Decision**: Create distinct value object types for each identifier: FieldId, EntityId, ProjectId, etc. These wrap strings but are not interchangeable.

**Consequences**:
- (+) Type system prevents ID mixing errors
- (+) IDs carry semantic meaning in signatures
- (+) IDE autocomplete shows correct ID types
- (+) Easy to add ID validation in constructors
- (-) Wrapping/unwrapping boilerplate
- (-) Database mappers must convert types

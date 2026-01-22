# ADR-V2-SCHEMA-DESIGNER: Schema Designer as Dedicated AppType

**Status**: Proposed

**Date**: 2026-01-22

**Context**: v2 Platform - Schema Authoring Capability

---

## Context

### Current State

The v2 platform supports multiple AppTypes with strict architectural guarantees:

1. **AppType Isolation**: Each AppType is self-contained with its own schema, templates, and resources
2. **Schema-Driven Runtime**: Entity and field definitions drive UI rendering and validation behavior
3. **Platform Invariants**: Projects must reference valid, registered AppTypes
4. **Clean Architecture**: Domain layer is pure, infrastructure implements interfaces, application orchestrates

Currently, schemas are authored manually by editing SQLite `config.db` files directly. This approach has several problems:

- **No Validation**: Authors can create malformed schemas that crash the runtime
- **No Discoverability**: Field types, validation constraints, and platform capabilities are not documented in-tool
- **No Safety**: Direct database manipulation bypasses all business rules
- **Poor UX**: Requires SQL knowledge and external tooling

### The Problem

We need a schema authoring capability that:

- Provides a guided UI for creating entities, fields, validation rules, formulas, and controls
- Validates schema definitions against platform contracts before persistence
- Prevents creation of invalid schemas (circular dependencies, missing references, type mismatches)
- Respects platform architecture (no privileged access, no layer violations)

### The Temptation

It is tempting to implement schema editing as a **built-in platform feature** with direct access to other AppTypes' config.db files. This would allow:

- Schema Designer to directly mutate `app_types/soil_investigation/config.db`
- Unified UI for editing all AppTypes in one session
- Immediate live updates without import/export steps

**However, this violates platform invariants:**

- **Breaks AppType Isolation**: Schema Designer would have privileged write access to other AppTypes
- **Weakens Schema Guarantees**: No enforcement of version compatibility or schema contracts
- **Creates Tight Coupling**: Schema Designer becomes a special-case that all AppTypes depend on
- **Violates Clean Architecture**: Infrastructure layer (file system access) would be exposed to application layer

---

## Decision

**Schema Designer will be implemented as a dedicated AppType, not a built-in platform feature.**

### Core Architectural Decisions

#### Decision 1: Schema Designer is an AppType

**What**: Schema Designer is registered in the AppType registry like `soil_investigation` or any other AppType.

**Rationale**:
- **Uniform Treatment**: Schema Designer has no special privileges or direct access to other AppTypes
- **Dogfooding**: If the platform cannot be extended using its own extension model, the extension model is insufficient
- **Isolation**: Schema Designer's own schema (entities for EntityDefinition, FieldDefinition, etc.) is isolated from target AppTypes

**Consequences**:
- ✅ **Benefit**: Schema Designer respects platform invariants
- ✅ **Benefit**: Forces platform extensibility model to be complete
- ✅ **Benefit**: Schema Designer can be versioned, updated, or replaced independently
- ❌ **Drawback**: Cannot edit multiple AppTypes in one session (must export/import)

---

#### Decision 2: Export/Import for Schema Distribution

**What**: Schema Designer produces **schema export files** (JSON or SQLite). AppType authors import these files into their `config.db` manually or via a tool.

**Rationale**:
- **No Direct Mutation**: Schema Designer never writes to `app_types/other_app/config.db`
- **Version Control Friendly**: Schema exports are diffable, committable artifacts
- **Explicit Change Points**: Import is an intentional action, not a silent background mutation
- **Compatibility Enforcement**: Import step can validate schema compatibility with platform version

**Consequences**:
- ✅ **Benefit**: Schema changes are explicit, traceable, and reversible
- ✅ **Benefit**: Export files can be shared, reviewed, and tested before deployment
- ✅ **Benefit**: No risk of live corruption of production AppTypes
- ❌ **Drawback**: Extra step required (design → export → import → test)

---

#### Decision 3: Schema Designer Projects are Schemas-in-Progress

**What**: When you "create a new project" in Schema Designer, you're creating a **schema definition project** (not a document generation project). The project contains EntityDefinition, FieldDefinition, ValidationRule entities.

**Rationale**:
- **Fits MVVM Model**: Schema Designer uses the same dynamic form rendering as other AppTypes
- **Validation-Ready**: Schema validations (e.g., "formula references must exist") are enforced via Schema Designer's own validation rules
- **Reuses Infrastructure**: No need for separate schema storage mechanism

**Consequences**:
- ✅ **Benefit**: Schema Designer leverages existing platform capabilities
- ✅ **Benefit**: Schema validation happens at design time, not import time
- ✅ **Benefit**: Schema projects can be saved, reopened, versioned like any other project
- ⚠️ **Consideration**: Schema Designer's schema is meta-schema (schema for defining schemas)

---

#### Decision 4: Target Audience is AppType Authors

**What**: Schema Designer is designed for **developers creating custom AppTypes**, not end users.

**Rationale**:
- **Technical Audience**: Creating schemas requires understanding of platform contracts, field types, and validation rules
- **Not No-Code**: Schema Designer is a **low-code tool for developers**, not a no-code tool for non-technical users
- **Documentation Required**: Schema Designer does not replace documentation; it enforces contracts defined in documentation

**Consequences**:
- ✅ **Benefit**: UI can assume technical knowledge (no need to hide complexity)
- ✅ **Benefit**: Can expose advanced features (formulas, control chains, custom transformers)
- ✅ **Benefit**: Can provide validation error messages with technical details
- ⚠️ **Consideration**: End users creating documents will never use Schema Designer

---

#### Decision 5: Compatibility Rules Enforced at Export

**What**: Schema Designer validates that exported schemas are compatible with the platform version specified in the export metadata.

**Rationale**:
- **Prevents Breakage**: Cannot export a schema using v3 features to a v2 platform
- **Clear Errors**: Export fails with message like "Formula syntax 'advanced_if' requires platform v3.1+"
- **Versioned Contracts**: Platform version determines available field types, validation constraints, transformer types

**Consequences**:
- ✅ **Benefit**: Schema authors know immediately if schema is incompatible with target platform
- ✅ **Benefit**: Prevents runtime errors when importing incompatible schemas
- ❌ **Drawback**: Schema Designer must track platform version compatibility rules

---

### Explicit Non-Goals

The following are **explicitly out of scope** for Schema Designer:

#### Non-Goal 1: Live Editing of Deployed AppTypes

**What**: Schema Designer will NOT provide in-place editing of `app_types/soil_investigation/config.db` while the AppType is installed.

**Why**: Violates AppType isolation. Changes to deployed AppTypes should go through export → import → test cycle.

**Alternative**: Edit schema in Schema Designer project, export, import into target AppType, restart application.

---

#### Non-Goal 2: Schema Migration Tools

**What**: Schema Designer will NOT automatically migrate existing projects when schema changes (e.g., field renamed, entity removed).

**Why**: Migration is a complex, AppType-specific problem. Some changes are safe (add optional field), others are destructive (remove required field).

**Alternative**: AppType authors must provide migration scripts or documentation for schema changes. Platform may provide migration hooks in v3+.

---

#### Non-Goal 3: Template Designer Integration

**What**: Schema Designer will NOT include a WYSIWYG Word/Excel template editor.

**Why**: Template design is a separate concern. Templates are created in Word/Excel with content control tags that match field IDs from schema.

**Alternative**: Schema Designer can export a **field ID reference** for template authors to use when tagging content controls.

---

#### Non-Goal 4: Real-Time Collaboration

**What**: Schema Designer will NOT support multiple users editing the same schema simultaneously.

**Why**: Adds significant complexity (conflict resolution, operational transforms). Not required for AppType authoring workflow.

**Alternative**: Use version control (Git) for schema projects. Export files are diffable and mergeable.

---

#### Non-Goal 5: Visual Schema Graph Editor

**What**: Schema Designer will NOT provide a visual drag-and-drop graph editor for entity relationships.

**Why**: Premature optimization. Form-based editing is sufficient for v2. Visual editor can be added in v3+ if needed.

**Alternative**: Relationships defined via form fields (source entity, target entity, cardinality).

---

## Architectural Guarantees

Schema Designer upholds the following platform guarantees:

### Guarantee 1: No Privileged Access

Schema Designer has **zero special access** to platform internals. It:

- Uses the same `ISchemaRepository` interface as other AppTypes
- Cannot bypass validation or write directly to other AppTypes' files
- Cannot access `app_types/` directory outside its own AppType folder

### Guarantee 2: Schema Contracts Enforced

Schema Designer enforces all platform schema contracts:

- **Field IDs**: Snake_case, 1-50 characters
- **Entity IDs**: Snake_case, 1-50 characters
- **AppType IDs**: Lowercase, alphanumeric + underscores, 3-50 characters
- **Semantic Versions**: Major.Minor.Patch format
- **Formula Dependencies**: No circular references
- **Control Chains**: Max depth 10

### Guarantee 3: Export Format is Stable

Schema export format is **versioned and backward compatible**:

- Export format version specified in export file (e.g., `"export_format": "1.0"`)
- Breaking changes to export format require new major version
- Platform can reject exports with unsupported format versions

### Guarantee 4: Import is Idempotent

Importing the same schema export twice produces the same result:

- Import does not depend on current state of target `config.db`
- Import either fully succeeds or fully fails (atomic operation)
- No partial imports or corrupted states

---

## Consequences

### Benefits

1. **Platform Integrity Preserved**: Schema Designer cannot violate AppType isolation or platform invariants
2. **Extensibility Validated**: If Schema Designer can be built as an AppType, so can any other tool
3. **Version Control Friendly**: Schema exports are text-based, diffable, and committable
4. **Explicit Change Points**: Import step prevents accidental schema corruption
5. **Reuses Infrastructure**: Schema Designer leverages existing MVVM, validation, and persistence layers

### Drawbacks

1. **Extra Step Required**: Cannot edit AppTypes in place; must export → import
2. **No Multi-AppType Editing**: Cannot edit soil_investigation and structural_report schemas in one session
3. **No Live Preview**: Cannot see schema changes reflected in target AppType until import
4. **Meta-Schema Complexity**: Schema Designer's own schema (schema for schemas) is inherently complex

### Risks

1. **User Confusion**: Developers may expect Schema Designer to directly edit AppTypes
   - **Mitigation**: Clear documentation explaining export/import workflow
2. **Export Format Drift**: Schema export format may diverge from `config.db` structure
   - **Mitigation**: Automated tests validate export → import round-trip
3. **Compatibility Tracking**: Schema Designer must track which features require which platform versions
   - **Mitigation**: Compatibility matrix in documentation, enforced at export time

---

## Alternatives Considered

### Alternative 1: Built-In Platform Feature

**Description**: Implement schema editing as a built-in feature with direct access to `app_types/` directory.

**Why Rejected**: Violates AppType isolation, creates privileged platform component, weakens schema guarantees.

---

### Alternative 2: Schema Editor Plugin for Each AppType

**Description**: Each AppType provides its own schema editor as part of its codebase.

**Why Rejected**: Duplicates effort across AppTypes, no shared validation logic, inconsistent UX.

---

### Alternative 3: External CLI Tool

**Description**: Provide a command-line tool (`doc-helper schema-edit`) that edits `config.db` files outside the GUI.

**Why Rejected**: Bypasses platform validation, no WYSIWYG preview, poor UX for visual schema design.

---

## Implementation Notes

The following are **non-prescriptive notes** on potential implementation approaches. They are **not part of the ADR decision**.

### Potential Schema Designer Schema

Schema Designer's own schema might include entities like:

- **EntityDefinition**: Represents a target AppType's entity
- **FieldDefinition**: Represents a field within an entity
- **ValidationRule**: Represents a validation constraint
- **FormulaDefinition**: Represents a calculated field formula
- **ControlRule**: Represents an inter-field control
- **OutputMapping**: Represents a field → template tag mapping

Each of these would be editable via dynamic forms, just like any other AppType.

### Potential Export Format

Schema exports might be JSON files with structure:

```json
{
  "export_format_version": "1.0",
  "platform_version_min": "2.0.0",
  "entities": [...],
  "fields": [...],
  "validation_rules": [...],
  "formulas": [...],
  "controls": [...]
}
```

### Potential Import Workflow

1. User selects "Import Schema" from AppType management UI
2. User selects export file and target AppType
3. Platform validates export format version
4. Platform validates compatibility with current platform version
5. Platform shows preview of changes (entities added/removed, fields modified)
6. User confirms import
7. Platform writes to target `config.db` atomically
8. Platform invalidates schema cache
9. User must restart application for changes to take effect

---

## Open Questions

The following questions are **deferred to implementation planning**:

1. **Schema Versioning**: How are schema changes versioned within an AppType? (e.g., soil_investigation schema v1.0 → v2.0)
2. **Migration Hooks**: Should platform provide hooks for AppTypes to define data migration logic when schema changes?
3. **Partial Exports**: Can users export a subset of schema (e.g., only one entity) or must export entire schema?
4. **Conflict Resolution**: If user imports a schema that conflicts with existing `config.db`, what happens? (Overwrite? Merge? Fail?)
5. **Template Sync**: How are templates kept in sync with schema changes? (e.g., field renamed → update all content control tags?)

---

## Related ADRs

- **ADR-002**: Clean Architecture + Domain-Driven Design (Schema Designer respects layer boundaries)
- **ADR-003**: Framework-Independent Domain Layer (Schema Designer's domain is pure Python)
- **ADR-013**: Multi-Document-Type Platform Vision (Schema Designer is an AppType, not built-in feature)
- **ADR-V2-APPTYPE-METADATA**: AppType manifest.json structure (Schema Designer produces valid manifests)

---

## Approval

**Proposed By**: [Author Name]

**Reviewers**: [List reviewers]

**Approval Status**: Proposed (awaiting review)

**Decision Date**: [Date when accepted/rejected]

---

**End of ADR-V2-SCHEMA-DESIGNER**

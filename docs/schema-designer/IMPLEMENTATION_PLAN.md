# Schema Designer Implementation Plan

**Status**: Draft

**Date**: 2026-01-22

**Related ADR**: [ADR-V2-SCHEMA-DESIGNER](adrs/ADR-V2-SCHEMA-DESIGNER.md)

**Purpose**: Staged implementation plan for building Schema Designer as a dedicated AppType

---

## Phase 1: Core Meta-Schema

### What Schema Designer Needs to Describe Itself

Schema Designer is a tool for creating schemas. But Schema Designer itself IS an AppType, which means it needs its own schema describing what data it collects. This is the "meta-schema" - a schema for defining schemas.

**EntityDefinition Entity**
- **Purpose**: Represents one entity in the target schema (like "Bridge" or "Girder")
- **Responsibility**: Stores entity name, whether it's singleton or collection, display order
- **Why needed**: Every schema needs entities. This is the container for all the entity-level properties.
- **Minimum to be useful**: Name, type (singleton/collection), optional description

**FieldDefinition Entity**
- **Purpose**: Represents one field within an entity (like "Bridge Name" or "Inspection Date")
- **Responsibility**: Stores field name, field type (TEXT, NUMBER, DATE, etc.), which entity it belongs to
- **Why needed**: Entities are containers; fields are what users actually fill out
- **Minimum to be useful**: Name, field type, parent entity, required flag, display order

**RelationshipDefinition Entity**
- **Purpose**: Represents a connection between two entities (like "Bridge has many Girders")
- **Responsibility**: Stores source entity, target entity, cardinality, cascade rules
- **Why needed**: Data is interconnected. Explicit relationships prevent the "text field" anti-pattern.
- **Minimum to be useful**: Source entity, target entity, cardinality (one-to-one, one-to-many, many-to-many)
- **Phase 1 Note**: RelationshipDefinition exists in the meta-schema from Phase 1, but UI support for creating relationships is deferred to Phase 2.1

**ValidationRule Entity**
- **Purpose**: Represents one validation constraint on a field (like "Year Built must be > 1800")
- **Responsibility**: Stores which field it validates, constraint type, constraint parameters
- **Why needed**: Fields need rules to prevent invalid data
- **Minimum to be useful**: Parent field, constraint type (required, min/max, pattern), constraint values

**FormulaDefinition Entity**
- **Purpose**: Represents a calculated field (like "Total Bridge Count = COUNT(bridges)")
- **Responsibility**: Stores formula expression, which fields it depends on
- **Why needed**: Schemas often need computed values
- **Minimum to be useful**: Parent field, expression text, list of dependencies

**ControlRule Entity**
- **Purpose**: Represents inter-field effects (like "If 'Has Damage' = Yes, show 'Damage Description' field")
- **Responsibility**: Stores source field, target field, effect type, condition
- **Why needed**: UX requires dynamic forms that respond to user input
- **Minimum to be useful**: Source field, target field, effect type (visibility, enable, value_set)

**OutputMapping Entity** (Phase 2, not Phase 1)
- **Purpose**: Maps fields to template tags in Word/Excel documents
- **Responsibility**: Stores field ID, template tag name, transformer type
- **Why needed**: Schemas must specify how data flows into documents
- **Deferred**: Phase 1 focuses on data structure, not document generation

### Absolute Minimum for Phase 1

To be minimally useful, Schema Designer needs:
- EntityDefinition (with name and type)
- FieldDefinition (with name, type, parent entity)
- ValidationRule (with basic required/min/max constraints)

Everything else can wait. This allows creating simple schemas with validated fields.

---

## Phase 2: Minimum Viable Schema Designer

### What a User Can Do

**Create entities:**
- Add entity, name it, choose singleton or collection
- See list of entities in the schema
- Delete entities (with warning if they have fields)

**Create fields:**
- Add field to an entity, name it, choose field type from the 12 standard types
- Mark field as required or optional
- Set display order (which field appears first in forms)

**Create basic validation:**
- Add "required" constraint to any field
- Add min/max constraints to number fields
- Add min_length/max_length to text fields
- Add min_date/max_date to date fields

**Export schema:**
- Click "Export Schema"
- Get validation results (errors block export, warnings allow export)
- Receive a JSON file with the schema definition

### What is Intentionally Not Supported Yet

**Not in Phase 2:**
- Relationship UI (entity exists in meta-schema, UI deferred to Phase 2.1)
- Formulas (deferred to Phase 2.2)
- Control rules (deferred to Phase 2.2)
- Output mappings (deferred to Phase 2.3)
- Regex pattern validation (deferred to Phase 2.1)
- Custom transformers (deferred to Phase 3)

**Why this is safe:**
Phase 2 produces schemas that can define simple data collection forms with basic validation. This is enough to:
- Test the export/import workflow
- Validate that Schema Designer itself works as an AppType
- Create simple document types (like contact forms, basic reports)
- Prove the architecture before adding complexity

A Phase 2 schema might define "Building Inspection" with entities: Building, Room, Inspector. Each entity has simple text, number, and date fields with required/optional validation. No formulas, no relationships, no fancy features. But it works, it's exportable, and it's safe.

---

## Phase 2.1: Relationships and Advanced Validation

### Add Relationships

**What users can now do:**
- Define "Bridge has many Girders" relationships
- Specify cardinality (one-to-one, one-to-many, many-to-many)
- Choose cascade behavior (delete cascade, restrict, set null)
- Name the inverse relationship for bidirectional navigation

**Why this is a separate phase:**
Relationships require additional validation. You must check:
- Source and target entities exist
- Cascade rules are safe (ambiguous or circular cascade configurations must be rejected)
- Cardinality constraints are consistent

**Note**: Cyclic relationship graphs (Entity A → B → C → A) are ALLOWED. Cycles are only forbidden in formulas and control chains, not in entity relationships.

### Add Pattern Validation

**What users can now do:**
- Add regex pattern validation to text fields
- Get error messages if pattern is malformed

**Why deferred from Phase 2:**
Pattern validation requires testing regex syntax, which can fail in complex ways. Phase 2 keeps validation simple.

---

## Phase 2.2: Formulas and Controls

### Add Formulas

**What users can now do:**
- Mark a field as calculated
- Enter a formula expression (like `{{field_count}} * 2`)
- Schema Designer validates that referenced fields exist
- Schema Designer detects circular dependencies

**Why this is complex:**
Formulas create dependency graphs. You must:
- Parse formula syntax
- Extract field references
- Build dependency graph
- Detect cycles
- Validate that formula output type matches field type

### Add Control Rules

**What users can now do:**
- Define "If Field A = X, then hide Field B"
- Define "If Field A = Y, then set Field B = Z"
- Specify control chains (A controls B, B controls C)

**Why this is complex:**
Controls can chain. You must:
- Detect control cycles
- Enforce max chain depth (10)
- Validate that source/target field types are compatible with effect type

---

## Phase 2.3: Output Mappings

**What users can now do:**
- Map fields to Word template tags
- Choose transformers (suffix, prefix, date format, etc.)
- Specify Excel cell references
- Generate a "template author reference guide" showing all field IDs and their purposes

**Why deferred:**
Output mappings don't affect data collection or validation. They only matter when generating documents. Phase 2 focuses on data structure first.

---

## Phase 3: Validation & Export

### When Validation Happens

**Continuous validation:**
As users work, Schema Designer continuously checks:
- Field names are unique within an entity
- Entity names are unique within the schema
- Field types are valid
- Referenced entities/fields exist

This gives immediate feedback to the user.

**Export-time validation:**
When user clicks "Export Schema", Schema Designer runs a comprehensive check:
- All ERROR-level issues (see below)
- All WARNING-level issues (see below)
- All INFO-level notices

### What Blocks Export (ERROR-level)

These prevent export file creation:
- **Circular dependencies**: Formula A depends on Formula B, which depends on Formula A
- **Broken references**: Field references an entity that doesn't exist
- **Invalid field types**: Field type doesn't exist in the platform version
- **Control chain too deep**: Control chain exceeds max depth (10)
- **Duplicate names**: Two fields in the same entity have the same name
- **Invalid app_type_id**: Schema's target app_type_id violates platform naming rules
- **Malformed formula**: Formula syntax is unparseable
- **Incompatible relationship**: Many-to-many relationship with delete cascade (doesn't make sense)

**User sees:**
"Export failed. Fix these errors first:"
- "Formula 'total_cost' has circular dependency: total_cost → unit_price → total_cost"
- "Field 'inspection_date' references entity 'inspectors' which doesn't exist"

**No file is created.**

### What Allows Export with Warnings (WARNING-level)

These produce export file but warn user:
- **Missing help text**: Field has no user-facing help text
- **Optional field, no default**: Optional field doesn't specify what value to use if empty
- **Unused entity**: Entity defined but has no fields
- **Very long field name**: Field name exceeds recommended 30 characters (still valid, but awkward)
- **Transformer not installed**: Schema references a custom transformer that isn't in the platform (Phase 2.3+ only)
- **No output mappings**: Schema has no output mappings (INFO-level until Phase 2.3, WARNING-level after)

**User sees:**
"Export succeeded with warnings:"
- "Field 'inspector_notes' is optional but has no default value. Documents may show blank spaces."
- "Entity 'archived_inspections' has no fields. Remove it or add fields."

**File is created.** Warnings array is included in export metadata.

### What Export Metadata Must Include

Every export file includes:
- **export_format_version**: "2.0.0" (file structure version)
- **schema_semantic_version**: "2.1.0" (schema meaning version)
- **platform_version_min**: "2.1.0" (minimum platform version required to use this schema)
- **created_date**: "2024-01-22T14:30:00Z"
- **created_by**: "Schema Designer v2.1.0"
- **target_app_type_id**: "bridge_inspection" (what AppType this schema is for)
- **warnings**: ["Missing help text: inspector_notes", ...] (list of warnings from export)
- **capabilities_required** (optional): ["CALCULATED fields", "RelationshipDefinition", "REGEX validation"] (features this schema uses, one possible compatibility mechanism)

This metadata allows import tooling to:
- Check compatibility before parsing
- Show warnings to user
- Determine if platform supports required features (via capability declarations or version checks)

---

## Phase 4: Import & Platform Integration

### How Schema Designer Output is Consumed

**Step 1: User receives export file**
- An exported schema file (JSON format)
- This file contains all entities, fields, relationships, validation rules, formulas, controls, output mappings

**Step 2: User runs import tool**
- Via provided import mechanism (command-line tool, GUI dialog, or other means)
- User specifies the export file and target AppType

**Step 3: Compatibility checks happen**

Before parsing the file contents, import tooling checks:

**Check 1: Export format version**
- Can this platform read this file structure?
- If export format major version is unsupported, fail immediately: "Cannot import: export format v3.0.0 not supported (platform supports v2.x only)"

**Check 2: Schema semantic version**
- Does this platform support the features this schema uses?
- Verify compatibility via capability declarations, version checks, or other mechanisms
- If unsupported features found, fail with clear message indicating what is missing

**Check 3: Platform version minimum**
- Is this platform new enough?
- If `platform_version_min` > current platform version, fail: "Cannot import: schema requires platform v2.5+, you have v2.1"

**If all checks pass, proceed to parsing.**

### What Happens on Success

**Import succeeds:**
1. Import tooling parses export file
2. Validates internal consistency (no broken references, no circular deps in formulas/controls)
3. Writes schema to target AppType storage
4. Logs success message confirming import
5. Shows warnings (if any) from export metadata
6. May require application restart for changes to take effect

**AppType registry loads the updated AppType.**
**User can now create projects using the new schema.**

### What Happens on Failure

**Compatibility check fails:**
- Import stops before parsing
- User sees clear message indicating version mismatch or missing features
- No changes made to target AppType
- User must upgrade platform or modify schema

**Parsing fails:**
- Import tooling encounters malformed file structure or missing required fields
- User sees error message indicating file corruption
- No changes made to target AppType
- User must re-export from Schema Designer

**Validation fails:**
- Schema has circular dependencies in formulas/controls or broken references that weren't caught at export
- User sees error message with details
- No changes made to target AppType
- This indicates a bug in Schema Designer export validation

### Where Compatibility Checks Happen

**At export time (Schema Designer):**
- Check that schema is internally consistent
- Check that schema doesn't use features beyond its declared schema semantic version
- Warn if schema uses platform features newer than platform_version_min

**At import time (Platform):**
- Check that export format version is readable
- Check that schema semantic version is supported
- Check that all required capabilities are available
- Check that platform version meets minimum requirement

**At runtime (Platform):**
- When loading AppType, validate that schema is compatible with current platform version
- If schema declares incompatible version, refuse to load AppType with clear error message

---

## Phase 5: Deferred Features

### Features That Must Not Be Built Yet

**Visual Graph Editor**
- **What it is**: Drag-and-drop boxes and arrows to define entities and relationships
- **Why deferred**: Complex UI, not needed for v2. Form-based editing is sufficient. Can be added in v3 if user feedback demands it.

**Live AppType Editing**
- **What it is**: Edit schema while AppType is installed, see changes immediately without restart
- **Why deferred**: Violates AppType isolation. Would require complex schema versioning and data migration mid-session. Export/import workflow is intentional safety boundary.

**Schema Migrations**
- **What it is**: Automatic conversion of old project data when schema changes (e.g., field renamed, entity removed)
- **Why deferred**: Migration is AppType-specific. Some changes are safe (add optional field), others destructive (remove required field). Platform cannot know intent. AppType authors must provide migration scripts separately. v3+ may add migration hook system.

**Real-Time Collaboration**
- **What it is**: Multiple users editing the same schema simultaneously (like Google Docs)
- **Why deferred**: Requires conflict resolution, operational transforms, server infrastructure. Not required for AppType authoring workflow. Use version control (Git) instead.

**Code Generation**
- **What it is**: Generate Python classes or TypeScript interfaces from schema
- **Why deferred**: Platform is schema-driven at runtime. Code generation is unnecessary for platform operation. Could be added as a developer convenience tool in v3+, but not core to Schema Designer.

**Template Designer Integration**
- **What it is**: WYSIWYG Word/Excel template editor built into Schema Designer
- **Why deferred**: Templates are created in Word/Excel. Schema Designer can export a field reference guide, but shouldn't try to replace Microsoft Office. Content control tagging is a manual, creative process.

**Schema Diffing Tool**
- **What it is**: Compare two schema versions, show what changed (like `git diff`)
- **Why deferred**: Useful for reviewing changes, but not needed for basic workflow. Can be added in v3 as quality-of-life improvement. For now, use version control and read the export JSON.

**Schema Composition**
- **What it is**: Import fragments from other schemas (like "add the standard 'Contact Info' entity to my schema")
- **Why deferred**: Complex. Requires namespace management, conflict resolution, version compatibility. Phase 2 focuses on creating schemas from scratch. Composition is a v3+ feature.

**AI-Assisted Schema Generation**
- **What it is**: "Create a schema for vehicle maintenance reports" → AI generates entities/fields
- **Why deferred**: Experimental. Requires AI integration, prompt engineering, validation of AI output. Not architecturally necessary. Can be added in v4+ if desired.

**Validation Rule Wizard**
- **What it is**: Guided UI for creating complex regex patterns or custom validation logic
- **Why deferred**: Phase 2 supports basic validation (required, min/max, pattern). Wizard for advanced patterns is quality-of-life, not core functionality. Can be added in v2.3+.

---

## Summary: Build Order

**Phase 1 (Core Meta-Schema):**
- EntityDefinition, FieldDefinition, ValidationRule entities
- Get the meta-schema right first

**Phase 2 (Minimum Viable):**
- Simple entity/field creation
- Basic validation (required, min/max)
- Export with error/warning checks

**Phase 2.1 (Relationships):**
- RelationshipDefinition UI support (entity exists in Phase 1 meta-schema)
- Advanced validation (pattern, regex)

**Phase 2.2 (Formulas and Controls):**
- FormulaDefinition entity
- ControlRule entity
- Dependency graph validation

**Phase 2.3 (Output Mappings):**
- OutputMapping entity
- Template reference guide generation

**Phase 3 (Validation & Export):**
- Comprehensive validation (error/warning/info levels)
- Metadata-rich export files
- Capability declaration system

**Phase 4 (Import & Integration):**
- Import tooling
- Compatibility checking
- Platform integration testing

**Not Now (Deferred):**
- Visual editors, live editing, migrations, collaboration, code generation, AI assistance

This plan builds foundational layers first, adds complexity incrementally, and explicitly postpones features that aren't architecturally necessary for v2.

---

## Appendix: Non-Binding Examples

The following examples illustrate concepts from the plan but are NOT prescriptive. Implementation details may vary.

### Example: Export File Naming
- Possible: `bridge_inspection_schema_v1.json`
- Or: `schema_export_20240122.json`
- Or: Any valid filename chosen by user

### Example: Import Mechanism
- Possible: Command-line tool like `doc-helper import-schema <file> --target <apptype>`
- Or: GUI dialog with file picker
- Or: Drag-and-drop import
- Or: Web-based import interface

### Example: File Storage Location
- Possible: `app_types/bridge_inspection/config.db`
- Or: `apptypes/bridge-inspection/schema.db`
- Or: Cloud storage, key-value store, or other persistence mechanism

### Example: User Feedback Messages
- Error example: "Cannot import: export format v3.0.0 not supported (platform supports v2.x only)"
- Warning example: "Field 'inspector_notes' is optional but has no default value"
- Success example: "Schema imported successfully. Restart to use new schema."

These are illustrations only. Actual implementation may use different wording, structure, or mechanisms.

---

**End of Implementation Plan**

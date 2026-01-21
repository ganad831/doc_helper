# ADR-V2-002: AppType Configuration and Project Identity Model

**Status**: Draft
**Date**: 2026-01-21
**Category**: v2 Platform Architecture
**Deciders**: Project Lead
**Governance**: See [AGENT_RULES.md](../AGENT_RULES.md) Section 16

---

## Context

With the introduction of the Platform-AppType boundary (ADR-V2-001), we need to address two related concerns:

### 1. AppType Configuration

Each AppType must declare its capabilities and requirements. In v1, this information is implicit:
- Schema location: hardcoded path
- Templates: discovered by convention
- Transformers: built-in only
- Metadata: embedded in code

For v2, AppTypes need a standardized way to declare:
- Identity (unique ID, display name, version)
- Resource locations (schema, templates, extensions)
- Capabilities (supported features, transformer registrations)

### 2. Project Identity

Projects must be associated with their AppType. In v1, all projects implicitly belong to "Soil Investigation". In v2:
- Each project must know its AppType
- This association is permanent (cannot change after creation)
- The association must survive project close/reopen
- The Platform must load the correct AppType when opening a project

Without explicit project identity:
- Platform cannot route project operations to correct AppType
- Projects could be opened with wrong AppType (schema mismatch)
- Migration between AppTypes would require undefined behavior

---

## Decision

### 1. AppType Manifest Format

Each AppType package will include a `manifest.json` file declaring its configuration:

```json
{
  "id": "soil_investigation",
  "name": "Soil Investigation Report",
  "version": "1.0.0",
  "description": "Generate professional soil investigation reports",
  "icon": "icon.png",

  "schema": {
    "source": "config.db",
    "type": "sqlite"
  },

  "templates": {
    "word": ["templates/report.docx"],
    "excel": ["templates/data.xlsx"],
    "default": "templates/report.docx"
  },

  "extensions": {
    "transformers": ["extensions/geo_transformers.py"]
  },

  "capabilities": {
    "supports_pdf_export": true,
    "supports_excel_export": true,
    "supports_word_export": true
  },

  "requirements": {
    "platform_version": ">=2.0.0"
  }
}
```

### 2. Manifest Schema Rules

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier (lowercase, alphanumeric, underscores) |
| `name` | Yes | Human-readable display name |
| `version` | Yes | Semantic version (X.Y.Z) |
| `description` | No | Short description for UI display |
| `icon` | No | Relative path to icon file (PNG, 128x128 recommended) |
| `schema.source` | Yes | Relative path to schema database |
| `schema.type` | Yes | Schema format (currently only "sqlite") |
| `templates.word` | No | List of Word template paths |
| `templates.excel` | No | List of Excel template paths |
| `templates.default` | No | Default template for generation |
| `extensions.transformers` | No | List of custom transformer module paths |
| `capabilities.*` | No | Feature flags |
| `requirements.platform_version` | No | Minimum platform version |

### 3. Project Identity Model

Projects will store their AppType association in the project database:

```sql
-- Added to project.db metadata table
ALTER TABLE project_metadata ADD COLUMN app_type_id TEXT NOT NULL DEFAULT 'soil_investigation';
```

**Project Metadata DTO**:

```python
@dataclass(frozen=True)
class ProjectIdentity:
    """Immutable project identity including AppType association."""

    project_id: ProjectId
    name: str
    app_type_id: str  # References AppType manifest 'id'
    created_at: datetime
    last_modified: datetime
```

### 4. Project-AppType Association Rules

1. **Permanent Association**: Once created, a project's `app_type_id` cannot be changed
2. **Creation Requirement**: `app_type_id` is mandatory at project creation
3. **Validation at Open**: Platform validates AppType exists before opening project
4. **Graceful Degradation**: If AppType not found, show error (don't open with wrong AppType)

### 5. Discovery and Validation Flow

```
App Startup:
1. Platform scans `app_types/` directory
2. For each subdirectory, load `manifest.json`
3. Validate manifest schema
4. Register valid AppTypes in registry
5. Invalid manifests logged, not registered

Project Creation:
1. User selects AppType from available list
2. Platform creates project with selected `app_type_id`
3. Project database initialized with AppType schema

Project Open:
1. Platform reads `app_type_id` from project metadata
2. Platform looks up AppType in registry
3. If found: load project with correct AppType context
4. If not found: display error, refuse to open
```

---

## Options Considered

### Option A: Manifest in JSON (Selected)
- Configuration in `manifest.json` file
- **Pros**: Human-readable, easy to edit, standard format
- **Cons**: Separate file from code
- **Selected**: Appropriate for configuration data

### Option B: Manifest in Python
- Configuration in `__init__.py` as Python constants
- **Pros**: No separate file, type checking
- **Cons**: Requires importing Python to read config
- **Rejected**: Tight coupling to Python execution

### Option C: Manifest in Database
- Configuration in `config.db` alongside schema
- **Pros**: Single data source
- **Cons**: Less accessible, requires SQLite to read
- **Rejected**: Configuration should be inspectable without database tools

### Option A (Project Identity): Database Column (Selected)
- Store `app_type_id` in project database
- **Pros**: Atomic with project data, survives all operations
- **Selected**: Natural home for project metadata

### Option B (Project Identity): Separate Metadata File
- Store `app_type_id` in `project_meta.json`
- **Pros**: Human-readable
- **Cons**: File could be deleted/corrupted separately
- **Rejected**: Risk of metadata/data desync

---

## Consequences

### Positive

1. **Self-Documenting AppTypes**: Manifest makes AppType capabilities explicit
2. **Robust Project Association**: Database storage ensures permanent association
3. **Validation at Boundaries**: Invalid configurations caught early
4. **Extensibility**: New manifest fields can be added without breaking existing

### Negative

1. **Manifest Maintenance**: Must keep manifest in sync with actual capabilities
2. **Migration Complexity**: Existing projects need `app_type_id` column added
3. **Validation Overhead**: Manifest parsing on every startup

### Neutral

1. **Schema Evolution**: Manifest schema may need versioning
2. **Localization**: Display names in manifest not localized (use translation keys)

---

## Implementation Plan

### Phase 1: Define Manifest Schema
1. Create JSON Schema for manifest validation
2. Document all manifest fields
3. Create sample manifest for Soil Investigation

### Phase 2: Implement Manifest Parsing
1. Create `ManifestParser` in infrastructure layer
2. Create `ManifestValidationError` for invalid manifests
3. Return `AppTypeManifest` value object

### Phase 3: Update Project Database
1. Add migration to add `app_type_id` column
2. Default existing projects to `soil_investigation`
3. Update `IProjectRepository` interface

### Phase 4: Integrate with Discovery
1. `AppTypeDiscoveryService` uses `ManifestParser`
2. Validation errors logged, invalid AppTypes skipped
3. Registry populated with valid `AppTypeManifest` objects

---

## Non-Goals

This ADR does NOT address:

1. **Manifest versioning/migration**: Schema changes handled as needed
2. **Manifest signing**: No integrity verification
3. **Dynamic manifest updates**: Manifests read at startup only
4. **Manifest inheritance**: Each AppType declares complete configuration
5. **Multi-language manifest names**: Use translation keys, not inline text

---

## Migration Plan

### v1 Projects Migration

1. **Automatic Migration**
   - When opening v1 project in v2 Platform
   - Database migrator adds `app_type_id` column
   - Default value: `soil_investigation`
   - No user action required

2. **No Data Loss**
   - All existing project data preserved
   - Only metadata extended

3. **Backward Compatibility**
   - v2 projects can be opened by v2 only (new column)
   - v1 projects automatically upgraded to v2 format

### Soil Investigation Manifest Creation

1. Create `app_types/soil_investigation/manifest.json`
2. Populate with current implicit configuration
3. Validate existing templates/schema paths

---

## Related ADRs

- **ADR-V2-001**: Platform AppType Boundary and Host Contract
- **ADR-V2-003**: Multi-App Module Layout and Dependency Rules
- **ADR-010**: Immutable Value Objects (manifest as value object)
- **ADR-007**: Repository Pattern (project repository changes)

---

## v1 Impact Assessment

**v1 Behavior Changes**: NONE
- All v1 functionality remains unchanged
- Implicit `soil_investigation` becomes explicit default

**v1 Code Changes**: EXTEND ONLY
- Project database schema extended (new column with default)
- Project repository interface extended (new field)
- No breaking changes to existing code

**v1 Data Migration**: AUTOMATIC
- Existing projects gain `app_type_id = 'soil_investigation'`
- Migration runs on first open in v2

---

*This ADR is DRAFT status. Implementation requires explicit authorization per AGENT_RULES.md Section 16.*

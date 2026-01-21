# Doc Helper Interchange Format v1

**ADR-039: Import/Export Data Format**

This document defines the JSON interchange format for importing and exporting Doc Helper projects.

## Format Version

**Current Version**: `1.0`

The interchange format version is independent of the application version. Format version changes when the structure of the interchange format changes in a non-backward-compatible way.

## Structure Overview

```json
{
  "format_version": "1.0",
  "metadata": {
    "project_id": "uuid-string",
    "project_name": "string",
    "created_at": "ISO-8601-datetime",
    "modified_at": "ISO-8601-datetime",
    "app_version": "semver-string",
    "exported_at": "ISO-8601-datetime",
    "exported_by": "app-version-string"
  },
  "schema": {
    "entities": [...],
    "fields": [...]
  },
  "data": {
    "entity_id": [
      {
        "record_id": "uuid-or-sequence",
        "fields": {
          "field_id": "value",
          ...
        }
      },
      ...
    ],
    ...
  }
}
```

## Section Specifications

### 1. Format Version

```json
{
  "format_version": "1.0"
}
```

**Required**: Yes
**Type**: String
**Purpose**: Identifies the interchange format version. Enables version compatibility checking and migration.

**Version Rules**:
- Major version increments indicate breaking changes (older importers cannot read)
- Minor version increments indicate backward-compatible additions (older importers can read, ignoring new fields)

### 2. Metadata Section

```json
{
  "metadata": {
    "project_id": "12345678-1234-5678-1234-567812345678",
    "project_name": "Soil Investigation - Downtown Site",
    "created_at": "2026-01-20T10:30:00Z",
    "modified_at": "2026-01-21T14:45:00Z",
    "app_version": "1.0.0",
    "exported_at": "2026-01-21T15:00:00Z",
    "exported_by": "Doc Helper 1.0.0"
  }
}
```

**Fields**:
- `project_id` (string, UUID): Unique identifier of the original project
- `project_name` (string): Human-readable project name
- `created_at` (string, ISO-8601): When the project was originally created
- `modified_at` (string, ISO-8601): When the project was last modified before export
- `app_version` (string, semver): Application version that created the project
- `exported_at` (string, ISO-8601): When the export was performed
- `exported_by` (string): Application identification string

**Import Behavior**:
- `project_id`: New UUID generated on import (original ID preserved in metadata only)
- `project_name`: Used as imported project name (user can rename)
- Timestamps: Preserved as metadata, not used for imported project timestamps
- `app_version`: Used for compatibility checking

### 3. Schema Section

```json
{
  "schema": {
    "entities": [
      {
        "id": "project",
        "name": "Project Information",
        "description": "Main project metadata",
        "entity_type": "SINGLETON"
      },
      {
        "id": "borehole",
        "name": "Borehole",
        "description": "Borehole records",
        "entity_type": "COLLECTION"
      }
    ],
    "fields": [
      {
        "id": "site_location",
        "entity_id": "project",
        "label": "Site Location",
        "field_type": "TEXT",
        "required": true,
        "validation_rules": {
          "min_length": 5,
          "max_length": 200
        }
      },
      {
        "id": "depth",
        "entity_id": "borehole",
        "label": "Depth (m)",
        "field_type": "NUMBER",
        "required": true,
        "validation_rules": {
          "min_value": 0,
          "max_value": 100
        }
      }
    ]
  }
}
```

**Purpose**: Schema section enables import validation without requiring the application to be running. External tools can validate data against schema before import.

**Entities Array**:
- `id` (string): Unique entity identifier
- `name` (string): Translatable display name key
- `description` (string, optional): Entity description
- `entity_type` (string): "SINGLETON" or "COLLECTION"

**Fields Array**:
- `id` (string): Unique field identifier within entity
- `entity_id` (string): Parent entity ID
- `label` (string): Field display label
- `field_type` (string): One of 12 field types (TEXT, NUMBER, DATE, etc.)
- `required` (boolean): Whether field is required
- `validation_rules` (object, optional): Type-specific validation constraints
- `options` (array, optional): For DROPDOWN, RADIO, CHECKBOX field types
- `formula` (string, optional): For CALCULATED field types

**Import Behavior**:
- Schema is validated against current application schema version
- If schemas are compatible, data is imported
- If schemas differ, compatibility rules determine import success/failure

### 4. Data Section

```json
{
  "data": {
    "project": [
      {
        "record_id": "default",
        "fields": {
          "site_location": "123 Main Street, Downtown",
          "owner_name": "John Doe",
          "start_date": "2026-01-15"
        }
      }
    ],
    "borehole": [
      {
        "record_id": "BH-001",
        "fields": {
          "depth": 10.5,
          "soil_type": "Clay",
          "description": "Brown clay with sand seams"
        }
      },
      {
        "record_id": "BH-002",
        "fields": {
          "depth": 15.0,
          "soil_type": "Sand",
          "description": "Fine to medium sand"
        }
      }
    ]
  }
}
```

**Structure**:
- Top-level keys are entity IDs (from schema)
- Values are arrays of records (even for SINGLETON entities)
- Each record has:
  - `record_id` (string): Record identifier (UUID for collections, "default" for singletons)
  - `fields` (object): Map of field_id → value

**Field Value Types**:
- `TEXT`, `TEXTAREA`: String
- `NUMBER`: Number (integer or float)
- `DATE`: String (ISO-8601 date: "YYYY-MM-DD")
- `DROPDOWN`, `RADIO`: String (option value)
- `CHECKBOX`: Boolean
- `CALCULATED`: Computed value (any JSON type)
- `LOOKUP`: String (reference to another record ID)
- `FILE`, `IMAGE`: String (file path or URL)
- `TABLE`: Array of objects (nested tabular data)

**Null Values**:
- Missing fields are treated as null/empty
- Explicit `null` values are permitted
- Required fields with null values fail validation on import

## Exclusions

**Not Included in Exports** (per ADR-039):
- Field history (ADR-027): Audit trail data, not interchange data
- Undo stack state (ADR-031): Session-specific ephemeral state
- Generated documents: Outputs, not source data
- Attachments content: File paths/references only, not file binary data

## Validation Rules

**On Export**:
- Project must be open and valid
- All required fields must have values
- No validation errors in project

**On Import**:
1. **Format Validation**:
   - JSON is well-formed
   - Required top-level sections present (format_version, metadata, schema, data)
   - Field types match expected types

2. **Schema Validation**:
   - Entity IDs are unique
   - Field IDs are unique within entity
   - Field types are recognized (one of 12 valid types)
   - Entity references are valid

3. **Data Validation**:
   - All data entities exist in schema
   - All data fields exist in schema
   - Field values match field types
   - Required fields are present
   - Validation constraints satisfied (min/max, patterns, etc.)
   - Referential integrity maintained (lookup references valid)

4. **Version Compatibility**:
   - Format version is supported
   - App version compatibility rules satisfied

**Import Failure Modes**:
- Invalid JSON syntax → Parse error reported
- Missing required sections → Structure error reported
- Schema incompatibility → Version error with details
- Validation failures → Field-specific errors reported with paths
- All failures prevent project creation (atomic import)

## Version Compatibility

**Backward Compatibility** (Guaranteed):
- Newer application versions can import exports from older versions
- Missing fields are treated as optional or get default values
- New fields in current schema are not required for old exports

**Forward Compatibility** (Not Guaranteed):
- Older application versions may not import exports from newer versions
- New field types may not be recognized by older versions
- New validation rules may cause old importers to reject data

**Compatibility Matrix** (v1.0):
| Export Version | Import Version | Compatibility |
|----------------|----------------|---------------|
| 1.0            | 1.0            | Full          |
| 1.0            | 1.1+           | Full          |
| 1.1            | 1.0            | Partial*      |

*Partial: Import succeeds with warnings if new fields are optional; fails if new fields are required.

## Example: Complete Export

```json
{
  "format_version": "1.0",
  "metadata": {
    "project_id": "a1b2c3d4-1234-5678-1234-567812345678",
    "project_name": "Downtown Site Investigation",
    "created_at": "2026-01-20T10:00:00Z",
    "modified_at": "2026-01-21T14:30:00Z",
    "app_version": "1.0.0",
    "exported_at": "2026-01-21T15:00:00Z",
    "exported_by": "Doc Helper 1.0.0"
  },
  "schema": {
    "entities": [
      {
        "id": "project",
        "name": "Project Information",
        "description": "Main project data",
        "entity_type": "SINGLETON"
      }
    ],
    "fields": [
      {
        "id": "site_location",
        "entity_id": "project",
        "label": "Site Location",
        "field_type": "TEXT",
        "required": true,
        "validation_rules": {
          "min_length": 5,
          "max_length": 200
        }
      },
      {
        "id": "owner_name",
        "entity_id": "project",
        "label": "Owner Name",
        "field_type": "TEXT",
        "required": false
      }
    ]
  },
  "data": {
    "project": [
      {
        "record_id": "default",
        "fields": {
          "site_location": "123 Main Street, Downtown",
          "owner_name": "John Doe"
        }
      }
    ]
  }
}
```

## Migration Path

**Future Format Changes**:
When the interchange format needs to evolve:

1. **Backward-Compatible Changes** (minor version bump: 1.0 → 1.1):
   - Adding optional fields
   - Adding new entity types
   - Relaxing validation constraints
   - Adding metadata fields

2. **Breaking Changes** (major version bump: 1.0 → 2.0):
   - Removing fields
   - Changing field types
   - Restructuring data organization
   - Tightening validation constraints

**Migration Strategy**:
- Application maintains importers for all supported format versions
- On import, detect format version and route to appropriate importer
- Importers transform old formats to current internal representation
- Export always uses current format version

---

**END OF INTERCHANGE FORMAT SPECIFICATION v1.0**

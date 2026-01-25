# AppType Author Guide

**Version**: v2 Platform (Phase 4 Complete)
**Date**: 2026-01-22
**Status**: Stable - Contracts Frozen

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [AppType Concepts](#2-apptype-concepts)
3. [Getting Started](#3-getting-started)
4. [Manifest File](#4-manifest-file)
5. [Schema Definition](#5-schema-definition)
6. [Templates](#6-templates)
7. [Platform Contracts](#7-platform-contracts)
8. [Best Practices](#8-best-practices)
9. [Testing Your AppType](#9-testing-your-apptype)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Introduction

### What is an AppType?

An **AppType** is a self-contained package that defines a document generation workflow for Doc Helper. Each AppType specifies:

- **Document schema**: What data needs to be collected (fields, entities, validation rules)
- **Templates**: Word/Excel/PDF templates for document generation
- **Metadata**: Name, version, description, capabilities

### Built-in AppTypes

Doc Helper ships with one built-in AppType:

- **`soil_investigation`**: Soil investigation reports and geotechnical analysis

### Why Create a Custom AppType?

Create a custom AppType when you need to generate documents with a different structure or workflow than the built-in AppTypes support. Examples:

- Structural engineering reports
- Environmental impact assessments
- Quality control checklists
- Laboratory test reports
- Inspection reports

---

## 2. AppType Concepts

### 2.1 AppType Package Structure

Each AppType is a folder containing:

```
app_types/
└── my_custom_app/          # AppType ID (must be unique)
    ├── manifest.json        # AppType metadata and capabilities
    ├── config.db            # Schema definition (SQLite database)
    └── templates/           # Document templates
        ├── default.docx     # Default Word template
        ├── report.xlsx      # Optional Excel template
        └── cover.pdf        # Optional PDF template
```

### 2.2 AppType Lifecycle

1. **Discovery**: Platform scans `app_types/` folder for `manifest.json` files
2. **Registration**: AppType metadata registered in `AppTypeRegistry`
3. **Selection**: User selects AppType when creating a new project
4. **Validation**: Platform validates AppType constraints (naming, version, schema)
5. **Usage**: Project bound to AppType for its lifetime

### 2.3 Key Constraints

- **AppType ID Format**: `^[a-z][a-z0-9_]*$` (lowercase, start with letter, alphanumeric + underscore)
- **Version Format**: Semantic versioning `X.Y.Z` (e.g., `1.0.0`, `2.3.14`)
- **Immutability**: AppType ID cannot change after projects are created

---

## 3. Getting Started

### Step 1: Create AppType Folder

```bash
cd app_types/
mkdir my_custom_app
cd my_custom_app
```

### Step 2: Create Manifest File

Create `manifest.json`:

```json
{
  "metadata": {
    "app_type_id": "my_custom_app",
    "name": "My Custom App",
    "version": "1.0.0",
    "description": "Custom document generation for my workflow",
    "author": "Your Name",
    "homepage": "https://example.com/my-custom-app"
  },
  "schema": {
    "source": "config.db",
    "schema_type": "sqlite"
  },
  "templates": {
    "default_template": "templates/default.docx"
  },
  "capabilities": {
    "supported_formats": ["word", "excel", "pdf"],
    "requires_formulas": true,
    "requires_validation": true
  }
}
```

### Step 3: Create Schema Database

Copy the reference schema from `soil_investigation`:

```bash
cp ../soil_investigation/config.db ./config.db
```

Then customize using the schema editor (see [Section 5](#5-schema-definition)).

### Step 4: Create Templates

Create `templates/` folder and add at least one Word template:

```bash
mkdir templates
# Add your default.docx template
```

### Step 5: Test Discovery

Launch Doc Helper and verify your AppType appears in the New Project dialog.

---

## 4. Manifest File

### 4.1 Complete Manifest Structure

```json
{
  "metadata": {
    "app_type_id": "my_custom_app",      // REQUIRED: Unique ID (^[a-z][a-z0-9_]*$)
    "name": "My Custom App",             // REQUIRED: Display name
    "version": "1.0.0",                  // REQUIRED: Semantic version (X.Y.Z)
    "description": "...",                // REQUIRED: Short description
    "author": "Your Name",               // OPTIONAL: Author name
    "homepage": "https://...",           // OPTIONAL: Project homepage
    "license": "MIT",                    // OPTIONAL: License identifier
    "tags": ["engineering", "reports"]   // OPTIONAL: Search tags
  },
  "schema": {
    "source": "config.db",               // REQUIRED: Relative path to schema DB
    "schema_type": "sqlite"              // REQUIRED: Must be "sqlite"
  },
  "templates": {
    "default_template": "templates/default.docx",  // REQUIRED: Default template
    "available_templates": [             // OPTIONAL: Additional templates
      {
        "id": "detailed",
        "name": "Detailed Report",
        "path": "templates/detailed.docx",
        "description": "Full report with all sections"
      },
      {
        "id": "summary",
        "name": "Executive Summary",
        "path": "templates/summary.docx",
        "description": "High-level summary only"
      }
    ]
  },
  "capabilities": {
    "supported_formats": ["word", "excel", "pdf"],  // REQUIRED: Output formats
    "requires_formulas": true,                      // Does schema use formulas?
    "requires_validation": true,                    // Does schema use validation?
    "requires_controls": false,                     // Does schema use control rules?
    "requires_overrides": false,                    // Does workflow use overrides?
    "min_platform_version": "2.0.0"                 // Minimum Doc Helper version
  }
}
```

### 4.2 Validation Rules

The platform validates:

1. **app_type_id**:
   - Must match regex `^[a-z][a-z0-9_]*$`
   - Must be unique across all AppTypes
   - Cannot contain uppercase, spaces, hyphens, or special characters
   - Examples: ✅ `soil_investigation`, `structural_report`, `report_v2`
   - Examples: ❌ `Soil-Investigation`, `soil investigation`, `123_report`

2. **version**:
   - Must follow semantic versioning: `X.Y.Z`
   - Each component must be a non-negative integer
   - Prerelease tags allowed: `1.0.0-beta`, `2.0.0-rc.1`
   - Examples: ✅ `1.0.0`, `2.3.14`, `1.0.0-beta`
   - Examples: ❌ `v1.0.0`, `1.0`, `beta-1.0.0`

3. **name**:
   - Must not be empty
   - Maximum 100 characters
   - Display-friendly (can contain spaces, uppercase, etc.)

4. **schema.source**:
   - Must be a valid relative path
   - Must point to an existing SQLite database
   - Path is relative to AppType folder

5. **templates.default_template**:
   - Must be a valid relative path
   - Must point to an existing file
   - Must have `.docx` extension (Word format)

6. **capabilities.supported_formats**:
   - Must be a non-empty array
   - Each format must be one of: `"word"`, `"excel"`, `"pdf"`

---

## 5. Schema Definition

### 5.1 Schema Database Structure

The `config.db` file is a SQLite database containing:

**Tables:**
- `entities`: Entity definitions (e.g., ProjectInfo, Borehole, TestResult)
- `fields`: Field definitions with types, validation, options
- `relationships`: Parent-child relationships between entities
- `validation_rules`: Field-level validation constraints
- `field_options`: Dropdown/radio options
- `dropdowns`: Shared dropdown definitions
- `dropdown_options`: Options for shared dropdowns
- `formulas`: Formula definitions for calculated fields
- `control_relations`: Inter-field control rules
- `output_mappings`: Field → Template mapping

### 5.2 Creating Your Schema

**Option A: Use Schema Editor UI** (Recommended)

1. Launch Doc Helper
2. Open `File → Schema Editor`
3. Create entities, fields, relationships
4. Define validation rules, formulas, controls
5. Save schema to your AppType's `config.db`

**Option B: Copy and Modify Existing Schema**

1. Copy `soil_investigation/config.db` to your AppType folder
2. Modify using SQLite browser or schema editor
3. Remove unnecessary entities/fields
4. Update field labels, validation rules, formulas

**Option C: Generate from Code**

See `tests/unit/domain/test_entity_definition.py` for examples of programmatically creating schema.

### 5.3 Field Types

Doc Helper supports 12 field types:

| Field Type | Description | Example Use Case |
|------------|-------------|------------------|
| `TEXT` | Single-line text | Name, title, reference number |
| `TEXTAREA` | Multi-line text | Description, notes, observations |
| `NUMBER` | Numeric input | Depth, diameter, quantity |
| `DATE` | Date picker | Test date, inspection date |
| `DROPDOWN` | Single selection from list | Soil type, test method |
| `CHECKBOX` | Boolean yes/no | Include appendix, requires signature |
| `RADIO` | Single selection (radio buttons) | Report type, severity level |
| `CALCULATED` | Formula-driven (read-only) | Total depth, average value |
| `LOOKUP` | Value from another entity | Borehole name in test result |
| `FILE` | File attachment | Photos, PDF scans |
| `IMAGE` | Image with preview | Site photos, charts |
| `TABLE` | Nested child entity | Boreholes in project, tests in borehole |

### 5.4 Validation Constraints

**Text Fields:**
- `min_length`, `max_length`: Character limits
- `pattern`: Regex pattern (e.g., `^[A-Z0-9-]+$` for reference numbers)
- `required`: Must not be empty

**Number Fields:**
- `min_value`, `max_value`: Numeric range
- `integer_only`: Disallow decimals
- `required`: Must not be empty

**Date Fields:**
- `min_date`, `max_date`: Date range
- `allow_future`: Allow future dates
- `allow_past`: Allow past dates
- `required`: Must not be empty

### 5.5 Formulas

Formula syntax: `{{field_id}}` for field references

**Example formulas:**

```sql
-- Simple arithmetic
total_depth = {{top_depth}} + {{bottom_depth}}

-- Conditional logic
status = if_else({{test_result}} > 50, "PASS", "FAIL")

-- String concatenation
full_name = concat({{first_name}}, " ", {{last_name}})

-- Aggregation (from child entity)
total_samples = sum({{boreholes.sample_count}})
```

**Allowed functions:**
- Math: `abs`, `min`, `max`, `round`, `sum`, `pow`
- String: `upper`, `lower`, `strip`, `concat`
- Logic: `if_else`, `is_empty`, `coalesce`

### 5.6 Control Rules

Control rules define inter-field dependencies:

**VALUE_SET**: When field A changes, auto-set field B
```sql
-- When soil_type = "Clay", set plasticity_test = "Required"
source_field: soil_type
target_field: plasticity_test
effect_type: VALUE_SET
condition: Clay
target_value: Required
```

**VISIBILITY**: Show/hide field based on another field
```sql
-- Only show contamination_details if contamination_detected = true
source_field: contamination_detected
target_field: contamination_details
effect_type: VISIBILITY
condition: true
```

**ENABLE**: Enable/disable field based on condition
```sql
-- Only enable manual_override_value if override_mode = "Manual"
source_field: override_mode
target_field: manual_override_value
effect_type: ENABLE
condition: Manual
```

---

## 6. Templates

### 6.1 Word Templates

Word templates use **Content Controls** for field mapping.

**Creating a Word Template:**

1. Open Microsoft Word
2. Insert Developer Tab (File → Options → Customize Ribbon → Developer)
3. Use `Developer → Controls → Plain Text Content Control` for fields
4. Set content control **Tag** property to match field ID

**Example:**

```
Field ID in schema: project_name
Content Control Tag: project_name
```

**Content Control Properties:**
- **Title**: Display name (shown in Word)
- **Tag**: Field ID (must match schema) ⚠️ CRITICAL
- **Locking**: Lock content control (optional)

**Best Practices:**
- Use descriptive titles for user clarity
- Tags must exactly match field IDs (case-sensitive)
- Test template with sample data before finalizing

### 6.2 Excel Templates

Excel templates use **cell markers** for field mapping.

**Syntax:**

```
{{field_id}}         # Single value
{{entity.field_id}}  # Field from child entity
```

**Example:**

| A | B | C |
|---|---|---|
| Project Name | {{project_name}} | |
| Date | {{inspection_date}} | |
| Borehole | Depth | Samples |
| {{boreholes.name}} | {{boreholes.depth}} | {{boreholes.sample_count}} |

**Repeated Rows:**
- For TABLE fields, the platform automatically repeats rows
- First data row defines the template
- Subsequent rows are inserted for each record

### 6.3 PDF Templates

PDF templates support:

1. **Overlay mode**: Add stamps/signatures to generated Word → PDF
2. **Form filling** (future): Fill PDF form fields

**Creating Overlay Template:**

1. Create blank PDF or use existing letterhead
2. Define stamp/signature positions in manifest
3. Platform overlays images at specified coordinates

**Example manifest:**

```json
{
  "pdf_overlay": {
    "stamp": {
      "path": "resources/assets/stamp.png",
      "page": 1,
      "x": 400,
      "y": 700,
      "scale": 0.5,
      "rotation": 0
    },
    "signature": {
      "path": "resources/assets/signature.png",
      "page": -1,  // Last page
      "x": 100,
      "y": 50,
      "scale": 0.3,
      "rotation": 0
    }
  }
}
```

---

## 7. Platform Contracts

### 7.1 AppType Registration Contract

**What the platform expects:**

1. **Unique app_type_id**: No duplicates across all AppTypes
2. **Valid manifest.json**: Passes JSON schema validation
3. **Accessible config.db**: SQLite database at specified path
4. **At least one template**: default_template must exist and be valid
5. **Backward compatibility**: Schema changes must not break existing projects

### 7.2 Schema Contract

**What the platform expects:**

1. **Root entity**: At least one entity with `is_root_entity = true`
2. **Valid field types**: All fields use one of the 12 supported types
3. **No circular dependencies**: Formulas and relationships must be acyclic
4. **Valid formulas**: All formula references resolve to existing fields
5. **Valid control rules**: Control chains do not exceed depth 10

### 7.3 Project Lifecycle Contract

**Invariants the platform enforces:**

1. **AppType immutability**: Project's app_type_id never changes after creation
2. **AppType availability**: Cannot open project if AppType not registered
3. **AppType validation**: All project creation/import/open paths validate app_type_id

**What happens when AppType is uninstalled:**

- Existing projects with that AppType **cannot be opened**
- Platform shows error: `AppType 'X' not found. Available AppTypes: Y, Z.`
- User must reinstall AppType to open projects

### 7.4 Validation Contract

**Platform validates at three points:**

1. **Manifest validation** (on discovery):
   - JSON structure matches schema
   - app_type_id format valid
   - version format valid
   - Paths resolve to existing files

2. **Schema validation** (on project creation):
   - All field types are supported
   - Formulas reference existing fields
   - Control rules do not form cycles
   - Root entity exists

3. **AppType existence** (on project open/import):
   - app_type_id exists in registry
   - Platform version meets min_platform_version

---

## 8. Best Practices

### 8.1 Naming Conventions

**AppType IDs:**
- ✅ Use descriptive names: `soil_investigation`, `structural_report`
- ✅ Include domain: `qa_checklist`, `lab_test_report`
- ❌ Avoid generic names: `app1`, `custom`, `report`
- ❌ Don't use abbreviations unless widely known: `si_report` (unclear)

**Entity Names:**
- ✅ Singular nouns: `Borehole`, `TestResult`, `Observation`
- ✅ PascalCase (schema editor convention)
- ❌ Plural: `Boreholes` (use `Borehole` with `is_collection = true`)

**Field IDs:**
- ✅ snake_case: `project_name`, `test_date`, `soil_type`
- ✅ Descriptive: `contamination_detected`, `sample_depth_meters`
- ❌ Abbreviations: `cont_det`, `smp_dp_m`

**Field Labels (User-Facing):**
- ✅ Display-friendly: "Project Name", "Test Date", "Soil Type"
- ✅ Include units: "Depth (meters)", "Pressure (kPa)"
- ✅ Use translation keys for i18n: `field.project_name`

### 8.2 Schema Design

**Normalize entities:**
- ✅ One entity per concept: `Borehole`, `SoilSample`, `TestResult`
- ❌ Don't flatten: `borehole_1_name`, `borehole_2_name` (use TABLE field)

**Use appropriate field types:**
- ✅ DROPDOWN for 5-20 options
- ✅ RADIO for 2-5 exclusive options
- ✅ CHECKBOX for yes/no flags
- ✅ CALCULATED for derived values
- ❌ Don't use TEXT for structured data (dates, numbers)

**Validation rules:**
- ✅ Mark critical fields as required
- ✅ Set realistic min/max constraints
- ✅ Use regex patterns for structured text (reference numbers, codes)
- ❌ Don't over-validate: Allow flexibility where needed

**Formula complexity:**
- ✅ Simple arithmetic and logic
- ✅ Break complex formulas into intermediate calculated fields
- ❌ Avoid deeply nested formulas (hard to debug)

### 8.3 Template Design

**Word templates:**
- ✅ Use styles for consistent formatting
- ✅ Test with maximum expected data volume
- ✅ Include headers/footers with page numbers
- ❌ Don't hardcode values that should be fields

**Excel templates:**
- ✅ Use cell markers for all variable data
- ✅ Format cells appropriately (numbers, dates, text)
- ✅ Use formulas for Excel-side calculations (not just Doc Helper formulas)
- ❌ Don't merge cells in table data regions (breaks row repetition)

**PDF overlays:**
- ✅ Test stamp/signature positions with different page layouts
- ✅ Use transparent PNGs for clean overlays
- ❌ Don't use large images (slow generation, large file sizes)

### 8.4 Version Management

**Semantic versioning:**
- **MAJOR (X.0.0)**: Breaking changes (schema structure changes)
- **MINOR (0.X.0)**: New features (new fields, new templates)
- **PATCH (0.0.X)**: Bug fixes (fix validation rules, update labels)

**Backward compatibility:**
- ✅ Add new fields (projects without them still work)
- ✅ Add new templates (existing projects use old default)
- ✅ Relax validation (more permissive)
- ❌ Don't remove fields (breaks existing projects)
- ❌ Don't rename fields (breaks templates and formulas)
- ❌ Don't tighten validation (existing projects may fail)

**Migration strategy (future):**
- v2+ platform will support schema migrations
- For now, create new AppType version if breaking changes needed

### 8.5 Testing

**Before releasing your AppType:**

1. **Discovery test**: Verify AppType appears in New Project dialog
2. **Creation test**: Create project, fill all field types
3. **Validation test**: Trigger validation errors, verify messages clear
4. **Formula test**: Change dependent fields, verify formulas update
5. **Control test**: Trigger control rules, verify effects apply
6. **Template test**: Generate documents, verify all fields populate
7. **Save/Load test**: Save project, close, reopen, verify data preserved
8. **Import/Export test**: Export project, import in fresh instance

**Use platform stability tests:**

See `tests/unit/platform/test_platform_stability.py` for examples:
- Test with corrupt app_type_id values (SQL injection, path traversal)
- Test with missing AppType at project open
- Test with invalid manifest formats

---

## 9. Testing Your AppType

### 9.1 Manual Testing Checklist

**AppType Discovery:**
- [ ] AppType appears in New Project dialog
- [ ] Name, description, version display correctly
- [ ] Icon/thumbnail displays (if provided)

**Project Creation:**
- [ ] Can create new project with your AppType
- [ ] All entities appear in navigation
- [ ] All fields render with correct widgets
- [ ] Validation rules trigger appropriately

**Data Entry:**
- [ ] All 12 field types work correctly
- [ ] Dropdown options populate
- [ ] Date picker shows valid dates
- [ ] File fields accept uploads
- [ ] Table fields allow add/edit/delete rows

**Formulas:**
- [ ] Calculated fields update on dependency change
- [ ] Formula errors show clear messages
- [ ] Circular dependencies detected and blocked

**Controls:**
- [ ] VALUE_SET rules auto-populate fields
- [ ] VISIBILITY rules show/hide fields
- [ ] ENABLE rules enable/disable fields
- [ ] Control chains propagate correctly

**Document Generation:**
- [ ] Word template populates all fields
- [ ] Excel template repeats table rows correctly
- [ ] PDF overlay applies stamps/signatures
- [ ] Generated documents open without errors

**Save/Load:**
- [ ] Project saves without errors
- [ ] Reopening project restores all data
- [ ] Recent projects list shows project

**Import/Export:**
- [ ] Export creates valid JSON interchange file
- [ ] Import from JSON recreates project correctly
- [ ] Warnings for missing fields display

### 9.2 Automated Testing

**Platform-level tests** (all AppTypes):

```bash
# Run platform stability tests
pytest tests/unit/platform/test_platform_stability.py

# Run AppType lifecycle tests
pytest tests/integration/test_apptype_lifecycle_enforcement.py

# Run multi-AppType discovery tests
pytest tests/integration/platform/test_multi_apptype_discovery.py
```

**AppType-specific tests** (create your own):

Example test structure:

```python
# tests/integration/apptypes/test_my_custom_app.py
from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
    SqliteSchemaRepository,
)

def test_my_custom_app_discovery():
    """Test: my_custom_app is discovered and registered."""
    discovery = AppTypeDiscoveryService()
    manifests = discovery.discover()

    my_app = next((m for m in manifests if m.metadata.app_type_id == "my_custom_app"), None)
    assert my_app is not None
    assert my_app.metadata.name == "My Custom App"
    assert my_app.metadata.version == "1.0.0"

def test_my_custom_app_schema_valid():
    """Test: config.db has valid schema structure."""
    schema_repo = SqliteSchemaRepository("app_types/my_custom_app/config.db")

    entities = schema_repo.get_all()
    assert entities.is_success()

    # Verify root entity exists
    root_entities = [e for e in entities.value if e.is_root_entity]
    assert len(root_entities) >= 1

def test_my_custom_app_template_valid():
    """Test: default.docx template exists and is valid."""
    template_path = Path("app_types/my_custom_app/templates/default.docx")

    assert template_path.exists()

    # Verify it's a valid Word document
    adapter = WordDocumentAdapter()
    validation = adapter.validate_template(template_path)
    assert validation.is_success()
```

---

## 10. Troubleshooting

### 10.1 Common Issues

#### Issue: AppType not appearing in New Project dialog

**Possible causes:**
1. `manifest.json` invalid JSON syntax
2. `app_type_id` violates naming rules (uppercase, spaces, hyphens)
3. `version` not semantic versioning format
4. `schema.source` path incorrect (relative to AppType folder)
5. AppType folder not in `app_types/` directory

**Solution:**
- Validate JSON syntax: `python -m json.tool manifest.json`
- Check app_type_id regex: `^[a-z][a-z0-9_]*$`
- Check version regex: `^\d+\.\d+\.\d+`
- Verify `config.db` exists at specified path
- Run platform with debug logging: `--log-level DEBUG`

#### Issue: "AppType 'X' not found" when opening project

**Cause:** AppType was unregistered or removed from `app_types/` folder.

**Solution:**
1. Verify AppType folder exists in `app_types/`
2. Verify `manifest.json` is valid
3. Restart Doc Helper to re-trigger discovery
4. Check logs for registration errors

#### Issue: Schema validation errors on project creation

**Possible causes:**
1. Circular dependencies in formulas
2. Control rules form cycles (A → B → A)
3. Formula references non-existent field
4. Invalid field type in `config.db`

**Solution:**
- Run schema validator: Check formula dependency graph for cycles
- Review control rules: Ensure no bidirectional mappings
- Verify all formula `{{field_id}}` references exist in schema
- Check `fields.field_type` column matches supported types

#### Issue: Template fields not populating

**Possible causes:**
1. Content control tags don't match field IDs (case-sensitive)
2. Field ID typo in template
3. Field value is NULL (no default, no user input)

**Solution:**
- Open Word template, check content control properties (Developer → Properties)
- Verify tag exactly matches field ID in schema
- Use `{{field_id}}` syntax in Excel templates (not just `field_id`)
- Set default values in schema for optional fields

#### Issue: Formula not updating

**Possible causes:**
1. Dependency field not triggering recalculation
2. Formula syntax error (missing `{{}}`, invalid function)
3. Circular dependency detected (formula disabled)

**Solution:**
- Check formula evaluation logs
- Verify all dependencies use `{{field_id}}` syntax
- Test formula in isolation with dummy values
- Use allowed functions only (abs, min, max, round, etc.)

### 10.2 Debugging Tools

**Platform Debug Mode:**

```bash
# Run with debug logging
python -m doc_helper --log-level DEBUG

# Check logs for:
# - AppType discovery events
# - Manifest validation errors
# - Schema loading errors
# - Template validation warnings
```

**SQLite Schema Inspection:**

```bash
# Open config.db in SQLite browser
sqlite3 app_types/my_custom_app/config.db

# Inspect tables
.tables
.schema entities
.schema fields

# Query entities
SELECT id, name, is_root_entity FROM entities;

# Query fields
SELECT entity_id, field_id, field_type, required FROM fields;

# Query formulas
SELECT field_id, formula_expression FROM formulas;
```

**Manifest Validation:**

```bash
# Validate JSON syntax
python -m json.tool manifest.json

# Pretty-print
python -c "import json; print(json.dumps(json.load(open('manifest.json')), indent=2))"
```

### 10.3 Support Resources

**Platform Documentation:**
- [plan.md](plan.md): Full platform architecture and design
- [AGENT_RULES.md](AGENT_RULES.md): Development rules and constraints
- [V2_PLATFORM_ENFORCEMENT_GAPS_ANALYSIS.md](V2_PLATFORM_ENFORCEMENT_GAPS_ANALYSIS.md): Validation enforcement

**Test Examples:**
- [tests/unit/platform/](tests/unit/platform/): Platform stability tests
- [tests/integration/platform/](tests/integration/platform/): Multi-AppType tests
- [tests/integration/test_apptype_lifecycle_enforcement.py](tests/integration/test_apptype_lifecycle_enforcement.py): AppType lifecycle

**Reference AppType:**
- [app_types/soil_investigation/](app_types/soil_investigation/): Complete working example
- Use as template for your custom AppType

**Issue Reporting:**
- GitHub Issues: https://github.com/your-org/doc-helper/issues
- Include: AppType manifest, schema dump, error logs, steps to reproduce

---

## Appendix A: Manifest JSON Schema

Complete JSON schema for validation:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["metadata", "schema", "templates", "capabilities"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["app_type_id", "name", "version", "description"],
      "properties": {
        "app_type_id": {
          "type": "string",
          "pattern": "^[a-z][a-z0-9_]*$",
          "description": "Unique identifier (lowercase, alphanumeric + underscore)"
        },
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Display name"
        },
        "version": {
          "type": "string",
          "pattern": "^\\d+\\.\\d+\\.\\d+",
          "description": "Semantic version (X.Y.Z)"
        },
        "description": {
          "type": "string",
          "minLength": 1,
          "maxLength": 500,
          "description": "Short description"
        },
        "author": {
          "type": "string",
          "description": "Author name (optional)"
        },
        "homepage": {
          "type": "string",
          "format": "uri",
          "description": "Project homepage URL (optional)"
        },
        "license": {
          "type": "string",
          "description": "License identifier (optional)"
        },
        "tags": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Search tags (optional)"
        }
      }
    },
    "schema": {
      "type": "object",
      "required": ["source", "schema_type"],
      "properties": {
        "source": {
          "type": "string",
          "description": "Relative path to schema database"
        },
        "schema_type": {
          "type": "string",
          "enum": ["sqlite"],
          "description": "Schema database type (must be sqlite)"
        }
      }
    },
    "templates": {
      "type": "object",
      "required": ["default_template"],
      "properties": {
        "default_template": {
          "type": "string",
          "description": "Relative path to default Word template (.docx)"
        },
        "available_templates": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "name", "path"],
            "properties": {
              "id": {"type": "string"},
              "name": {"type": "string"},
              "path": {"type": "string"},
              "description": {"type": "string"}
            }
          },
          "description": "Additional templates (optional)"
        }
      }
    },
    "capabilities": {
      "type": "object",
      "required": ["supported_formats"],
      "properties": {
        "supported_formats": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["word", "excel", "pdf"]
          },
          "minItems": 1,
          "description": "Output formats supported"
        },
        "requires_formulas": {
          "type": "boolean",
          "description": "Does schema use formulas?"
        },
        "requires_validation": {
          "type": "boolean",
          "description": "Does schema use validation?"
        },
        "requires_controls": {
          "type": "boolean",
          "description": "Does schema use control rules?"
        },
        "requires_overrides": {
          "type": "boolean",
          "description": "Does workflow use overrides?"
        },
        "min_platform_version": {
          "type": "string",
          "pattern": "^\\d+\\.\\d+\\.\\d+",
          "description": "Minimum Doc Helper version"
        }
      }
    }
  }
}
```

---

## Appendix B: Quick Reference

### AppType ID Format

```
^[a-z][a-z0-9_]*$

✅ soil_investigation
✅ structural_report
✅ report_v2
✅ qa_checklist_2024

❌ Soil_Investigation    (uppercase)
❌ soil-investigation    (hyphen)
❌ soil investigation    (space)
❌ 123_report            (starts with number)
❌ _soil_investigation   (starts with underscore)
```

### Version Format

```
^\\d+\\.\\d+\\.\\d+

✅ 1.0.0
✅ 2.3.14
✅ 0.1.0
✅ 1.0.0-beta       (prerelease tag allowed)
✅ 2.0.0-rc.1       (release candidate)

❌ v1.0.0            (prefix)
❌ 1.0               (missing patch)
❌ 1                 (only major)
❌ beta-1.0.0        (doesn't start with X.Y.Z)
```

### Supported Field Types

```
TEXT, TEXTAREA, NUMBER, DATE, DROPDOWN, CHECKBOX, RADIO,
CALCULATED, LOOKUP, FILE, IMAGE, TABLE
```

### Supported Output Formats

```
word, excel, pdf
```

### Allowed Formula Functions

```
abs, min, max, round, sum, pow,          # Math
upper, lower, strip, concat,             # String
if_else, is_empty, coalesce              # Logic
```

---

**End of AppType Author Guide**

For questions or support, see [Section 10.3](#103-support-resources).

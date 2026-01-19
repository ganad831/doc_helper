# Doc Helper: Comprehensive Rebuild Plan

## 1. PROJECT IDENTITY

**Name**: Doc Helper

**Purpose**: A document generation platform designed to automate the creation of professional documents from structured data. Built with Clean Architecture and Domain-Driven Design principles for maintainability, testability, and extensibility.

**v1 Scope**: Single document type support (Soil Investigation Reports)
- Focused on delivering a solid, production-ready implementation for one document type
- All core features fully implemented and tested
- Foundation designed for future extensibility

**v2+ Vision**: Universal multi-document-type platform
- Support for multiple document types (structural reports, environmental assessments, etc.)
- Plugin-style architecture with app type discovery
- Extensible transformer system for custom document types
- See [ADR-013: Multi-Document-Type Platform Vision](adrs/ADR-013-multi-app-type-platform-vision.md) for details

---

## 2. v1 DEFINITION OF DONE

**Minimum Usable Doc Helper v1**:

1. **Create/Open/Save/Close** a Soil Investigation project
2. **Dynamic form rendering** from schema (config.db)
3. **All 12 field types** working with validation (see frozen list below)
4. **Formula evaluation** with dependency tracking
5. **Control system** (VALUE_SET, VISIBILITY, ENABLE)
6. **Override system** with state machine (PENDING → ACCEPTED → SYNCED)
7. **Document generation** (see priority below)
8. **Transformer system** (all 15+ built-in transformers)
9. **Undo/Redo** for field value changes only (see scope below)
10. **Recent projects** tracking
11. **Internationalization (i18n)** with multi-language support (English, Arabic) and RTL layout

### Document Adapter Priority (v1)

| Priority | Adapter | Description |
|----------|---------|-------------|
| **Primary** | Word (.docx) | Content control mapping, full support |
| Secondary | Excel (.xlsx) | Cell mapping, formula preservation |
| Secondary | PDF | Stamp/signature overlay on generated Word |

Word generation is the core deliverable. Excel and PDF are included in v1 but may have fewer edge cases handled.

### Undo/Redo Scope (v1)

**Included**:
- Field value changes (user edits)
- Formula-computed value acceptance
- Override state changes

**NOT included**:
- File operations (save, open, close)
- Document generation
- Project creation/deletion

### 12 Field Types (FROZEN for v1)

| # | Field Type | Description |
|---|------------|-------------|
| 1 | `TEXT` | Single-line text input |
| 2 | `TEXTAREA` | Multi-line text input |
| 3 | `NUMBER` | Numeric input with optional decimals |
| 4 | `DATE` | Date picker |
| 5 | `DROPDOWN` | Single selection from options |
| 6 | `CHECKBOX` | Boolean true/false |
| 7 | `RADIO` | Single selection (radio buttons) |
| 8 | `CALCULATED` | Formula-driven read-only value |
| 9 | `LOOKUP` | Value from another entity/record |
| 10 | `FILE` | File attachment reference |
| 11 | `IMAGE` | Image attachment with preview |
| 12 | `TABLE` | Nested tabular data (child records) |

**FROZEN**: No new field types will be added in v1. Any new types are v2+.

---

**NOT in v1**:
- Multiple app types
- App type selection UI
- Dark mode
- Auto-save
- Field history viewing
- Quick search
- Import from Excel
- Export project data
- Clone project
- Document version history

---

## 3. FEATURES BY DOMAIN (v1 Scope)

### 3.1 Project Management
- **Create New Project**: Initialize project with default Soil Investigation schema
- **Open Existing Project**: Browse filesystem → validate project.db → restore navigation state
- **Save Project**: Persist all form data to SQLite database
- **Close Project**: Prompt for unsaved changes → return to welcome screen
- **Recent Projects**: Track last 5 projects with quick-reopen functionality
- **Project Lifecycle**: Welcome screen → Edit → Generate → Export → Close

**Note**: v1 supports only Soil Investigation reports. Multi-app-type selection is a v2+ feature (see [ADR-013](adrs/ADR-013-multi-app-type-platform-vision.md)).

### 3.2 Dynamic Form System
- **Schema-Driven UI**: Forms generated at runtime from database schema
- **12 Field Types**: TEXT, TEXTAREA, NUMBER, DATE, DROPDOWN, CHECKBOX, RADIO, CALCULATED, LOOKUP, FILE, IMAGE, TABLE
- **Entity Types**: SINGLETON (single record like project_info) or COLLECTION (multiple records like boreholes)
- **Tab Navigation**: Dynamic tabs built from schema with back/forward history
- **Field Grouping**: Collapsible groups within tabs

### 3.3 Validation System
- **Required Fields**: Block generation if required fields empty
- **Numeric Validation**: min_value, max_value, integer_only constraints
- **Text Validation**: min_length, max_length, regex patterns
- **Date Validation**: min_date, max_date, allow_future, allow_past
- **Real-Time Feedback**: Validation as user types with visual indicators
- **Form-Wide Validity**: Track overall form validity status

### 3.4 Formula System
- **Computed Fields**: Auto-calculated values using template syntax `{{field_id}}`
- **Dependency Tracking**: Automatic updates when dependencies change
- **Safe Evaluation**: Restricted eval() with allowed functions (abs, min, max, round, etc.)
- **Cross-Tab References**: Formulas can reference fields from any tab
- **Formula Modes**: AUTO (system computed), MANUAL (user override), CUSTOM

### 3.5 Control System (Inter-Field Dependencies)
- **VALUE_SET**: When field A changes, auto-set field B
- **VISIBILITY**: Show/hide fields based on another field's value
- **ENABLE/DISABLE**: Enable/disable fields based on conditions
- **OPTIONS_FILTER**: Filter dropdown options based on another field
- **Chain Evaluation**: A→B→C propagation with cycle detection (max depth: 10)

### 3.6 Override System
- **User Edits from Word**: Track differences between system values and Word document values
- **State Machine**: PENDING → ACCEPTED/INVALID → SYNCED → cleanup
- **Conflict Detection**: Multiple different values for same field
- **Override Management Dialog**: Review, accept, revert overrides
- **Formula Override**: Special SYNCED_FORMULA state preserved across iterations

### 3.7 File Management
- **Single/Multiple File Fields**: Configurable file upload widgets
- **Drag-and-Drop**: File drag-drop support
- **File Preview**: Image preview with zoom, PDF preview with pagination
- **Figure Numbering**: Automatic caption numbering with customizable formats
- **Captions**: Figure, Image, Plan, Section, Table, Chart, Appendix types
- **Numbering Formats**: Arabic, Roman, Letter styles
- **Reordering**: Drag-to-reorder for custom figure sequence

### 3.8 Document Generation
- **Word Document Generation**: Populate Word templates with form data
- **Template Selection**: Multiple templates per app type with default
- **Content Control Mapping**: Fields mapped to Word content controls by tag
- **Excel Generation**: Populate Excel templates (xlwings)
- **PDF Export**: Convert to PDF with optional password protection
- **Stamp/Signature Application**: Configurable position, scale, rotation

### 3.9 Transformer System
- **Bidirectional Conversion**: Raw values ↔ Document display values
- **SuffixTransformer**: "5" ↔ "5 جسات" (boreholes)
- **PrefixTransformer**: "100" ↔ "ك م² 100"
- **MapTransformer**: Value mapping (owner_type: "single" → "سيد")
- **TemplateTransformer**: Pattern-based (e.g., "BH-{index}")
- **DateFormatTransformer**: Date formatting
- **ArabicNumberTransformer**: English-to-Arabic numerals
- **ArabicOrdinalTransformer**: Ordinal numbers in Arabic

### 3.10 Schema Editor
- **Entity Management**: Add, edit, delete entities
- **Field Management**: Configure field type, validation, formulas, options
- **Relationship Editor**: Define entity relationships
- **Control Rules**: Configure inter-field dependencies
- **Batch Save**: All changes saved together

**Note**: v1 includes schema editor for modifying the Soil Investigation schema only.

### 3.11 History/Undo System
- **Undo/Redo**: Ctrl+Z/Ctrl+Y for field changes
- **Command Pattern**: SetFieldValueCommand, OverrideCommand
- **Dirty Tracking**: Track unsaved changes

**Note**: Undo/Redo scope is limited in v1 (see section 2). File operations and document generation are NOT undoable.

### 3.12 Internationalization (i18n)
- **Multi-Language Support**: English and Arabic languages
- **Language Switching**: Settings dialog with language selector, no restart required
- **RTL Layout**: Right-to-left layout for Arabic (mirrored navigation, right-aligned text)
- **Translation System**: JSON-based translation files with key-value structure
- **UI Coverage**: All menus, dialogs, buttons, labels, field labels, validation messages, error messages
- **Persisted Preference**: Language choice saved in user config and restored on app launch
- **Dynamic Updates**: UI text and layout direction update immediately on language change

**Note**: v1 includes English and Arabic. Additional languages can be added in v2+ by adding translation files.

---

## 4. BUSINESS RULES

### 4.1 Data Integrity Rules
- Every project must be associated with the Soil Investigation schema (v1: hardcoded, v2+: app_type_id)
- Fields must be unique by ID within an entity
- Formulas cannot have circular dependencies
- Control chains limited to depth 10 to prevent infinite loops
- Override values must pass field validation to be ACCEPTED

### 4.2 Value Resolution Priority
1. **Override value** (if ACCEPTED and should_use_in_generation)
2. **Formula computed value** (if formula field)
3. **Raw value from database**

### 4.3 Validation Rules
- Required fields block report generation if empty
- Numeric fields enforce min/max/integer constraints
- Text fields enforce length and pattern constraints
- Date fields enforce range and past/future constraints

### 4.4 Formula Evaluation Rules
- Dependencies extracted using `{{field_id}}` pattern
- Evaluation order determined by dependency graph
- Only allowed functions: abs, min, max, round, sum, pow, upper, lower, strip, concat, if_else, is_empty, coalesce
- Dependency changes trigger re-evaluation of affected formulas

### 4.5 Control Evaluation Rules
- VALUE_SET: Target field auto-populated when source changes
- VISIBILITY: Target field shown/hidden based on source value
- Exact value match has priority over default mapping
- Chain propagation: When A updates B, check if B has controls too

### 4.6 Override State Transitions
```
[New Override] → PENDING
PENDING + User Accept → ACCEPTED
PENDING + Validation Fail → INVALID
ACCEPTED + Write to Word → SYNCED
SYNCED + Non-Formula → Cleanup (deleted)
SYNCED + Formula → SYNCED_FORMULA (preserved)
```

### 4.7 Naming Rules
- **manual**: User provides name
- **autoincrement**: Sequential 1, 2, 3...
- **pattern**: Template tokens ({YYYY}, {MM}, {DD}, {#}, {##}, etc.)
- **uuid**: Random UUID generation

### 4.8 File Field Rules
- min_files/max_files constraints per field
- Allowed extensions filtering
- Size limits
- Files copied to project directory on save

---

## 5. SIDE EFFECTS & HIDDEN BEHAVIORS

### 5.1 Database Operations

**App Type Config Database (app_types/soil_investigation/config.db)** - v1 only
- Read: Entities, fields, relationships, validation rules, options, formulas, output mappings
- Write: Schema editor changes (entities, fields, relationships, controls)
- Tables: entities, fields, relationships, validation_rules, field_options, dropdowns, dropdown_options, formulas, auto_generate, file_configs, ui_configs, output_mappings, control_relations

**Project Database (Projects/{name}/project.db)**
- Read: Project metadata, entity data, overrides, sequences
- Write: Form data saves, override state changes, sequence increments
- Tables: Dynamic per-schema + metadata, sequences, overrides

**Recent Projects Tracking**
- Read/Write: Recent projects list (last 5 projects)
- Updated on project open/create

### 5.2 File System Operations

**Project Files**
- Create: Project directory structure
- Read: Project.db, attached files
- Write: Save project data, copy uploaded files
- Delete: Orphaned files on cleanup

**Templates**
- Read: Word templates (.docx), Excel templates (.xlsx)
- Located in: app_types/soil_investigation/templates/

**Generated Documents**
- Write: Generated Word documents to project folder
- Write: PDF exports with stamps/signatures

**Configuration Files**
- Read/Write: `config/user_config.json` (includes language preference)
- Read/Write: `config/recent_projects.json`
- Read: `config/excel_ranges.json`, `config/table_columns.json`

**Translation Files** (v1)
- Read: `translations/en.json`, `translations/ar.json`
- Loaded on app startup and language change
- Contains all UI strings (menus, dialogs, buttons, labels, error messages)

**Resources**
- Read: `resources/assets/stamp.png`, `resources/assets/signature.png`

### 5.3 External Library Calls

**xlwings** (Excel)
- Open Excel workbooks
- Read/write cell values
- Auto-fit columns
- Save workbooks

**python-docx** (Word)
- Open Word documents
- Iterate content controls
- Set content control values
- Save documents

**PyMuPDF (fitz)** (PDF)
- Open PDF documents
- Add images (stamps/signatures) at coordinates
- Set password protection
- Save PDF

**Pillow** (Images)
- Read image dimensions
- Thumbnail generation for previews

### 5.4 API Integrations

**Google GenAI** (`services/ai_service.py`)
- AI integration (currently minimal usage in legacy app)
- Potential for AI-assisted report generation (v2+)

### 5.5 Automatic Behaviors
- **Auto-save before generate**: Project saved automatically before report generation
- **Navigation state persistence**: Last tab/position restored on project reopen
- **Tab history**: Back/forward navigation within tabs
- **Thread-local DB connections**: Each thread gets its own SQLite connection
- **PRAGMA settings**: foreign_keys=ON, journal_mode=WAL automatically applied
- **Recent projects auto-update**: On project open/create
- **Language preference persistence** (v1): Selected language saved in user_config.json and restored on app launch
- **Dynamic UI language update** (v1): All UI text and layout direction update immediately on language change (no restart required)

### 5.6 Implicit Data Transformations
- **Row-to-dict conversion**: SQLite rows automatically converted to dictionaries
- **JSON serialization**: Complex types stored as JSON strings in SQLite
- **Transformer application**: Output values automatically transformed before writing to documents

### 5.7 Implicit Cleanup Operations
- **Orphaned file cleanup**: Files not referenced by any field deleted on save
- **SYNCED override cleanup**: Non-formula SYNCED overrides deleted after generation
- **Conflict cleanup**: Resolved conflicts cleared after successful generation

### 5.8 Default Value Resolution
- Empty string defaults for missing text fields
- Zero defaults for missing numeric fields
- None handling throughout for optional fields
- Default transformer returns empty string if field missing

### 5.9 Signal Emissions (Observer Pattern)
- Validation state changes emit signals for UI updates
- History manager emits can_undo/can_redo signals
- Formula changes propagate to dependent fields
- Control evaluations propagate through chains

### 5.10 State Management Side Effects
- **ApplicationState**: Global singleton affects all services (v1: simplified, no multi-app state)
- **ProjectContext**: Per-project state affects field resolution
- **WidgetRegistry**: Widgets register themselves for formula updates

### 5.11 Error Recovery Behaviors
- **CircularDependencyError**: Max depth 10 prevents infinite loops
- **FormulaEvaluationError**: Returns None, doesn't crash
- **ValidationError**: Sets field state to invalid, doesn't block UI
- **DatabaseError**: Wraps SQLite errors with context

### 5.12 Cascade Effects
- Deleting entity cascades to fields, relationships, validations
- Deleting dropdown cascades to all field_options using it
- Changing field type clears incompatible validations/options
- Renaming entity/field updates all references

### 5.13 Implicit File Operations
- Files uploaded but not saved exist in temp location until project save
- Multiple files field tracks order for numbering
- File metadata (dimensions, size) read on upload

### 5.14 Threading Considerations
- Thread-local database connections
- UI operations on main thread only
- Background tasks for long operations (progress dialog)

---

## 6. ARCHITECTURAL PAIN POINTS (Legacy App Diagnosis)

**Context**: These pain points were identified in the legacy application and inform the design decisions for the Doc Helper rebuild (both v1 and v2+).

### 6.1 God Objects (Critical)

| Class | File | Lines | Methods | Problem |
|-------|------|-------|---------|---------|
| **MainWindow** | ui/main_window.py | 2024 | 58 | Handles UI, business logic, project lifecycle, menus, dialogs, state |
| **ProjectContext** | core/state/project_context.py | 862 | 54 | Composes 7 sub-components, duplicates all their interfaces |
| **AppTypeManager** | services/managers/app_type_manager.py | 1147 | 40+ | CRUD, languages, templates, DB pooling, recent projects, config |
| **TransformerRegistry** | core/transformers.py | 1605 | 93 | 16 transformer classes + registry in one file |
| **OverrideStore** | core/overrides/override_store.py | 884 | 45 | State + persistence + validation + history mixed |

### 6.2 Tight Coupling Points

**Core Layer Imports PyQt6** (Critical violation of clean architecture):
```
core/history/field_commands.py      → from PyQt6.QtGui import QUndoCommand
core/history/history_manager.py     → from PyQt6.QtCore import QObject, pyqtSignal
core/state/data_binder.py           → from PyQt6.QtCore import QObject, pyqtSignal, QTimer
core/state/project_context.py       → from PyQt6.QtCore import QObject, pyqtSignal
core/validation/features/*.py       → Multiple PyQt6 imports
```
**Impact**: Core layer cannot be tested without Qt, cannot be reused outside PyQt6 apps.

**MainWindow Constructor** takes 7 concrete service parameters:
```python
def __init__(self, excel_service, word_service, template_engine,
             structure_manager, config_path, recent_manager, app_type_manager)
```

**Bidirectional Dependencies**:
- `services/` imports from `core/state/`, `core/controls/`, `core/formulas/`
- `core/services/` is used by `core/state/`
- Circular dependency risk between layers

### 6.3 SOLID Violations

**Single Responsibility (SRP)**:
- MainWindow: UI + business logic + persistence + file ops + config
- AppTypeManager: CRUD + languages + templates + DB pooling + recent projects
- TemplateEngine: Report generation + file handling + Excel conversion + PDF processing
- ValidationManager: Registration + execution + result tracking + batch ops

**Open/Closed (OCP)**:
- FieldFactory: Hard-coded type→widget mapping (adding field type = modify factory)
- ValidationManager: Hard-coded type→validator selection
- OutputMappingManager: Hard-coded word/excel/pdf methods

**Dependency Inversion (DIP)**:
- AppTypeManager creates DatabaseConnection directly
- MainWindow receives concrete services, not interfaces
- ProjectController fetches from service container instead of constructor injection
- SchemaEditorDialog instantiates FileConfigManager directly

### 6.4 State Management Issues

**Two Competing State Systems**:
1. `ApplicationState` - Global paths, current project path (singleton)
2. `ProjectContext` - Navigation, data binding, validation (singleton)
- Manual sync required between them in MainWindow

**Mutable Shared State**:
- DataBinder has flags (`_suppress_signals`, `_loading`, `_record_history`) that can corrupt state on exceptions
- ProjectContext accumulates state in dictionaries never cleared between projects
- WidgetRegistry uses WeakRef for widgets but strong refs for metadata (leak risk)

**Global Singletons**:
```python
ApplicationState.get_instance()  # Used throughout without DI
get_project_context()            # Global mutable state
```

### 6.5 Layer Mixing

**Business Logic in UI**:
- Widgets call `validate()` themselves
- Widgets evaluate controls when values change
- Field visibility logic in both FieldService AND widget layer

**Domain Classes Know Infrastructure**:
- SchemaManager has direct SQL queries with hardcoded table/column names
- PersistenceService writes raw SQL
- ApplicationState creates filesystem directories

**PyQt6 in Domain Layer**:
- ProjectContext inherits QObject
- DataBinder uses QTimer for debouncing
- HistoryManager wraps QUndoStack
- All signals are pyqtSignal (not framework-agnostic)

---

## 7. ROOT CAUSES & RISKS

### 7.1 Root Causes (Why the Legacy System Became Complex)

**7.1.1 Iterative AI-Assisted Development Without Architecture**
- Features added incrementally without upfront design
- Each feature solved immediate problem but increased coupling
- No clear boundaries established between layers
- Refactoring happened within existing structure rather than challenging it

**7.1.2 Convenience Over Decoupling**
- PyQt6 signals used everywhere because they're convenient
- Singletons used because they're easy to access
- Direct database queries because repositories are "more code"
- Concrete types because interfaces feel like overhead

**7.1.3 Missing Abstractions**
- No repository layer between domain and database
- No view models between UI and domain
- No event bus independent of PyQt6
- No clear service interfaces (just concrete classes)

**7.1.4 Feature Creep Without Refactoring Budget**
- Override system added → required state tracking → added to existing classes
- Formula system added → required dependency tracking → coupled to existing validators
- Control system added → required chain evaluation → embedded in widgets
- Each feature expanded existing classes rather than creating new bounded contexts

**7.1.5 Testing Not Driving Design**
- No unit tests forcing decoupling
- Integration tests (if any) mask coupling problems
- Classes not designed for testability
- Global state makes isolated testing impossible

**7.1.6 Domain Complexity Absorbed by Infrastructure**
- Business rules (validation, formulas, controls) scattered across layers
- No domain model - just data classes + services with SQL
- State transitions implicit rather than explicit (state machines)
- Value objects missing (field values, validation results as primitives)

### 7.2 Risks If System Keeps Growing

**7.2.1 Maintenance Risks (High)**
- **Change amplification**: Modifying one feature requires changes in 5+ files
- **Cognitive load**: Understanding any feature requires understanding entire system
- **Regression risk**: No isolated tests, any change can break unrelated features
- **Onboarding cost**: New developers need weeks to understand the architecture

**7.2.2 Extension Risks (High)**
- **New field type**: Requires modifying FieldFactory, ValidationManager, potentially UI widgets
- **New output format**: Requires modifying OutputMappingManager, TemplateEngine
- **New app type feature**: Requires modifying AppTypeManager (1147 lines)
- **New validation rule**: Requires modifying hard-coded validator selection

**7.2.3 Scalability Risks (Medium)**
- **Memory leaks**: Strong references in registries without cleanup
- **Thread safety**: Global singletons with mutable state
- **Performance**: No caching strategy, repeated database queries

**7.2.4 Technical Debt Risks (Critical)**
- **Framework lock-in**: Cannot port to web/mobile without complete rewrite
- **Library upgrades**: PyQt6 upgrade could break core layer
- **Testing debt**: Adding tests now requires massive refactoring first

**7.2.5 Team Risks (Medium-High)**
- **Bus factor**: Only someone who understands everything can make changes safely
- **Parallel development**: Two developers cannot work on different features without conflicts
- **Code review**: Impossible to review changes without full context

---

## 8. REWRITE STRATEGY

### 8.1 Assessment: Big Bang vs Incremental

| Factor | Big Bang | Incremental |
|--------|----------|-------------|
| **Current test coverage** | None/minimal → favors Big Bang | - |
| **Clear requirements** | Yes (functional audit) → favors Big Bang | - |
| **Business pressure** | Development stage, no users → favors Big Bang | - |
| **Team size** | Likely 1-2 people → favors Big Bang | - |
| **Coupling level** | Extreme → makes Incremental very hard | - |
| **Domain complexity** | Moderate → manageable in Big Bang | - |

### 8.2 Recommendation: Controlled Big Bang Rewrite

**Rationale**:
1. The coupling is too severe for incremental extraction
2. No existing tests to preserve behavior during incremental changes
3. Still in development - no production users to migrate
4. Clear functional requirements from audit
5. The "strangler fig" pattern would take longer than rewriting

**See [ADR-001: Controlled Big Bang Rewrite Strategy](adrs/ADR-001-controlled-big-bang-rewrite.md) for details.**

### 8.3 Rewrite Approach

**Phase A: Domain Model First**
- Define pure domain entities (no PyQt6, no SQLite)
- Define value objects (FieldValue, ValidationResult, etc.)
- Define domain services with interfaces
- Unit test domain logic in isolation

**Phase B: Infrastructure Adapters**
- Implement repository interfaces with SQLite
- Implement event bus independent of PyQt6
- Create adapters for external libraries (xlwings, python-docx, PyMuPDF)

**Phase C: Application Services**
- Orchestrate domain operations
- Handle transactions and unit of work
- Coordinate between repositories

**Phase D: UI Layer**
- Create view models (not direct domain exposure)
- Build widgets that consume view models
- Use dependency injection throughout

### 8.4 Risk Mitigation

- **Keep old code running**: New app built alongside, not replacing (legacy_app/ directory)
- **Feature parity checklist**: Use functional audit as acceptance criteria
- **Parallel testing**: Run both apps with same inputs, compare outputs
- **Incremental migration**: Move one feature at a time once new app stable

---

## 9. SUMMARY

### Critical Issues (Must Fix)
1. Core layer depends on PyQt6 → untestable, non-portable
2. God objects (MainWindow 2024 LOC, AppTypeManager 1147 LOC)
3. Two competing global state systems
4. No abstractions between layers
5. Business logic scattered across UI, services, persistence

### Root Causes
1. Iterative development without architecture
2. Convenience over decoupling
3. Testing not driving design
4. Feature creep without refactoring

### Recommendation
**Controlled Big Bang rewrite** with domain-first approach, keeping old code as reference until feature parity achieved.

**Doc Helper v1** will implement the clean architecture properly from the start, avoiding all these pitfalls.

---

## 10. HIGH-LEVEL ARCHITECTURE

### 10.1 Architecture Style: Clean Architecture + Domain-Driven Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  MainWindow │  │   Dialogs   │  │   Widgets   │  │ ViewModels  │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │            │
│         └────────────────┴────────────────┴────────────────┘            │
│                                    │                                     │
│                                    ▼                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                           APPLICATION LAYER                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Use Cases     │  │  App Services   │  │   Event Bus     │         │
│  │  (Commands/     │  │  (Orchestration)│  │  (Pub/Sub)      │         │
│  │   Queries)      │  │                 │  │                 │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           │                    │                    │                   │
│           └────────────────────┴────────────────────┘                   │
│                                │                                         │
│                                ▼                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                            DOMAIN LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   Entities   │  │Value Objects │  │Domain Services│  │  Events    │  │
│  │  (Aggregates)│  │              │  │              │  │            │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Repositories │  │  Factories   │  │Specifications│                  │
│  │ (Interfaces) │  │              │  │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                         INFRASTRUCTURE LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   SQLite    │  │    File     │  │   Document  │  │   Config    │    │
│  │ Repositories│  │   System    │  │  Generators │  │   Loaders   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │   xlwings   │  │ python-docx │  │  PyMuPDF    │                     │
│  │   Adapter   │  │   Adapter   │  │   Adapter   │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Dependency Rule

```
DEPENDENCIES POINT INWARD ONLY

Presentation → Application → Domain ← Infrastructure
                              ↑
                              │
                    Infrastructure implements
                    Domain interfaces
```

**Key Principle**: Domain layer has ZERO external dependencies. No PyQt6, no SQLite, no file system.

**See Also**:
- [ADR-002: Clean Architecture with Domain-Driven Design](adrs/ADR-002-clean-architecture-ddd.md)
- [ADR-003: Framework-Independent Domain Layer](adrs/ADR-003-framework-independent-domain.md)

---

## 11. FOLDER STRUCTURE (v1)

**Note**: This structure is for v1. The folder naming and organization support future extension to v2+ multi-app-type platform.

```
doc_helper/
├── pyproject.toml                    # Project config, dependencies
├── pytest.ini                        # Test configuration
│
├── src/
│   └── doc_helper/
│       │
│       ├── __init__.py
│       ├── main.py                   # Entry point, DI composition root
│       │
│       ├── domain/                   # DOMAIN LAYER (no external deps)
│       │   ├── __init__.py
│       │   │
│       │   ├── common/               # Shared domain concepts
│       │   │   ├── __init__.py
│       │   │   ├── entity.py         # Base Entity, AggregateRoot
│       │   │   ├── value_object.py   # Base ValueObject
│       │   │   ├── events.py         # DomainEvent base
│       │   │   ├── result.py         # Result[T, E] monad
│       │   │   ├── specification.py  # Specification pattern base
│       │   │   ├── i18n.py           # i18n value objects (Language, TextDirection, TranslationKey)
│       │   │   └── translation.py    # ITranslationService interface
│       │   │
│       │   ├── schema/               # Schema Bounded Context (v1)
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   ├── entity_definition.py  # EntityDefinition aggregate
│       │   │   │   └── field_definition.py   # FieldDefinition
│       │   │   ├── value_objects/
│       │   │   │   ├── field_type.py         # FieldType enum + behavior
│       │   │   │   ├── field_id.py           # Strongly typed ID
│       │   │   │   ├── entity_id.py          # Strongly typed ID
│       │   │   │   └── schema_version.py     # Version value object
│       │   │   ├── services/
│       │   │   │   └── schema_validator.py   # Domain validation logic
│       │   │   ├── repositories.py           # Repository interfaces
│       │   │   └── events.py                 # Schema domain events
│       │   │
│       │   ├── project/              # Project Bounded Context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   ├── project.py            # Project aggregate root
│       │   │   │   └── field_value.py        # FieldValue entity
│       │   │   ├── value_objects/
│       │   │   │   ├── project_id.py         # Strongly typed ID
│       │   │   │   ├── project_path.py       # Path value object
│       │   │   │   └── field_data.py         # Immutable field data
│       │   │   ├── services/
│       │   │   │   └── project_validator.py  # Project-level validation
│       │   │   ├── repositories.py           # Repository interfaces
│       │   │   └── events.py                 # Project domain events
│       │   │
│       │   ├── validation/           # Validation Bounded Context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   └── validation_rule.py    # ValidationRule aggregate
│       │   │   ├── value_objects/
│       │   │   │   ├── validation_result.py  # Immutable result (v1: simple)
│       │   │   │   ├── constraint.py         # Constraint types
│       │   │   │   └── error_message.py      # Localized error
│       │   │   ├── services/
│       │   │   │   ├── validator.py          # Validator interface
│       │   │   │   ├── text_validator.py     # Text validation
│       │   │   │   ├── number_validator.py   # Number validation
│       │   │   │   ├── date_validator.py     # Date validation
│       │   │   │   └── composite_validator.py
│       │   │   ├── specifications/
│       │   │   │   ├── required_spec.py
│       │   │   │   ├── range_spec.py
│       │   │   │   └── pattern_spec.py
│       │   │   └── repositories.py
│       │   │
│       │   ├── formula/              # Formula Bounded Context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   └── formula.py            # Formula aggregate
│       │   │   ├── value_objects/
│       │   │   │   ├── expression.py         # Formula expression
│       │   │   │   ├── dependency_graph.py   # Immutable dep graph
│       │   │   │   └── evaluation_context.py # Context for eval
│       │   │   ├── services/
│       │   │   │   ├── parser.py             # Expression parser
│       │   │   │   ├── evaluator.py          # Safe evaluator
│       │   │   │   └── dependency_resolver.py
│       │   │   └── repositories.py
│       │   │
│       │   ├── control/              # Field Control Bounded Context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   └── control_rule.py       # ControlRule aggregate
│       │   │   ├── value_objects/
│       │   │   │   ├── control_effect.py     # Effect type
│       │   │   │   ├── control_mapping.py    # Source→Target mapping
│       │   │   │   └── effect_result.py      # Evaluation result
│       │   │   ├── services/
│       │   │   │   └── control_evaluator.py  # Chain evaluator
│       │   │   └── repositories.py
│       │   │
│       │   ├── override/             # Override Bounded Context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   └── override.py           # Override aggregate
│       │   │   ├── value_objects/
│       │   │   │   ├── override_state.py     # State enum + transitions
│       │   │   │   ├── override_value.py     # System vs report value
│       │   │   │   └── conflict.py           # Conflict detection
│       │   │   ├── services/
│       │   │   │   └── override_resolver.py  # Resolution logic
│       │   │   └── repositories.py
│       │   │
│       │   ├── document/             # Document Generation Context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   ├── template.py           # Template aggregate
│       │   │   │   └── output_mapping.py     # Field→Output mapping
│       │   │   ├── value_objects/
│       │   │   │   ├── template_id.py
│       │   │   │   ├── content_tag.py        # Word content control tag
│       │   │   │   └── cell_reference.py     # Excel cell ref
│       │   │   ├── services/
│       │   │   │   └── value_resolver.py     # Override→Formula→Raw
│       │   │   └── repositories.py
│       │   │
│       │   ├── transformer/          # Transformer Bounded Context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   └── transformer.py        # Transformer interface
│       │   │   ├── implementations/          # Built-in transformers
│       │   │   │   ├── suffix.py
│       │   │   │   ├── prefix.py
│       │   │   │   ├── map.py
│       │   │   │   ├── date_format.py
│       │   │   │   ├── arabic_number.py
│       │   │   │   └── ...               # All 15+ transformers (v1)
│       │   │   └── services/
│       │   │       └── transformer_registry.py
│       │   │
│       │   └── file/                 # File Management Context
│       │       ├── __init__.py
│       │       ├── entities/
│       │       │   └── attachment.py         # Attachment aggregate
│       │       ├── value_objects/
│       │       │   ├── file_path.py
│       │       │   ├── file_metadata.py      # Size, dimensions, etc.
│       │       │   ├── figure_number.py      # Caption numbering
│       │       │   └── allowed_extensions.py
│       │       ├── services/
│       │       │   ├── numbering_service.py  # Figure numbering
│       │       │   └── caption_generator.py
│       │       └── repositories.py
│       │
│       ├── application/              # APPLICATION LAYER
│       │   ├── __init__.py
│       │   │
│       │   ├── common/
│       │   │   ├── __init__.py
│       │   │   ├── use_case.py       # UseCase base class
│       │   │   ├── unit_of_work.py   # UoW interface
│       │   │   └── event_bus.py      # Event bus interface
│       │   │
│       │   ├── commands/             # Write operations (CQRS)
│       │   │   ├── __init__.py
│       │   │   ├── project/
│       │   │   │   ├── create_project.py      # v1
│       │   │   │   ├── open_project.py        # v1
│       │   │   │   ├── save_project.py        # v1
│       │   │   │   ├── close_project.py       # v1
│       │   │   │   └── update_field_value.py  # v1
│       │   │   ├── schema/
│       │   │   │   ├── add_entity.py          # v1 (schema editor)
│       │   │   │   ├── add_field.py           # v1 (schema editor)
│       │   │   │   └── update_field.py        # v1 (schema editor)
│       │   │   ├── override/
│       │   │   │   ├── accept_override.py     # v1
│       │   │   │   ├── reject_override.py     # v1
│       │   │   │   └── cleanup_synced.py      # v1
│       │   │   └── document/
│       │   │       ├── generate_report.py     # v1
│       │   │       └── export_pdf.py          # v1
│       │   │
│       │   ├── queries/              # Read operations (CQRS)
│       │   │   ├── __init__.py
│       │   │   ├── project/
│       │   │   │   ├── get_project.py         # v1
│       │   │   │   ├── get_field_value.py     # v1
│       │   │   │   └── get_recent_projects.py # v1
│       │   │   ├── schema/
│       │   │   │   ├── get_schema.py          # v1
│       │   │   │   ├── get_entities.py        # v1
│       │   │   │   └── get_fields.py          # v1
│       │   │   ├── validation/
│       │   │   │   └── validate_field.py      # v1
│       │   │   └── formula/
│       │   │       └── compute_formula.py     # v1
│       │   │
│       │   ├── services/             # Application services
│       │   │   ├── __init__.py
│       │   │   ├── project_service.py        # Orchestrates project ops (v1)
│       │   │   ├── schema_service.py         # Orchestrates schema ops (v1)
│       │   │   ├── validation_service.py     # Batch validation (v1)
│       │   │   ├── formula_service.py        # Formula orchestration (v1)
│       │   │   ├── control_service.py        # Control evaluation (v1)
│       │   │   └── document_service.py       # Report generation (v1)
│       │   │
│       │   ├── dto/                  # Data Transfer Objects
│       │   │   ├── __init__.py
│       │   │   ├── project_dto.py
│       │   │   ├── field_dto.py
│       │   │   ├── validation_dto.py
│       │   │   └── report_dto.py
│       │   │
│       │   └── events/               # Application events
│       │       ├── __init__.py
│       │       ├── handlers/
│       │       │   ├── on_field_changed.py   # Trigger formula recompute
│       │       │   ├── on_project_saved.py   # Cleanup operations
│       │       │   └── on_override_accepted.py
│       │       └── integration_events.py     # Cross-context events
│       │
│       ├── infrastructure/           # INFRASTRUCTURE LAYER
│       │   ├── __init__.py
│       │   │
│       │   ├── persistence/          # Database implementations
│       │   │   ├── __init__.py
│       │   │   ├── sqlite/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── connection.py         # Connection management
│       │   │   │   ├── unit_of_work.py       # SQLite UoW
│       │   │   │   ├── repositories/
│       │   │   │   │   ├── schema_repository.py       # v1
│       │   │   │   │   ├── project_repository.py      # v1
│       │   │   │   │   ├── validation_repository.py   # v1
│       │   │   │   │   ├── formula_repository.py      # v1
│       │   │   │   │   ├── override_repository.py     # v1
│       │   │   │   │   └── template_repository.py     # v1
│       │   │   │   └── migrations/
│       │   │   │       ├── __init__.py
│       │   │   │       └── ...
│       │   │   └── mappers/                  # Entity ↔ DB row mappers
│       │   │       ├── field_mapper.py
│       │   │       ├── project_mapper.py
│       │   │       └── ...
│       │   │
│       │   ├── filesystem/           # File system operations
│       │   │   ├── __init__.py
│       │   │   ├── project_storage.py        # Project directory ops
│       │   │   ├── attachment_storage.py     # File copy/delete
│       │   │   ├── config_loader.py          # JSON config loading
│       │   │   └── recent_projects.py        # Recent projects file (v1)
│       │   │
│       │   ├── documents/            # Document library adapters
│       │   │   ├── __init__.py
│       │   │   ├── excel/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── xlwings_adapter.py    # xlwings implementation (v1)
│       │   │   │   └── interfaces.py         # IExcelService
│       │   │   ├── word/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── docx_adapter.py       # python-docx implementation (v1)
│       │   │   │   └── interfaces.py         # IWordService
│       │   │   └── pdf/
│       │   │       ├── __init__.py
│       │   │       ├── pymupdf_adapter.py    # PyMuPDF implementation (v1)
│       │   │       └── interfaces.py         # IPdfService
│       │   │
│       │   ├── i18n/                 # Internationalization (v1)
│       │   │   ├── __init__.py
│       │   │   ├── json_translation_service.py  # JSON file-based translation loader
│       │   │   └── translation_loader.py        # Translation file parser
│       │   │
│       │   ├── events/               # Event infrastructure
│       │   │   ├── __init__.py
│       │   │   ├── in_memory_bus.py          # Simple event bus (v1)
│       │   │   └── event_dispatcher.py
│       │   │
│       │   └── di/                   # Dependency Injection
│       │       ├── __init__.py
│       │       └── container.py              # DI container setup
│       │
│       └── presentation/             # PRESENTATION LAYER (PyQt6)
│           ├── __init__.py
│           │
│           ├── viewmodels/           # View Models (MVVM)
│           │   ├── __init__.py
│           │   ├── main_window_vm.py         # v1: Recent projects only
│           │   ├── project_vm.py             # v1
│           │   ├── field_vm.py               # v1: All 12 field types
│           │   ├── validation_vm.py          # v1
│           │   ├── schema_editor_vm.py       # v1
│           │   └── override_vm.py            # v1
│           │
│           ├── views/                # PyQt6 Views
│           │   ├── __init__.py
│           │   ├── main_window.py            # Main window (thin) (v1)
│           │   ├── welcome_view.py           # v1: Recent projects list only
│           │   ├── project_view.py           # v1
│           │   └── tabs/
│           │       ├── dynamic_tab.py        # v1
│           │       └── file_tab.py           # v1
│           │
│           ├── widgets/              # Reusable widgets
│           │   ├── __init__.py
│           │   ├── fields/
│           │   │   ├── base_field.py         # v1
│           │   │   ├── text_field.py         # v1
│           │   │   ├── number_field.py       # v1
│           │   │   ├── date_field.py         # v1
│           │   │   ├── option_field.py       # v1 (DROPDOWN, RADIO, CHECKBOX)
│           │   │   ├── formula_field.py      # v1 (CALCULATED)
│           │   │   ├── lookup_field.py       # v1 (LOOKUP)
│           │   │   ├── file_field.py         # v1 (FILE, IMAGE)
│           │   │   └── table_field.py        # v1 (TABLE)
│           │   ├── common/
│           │   │   ├── collapsible_group.py  # v1
│           │   │   └── flow_layout.py        # v1
│           │   └── file/
│           │       ├── gallery.py            # v1
│           │       ├── file_preview.py       # v1
│           │       └── file_details.py       # v1
│           │
│           ├── dialogs/              # Modal dialogs
│           │   ├── __init__.py
│           │   ├── settings_dialog.py        # v1 (language selector, light theme only)
│           │   ├── override_dialog.py        # v1
│           │   ├── template_dialog.py        # v1
│           │   ├── conflict_dialog.py        # v1
│           │   ├── figure_numbering_dialog.py # v1
│           │   └── schema_editor/
│           │       ├── schema_editor_dialog.py  # v1
│           │       ├── entity_panel.py       # v1
│           │       └── field_panel.py        # v1
│           │
│           ├── factories/            # Widget factories
│           │   ├── __init__.py
│           │   ├── field_widget_factory.py   # Creates field widgets (v1)
│           │   └── dialog_factory.py         # v1
│           │
│           ├── adapters/             # UI ↔ Application adapters
│           │   ├── __init__.py
│           │   ├── qt_event_adapter.py       # Domain events → Qt signals (v1)
│           │   ├── history_adapter.py        # Undo/Redo via QUndoStack (v1)
│           │   └── qt_translation_adapter.py # i18n adapter: ITranslationService → Qt UI (v1)
│           │
│           └── styles/
│               ├── __init__.py
│               └── theme.py                  # v1: Light theme only
│
├── translations/                     # i18n translation files (v1)
│   ├── en.json                       # English translations
│   └── ar.json                       # Arabic translations
│
└── tests/
    ├── __init__.py
    ├── conftest.py                   # Shared fixtures
    │
    ├── unit/                         # Unit tests (no I/O)
    │   ├── domain/
    │   │   ├── test_validation.py
    │   │   ├── test_formula.py
    │   │   ├── test_control.py
    │   │   ├── test_override.py
    │   │   └── test_transformer.py
    │   └── application/
    │       ├── test_commands.py
    │       └── test_queries.py
    │
    ├── integration/                  # Integration tests (with I/O)
    │   ├── test_sqlite_repos.py
    │   ├── test_document_generation.py
    │   └── test_project_lifecycle.py
    │
    └── e2e/                          # End-to-end tests
        └── test_full_workflow.py
```

**v1 Scope Notes**:
- Folder structure uses `doc_helper/` naming throughout
- All v1 core features are included
- NO app type discovery/selection infrastructure (v2+)
- NO extension loading mechanism (v2+)
- Schema is loaded directly from `app_types/soil_investigation/config.db`
- Recent projects tracking is simple file-based (no multi-app metadata)

---

## 12. DOMAIN MODEL SUMMARY (v1)

**Note**: This section provides a high-level summary of the domain model. The folder structure above details the complete organization of entities, value objects, services, and repositories for each bounded context.

### Core Bounded Contexts (v1)

1. **Schema Context**: EntityDefinition, FieldDefinition, FieldType (12 types), schema validation
2. **Project Context**: Project aggregate, FieldValue entities, project-level validation
3. **Validation Context**: ValidationRule, constraints, validators for all 12 field types
4. **Formula Context**: Formula aggregate, expression parser, evaluator, dependency resolution
5. **Control Context**: ControlRule, effect types (VALUE_SET, VISIBILITY, ENABLE), chain evaluation
6. **Override Context**: Override aggregate, state machine (PENDING → ACCEPTED → SYNCED), conflict detection
7. **Document Context**: Template aggregate, output mappings, value resolution
8. **Transformer Context**: ITransformer interface, 15+ built-in transformers (suffix, prefix, map, date, arabic, etc.)
9. **File Context**: Attachment aggregate, file metadata, figure numbering, caption generation

### Design Patterns Used

- **Aggregate Pattern**: Project, Override, Formula, ControlRule as consistency boundaries
- **Value Object Pattern**: Immutable types (FieldType, ValidationResult, OverrideState, etc.)
- **Repository Pattern**: Interface in domain, implementation in infrastructure
- **Specification Pattern**: Composable validation rules
- **Strategy Pattern**: Validators, Transformers, Naming strategies
- **State Machine Pattern**: Override state transitions with explicit rules
- **Dependency Injection**: Constructor injection throughout, no service locator
- **CQRS Pattern**: Commands for writes, Queries for reads
- **Event Sourcing Ready**: Domain events collected in aggregates
- **Result Monad**: Explicit error handling instead of exceptions

**See ADRs for detailed architectural decisions**:
- [ADR-002: Clean Architecture with DDD](adrs/ADR-002-clean-architecture-ddd.md)
- [ADR-004: CQRS Pattern](adrs/ADR-004-cqrs-pattern.md)
- [ADR-007: Repository Pattern](adrs/ADR-007-repository-pattern.md)
- [ADR-008: Result Monad](adrs/ADR-008-result-monad.md)
- [ADR-009: Strongly Typed IDs](adrs/ADR-009-strongly-typed-ids.md)
- [ADR-010: Immutable Value Objects](adrs/ADR-010-immutable-value-objects.md)
- [ADR-012: Registry-Based Factory](adrs/ADR-012-registry-based-factory.md)

---

## 13. IMPLEMENTATION MILESTONES (v1 Scope)

### Milestone Summary

| # | Milestone | Duration | Focus | v1 Scope |
|---|-----------|----------|-------|----------|
| **M1** | Foundation | Days 1-13 | Project setup, base classes, i18n infrastructure | ✅ Full v1 + i18n foundation |
| **M2** | Validation Domain | Days 14-23 | Constraints, validators | ✅ Simple pass/fail (no severity) |
| **M3** | Schema Domain | Days 24-33 | Entity/field definitions | ✅ Single app type only |
| **M4** | Formula Domain | Days 34-45 | Parser, evaluator | ✅ Full v1 |
| **M5** | Control Domain | Days 46-55 | Inter-field dependencies | ✅ Full v1 |
| **M6** | Project Domain | Days 56-68 | Project aggregate | ✅ No history/autosave |
| **M7** | Override Domain | Days 69-78 | State machine | ✅ Full v1 |
| **M8** | Infrastructure | Days 79-98 | SQLite, file storage | ✅ No extensions |
| **M9** | Document Gen | Days 99-118 | Transformers, adapters | ✅ Basic naming only |
| **M10** | Application Layer | Days 119-138 | Commands, queries | ✅ No import/export |
| **M11** | Presentation | Days 139-185 | UI, ViewModels, i18n UI | ✅ i18n support (English/Arabic + RTL) |
| **M12** | Polish & Testing | Days 186-213 | Tests, docs, bugs, i18n tests | ✅ Full v1 + i18n testing |

**Total**: ~213 days (43 weeks / 10.5 months)

---

### M1: Foundation (Days 1-13)

**Objective**: Set up project structure and core domain primitives

**Deliverables**:
- `doc_helper/` project structure with `pyproject.toml`
- Base domain classes: `Entity`, `AggregateRoot`, `ValueObject`
- `Result[T, E]` monad for error handling
- `DomainEvent` base class
- `Specification` pattern base
- Initial test infrastructure
- **i18n infrastructure** (+3 days):
  - Translation key system with `TranslationKey` value object
  - `ITranslationService` interface (domain layer)
  - Translation file structure (JSON-based: `en.json`, `ar.json`)
  - Language enum: `Language.ENGLISH`, `Language.ARABIC`
  - Text direction enum: `TextDirection.LTR`, `TextDirection.RTL`

**Key Files**:
- `src/doc_helper/domain/common/entity.py`
- `src/doc_helper/domain/common/value_object.py`
- `src/doc_helper/domain/common/result.py`
- `src/doc_helper/domain/common/events.py`
- `src/doc_helper/domain/common/i18n.py` *(new - i18n value objects)*
- `src/doc_helper/domain/common/translation.py` *(new - ITranslationService interface)*

**v1 Scope**: Full foundation + i18n infrastructure.

---

### M2: Validation Domain (Days 11-20)

**Objective**: Implement field validation system

**Deliverables**:
- `FieldConstraint` value objects (min/max, pattern, required)
- `IValidator` interface
- `ValidationResult` with errors list
- Built-in validators: `TextValidator`, `NumberValidator`, `DateValidator`
- Composite validator for combining rules
- Specification pattern for constraints

**Key Entities**:
- `ValidationRule` aggregate
- `Constraint` value objects
- `ErrorMessage` value object

**v1 Scope**:
- ✅ Simple ValidationResult (errors list)
- ❌ NO `ValidationSeverity` (ERROR/WARNING/INFO) - v2+
- ❌ NO warning-level validation - v2+

---

### M3: Schema Domain (Days 21-30)

**Objective**: Implement schema definition system

**Deliverables**:
- `FieldType` enum (12 types: TEXT, TEXTAREA, NUMBER, DATE, DROPDOWN, CHECKBOX, RADIO, CALCULATED, LOOKUP, FILE, IMAGE, TABLE)
- `FieldDefinition` value object with validation rules, options, formulas
- `EntityDefinition` aggregate with field collection
- `ISchemaRepository` interface
- Schema loaded directly from `app_types/soil_investigation/config.db`

**Key Entities**:
- `EntityDefinition` aggregate
- `FieldDefinition` value object
- `FieldType` enum

**v1 Scope**:
- ✅ EntityDefinition, FieldDefinition, 12 FieldTypes
- ✅ Schema loaded from single config.db (hardcoded path)
- ❌ NO `AppTypeInfo` aggregate - v2+
- ❌ NO manifest.json parsing - v2+
- ❌ NO app type discovery - v2+

---

### M4: Formula Domain (Days 31-42)

**Objective**: Implement formula parsing and evaluation

**Deliverables**:
- Formula tokenizer and parser
- Expression AST (Abstract Syntax Tree)
- `FormulaEvaluator` with safe evaluation
- Dependency graph construction
- Circular dependency detection
- Allowed functions: abs, min, max, round, sum, pow, upper, lower, strip, concat, if_else, is_empty, coalesce

**Key Entities**:
- `Formula` aggregate
- `Expression` value object
- `DependencyGraph` value object

**v1 Scope**: Full formula system - no exclusions.

---

### M5: Control Domain (Days 43-52)

**Objective**: Implement inter-field control system

**Deliverables**:
- `ControlRule` aggregate
- Control effect types: VALUE_SET, VISIBILITY, ENABLE
- `ControlEffectEvaluator` with chain propagation
- Cycle detection (max depth: 10)
- Conditional mapping (source value → target effect)

**Key Entities**:
- `ControlRule` aggregate
- `ControlEffect` value object
- `ControlMapping` value object

**v1 Scope**: Full control system - no exclusions.

---

### M6: Project Domain (Days 53-65)

**Objective**: Implement project aggregate and field values

**Deliverables**:
- `Project` aggregate root with metadata
- `FieldValue` entity with value storage
- `IProjectRepository` interface
- Recent projects tracking (simple list, last 5 projects)
- Value resolution logic (override → formula → raw)

**Key Entities**:
- `Project` aggregate root
- `FieldValue` entity
- `ProjectId`, `ProjectPath` value objects

**v1 Scope**:
- ✅ Project aggregate, field values
- ✅ Recent projects tracking (simple list)
- ❌ NO `FieldHistoryEntry` entity - v2+
- ❌ NO auto-save mechanism - v2+
- ❌ NO change history tracking - v2+

---

### M7: Override Domain (Days 66-75)

**Objective**: Implement override state machine

**Deliverables**:
- `Override` aggregate with state machine
- `OverrideState` enum: PENDING, ACCEPTED, INVALID, SYNCED, SYNCED_FORMULA
- State transitions with validation
- Conflict detection (multiple different values)
- Formula/Control conflict detection

**Key Entities**:
- `Override` aggregate
- `OverrideState` enum
- `Conflict` value object

**v1 Scope**: Full override system - no exclusions.

---

### M8: Infrastructure Layer (Days 76-95)

**Objective**: Implement persistence and file storage

**Deliverables**:
- `SqliteConnection` with connection pooling
- `SqliteUnitOfWork` for transactions
- Repositories: `SqliteSchemaRepository`, `SqliteProjectRepository`, `SqliteValidationRepository`, `SqliteFormulaRepository`, `SqliteOverrideRepository`
- Entity-to-row mappers for all aggregates
- `FileProjectStorage` for .dhproj files
- `AttachmentStorage` for file fields
- `ConfigLoader` for JSON config
- `RecentProjectsStorage` (simple file-based)

**Key Classes**:
- `SqliteConnection`
- `SqliteUnitOfWork`
- All repository implementations
- Mappers

**v1 Scope**:
- ✅ SQLite repositories for all v1 entities
- ✅ File storage for projects and attachments
- ✅ Recent projects persistence (simple)
- ❌ NO `ExtensionLoader` - v2+
- ❌ NO `FieldHistoryRepository` - v2+
- ❌ NO `AutoSaveStorage` - v2+

---

### M9: Document Generation (Days 96-115)

**Objective**: Implement document generation system

**Deliverables**:
- All 15+ built-in transformers (Suffix, Prefix, Map, Template, DateFormat, ArabicNumber, ArabicOrdinal, etc.)
- `ITransformer` interface
- `TransformerRegistry` for registration
- `WordDocumentAdapter` (python-docx) with content control mapping
- `ExcelDocumentAdapter` (xlwings) with cell mapping
- `PdfExportAdapter` (PyMuPDF) for stamp/signature overlay
- Template loading from `app_types/soil_investigation/templates/`
- Basic output naming (project name based)

**Key Adapters**:
- `WordDocumentAdapter`
- `ExcelDocumentAdapter`
- `PdfExportAdapter`

**v1 Scope**:
- ✅ All 15+ transformers
- ✅ Word, Excel, PDF adapters
- ✅ Basic output naming (project name)
- ❌ NO `DocumentVersion` tracking - v2+
- ❌ NO `NamingPattern` tokens ({YYYY}, {MM}, etc.) - v2+
- ❌ NO document version history - v2+

---

### M10: Application Layer (Days 116-135)

**Objective**: Implement commands, queries, and services

**Commands** (v1):
- `CreateProjectCommand` - Initialize new project
- `OpenProjectCommand` - Load existing project
- `SaveProjectCommand` - Persist all changes
- `CloseProjectCommand` - Clean up resources
- `UpdateFieldCommand` - Update field value
- `SetFieldOverrideCommand` - Accept/reject override
- `GenerateDocumentCommand` - Generate Word/Excel/PDF

**Queries** (v1):
- `GetProjectQuery` - Retrieve project details
- `GetEntityFieldsQuery` - Get fields for entity
- `GetValidationResultQuery` - Validate field/project

**Services** (v1):
- `ValidationService` - Batch validation orchestration
- `FormulaService` - Formula evaluation coordination
- `ControlService` - Control chain evaluation
- `DocumentGenerationService` - Document generation workflow

**v1 Exclusions**:
- ❌ NO `ImportFromExcelCommand` - v2+
- ❌ NO `ExportProjectCommand` - v2+
- ❌ NO `CloneProjectCommand` - v2+
- ❌ NO `GetFieldHistoryQuery` - v2+
- ❌ NO `GetAppTypesQuery` - v2+
- ❌ NO `AppTypeDiscoveryService` - v2+
- ❌ NO `AutoSaveService` - v2+

---

### M11: Presentation Layer (Days 139-185)

**Objective**: Implement UI with MVVM pattern and internationalization

**ViewModels** (v1):
- `WelcomeViewModel` - Recent projects list (NO app type selection)
- `ProjectViewModel` - Project-level state
- `EntityViewModel` - Entity navigation
- `FieldViewModel` - Per-field-type ViewModels (12 types)
- `ValidationViewModel` - Validation state
- `OverrideViewModel` - Override management
- `DocumentGenerationViewModel` - Document generation flow
- `SchemaEditorViewModel` - Schema editor

**Widgets** (v1):
- 12 field type widgets: `TextField`, `TextAreaField`, `NumberField`, `DateField`, `DropdownField`, `CheckboxField`, `RadioField`, `CalculatedField`, `LookupField`, `FileField`, `ImageField`, `TableField`
- `CollapsibleGroup` - Field grouping
- `Gallery` - File preview
- Entity navigation sidebar

**Views** (v1):
- `WelcomeView` - Recent projects list
- `MainWindow` - Thin orchestrator
- `ProjectView` - Dynamic form rendering
- `OverrideDialog` - Override management
- `ConflictDialog` - Conflict resolution
- `TemplateDialog` - Template selection
- `SchemaEditorDialog` - Schema editing
- Document generation dialog with pre-generation checklist (errors only)

**Features** (v1):
- Minimal keyboard shortcuts: Ctrl+S (save), Ctrl+Z/Y (undo/redo)
- Light theme only
- Field validation indicators
- Tab navigation
- **Internationalization (i18n)** (+7 days):
  - Language selector in settings dialog (English/Arabic)
  - All UI strings translated (menus, dialogs, buttons, labels, error messages)
  - RTL layout support for Arabic (mirrored navigation, right-aligned text)
  - Translation loading from JSON files (`translations/en.json`, `translations/ar.json`)
  - Dynamic UI update on language change (no restart required)
  - `QtTranslationAdapter` implements `ITranslationService`
  - Persisted language preference in user config

**v1 Exclusions**:
- ❌ NO app type selection cards - v2+
- ❌ NO `SearchViewModel`/search bar - v2+
- ❌ NO `FieldHistoryViewModel`/history popover - v2+
- ❌ NO full keyboard navigation adapter - v2+
- ❌ NO dark mode / theme switching - v2+
- ❌ NO validation severity (warnings) - v2+

---

### M12: Polish & Testing (Days 186-213)

**Objective**: Testing, bug fixes, documentation, and i18n validation

**Deliverables**:
- Unit tests for all domain logic (validation, formula, control, override)
- Integration tests for repositories and document generation
- End-to-end tests for full workflows
- UI smoke tests
- Performance optimization (formula evaluation, control chains)
- User documentation
- Developer documentation
- Bug fixes from testing
- **i18n testing & validation** (+3 days):
  - Translation completeness verification (all keys present in en.json and ar.json)
  - RTL layout testing (visual verification for Arabic)
  - Language switching tests (ensure no UI crashes, proper text direction updates)
  - Translation quality review with native Arabic speaker
  - Documentation of translation key naming conventions
  - User guide in both English and Arabic

**Testing Coverage**:
- Domain layer: 90%+ coverage
- Application layer: 80%+ coverage
- Infrastructure: Integration tests for all repos
- Presentation: UI smoke tests for all 12 field types
- i18n: Translation coverage 100% (all UI strings), RTL layout verification

**v1 Exclusions**:
- ❌ NO `app_types/_template/` folder - v2+
- ❌ NO app type creation guide - v2+

---

### Implementation Notes

**Dependencies Between Milestones**:
- M2-M7 (Domain): Can be developed in parallel after M1
- M8 (Infrastructure): Depends on M2-M7 domain interfaces
- M9 (Document Gen): Depends on M3 (schema), M6 (project), M7 (override)
- M10 (Application): Depends on M2-M9
- M11 (Presentation): Depends on M10
- M12 (Testing): Throughout all milestones

**Testing Strategy**:
- Unit tests written alongside domain code (M2-M7)
- Integration tests after infrastructure (M8-M9)
- E2E tests after presentation (M11)
- Final testing and bug fixes (M12)

**Risk Mitigation**:
- Keep legacy app running for behavioral comparison
- Implement one milestone at a time
- Test each milestone before moving to next
- Use legacy app as oracle for correctness

---

## 14. FUTURE ROADMAP (v2+ Features)

This section documents features deferred beyond v1. These features represent the long-term vision for Doc Helper as a universal document generation platform, but are explicitly OUT OF SCOPE for the initial release.

### 14.1 Multi-App-Type Platform (v2)

**Vision**: Transform Doc Helper from a single-purpose tool into a universal document generation platform supporting multiple document types without code modification.

**Architecture** (see [ADR-013](adrs/ADR-013-multi-app-type-platform-vision.md)):

**App Type Discovery**:
- `AppTypeInfo` aggregate representing app type metadata
- `IAppTypeRegistry` for registering/querying available types
- `AppTypeDiscoveryService` scans `app_types/` folder for manifest.json files
- Each app type package contains:
  - `manifest.json` - declares capabilities, schema location, templates
  - `config.db` - schema definition (EntityDefinition, FieldDefinition)
  - `templates/` - Word/Excel/PDF templates
  - `extensions/` - optional custom transformers (Python modules)

**Extension Architecture**:
- `ExtensionLoader` dynamically loads custom transformers from app type packages
- Custom transformers extend built-in transformer library
- Example: geological-specific transformers for soil reports, structural calculations for engineering reports

**UI Changes**:
- Welcome screen shows app type cards (icon, name, description)
- User selects app type before creating new project
- App type locked after project creation
- Recent projects show app type badge

**Implementation Considerations**:
- v1 architecture already supports this (clean interfaces, dependency injection)
- `app_types/soil_investigation/` structure already matches v2 layout
- Main work: add discovery service, manifest parsing, extension loader
- Estimated effort: M13-M14 (40-50 days)

---

### 14.2 UX Enhancements (v2+)

**Validation Severity Levels**:
- Extend `ValidationResult` to include severity: ERROR, WARNING, INFO
- UI shows color-coded indicators (red/yellow/blue)
- Pre-generation checklist distinguishes errors (blocking) from warnings (can proceed)
- Example: Missing optional field = WARNING, invalid required field = ERROR

**Dark Mode / Theme Switching**:
- `IThemeProvider` interface with light/dark implementations
- Theme preference persisted in user settings
- Dynamic stylesheet switching
- All custom widgets support both themes

**Auto-Save & Recovery**:
- `AutoSaveService` periodically saves project state to temp storage
- On crash/restart, offer to recover unsaved changes
- `AutoSaveStorage` repository for managing recovery files
- Configurable auto-save interval (default: 30 seconds)

**Quick Search (Ctrl+F)**:
- `SearchViewModel` with indexed field search
- Search across all entities and field labels/values
- Jump to matching fields in UI
- Search history with recent searches

**Full Keyboard Navigation**:
- `KeyboardNavigationAdapter` for tab order management
- Alt+[letter] shortcuts for all menu items
- Ctrl+Tab to switch between entities
- Arrow keys for field navigation within entity

**Field History UI**:
- `FieldHistoryViewModel` displays change history per field
- Popover showing: timestamp, old value, new value, source (user/formula/control)
- Revert to previous value option
- `FieldHistoryRepository` for persistence

**Note**: Internationalization (i18n) was originally planned for v2+ but has been moved to v1 due to active Arabic language usage in the legacy application. See Section 3.12 and milestones M1, M11, M12 for v1 i18n implementation details.

**Estimated Effort**: M15-M16 (30-40 days)

---

### 14.3 Data Operations (v2+)

**Import from Excel**:
- `ImportFromExcelCommand` maps Excel columns to field definitions
- Column mapping UI with preview
- Bulk create projects from spreadsheet rows
- Validation before import (show preview with errors)

**Export Project Data**:
- `ExportProjectCommand` serializes project to JSON/Excel/CSV
- User selects entities and fields to export
- Export template saved for reuse
- Useful for data analysis, reporting, backup

**Clone Project**:
- `CloneProjectCommand` creates deep copy of project
- Option to clone with/without document outputs
- Useful for creating similar projects (e.g., adjacent sites)

**Document Version History**:
- `DocumentVersion` value object tracks generation history
- Store: timestamp, template version, output path, transformer config
- `GetDocumentVersionsQuery` lists all versions for a project
- Regenerate from previous version
- Compare outputs between versions

**Estimated Effort**: M17-M18 (30-40 days)

---

### 14.4 Advanced Document Features (v2+)

**Smart Output Naming**:
- `NamingPattern` value object with token substitution
- Tokens: `{project_name}`, `{date}`, `{version}`, `{entity:field_name}`
- Example: `{project_name}_SoilReport_{date:YYYY-MM-DD}_v{version}.docx`
- UI for editing naming patterns per app type

**Template Variables**:
- Beyond simple field mapping, support calculated template variables
- Example: `total_samples = COUNT(borehole_records)`
- Template expressions evaluated at generation time

**Conditional Sections**:
- Show/hide document sections based on field values
- Example: Only include "Contamination Analysis" section if contamination detected
- Defined in template metadata or app type manifest

**Estimated Effort**: M19 (20-30 days)

---

### 14.5 Roadmap Summary

| Phase | Features | Estimated Effort | Dependencies |
|-------|----------|------------------|--------------|
| **v1** | Core platform (12 milestones) | 200 days | - |
| **v2.0** | Multi-app-type platform | 40-50 days | v1 complete |
| **v2.1** | UX enhancements | 30-40 days | v1 complete |
| **v2.2** | Data operations | 30-40 days | v1 complete |
| **v2.3** | Advanced document features | 20-30 days | v1 complete |

**Total Estimated Effort**: ~320-360 days (v1 + v2.x)

**Note**: v2 phases can be developed in parallel after v1 ships, as they are largely independent features.

---

## 15. ARCHITECTURE DECISION RECORDS (ADRs)

All architectural decisions are documented in separate ADR files in the [adrs/](adrs/) directory. Each ADR follows the format: Status, Context, Decision, Consequences.

### 15.1 ADR Index

| ADR | Title | Status | Category |
|-----|-------|--------|----------|
| [ADR-001](adrs/ADR-001-controlled-big-bang-rewrite.md) | Controlled Big Bang Rewrite Strategy | Accepted | Strategy |
| [ADR-002](adrs/ADR-002-clean-architecture-ddd.md) | Clean Architecture + Domain-Driven Design | Accepted | Architecture |
| [ADR-003](adrs/ADR-003-framework-independent-domain.md) | Framework-Independent Domain Layer | Accepted | Architecture |
| [ADR-004](adrs/ADR-004-cqrs-pattern.md) | CQRS Pattern for Application Layer | Accepted | Patterns |
| [ADR-005](adrs/ADR-005-mvvm-pattern.md) | MVVM Pattern for Presentation Layer | Accepted | Patterns |
| [ADR-006](adrs/ADR-006-event-bus.md) | Domain Event Bus for Cross-Cutting Concerns | Accepted | Patterns |
| [ADR-007](adrs/ADR-007-repository-pattern.md) | Repository Pattern with Interface Segregation | Accepted | Patterns |
| [ADR-008](adrs/ADR-008-result-monad.md) | Result Monad for Error Handling | Accepted | Patterns |
| [ADR-009](adrs/ADR-009-strongly-typed-ids.md) | Strongly Typed Identifiers | Accepted | Domain Design |
| [ADR-010](adrs/ADR-010-immutable-value-objects.md) | Immutable Value Objects | Accepted | Domain Design |
| [ADR-011](adrs/ADR-011-unit-of-work.md) | Unit of Work for Transaction Management | Accepted | Patterns |
| [ADR-012](adrs/ADR-012-registry-based-factory.md) | Registry-Based Factory for Extensibility | Accepted | Patterns |
| [ADR-013](adrs/ADR-013-multi-app-type-platform-vision.md) | Multi-Document-Type Platform Vision | Proposed (v2+) | Vision |

### 15.2 ADR Summary by Category

#### Strategy & Architecture
- **ADR-001**: Controlled big bang rewrite rather than incremental refactoring
- **ADR-002**: Clean Architecture with DDD tactical patterns (aggregates, entities, value objects)
- **ADR-003**: Domain layer has zero external dependencies (no PyQt6, SQLite, filesystem)

#### Application & Presentation Patterns
- **ADR-004**: CQRS - separate Commands (write) from Queries (read) in application layer
- **ADR-005**: MVVM - ViewModels mediate between domain and PyQt6 views
- **ADR-006**: Domain Event Bus for publish/subscribe decoupling (formula recalc, control effects)

#### Data & Persistence Patterns
- **ADR-007**: Repository pattern with interface in domain, implementation in infrastructure
- **ADR-011**: Unit of Work for atomic multi-repository transactions
- **ADR-012**: Registry-based factories for extensibility (field widgets, transformers)

#### Domain Design Patterns
- **ADR-008**: Result[T, E] monad for explicit error handling (no exceptions in domain)
- **ADR-009**: Strongly typed IDs (FieldId, EntityId, ProjectId) prevent mixing errors
- **ADR-010**: Immutable value objects with frozen dataclasses

#### Future Vision
- **ADR-013**: Multi-app-type platform architecture (deferred to v2+)

### 15.3 Key Architectural Constraints

These constraints derive from the ADRs and are **mandatory** for all implementation:

1. **Domain Purity** (ADR-003):
   - Domain layer imports NO external frameworks
   - NO database, filesystem, network, UI dependencies in domain
   - Pure Python business logic only

2. **Dependency Rule** (ADR-002):
   - Dependencies point inward: Presentation → Application → Domain
   - Domain has zero outward dependencies
   - Infrastructure depends on domain interfaces

3. **Explicit Error Handling** (ADR-008):
   - Use Result[T, E] monad instead of exceptions
   - Errors are values, not control flow
   - Caller decides how to handle errors

4. **Immutability** (ADR-010):
   - All value objects are frozen dataclasses
   - Updates return new instances
   - Thread-safe by design

5. **Strong Typing** (ADR-009):
   - No raw strings for IDs
   - Type system prevents ID mixing
   - IDs carry semantic meaning

6. **Testability** (ADR-003):
   - Pure functions for business logic
   - Mock infrastructure via interfaces
   - No global state, no singletons

---

# 16. Anti-Pattern Checklist

This checklist documents specific anti-patterns observed in the old codebase. Use it during code review and development to prevent regression into bad habits.

## 16.1 Architecture Anti-Patterns

### 16.1.1 Layer Violations

| # | Anti-Pattern | Old Code Example | Correct Approach |
|---|--------------|------------------|------------------|
| A1 | **Domain imports UI framework** | `core/history/field_commands.py` imports `QUndoCommand` | Domain layer has ZERO framework imports |
| A2 | **Domain uses Qt signals** | `core/state/project_context.py` uses `pyqtSignal` | Use framework-independent event bus |
| A3 | **Domain uses Qt timers** | `core/state/data_binder.py` uses `QTimer` | Debouncing in presentation layer only |
| A4 | **Business logic in widgets** | Widgets call `validate()` directly | All logic flows through application layer |
| A5 | **SQL in domain services** | `SchemaManager` has hardcoded SQL | SQL lives only in infrastructure |

**Review Checklist:**
- [ ] No `PyQt6` imports in `domain/` folder
- [ ] No `sqlite3` imports in `domain/` folder
- [ ] No file system operations in `domain/` folder
- [ ] No database queries outside `infrastructure/persistence/`
- [ ] Widgets contain no business logic

---

### 16.1.2 God Objects

| # | Anti-Pattern | Old Code Example | Correct Approach |
|---|--------------|------------------|------------------|
| A6 | **Mega-class** | `MainWindow` (2024 LOC, 58 methods) | Split: View, ViewModel, Services |
| A7 | **Manager doing everything** | `AppTypeManager` (1147 LOC) | One class = one responsibility |
| A8 | **Facade duplicating interfaces** | `ProjectContext` (862 LOC, 54 methods) | Expose sub-components directly |
| A9 | **Multiple classes in one file** | `transformers.py` (1605 LOC, 16 classes) | One class per file |

**Review Checklist:**
- [ ] No class exceeds 300 lines of code
- [ ] No class has more than 10 public methods
- [ ] No file contains more than 2 classes
- [ ] Class name describes single responsibility

---

### 16.1.3 Dependency Issues

| # | Anti-Pattern | Old Code Example | Correct Approach |
|---|--------------|------------------|------------------|
| A10 | **Too many constructor params** | `MainWindow.__init__` takes 7 services | Use DI container, inject interfaces |
| A11 | **Self-creating dependencies** | `AppTypeManager` creates `DatabaseConnection` | All deps injected via constructor |
| A12 | **Runtime container access** | `ProjectController` fetches from container | Inject all deps at construction |
| A13 | **Circular dependencies** | `services/` ↔ `core/state/` | Strict layer ordering |

**Review Checklist:**
- [ ] All dependencies injected via constructor
- [ ] No `ServiceContainer.get()` outside composition root
- [ ] No circular imports between packages
- [ ] Dependencies are interfaces, not concrete classes

---

## 16.2 State Management Anti-Patterns

| # | Anti-Pattern | Old Code Example | Correct Approach |
|---|--------------|------------------|------------------|
| S1 | **Global mutable singleton** | `ApplicationState.get_instance()` | Pass state via dependency injection |
| S2 | **Multiple state systems** | `ApplicationState` AND `ProjectContext` | Single source of truth per concern |
| S3 | **State not cleared** | `ProjectContext` dicts never cleared | Explicit state reset on operations |
| S4 | **Hidden behavior flags** | `_suppress_signals`, `_loading` flags | Explicit state machines |
| S5 | **Mutable dicts passed around** | Field values in mutable dicts | Immutable value objects |
| S6 | **Inconsistent ref strategy** | WeakRef for widgets, strong for metadata | Consistent lifecycle management |

**Review Checklist:**
- [ ] No `get_instance()` singleton for mutable state
- [ ] State ownership is clear and documented
- [ ] State transitions use explicit methods
- [ ] No boolean flags controlling complex behavior
- [ ] Value objects are frozen dataclasses

---

## 16.3 Error Handling Anti-Patterns

| # | Anti-Pattern | Old Code Example | Correct Approach |
|---|--------------|------------------|------------------|
| E1 | **Exceptions for control flow** | Raise `ValidationError` for invalid input | Use `Result[T, E]` monad |
| E2 | **Swallowing exceptions** | `except Exception: pass` | Handle specific exceptions, log others |
| E3 | **Inconsistent handling** | Some raise, some return None | Consistent: Result for expected, exceptions for bugs |
| E4 | **Hardcoded error messages** | English messages in domain | Error codes in domain, localize in UI |

**Review Checklist:**
- [ ] Business rule violations return `Result.failure()`
- [ ] No bare `except:` handlers
- [ ] Unexpected exceptions logged with stack trace
- [ ] Error messages localized in presentation only

---

## 16.4 Testing Anti-Patterns

| # | Anti-Pattern | Old Code Example | Correct Approach |
|---|--------------|------------------|------------------|
| T1 | **No tests** | Zero unit tests | Test-first, 80%+ domain coverage |
| T2 | **Untestable design** | Domain depends on PyQt6 | Domain has zero external deps |
| T3 | **Shared test state** | Singletons affect test isolation | Inject deps, reset between tests |
| T4 | **Real DB required** | Can't test without SQLite file | Fake repositories for unit tests |

**Review Checklist:**
- [ ] Every domain class has unit tests
- [ ] Domain tests run without external deps
- [ ] Tests are isolated (no shared state)
- [ ] Integration tests use in-memory SQLite

---

## 16.5 Domain Modeling Anti-Patterns

| # | Anti-Pattern | Old Code Example | Correct Approach |
|---|--------------|------------------|------------------|
| D1 | **Anemic domain** | Entities are data-only, logic in services | Rich model: entities have behavior |
| D2 | **Services doing entity work** | `ValidationManager` validates | Entities validate themselves |
| D3 | **Primitive obsession** | IDs as raw strings | Strongly typed: `FieldId`, `EntityId` |
| D4 | **No aggregate boundaries** | Any code modifies any entity | Aggregate roots control children |
| D5 | **Implicit state machines** | Override states as strings | Explicit enum with `can_transition_to()` |
| D6 | **Scattered business rules** | Validation in UI, services, persistence | Specification pattern in domain |
| D7 | **Dict instead of value object** | `{"valid": True, "errors": [...]}` | `ValidationResult` value object |
| D8 | **No domain events** | Direct method calls on state change | Emit `FieldValueChanged`, etc. |

**Review Checklist:**
- [ ] Entities have behavior methods
- [ ] Identifiers are strongly typed
- [ ] Aggregate roots control child access
- [ ] State transitions use state machine
- [ ] Business rules in Specification classes

---

## 16.6 UI Layer Anti-Patterns

| # | Anti-Pattern | Old Code Example | Correct Approach |
|---|--------------|------------------|------------------|
| U1 | **View contains logic** | Widget decides visibility from business rules | Bind to ViewModel's `is_visible` |
| U2 | **Direct domain access** | Widget calls repository directly | UI → ViewModel → App Service → Domain |
| U3 | **Duplicate UI state** | Dirty flag in widget AND controller | Single source: ViewModel owns state |
| U4 | **Hardcoded widget creation** | `if type == "STRING": QLineEdit()` | Registry factory pattern |
| U5 | **Inconsistent async** | Some ops block, others use threads | Consistent: long ops always async |

**Review Checklist:**
- [ ] Views have no `if` on business data
- [ ] Views don't import domain/application
- [ ] All UI state in ViewModels
- [ ] Widget factories use registry

---

## 16.7 Persistence Anti-Patterns

| # | Anti-Pattern | Old Code Example | Correct Approach |
|---|--------------|------------------|------------------|
| P1 | **SQL everywhere** | Hardcoded SQL in services, managers | SQL only in repositories |
| P2 | **No transaction boundaries** | Each save commits immediately | Unit of Work with explicit commit |
| P3 | **Entity knows persistence** | `Project.save()` writes to DB | Entities are persistence-ignorant |
| P4 | **Schema in multiple places** | Table names hardcoded everywhere | Schema in migrations only |
| P5 | **Connection leaks** | Connections opened, never closed | Context managers, connection pool |

**Review Checklist:**
- [ ] SQL only in `infrastructure/persistence/`
- [ ] Multi-step ops use Unit of Work
- [ ] Domain entities have no persistence code
- [ ] Connections use context managers

---

## 16.8 Quick Reference

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ANTI-PATTERN QUICK REFERENCE                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ❌ DON'T                              ✅ DO                            │
│  ──────────────────────────────────    ─────────────────────────────── │
│  Import PyQt6 in domain               Keep domain pure Python           │
│  Use global singletons                Inject dependencies               │
│  Raise exceptions for validation      Return Result[T, E]               │
│  Put SQL in services                  SQL only in repositories          │
│  Create 2000-line classes             Max 300 lines per class           │
│  Use raw strings for IDs              Use strongly typed IDs            │
│  Modify input parameters              Return new instances              │
│  Put logic in views                   Logic in ViewModels               │
│  Skip writing tests                   Test-first development            │
│  Use boolean flags for state          Use explicit state machines       │
│  Hardcode widget creation             Use registry-based factories      │
│  Commit after every operation         Use Unit of Work                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 16.9 Vocabulary Standards

| Concept | Standard Term | Avoid |
|---------|---------------|-------|
| Retrieve single | `get_*` | `fetch_*`, `retrieve_*`, `find_*` |
| Retrieve multiple | `list_*` | `get_all_*`, `fetch_all_*` |
| Check existence | `exists()` | `has()`, `contains()` |
| Create new | `create_*` | `make_*`, `build_*`, `new_*` |
| Update existing | `update_*` | `modify_*`, `change_*` |
| Delete | `delete_*` | `remove_*`, `destroy_*` |
| Convert | `to_*` | `as_*`, `convert_to_*` |
| Parse from | `from_*` | `parse_*`, `read_*` |
| Validate | `validate()` | `check()`, `verify()` |
| Calculate | `compute_*` | `calculate_*`, `calc_*` |

---

## 16.10 Code Review Gate

**Before approving any PR, verify:**

```
ARCHITECTURE
  [ ] No layer violations (check imports at top of files)
  [ ] No class > 300 LOC
  [ ] All dependencies injected

DOMAIN
  [ ] No PyQt6/sqlite3 imports in domain/
  [ ] Entities have behavior
  [ ] Value objects are frozen

STATE
  [ ] No global mutable singletons
  [ ] Explicit state transitions

ERRORS
  [ ] Result monad for expected failures
  [ ] No bare except clauses

TESTS
  [ ] New code has tests
  [ ] Tests are isolated

UI
  [ ] Views have no business logic
  [ ] State in ViewModels only

PERSISTENCE
  [ ] SQL in repositories only
  [ ] Unit of Work for transactions
```

---


# Functional Audit: Soil Investigation Report Generator

## Phase 1 Analysis - Complete System Inventory

---

## 1. FEATURES BY DOMAIN

### 1.1 Project Management
- **Create New Project**: Select app type → parent folder → project name → auto-initialize database
- **Open Existing Project**: Browse filesystem → validate project.db → restore navigation state
- **Save Project**: Persist all form data to SQLite database
- **Close Project**: Prompt for unsaved changes → return to welcome screen
- **Recent Projects**: Track last 5 projects with quick-reopen functionality
- **Project Lifecycle**: Welcome screen → Edit → Generate → Export → Close

### 1.2 Dynamic Form System
- **Schema-Driven UI**: Forms generated at runtime from database schema
- **12 Field Types**: STRING, TEXT, NUMBER, DATE, OPTION, FORMULA, FILE, CHECKBOX, etc.
- **Entity Types**: SINGLETON (single record like project_info) or COLLECTION (multiple records like boreholes)
- **Tab Navigation**: Dynamic tabs built from schema with back/forward history
- **Field Grouping**: Collapsible groups within tabs

### 1.3 Validation System
- **Required Fields**: Block generation if required fields empty
- **Numeric Validation**: min_value, max_value, integer_only constraints
- **Text Validation**: min_length, max_length, regex patterns
- **Date Validation**: min_date, max_date, allow_future, allow_past
- **Real-Time Feedback**: Validation as user types with visual indicators
- **Form-Wide Validity**: Track overall form validity status

### 1.4 Formula System
- **Computed Fields**: Auto-calculated values using template syntax `{{field_id}}`
- **Dependency Tracking**: Automatic updates when dependencies change
- **Safe Evaluation**: Restricted eval() with allowed functions (abs, min, max, round, etc.)
- **Cross-Tab References**: Formulas can reference fields from any tab
- **Formula Modes**: AUTO (system computed), MANUAL (user override), CUSTOM

### 1.5 Control System (Inter-Field Dependencies)
- **VALUE_SET**: When field A changes, auto-set field B
- **VISIBILITY**: Show/hide fields based on another field's value
- **ENABLE/DISABLE**: Enable/disable fields based on conditions
- **OPTIONS_FILTER**: Filter dropdown options based on another field
- **Chain Evaluation**: A→B→C propagation with cycle detection (max depth: 10)

### 1.6 Override System
- **User Edits from Word**: Track differences between system values and Word document values
- **State Machine**: PENDING → ACCEPTED/INVALID → SYNCED → cleanup
- **Conflict Detection**: Multiple different values for same field
- **Override Management Dialog**: Review, accept, revert overrides
- **Formula Override**: Special SYNCED_FORMULA state preserved across iterations

### 1.7 File Management
- **Single/Multiple File Fields**: Configurable file upload widgets
- **Drag-and-Drop**: File drag-drop support
- **File Preview**: Image preview with zoom, PDF preview with pagination
- **Figure Numbering**: Automatic caption numbering with customizable formats
- **Captions**: Figure, Image, Plan, Section, Table, Chart, Appendix types
- **Numbering Formats**: Arabic, Roman, Letter styles
- **Reordering**: Drag-to-reorder for custom figure sequence

### 1.8 Document Generation
- **Word Document Generation**: Populate Word templates with form data
- **Template Selection**: Multiple templates per app type with default
- **Content Control Mapping**: Fields mapped to Word content controls by tag
- **Excel Generation**: Populate Excel templates (xlwings)
- **PDF Export**: Convert to PDF with optional password protection
- **Stamp/Signature Application**: Configurable position, scale, rotation

### 1.9 Transformer System
- **Bidirectional Conversion**: Raw values ↔ Document display values
- **SuffixTransformer**: "5" ↔ "5 جسات" (boreholes)
- **PrefixTransformer**: "100" ↔ "ك م² 100"
- **MapTransformer**: Value mapping (owner_type: "single" → "سيد")
- **TemplateTransformer**: Pattern-based (e.g., "BH-{index}")
- **DateFormatTransformer**: Date formatting
- **ArabicNumberTransformer**: English-to-Arabic numerals
- **ArabicOrdinalTransformer**: Ordinal numbers in Arabic

### 1.10 Schema Editor
- **Entity Management**: Add, edit, delete entities
- **Field Management**: Configure field type, validation, formulas, options
- **Relationship Editor**: Define entity relationships
- **Control Rules**: Configure inter-field dependencies
- **Batch Save**: All changes saved together

### 1.11 App Type System
- **Multi-App Support**: Different configurations for different report types
- **App Type Manager**: View, edit, set default, delete app types
- **App Type Wizard**: Create new app type with database initialization
- **Per-App Templates**: Separate Word templates per app type

### 1.12 History/Undo System
- **Undo/Redo**: Ctrl+Z/Ctrl+Y for field changes
- **Command Pattern**: SetFieldValueCommand, OverrideCommand
- **Dirty Tracking**: Track unsaved changes

---

## 2. CORE BUSINESS RULES

### 2.1 Data Integrity Rules
- Every project must have an associated app_type_id
- Fields must be unique by ID within an entity
- Formulas cannot have circular dependencies
- Control chains limited to depth 10 to prevent infinite loops
- Override values must pass field validation to be ACCEPTED

### 2.2 Value Resolution Priority
1. **Override value** (if ACCEPTED and should_use_in_generation)
2. **Formula computed value** (if formula field)
3. **Raw value from database**

### 2.3 Validation Rules
- Required fields block report generation if empty
- Numeric fields enforce min/max/integer constraints
- Text fields enforce length and pattern constraints
- Date fields enforce range and past/future constraints

### 2.4 Formula Evaluation Rules
- Dependencies extracted using `{{field_id}}` pattern
- Evaluation order determined by dependency graph
- Only allowed functions: abs, min, max, round, sum, pow, upper, lower, strip, concat, if_else, is_empty, coalesce
- Dependency changes trigger re-evaluation of affected formulas

### 2.5 Control Evaluation Rules
- VALUE_SET: Target field auto-populated when source changes
- VISIBILITY: Target field shown/hidden based on source value
- Exact value match has priority over default mapping
- Chain propagation: When A updates B, check if B has controls too

### 2.6 Override State Transitions
```
  [New Override] → PENDING
  PENDING + User Accept → ACCEPTED
  PENDING + Validation Fail → INVALID
  ACCEPTED + Write to Word → SYNCED
  SYNCED + Non-Formula → Cleanup (deleted)
  SYNCED + Formula → SYNCED_FORMULA (preserved)
```

### 2.7 Naming Rules
- **manual**: User provides name
- **autoincrement**: Sequential 1, 2, 3...
- **pattern**: Template tokens ({YYYY}, {MM}, {DD}, {#}, {##}, etc.)
- **uuid**: Random UUID generation

### 2.8 File Field Rules
- min_files/max_files constraints per field
- Allowed extensions filtering
- Size limits
- Files copied to project directory on save

---

## 3. SIDE EFFECTS (I/O, DATABASE, FILES, APIs)

### 3.1 Database Operations

**Global Config Database (config.db)**
- Read: App types registry, languages, templates catalog, recent projects
- Write: App type creation, template registration, recent projects update

**App Type Config Database (app_types/{name}/config.db)**
- Read: Entities, fields, relationships, validation rules, options, formulas, output mappings
- Write: Schema editor changes (entities, fields, relationships, controls)
- Tables: entities, fields, relationships, validation_rules, field_options, dropdowns, dropdown_options, formulas, auto_generate, file_configs, ui_configs, output_mappings, control_relations

**Project Database (Projects/{name}/project.db)**
- Read: Project metadata, entity data, overrides, sequences
- Write: Form data saves, override state changes, sequence increments
- Tables: Dynamic per-schema + metadata, sequences, overrides

### 3.2 File System Operations

**Project Files**
- Create: Project directory structure
- Read: Project.db, attached files
- Write: Save project data, copy uploaded files
- Delete: Orphaned files on cleanup

**Templates**
- Read: Word templates (.docx), Excel templates (.xlsx)
- Copy: Template files to app type directories

**Generated Documents**
- Write: Generated Word documents to project folder
- Write: PDF exports with stamps/signatures

**Configuration Files**
- Read/Write: `config/user_config.json`
- Read/Write: `config/recent_projects.json`
- Read: `config/excel_ranges.json`, `config/table_columns.json`

**Resources**
- Read: `resources/assets/stamp.png`, `resources/assets/signature.png`

### 3.3 External Library Calls

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

### 3.4 API Integrations

**Google GenAI** (`services/ai_service.py`)
- AI integration (currently minimal usage)
- Potential for AI-assisted report generation

---

## 4. HIDDEN OR IMPLICIT BEHAVIORS

### 4.1 Automatic Behaviors
- **Auto-save before generate**: Project saved automatically before report generation
- **Navigation state persistence**: Last tab/position restored on project reopen
- **Tab history**: Back/forward navigation within tabs
- **Thread-local DB connections**: Each thread gets its own SQLite connection
- **PRAGMA settings**: foreign_keys=ON, journal_mode=WAL automatically applied
- **Recent projects auto-update**: On project open/create

### 4.2 Implicit Data Transformations
- **Row-to-dict conversion**: SQLite rows automatically converted to dictionaries
- **JSON serialization**: Complex types stored as JSON strings in SQLite
- **Transformer application**: Output values automatically transformed before writing to documents

### 4.3 Implicit Cleanup Operations
- **Orphaned file cleanup**: Files not referenced by any field deleted on save
- **SYNCED override cleanup**: Non-formula SYNCED overrides deleted after generation
- **Conflict cleanup**: Resolved conflicts cleared after successful generation

### 4.4 Default Value Resolution
- Empty string defaults for missing text fields
- Zero defaults for missing numeric fields
- None handling throughout for optional fields
- Default transformer returns empty string if field missing

### 4.5 Signal Emissions (Observer Pattern)
- Validation state changes emit signals for UI updates
- History manager emits can_undo/can_redo signals
- Formula changes propagate to dependent fields
- Control evaluations propagate through chains

### 4.6 State Management Side Effects
- **ApplicationState**: Global singleton affects all services
- **ProjectContext**: Per-project state affects field resolution
- **WidgetRegistry**: Widgets register themselves for formula updates

### 4.7 Error Recovery Behaviors
- **CircularDependencyError**: Max depth 10 prevents infinite loops
- **FormulaEvaluationError**: Returns None, doesn't crash
- **ValidationError**: Sets field state to invalid, doesn't block UI
- **DatabaseError**: Wraps SQLite errors with context

### 4.8 Cascade Effects
- Deleting entity cascades to fields, relationships, validations
- Deleting dropdown cascades to all field_options using it
- Changing field type clears incompatible validations/options
- Renaming entity/field updates all references

### 4.9 Implicit File Operations
- Files uploaded but not saved exist in temp location until project save
- Multiple files field tracks order for numbering
- File metadata (dimensions, size) read on upload

### 4.10 Threading Considerations
- Thread-local database connections
- UI operations on main thread only
- Background tasks for long operations (progress dialog)

---

## 5. ARCHITECTURE SUMMARY

### 5.1 Layer Structure
```
UI Layer (PyQt6)
├── MainWindow
├── Dialogs (50+ dialog types)
├── Widgets (smart, base, input types)
├── Dynamic form generation
└── Controllers (project, navigation, data)

Service Layer
├── Document services (Excel, Word, PDF)
├── Template engine
├── Attachment manager
├── Feature plugins (selection, keyboard, zoom, etc.)
└── Value resolver

Core Layer
├── Schema management
├── Validation system
├── Formula system
├── Control system
├── Override system
├── Naming system
├── Persistence (repositories, backends)
├── State management
└── History/Undo
```

### 5.2 Database Hierarchy
```
config.db (global)
└── app_types/{name}/config.db (per app type)
    └── Projects/{name}/project.db (per project)
```

### 5.3 Key Patterns Used
- **Dependency Injection**: ServiceContainer for service wiring
- **Repository Pattern**: Separate data access from business logic
- **Aggregate Pattern**: FieldAggregate bundles related field data
- **Factory Pattern**: FieldFactory creates widgets dynamically
- **Observer Pattern**: Signals for state changes
- **Command Pattern**: Undo/redo with command objects
- **Strategy Pattern**: Validators, Transformers, NamingStrategies

---

# Phase 2: Architectural Diagnosis

## 6. ARCHITECTURAL PAIN POINTS

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

## 7. ROOT CAUSES (Why the System Became Complex)

### 7.1 Iterative AI-Assisted Development Without Architecture
- Features added incrementally without upfront design
- Each feature solved immediate problem but increased coupling
- No clear boundaries established between layers
- Refactoring happened within existing structure rather than challenging it

### 7.2 Convenience Over Decoupling
- PyQt6 signals used everywhere because they're convenient
- Singletons used because they're easy to access
- Direct database queries because repositories are "more code"
- Concrete types because interfaces feel like overhead

### 7.3 Missing Abstractions
- No repository layer between domain and database
- No view models between UI and domain
- No event bus independent of PyQt6
- No clear service interfaces (just concrete classes)

### 7.4 Feature Creep Without Refactoring Budget
- Override system added → required state tracking → added to existing classes
- Formula system added → required dependency tracking → coupled to existing validators
- Control system added → required chain evaluation → embedded in widgets
- Each feature expanded existing classes rather than creating new bounded contexts

### 7.5 Testing Not Driving Design
- No unit tests forcing decoupling
- Integration tests (if any) mask coupling problems
- Classes not designed for testability
- Global state makes isolated testing impossible

### 7.6 Domain Complexity Absorbed by Infrastructure
- Business rules (validation, formulas, controls) scattered across layers
- No domain model - just data classes + services with SQL
- State transitions implicit rather than explicit (state machines)
- Value objects missing (field values, validation results as primitives)

---

## 8. RISKS IF SYSTEM KEEPS GROWING

### 8.1 Maintenance Risks (High)
- **Change amplification**: Modifying one feature requires changes in 5+ files
- **Cognitive load**: Understanding any feature requires understanding entire system
- **Regression risk**: No isolated tests, any change can break unrelated features
- **Onboarding cost**: New developers need weeks to understand the architecture

### 8.2 Extension Risks (High)
- **New field type**: Requires modifying FieldFactory, ValidationManager, potentially UI widgets
- **New output format**: Requires modifying OutputMappingManager, TemplateEngine
- **New app type feature**: Requires modifying AppTypeManager (1147 lines)
- **New validation rule**: Requires modifying hard-coded validator selection

### 8.3 Scalability Risks (Medium)
- **Memory leaks**: Strong references in registries without cleanup
- **Thread safety**: Global singletons with mutable state
- **Performance**: No caching strategy, repeated database queries

### 8.4 Technical Debt Risks (Critical)
- **Framework lock-in**: Cannot port to web/mobile without complete rewrite
- **Library upgrades**: PyQt6 upgrade could break core layer
- **Testing debt**: Adding tests now requires massive refactoring first

### 8.5 Team Risks (Medium-High)
- **Bus factor**: Only someone who understands everything can make changes safely
- **Parallel development**: Two developers cannot work on different features without conflicts
- **Code review**: Impossible to review changes without full context

---

## 9. REWRITE STRATEGY RECOMMENDATION

### 9.1 Assessment: Big Bang vs Incremental

| Factor | Big Bang | Incremental |
|--------|----------|-------------|
| **Current test coverage** | None/minimal → favors Big Bang | - |
| **Clear requirements** | Yes (Phase 1 audit) → favors Big Bang | - |
| **Business pressure** | Development stage, no users → favors Big Bang | - |
| **Team size** | Likely 1-2 people → favors Big Bang | - |
| **Coupling level** | Extreme → makes Incremental very hard | - |
| **Domain complexity** | Moderate → manageable in Big Bang | - |

### 9.2 Recommendation: **Controlled Big Bang Rewrite**

**Rationale**:
1. The coupling is too severe for incremental extraction
2. No existing tests to preserve behavior during incremental changes
3. Still in development - no production users to migrate
4. Clear functional requirements from Phase 1 audit
5. The "strangler fig" pattern would take longer than rewriting

### 9.3 Rewrite Approach

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

### 9.4 Risk Mitigation

- **Keep old code running**: New app built alongside, not replacing
- **Feature parity checklist**: Use Phase 1 audit as acceptance criteria
- **Parallel testing**: Run both apps with same inputs, compare outputs
- **Incremental migration**: Move one feature at a time once new app stable

---

## 10. SUMMARY

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

---

# Phase 3: Target Architecture Design

## 11. HIGH-LEVEL ARCHITECTURE

### 11.1 Architecture Style: Clean Architecture + Domain-Driven Design

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

### 11.2 Dependency Rule

```
DEPENDENCIES POINT INWARD ONLY

Presentation → Application → Domain ← Infrastructure
                              ↑
                              │
                    Infrastructure implements
                    Domain interfaces
```

**Key Principle**: Domain layer has ZERO external dependencies. No PyQt6, no SQLite, no file system.

---

## 12. FOLDER STRUCTURE

```
soil_report_v2/
├── pyproject.toml                    # Project config, dependencies
├── pytest.ini                        # Test configuration
│
├── src/
│   └── soil_report/
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
│       │   │   └── specification.py  # Specification pattern base
│       │   │
│       │   ├── schema/               # Schema Bounded Context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   ├── app_type.py           # AppType aggregate root
│       │   │   │   ├── entity_definition.py  # EntityDefinition
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
│       │   │   │   ├── validation_result.py  # Immutable result
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
│       │   │   │   └── ...
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
│       │   │   │   ├── create_project.py
│       │   │   │   ├── open_project.py
│       │   │   │   ├── save_project.py
│       │   │   │   ├── close_project.py
│       │   │   │   └── update_field_value.py
│       │   │   ├── schema/
│       │   │   │   ├── create_app_type.py
│       │   │   │   ├── add_entity.py
│       │   │   │   ├── add_field.py
│       │   │   │   └── update_field.py
│       │   │   ├── override/
│       │   │   │   ├── accept_override.py
│       │   │   │   ├── reject_override.py
│       │   │   │   └── cleanup_synced.py
│       │   │   └── document/
│       │   │       ├── generate_report.py
│       │   │       └── export_pdf.py
│       │   │
│       │   ├── queries/              # Read operations (CQRS)
│       │   │   ├── __init__.py
│       │   │   ├── project/
│       │   │   │   ├── get_project.py
│       │   │   │   ├── get_field_value.py
│       │   │   │   └── get_recent_projects.py
│       │   │   ├── schema/
│       │   │   │   ├── get_schema.py
│       │   │   │   ├── get_entities.py
│       │   │   │   └── get_fields.py
│       │   │   ├── validation/
│       │   │   │   └── validate_field.py
│       │   │   └── formula/
│       │   │       └── compute_formula.py
│       │   │
│       │   ├── services/             # Application services
│       │   │   ├── __init__.py
│       │   │   ├── project_service.py        # Orchestrates project ops
│       │   │   ├── schema_service.py         # Orchestrates schema ops
│       │   │   ├── validation_service.py     # Batch validation
│       │   │   ├── formula_service.py        # Formula orchestration
│       │   │   ├── control_service.py        # Control evaluation
│       │   │   └── document_service.py       # Report generation
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
│       │   │   │   │   ├── app_type_repository.py
│       │   │   │   │   ├── schema_repository.py
│       │   │   │   │   ├── project_repository.py
│       │   │   │   │   ├── validation_repository.py
│       │   │   │   │   ├── formula_repository.py
│       │   │   │   │   ├── override_repository.py
│       │   │   │   │   └── template_repository.py
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
│       │   │   └── recent_projects.py        # Recent projects file
│       │   │
│       │   ├── documents/            # Document library adapters
│       │   │   ├── __init__.py
│       │   │   ├── excel/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── xlwings_adapter.py    # xlwings implementation
│       │   │   │   └── interfaces.py         # IExcelService
│       │   │   ├── word/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── docx_adapter.py       # python-docx implementation
│       │   │   │   └── interfaces.py         # IWordService
│       │   │   └── pdf/
│       │   │       ├── __init__.py
│       │   │       ├── pymupdf_adapter.py    # PyMuPDF implementation
│       │   │       └── interfaces.py         # IPdfService
│       │   │
│       │   ├── events/               # Event infrastructure
│       │   │   ├── __init__.py
│       │   │   ├── in_memory_bus.py          # Simple event bus
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
│           │   ├── main_window_vm.py
│           │   ├── project_vm.py
│           │   ├── field_vm.py
│           │   ├── validation_vm.py
│           │   ├── schema_editor_vm.py
│           │   └── override_vm.py
│           │
│           ├── views/                # PyQt6 Views
│           │   ├── __init__.py
│           │   ├── main_window.py            # Main window (thin)
│           │   ├── welcome_view.py
│           │   ├── project_view.py
│           │   └── tabs/
│           │       ├── dynamic_tab.py
│           │       └── file_tab.py
│           │
│           ├── widgets/              # Reusable widgets
│           │   ├── __init__.py
│           │   ├── fields/
│           │   │   ├── base_field.py
│           │   │   ├── text_field.py
│           │   │   ├── number_field.py
│           │   │   ├── date_field.py
│           │   │   ├── option_field.py
│           │   │   ├── formula_field.py
│           │   │   └── file_field.py
│           │   ├── common/
│           │   │   ├── collapsible_group.py
│           │   │   └── flow_layout.py
│           │   └── file/
│           │       ├── gallery.py
│           │       ├── file_preview.py
│           │       └── file_details.py
│           │
│           ├── dialogs/              # Modal dialogs
│           │   ├── __init__.py
│           │   ├── settings_dialog.py
│           │   ├── override_dialog.py
│           │   ├── template_dialog.py
│           │   ├── conflict_dialog.py
│           │   ├── app_type_dialog.py
│           │   ├── figure_numbering_dialog.py
│           │   └── schema_editor/
│           │       ├── schema_editor_dialog.py
│           │       ├── entity_panel.py
│           │       └── field_panel.py
│           │
│           ├── factories/            # Widget factories
│           │   ├── __init__.py
│           │   ├── field_widget_factory.py   # Creates field widgets
│           │   └── dialog_factory.py
│           │
│           ├── adapters/             # UI ↔ Application adapters
│           │   ├── __init__.py
│           │   ├── qt_event_adapter.py       # Domain events → Qt signals
│           │   └── history_adapter.py        # Undo/Redo via QUndoStack
│           │
│           └── styles/
│               ├── __init__.py
│               └── theme.py
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

---

## 13. CORE DOMAIN ENTITIES

### 13.1 Common Base Classes

```
Entity (Abstract)
├── id: EntityId                    # Strongly typed identifier
├── created_at: datetime
├── updated_at: datetime
└── domain_events: List[DomainEvent]  # Collected events

AggregateRoot(Entity)
├── version: int                    # Optimistic concurrency
└── apply_event(event) → None       # Event sourcing ready

ValueObject (Abstract)
├── Immutable (frozen dataclass)
├── Equality by value
└── No identity

DomainEvent (Abstract)
├── event_id: UUID
├── occurred_at: datetime
├── aggregate_id: str
└── aggregate_type: str
```

### 13.2 Schema Context Entities

```
AppType (AggregateRoot)
├── id: AppTypeId
├── name: str
├── description: str
├── is_default: bool
├── entities: List[EntityDefinition]
├── version: SchemaVersion
│
├── add_entity(entity) → Result
├── remove_entity(entity_id) → Result
└── validate() → ValidationResult

EntityDefinition (Entity)
├── id: EntityId
├── name: str
├── label: str
├── entity_type: EntityType (SINGLETON | COLLECTION)
├── sort_order: int
├── fields: List[FieldDefinition]
│
├── add_field(field) → Result
├── remove_field(field_id) → Result
└── reorder_fields(order) → Result

FieldDefinition (Entity)
├── id: FieldId
├── name: str
├── label: str
├── field_type: FieldType
├── required: bool
├── default_value: Optional[Any]
├── sort_order: int
│
└── with_type(new_type) → FieldDefinition  # Immutable update
```

### 13.3 Project Context Entities

```
Project (AggregateRoot)
├── id: ProjectId
├── path: ProjectPath
├── app_type_id: AppTypeId
├── name: str
├── created_at: datetime
├── field_values: Dict[FieldId, FieldValue]
│
├── set_value(field_id, value) → Result
├── get_value(field_id) → Optional[FieldValue]
├── get_computed_value(field_id) → Any    # With formula/override
└── is_dirty() → bool

FieldValue (Entity)
├── id: FieldValueId
├── field_id: FieldId
├── raw_value: Any
├── override: Optional[Override]
├── computed_value: Optional[Any]         # Formula result cache
│
├── apply_override(override) → FieldValue
├── clear_override() → FieldValue
└── recompute(formula_result) → FieldValue
```

### 13.4 Validation Context

```
ValidationRule (AggregateRoot)
├── id: ValidationRuleId
├── field_id: FieldId
├── constraints: List[Constraint]
│
└── validate(value) → ValidationResult

Constraint (ValueObject) - Sum Type
├── RequiredConstraint
├── MinLengthConstraint(min: int)
├── MaxLengthConstraint(max: int)
├── PatternConstraint(regex: str)
├── MinValueConstraint(min: Decimal)
├── MaxValueConstraint(max: Decimal)
├── IntegerOnlyConstraint
├── MinDateConstraint(min: date)
├── MaxDateConstraint(max: date)
└── CustomConstraint(validator_fn: str)

ValidationResult (ValueObject)
├── is_valid: bool
├── errors: List[ValidationError]
└── field_id: FieldId

ValidationError (ValueObject)
├── constraint_type: str
├── message: str
└── details: Dict[str, Any]
```

### 13.5 Formula Context

```
Formula (AggregateRoot)
├── id: FormulaId
├── field_id: FieldId
├── expression: Expression
├── dependencies: FrozenSet[FieldId]
│
├── evaluate(context: EvaluationContext) → Result[Any, FormulaError]
└── get_affected_fields() → FrozenSet[FieldId]

Expression (ValueObject)
├── raw: str                              # "{{depth_to}} - {{depth_from}}"
├── tokens: Tuple[Token, ...]             # Parsed tokens
└── is_valid: bool

EvaluationContext (ValueObject)
├── values: FrozenDict[FieldId, Any]      # Field values snapshot
└── functions: FrozenDict[str, Callable]  # Allowed functions

DependencyGraph (ValueObject)
├── graph: FrozenDict[FieldId, FrozenSet[FieldId]]
│
├── get_evaluation_order() → Tuple[FieldId, ...]
├── get_affected_by(field_id) → FrozenSet[FieldId]
└── detect_cycles() → List[Tuple[FieldId, ...]]
```

### 13.6 Control Context

```
ControlRule (AggregateRoot)
├── id: ControlRuleId
├── source_field: FieldId
├── target_field: FieldId
├── effect_type: ControlEffectType
├── mappings: List[ControlMapping]
│
└── evaluate(source_value) → EffectResult

ControlEffectType (Enum)
├── VALUE_SET
├── VISIBILITY
├── ENABLE
└── OPTIONS_FILTER

ControlMapping (ValueObject)
├── source_value: Optional[Any]           # None = default
├── target_value: Any
├── priority: int

EffectResult (ValueObject)
├── effect_type: ControlEffectType
├── target_field: FieldId
├── value: Any                            # New value, visibility, etc.
```

### 13.7 Override Context

```
Override (AggregateRoot)
├── id: OverrideId
├── field_id: FieldId
├── system_value: Any
├── report_values: Tuple[Any, ...]        # May have multiple
├── state: OverrideState
├── is_formula_field: bool
│
├── accept() → Result[Override, OverrideError]
├── reject() → Result[Override, OverrideError]
├── sync() → Result[Override, OverrideError]
├── can_transition_to(state) → bool
└── get_effective_value() → Any

OverrideState (ValueObject with transitions)
├── PENDING
├── ACCEPTED
├── INVALID
├── SYNCED
├── SYNCED_FORMULA
│
└── allowed_transitions: Dict[State, Set[State]]
```

### 13.8 Document Context

```
Template (AggregateRoot)
├── id: TemplateId
├── app_type_id: AppTypeId
├── name: str
├── path: FilePath
├── is_default: bool
├── output_mappings: List[OutputMapping]

OutputMapping (Entity)
├── id: MappingId
├── field_id: FieldId
├── target_type: OutputType (WORD | EXCEL | PDF)
├── target_tag: ContentTag              # Word content control
├── transformer_id: Optional[TransformerId]
├── default_value: Optional[str]
```

### 13.9 Transformer Context

```
Transformer (Interface)
├── id: TransformerId
├── name: str
├── supported_types: Set[FieldType]
│
├── to_output(value: Any) → str         # Raw → Display
└── from_output(text: str) → Any        # Display → Raw

# Implementations (each in separate file)
├── SuffixTransformer
├── PrefixTransformer
├── MapTransformer
├── DateFormatTransformer
├── ArabicNumberTransformer
└── ...
```

---

## 14. APPLICATION LAYER - USE CASES

### 14.1 Command Pattern (Write Operations)

```
Command (Abstract)
├── Immutable input DTO
└── Returns Result[Output, Error]

CommandHandler (Interface)
└── execute(command) → Result

Example: UpdateFieldValueCommand
├── Input: project_id, field_id, new_value
├── Process:
│   1. Load Project aggregate
│   2. Call project.set_value()
│   3. Validate new value
│   4. Evaluate affected formulas
│   5. Evaluate affected controls
│   6. Save via UnitOfWork
│   7. Publish FieldValueChanged event
└── Output: UpdatedFieldDTO
```

### 14.2 Query Pattern (Read Operations)

```
Query (Abstract)
├── Immutable input
└── Returns DTO (never domain entity)

QueryHandler (Interface)
└── execute(query) → DTO

Example: GetFieldValueQuery
├── Input: project_id, field_id
├── Process:
│   1. Load from read-optimized store
│   2. Apply value resolution (override → formula → raw)
│   3. Map to DTO
└── Output: FieldValueDTO
```

### 14.3 Application Services

```
ProjectService
├── create_project(name, app_type_id, path) → ProjectDTO
├── open_project(path) → ProjectDTO
├── save_project(project_id) → Result
├── close_project(project_id) → Result
└── get_recent_projects() → List[RecentProjectDTO]

ValidationService
├── validate_field(project_id, field_id, value) → ValidationResultDTO
├── validate_form(project_id, entity_id) → FormValidationDTO
└── get_blocking_issues(project_id) → List[ValidationErrorDTO]

FormulaService
├── compute_formula(project_id, field_id) → Any
├── recompute_affected(project_id, changed_field_id) → Dict[FieldId, Any]
└── get_dependency_graph(app_type_id) → DependencyGraphDTO

DocumentService
├── generate_report(project_id, template_id) → ReportDTO
├── export_pdf(project_id, options) → PdfResultDTO
└── detect_conflicts(project_id) → List[ConflictDTO]
```

### 14.4 Event Handlers

```
OnFieldValueChanged
├── Trigger: FieldValueChanged event
├── Actions:
│   1. Recompute dependent formulas
│   2. Evaluate triggered controls
│   3. Re-validate affected fields
│   4. Update dirty tracking
└── Publishes: FormulasRecomputed, ControlsEvaluated

OnProjectSaved
├── Trigger: ProjectSaved event
├── Actions:
│   1. Cleanup orphaned files
│   2. Update recent projects
│   3. Clear dirty flags
└── Publishes: None

OnOverrideAccepted
├── Trigger: OverrideAccepted event
├── Actions:
│   1. Update field value
│   2. Mark override as ACCEPTED
│   3. Trigger formula recompute if needed
└── Publishes: FieldValueChanged
```

---

## 15. INFRASTRUCTURE ADAPTERS

### 15.1 Repository Implementations

```
SQLiteProjectRepository implements IProjectRepository
├── __init__(connection: SQLiteConnection)
├── get_by_id(id) → Optional[Project]
├── save(project) → None
├── delete(id) → None
└── exists(path) → bool

# Maps domain entities ↔ database rows
# Uses mappers to avoid ORM dependency
```

### 15.2 Document Adapters

```
XlwingsExcelAdapter implements IExcelService
├── __init__(app_visible: bool = False)
├── open_workbook(path) → Workbook
├── read_cell(sheet, cell) → Any
├── write_cell(sheet, cell, value) → None
├── convert_to_image(range) → bytes
└── close_workbook(workbook) → None

DocxWordAdapter implements IWordService
├── __init__()
├── open_document(path) → Document
├── get_content_controls() → List[ContentControl]
├── set_content_control(tag, value) → None
└── save_document(document, path) → None

PyMuPdfAdapter implements IPdfService
├── __init__()
├── open_pdf(path) → Pdf
├── add_image(page, image, position) → None
├── set_password(password) → None
└── save_pdf(pdf, path) → None
```

### 15.3 Event Bus Implementation

```
InMemoryEventBus implements IEventBus
├── _handlers: Dict[Type[Event], List[Handler]]
│
├── subscribe(event_type, handler) → None
├── publish(event) → None
├── publish_all(events) → None
└── clear() → None

# No PyQt6 dependency - pure Python
# Handlers executed synchronously in same thread
# Can be swapped for async implementation later
```

### 15.4 Unit of Work

```
SQLiteUnitOfWork implements IUnitOfWork
├── _connection: SQLiteConnection
├── _repositories: Dict[Type, Repository]
├── _committed: bool
│
├── __enter__() → UnitOfWork
├── __exit__() → None
├── commit() → None
├── rollback() → None
└── repository(type) → Repository
```

---

## 16. PRESENTATION LAYER

### 16.1 View Models (MVVM Pattern)

```
FieldViewModel
├── field_id: str (readonly)
├── label: str (readonly)
├── field_type: str (readonly)
├── value: Any (observable)
├── display_value: str (computed)
├── is_valid: bool (observable)
├── error_message: str (observable)
├── is_visible: bool (observable)
├── is_readonly: bool (observable)
│
├── set_value(value) → None           # Calls application layer
├── validate() → None
└── on_value_changed: Callable        # For UI binding

ProjectViewModel
├── project_id: str
├── name: str
├── is_dirty: bool (observable)
├── fields: Dict[str, FieldViewModel]
├── tabs: List[TabViewModel]
│
├── save() → None
├── close() → None
└── generate_report() → None
```

### 16.2 Qt Signal Adapter

```
QtEventAdapter
├── _event_bus: IEventBus
├── _signal_emitter: QObject
│
├── connect() → None                  # Subscribe to domain events
├── disconnect() → None
└── _on_domain_event(event) → None    # Emit Qt signal

# Bridges domain events to Qt signals
# Only place PyQt6 touches domain
```

### 16.3 Widget Factory (Open/Closed)

```
FieldWidgetFactory
├── _registry: Dict[FieldType, Type[BaseFieldWidget]]
│
├── register(field_type, widget_class) → None
├── create(field_vm: FieldViewModel) → BaseFieldWidget
└── supports(field_type) → bool

# Adding new field type = register new class
# No modification to factory code
```

---

## 17. DEPENDENCY INJECTION SETUP

```python
# main.py - Composition Root

def create_container() -> Container:
    container = Container()

    # Infrastructure
    container.register(SQLiteConnection, singleton=True)
    container.register(IEventBus, InMemoryEventBus, singleton=True)
    container.register(IUnitOfWork, SQLiteUnitOfWork)

    # Repositories
    container.register(IProjectRepository, SQLiteProjectRepository)
    container.register(ISchemaRepository, SQLiteSchemaRepository)
    container.register(IValidationRepository, SQLiteValidationRepository)
    # ... more repositories

    # Document adapters
    container.register(IExcelService, XlwingsExcelAdapter)
    container.register(IWordService, DocxWordAdapter)
    container.register(IPdfService, PyMuPdfAdapter)

    # Application services
    container.register(ProjectService)
    container.register(ValidationService)
    container.register(FormulaService)
    container.register(DocumentService)

    # Event handlers
    container.register(OnFieldValueChanged)
    container.register(OnProjectSaved)

    # Presentation (only PyQt6 code here)
    container.register(QtEventAdapter)
    container.register(FieldWidgetFactory)

    return container
```

---

## 18. DESIGN PATTERNS & JUSTIFICATIONS

| Pattern | Location | Justification |
|---------|----------|---------------|
| **Aggregate Root** | Domain entities | Ensures consistency boundaries, controls access to child entities |
| **Value Object** | All immutable domain data | Thread-safe, no defensive copying, easy equality |
| **Repository** | Data access abstraction | Decouples domain from persistence, enables testing with fakes |
| **Unit of Work** | Transaction management | Atomic operations, tracks changes, single commit point |
| **Factory** | Widget creation | Open/Closed - add field types without modifying factory |
| **Strategy** | Validators, Transformers | Interchangeable algorithms, easy to add new ones |
| **Specification** | Validation rules | Composable business rules, reusable predicates |
| **CQRS** | Commands/Queries | Separate read/write models, optimized for each use case |
| **Event-Driven** | Cross-context communication | Loose coupling between bounded contexts |
| **MVVM** | Presentation layer | Testable UI logic, clean separation from views |
| **Adapter** | Infrastructure integrations | Isolates external libraries, enables swapping |
| **Dependency Injection** | Entire application | Testability, loose coupling, configuration flexibility |
| **Result Monad** | Error handling | Explicit error handling, no exceptions for business errors |

---

## 19. TESTABILITY BY LAYER

### Domain Layer (100% unit testable)
- No external dependencies
- Pure functions and immutable data
- Test validation rules, formula evaluation, control logic
- Mock nothing - just create objects

### Application Layer (unit + integration testable)
- Unit test with fake repositories
- Integration test with real SQLite (in-memory)
- Test command/query handlers in isolation

### Infrastructure Layer (integration testable)
- Test repository implementations with real DB
- Test document adapters with real files (temp dir)
- Test mappers with sample data

### Presentation Layer (unit + E2E testable)
- Unit test ViewModels (no Qt required)
- E2E test with Qt test framework
- Snapshot test widget rendering

---

## 20. MIGRATION PATH FROM OLD SYSTEM

### Step 1: Domain First
- Build domain layer completely
- 100% test coverage
- No UI, no database

### Step 2: Infrastructure Second
- Implement repositories
- Build database adapters
- Test with old database files

### Step 3: Application Layer
- Build use cases
- Wire event handlers
- Test full business flows

### Step 4: Presentation Last
- Build ViewModels
- Create widgets
- Connect to application layer

### Step 5: Data Migration
- Create migration script
- Map old DB schema → new schema
- Verify with comparison tests

---

# Phase 4: Incremental Rebuild Plan

## 21. IMPLEMENTATION STRATEGY

### 21.1 Core Principles

1. **Domain First**: Build and test domain logic before any infrastructure
2. **Vertical Slices**: Complete one feature end-to-end before starting next
3. **Test-Driven**: Write tests before implementation
4. **Old App as Oracle**: Compare outputs with existing app to verify correctness
5. **No Big Bang UI**: Build minimal UI incrementally as features complete

### 21.2 Risk Mitigation

- Keep old app running throughout
- Each milestone produces working (partial) software
- Rollback point at each checkpoint
- Feature flags for gradual migration

---

## 22. MILESTONE OVERVIEW

```
M1: Foundation (Week 1-2)
├── Project setup, base classes, Result monad
└── ✓ Can run tests

M2: Validation Domain (Week 2-3)
├── Constraints, validators, validation rules
└── ✓ Validation logic matches old app

M3: Schema Domain (Week 3-4)
├── Field types, entities, app types
└── ✓ Can load schema from old database

M4: Formula Domain (Week 4-5)
├── Parser, evaluator, dependency graph
└── ✓ Formulas compute same results as old app

M5: Control Domain (Week 5-6)
├── Control rules, effect evaluation
└── ✓ Controls produce same effects as old app

M6: Project Domain (Week 6-7)
├── Project, field values, value resolution
└── ✓ Can load/save project data

M7: Override Domain (Week 7-8)
├── Override state machine, conflict detection
└── ✓ Override logic matches old app

M8: Infrastructure (Week 8-10)
├── SQLite repositories, file storage
└── ✓ Full data persistence working

M9: Document Generation (Week 10-12)
├── Word/Excel/PDF adapters, transformers
└── ✓ Generated documents match old app

M10: Application Layer (Week 12-14)
├── Commands, queries, event handlers
└── ✓ Business flows work end-to-end

M11: Presentation (Week 14-18)
├── ViewModels, widgets, main window
└── ✓ Full UI functional

M12: Migration & Polish (Week 18-20)
├── Data migration, testing, documentation
└── ✓ Ready for production
```

---

## 23. DETAILED IMPLEMENTATION STEPS

### MILESTONE 1: Foundation (Days 1-10)

#### Step 1.1: Project Setup
**What**: Create project structure, configure tooling
**Why**: Foundation for all other work

```
Tasks:
□ Create soil_report_v2/ directory
□ Initialize pyproject.toml with dependencies
□ Configure pytest, mypy, ruff
□ Create src/soil_report/ package structure
□ Create tests/ structure
□ Set up CI pipeline (GitHub Actions)
```

**Verification**:
- `pytest` runs with 0 tests
- `mypy src/` passes
- `ruff check src/` passes

#### Step 1.2: Domain Common Module
**What**: Base classes for all domain objects
**Why**: Consistent patterns across all bounded contexts

```
Files to create:
□ domain/common/entity.py
  - Entity base class with id, created_at, updated_at
  - AggregateRoot with version, domain_events
□ domain/common/value_object.py
  - ValueObject base (frozen dataclass)
□ domain/common/events.py
  - DomainEvent base class
□ domain/common/result.py
  - Result[T, E] monad for error handling
□ domain/common/specification.py
  - Specification pattern base
```

**Verification**:
- Unit tests for Result monad (success, failure, map, flatMap)
- Unit tests for Entity equality and events
- Unit tests for ValueObject immutability

```python
# Example test
def test_result_success():
    result = Result.success(42)
    assert result.is_success
    assert result.value == 42

def test_result_failure():
    result = Result.failure("error")
    assert result.is_failure
    assert result.error == "error"
```

**Checkpoint 1**: ✓ Foundation complete, all base classes tested

---

### MILESTONE 2: Validation Domain (Days 11-20)

#### Step 2.1: Validation Value Objects
**What**: Constraint types and validation results
**Why**: Core building block for all field validation

```
Files to create:
□ domain/validation/value_objects/constraint.py
  - RequiredConstraint
  - MinLengthConstraint, MaxLengthConstraint
  - PatternConstraint
  - MinValueConstraint, MaxValueConstraint
  - IntegerOnlyConstraint
  - MinDateConstraint, MaxDateConstraint
□ domain/validation/value_objects/validation_result.py
  - ValidationResult (is_valid, errors, field_id)
□ domain/validation/value_objects/error_message.py
  - ValidationError (constraint_type, message, details)
```

**Verification**:
- Test each constraint type is immutable
- Test ValidationResult combines multiple errors

#### Step 2.2: Validators (Domain Services)
**What**: Validation logic for each field type
**Why**: Encapsulates validation rules

```
Files to create:
□ domain/validation/services/validator.py
  - IValidator interface
□ domain/validation/services/text_validator.py
  - Validates: required, min_length, max_length, pattern
□ domain/validation/services/number_validator.py
  - Validates: required, min_value, max_value, integer_only
□ domain/validation/services/date_validator.py
  - Validates: required, min_date, max_date
□ domain/validation/services/composite_validator.py
  - Combines multiple validators
```

**Verification**:
- Test each validator with valid/invalid inputs
- Test composite validator combines results
- **ORACLE TEST**: Extract validation rules from old app's config.db, run same inputs through new validators, compare results

```python
# Oracle test example
@pytest.mark.parametrize("field_id,value,expected_valid", [
    ("report_number", "2024-001", True),
    ("report_number", "", False),  # required
    ("boreholes_count", 5, True),
    ("boreholes_count", -1, False),  # min_value
])
def test_validation_matches_old_app(field_id, value, expected_valid):
    # Load validation rules from old config.db
    rules = load_old_validation_rules(field_id)
    validator = create_validator_from_rules(rules)
    result = validator.validate(value)
    assert result.is_valid == expected_valid
```

#### Step 2.3: ValidationRule Aggregate
**What**: Aggregate root managing field validation
**Why**: Single entry point for validation per field

```
Files to create:
□ domain/validation/entities/validation_rule.py
  - ValidationRule aggregate root
  - Contains list of Constraints
  - validate(value) → ValidationResult
□ domain/validation/repositories.py
  - IValidationRuleRepository interface
```

**Verification**:
- Test ValidationRule aggregates constraints
- Test domain events emitted on validation

**Checkpoint 2**: ✓ Validation domain complete, matches old app behavior

---

### MILESTONE 3: Schema Domain (Days 21-30)

#### Step 3.1: Schema Value Objects
**What**: Field types, IDs, versions
**Why**: Type-safe identifiers and field type behavior

```
Files to create:
□ domain/schema/value_objects/field_type.py
  - FieldType enum (STRING, TEXT, NUMBER, DATE, OPTION, FORMULA, FILE, etc.)
  - get_default_value() method
  - is_computed() property
□ domain/schema/value_objects/field_id.py
  - FieldId strongly typed ID
□ domain/schema/value_objects/entity_id.py
  - EntityId strongly typed ID
□ domain/schema/value_objects/schema_version.py
  - SchemaVersion for optimistic concurrency
```

**Verification**:
- Test FieldType enum covers all old app types
- Test strongly typed IDs prevent mixing

#### Step 3.2: Schema Entities
**What**: Field, Entity, AppType definitions
**Why**: Core schema model

```
Files to create:
□ domain/schema/entities/field_definition.py
  - FieldDefinition entity
  - Properties: id, name, label, field_type, required, default_value, sort_order
□ domain/schema/entities/entity_definition.py
  - EntityDefinition entity
  - Contains List[FieldDefinition]
  - entity_type: SINGLETON | COLLECTION
□ domain/schema/entities/app_type.py
  - AppType aggregate root
  - Contains List[EntityDefinition]
  - add_entity(), remove_entity(), validate()
□ domain/schema/repositories.py
  - ISchemaRepository interface
```

**Verification**:
- Test adding/removing fields from entity
- Test adding/removing entities from app type
- Test schema validation (no duplicate IDs, etc.)

#### Step 3.3: Schema Loading (Temporary Infrastructure)
**What**: Load schema from old app's config.db
**Why**: Verify schema model correctness against real data

```
Files to create (temporary, will be replaced):
□ infrastructure/persistence/sqlite/schema_loader.py
  - Load entities table from old config.db
  - Load fields table
  - Map to domain objects
```

**Verification**:
- **ORACLE TEST**: Load schema from old app, verify all entities/fields present
- Compare field counts, types, relationships

```python
def test_schema_loads_all_entities():
    old_db = Path("app_types/soil_investigation/config.db")
    schema = load_schema_from_old_db(old_db)

    # Known entities in old app
    assert "project_info" in [e.id for e in schema.entities]
    assert "boreholes" in [e.id for e in schema.entities]

    # Known field count
    project_info = schema.get_entity("project_info")
    assert len(project_info.fields) >= 20  # Approximate from old app
```

**Checkpoint 3**: ✓ Schema domain complete, loads old app schemas

---

### MILESTONE 4: Formula Domain (Days 31-42)

#### Step 4.1: Formula Value Objects
**What**: Expression parsing and evaluation context
**Why**: Safe formula handling

```
Files to create:
□ domain/formula/value_objects/expression.py
  - Expression value object
  - raw: str, tokens: Tuple[Token], is_valid: bool
  - extract_dependencies() → Set[FieldId]
□ domain/formula/value_objects/evaluation_context.py
  - EvaluationContext (frozen dict of field values)
  - ALLOWED_FUNCTIONS dict
□ domain/formula/value_objects/dependency_graph.py
  - DependencyGraph (immutable)
  - get_evaluation_order() → topological sort
  - get_affected_by(field_id) → Set[FieldId]
  - detect_cycles() → List[cycle]
```

**Verification**:
- Test expression parses {{field_id}} syntax
- Test dependency extraction
- Test topological sort order
- Test cycle detection

#### Step 4.2: Formula Services
**What**: Parser and evaluator
**Why**: Core formula computation

```
Files to create:
□ domain/formula/services/parser.py
  - parse(expression_str) → Expression
  - Tokenize {{field_id}} references
□ domain/formula/services/evaluator.py
  - evaluate(expression, context) → Result[Any, FormulaError]
  - Restricted eval with allowed functions only
  - Safe handling of missing values
□ domain/formula/services/dependency_resolver.py
  - build_graph(formulas) → DependencyGraph
  - resolve_order(changed_field) → List[FieldId]
```

**Verification**:
- Test parser with complex expressions
- Test evaluator with all allowed functions
- Test evaluator rejects dangerous code
- **ORACLE TEST**: Extract formulas from old app, compute with same inputs, compare results

```python
@pytest.mark.parametrize("formula_expr,inputs,expected", [
    ("{{depth_to}} - {{depth_from}}", {"depth_to": 10, "depth_from": 2}, 8),
    ("round({{value}} * 1.5, 2)", {"value": 3.333}, 5.0),
])
def test_formula_evaluation_matches_old_app(formula_expr, inputs, expected):
    expression = parser.parse(formula_expr)
    context = EvaluationContext(inputs)
    result = evaluator.evaluate(expression, context)
    assert result.value == expected
```

#### Step 4.3: Formula Aggregate
**What**: Formula entity with dependencies
**Why**: Manages formula lifecycle

```
Files to create:
□ domain/formula/entities/formula.py
  - Formula aggregate root
  - field_id, expression, dependencies
  - evaluate(context) → Result
□ domain/formula/repositories.py
  - IFormulaRepository interface
□ domain/formula/events.py
  - FormulaComputed event
```

**Verification**:
- Test formula stores dependencies correctly
- Test formula emits events on computation

**Checkpoint 4**: ✓ Formula domain complete, computations match old app

---

### MILESTONE 5: Control Domain (Days 43-52)

#### Step 5.1: Control Value Objects
**What**: Control effects and mappings
**Why**: Type-safe control definitions

```
Files to create:
□ domain/control/value_objects/control_effect.py
  - ControlEffectType enum (VALUE_SET, VISIBILITY, ENABLE, OPTIONS_FILTER)
□ domain/control/value_objects/control_mapping.py
  - ControlMapping (source_value, target_value, priority)
□ domain/control/value_objects/effect_result.py
  - EffectResult (effect_type, target_field, value)
```

#### Step 5.2: Control Services
**What**: Control evaluation logic
**Why**: Core inter-field dependency handling

```
Files to create:
□ domain/control/services/control_evaluator.py
  - evaluate_single(rule, source_value) → EffectResult
  - evaluate_chain(rules, changed_field, values) → List[EffectResult]
  - MAX_CHAIN_DEPTH = 10 (cycle protection)
```

**Verification**:
- Test single control evaluation
- Test chain evaluation (A→B→C)
- Test cycle detection stops at max depth
- **ORACLE TEST**: Load controls from old app, trigger with same values, compare effects

#### Step 5.3: ControlRule Aggregate
**What**: Control rule entity
**Why**: Encapsulates control definition

```
Files to create:
□ domain/control/entities/control_rule.py
  - ControlRule aggregate root
  - source_field, target_field, effect_type, mappings
  - evaluate(source_value) → EffectResult
□ domain/control/repositories.py
  - IControlRuleRepository interface
```

**Checkpoint 5**: ✓ Control domain complete, effects match old app

---

### MILESTONE 6: Project Domain (Days 53-65)

#### Step 6.1: Project Value Objects
**What**: Project identifiers and field data
**Why**: Type-safe project handling

```
Files to create:
□ domain/project/value_objects/project_id.py
  - ProjectId strongly typed
□ domain/project/value_objects/project_path.py
  - ProjectPath value object with validation
□ domain/project/value_objects/field_data.py
  - FieldData immutable snapshot
```

#### Step 6.2: Field Value Entity
**What**: Individual field value with override support
**Why**: Core data storage unit

```
Files to create:
□ domain/project/entities/field_value.py
  - FieldValue entity
  - raw_value, override (optional), computed_value (cache)
  - apply_override(), clear_override(), recompute()
  - get_effective_value() → value resolution
```

**Verification**:
- Test value resolution: override > formula > raw
- Test apply/clear override
- Test recompute updates cache

#### Step 6.3: Project Aggregate
**What**: Main project entity
**Why**: Aggregate root for project data

```
Files to create:
□ domain/project/entities/project.py
  - Project aggregate root
  - id, path, app_type_id, name, field_values dict
  - set_value(), get_value(), get_computed_value()
  - is_dirty(), mark_clean()
□ domain/project/repositories.py
  - IProjectRepository interface
□ domain/project/events.py
  - ProjectCreated, ProjectOpened, FieldValueChanged, ProjectSaved
```

**Verification**:
- Test set/get values
- Test dirty tracking
- Test domain events emitted
- **ORACLE TEST**: Load project data from old app, verify all values present

**Checkpoint 6**: ✓ Project domain complete, can model project data

---

### MILESTONE 7: Override Domain (Days 66-75)

#### Step 7.1: Override Value Objects
**What**: Override state and conflict detection
**Why**: Type-safe override handling

```
Files to create:
□ domain/override/value_objects/override_state.py
  - OverrideState enum with transition rules
  - PENDING, ACCEPTED, INVALID, SYNCED, SYNCED_FORMULA
  - can_transition_to(target_state) → bool
□ domain/override/value_objects/override_value.py
  - OverrideValue (system_value, report_values)
□ domain/override/value_objects/conflict.py
  - Conflict detection (multiple different report values)
```

**Verification**:
- Test all valid state transitions
- Test invalid transitions rejected
- Test conflict detection

#### Step 7.2: Override Aggregate
**What**: Override entity with state machine
**Why**: Manages override lifecycle

```
Files to create:
□ domain/override/entities/override.py
  - Override aggregate root
  - field_id, system_value, report_values, state
  - accept() → Result (transition to ACCEPTED)
  - reject() → Result (delete)
  - sync() → Result (transition to SYNCED)
  - get_effective_value()
□ domain/override/services/override_resolver.py
  - resolve_value(field_value, override) → Any
□ domain/override/repositories.py
  - IOverrideRepository interface
□ domain/override/events.py
  - OverrideCreated, OverrideAccepted, OverrideSynced
```

**Verification**:
- Test full state machine transitions
- Test override affects value resolution
- **ORACLE TEST**: Create overrides matching old app scenarios, verify behavior

**Checkpoint 7**: ✓ All core domain complete, business logic verified

---

### MILESTONE 8: Infrastructure Layer (Days 76-95)

#### Step 8.1: SQLite Connection
**What**: Database connection management
**Why**: Foundation for all persistence

```
Files to create:
□ infrastructure/persistence/sqlite/connection.py
  - SQLiteConnection class
  - Thread-local connections
  - PRAGMA configuration (foreign_keys, WAL)
  - Context manager support
```

**Verification**:
- Test connection in same thread reused
- Test different threads get different connections
- Test PRAGMA settings applied

#### Step 8.2: Entity Mappers
**What**: Domain ↔ Database row conversion
**Why**: Clean separation of domain and persistence

```
Files to create:
□ infrastructure/persistence/mappers/field_mapper.py
□ infrastructure/persistence/mappers/entity_mapper.py
□ infrastructure/persistence/mappers/project_mapper.py
□ infrastructure/persistence/mappers/validation_mapper.py
□ infrastructure/persistence/mappers/formula_mapper.py
□ infrastructure/persistence/mappers/override_mapper.py
```

**Verification**:
- Test round-trip: domain → row → domain (equality)
- Test handles None values correctly

#### Step 8.3: Repository Implementations
**What**: SQLite implementations of repository interfaces
**Why**: Actual data persistence

```
Files to create:
□ infrastructure/persistence/sqlite/repositories/schema_repository.py
□ infrastructure/persistence/sqlite/repositories/project_repository.py
□ infrastructure/persistence/sqlite/repositories/validation_repository.py
□ infrastructure/persistence/sqlite/repositories/formula_repository.py
□ infrastructure/persistence/sqlite/repositories/control_repository.py
□ infrastructure/persistence/sqlite/repositories/override_repository.py
```

**Verification**:
- Integration tests with in-memory SQLite
- Test CRUD operations
- **ORACLE TEST**: Load from old app databases, save to new, compare

#### Step 8.4: Unit of Work
**What**: Transaction management
**Why**: Atomic operations

```
Files to create:
□ infrastructure/persistence/sqlite/unit_of_work.py
  - SQLiteUnitOfWork
  - commit(), rollback()
  - repository(type) accessor
```

**Verification**:
- Test commit persists changes
- Test rollback discards changes
- Test multiple repositories in same transaction

#### Step 8.5: File System Infrastructure
**What**: Project storage, attachments
**Why**: File operations

```
Files to create:
□ infrastructure/filesystem/project_storage.py
  - Create project directory structure
  - Copy files to project
□ infrastructure/filesystem/attachment_storage.py
  - Store/retrieve attachments
  - Orphan cleanup
□ infrastructure/filesystem/config_loader.py
  - Load JSON configurations
□ infrastructure/filesystem/recent_projects.py
  - Manage recent projects list
```

**Verification**:
- Test project directory creation
- Test file copy/delete
- Test recent projects persistence

**Checkpoint 8**: ✓ Infrastructure complete, can persist all data

---

### MILESTONE 9: Document Generation (Days 96-115)

#### Step 9.1: Transformer Domain
**What**: Value transformers for output
**Why**: Convert raw values to display format

```
Files to create:
□ domain/transformer/entities/transformer.py
  - Transformer interface
  - to_output(value) → str
  - from_output(text) → Any
□ domain/transformer/implementations/
  - suffix.py (SuffixTransformer)
  - prefix.py (PrefixTransformer)
  - map.py (MapTransformer)
  - date_format.py (DateFormatTransformer)
  - arabic_number.py (ArabicNumberTransformer)
  - arabic_ordinal.py (ArabicOrdinalTransformer)
  - ... (one file per transformer)
□ domain/transformer/services/transformer_registry.py
  - Register/lookup transformers
```

**Verification**:
- Test each transformer bidirectionally
- **ORACLE TEST**: Compare transformer outputs with old app

#### Step 9.2: Document Domain
**What**: Template and output mapping model
**Why**: Document generation structure

```
Files to create:
□ domain/document/entities/template.py
  - Template aggregate (name, path, is_default)
□ domain/document/entities/output_mapping.py
  - OutputMapping (field_id → target_tag)
□ domain/document/services/value_resolver.py
  - Resolve field value with override/formula/transformer
□ domain/document/repositories.py
  - ITemplateRepository interface
```

#### Step 9.3: Document Adapters
**What**: External library adapters
**Why**: Isolate document generation dependencies

```
Files to create:
□ infrastructure/documents/word/interfaces.py
  - IWordService interface
□ infrastructure/documents/word/docx_adapter.py
  - python-docx implementation
□ infrastructure/documents/excel/interfaces.py
  - IExcelService interface
□ infrastructure/documents/excel/xlwings_adapter.py
  - xlwings implementation
□ infrastructure/documents/pdf/interfaces.py
  - IPdfService interface
□ infrastructure/documents/pdf/pymupdf_adapter.py
  - PyMuPDF implementation
```

**Verification**:
- Test Word document generation with sample template
- Test Excel cell reading/writing
- Test PDF stamp/signature addition
- **ORACLE TEST**: Generate document with same data as old app, compare outputs

**Checkpoint 9**: ✓ Document generation complete, outputs match old app

---

### MILESTONE 10: Application Layer (Days 116-135)

#### Step 10.1: Event Bus
**What**: In-memory event bus
**Why**: Cross-context communication

```
Files to create:
□ application/common/event_bus.py
  - IEventBus interface
□ infrastructure/events/in_memory_bus.py
  - InMemoryEventBus implementation
```

#### Step 10.2: Commands (Write Operations)
**What**: CQRS command handlers
**Why**: Encapsulate write operations

```
Files to create:
□ application/commands/project/create_project.py
□ application/commands/project/open_project.py
□ application/commands/project/save_project.py
□ application/commands/project/close_project.py
□ application/commands/project/update_field_value.py
□ application/commands/override/accept_override.py
□ application/commands/override/reject_override.py
□ application/commands/document/generate_report.py
□ application/commands/document/export_pdf.py
```

**Verification**:
- Test each command with mock repositories
- Test commands emit correct events

#### Step 10.3: Queries (Read Operations)
**What**: CQRS query handlers
**Why**: Encapsulate read operations

```
Files to create:
□ application/queries/project/get_project.py
□ application/queries/project/get_field_value.py
□ application/queries/project/get_recent_projects.py
□ application/queries/schema/get_schema.py
□ application/queries/validation/validate_field.py
□ application/queries/formula/compute_formula.py
```

#### Step 10.4: Event Handlers
**What**: React to domain events
**Why**: Orchestrate cross-cutting concerns

```
Files to create:
□ application/events/handlers/on_field_changed.py
  - Recompute formulas
  - Evaluate controls
  - Re-validate
□ application/events/handlers/on_project_saved.py
  - Cleanup orphaned files
  - Update recent projects
□ application/events/handlers/on_override_accepted.py
  - Update field value
  - Trigger formula recompute
```

**Verification**:
- Integration tests for full workflows
- **ORACLE TEST**: Run same workflow as old app, compare final state

#### Step 10.5: Application Services
**What**: High-level orchestration
**Why**: Simplify presentation layer

```
Files to create:
□ application/services/project_service.py
□ application/services/validation_service.py
□ application/services/formula_service.py
□ application/services/document_service.py
```

**Checkpoint 10**: ✓ Application layer complete, business flows work

---

### MILESTONE 11: Presentation Layer (Days 136-175)

#### Step 11.1: ViewModels
**What**: UI state management
**Why**: Testable UI logic

```
Files to create:
□ presentation/viewmodels/field_vm.py
□ presentation/viewmodels/project_vm.py
□ presentation/viewmodels/validation_vm.py
□ presentation/viewmodels/override_vm.py
□ presentation/viewmodels/main_window_vm.py
```

**Verification**:
- Unit test ViewModels WITHOUT PyQt6
- Test state changes trigger callbacks

#### Step 11.2: Qt Event Adapter
**What**: Bridge domain events to Qt signals
**Why**: Only PyQt6 touchpoint for domain

```
Files to create:
□ presentation/adapters/qt_event_adapter.py
  - Subscribe to domain events
  - Emit Qt signals
□ presentation/adapters/history_adapter.py
  - Wrap QUndoStack for undo/redo
```

#### Step 11.3: Field Widgets
**What**: Input widgets for each field type
**Why**: Core UI components

```
Files to create:
□ presentation/widgets/fields/base_field.py
□ presentation/widgets/fields/text_field.py
□ presentation/widgets/fields/number_field.py
□ presentation/widgets/fields/date_field.py
□ presentation/widgets/fields/option_field.py
□ presentation/widgets/fields/formula_field.py
□ presentation/widgets/fields/file_field.py
```

#### Step 11.4: Widget Factory
**What**: Create widgets from field type
**Why**: Open/Closed for field types

```
Files to create:
□ presentation/factories/field_widget_factory.py
  - Registry pattern
  - register(field_type, widget_class)
  - create(field_vm) → widget
```

#### Step 11.5: Dialogs
**What**: Modal dialogs
**Why**: User interactions

```
Files to create:
□ presentation/dialogs/settings_dialog.py
□ presentation/dialogs/override_dialog.py
□ presentation/dialogs/template_dialog.py
□ presentation/dialogs/conflict_dialog.py
□ presentation/dialogs/app_type_dialog.py
□ presentation/dialogs/figure_numbering_dialog.py
□ presentation/dialogs/schema_editor/
```

#### Step 11.6: Main Window
**What**: Application shell
**Why**: Entry point for UI

```
Files to create:
□ presentation/views/main_window.py (THIN - delegates to VM)
□ presentation/views/welcome_view.py
□ presentation/views/project_view.py
□ presentation/views/tabs/dynamic_tab.py
```

#### Step 11.7: Dependency Injection Setup
**What**: Wire everything together
**Why**: Composition root

```
Files to create:
□ infrastructure/di/container.py
□ main.py (entry point)
```

**Verification**:
- Manual testing of UI
- E2E tests for critical paths
- **ORACLE TEST**: Side-by-side comparison with old app

**Checkpoint 11**: ✓ Full application functional

---

### MILESTONE 12: Migration & Polish (Days 176-200)

#### Step 12.1: Data Migration Script
**What**: Convert old projects to new format
**Why**: Preserve user data

```
Tasks:
□ Map old DB schema to new schema
□ Create migration script
□ Handle edge cases (missing data, corrupted files)
□ Verification: migrate, load in new app, compare with old
```

#### Step 12.2: Feature Parity Testing
**What**: Verify all features work
**Why**: Ensure nothing lost

```
Tasks:
□ Create checklist from Phase 1 audit
□ Test each feature systematically
□ Document any intentional differences
```

#### Step 12.3: Performance Testing
**What**: Verify acceptable performance
**Why**: User experience

```
Tasks:
□ Load large projects
□ Measure formula computation time
□ Measure document generation time
□ Optimize if needed
```

#### Step 12.4: Documentation
**What**: User and developer docs
**Why**: Maintainability

```
Tasks:
□ README with setup instructions
□ Architecture documentation
□ API documentation
□ User guide (if needed)
```

**Checkpoint 12**: ✓ Production ready

---

## 24. VERIFICATION STRATEGY

### 24.1 Test Types by Phase

| Phase | Unit Tests | Integration Tests | Oracle Tests |
|-------|------------|-------------------|--------------|
| Domain | ✓✓✓ | - | ✓ (compare with old app) |
| Infrastructure | ✓ | ✓✓✓ | ✓ (load old data) |
| Application | ✓✓ | ✓✓ | ✓ (same workflows) |
| Presentation | ✓ (VMs) | ✓ | ✓ (side-by-side) |

### 24.2 Oracle Testing Pattern

```python
# Pattern for verifying behavior matches old app

class OracleTest:
    """Compare new implementation against old app behavior."""

    def __init__(self, old_db_path: Path):
        self.old_db = sqlite3.connect(old_db_path)

    def get_old_validation_result(self, field_id: str, value: Any) -> bool:
        """Get expected result from old app logic."""
        # Query old app's validation rules
        # Apply old app's validation logic
        pass

    def test_validation_matches(self, field_id: str, value: Any):
        old_result = self.get_old_validation_result(field_id, value)
        new_result = new_validator.validate(field_id, value)
        assert new_result.is_valid == old_result
```

### 24.3 Checkpoint Criteria

Each checkpoint requires:
1. All unit tests pass
2. All integration tests pass
3. Oracle tests confirm behavior matches old app
4. Code review completed
5. Documentation updated

---

## 25. RISK MITIGATION

### 25.1 Technical Risks

| Risk | Mitigation |
|------|------------|
| Formula evaluation differs | Extensive oracle testing with real formulas |
| Control chains behave differently | Side-by-side comparison with old app |
| Document generation differs | Binary comparison of generated files |
| Performance regression | Benchmark critical paths early |
| Data migration loses data | Checksums, verification scripts |

### 25.2 Process Risks

| Risk | Mitigation |
|------|------------|
| Scope creep | Strict feature parity only, no enhancements |
| Integration issues late | Vertical slices, continuous integration |
| Unclear requirements | Old app as oracle, Phase 1 audit as spec |

### 25.3 Rollback Plan

- Keep old app fully functional throughout
- Each milestone produces deployable (partial) software
- Data migration is reversible (keep old databases)
- Feature flags allow gradual rollout

---

## 26. IMPLEMENTATION ORDER RATIONALE

### Why This Order?

1. **Foundation first**: All other code depends on base classes
2. **Validation before schema**: Validation is simpler, builds confidence
3. **Schema before formula**: Formulas reference fields
4. **Formula before control**: Controls may trigger formula recomputes
5. **Project last in domain**: Depends on all other contexts
6. **Infrastructure after domain**: Implements domain interfaces
7. **Documents after infrastructure**: Needs persistence + adapters
8. **Application after infrastructure**: Orchestrates domain + infra
9. **Presentation last**: Consumes everything else

### Why Vertical Slices?

- Each milestone delivers testable value
- Bugs found early, not at integration time
- Oracle testing possible at each step
- Motivation from working software

---

## PHASE 4 COMPLETE

**Deliverables:**
1. 12 milestones with clear checkpoints
2. ~200 days of detailed implementation steps
3. File-by-file creation order
4. Verification strategy for each step
5. Oracle testing pattern for correctness
6. Risk mitigation plan
7. Rationale for implementation order

**Ready to begin implementation.**

---

# Architecture Decision Records (ADRs)

## ADR-001: Controlled Big Bang Rewrite Strategy

**Status**: Accepted

**Context**: The existing codebase has extreme coupling (core layer imports PyQt6), god objects (MainWindow 2024 LOC), two competing global state systems, and zero test coverage. Incremental refactoring would require maintaining backward compatibility with untested code while extracting components from tightly coupled classes.

**Decision**: Perform a controlled big bang rewrite, building the new application alongside the old one rather than modifying existing code. Use the old app as a behavioral oracle for testing.

**Consequences**:
- (+) Clean slate with proper architecture from day one
- (+) No backward compatibility constraints
- (+) Old app remains functional as reference
- (+) Feature parity verifiable through oracle testing
- (-) Temporary code duplication during transition
- (-) Cannot leverage existing code directly

---

## ADR-002: Clean Architecture with Domain-Driven Design

**Status**: Accepted

**Context**: The old system mixed business logic across UI, services, and persistence layers. Changes to one feature required modifications in 5+ files. No clear domain model existed—just data classes with services containing SQL.

**Decision**: Adopt Clean Architecture (Presentation → Application → Domain ← Infrastructure) combined with DDD tactical patterns (Aggregates, Value Objects, Domain Events, Repositories).

**Consequences**:
- (+) Clear separation of concerns
- (+) Domain logic testable in isolation
- (+) Infrastructure swappable without domain changes
- (+) Bounded contexts prevent feature entanglement
- (-) More files and indirection
- (-) Learning curve for DDD patterns

---

## ADR-003: Framework-Independent Domain Layer

**Status**: Accepted

**Context**: The old core layer imported PyQt6 throughout (QObject, pyqtSignal, QTimer, QUndoCommand). This made the domain untestable without Qt and impossible to reuse in non-Qt contexts.

**Decision**: Domain layer has ZERO external dependencies. No PyQt6, no SQLite, no file system. Only Python standard library. PyQt6 usage confined strictly to presentation layer.

**Consequences**:
- (+) 100% unit testable without mocking frameworks
- (+) Domain can be reused in CLI, web, or mobile contexts
- (+) Framework upgrades don't affect business logic
- (-) Cannot use convenient Qt patterns (signals) in domain
- (-) Requires event bus abstraction for communication

---

## ADR-004: CQRS for Read/Write Separation

**Status**: Accepted

**Context**: The old system used the same code paths for reading and writing data, leading to complex methods that handled both concerns. Read operations often loaded more data than needed.

**Decision**: Separate Commands (write operations) from Queries (read operations). Commands modify state and return Result types. Queries return DTOs optimized for the caller's needs.

**Consequences**:
- (+) Read models optimized for display
- (+) Write operations focused on validation and business rules
- (+) Easier to reason about state changes
- (+) Clear audit trail of mutations
- (-) More classes (Command + Handler for each operation)
- (-) Potential for read/write model drift

---

## ADR-005: MVVM Pattern for Presentation Layer

**Status**: Accepted

**Context**: The old MainWindow (2024 LOC) mixed UI rendering with business logic, state management, and persistence. UI logic couldn't be tested without rendering actual widgets.

**Decision**: Adopt Model-View-ViewModel (MVVM) pattern. ViewModels contain all UI state and logic, exposing observable properties. Views (PyQt6 widgets) bind to ViewModels but contain no logic.

**Consequences**:
- (+) UI logic testable without Qt
- (+) Views become thin and declarative
- (+) Clear data binding contract
- (+) ViewModels reusable across different views
- (-) Boilerplate for property change notification
- (-) Requires discipline to keep views logic-free

---

## ADR-006: In-Memory Event Bus Over PyQt Signals

**Status**: Accepted

**Context**: The old system used PyQt signals (pyqtSignal) throughout, including in the core layer. This coupled the domain to PyQt6 and made cross-context communication implicit.

**Decision**: Use a framework-independent in-memory event bus for domain/application events. Create a Qt adapter in the presentation layer that bridges domain events to Qt signals.

**Consequences**:
- (+) Domain events work without PyQt6
- (+) Explicit event subscription/publishing
- (+) Easy to add event logging/debugging
- (+) Can swap to async or distributed bus later
- (-) Less convenient than pyqtSignal
- (-) Extra adapter layer for Qt integration

---

## ADR-007: Repository Pattern with Raw SQL Mappers

**Status**: Accepted

**Context**: The old system had direct SQL queries scattered throughout services with hardcoded table/column names. No abstraction existed between domain entities and database operations.

**Decision**: Define repository interfaces in domain layer. Implement with SQLite in infrastructure using explicit row-to-entity mappers. No ORM—just raw SQL with typed mappers.

**Consequences**:
- (+) Domain decoupled from persistence mechanism
- (+) Easy to test with in-memory fakes
- (+) Full control over SQL performance
- (+) No ORM magic or N+1 surprises
- (-) More manual mapping code
- (-) Schema changes require mapper updates

---

## ADR-008: Result Monad for Error Handling

**Status**: Accepted

**Context**: The old system used exceptions for both unexpected errors and business rule violations. Error handling was inconsistent, and callers often forgot to handle specific exceptions.

**Decision**: Use Result[T, E] monad for operations that can fail expectedly. Return Result.success(value) or Result.failure(error). Reserve exceptions for truly unexpected conditions (bugs, infrastructure failures).

**Consequences**:
- (+) Explicit error handling at call sites
- (+) Cannot forget to handle failures (type system helps)
- (+) Composable with map/flatMap operations
- (+) Clear distinction: Result = expected failure, Exception = bug
- (-) More verbose than try/catch
- (-) Learning curve for functional patterns

---

## ADR-009: Strongly Typed Identifiers

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

---

## ADR-010: Immutable Value Objects

**Status**: Accepted

**Context**: The old system used mutable dictionaries and data classes throughout. Shared mutable state led to subtle bugs when objects were modified unexpectedly.

**Decision**: Use frozen dataclasses for all value objects. Value objects are immutable, compared by value, and have no identity. Updates return new instances.

**Consequences**:
- (+) Thread-safe by design
- (+) No defensive copying needed
- (+) Simpler reasoning about state
- (+) Natural fit for caching/memoization
- (-) Memory overhead from creating new objects
- (-) Verbose update syntax (replace() or with_*() methods)

---

## ADR-011: Unit of Work for Transaction Management

**Status**: Accepted

**Context**: The old system committed database changes immediately within service methods. There was no way to group multiple repository operations into a single atomic transaction.

**Decision**: Implement Unit of Work pattern. Repositories obtained from UoW share a connection. Changes are tracked and committed atomically when UoW.commit() is called.

**Consequences**:
- (+) Atomic multi-repository operations
- (+) Automatic rollback on exceptions
- (+) Single commit point for consistency
- (+) Clear transaction boundaries
- (-) Must pass UoW to all repository operations
- (-) Longer-lived connections during transactions

---

## ADR-012: Registry-Based Factory for Extensibility

**Status**: Accepted

**Context**: The old FieldFactory had hard-coded type→widget mappings. Adding a new field type required modifying the factory class, violating Open/Closed Principle.

**Decision**: Use registry-based factories where new types can be registered without modifying factory code. Factory.register(field_type, widget_class) adds new types. Factory.create(field_type) looks up and instantiates.

**Consequences**:
- (+) Open for extension, closed for modification
- (+) Third-party extensions possible
- (+) Runtime registration for plugin systems
- (+) Easy to add new field/transformer/validator types
- (-) Runtime errors if type not registered
- (-) Less discoverable than hard-coded mappings

---

## ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| 001 | Controlled Big Bang Rewrite Strategy | Accepted |
| 002 | Clean Architecture with Domain-Driven Design | Accepted |
| 003 | Framework-Independent Domain Layer | Accepted |
| 004 | CQRS for Read/Write Separation | Accepted |
| 005 | MVVM Pattern for Presentation Layer | Accepted |
| 006 | In-Memory Event Bus Over PyQt Signals | Accepted |
| 007 | Repository Pattern with Raw SQL Mappers | Accepted |
| 008 | Result Monad for Error Handling | Accepted |
| 009 | Strongly Typed Identifiers | Accepted |
| 010 | Immutable Value Objects | Accepted |
| 011 | Unit of Work for Transaction Management | Accepted |
| 012 | Registry-Based Factory for Extensibility | Accepted |

---

# Target Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    USER INTERFACE                                    │
│                                      (PyQt6)                                         │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                              Views (PyQt6 Widgets)                              ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               ││
│  │  │ MainWindow  │ │  Dialogs    │ │ Field       │ │ File        │               ││
│  │  │   View      │ │  (50+)      │ │ Widgets     │ │ Gallery     │               ││
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘               ││
│  └─────────┼───────────────┼───────────────┼───────────────┼───────────────────────┘│
│            │               │               │               │                         │
│            └───────────────┴───────────────┴───────────────┘                         │
│                                    │ binds to                                        │
│                                    ▼                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                              ViewModels (MVVM)                                  ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               ││
│  │  │ ProjectVM   │ │ FieldVM     │ │OverrideVM   │ │ SchemaVM    │               ││
│  │  │ • is_dirty  │ │ • value     │ │ • state     │ │ • entities  │               ││
│  │  │ • tabs      │ │ • is_valid  │ │ • conflicts │ │ • fields    │               ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                    │                                                 │
│  ┌─────────────────────────────────┼───────────────────────────────────────────────┐│
│  │  Adapters                       │                                               ││
│  │  ┌──────────────────┐  ┌───────┴────────┐  ┌─────────────────┐                 ││
│  │  │ QtEventAdapter   │  │ HistoryAdapter │  │ WidgetFactory   │                 ││
│  │  │ Domain→Qt Signal │  │ QUndoStack     │  │ Registry-based  │                 ││
│  │  └──────────────────┘  └────────────────┘  └─────────────────┘                 ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────┬───────────────────────────────────────────────┘
                                      │ calls
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION LAYER                                       │
│  ┌──────────────────────────────────┬──────────────────────────────────────────────┐│
│  │         Commands (Write)         │           Queries (Read)                     ││
│  │  ┌────────────────────────────┐  │  ┌────────────────────────────┐              ││
│  │  │ • CreateProject            │  │  │ • GetProject               │              ││
│  │  │ • UpdateFieldValue         │  │  │ • GetFieldValue            │              ││
│  │  │ • AcceptOverride           │  │  │ • ValidateField            │              ││
│  │  │ • GenerateReport           │  │  │ • ComputeFormula           │              ││
│  │  │ • ExportPdf                │  │  │ • GetRecentProjects        │              ││
│  │  └────────────────────────────┘  │  └────────────────────────────┘              ││
│  └──────────────────────────────────┴──────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                          Application Services                                   ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               ││
│  │  │ Project     │ │ Validation  │ │ Formula     │ │ Document    │               ││
│  │  │ Service     │ │ Service     │ │ Service     │ │ Service     │               ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                           Event Handlers                                        ││
│  │  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐       ││
│  │  │ OnFieldValueChanged │ │ OnProjectSaved      │ │ OnOverrideAccepted  │       ││
│  │  │ → Recompute formulas│ │ → Cleanup files     │ │ → Update field      │       ││
│  │  │ → Evaluate controls │ │ → Update recents    │ │ → Trigger formulas  │       ││
│  │  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────┬───────────────────────────────────────────────┘
                                      │ uses interfaces
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                DOMAIN LAYER                                          │
│                        (Pure Python - NO external dependencies)                      │
│                                                                                      │
│  ┌────────────────────────────────── BOUNDED CONTEXTS ─────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  ││
│  │  │     SCHEMA      │  │    PROJECT      │  │   VALIDATION    │                  ││
│  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │                  ││
│  │  │  │ AppType   │  │  │  │ Project   │  │  │  │Validation │  │                  ││
│  │  │  │ (root)    │  │  │  │ (root)    │  │  │  │Rule (root)│  │                  ││
│  │  │  ├───────────┤  │  │  ├───────────┤  │  │  ├───────────┤  │                  ││
│  │  │  │ Entity    │  │  │  │ FieldValue│  │  │  │Constraint │  │                  ││
│  │  │  │ Definition│  │  │  │           │  │  │  │(sum type) │  │                  ││
│  │  │  ├───────────┤  │  │  └───────────┘  │  │  ├───────────┤  │                  ││
│  │  │  │ Field     │  │  │                 │  │  │Validation │  │                  ││
│  │  │  │ Definition│  │  │                 │  │  │Result     │  │                  ││
│  │  │  └───────────┘  │  │                 │  │  └───────────┘  │                  ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  ││
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  ││
│  │  │     FORMULA     │  │    CONTROL      │  │    OVERRIDE     │                  ││
│  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │                  ││
│  │  │  │ Formula   │  │  │  │ControlRule│  │  │  │ Override  │  │                  ││
│  │  │  │ (root)    │  │  │  │ (root)    │  │  │  │ (root)    │  │                  ││
│  │  │  ├───────────┤  │  │  ├───────────┤  │  │  ├───────────┤  │                  ││
│  │  │  │Expression │  │  │  │ Control   │  │  │  │ Override  │  │                  ││
│  │  │  ├───────────┤  │  │  │ Mapping   │  │  │  │ State     │  │                  ││
│  │  │  │Dependency │  │  │  ├───────────┤  │  │  │ (machine) │  │                  ││
│  │  │  │Graph      │  │  │  │ Effect    │  │  │  ├───────────┤  │                  ││
│  │  │  ├───────────┤  │  │  │ Result    │  │  │  │ Conflict  │  │                  ││
│  │  │  │Evaluation │  │  │  └───────────┘  │  │  └───────────┘  │                  ││
│  │  │  │Context    │  │  │                 │  │                 │                  ││
│  │  │  └───────────┘  │  │                 │  │                 │                  ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  ││
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  ││
│  │  │    DOCUMENT     │  │   TRANSFORMER   │  │      FILE       │                  ││
│  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │                  ││
│  │  │  │ Template  │  │  │  │Transformer│  │  │  │Attachment │  │                  ││
│  │  │  │ (root)    │  │  │  │(interface)│  │  │  │ (root)    │  │                  ││
│  │  │  ├───────────┤  │  │  ├───────────┤  │  │  ├───────────┤  │                  ││
│  │  │  │ Output    │  │  │  │• Suffix   │  │  │  │ File      │  │                  ││
│  │  │  │ Mapping   │  │  │  │• Prefix   │  │  │  │ Metadata  │  │                  ││
│  │  │  ├───────────┤  │  │  │• Map      │  │  │  ├───────────┤  │                  ││
│  │  │  │ Content   │  │  │  │• Date     │  │  │  │ Figure    │  │                  ││
│  │  │  │ Tag       │  │  │  │• Arabic   │  │  │  │ Number    │  │                  ││
│  │  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │                  ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  ││
│  │                                                                                  ││
│  └──────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌──────────────────────────────── SHARED KERNEL ──────────────────────────────────┐│
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               ││
│  │  │   Entity    │ │ValueObject  │ │ DomainEvent │ │Result[T,E]  │               ││
│  │  │ (base)      │ │ (frozen)    │ │ (base)      │ │ (monad)     │               ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                               ││
│  │  │Aggregate    │ │Specification│ │ Repository  │  ← interfaces only            ││
│  │  │Root (base)  │ │ (pattern)   │ │ (interface) │                               ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘                               ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌──────────────────────────────── DOMAIN SERVICES ────────────────────────────────┐│
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                   ││
│  │  │ FormulaEvaluator│ │ControlEvaluator │ │OverrideResolver │                   ││
│  │  │ (pure functions)│ │ (chain logic)   │ │ (state machine) │                   ││
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘                   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      ▲
                                      │ implements interfaces
                                      │
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            INFRASTRUCTURE LAYER                                      │
│                                                                                      │
│  ┌────────────────────────────── PERSISTENCE ──────────────────────────────────────┐│
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   ││
│  │  │                         SQLite Repositories                              │   ││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │   ││
│  │  │  │ Project     │ │ Schema      │ │ Validation  │ │ Formula     │        │   ││
│  │  │  │ Repository  │ │ Repository  │ │ Repository  │ │ Repository  │        │   ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │   ││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                        │   ││
│  │  │  │ Override    │ │ Control     │ │ Template    │                        │   ││
│  │  │  │ Repository  │ │ Repository  │ │ Repository  │                        │   ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘                        │   ││
│  │  └─────────────────────────────────────────────────────────────────────────┘   ││
│  │                                                                                 ││
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐          ││
│  │  │ SQLiteConnection  │  │ SQLiteUnitOfWork  │  │ Entity Mappers    │          ││
│  │  │ (thread-local)    │  │ (transactions)    │  │ (row ↔ domain)    │          ││
│  │  └───────────────────┘  └───────────────────┘  └───────────────────┘          ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌────────────────────────────── FILE SYSTEM ──────────────────────────────────────┐│
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 ││
│  │  │ ProjectStorage  │  │AttachmentStorage│  │ ConfigLoader    │                 ││
│  │  │ (directories)   │  │ (copy/delete)   │  │ (JSON files)    │                 ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                 ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌────────────────────────────── DOCUMENT ADAPTERS ────────────────────────────────┐│
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 ││
│  │  │ XlwingsAdapter  │  │ DocxAdapter     │  │ PyMuPdfAdapter  │                 ││
│  │  │ (Excel)         │  │ (Word)          │  │ (PDF)           │                 ││
│  │  │ IExcelService   │  │ IWordService    │  │ IPdfService     │                 ││
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                 ││
│  └───────────┼────────────────────┼────────────────────┼───────────────────────────┘│
│              │                    │                    │                             │
│  ┌───────────┼────────────────────┼────────────────────┼───────────────────────────┐│
│  │           ▼                    ▼                    ▼          EXTERNAL LIBS    ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 ││
│  │  │    xlwings      │  │   python-docx   │  │    PyMuPDF      │                 ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                 ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌────────────────────────────── EVENT INFRASTRUCTURE ─────────────────────────────┐│
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   ││
│  │  │                      InMemoryEventBus                                    │   ││
│  │  │  • subscribe(event_type, handler)    • No PyQt6 dependency              │   ││
│  │  │  • publish(event)                    • Synchronous execution            │   ││
│  │  └─────────────────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌────────────────────────────── DEPENDENCY INJECTION ─────────────────────────────┐│
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   ││
│  │  │  DI Container  •  Interface → Implementation mappings                    │   ││
│  │  │                •  Singleton/transient lifetimes  •  Composition root     │   ││
│  │  └─────────────────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SYSTEMS                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                      │
│  │   SQLite DBs    │  │   File System   │  │  Office Apps    │                      │
│  │  • config.db    │  │  • Projects/    │  │  • Excel        │                      │
│  │  • project.db   │  │  • Templates/   │  │  • Word         │                      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Dependency Flow

```
                    ┌─────────────────────────────────────────┐
                    │         DEPENDENCY RULE                 │
                    │                                         │
                    │    Dependencies point INWARD only       │
                    │                                         │
                    │  Outer layers depend on inner layers    │
                    │  Inner layers know nothing of outer     │
                    └─────────────────────────────────────────┘

     OUTER                                                        INNER
       │                                                            │
       ▼                                                            ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Presentation │────▶│ Application  │────▶│    Domain    │◀────│Infrastructure│
│              │     │              │     │              │     │              │
│  • Views     │     │  • Commands  │     │  • Entities  │     │  • SQLite    │
│  • ViewModels│     │  • Queries   │     │  • Values    │     │  • Adapters  │
│  • Widgets   │     │  • Services  │     │  • Services  │     │  • File I/O  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    ▲                    │
       │                    │                    │                    │
       │                    └────────────────────┼────────────────────┘
       │                         uses            │      implements
       │                      interfaces         │      interfaces
       └─────────────────────────────────────────┘
                    calls application layer
```

## Data Flow: Update Field Value

```
┌─────────┐  1. User types    ┌─────────────┐  2. Calls        ┌─────────────────────┐
│  View   │ ────────────────▶ │ FieldVM     │ ───────────────▶ │ UpdateFieldValue    │
│ (Input) │                   │ set_value() │                  │ Command             │
└─────────┘                   └─────────────┘                  └──────────┬──────────┘
                                                                          │
     ┌────────────────────────────────────────────────────────────────────┘
     │  3. Handler executes
     ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  UpdateFieldValueHandler.execute(command):                                          │
│    1. project = project_repo.get_by_id(project_id)     ─── Load aggregate           │
│    2. result = project.set_value(field_id, value)      ─── Domain logic             │
│    3. validation = validator.validate(field, value)    ─── Validate                 │
│    4. affected = formula_service.recompute(field_id)   ─── Cascade formulas         │
│    5. effects = control_service.evaluate(field_id)     ─── Cascade controls         │
│    6. uow.commit()                                     ─── Persist                  │
│    7. event_bus.publish(FieldValueChanged)             ─── Notify                   │
│    8. return Result.success(dto)                       ─── Return                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
     │
     │  8. Result returned
     ▼
┌─────────────────┐  9. Event bridged   ┌─────────────────┐  10. Updates  ┌──────────┐
│ QtEventAdapter  │ ─────────────────▶  │ FieldVM         │ ────────────▶ │   View   │
│ (Qt signal)     │                     │ (notifies)      │               │ (refresh)│
└─────────────────┘                     └─────────────────┘               └──────────┘
```

## Database Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  config.db (Global)                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │
│  │ app_types   │ │ languages   │ │ templates   │ │ recent_     │                   │
│  │             │ │             │ │ catalog     │ │ projects    │                   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                   │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │ references
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  app_types/{name}/config.db (Per App Type)                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │
│  │ entities    │ │ fields      │ │ validation_ │ │ formulas    │                   │
│  │             │ │             │ │ rules       │ │             │                   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │
│  │ control_    │ │ output_     │ │ transformers│ │ dropdowns   │                   │
│  │ relations   │ │ mappings    │ │             │ │             │                   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                   │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │ defines schema for
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  Projects/{name}/project.db (Per Project)                                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │
│  │ metadata    │ │ {entity}_   │ │ overrides   │ │ sequences   │                   │
│  │             │ │ data        │ │             │ │             │                   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                   │
│                  (dynamic tables per schema)                                        │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

# Anti-Pattern Checklist

This checklist documents specific anti-patterns observed in the old codebase. Use it during code review and development to prevent regression into bad habits.

## 1. ARCHITECTURE ANTI-PATTERNS

### 1.1 Layer Violations

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

### 1.2 God Objects

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

### 1.3 Dependency Issues

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

## 2. STATE MANAGEMENT ANTI-PATTERNS

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

## 3. ERROR HANDLING ANTI-PATTERNS

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

## 4. TESTING ANTI-PATTERNS

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

## 5. DOMAIN MODELING ANTI-PATTERNS

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

## 6. UI LAYER ANTI-PATTERNS

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

## 7. PERSISTENCE ANTI-PATTERNS

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

## 8. QUICK REFERENCE

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

## 9. VOCABULARY STANDARDS

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

## 10. CODE REVIEW GATE

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

# Phase 5: Generalization to "Doc Helper"

## 27. PROJECT RENAME AND GENERALIZATION

### 27.1 New Project Identity

| Aspect | Value |
|--------|-------|
| **Name** | Doc Helper |
| **Purpose** | Universal document/report generation platform |
| **Tagline** | "One platform, unlimited document types" |
| **Folder** | `doc_helper/` (replaces `soil_report_v2/`) |

### 27.2 Terminology Mapping

| Old Term | New Term | Notes |
|----------|----------|-------|
| Soil Investigation Report | App Type | Generic container for any document type |
| soil_report | doc_helper | Package name |
| Report | Document | Generated output |
| Borehole, Sample, etc. | Collection Entity | Defined per app type |

---

## 28. MULTI-DOCUMENT-TYPE ARCHITECTURE

### 28.1 Core Principle: Shared Core + Pluggable App Types

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              DOC HELPER PLATFORM                                     │
│                                                                                      │
│  ┌────────────────────────────── SHARED CORE ──────────────────────────────────┐   │
│  │  • Validation Engine      • Formula Engine       • Control Engine            │   │
│  │  • Override Management    • File Management      • Document Generation       │   │
│  │  • Schema System          • Template Engine      • Transformer Registry      │   │
│  │  • UI Framework           • Persistence Layer    • Event System              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                              │
│                    Provides services to                                              │
│                                       ▼                                              │
│  ┌────────────────────────────── APP TYPES ────────────────────────────────────┐   │
│  │                                                                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │   │
│  │  │    Soil     │  │ Structural  │  │Environmental│  │   Custom    │        │   │
│  │  │Investigation│  │   Report    │  │ Assessment  │  │  App Type   │        │   │
│  │  │   Report    │  │             │  │             │  │             │        │   │
│  │  ├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤        │   │
│  │  │ • Schema    │  │ • Schema    │  │ • Schema    │  │ • Schema    │        │   │
│  │  │ • Templates │  │ • Templates │  │ • Templates │  │ • Templates │        │   │
│  │  │ • Transform.│  │ • Transform.│  │ • Transform.│  │ • Transform.│        │   │
│  │  │ • Mappings  │  │ • Mappings  │  │ • Mappings  │  │ • Mappings  │        │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 28.2 What's Shared vs. App-Type-Specific

| Layer | Shared (Platform) | App-Type-Specific |
|-------|-------------------|-------------------|
| **Domain** | All bounded contexts | Schema definitions loaded from app type DB |
| **Validation** | Validation engine, constraint types | Custom constraint implementations (optional) |
| **Formula** | Parser, evaluator, allowed functions | Custom functions (optional extension) |
| **Control** | Control engine, effect types | Control rules defined in schema |
| **Transformer** | Registry, base transformers (15+) | Custom transformers per app type |
| **Template** | Template engine | Word/Excel templates per app type |
| **UI** | Widget factory, base widgets | Custom widgets (rare, optional) |
| **Persistence** | Repository implementations | Per-app-type config.db |

### 28.3 App Type Package Structure

```
doc_helper/
├── src/doc_helper/
│   ├── domain/                    # SHARED - All bounded contexts
│   ├── application/               # SHARED - Commands, queries, services
│   ├── infrastructure/            # SHARED - Repositories, adapters
│   └── presentation/              # SHARED - UI framework
│
└── app_types/                     # APP-TYPE-SPECIFIC
    ├── soil_investigation/
    │   ├── config.db              # Schema, validation, formulas, controls
    │   ├── templates/
    │   │   ├── report_ar.docx     # Arabic Word template
    │   │   ├── report_en.docx     # English Word template
    │   │   └── data.xlsx          # Excel template
    │   ├── transformers/          # Custom transformers (optional)
    │   │   └── soil_specific.py
    │   └── manifest.json          # App type metadata
    │
    ├── structural_report/
    │   ├── config.db
    │   ├── templates/
    │   └── manifest.json
    │
    └── environmental_assessment/
        ├── config.db
        ├── templates/
        └── manifest.json
```

### 28.4 App Type Manifest

Each app type has a `manifest.json` describing its capabilities:

```json
{
  "id": "soil_investigation",
  "name": "Soil Investigation Report",
  "name_ar": "تقرير فحص التربة",
  "version": "1.0.0",
  "description": "Generate soil investigation reports for construction projects",
  "author": "Doc Helper Team",

  "icon": "icons/soil.png",
  "color": "#8B4513",

  "capabilities": {
    "excel_generation": true,
    "word_generation": true,
    "pdf_export": true,
    "multi_language": ["ar", "en"]
  },

  "extensions": {
    "custom_transformers": ["transformers/soil_specific.py"],
    "custom_widgets": [],
    "custom_validators": []
  },

  "templates": {
    "default": "templates/report_ar.docx",
    "available": [
      {"id": "report_ar", "name": "Arabic Report", "path": "templates/report_ar.docx"},
      {"id": "report_en", "name": "English Report", "path": "templates/report_en.docx"}
    ]
  },

  "output": {
    "word": {
      "naming_pattern": "{report_number}_{project_name}",
      "default_folder": "generated"
    },
    "excel": {
      "naming_pattern": "{report_number}_data",
      "default_folder": "generated"
    },
    "pdf": {
      "naming_pattern": "{report_number}_{project_name}_final",
      "default_folder": "generated"
    }
  }
}
```

---

## 29. DOCUMENT NAMING SYSTEM

### 29.1 Overview

Each app type defines its own naming patterns for generated documents in `manifest.json`. The system supports:
- Field value tokens: `{field_id}` - replaced with actual field values
- Built-in tokens: `{date}`, `{project_name}`, etc.
- Literal text: Any text outside `{}` is kept as-is

### 29.2 Available Tokens

| Token | Description | Example |
|-------|-------------|---------|
| `{field_id}` | Any field from the schema | `{report_number}` → `2024-001` |
| `{project_name}` | Project name | `Building A Site` |
| `{app_type}` | App type name | `Soil Investigation` |
| `{template_name}` | Selected template name | `Arabic Report` |
| `{date}` | Current date (YYYY-MM-DD) | `2024-01-19` |
| `{YYYY}` | Year | `2024` |
| `{MM}` | Month (zero-padded) | `01` |
| `{DD}` | Day (zero-padded) | `19` |
| `{timestamp}` | Unix timestamp | `1705689600` |
| `{#}` | Auto-increment number | `1`, `2`, `3`... |
| `{##}` | Zero-padded (2 digits) | `01`, `02`... |
| `{###}` | Zero-padded (3 digits) | `001`, `002`... |

### 29.3 Pattern Examples by App Type

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         NAMING PATTERN EXAMPLES                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  SOIL INVESTIGATION                                                                  │
│  ─────────────────                                                                   │
│  Pattern: "{report_number}_{project_name}"                                          │
│  Result:  "2024-001_Building A Site.docx"                                           │
│                                                                                      │
│  STRUCTURAL REPORT                                                                   │
│  ─────────────────                                                                   │
│  Pattern: "{project_code}_Structural_{date}"                                        │
│  Result:  "PRJ-123_Structural_2024-01-19.docx"                                      │
│                                                                                      │
│  ENVIRONMENTAL ASSESSMENT                                                            │
│  ────────────────────────                                                            │
│  Pattern: "EA_{client_name}_{site_location}_{YYYY}"                                 │
│  Result:  "EA_ABC Corp_Downtown_2024.docx"                                          │
│                                                                                      │
│  GENERIC (FALLBACK)                                                                  │
│  ─────────────────                                                                   │
│  Pattern: "{project_name}_{date}"                                                   │
│  Result:  "My Project_2024-01-19.docx"                                              │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 29.4 Domain: Naming Value Objects

```python
# domain/document/value_objects/naming_pattern.py

@dataclass(frozen=True)
class NamingPattern:
    """Pattern for generating document filenames."""
    pattern: str  # e.g., "{report_number}_{project_name}"

    def get_tokens(self) -> List[str]:
        """Extract all tokens from pattern."""
        import re
        return re.findall(r'\{([^}]+)\}', self.pattern)

    def get_field_tokens(self) -> List[str]:
        """Get tokens that reference field IDs (not built-in)."""
        built_in = {'date', 'YYYY', 'MM', 'DD', 'timestamp',
                    'project_name', 'app_type', 'template_name',
                    '#', '##', '###', '####'}
        return [t for t in self.get_tokens() if t not in built_in]


@dataclass(frozen=True)
class GeneratedFileName:
    """Resolved filename after applying pattern."""
    name: str           # Without extension
    extension: str      # .docx, .xlsx, .pdf
    full_name: str      # name + extension

    @staticmethod
    def sanitize(name: str) -> str:
        """Remove invalid filename characters."""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '_')
        return name.strip()
```

### 29.5 Domain: Naming Service

```python
# domain/document/services/document_naming_service.py

class DocumentNamingService:
    """Resolves naming patterns to actual filenames."""

    BUILT_IN_RESOLVERS = {
        'date': lambda ctx: ctx.now.strftime('%Y-%m-%d'),
        'YYYY': lambda ctx: ctx.now.strftime('%Y'),
        'MM': lambda ctx: ctx.now.strftime('%m'),
        'DD': lambda ctx: ctx.now.strftime('%d'),
        'timestamp': lambda ctx: str(int(ctx.now.timestamp())),
        'project_name': lambda ctx: ctx.project_name,
        'app_type': lambda ctx: ctx.app_type_name,
        'template_name': lambda ctx: ctx.template_name,
    }

    def resolve(
        self,
        pattern: NamingPattern,
        context: NamingContext,
        field_values: Dict[FieldId, Any]
    ) -> Result[GeneratedFileName, NamingError]:
        """Resolve pattern to filename."""

        result = pattern.pattern

        # Resolve field tokens
        for token in pattern.get_field_tokens():
            field_id = FieldId(token)
            if field_id in field_values:
                value = str(field_values[field_id] or '')
                result = result.replace(f'{{{token}}}', value)
            else:
                # Field not found - use empty string
                result = result.replace(f'{{{token}}}', '')

        # Resolve built-in tokens
        for token, resolver in self.BUILT_IN_RESOLVERS.items():
            result = result.replace(f'{{{token}}}', resolver(context))

        # Handle auto-increment tokens
        result = self._resolve_increment(result, context)

        # Sanitize and create filename
        sanitized = GeneratedFileName.sanitize(result)

        if not sanitized:
            return Result.failure(NamingError("Pattern resulted in empty filename"))

        return Result.success(GeneratedFileName(
            name=sanitized,
            extension=context.extension,
            full_name=f"{sanitized}{context.extension}"
        ))

    def _resolve_increment(self, pattern: str, context: NamingContext) -> str:
        """Resolve {#}, {##}, {###} tokens."""
        import re

        def replace_increment(match):
            hashes = match.group(1)
            width = len(hashes)
            return str(context.increment_value).zfill(width)

        return re.sub(r'\{(#+)\}', replace_increment, pattern)


@dataclass(frozen=True)
class NamingContext:
    """Context for resolving naming patterns."""
    project_name: str
    app_type_name: str
    template_name: str
    extension: str          # .docx, .xlsx, .pdf
    now: datetime
    increment_value: int    # For {#} tokens
```

### 29.6 Application: Generate Document Command

```python
# application/commands/document/generate_document.py

@dataclass(frozen=True)
class GenerateDocumentCommand:
    project_id: ProjectId
    template_id: TemplateId
    output_type: OutputType  # WORD, EXCEL, PDF
    custom_filename: Optional[str] = None  # Override pattern if provided


class GenerateDocumentHandler:
    def __init__(
        self,
        project_repo: IProjectRepository,
        template_repo: ITemplateRepository,
        naming_service: DocumentNamingService,
        document_generator: IDocumentGenerator
    ):
        self._project_repo = project_repo
        self._template_repo = template_repo
        self._naming_service = naming_service
        self._generator = document_generator

    def execute(self, cmd: GenerateDocumentCommand) -> Result[GeneratedDocumentDTO, Error]:
        # Load project and template
        project = self._project_repo.get_by_id(cmd.project_id)
        template = self._template_repo.get_by_id(cmd.template_id)

        # Determine filename
        if cmd.custom_filename:
            filename = GeneratedFileName(
                name=cmd.custom_filename,
                extension=self._get_extension(cmd.output_type),
                full_name=f"{cmd.custom_filename}{self._get_extension(cmd.output_type)}"
            )
        else:
            # Use pattern from manifest
            pattern = template.get_naming_pattern(cmd.output_type)
            context = NamingContext(
                project_name=project.name,
                app_type_name=template.app_type_name,
                template_name=template.name,
                extension=self._get_extension(cmd.output_type),
                now=datetime.now(),
                increment_value=project.get_next_increment()
            )

            result = self._naming_service.resolve(pattern, context, project.field_values)
            if result.is_failure:
                return Result.failure(result.error)
            filename = result.value

        # Generate document with resolved filename
        output_path = project.path / template.default_folder / filename.full_name
        return self._generator.generate(project, template, output_path)
```

### 29.7 Fallback Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           NAMING FALLBACK CHAIN                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  1. Custom filename provided?                                                        │
│     └─► YES: Use custom filename                                                     │
│     └─► NO: Continue to step 2                                                       │
│                                                                                      │
│  2. Pattern defined in manifest.json?                                                │
│     └─► YES: Resolve pattern with field values                                       │
│     └─► NO: Continue to step 3                                                       │
│                                                                                      │
│  3. Pattern resulted in empty string?                                                │
│     └─► YES: Continue to step 4                                                      │
│     └─► NO: Use resolved filename                                                    │
│                                                                                      │
│  4. Use default fallback: "{project_name}_{date}"                                   │
│                                                                                      │
│  5. Still empty? Use: "document_{timestamp}"                                        │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 30. APP TYPE REGISTRY SYSTEM

### 30.1 Domain: App Type Aggregate

```python
# domain/app_type/entities/app_type_info.py

@dataclass(frozen=True)
class AppTypeInfo(AggregateRoot):
    """Metadata about an installed app type."""
    id: AppTypeId
    name: str
    name_localized: Dict[str, str]  # {"ar": "...", "en": "..."}
    version: str
    description: str
    icon_path: Optional[Path]
    color: Optional[str]
    capabilities: AppTypeCapabilities
    extensions: AppTypeExtensions
    is_builtin: bool  # True for pre-installed, False for user-added
```

### 30.2 Application: App Type Discovery Service

```python
# application/services/app_type_discovery_service.py

class AppTypeDiscoveryService:
    """Discovers and manages available app types."""

    def __init__(self, app_types_path: Path, registry: IAppTypeRegistry):
        self._path = app_types_path
        self._registry = registry

    def discover_all(self) -> List[AppTypeInfo]:
        """Scan app_types/ folder and register all valid app types."""
        app_types = []
        for folder in self._path.iterdir():
            if folder.is_dir() and (folder / "manifest.json").exists():
                info = self._load_app_type(folder)
                if info:
                    self._registry.register(info)
                    app_types.append(info)
        return app_types

    def _load_app_type(self, folder: Path) -> Optional[AppTypeInfo]:
        """Load app type from manifest.json."""
        manifest = json.loads((folder / "manifest.json").read_text())
        return AppTypeInfo(
            id=AppTypeId(manifest["id"]),
            name=manifest["name"],
            # ... map all fields
        )
```

### 30.3 Infrastructure: Extension Loader

```python
# infrastructure/extensions/extension_loader.py

class ExtensionLoader:
    """Loads custom extensions (transformers, validators, widgets) from app types."""

    def load_transformers(self, app_type: AppTypeInfo) -> Dict[str, Type[Transformer]]:
        """Load custom transformers from app type folder."""
        transformers = {}
        for module_path in app_type.extensions.custom_transformers:
            full_path = self._app_types_path / app_type.id / module_path
            module = self._import_module(full_path)
            for name, cls in inspect.getmembers(module, self._is_transformer):
                transformers[name] = cls
        return transformers

    def _is_transformer(self, obj) -> bool:
        return inspect.isclass(obj) and issubclass(obj, Transformer) and obj is not Transformer
```

---

## 31. WELCOME SCREEN DESIGN

### 31.1 App Type Selection UI

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│                              ╔═══════════════════════╗                              │
│                              ║     DOC HELPER        ║                              │
│                              ║  Document Generation  ║                              │
│                              ╚═══════════════════════╝                              │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                         Select Document Type                                 │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌───────────┐      │
│  │   🏗️ Soil       │  │   🏢 Structural │  │   🌿 Environ.   │  │    ➕     │      │
│  │  Investigation  │  │     Report      │  │   Assessment    │  │   Add     │      │
│  │                 │  │                 │  │                 │  │   New     │      │
│  │  [New Project]  │  │  [New Project]  │  │  [New Project]  │  │           │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └───────────┘      │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Recent Projects                                    │   │
│  ├─────────────────────────────────────────────────────────────────────────────┤   │
│  │  📁 Project Alpha      │ Soil Investigation │ Modified: 2024-01-15        │   │
│  │  📁 Building B Report  │ Structural Report  │ Modified: 2024-01-14        │   │
│  │  📁 Site Assessment    │ Environmental      │ Modified: 2024-01-10        │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  [Open Existing Project]                               [Settings] [Help]            │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 31.2 Welcome Screen ViewModel

```python
# presentation/viewmodels/welcome_vm.py

class WelcomeViewModel:
    """ViewModel for the welcome/app-type selection screen."""

    def __init__(self,
                 app_type_service: AppTypeDiscoveryService,
                 recent_service: RecentProjectsService,
                 project_service: ProjectService):
        self._app_type_service = app_type_service
        self._recent_service = recent_service
        self._project_service = project_service

        # Observable state
        self.app_types: List[AppTypeInfo] = []
        self.recent_projects: List[RecentProjectDTO] = []
        self.selected_app_type: Optional[AppTypeId] = None

    def load(self):
        """Load available app types and recent projects."""
        self.app_types = self._app_type_service.discover_all()
        self.recent_projects = self._recent_service.get_recent(limit=5)

    def create_new_project(self, app_type_id: AppTypeId, name: str, path: Path):
        """Create a new project of the selected app type."""
        return self._project_service.create_project(
            app_type_id=app_type_id,
            name=name,
            path=path
        )

    def open_project(self, path: Path):
        """Open an existing project (auto-detects app type from DB)."""
        return self._project_service.open_project(path)
```

---

## 32. FUTURE EXTENSIBILITY

### 32.1 Adding a New App Type (User Guide)

To add a new document type to Doc Helper:

1. **Create folder**: `app_types/my_new_type/`

2. **Create manifest.json**:
   ```json
   {
     "id": "my_new_type",
     "name": "My New Report Type",
     "version": "1.0.0",
     "capabilities": { "word_generation": true }
   }
   ```

3. **Create config.db** with tables:
   - `entities` - Define your data entities (forms/tabs)
   - `fields` - Define fields within each entity
   - `validation_rules` - Add validation for fields
   - `formulas` - Add computed fields
   - `control_relations` - Add inter-field dependencies
   - `output_mappings` - Map fields to Word content controls

4. **Create templates/** folder with Word/Excel templates

5. **Restart Doc Helper** - Your new type appears automatically!

### 32.2 Extension Points

| Extension | How to Add | Example Use Case |
|-----------|------------|------------------|
| **Custom Transformer** | Python file in `app_type/transformers/` | Arabic date formatting |
| **Custom Validator** | Python file in `app_type/validators/` | Industry-specific validation |
| **Custom Widget** | Python file in `app_type/widgets/` | Specialized input control |
| **Custom Function** | Register in manifest | Domain-specific formula function |

### 32.3 Marketplace Ready (Future)

The architecture supports a potential app type marketplace:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            App Type Marketplace                                      │
│                                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                      │
│  │  Construction   │  │    Medical      │  │     Legal       │                      │
│  │    Reports      │  │    Reports      │  │   Documents     │                      │
│  │   ⭐⭐⭐⭐⭐       │  │   ⭐⭐⭐⭐         │  │   ⭐⭐⭐⭐⭐       │                      │
│  │   [Install]     │  │   [Install]     │  │   [Installed]   │                      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                      │
│                                                                                      │
│  • Download app type packages (.dochelper files)                                    │
│  • Auto-install templates and schemas                                               │
│  • Version management and updates                                                   │
│  • Community-contributed app types                                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 33. UPDATED FOLDER STRUCTURE

```
doc_helper/
├── pyproject.toml
├── pytest.ini
│
├── src/
│   └── doc_helper/                   # Renamed from soil_report
│       │
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── domain/                   # UNCHANGED - All bounded contexts
│       │   ├── common/
│       │   ├── schema/
│       │   ├── project/
│       │   ├── validation/
│       │   ├── formula/
│       │   ├── control/
│       │   ├── override/
│       │   ├── document/
│       │   ├── transformer/
│       │   ├── file/
│       │   └── app_type/             # NEW - App type registry
│       │       ├── entities/
│       │       │   └── app_type_info.py
│       │       ├── value_objects/
│       │       │   ├── app_type_id.py
│       │       │   ├── capabilities.py
│       │       │   └── extensions.py
│       │       └── repositories.py
│       │
│       ├── application/              # Minor additions
│       │   ├── services/
│       │   │   ├── app_type_discovery_service.py  # NEW
│       │   │   └── ... (existing)
│       │   └── ... (existing)
│       │
│       ├── infrastructure/           # Minor additions
│       │   ├── extensions/           # NEW - Extension loading
│       │   │   ├── __init__.py
│       │   │   └── extension_loader.py
│       │   └── ... (existing)
│       │
│       └── presentation/             # Minor additions
│           ├── views/
│           │   ├── welcome_view.py   # UPDATED - App type selection
│           │   └── ... (existing)
│           ├── viewmodels/
│           │   ├── welcome_vm.py     # UPDATED - App type logic
│           │   └── ... (existing)
│           └── ... (existing)
│
├── app_types/                        # APP-TYPE PACKAGES
│   ├── soil_investigation/
│   │   ├── manifest.json
│   │   ├── config.db
│   │   ├── templates/
│   │   └── transformers/
│   │
│   └── _template/                    # Template for new app types
│       ├── manifest.json
│       ├── config.db.template
│       └── README.md
│
├── config/                           # Global config (unchanged)
│   ├── user_config.json
│   └── recent_projects.json
│
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## 34. MIGRATION FROM OLD DESIGN

### 34.1 What Changes from Original Plan

| Aspect | Original Plan | Updated for Doc Helper |
|--------|---------------|------------------------|
| Package name | `soil_report` | `doc_helper` |
| Welcome screen | Direct to project | App type selection first |
| App type handling | One app type assumed | Discovery service scans folder |
| Extensions | None | Custom transformers/validators per app type |
| Manifest | None | `manifest.json` per app type |

### 34.2 What Stays the Same

- All 9 bounded contexts (unchanged)
- All 12 ADRs (still valid)
- Clean Architecture layers (unchanged)
- CQRS pattern (unchanged)
- MVVM in presentation (unchanged)
- Repository pattern (unchanged)
- Test strategy (unchanged)

### 34.3 Updated Milestone Impact

Only 2 milestones need minor updates:

| Milestone | Update Needed |
|-----------|---------------|
| M1: Foundation | Rename to `doc_helper/` |
| M11: Presentation | Add app type selection to welcome screen |

All other milestones remain identical - the generalization is mostly in naming and the welcome screen.

---

## 35. SUMMARY: DOC HELPER BENEFITS

### 35.1 For Users
- One application for all document types
- Consistent experience across different reports
- Easy to add new document types
- Share projects across team

### 35.2 For Developers
- Single codebase to maintain
- Shared core reduces duplication
- App types are self-contained
- Easy to test each app type independently

### 35.3 For Future Growth
- Marketplace-ready architecture
- Community can contribute app types
- Versioned app type packages
- Gradual feature rollout per app type

---

# Phase 6: Additional Features

## 36. USER EXPERIENCE ENHANCEMENTS

### 36.1 Auto-Save & Draft Recovery

**Purpose**: Prevent data loss from crashes or accidental closure.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           AUTO-SAVE SYSTEM                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐    │
│  │ User edits  │ ───▶ │  Debounce   │ ───▶ │ Save draft  │ ───▶ │  .autosave  │    │
│  │   field     │      │  (30 sec)   │      │  to file    │      │    file     │    │
│  └─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘    │
│                                                                                      │
│  On App Start:                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  Check for .autosave file → Prompt "Recover unsaved changes?" → Yes/No      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Implementation**:
```python
# domain/project/services/auto_save_service.py

class AutoSaveService:
    DEBOUNCE_SECONDS = 30
    AUTOSAVE_FILENAME = ".autosave.json"

    def __init__(self, project_repo: IProjectRepository):
        self._project_repo = project_repo
        self._timer: Optional[Timer] = None
        self._pending_changes: Dict[FieldId, Any] = {}

    def on_field_changed(self, field_id: FieldId, value: Any):
        """Queue change and reset debounce timer."""
        self._pending_changes[field_id] = value
        self._reset_timer()

    def _reset_timer(self):
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(self.DEBOUNCE_SECONDS, self._save_draft)
        self._timer.start()

    def _save_draft(self):
        """Save pending changes to autosave file."""
        # Write to .autosave.json in project folder
        pass

    def check_recovery(self, project_path: Path) -> Optional[AutoSaveData]:
        """Check if autosave file exists for recovery."""
        autosave_path = project_path / self.AUTOSAVE_FILENAME
        if autosave_path.exists():
            return AutoSaveData.from_file(autosave_path)
        return None

    def clear_autosave(self, project_path: Path):
        """Delete autosave file after successful save."""
        autosave_path = project_path / self.AUTOSAVE_FILENAME
        if autosave_path.exists():
            autosave_path.unlink()
```

**UI Flow**:
1. On app start with project → check for `.autosave.json`
2. If found → show dialog: "Unsaved changes detected. Recover?"
3. Yes → merge autosave data into project
4. No → delete autosave file
5. On successful manual save → delete autosave file

---

### 36.2 Quick Search (Ctrl+F)

**Purpose**: Find fields quickly in large forms.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔍 Search: [report_num____________]  [< Prev] [Next >]  3 of 12 matches            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Search matches:                                                                     │
│  • Field labels (e.g., "Report Number")                                             │
│  • Field values (e.g., "2024-001")                                                  │
│  • Field IDs (e.g., "report_number")                                                │
│                                                                                      │
│  Actions:                                                                            │
│  • Enter / F3 → Jump to next match                                                  │
│  • Shift+F3 → Jump to previous match                                                │
│  • Esc → Close search bar                                                           │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Implementation**:
```python
# presentation/viewmodels/search_vm.py

@dataclass
class SearchMatch:
    entity_id: EntityId
    field_id: FieldId
    match_type: str  # "label", "value", "id"
    match_text: str
    highlight_range: Tuple[int, int]


class SearchViewModel:
    def __init__(self, project_vm: ProjectViewModel):
        self._project_vm = project_vm
        self.query: str = ""
        self.matches: List[SearchMatch] = []
        self.current_index: int = 0

    def search(self, query: str):
        """Search across all fields."""
        self.query = query.lower()
        self.matches = []

        for entity in self._project_vm.entities:
            for field in entity.fields:
                # Search in label
                if self.query in field.label.lower():
                    self.matches.append(SearchMatch(
                        entity_id=entity.id,
                        field_id=field.id,
                        match_type="label",
                        match_text=field.label,
                        highlight_range=self._find_range(field.label, query)
                    ))
                # Search in value
                value_str = str(field.value or "")
                if self.query in value_str.lower():
                    self.matches.append(SearchMatch(...))

        self.current_index = 0 if self.matches else -1

    def next_match(self) -> Optional[SearchMatch]:
        if not self.matches:
            return None
        self.current_index = (self.current_index + 1) % len(self.matches)
        return self.matches[self.current_index]

    def previous_match(self) -> Optional[SearchMatch]:
        if not self.matches:
            return None
        self.current_index = (self.current_index - 1) % len(self.matches)
        return self.matches[self.current_index]
```

---

### 36.3 Keyboard Navigation

**Purpose**: Efficient navigation without mouse.

| Shortcut | Action |
|----------|--------|
| `Tab` / `Shift+Tab` | Move to next/previous field |
| `Ctrl+S` | Save project |
| `Ctrl+G` | Generate document |
| `Ctrl+F` | Open search |
| `Ctrl+Z` / `Ctrl+Y` | Undo / Redo |
| `Ctrl+N` | New project |
| `Ctrl+O` | Open project |
| `Ctrl+W` | Close project |
| `F1` | Help |
| `Ctrl+1-9` | Jump to tab 1-9 |
| `Ctrl+Tab` | Next tab |
| `Ctrl+Shift+Tab` | Previous tab |

**Implementation**:
```python
# presentation/adapters/keyboard_adapter.py

class KeyboardAdapter:
    def __init__(self, main_window: QMainWindow, command_bus: ICommandBus):
        self._main_window = main_window
        self._command_bus = command_bus
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        shortcuts = {
            "Ctrl+S": self._save_project,
            "Ctrl+G": self._generate_document,
            "Ctrl+F": self._open_search,
            "Ctrl+Z": self._undo,
            "Ctrl+Y": self._redo,
            "Ctrl+N": self._new_project,
            "Ctrl+O": self._open_project,
            "Ctrl+W": self._close_project,
        }

        for key, handler in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self._main_window)
            shortcut.activated.connect(handler)

        # Tab shortcuts (Ctrl+1 through Ctrl+9)
        for i in range(1, 10):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self._main_window)
            shortcut.activated.connect(lambda idx=i: self._jump_to_tab(idx - 1))
```

---

### 36.4 Field History

**Purpose**: View and restore previous values of a field.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  Field: Report Number                                                    [History]  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │ 2024-003                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─────────────────────── Field History ───────────────────────┐                    │
│  │  2024-01-19 14:32  │  2024-003      │ (current)  │          │                    │
│  │  2024-01-19 10:15  │  2024-002      │            │ [Restore]│                    │
│  │  2024-01-18 16:45  │  2024-001      │            │ [Restore]│                    │
│  │  2024-01-18 09:00  │  (empty)       │            │ [Restore]│                    │
│  └─────────────────────────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Database Schema**:
```sql
-- In project.db
CREATE TABLE field_history (
    id INTEGER PRIMARY KEY,
    field_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    record_id TEXT,           -- For collection entities
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_source TEXT        -- "user", "formula", "import", "restore"
);

CREATE INDEX idx_field_history_field ON field_history(field_id, entity_id);
```

**Domain**:
```python
# domain/project/entities/field_history_entry.py

@dataclass(frozen=True)
class FieldHistoryEntry:
    id: HistoryEntryId
    field_id: FieldId
    entity_id: EntityId
    record_id: Optional[str]
    old_value: Any
    new_value: Any
    changed_at: datetime
    change_source: ChangeSource  # USER, FORMULA, IMPORT, RESTORE

# domain/project/repositories.py
class IFieldHistoryRepository(ABC):
    @abstractmethod
    def get_history(self, field_id: FieldId, entity_id: EntityId,
                    limit: int = 20) -> List[FieldHistoryEntry]: ...

    @abstractmethod
    def add_entry(self, entry: FieldHistoryEntry) -> None: ...
```

---

### 36.5 Dark Mode

**Purpose**: Reduce eye strain, user preference.

```python
# presentation/styles/theme.py

from enum import Enum
from dataclasses import dataclass

class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"  # Follow OS setting


@dataclass(frozen=True)
class ThemeColors:
    background: str
    surface: str
    primary: str
    secondary: str
    text: str
    text_secondary: str
    border: str
    error: str
    warning: str
    success: str


LIGHT_THEME = ThemeColors(
    background="#FFFFFF",
    surface="#F5F5F5",
    primary="#1976D2",
    secondary="#424242",
    text="#212121",
    text_secondary="#757575",
    border="#E0E0E0",
    error="#D32F2F",
    warning="#FFA000",
    success="#388E3C",
)

DARK_THEME = ThemeColors(
    background="#121212",
    surface="#1E1E1E",
    primary="#90CAF9",
    secondary="#B0BEC5",
    text="#FFFFFF",
    text_secondary="#B0B0B0",
    border="#333333",
    error="#EF5350",
    warning="#FFB74D",
    success="#66BB6A",
)


class ThemeManager:
    def __init__(self):
        self._mode = ThemeMode.LIGHT
        self._on_change_callbacks: List[Callable] = []

    @property
    def colors(self) -> ThemeColors:
        if self._mode == ThemeMode.DARK:
            return DARK_THEME
        elif self._mode == ThemeMode.SYSTEM:
            # Check OS dark mode setting
            return DARK_THEME if self._is_system_dark() else LIGHT_THEME
        return LIGHT_THEME

    def set_mode(self, mode: ThemeMode):
        self._mode = mode
        self._notify_change()

    def get_stylesheet(self) -> str:
        """Generate Qt stylesheet from current theme."""
        c = self.colors
        return f"""
            QMainWindow, QDialog {{
                background-color: {c.background};
                color: {c.text};
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {c.surface};
                border: 1px solid {c.border};
                color: {c.text};
                padding: 8px;
            }}
            QPushButton {{
                background-color: {c.primary};
                color: white;
                border: none;
                padding: 8px 16px;
            }}
            /* ... more styles ... */
        """
```

---

## 37. DATA MANAGEMENT

### 37.1 Import from Excel/CSV

**Purpose**: Bulk import data from spreadsheets.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            Import Data from Excel                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  File: [C:\data\boreholes.xlsx_________________] [Browse...]                        │
│                                                                                      │
│  Sheet: [Boreholes ▼]                                                               │
│                                                                                      │
│  ┌─────────────────────────── Column Mapping ───────────────────────────┐           │
│  │                                                                       │           │
│  │  Excel Column          →    Field                                     │           │
│  │  ─────────────────────────────────────────────────────────────────   │           │
│  │  A: "Borehole ID"      →    [borehole_name ▼]                        │           │
│  │  B: "Depth (m)"        →    [total_depth ▼]                          │           │
│  │  C: "X Coordinate"     →    [coord_x ▼]                              │           │
│  │  D: "Y Coordinate"     →    [coord_y ▼]                              │           │
│  │  E: "Date"             →    [drilling_date ▼]                        │           │
│  │  F: "Notes"            →    [-- Skip --▼]                            │           │
│  │                                                                       │           │
│  └───────────────────────────────────────────────────────────────────────┘           │
│                                                                                      │
│  Preview (first 5 rows):                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐           │
│  │  BH-01  │  15.0  │  123456.7  │  987654.3  │  2024-01-15  │           │           │
│  │  BH-02  │  12.5  │  123460.2  │  987650.1  │  2024-01-16  │           │           │
│  │  ...                                                                  │           │
│  └───────────────────────────────────────────────────────────────────────┘           │
│                                                                                      │
│  Options:                                                                            │
│  [✓] First row is header                                                            │
│  [ ] Replace existing data    [✓] Append to existing                                │
│                                                                                      │
│                                              [Cancel]  [Preview Import]  [Import]   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Implementation**:
```python
# application/commands/data/import_from_excel.py

@dataclass(frozen=True)
class ImportFromExcelCommand:
    project_id: ProjectId
    file_path: Path
    sheet_name: str
    target_entity: EntityId
    column_mapping: Dict[str, FieldId]  # Excel column → Field ID
    has_header: bool
    mode: ImportMode  # REPLACE, APPEND


class ImportFromExcelHandler:
    def __init__(self,
                 project_repo: IProjectRepository,
                 excel_service: IExcelService,
                 validation_service: ValidationService):
        self._project_repo = project_repo
        self._excel_service = excel_service
        self._validation_service = validation_service

    def execute(self, cmd: ImportFromExcelCommand) -> Result[ImportResultDTO, ImportError]:
        # 1. Read Excel file
        rows = self._excel_service.read_sheet(cmd.file_path, cmd.sheet_name)

        # 2. Skip header if needed
        data_rows = rows[1:] if cmd.has_header else rows

        # 3. Map columns to fields
        imported = []
        errors = []

        for row_idx, row in enumerate(data_rows):
            record = {}
            row_errors = []

            for col, field_id in cmd.column_mapping.items():
                col_idx = self._col_to_index(col)
                value = row[col_idx] if col_idx < len(row) else None

                # Validate value
                validation = self._validation_service.validate_field(field_id, value)
                if validation.is_valid:
                    record[field_id] = value
                else:
                    row_errors.append(f"Row {row_idx + 1}, {col}: {validation.error}")

            if row_errors:
                errors.extend(row_errors)
            else:
                imported.append(record)

        # 4. Apply to project
        if cmd.mode == ImportMode.REPLACE:
            self._clear_entity_data(cmd.project_id, cmd.target_entity)

        for record in imported:
            self._add_record(cmd.project_id, cmd.target_entity, record)

        return Result.success(ImportResultDTO(
            total_rows=len(data_rows),
            imported_count=len(imported),
            error_count=len(errors),
            errors=errors[:20]  # First 20 errors
        ))
```

---

### 37.2 Export Project Data

**Purpose**: Export all project data (not just generated document).

**Export Formats**:
- **JSON**: Full project data with metadata
- **Excel**: One sheet per entity
- **CSV**: One file per entity

```python
# application/commands/data/export_project_data.py

@dataclass(frozen=True)
class ExportProjectDataCommand:
    project_id: ProjectId
    output_path: Path
    format: ExportFormat  # JSON, EXCEL, CSV
    include_metadata: bool
    include_history: bool


class ExportProjectDataHandler:
    def execute(self, cmd: ExportProjectDataCommand) -> Result[Path, ExportError]:
        project = self._project_repo.get_by_id(cmd.project_id)

        if cmd.format == ExportFormat.JSON:
            return self._export_json(project, cmd)
        elif cmd.format == ExportFormat.EXCEL:
            return self._export_excel(project, cmd)
        elif cmd.format == ExportFormat.CSV:
            return self._export_csv(project, cmd)

    def _export_json(self, project: Project, cmd: ExportProjectDataCommand) -> Result:
        data = {
            "project_name": project.name,
            "app_type": project.app_type_id,
            "exported_at": datetime.now().isoformat(),
            "entities": {}
        }

        for entity in project.entities:
            data["entities"][entity.id] = {
                "type": entity.entity_type,
                "records": [
                    {field.id: field.value for field in record.fields}
                    for record in entity.records
                ]
            }

        if cmd.include_metadata:
            data["metadata"] = {
                "created_at": project.created_at.isoformat(),
                "modified_at": project.modified_at.isoformat(),
            }

        output_path = cmd.output_path / f"{project.name}_export.json"
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return Result.success(output_path)
```

---

### 37.3 Clone Project

**Purpose**: Duplicate an existing project as a starting point.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Clone Project                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Source Project: "Building A Site Investigation"                                     │
│                                                                                      │
│  New Project Name: [Building B Site Investigation____]                              │
│                                                                                      │
│  Location: [C:\Projects\________________________] [Browse...]                       │
│                                                                                      │
│  Clone Options:                                                                      │
│  [✓] Copy all field values                                                          │
│  [✓] Copy attached files                                                            │
│  [ ] Copy generated documents                                                        │
│  [ ] Copy field history                                                              │
│                                                                                      │
│  Fields to Clear (reset to default):                                                │
│  [✓] Report Number                                                                  │
│  [✓] Report Date                                                                    │
│  [ ] Project Name                                                                   │
│  [ ] Client Name                                                                    │
│                                                                                      │
│                                                    [Cancel]  [Clone Project]        │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Implementation**:
```python
# application/commands/project/clone_project.py

@dataclass(frozen=True)
class CloneProjectCommand:
    source_project_id: ProjectId
    new_name: str
    new_path: Path
    copy_files: bool
    copy_generated: bool
    copy_history: bool
    fields_to_clear: List[FieldId]


class CloneProjectHandler:
    def execute(self, cmd: CloneProjectCommand) -> Result[ProjectDTO, CloneError]:
        # 1. Load source project
        source = self._project_repo.get_by_id(cmd.source_project_id)

        # 2. Create new project with same app type
        new_project = Project.create(
            name=cmd.new_name,
            path=cmd.new_path,
            app_type_id=source.app_type_id
        )

        # 3. Copy field values (except cleared ones)
        for field_id, value in source.field_values.items():
            if field_id not in cmd.fields_to_clear:
                new_project.set_value(field_id, value.raw_value)

        # 4. Copy files if requested
        if cmd.copy_files:
            self._copy_attachments(source, new_project)

        # 5. Save new project
        self._project_repo.save(new_project)

        return Result.success(ProjectDTO.from_entity(new_project))
```

---

## 38. DOCUMENT GENERATION ENHANCEMENTS

### 38.1 Version History

**Purpose**: Keep track of all generated documents.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          Document Version History                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Project: Building A Site Investigation                                              │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  Version  │  Generated      │  Template        │  Size    │  Actions       │   │
│  │───────────┼─────────────────┼──────────────────┼──────────┼────────────────│   │
│  │  v5       │  2024-01-19     │  Arabic Report   │  2.4 MB  │  [Open] [Del]  │   │
│  │           │  14:32:15       │                  │          │                │   │
│  │───────────┼─────────────────┼──────────────────┼──────────┼────────────────│   │
│  │  v4       │  2024-01-18     │  Arabic Report   │  2.3 MB  │  [Open] [Del]  │   │
│  │           │  16:45:22       │                  │          │                │   │
│  │───────────┼─────────────────┼──────────────────┼──────────┼────────────────│   │
│  │  v3       │  2024-01-17     │  English Report  │  2.1 MB  │  [Open] [Del]  │   │
│  │           │  09:15:33       │                  │          │                │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  [Compare v4 ↔ v5]                          [Delete All Old Versions]               │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Storage Structure**:
```
Projects/
└── Building A/
    ├── project.db
    ├── attachments/
    └── generated/
        ├── current/
        │   └── 2024-001_Building A.docx    # Latest version
        └── history/
            ├── v1_2024-01-15_093012/
            │   └── 2024-001_Building A.docx
            ├── v2_2024-01-16_141522/
            │   └── 2024-001_Building A.docx
            └── v3_2024-01-17_091533/
                └── 2024-001_Building A.docx
```

**Database Schema**:
```sql
-- In project.db
CREATE TABLE document_versions (
    id INTEGER PRIMARY KEY,
    version_number INTEGER NOT NULL,
    template_id TEXT NOT NULL,
    template_name TEXT NOT NULL,
    output_type TEXT NOT NULL,      -- WORD, EXCEL, PDF
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_by TEXT,              -- User name (future)
    notes TEXT
);
```

---

## 39. VALIDATION & QUALITY

### 39.1 Warnings vs Errors

**Purpose**: Distinguish between blocking errors and non-blocking warnings.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        VALIDATION SEVERITY LEVELS                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  🔴 ERROR (Blocking)                                                                │
│  ─────────────────                                                                   │
│  • Required field is empty                                                          │
│  • Value out of allowed range                                                       │
│  • Invalid format (e.g., date, number)                                              │
│  • Constraint violation                                                              │
│  → BLOCKS document generation                                                        │
│                                                                                      │
│  🟡 WARNING (Non-blocking)                                                          │
│  ────────────────────────                                                            │
│  • Unusually high/low value                                                         │
│  • Recommended field is empty                                                       │
│  • Potential typo detected                                                          │
│  • Data inconsistency between fields                                                │
│  → Shows warning, but ALLOWS generation                                             │
│                                                                                      │
│  🔵 INFO (Informational)                                                            │
│  ───────────────────────                                                             │
│  • Default value being used                                                         │
│  • Auto-calculated value                                                            │
│  • Suggestion for improvement                                                       │
│  → No impact on generation                                                          │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Domain Implementation**:
```python
# domain/validation/value_objects/validation_severity.py

class ValidationSeverity(Enum):
    ERROR = "error"        # Blocking
    WARNING = "warning"    # Non-blocking
    INFO = "info"          # Informational


@dataclass(frozen=True)
class ValidationIssue:
    field_id: FieldId
    severity: ValidationSeverity
    message: str
    code: str  # e.g., "REQUIRED", "OUT_OF_RANGE", "UNUSUAL_VALUE"


@dataclass(frozen=True)
class ValidationResult:
    issues: Tuple[ValidationIssue, ...]

    @property
    def has_errors(self) -> bool:
        return any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == ValidationSeverity.WARNING for i in self.issues)

    @property
    def can_generate(self) -> bool:
        """True if no blocking errors."""
        return not self.has_errors

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
```

**Schema Configuration**:
```sql
-- In config.db (validation_rules table)
-- Add severity column
ALTER TABLE validation_rules ADD COLUMN severity TEXT DEFAULT 'error';

-- Example: Unusual depth warning
INSERT INTO validation_rules (field_id, rule_type, severity, params)
VALUES ('total_depth', 'MAX_VALUE', 'warning', '{"max": 100, "message": "Depth > 100m is unusual"}');
```

---

### 39.2 Pre-Generation Checklist

**Purpose**: Review all issues before generating document.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Pre-Generation Checklist                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Template: Arabic Report                                                             │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  🔴 ERRORS (2) - Must fix before generating                                  │   │
│  ├─────────────────────────────────────────────────────────────────────────────┤   │
│  │  ❌ Report Number is required                          [Go to field]         │   │
│  │  ❌ At least one borehole is required                  [Go to tab]           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  🟡 WARNINGS (3) - Review recommended                                        │   │
│  ├─────────────────────────────────────────────────────────────────────────────┤   │
│  │  ⚠️ Total depth (150m) is unusually high               [Go to field]         │   │
│  │  ⚠️ Project date is more than 1 year ago               [Go to field]         │   │
│  │  ⚠️ Client phone number is empty                       [Go to field]         │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  ✅ PASSED (45 fields validated)                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  [ ] I have reviewed all warnings and want to proceed                               │
│                                                                                      │
│                                [Cancel]  [Generate with Warnings]                   │
│                                          (disabled until checkbox checked)          │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 39.3 Conditional Required

**Purpose**: Fields required only under certain conditions.

**Examples**:
- "Water Level" required only if "Water Encountered" = Yes
- "Company Registration" required only if "Client Type" = Company
- "Soil Description" required for each borehole with samples

**Schema Configuration**:
```sql
-- In config.db (validation_rules table)
CREATE TABLE conditional_required (
    id INTEGER PRIMARY KEY,
    field_id TEXT NOT NULL,              -- Field that becomes required
    condition_field TEXT NOT NULL,        -- Field to check
    condition_operator TEXT NOT NULL,     -- "equals", "not_equals", "greater_than", etc.
    condition_value TEXT,                 -- Value to compare
    error_message TEXT
);

-- Example: Water Level required if Water Encountered = "yes"
INSERT INTO conditional_required (field_id, condition_field, condition_operator, condition_value, error_message)
VALUES ('water_level', 'water_encountered', 'equals', 'yes', 'Water level is required when water is encountered');
```

**Domain Implementation**:
```python
# domain/validation/specifications/conditional_required_spec.py

@dataclass(frozen=True)
class ConditionalRequiredSpec(Specification):
    target_field: FieldId
    condition_field: FieldId
    operator: ConditionOperator
    condition_value: Any
    error_message: str

    def is_satisfied_by(self, context: ValidationContext) -> bool:
        """Check if field is required and has value."""
        # First check if condition is met
        condition_value = context.get_value(self.condition_field)

        condition_met = self._evaluate_condition(condition_value)

        if not condition_met:
            # Condition not met, field not required
            return True

        # Condition met, field IS required
        target_value = context.get_value(self.target_field)
        return target_value is not None and target_value != ""

    def _evaluate_condition(self, actual_value: Any) -> bool:
        if self.operator == ConditionOperator.EQUALS:
            return actual_value == self.condition_value
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return actual_value != self.condition_value
        elif self.operator == ConditionOperator.GREATER_THAN:
            return actual_value > self.condition_value
        # ... more operators
```

---

## 40. FEATURE PRIORITY FOR IMPLEMENTATION

### 40.1 Phase 1 (Core Features) - Include in M11

| Feature | Priority | Effort |
|---------|----------|--------|
| Keyboard Navigation | High | Low |
| Warnings vs Errors | High | Medium |
| Pre-Generation Checklist | High | Medium |

### 40.2 Phase 2 (After Initial Release)

| Feature | Priority | Effort |
|---------|----------|--------|
| Auto-Save & Recovery | High | Medium |
| Dark Mode | Medium | Medium |
| Clone Project | High | Low |
| Quick Search | Medium | Medium |

### 40.3 Phase 3 (Enhancement)

| Feature | Priority | Effort |
|---------|----------|--------|
| Import from Excel | High | High |
| Export Project Data | Medium | Medium |
| Field History | Medium | Medium |
| Version History | Low | Medium |
| Conditional Required | Medium | Medium |

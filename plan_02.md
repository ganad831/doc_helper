# Plan: Rebuild plan.md with Phase 5/6 Integrated

## Objective
Restructure the plan.md to integrate the "Doc Helper" generalization (Phase 5) and UX enhancements (Phase 6) directly into the core phases, rather than having them as separate add-on phases.

**Decision**: Keep 12 milestones, integrate features within existing milestones.

---

## CRITICAL CORRECTIONS

### 1. Execution Scope vs Architectural Vision

**v1 Scope (Immediate Implementation)**:
- Single app type: Soil Investigation Report
- No manifest discovery, no registry, no welcome screen selection
- Hardcoded app type loading
- Core correctness features only

**v2+ Scope (Deferred / Architectural Vision)**:
- Multi-app-type support (manifest.json, discovery, registry)
- Welcome screen with app type selection
- Extension loading (custom transformers per app type)
- UX enhancements (dark mode, autosave, search, keyboard nav, field history UI)

### 2. Multi-App-Type is FUTURE
- v1 loads one concrete app type directly
- `AppTypeInfo` exists as a value object but is constructed programmatically, not from manifest
- No `AppTypeDiscoveryService` in v1
- No `ExtensionLoader` in v1
- Welcome screen shows recent projects only (no app type cards)

### 3. Schema Domain ≠ App Type Domain
**Schema Domain** (v1):
- `EntityDefinition`, `FieldDefinition`, `FieldType`
- Schema validation, field type behavior
- Loaded from config.db

**App Type Domain** (v2+):
- `AppTypeInfo`, `AppTypeCapabilities`, `AppTypeExtensions`
- Manifest parsing, extension discovery
- Plugin architecture

### 4. Domain Purity Enforcement
Domain layer must NOT:
- Parse JSON (infrastructure concern)
- Access filesystem (infrastructure concern)
- Use timers/scheduling (application/presentation concern)
- Perform I/O of any kind

All such operations belong in Infrastructure or Application layers.

### 5. UX Features Reclassified

**Core (v1 must-have)**:
- Keyboard shortcuts (Ctrl+S, Ctrl+Z/Y) - minimal set
- Pre-generation validation checklist (errors only, no warnings distinction yet)

**Secondary (v1.1 or v2)**:
- Dark mode
- Auto-save & recovery
- Quick search (Ctrl+F)
- Full keyboard navigation
- Field history UI
- Warnings vs Errors distinction

---

## v1 Definition of Done

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

## New Document Structure (Rebuilt plan.md)

```
1. PROJECT IDENTITY
   - Name: Doc Helper
   - Purpose: Document generation platform (v1: Soil Investigation only)
   - Vision: Universal multi-type platform (v2+)

2. FEATURES BY DOMAIN (v1 scope only)
   - Validation: Constraints, validators, simple pass/fail
   - Schema: EntityDefinition, FieldDefinition, FieldType
   - Formula: Parser, evaluator, dependency graph
   - Control: VALUE_SET, VISIBILITY, ENABLE rules
   - Project: Aggregate, field values, recent projects
   - Override: State machine (PENDING → ACCEPTED → SYNCED)
   - Document: Transformers, templates, adapters

3. BUSINESS RULES (keep from Phase 1)

4-5. SIDE EFFECTS & HIDDEN BEHAVIORS (keep)

6. ARCHITECTURAL PAIN POINTS (keep diagnosis)

7-8. ROOT CAUSES & RISKS (keep)

9. REWRITE STRATEGY (keep)

10. SUMMARY (keep)

11. HIGH-LEVEL ARCHITECTURE
   - Clean Architecture diagram
   - v1: Single app type (Soil Investigation)
   - v2+ Vision: Multi-app-type platform (documented but not implemented)

12. FOLDER STRUCTURE
   - Use doc_helper/ naming
   - app_types/ exists but v1 loads soil_investigation directly
   - NO extensions/ folder in v1

13-14. CORE DOMAIN ENTITIES (v1 scope)
   - Validation, Schema, Formula, Control, Project, Override, Document
   - NO App Type bounded context (v2+)
   - NO ValidationSeverity, FieldHistoryEntry, DocumentVersion (v2+)

15. APPLICATION LAYER (v1 scope)
   - Core CRUD commands, GenerateDocumentCommand
   - NO Import/Export/Clone commands (v2+)
   - NO AppTypeDiscoveryService (v2+)

16. INFRASTRUCTURE ADAPTERS (v1 scope)
   - SQLite repos, file storage
   - NO ExtensionLoader, AutoSaveStorage (v2+)

17. PRESENTATION LAYER (v1 scope)
   - ViewModels, widgets, views
   - Welcome screen with recent projects only
   - NO app type selection, search, dark mode (v2+)

18. DI SETUP (keep)

19. DESIGN PATTERNS (keep)

20. TESTABILITY (keep)

21-23. MILESTONES (v1 scope - 12 milestones)

24-26. VERIFICATION, RISKS, RATIONALE (keep)

ADRs (keep 12 + add ADR-013 for multi-app-type VISION)

ARCHITECTURE DIAGRAMS (v1 architecture)

ANTI-PATTERN CHECKLIST (keep)

NEW: FUTURE ROADMAP (v2+ features)
   - Multi-app-type platform
   - UX enhancements
   - Data operations
```

---

## Key Changes (v1 Focus)

### 1. Project Identity (From Start)
- Rename from `soil_report_v2/` → `doc_helper/`
- Package name: `doc_helper` (not `soil_report`)
- Position as "Document Generation Platform" (vision: universal, but v1 = one type)

### 2. v1 Domain Layer (M2-M7)
- **Validation Domain** (M2):
  - Core validation constraints and validators
  - Simple ValidationResult (errors only, no severity levels yet)

- **Schema Domain** (M3):
  - `EntityDefinition`, `FieldDefinition`, `FieldType`
  - Schema loaded directly from config.db
  - NO `AppTypeInfo` aggregate (v2+)
  - NO manifest.json parsing (v2+)

- **Formula Domain** (M4):
  - Parser, evaluator, dependency graph
  - (Unchanged from original)

- **Control Domain** (M5):
  - Control rules, effect evaluation
  - (Unchanged from original)

- **Project Domain** (M6):
  - Project aggregate, field values
  - NO `FieldHistoryEntry` (v2+)
  - NO auto-save concept (v2+)

- **Override Domain** (M7):
  - Override state machine, conflict detection
  - (Unchanged from original)

### 3. v1 Infrastructure Layer (M8)
- SQLite repositories for all domain entities
- File storage for projects
- NO `ExtensionLoader` (v2+)
- NO `FieldHistoryRepository` (v2+)
- NO `AutoSaveStorage` (v2+)

### 4. v1 Application Layer (M10)
- **Commands**:
  - `CreateProjectCommand`, `OpenProjectCommand`, `SaveProjectCommand`
  - `UpdateFieldCommand`, `SetFieldOverrideCommand`
  - `GenerateDocumentCommand` (basic naming only)
  - NO import/export/clone commands (v2+)

- **Services**:
  - `ValidationService`, `FormulaService`, `ControlService`
  - NO `AppTypeDiscoveryService` (v2+)
  - NO `AutoSaveService` (v2+)

- **Queries**:
  - `GetProjectQuery`, `GetEntityFieldsQuery`
  - `GetValidationResultQuery`
  - NO `GetFieldHistoryQuery` (v2+)
  - NO `GetDocumentVersionsQuery` (v2+)

### 5. v1 Presentation Layer (M11)
- **Welcome Screen**:
  - Recent projects list ONLY
  - NO app type selection cards (v2+)

- **ViewModels**:
  - `ProjectViewModel`, `EntityViewModel`, `FieldViewModel`
  - `DocumentGenerationViewModel`
  - NO `SearchViewModel` (v2+)
  - NO `FieldHistoryViewModel` (v2+)

- **Widgets/Features**:
  - All 12 field type widgets
  - Pre-generation checklist dialog (errors only)
  - Minimal keyboard shortcuts (Ctrl+S, Ctrl+Z/Y)
  - NO full keyboard navigation adapter (v2+)
  - NO search bar (v2+)
  - NO field history popover (v2+)

- **Styles**:
  - Light theme only
  - NO dark mode / theme switching (v2+)

### 6. v1 Folder Structure
```
doc_helper/
├── src/doc_helper/
│   ├── domain/
│   │   ├── validation/        # constraints, validators
│   │   ├── schema/            # entity/field definitions
│   │   ├── formula/           # parser, evaluator
│   │   ├── control/           # control rules
│   │   ├── project/           # project aggregate
│   │   ├── override/          # override state machine
│   │   └── document/          # transformers, templates
│   ├── application/
│   │   ├── commands/          # CRUD + generate
│   │   ├── queries/           # read operations
│   │   └── services/          # coordination
│   ├── infrastructure/
│   │   ├── persistence/       # SQLite repos
│   │   └── filesystem/        # file storage
│   └── presentation/
│       ├── viewmodels/        # MVVM
│       ├── widgets/           # field widgets
│       └── views/             # main views
│
└── app_types/
    └── soil_investigation/
        ├── config.db          # schema definition
        └── templates/         # Word/Excel templates
```

**Note**: `app_types/` folder exists but v1 only uses `soil_investigation/` directly (no manifest.json discovery).

### 7. v1 Milestone Summary

| Milestone | Focus | Scope |
|-----------|-------|-------|
| M1 | Foundation | `doc_helper/` naming, base classes, Result monad |
| M2 | Validation | Constraints, validators (no severity levels) |
| M3 | Schema | EntityDefinition, FieldDefinition, FieldType |
| M4 | Formula | Parser, evaluator, dependency graph |
| M5 | Control | Control rules, effect evaluation |
| M6 | Project | Project aggregate, field values (no history) |
| M7 | Override | Override state machine |
| M8 | Infrastructure | SQLite repos, file storage |
| M9 | Document Gen | Transformers, templates, adapters |
| M10 | Application | Commands, queries, services |
| M11 | Presentation | ViewModels, widgets, views, minimal shortcuts |
| M12 | Polish | Testing, bug fixes, documentation |

### 8. v2+ Deferred Features

**App Type Platform (v2)**:
- `AppTypeInfo` aggregate, `IAppTypeRegistry`
- `manifest.json` parsing
- `AppTypeDiscoveryService`
- `ExtensionLoader`
- Welcome screen with app type cards

**UX Enhancements (v2+)**:
- ValidationSeverity (ERROR/WARNING/INFO)
- Dark mode / theme switching
- Auto-save & recovery
- Quick search (Ctrl+F)
- Full keyboard navigation
- Field history UI

**Data Operations (v2+)**:
- Import from Excel
- Export project data
- Clone project
- Document version history

## Implementation Approach

The rebuilt plan.md will:
1. Use "Doc Helper" naming throughout
2. Document v2+ features as VISION (not immediate implementation)
3. Keep milestones focused on v1 scope
4. Move Phase 5/6 content to "Future Roadmap" section
5. Remove Phase 5/6 headers - content reorganized
6. Add ADR-013 for multi-app-type VISION (deferred implementation)

---

## Detailed Milestone Integration (v1 Scope)

### M1: Foundation (Days 1-10)
**Scope**: Project setup, base classes, Result monad
- Use `doc_helper/` folder name from start
- Package: `src/doc_helper/`
- Base classes: Entity, AggregateRoot, ValueObject
- Result[T, E] monad for error handling
- Domain event infrastructure

### M2: Validation Domain (Days 11-20)
**Scope**: Core validation constraints and validators
- `FieldConstraint` value objects (min/max, pattern, required)
- `IValidator` interface
- `ValidationResult` with errors list
- Built-in validators for all 12 field types
- NO ValidationSeverity (v2+ - keep simple pass/fail for v1)

### M3: Schema Domain (Days 21-30)
**Scope**: Field types, entity definitions
- `FieldType` enum (12 types)
- `FieldDefinition` value object
- `EntityDefinition` aggregate
- `ISchemaRepository` interface
- Schema loaded directly from config.db
- NO `AppTypeInfo` aggregate (v2+)
- NO manifest parsing (v2+)

### M4: Formula Domain (Days 31-42)
**Scope**: Parser, evaluator, dependency graph
- Formula tokenizer and parser
- Expression AST
- `FormulaEvaluator` with dependency tracking
- Circular dependency detection
- (Unchanged from original plan)

### M5: Control Domain (Days 43-52)
**Scope**: Control rules, effect evaluation
- `ControlRule` entity
- Control types: VALUE_SET, VISIBILITY, ENABLE
- `ControlEffectEvaluator`
- (Unchanged from original plan)

### M6: Project Domain (Days 53-65)
**Scope**: Project aggregate, field values
- `Project` aggregate root
- `FieldValue` value object
- `IProjectRepository` interface
- Recent projects tracking (simple list)
- NO `FieldHistoryEntry` (v2+)
- NO auto-save (v2+)

### M7: Override Domain (Days 66-75)
**Scope**: Override state machine, conflict detection
- `OverrideState` enum (PENDING, ACCEPTED, SYNCED)
- State transitions: accept, reject, sync
- Formula/Control conflict detection
- (Unchanged from original plan)

### M8: Infrastructure Layer (Days 76-95)
**Scope**: SQLite repositories, file storage
- `SqliteSchemaRepository`
- `SqliteProjectRepository`
- `FileProjectStorage` (.dhproj files)
- Recent projects persistence
- NO `ExtensionLoader` (v2+)
- NO `FieldHistoryRepository` (v2+)
- NO `AutoSaveStorage` (v2+)

### M9: Document Generation (Days 96-115)
**Scope**: Transformers, templates, adapters
- All 15+ built-in transformers
- `ITransformer` interface
- `WordDocumentAdapter` (python-docx)
- `ExcelDocumentAdapter` (xlwings)
- `PdfExportAdapter` (PyMuPDF)
- Content control mapping
- Basic output naming (project name based)
- NO `DocumentVersion` tracking (v2+)
- NO `NamingPattern` tokens (v2+)

### M10: Application Layer (Days 116-135)
**Scope**: Commands, queries, services

**Commands**:
- `CreateProjectCommand`
- `OpenProjectCommand`
- `SaveProjectCommand`
- `CloseProjectCommand`
- `UpdateFieldCommand`
- `SetFieldOverrideCommand`
- `GenerateDocumentCommand`
- NO import/export/clone (v2+)

**Queries**:
- `GetProjectQuery`
- `GetEntityFieldsQuery`
- `GetValidationResultQuery`
- NO `GetFieldHistoryQuery` (v2+)
- NO `GetAppTypesQuery` (v2+)

**Services**:
- `ValidationService`
- `FormulaService`
- `ControlService`
- `DocumentGenerationService`
- NO `AppTypeDiscoveryService` (v2+)
- NO `AutoSaveService` (v2+)

### M11: Presentation Layer (Days 136-175)
**Scope**: ViewModels, widgets, views

**ViewModels**:
- `WelcomeViewModel` (recent projects only)
- `ProjectViewModel`
- `EntityViewModel`
- `FieldViewModel` (per field type)
- `DocumentGenerationViewModel`
- NO `SearchViewModel` (v2+)
- NO `FieldHistoryViewModel` (v2+)

**Widgets**:
- All 12 field type widgets
- Entity navigation sidebar
- Field validation indicators

**Views**:
- Welcome view (recent projects list)
- Main project view
- Document generation dialog
- Pre-generation checklist (errors only)
- NO app type selection cards (v2+)
- NO search overlay (v2+)
- NO field history popover (v2+)

**Features**:
- Minimal keyboard shortcuts (Ctrl+S save, Ctrl+Z/Y undo/redo)
- Light theme only
- NO full keyboard navigation (v2+)
- NO dark mode (v2+)

### M12: Polish & Testing (Days 176-200)
**Scope**: Testing, documentation, bug fixes
- Integration tests for all workflows
- UI smoke tests
- Performance optimization
- User documentation
- NO `app_types/_template/` (v2+)
- NO app type creation guide (v2+)

---

## Sections to Remove/Reorganize

**Remove entirely**:
- ~~# Phase 5: Generalization to "Doc Helper"~~ (Section 27-35)
- ~~# Phase 6: Additional Features~~ (Section 36-40)

**Move to "Future Roadmap" section**:
- App Type bounded context design (from Phase 5)
- Manifest.json structure (from Phase 5)
- Extension architecture (from Phase 5)
- UX enhancements: dark mode, autosave, search, keyboard nav (from Phase 6)
- Data operations: import/export/clone (from Phase 6)
- Field history, document versioning (from Phase 6)

**Keep in main document**:
- Doc Helper naming (applied throughout)
- Core v1 architecture
- 12 milestones with v1 scope

---

## New ADR to Add

### ADR-013: Multi-Document-Type Platform Vision (DEFERRED)

**Status**: Proposed (for v2+)

**Context**: The application may eventually support multiple document types (soil investigation, structural reports, environmental assessments) without code duplication. Each type would have different schemas, templates, and potentially custom transformers.

**Decision**: Design v1 with extensibility in mind, but defer implementation:
- v1: Single app type (Soil Investigation) loaded directly
- v2+: Plugin-style architecture with app type discovery

**v2+ Vision**:
- Each document type is an "App Type" package in `app_types/`
- App Types define schema (config.db), templates, and optional extensions
- `manifest.json` declares capabilities and extension points
- `AppTypeDiscoveryService` scans and loads available types
- `ExtensionLoader` loads custom transformers per app type

**v1 Implementation**:
- `app_types/soil_investigation/` exists with config.db and templates
- Application loads this path directly (hardcoded)
- No manifest parsing, no discovery, no extension loading
- Clean interfaces allow v2+ to add these features

**Consequences**:
- (+) v1 ships faster with simpler codebase
- (+) Architecture supports future extension
- (+) No premature abstraction
- (-) v2 requires additional work for multi-type support

---

## Files to Modify
- `d:\Local Drive\Coding\soil_report\plan.md` - Complete restructure

## Execution Steps

### Phase A: Restructure Document
1. Add Project Identity section at top with Doc Helper naming
2. Update Features by Domain to show v1 scope only
3. Update folder structure to `doc_helper/` with v1 layout
4. Update domain entities (remove v2+ features from v1 scope)
5. Update application layer (v1 commands/queries/services only)
6. Update infrastructure layer (v1 repos/storage only)
7. Update presentation layer (v1 views/widgets only)

### Phase B: Update Milestones
8. Revise M2 - remove ValidationSeverity
9. Revise M3 - remove AppTypeInfo, manifest parsing
10. Revise M6 - remove FieldHistoryEntry, auto-save
11. Revise M8 - remove ExtensionLoader, FieldHistoryRepository, AutoSaveStorage
12. Revise M9 - remove DocumentVersion, NamingPattern tokens
13. Revise M10 - remove Import/Export/Clone, AppTypeDiscoveryService, AutoSaveService
14. Revise M11 - remove app type selection, search, dark mode, field history UI
15. Update M12 - focus on testing and polish only

### Phase C: Add Vision & Cleanup
16. Add ADR-013 (Multi-App-Type Vision - DEFERRED)
17. Create "Future Roadmap" section with v2+ features
18. Remove Phase 5 section entirely (Sections 27-35)
19. Remove Phase 6 section entirely (Sections 36-40)
20. Update architecture diagrams to show v1 scope
21. Final review: ensure v1/v2+ separation is clear throughout

## Verification

**v1 Scope Verification**:
- [ ] No manifest.json parsing in v1 milestones
- [ ] No AppTypeDiscoveryService in v1 milestones
- [ ] No ExtensionLoader in v1 milestones
- [ ] No dark mode, auto-save, search, field history in v1 milestones
- [ ] No import/export/clone commands in v1 milestones
- [ ] No ValidationSeverity in v1 milestones
- [ ] Welcome screen shows recent projects only (no app type cards)

**Document Structure Verification**:
- [ ] No "Phase 5" section header
- [ ] No "Phase 6" section header
- [ ] Doc Helper naming used throughout
- [ ] 12 milestones maintained
- [ ] "Future Roadmap" section exists with v2+ features
- [ ] ADR-013 present with DEFERRED status
- [ ] v1 Definition of Done is clear

**Domain Purity Verification**:
- [ ] Domain layer has no JSON parsing
- [ ] Domain layer has no filesystem access
- [ ] Domain layer has no timers/scheduling
- [ ] All I/O operations in Infrastructure layer

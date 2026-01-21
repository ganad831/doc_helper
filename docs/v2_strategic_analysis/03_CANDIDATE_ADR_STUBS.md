# DRAFT: Doc Helper v2 Candidate ADR Stubs

**Document Status**: DRAFT - Stubs Only (NOT Accepted)
**Date**: 2026-01-21
**Author**: Strategic Planning Agent
**Purpose**: Pre-draft ADR outlines for v2 features

---

## About This Document

This document contains **DRAFT ADR stubs** for potential v2 features. These are NOT accepted ADRs. They are pre-drafts to accelerate v2 planning when the time comes.

**Rules**:
- These stubs have NO authority until formally proposed and accepted
- Do NOT reference these in implementation work
- Do NOT use ADR numbers - they will be assigned when formalized
- Status is DRAFT for all stubs

---

## ADR-V2-001: App Type Discovery Service

**Status**: DRAFT

### Context

v1 loads schema from hardcoded `app_types/soil_investigation/config.db`. v2 needs to discover and load multiple app types dynamically.

### Decision (Proposed)

Implement `AppTypeDiscoveryService` that:
1. Scans `app_types/` directory for subdirectories
2. Parses `manifest.json` in each subdirectory
3. Validates manifest schema and required files
4. Registers discovered app types with `IAppTypeRegistry`

### Manifest Structure (Draft)

```json
{
  "id": "soil_investigation",
  "name": "Soil Investigation Report",
  "version": "1.0.0",
  "description": "Generate soil investigation reports",
  "icon": "icon.png",
  "schema": "config.db",
  "templates": {
    "word": ["templates/report.docx"],
    "excel": ["templates/data.xlsx"]
  },
  "extensions": {
    "transformers": ["extensions/geo_transformers.py"]
  }
}
```

### Consequences

- (+) Dynamic app type loading without code changes
- (+) Third-party app types possible
- (-) Manifest validation complexity
- (-) Extension security considerations

### Related ADRs (Existing)

- ADR-013 (Multi-Document-Type Platform Vision)
- ADR-012 (Registry-Based Factory)

---

## ADR-V2-002: Extension Loading Mechanism

**Status**: DRAFT

### Context

v2 app types may include custom transformers, validators, or other extensions. Need secure mechanism to load Python modules from app type packages.

### Decision (Proposed)

Implement `ExtensionLoader` service that:
1. Loads Python modules from app type `extensions/` directory
2. Validates extensions implement required interfaces
3. Registers extensions with appropriate registries
4. Sandboxes execution (allowed imports, no file system access)

### Extension Interface (Draft)

```python
# App type extension must implement
class ITransformerExtension(Protocol):
    """Extension providing custom transformers."""

    def get_transformers(self) -> list[tuple[str, ITransformer]]:
        """Return list of (name, transformer) pairs to register."""
        ...
```

### Security Considerations

- Extensions run in same process (no true sandbox)
- Limit imports to safe modules
- No network or filesystem access
- Audit trail for loaded extensions

### Consequences

- (+) Extensibility for domain-specific transformers
- (+) App types are self-contained
- (-) Security risk from arbitrary code execution
- (-) Debugging complexity

### Related ADRs (Existing)

- ADR-012 (Registry-Based Factory)
- ADR-013 (Multi-Document-Type Platform Vision)

---

## ADR-V2-003: Field Type Extensibility

**Status**: DRAFT

### Context

v1 has 12 frozen field types as enum. Custom app types may need domain-specific field types (e.g., coordinate picker for geology, material selector for structural).

### Decision (Proposed)

Two options under consideration:

**Option A: String-Based Field Types**
- Replace enum with string identifiers
- Registry-based validation
- Maximum flexibility, minimum type safety

**Option B: Extension Points in Existing Types**
- Keep 12 base types
- Add configuration extensions per type
- Less flexibility, better type safety

### Analysis

| Criterion | Option A | Option B |
|-----------|----------|----------|
| Type Safety | LOW | HIGH |
| Flexibility | HIGH | MEDIUM |
| Ripple Effect | HIGH | LOW |
| Testing Complexity | HIGH | LOW |
| v1 Compatibility | BREAKING | COMPATIBLE |

### Recommendation (Tentative)

Option B preferred - extend existing types rather than replace enum.

### Consequences

- Option A: Major refactor, high risk
- Option B: Incremental extension, lower risk

### Related ADRs (Existing)

- plan.md Section 2 (12 Field Types FROZEN)

---

## ADR-V2-004: Dark Mode Theme System

**Status**: DRAFT

### Context

v1 has light theme only. Users request dark mode for reduced eye strain.

### Decision (Proposed)

Implement `IThemeProvider` interface with:
1. `LightTheme` implementation (current)
2. `DarkTheme` implementation (new)
3. Theme switching via settings dialog
4. Persisted theme preference in user config

### Implementation Approach

- Qt stylesheets for theme application
- Theme-aware color constants
- Custom widgets must support both themes
- No forced reload on theme switch

### Consequences

- (+) User preference support
- (+) Reduced eye strain option
- (-) All custom widgets need theme support
- (-) Testing matrix doubles

### Related ADRs (Existing)

- ADR-005 (MVVM Pattern)

---

## ADR-V2-005: Auto-Save and Recovery

**Status**: DRAFT

### Context

v1 requires manual save. Users may lose work on crash. Need auto-save with recovery option.

### Decision (Proposed)

Implement `AutoSaveService` that:
1. Saves project state to temp location periodically (default: 60 seconds)
2. On crash, recovery file detected at next launch
3. User prompted to recover or discard
4. Recovery file deleted after successful recovery or explicit discard

### Recovery File Format

- Same as project.db but in temp directory
- Named: `{project_name}_recovery_{timestamp}.db`
- Contains full project state

### User Flow

```
Launch → Recovery file exists?
  ├─ No → Normal startup
  └─ Yes → Prompt: "Recover unsaved changes?"
           ├─ Recover → Load recovery file, delete original
           └─ Discard → Delete recovery file, load original
```

### Consequences

- (+) Data loss prevention
- (+) User confidence
- (-) Temp file management complexity
- (-) Potential for outdated recovery files

### Related ADRs (Existing)

- ADR-011 (Unit of Work) - for atomic saves

---

## ADR-V2-006: Document Version History

**Status**: DRAFT

### Context

v1 generates documents without tracking history. Users want to regenerate previous versions or compare outputs.

### Decision (Proposed)

Implement `DocumentHistoryService` that:
1. Records each generation with metadata
2. Stores: timestamp, template used, parameters, output hash
3. Enables regeneration from historical state (if project data allows)
4. Provides comparison between versions

### Domain Model Addition

```python
@dataclass(frozen=True)
class DocumentVersion:
    version_id: str
    project_id: str
    generated_at: datetime
    template_id: str
    template_version: str
    output_format: DocumentFormat
    output_hash: str  # SHA256 of generated file
    parameters: dict[str, Any]  # Generation parameters
```

### Storage

- New table in project.db: `document_versions`
- Output files stored with version suffix
- Configurable retention (default: last 10 versions)

### Consequences

- (+) Audit trail for documents
- (+) Regeneration capability
- (-) Storage growth
- (-) Complexity in version comparison

### Related ADRs (Existing)

- ADR-007 (Repository Pattern) - for history repository

---

## ADR-V2-007: Quick Search Architecture

**Status**: DRAFT (Note: ADR-026 implements basic search in v1)

### Context

ADR-026 implements basic field search. v2 may need enhanced search capabilities.

### Decision (Proposed)

Extend search capabilities:
1. Global search across all projects (optional)
2. Search history persistence
3. Advanced filters (by entity, field type, validation state)
4. Search result export

### Implementation Notes

- Build on ADR-026 foundation
- Add search index for cross-project search
- Keyboard shortcut: Ctrl+Shift+F for global search

### Consequences

- (+) Improved discoverability
- (+) Power user feature
- (-) Index maintenance overhead
- (-) Memory usage for large project collections

### Related ADRs (Existing)

- ADR-026 (Search Architecture) - v1 foundation

---

## ADR-V2-008: Keyboard Navigation Framework

**Status**: DRAFT

### Context

v1 has minimal keyboard shortcuts (Ctrl+S, Ctrl+Z/Y). Power users need comprehensive keyboard navigation.

### Decision (Proposed)

Implement `KeyboardNavigationAdapter` that:
1. Manages global shortcut registration
2. Tab-order navigation within forms
3. Entity switching via keyboard
4. Field jumping via shortcut

### Shortcut Map (Draft)

| Shortcut | Action |
|----------|--------|
| Ctrl+S | Save project |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+N | New project |
| Ctrl+O | Open project |
| Ctrl+Tab | Next entity |
| Ctrl+Shift+Tab | Previous entity |
| Ctrl+F | Search fields |
| Ctrl+G | Generate document |
| F1 | Help |
| Escape | Cancel/close dialog |

### Consequences

- (+) Accessibility improvement
- (+) Power user efficiency
- (-) Shortcut conflict management
- (-) Platform-specific handling (Mac vs Windows)

### Related ADRs (Existing)

- ADR-005 (MVVM Pattern)

---

## ADR-V2-009: Project Import/Export Enhancement

**Status**: DRAFT (Note: ADR-039 implements basic import/export in v1)

### Context

ADR-039 implements JSON interchange format. v2 may need enhanced import/export capabilities.

### Decision (Proposed)

Extend import/export:
1. Excel import for bulk data entry
2. CSV export for field values
3. Project cloning with transformation
4. Merge import (update existing vs create new)

### Considerations

- Schema validation on import
- Conflict resolution for merge
- Field mapping UI for Excel import

### Consequences

- (+) Data migration support
- (+) Bulk operations
- (-) Complex conflict handling
- (-) Excel format variations

### Related ADRs (Existing)

- ADR-039 (Import/Export Data Format) - v1 foundation

---

## ADR-V2-010: Multi-Language Translation Enhancement

**Status**: DRAFT

### Context

v1 supports English and Arabic. v2 may need additional languages and improved translation workflow.

### Decision (Proposed)

1. Add translation contributor workflow
2. Translation key validation (detect missing keys)
3. Fallback chain: Requested → English → Key name
4. App-type-specific translation namespaces

### Translation Key Namespacing

```json
{
  "common.save": "Save",
  "common.cancel": "Cancel",
  "soil.borehole_depth": "Borehole Depth",
  "structural.load_capacity": "Load Capacity"
}
```

### Consequences

- (+) Scalable to many languages
- (+) App-type-specific terminology
- (-) Translation management overhead
- (-) Key naming conventions enforcement

### Related ADRs (Existing)

- plan.md Section 3.12 (Internationalization)

---

## Summary Table

| Stub ID | Title | v2 Priority | Complexity | Dependencies |
|---------|-------|-------------|------------|--------------|
| V2-001 | App Type Discovery | P1 | HIGH | ADR-013 |
| V2-002 | Extension Loading | P1 | HIGH | V2-001 |
| V2-003 | Field Type Extensibility | P2 | HIGH | V2-001 |
| V2-004 | Dark Mode | P3 | MEDIUM | None |
| V2-005 | Auto-Save | P2 | MEDIUM | ADR-011 |
| V2-006 | Document History | P3 | MEDIUM | ADR-007 |
| V2-007 | Enhanced Search | P3 | LOW | ADR-026 |
| V2-008 | Keyboard Navigation | P3 | LOW | ADR-005 |
| V2-009 | Import/Export Enhancement | P3 | MEDIUM | ADR-039 |
| V2-010 | Multi-Language Enhancement | P4 | LOW | v1 i18n |

---

## Next Steps (When v2 Work Begins)

1. Prioritize based on business requirements
2. Convert relevant stubs to formal ADR proposals
3. Assign ADR numbers
4. Follow unfreeze process for any frozen ADR modifications
5. Update AGENT_RULES.md Section 14 with new frozen ADRs

---

*These are DRAFT stubs for planning purposes only. They have no authority until formally accepted.*

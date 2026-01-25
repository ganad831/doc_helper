# DRAFT: Doc Helper v2 Architectural Pressure Points Analysis

**Document Status**: DRAFT - Analysis Only
**Date**: 2026-01-21
**Author**: Strategic Planning Agent
**Purpose**: Identify v1 architecture areas under pressure from growth

---

## Executive Summary

This analysis identifies architectural "pressure points" - areas in the v1 implementation where the current design may experience strain as the system evolves toward v2 capabilities. These are NOT recommendations for change; they are objective observations to inform v2 planning.

---

## 1. Schema Context Pressure Points

### 1.1 Hardcoded App Type Path (LOW PRESSURE)

**Location**: [infrastructure/persistence/sqlite/repositories/schema_repository.py](../../src/doc_helper/infrastructure/persistence/sqlite/repositories/schema_repository.py)

> **Historical Note (2026-01-25)**: This analysis originally referenced `sqlite_schema_repository.py`. As of Phase M-3, the authoritative schema repository is `sqlite/repositories/schema_repository.py`. The legacy file is deprecated.

**Current State**: Schema loads from `app_types/soil_investigation/config.db` via hardcoded path.

**v2 Pressure**:
- Multi-app-type requires dynamic path resolution
- App type discovery needs manifest.json parsing
- Schema versioning needs to be per-app-type

**Observation**: The `ISchemaRepository` interface is clean; only implementation needs adaptation.

**Pressure Level**: LOW - Clean interface means implementation swap is straightforward.

---

### 1.2 FieldType Enum Extensibility (MEDIUM PRESSURE)

**Location**: [domain/schema/field_type.py](../../src/doc_helper/domain/schema/field_type.py)

**Current State**: 12 field types defined as frozen enum (TEXT, TEXTAREA, NUMBER, DATE, DROPDOWN, CHECKBOX, RADIO, CALCULATED, LOOKUP, FILE, IMAGE, TABLE).

**v2 Pressure**:
- Custom app types may need custom field types
- Plugin-based field type registration would require enum extension or alternative pattern
- Validators and widgets are registered against this fixed enum

**Observation**: Enum approach ensures type safety but limits extensibility. Alternative: string-based type IDs with registry validation.

**Pressure Level**: MEDIUM - Fundamental data model change would ripple through all layers.

---

## 2. Validation Context Pressure Points

### 2.1 Validator Registration (LOW PRESSURE)

**Location**: [domain/validation/validators.py](../../src/doc_helper/domain/validation/validators.py)

**Current State**: Validators for all 12 field types implemented. Registry pattern used.

**v2 Pressure**:
- Custom field types need custom validators
- App-type-specific validation rules beyond current constraints

**Observation**: Registry pattern (ADR-012) already supports dynamic registration.

**Pressure Level**: LOW - Architecture already supports extension.

---

### 2.2 Severity Levels (RESOLVED)

**Location**: [domain/validation/severity.py](../../src/doc_helper/domain/validation/severity.py)

**Current State**: Three severity levels (ERROR, WARNING, INFO) implemented per ADR-025.

**v2 Pressure**: None identified. Current implementation is sufficient.

**Pressure Level**: RESOLVED - ADR-025 implementation is complete and extensible.

---

## 3. Transformer Context Pressure Points

### 3.1 Transformer Discovery (MEDIUM PRESSURE)

**Location**: [domain/document/transformers.py](../../src/doc_helper/domain/document/transformers.py), [domain/document/transformer_registry.py](../../src/doc_helper/domain/document/transformer_registry.py)

**Current State**: 15+ built-in transformers with registry-based lookup.

**v2 Pressure**:
- App types may need custom transformers (geological, structural, environmental)
- Extension loading mechanism needed for Python modules in app type packages
- Transformer registration per app type context

**Observation**: Registry pattern exists but lacks dynamic loading capability. Need `ExtensionLoader` service.

**Pressure Level**: MEDIUM - Registry exists but no extension loading infrastructure.

---

## 4. Project Context Pressure Points

### 4.1 Project-to-AppType Association (MEDIUM PRESSURE)

**Location**: [domain/project/project.py](../../src/doc_helper/domain/project/project.py)

**Current State**: Project has no explicit app_type_id field. v1 assumes all projects are Soil Investigation.

**v2 Pressure**:
- Projects must store which app type they belong to
- Project opening must load correct schema
- Recent projects must show app type badge

**Observation**: Adding `app_type_id: str` field to Project is low-impact but requires migration.

**Pressure Level**: MEDIUM - Schema change to existing aggregate.

---

### 4.2 Field History Scope (LOW PRESSURE)

**Location**: [infrastructure/persistence/sqlite_field_history_repository.py](../../src/doc_helper/infrastructure/persistence/sqlite_field_history_repository.py)

**Current State**: Field history tracked per project. ADR-027 implemented.

**v2 Pressure**: None identified for multi-app-type. History is project-scoped, not app-type-scoped.

**Pressure Level**: LOW - Current implementation scales to v2.

---

## 5. Infrastructure Pressure Points

### 5.1 DI Container Scoping (LOW PRESSURE)

**Location**: [infrastructure/di/container.py](../../src/doc_helper/infrastructure/di/container.py)

**Current State**: Singleton, Scoped (per-project), and Transient lifetimes supported.

**v2 Pressure**:
- App type context may need per-app-type scoping
- Extension services need scoped registration

**Observation**: Current scoping model can extend to per-app-type context.

**Pressure Level**: LOW - Architecture supports extension.

---

### 5.2 Translation Files (LOW PRESSURE)

**Location**: [translations/](../../translations/)

**Current State**: Global `en.json` and `ar.json` for all UI strings.

**v2 Pressure**:
- App types may have domain-specific terminology
- Need app-type-specific translation overrides or namespacing

**Observation**: Could use translation key namespacing: `soil.field_name` vs `structural.field_name`.

**Pressure Level**: LOW - Additive change, not breaking.

---

## 6. Presentation Layer Pressure Points

### 6.1 Widget Factory Registration (MEDIUM PRESSURE)

**Location**: [presentation/factories/field_widget_factory.py](../../src/doc_helper/presentation/factories/field_widget_factory.py)

**Current State**: Fixed registration of 12 field type widgets.

**v2 Pressure**:
- Custom field types need custom widgets
- Extension-provided widgets require dynamic registration
- Widget factory must be app-type-aware

**Observation**: Factory pattern exists but registration is static. Need registration API.

**Pressure Level**: MEDIUM - Requires factory redesign for dynamic registration.

---

### 6.2 Welcome View App Type Selection (HIGH PRESSURE)

**Location**: [presentation/views/welcome_view.py](../../src/doc_helper/presentation/views/welcome_view.py)

**Current State**: Shows recent projects list only. No app type selection UI.

**v2 Pressure**:
- Need app type card grid (icon, name, description)
- Selection flow before project creation
- App type discovery must feed this UI

**Observation**: v2 requires substantial welcome screen redesign. Current UI is v1-only.

**Pressure Level**: HIGH - Significant UI addition required.

---

### 6.3 Settings Dialog (LOW PRESSURE)

**Location**: [presentation/dialogs/settings_dialog.py](../../src/doc_helper/presentation/dialogs/settings_dialog.py)

**Current State**: Language selection only.

**v2 Pressure**:
- Dark mode theme toggle
- Auto-save settings
- Default app type preference

**Observation**: Additive changes to existing dialog.

**Pressure Level**: LOW - Extension of existing UI.

---

## 7. Document Generation Pressure Points

### 7.1 Template Discovery (MEDIUM PRESSURE)

**Location**: [infrastructure/document/](../../src/doc_helper/infrastructure/document/)

**Current State**: Templates loaded from `app_types/soil_investigation/templates/`.

**v2 Pressure**:
- Per-app-type template directories
- Template metadata (name, description, default flag) from manifest
- Template validation per app type schema

**Observation**: Path handling needs generalization but adapter interfaces are clean.

**Pressure Level**: MEDIUM - Path and discovery changes needed.

---

### 7.2 Document Version History (NOT IMPLEMENTED)

**Current State**: Not implemented (explicitly v2+).

**v2 Pressure**:
- Track generation history per project
- Store template version, timestamp, parameters
- Enable regeneration from historical state

**Observation**: New domain context required (`domain/document_history/`).

**Pressure Level**: N/A - New feature, not pressure on existing code.

---

## 8. Cross-Cutting Pressure Points

### 8.1 Event Bus Scalability (LOW PRESSURE)

**Location**: [infrastructure/events/](../../src/doc_helper/infrastructure/events/)

**Current State**: In-memory event bus for domain events.

**v2 Pressure**:
- More event types as features grow
- Extension-provided event handlers

**Observation**: Current in-memory bus scales adequately. No async persistence needed for v2.

**Pressure Level**: LOW - Architecture is sufficient.

---

### 8.2 Unit of Work Scope (LOW PRESSURE)

**Location**: [infrastructure/persistence/sqlite_base.py](../../src/doc_helper/infrastructure/persistence/sqlite_base.py)

**Current State**: SQLite-based Unit of Work per operation.

**v2 Pressure**:
- Multi-database operations (project.db + config.db)
- Transaction coordination across databases

**Observation**: SQLite limitations exist but are acceptable for desktop app.

**Pressure Level**: LOW - Desktop-appropriate design.

---

## Pressure Summary Matrix

| Area | Pressure Point | Level | v2 Impact | Notes |
|------|---------------|-------|-----------|-------|
| Schema | Hardcoded path | LOW | Path generalization | Interface clean |
| Schema | FieldType enum | MEDIUM | Extensibility model | Ripple effect risk |
| Validation | Validators | LOW | Registry extension | Already extensible |
| Transformer | Discovery | MEDIUM | Extension loading | New infrastructure needed |
| Project | App type ID | MEDIUM | Schema migration | Aggregate change |
| DI | Scoping | LOW | Per-app-type scope | Additive |
| Presentation | Widget factory | MEDIUM | Dynamic registration | Pattern exists, API needed |
| Presentation | Welcome view | HIGH | Complete redesign | New feature set |
| Document | Templates | MEDIUM | Path generalization | Adapters clean |

---

## Conclusion

**Overall Assessment**: The v1 architecture is well-designed for extension. Most pressure points are LOW or MEDIUM intensity. The primary HIGH-pressure area is the Welcome View UI redesign for app type selection.

**Key Observations**:
1. Repository interfaces (ADR-007) insulate domain from infrastructure changes
2. Registry pattern (ADR-012) provides extension points
3. DTO-only MVVM (ADR-020) isolates presentation from domain changes
4. Main challenges are in discovery infrastructure and UI expansion

**Recommendation**: The identified pressure points can be addressed incrementally in v2 without architectural overhaul. The frozen ADRs (Section 14, AGENT_RULES.md) provide a stable foundation.

---

*This document is for analysis purposes only. No code changes are proposed or authorized.*

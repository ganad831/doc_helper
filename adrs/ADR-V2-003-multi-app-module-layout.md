# ADR-V2-003: Multi-App Module Layout and Dependency Rules

**Status**: Draft
**Date**: 2026-01-21
**Category**: v2 Platform Architecture
**Deciders**: Project Lead
**Governance**: See [AGENT_RULES.md](../AGENT_RULES.md) Section 16

---

## Context

The v1 Doc Helper has a monolithic package structure:

```
src/doc_helper/
├── domain/
├── application/
├── infrastructure/
└── presentation/
```

This structure implicitly assumes a single AppType. With the Platform-AppType boundary (ADR-V2-001) and AppType configuration model (ADR-V2-002), we need to define:

1. **Physical module layout**: Where do Platform and AppType packages live?
2. **Dependency rules**: What can import what?
3. **Shared code**: How do AppTypes reuse common domain logic?
4. **Clean Architecture preservation**: How do new modules respect existing layers?

Without explicit rules:
- Cross-AppType imports could create coupling
- Platform could depend on specific AppType internals
- Clean Architecture layers could be violated
- Code organization could become inconsistent

---

## Decision

### 1. Physical Module Layout

```
src/doc_helper/
│
├── domain/                        # SHARED DOMAIN (unchanged)
│   ├── common/                    # Base classes, value objects
│   ├── schema/                    # Schema entities (shared)
│   ├── project/                   # Project entities (shared)
│   ├── validation/                # Validation (shared)
│   ├── formula/                   # Formula (shared)
│   ├── control/                   # Control (shared)
│   ├── override/                  # Override (shared)
│   ├── document/                  # Document (shared)
│   ├── transformer/               # Transformer (shared)
│   └── file/                      # File (shared)
│
├── application/                   # SHARED APPLICATION (unchanged)
│   ├── commands/
│   ├── queries/
│   ├── services/
│   ├── dto/
│   └── events/
│
├── infrastructure/                # SHARED INFRASTRUCTURE (unchanged)
│   ├── persistence/
│   ├── filesystem/
│   ├── documents/
│   └── events/
│
├── presentation/                  # SHARED PRESENTATION (mostly unchanged)
│   ├── viewmodels/
│   ├── views/
│   ├── widgets/
│   └── dialogs/
│
├── platform/                      # NEW: PLATFORM HOST
│   ├── __init__.py
│   ├── discovery/                 # AppType discovery
│   │   ├── __init__.py
│   │   ├── app_type_discovery_service.py
│   │   └── manifest_parser.py
│   ├── registry/                  # AppType registry
│   │   ├── __init__.py
│   │   ├── app_type_registry.py
│   │   └── interfaces.py
│   ├── routing/                   # Request routing to AppTypes
│   │   ├── __init__.py
│   │   └── app_type_router.py
│   └── composition/               # v2 composition root
│       ├── __init__.py
│       └── platform_container.py
│
└── app_types/                     # NEW: APPTYPE MODULES
    │
    ├── __init__.py                # AppType package marker
    │
    ├── contracts/                 # SHARED CONTRACTS
    │   ├── __init__.py
    │   ├── i_app_type.py          # IAppType interface
    │   ├── i_platform_services.py # IPlatformServices interface
    │   └── app_type_metadata.py   # AppTypeMetadata value object
    │
    └── soil_investigation/        # FIRST APPTYPE (extracted from v1)
        ├── __init__.py            # Implements IAppType
        ├── manifest.json          # AppType manifest
        ├── config.db              # Schema database (moved)
        ├── templates/             # Document templates (moved)
        │   ├── report.docx
        │   └── data.xlsx
        ├── extensions/            # Custom transformers
        │   └── geo_transformers.py
        └── resources/             # AppType-specific resources
            └── icon.png
```

### 2. Dependency Rules

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY RULES                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   platform/                                                              │
│       ├── MAY import: domain/, application/, app_types/contracts/       │
│       ├── MUST NOT import: infrastructure/, presentation/               │
│       └── MUST NOT import: app_types/{specific_apptype}/                │
│                                                                          │
│   app_types/contracts/                                                   │
│       ├── MAY import: domain/common/                                    │
│       └── MUST NOT import: anything else                                │
│                                                                          │
│   app_types/{apptype}/                                                   │
│       ├── MAY import: domain/, application/, app_types/contracts/       │
│       ├── MAY import: infrastructure/ (for repository implementations)  │
│       └── MUST NOT import: other app_types/{other}/, platform/          │
│                                                                          │
│   presentation/                                                          │
│       ├── MAY import: application/dto/, platform/registry/ (read-only)  │
│       └── MUST NOT import: domain/, infrastructure/, app_types/         │
│                                                                          │
│   CRITICAL FORBIDDEN:                                                    │
│       ❌ app_types/soil_investigation → app_types/other_apptype         │
│       ❌ platform/ → app_types/soil_investigation/ (internals)          │
│       ❌ presentation/ → domain/                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Dependency Rule Enforcement

The existing architectural compliance scan (ADR-024) will be extended:

```python
# New rules added to check_architecture.py

PLATFORM_FORBIDDEN_IMPORTS = [
    "doc_helper.infrastructure",
    "doc_helper.presentation",
    "doc_helper.app_types.soil_investigation",  # No specific AppType
]

APPTYPE_FORBIDDEN_IMPORTS = {
    "soil_investigation": [
        "doc_helper.app_types.other_apptype",  # No cross-AppType
        "doc_helper.platform",  # AppTypes don't import Platform
    ]
}
```

### 4. Shared vs AppType-Specific Code

| Code Location | Ownership | Can Be Extended |
|--------------|-----------|-----------------|
| `domain/` | Shared Platform | No (v1 baseline) |
| `application/` | Shared Platform | No (v1 baseline) |
| `infrastructure/` | Shared Platform | Yes (new adapters) |
| `presentation/` | Shared Platform | Yes (new views) |
| `platform/` | Platform Host | Yes (v2 work) |
| `app_types/contracts/` | Shared | No (stable contracts) |
| `app_types/{apptype}/` | Specific AppType | Yes (isolated) |

### 5. Interface Locations

| Interface | Location | Rationale |
|-----------|----------|-----------|
| `IAppType` | `app_types/contracts/` | Contract between Platform and AppTypes |
| `IPlatformServices` | `app_types/contracts/` | Services Platform provides to AppTypes |
| `AppTypeMetadata` | `app_types/contracts/` | Shared value object |
| `IAppTypeRegistry` | `platform/registry/` | Platform-internal interface |
| `IAppTypeDiscovery` | `platform/discovery/` | Platform-internal interface |

---

## Options Considered

### Option A: Flat Structure with Prefixes
```
src/doc_helper/
├── platform_discovery/
├── platform_registry/
├── apptype_soil_investigation/
└── apptype_contracts/
```
- **Pros**: No nesting
- **Cons**: Messy with many AppTypes, hard to find related code
- **Rejected**: Poor organization at scale

### Option B: Nested Structure (Selected)
```
src/doc_helper/
├── platform/
│   ├── discovery/
│   └── registry/
└── app_types/
    ├── contracts/
    └── soil_investigation/
```
- **Pros**: Clear hierarchy, related code together
- **Cons**: Deeper paths
- **Selected**: Better organization and discoverability

### Option C: External AppTypes
```
doc_helper/                   # Core package
app_types/                    # Separate package
├── soil_investigation/
└── other_apptype/
```
- **Pros**: Clear separation, independent versioning
- **Cons**: Complex deployment, testing across packages
- **Rejected**: Over-engineering for current needs

---

## Consequences

### Positive

1. **Clear Organization**: Platform and AppType code clearly separated
2. **Enforceable Rules**: Dependency rules can be checked automatically
3. **Isolation**: AppTypes cannot accidentally couple to each other
4. **Scalability**: Structure supports many AppTypes
5. **Clean Architecture Preserved**: Existing layer rules still apply

### Negative

1. **More Directories**: Deeper package hierarchy
2. **Import Paths**: Longer import statements
3. **Refactoring Effort**: Moving existing code to new locations

### Neutral

1. **Learning Curve**: Developers must understand new structure
2. **IDE Support**: Some IDEs may need reconfiguration

---

## Implementation Plan

### Phase 1: Create Directory Structure
1. Create `src/doc_helper/platform/` package with subdirectories
2. Create `src/doc_helper/app_types/` package with subdirectories
3. Create `src/doc_helper/app_types/contracts/` with interfaces
4. Add `__init__.py` files throughout

### Phase 2: Define Contracts
1. Create `IAppType` interface in `app_types/contracts/`
2. Create `IPlatformServices` interface in `app_types/contracts/`
3. Create `AppTypeMetadata` value object in `app_types/contracts/`
4. Document contract stability guarantees

### Phase 3: Extract Soil Investigation AppType
1. Move `app_types/soil_investigation/config.db` (already exists, verify location)
2. Move templates to `app_types/soil_investigation/templates/`
3. Create `app_types/soil_investigation/__init__.py` implementing `IAppType`
4. Create `app_types/soil_investigation/manifest.json`

### Phase 4: Implement Platform Services
1. Implement `AppTypeDiscoveryService` in `platform/discovery/`
2. Implement `AppTypeRegistry` in `platform/registry/`
3. Implement `AppTypeRouter` in `platform/routing/`
4. Create new composition root in `platform/composition/`

### Phase 5: Update Compliance Scanning
1. Add new dependency rules to `check_architecture.py`
2. Test scanning catches cross-AppType imports
3. Test scanning catches Platform-to-specific-AppType imports
4. Integrate into CI

---

## Non-Goals

This ADR does NOT address:

1. **Runtime module loading**: Static imports only
2. **AppType hot-swapping**: Restart required for AppType changes
3. **AppType isolation via subprocesses**: Same process model
4. **Namespace packages**: Standard Python packages only
5. **AppType dependency management**: Shared dependencies only

---

## Migration Plan

### Existing Code Migration

1. **No v1 Code Movement in Phase 1**
   - Platform/AppType structure created alongside existing code
   - v1 code continues working unchanged

2. **Gradual Extraction**
   - Soil Investigation AppType created incrementally
   - Each component moved with corresponding tests
   - Original location deprecated, then removed

3. **Compliance Validation**
   - Run architectural scan after each migration step
   - All existing tests must pass
   - New dependency rules enforced

### Import Path Migration

1. **Aliases for Backward Compatibility**
   - Old import paths work during transition
   - Deprecation warnings logged
   - Old paths removed after full migration

2. **Example**:
   ```python
   # Old (deprecated)
   from doc_helper.infrastructure.persistence import SchemaRepository

   # New (after migration)
   from doc_helper.app_types.soil_investigation import SoilInvestigationAppType
   # SchemaRepository accessed via AppType interface
   ```

---

## Related ADRs

- **ADR-V2-001**: Platform AppType Boundary and Host Contract
- **ADR-V2-002**: AppType Configuration and Project Identity Model
- **ADR-002**: Clean Architecture with DDD (layer rules preserved)
- **ADR-003**: Framework-Independent Domain (domain stays pure)
- **ADR-024**: Architectural Compliance Scanning (extended for v2)

---

## v1 Impact Assessment

**v1 Behavior Changes**: NONE
- All v1 functionality remains unchanged
- Existing import paths work during transition

**v1 Code Changes**: LOCATION ONLY
- Code moves to new locations
- Functionality unchanged
- Tests updated for new paths

**v1 Tests**: MUST PASS
- All existing tests continue passing
- New tests added for Platform/AppType interaction
- No test behavior changes

---

*This ADR is DRAFT status. Implementation requires explicit authorization per AGENT_RULES.md Section 16.*

# Doc Helper v2 Platform Implementation Plan

**Document Status**: AUTHORIZED
**Date**: 2026-01-21
**Objective**: Multi-App Support (Multi-AppType Platform)
**Governance**: See [AGENT_RULES.md](AGENT_RULES.md) Section 16

---

## Executive Summary

This document defines the implementation plan for transforming Doc Helper from a single-AppType application into a Multi-AppType Platform. The plan consists of four phases, each with clear deliverables and success criteria.

**Key Principle**: v1 behavior remains locked. All changes are additive or restructuring only.

---

## Prerequisites

Before implementation begins, ensure:

1. **v2 ADRs Accepted**
   - [ ] ADR-V2-001: Platform AppType Boundary and Host Contract
   - [ ] ADR-V2-002: AppType Configuration and Project Identity Model
   - [ ] ADR-V2-003: Multi-App Module Layout and Dependency Rules

2. **v1 Baseline Verified**
   - [ ] All 1,400+ tests passing
   - [ ] Zero architectural violations (ADR-024 scan)
   - [ ] Documentation up to date

3. **Governance Understood**
   - [ ] AGENT_RULES.md Section 16 read and understood
   - [ ] v1 behavior lock acknowledged
   - [ ] Clean Architecture constraints acknowledged

---

## Phase 1: Platform Host + AppType Registry

**Objective**: Create platform infrastructure without a second AppType. Existing v1 continues working.

**Duration Estimate**: 2-3 weeks

### Deliverables

1. **Directory Structure Creation**
   ```
   src/doc_helper/
   ├── platform/
   │   ├── __init__.py
   │   ├── discovery/
   │   │   ├── __init__.py
   │   │   ├── app_type_discovery_service.py
   │   │   └── manifest_parser.py
   │   ├── registry/
   │   │   ├── __init__.py
   │   │   ├── app_type_registry.py
   │   │   └── interfaces.py
   │   ├── routing/
   │   │   ├── __init__.py
   │   │   └── app_type_router.py
   │   └── composition/
   │       ├── __init__.py
   │       └── platform_container.py
   └── app_types/
       ├── __init__.py
       └── contracts/
           ├── __init__.py
           ├── i_app_type.py
           ├── i_platform_services.py
           └── app_type_metadata.py
   ```

2. **Contract Interfaces**
   - `IAppType` protocol defining AppType module contract
   - `IPlatformServices` protocol defining Platform-provided services
   - `AppTypeMetadata` immutable value object

3. **Platform Services**
   - `ManifestParser`: Parse and validate `manifest.json` files
   - `AppTypeDiscoveryService`: Scan `app_types/` for valid AppTypes
   - `AppTypeRegistry`: Register and query available AppTypes
   - `AppTypeRouter`: Route operations to appropriate AppType

4. **Manifest Validation**
   - JSON Schema for manifest validation
   - Validation error reporting
   - Required vs optional field enforcement

### Success Criteria

- [ ] Platform package structure created
- [ ] Contract interfaces defined and documented
- [ ] ManifestParser can parse valid manifests
- [ ] ManifestParser rejects invalid manifests with clear errors
- [ ] AppTypeDiscoveryService finds no AppTypes (soil_investigation not yet migrated)
- [ ] All existing v1 tests still pass
- [ ] Architectural scan passes (new rules added)
- [ ] No v1 behavior changed

### Tests Required

- Unit tests for ManifestParser (valid/invalid manifests)
- Unit tests for AppTypeRegistry (registration, lookup)
- Unit tests for AppTypeDiscoveryService (empty directory, invalid directories)
- Integration test: Platform startup with empty app_types/

---

## Phase 2: Extract v1 as First AppType

**Objective**: Restructure Soil Investigation into an AppType module without changing behavior.

**Duration Estimate**: 3-4 weeks

### Deliverables

1. **Soil Investigation AppType Module**
   ```
   src/doc_helper/app_types/
   └── soil_investigation/
       ├── __init__.py           # Implements IAppType
       ├── manifest.json         # AppType manifest
       ├── config.db             # Schema database (existing)
       ├── templates/            # Document templates (existing)
       │   ├── report.docx
       │   └── data.xlsx
       ├── extensions/           # Custom transformers (if any)
       └── resources/
           └── icon.png
   ```

2. **Manifest File**
   ```json
   {
     "id": "soil_investigation",
     "name": "Soil Investigation Report",
     "version": "1.0.0",
     "description": "Generate professional soil investigation reports",
     "icon": "resources/icon.png",
     "schema": {
       "source": "config.db",
       "type": "sqlite"
     },
     "templates": {
       "word": ["templates/report.docx"],
       "excel": ["templates/data.xlsx"],
       "default": "templates/report.docx"
     },
     "capabilities": {
       "supports_pdf_export": true,
       "supports_excel_export": true,
       "supports_word_export": true
     }
   }
   ```

3. **IAppType Implementation**
   - `SoilInvestigationAppType` class implementing `IAppType`
   - Returns existing repositories through interface
   - Registers existing transformers

4. **Project Database Migration**
   - Add `app_type_id` column to project metadata
   - Default value: `'soil_investigation'`
   - Migration runs automatically on project open

5. **Updated Composition Root**
   - New composition root uses Platform to discover AppType
   - Falls back to direct instantiation if Platform fails (robustness)

### Success Criteria

- [ ] Soil Investigation AppType module created
- [ ] manifest.json validates successfully
- [ ] SoilInvestigationAppType implements IAppType
- [ ] AppTypeDiscoveryService discovers soil_investigation
- [ ] Project database schema extended with app_type_id
- [ ] Existing projects migrated to have app_type_id
- [ ] Application starts and functions identically to v1
- [ ] All existing v1 tests still pass
- [ ] No v1 behavior changed

### Tests Required

- Unit tests for SoilInvestigationAppType
- Integration test: Discovery finds soil_investigation
- Integration test: Project open with migration
- Integration test: Full workflow through Platform routing
- Regression tests: All existing functionality

---

## Phase 3: Add Second AppType (Proof of Isolation)

**Objective**: Create a minimal stub AppType to prove the platform supports multiple AppTypes.

**Duration Estimate**: 1-2 weeks

### Deliverables

1. **Test Report AppType Module** (Minimal Stub)
   ```
   src/doc_helper/app_types/
   └── test_report/
       ├── __init__.py           # Implements IAppType
       ├── manifest.json
       ├── config.db             # Minimal schema (2-3 fields)
       └── templates/
           └── test_report.docx  # Simple template
   ```

2. **Minimal Schema**
   - 1 entity: `report_info` (singleton)
   - 3 fields: `title` (TEXT), `date` (DATE), `summary` (TEXTAREA)
   - No formulas, no controls, no overrides

3. **Simple Template**
   - Word document with 3 content controls
   - Basic formatting only

4. **Isolation Verification**
   - Create project with test_report AppType
   - Verify soil_investigation projects unchanged
   - Verify no cross-AppType imports in codebase

### Success Criteria

- [ ] test_report AppType module created
- [ ] test_report manifest validates
- [ ] AppTypeDiscoveryService finds both AppTypes
- [ ] Can create new project with test_report AppType
- [ ] Can open existing soil_investigation project
- [ ] Cannot open test_report project with soil_investigation (and vice versa)
- [ ] No imports between soil_investigation and test_report
- [ ] All existing v1 tests still pass
- [ ] No v1 behavior changed

### Tests Required

- Unit tests for TestReportAppType
- Integration test: Discovery finds both AppTypes
- Integration test: Create project with each AppType
- Integration test: Open project validates AppType match
- Isolation test: Static analysis confirms no cross-imports

---

## Phase 4: UI Updates for AppType Switching

**Objective**: Update Welcome screen to show AppType selection and update project navigation.

**Duration Estimate**: 2-3 weeks

### Deliverables

1. **Welcome View Updates**
   - Display available AppTypes as cards/list
   - Show AppType icon, name, description
   - "Create New Project" shows AppType selection first
   - Recent projects show AppType badge

2. **AppType Selection Dialog**
   - Grid or list of available AppTypes
   - Icon, name, description per AppType
   - Select to proceed to project creation

3. **Project View Updates**
   - Show current AppType in window title or status bar
   - AppType-aware navigation state

4. **ViewModels**
   - `WelcomeViewModel` extended with AppType list
   - `AppTypeSelectionViewModel` for selection dialog
   - `ProjectViewModel` extended with AppType context

### Success Criteria

- [ ] Welcome screen shows available AppTypes
- [ ] New project flow includes AppType selection
- [ ] Recent projects show AppType association
- [ ] Cannot create project without selecting AppType
- [ ] Window title/status shows current AppType
- [ ] All existing v1 tests still pass
- [ ] UI tests for new components
- [ ] No v1 behavior changed (except explicit AppType selection)

### Tests Required

- Unit tests for WelcomeViewModel AppType features
- Unit tests for AppTypeSelectionViewModel
- Integration test: Full project creation flow with AppType selection
- UI smoke tests: AppType cards display correctly
- UI smoke tests: Recent projects with AppType badges

---

## Implementation Rules

### v1 Protection (MANDATORY)

Every phase MUST comply with:

1. **No v1 Behavior Changes**
   - Existing functionality works identically
   - Test suite passes without modification
   - User workflows unchanged (except explicit AppType selection in Phase 4)

2. **Clean Architecture Compliance**
   - Domain layer remains framework-independent
   - DTO-only MVVM maintained
   - Layer dependencies respected

3. **Architectural Scan**
   - Run `check_architecture.py` after every change
   - Zero violations required
   - New rules for Platform/AppType added in Phase 1

### Change Verification

Before completing any phase:

```bash
# Run full test suite
.venv/Scripts/python -m pytest tests/ -v

# Run architectural compliance scan
.venv/Scripts/python scripts/check_architecture.py

# Verify test count hasn't decreased
# (new tests added, none removed)
```

### Rollback Strategy

If issues discovered:

1. **Phase 1**: Remove platform/ directory, revert to v1 composition
2. **Phase 2**: Keep soil_investigation in original location, don't use AppType routing
3. **Phase 3**: Remove test_report AppType, continue with single AppType
4. **Phase 4**: Revert Welcome view, use direct project creation

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking v1 tests | Low | High | Run full suite after each change |
| Cross-AppType coupling | Medium | High | Static analysis in CI |
| Migration data loss | Low | High | Backup before migration, test with copy |
| Performance regression | Low | Medium | Profile startup with multiple AppTypes |
| UI confusion | Medium | Low | User testing, clear AppType labels |

---

## Dependencies Between Phases

```
Phase 1 (Platform Infrastructure)
    │
    ▼
Phase 2 (Extract Soil Investigation)
    │
    ├──────────────────┐
    ▼                  ▼
Phase 3 (Add Second)   Phase 4 (UI Updates)
    │                  │
    └──────────────────┘
            │
            ▼
      v2 Platform Complete
```

- Phase 2 depends on Phase 1 completion
- Phase 3 and Phase 4 can run in parallel after Phase 2
- Both Phase 3 and Phase 4 required for v2 Platform completion

---

## Documentation Updates Required

After each phase, update:

1. **AGENT_RULES.md**: Mark phase complete in Section 16
2. **CONTINUOUS_TECHNICAL_ROADMAP.md**: Update Section 5.1 status
3. **ADR_INDEX.md**: Update v2 ADR status (Draft → Accepted → Implemented)
4. **This document**: Mark phase deliverables complete

---

## Acceptance Criteria (v2 Platform Complete)

The v2 Platform implementation is complete when:

- [ ] All four phases completed
- [ ] Two AppTypes functional (soil_investigation + test_report)
- [ ] Welcome screen shows AppType selection
- [ ] Projects correctly associated with AppTypes
- [ ] No cross-AppType dependencies
- [ ] All v1 tests pass
- [ ] New tests for Platform/AppType functionality
- [ ] Documentation updated
- [ ] Architectural scan passes

---

## Post-v2 Considerations

After v2 Platform is complete, consider:

1. **Additional AppTypes**: Add real second AppType (e.g., Structural Report)
2. **Extension Loading**: Custom transformers from AppType packages
3. **AppType SDK**: Documentation for creating new AppTypes
4. **Performance Optimization**: Lazy loading for many AppTypes

These are OUT OF SCOPE for v2 Platform implementation.

---

## Related Documents

- [AGENT_RULES.md](AGENT_RULES.md) - Section 16: v2 Platform Work Rules
- [ADR-V2-001](adrs/ADR-V2-001-platform-apptype-boundary.md) - Platform AppType Boundary
- [ADR-V2-002](adrs/ADR-V2-002-apptype-configuration-project-identity.md) - AppType Configuration
- [ADR-V2-003](adrs/ADR-V2-003-multi-app-module-layout.md) - Module Layout
- [CONTINUOUS_TECHNICAL_ROADMAP.md](CONTINUOUS_TECHNICAL_ROADMAP.md) - Section 5.1

---

*This implementation plan is AUTHORIZED per AGENT_RULES.md Section 16. Implementation requires following all v1 protection rules and governance.*

# ADR-V2-001: Platform AppType Boundary and Host Contract

**Status**: Draft
**Date**: 2026-01-21
**Category**: v2 Platform Architecture
**Deciders**: Project Lead
**Governance**: See [AGENT_RULES.md](../AGENT_RULES.md) Section 16

---

## Context

Doc Helper v1 is a document generation application built for a single document type (Soil Investigation Reports). The v1 architecture implicitly couples the application to this single AppType through:

1. **Hardcoded schema path**: `app_types/soil_investigation/config.db`
2. **Fixed template location**: `app_types/soil_investigation/templates/`
3. **Implicit AppType assumption**: No concept of AppType identity in project metadata
4. **Monolithic composition root**: All services wired for single AppType

The v2 vision (from ADR-013) is to transform Doc Helper into a **Multi-AppType Platform** that supports multiple document types without code modification. This requires a clear architectural boundary between:

- **Platform Host**: The application shell that discovers, loads, and coordinates AppTypes
- **AppType Modules**: Self-contained packages that implement domain-specific document generation

Without a well-defined boundary contract, we risk:
- Tight coupling between Platform and AppTypes
- Inability to add new AppTypes without code changes
- Cross-AppType dependencies that violate Clean Architecture
- Difficulty testing Platform and AppTypes in isolation

---

## Decision

We will establish a **Platform-AppType Boundary** with explicit contracts defining:

### 1. Platform Host Responsibilities

The Platform Host owns:
- **AppType Discovery**: Scanning `app_types/` directory for valid AppType packages
- **AppType Lifecycle**: Loading, initializing, and unloading AppType modules
- **AppType Registry**: Maintaining a registry of available AppTypes
- **Routing**: Directing requests to the appropriate AppType based on project identity
- **Shared Infrastructure**: Providing cross-cutting services (persistence, events, i18n)
- **Welcome UI**: Displaying available AppTypes and recent projects

### 2. AppType Module Responsibilities

Each AppType module owns:
- **Schema Definition**: Entities, fields, validation rules, formulas, controls
- **Templates**: Word/Excel/PDF templates for document generation
- **Transformers**: Custom transformers specific to the document domain
- **AppType Metadata**: Name, description, icon, version information

### 3. Platform-AppType Contract (Interfaces)

```python
# Platform provides to AppTypes
class IPlatformServices(Protocol):
    """Services provided by Platform to AppType modules."""

    @property
    def event_bus(self) -> IEventBus: ...

    @property
    def unit_of_work_factory(self) -> Callable[[], IUnitOfWork]: ...

    @property
    def translation_service(self) -> ITranslationService: ...

    @property
    def transformer_registry(self) -> ITransformerRegistry: ...

# AppTypes implement for Platform
class IAppType(Protocol):
    """Contract that all AppType modules must implement."""

    @property
    def app_type_id(self) -> str:
        """Unique identifier for this AppType."""
        ...

    @property
    def metadata(self) -> AppTypeMetadata:
        """Display metadata (name, description, icon, version)."""
        ...

    def get_schema_repository(self) -> ISchemaRepository:
        """Return schema repository for this AppType."""
        ...

    def get_template_repository(self) -> ITemplateRepository:
        """Return template repository for this AppType."""
        ...

    def register_transformers(self, registry: ITransformerRegistry) -> None:
        """Register AppType-specific transformers."""
        ...

    def initialize(self, platform_services: IPlatformServices) -> None:
        """Initialize AppType with platform services."""
        ...
```

### 4. Dependency Direction

```
Platform Host
    ├── Depends on: IAppType (interface)
    ├── Provides: IPlatformServices
    └── DOES NOT depend on: Any specific AppType implementation

AppType Module
    ├── Implements: IAppType
    ├── Receives: IPlatformServices
    └── DOES NOT depend on: Other AppType modules
```

---

## Options Considered

### Option A: Plugin Architecture with Dynamic Loading
- Load AppTypes as separate Python packages at runtime
- Full isolation with separate virtual environments
- **Pros**: Maximum isolation, versioning per AppType
- **Cons**: Complex deployment, slow startup, debugging difficulty
- **Rejected**: Over-engineering for current needs

### Option B: Monorepo with Internal Packages (Selected)
- AppTypes as internal packages within single codebase
- Static discovery at application startup
- **Pros**: Simple deployment, fast startup, easy debugging
- **Cons**: Less isolation, shared dependency versions
- **Selected**: Appropriate complexity for v2 scope

### Option C: Configuration-Driven without Contracts
- AppTypes defined purely by configuration/manifest
- No Python code in AppType packages
- **Pros**: Simplest approach, no code loading
- **Cons**: Cannot support custom transformers, limited extensibility
- **Rejected**: Insufficient for domain-specific needs

---

## Consequences

### Positive

1. **Clear Boundaries**: Platform and AppTypes have explicit responsibilities
2. **Testability**: Platform can be tested with mock AppTypes, AppTypes with mock Platform
3. **Extensibility**: New AppTypes can be added without modifying Platform code
4. **Maintainability**: Changes to one AppType don't affect others
5. **Clean Architecture Compliance**: Boundary respects existing layer rules

### Negative

1. **Interface Overhead**: Requires defining and maintaining contracts
2. **Indirection**: Some operations require crossing the boundary
3. **Complexity**: More moving parts than monolithic approach
4. **Migration Effort**: v1 code must be restructured into AppType module

### Neutral

1. **Discovery Mechanism**: Must implement AppType discovery service
2. **Testing Strategy**: Need integration tests for Platform-AppType interaction

---

## Implementation Plan

### Phase 1: Define Interfaces (No Code Changes)
1. Define `IAppType` interface in domain layer
2. Define `IPlatformServices` interface in domain layer
3. Define `AppTypeMetadata` value object
4. Document interface contracts

### Phase 2: Extract v1 as First AppType
1. Create `doc_helper.app_types.soil_investigation` package
2. Implement `IAppType` for Soil Investigation
3. Move schema/template loading to AppType module
4. Wire existing services through `IPlatformServices`

### Phase 3: Platform Host Implementation
1. Create `doc_helper.platform` package
2. Implement `AppTypeDiscoveryService`
3. Implement `AppTypeRegistry`
4. Create new composition root that loads AppTypes

### Phase 4: Validate with Second AppType
1. Create minimal stub AppType (e.g., "Test Report")
2. Verify Platform correctly loads both AppTypes
3. Verify no cross-AppType dependencies

---

## Non-Goals

This ADR does NOT address:

1. **Dynamic loading at runtime**: AppTypes are discovered at startup only
2. **AppType versioning/updates**: Version management is out of scope
3. **AppType marketplace/distribution**: No external AppType support
4. **Security sandboxing**: AppTypes run in same process with full trust
5. **Cross-AppType data sharing**: Each AppType's data is isolated
6. **UI customization per AppType**: AppTypes use standard field widgets

---

## Migration Plan

### From v1 to v2 Platform

1. **v1 Projects Compatibility**
   - Existing projects will automatically associate with `soil_investigation` AppType
   - Project database schema unchanged (new `app_type_id` column added with default)
   - No migration wizard required

2. **Code Migration**
   - v1 domain/application code remains unchanged
   - Infrastructure code restructured around Platform/AppType boundary
   - Presentation layer updated for AppType-aware navigation

3. **Rollback Strategy**
   - v2 code can run in "single AppType mode" (legacy behavior)
   - If issues found, revert to single composition root

---

## Related ADRs

- **ADR-013**: Multi-Document-Type Platform Vision (proposed vision, this ADR implements it)
- **ADR-002**: Clean Architecture with DDD (boundary must respect layers)
- **ADR-003**: Framework-Independent Domain (interfaces in domain layer)
- **ADR-012**: Registry-Based Factory (transformer registry pattern)
- **ADR-V2-002**: AppType Configuration and Project Identity Model
- **ADR-V2-003**: Multi-App Module Layout and Dependency Rules

---

## v1 Impact Assessment

**v1 Behavior Changes**: NONE
- All v1 functionality remains unchanged
- Default AppType is `soil_investigation`
- Projects without explicit AppType use default

**v1 Code Changes**: RESTRUCTURE ONLY
- Code moves between modules, functionality unchanged
- Existing tests must pass without modification
- New tests for Platform-AppType interaction

---

*This ADR is DRAFT status. Implementation requires explicit authorization per AGENT_RULES.md Section 16.*

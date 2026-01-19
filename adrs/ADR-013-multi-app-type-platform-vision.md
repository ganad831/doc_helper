# ADR-013: Multi-Document-Type Platform Vision (DEFERRED)

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

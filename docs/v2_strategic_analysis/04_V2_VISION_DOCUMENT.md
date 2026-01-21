# DRAFT: Doc Helper v2 Vision Document

**Document Status**: DRAFT - Strategic Vision Only
**Date**: 2026-01-21
**Author**: Strategic Planning Agent
**Purpose**: Concise vision for Doc Helper v2 evolution

---

## 1. Vision Statement

**Doc Helper v2** transforms the application from a single-purpose Soil Investigation report generator into a **universal document generation platform** that supports multiple document types through a plugin-style architecture while preserving the architectural rigor and clean boundaries established in v1.

---

## 2. v1 Foundation Summary

Doc Helper v1 delivers:
- **12 field types** with validation, formulas, and controls
- **Clean Architecture** with strict layer separation
- **DTO-only MVVM** for presentation isolation
- **Command-based undo** with state machine overrides
- **Word/Excel/PDF generation** with 15+ transformers
- **i18n support** (English/Arabic with RTL)
- **Field history and search** capabilities
- **Import/export** via JSON interchange format

**v1 Success Criteria Met**:
- 1,400+ tests passing
- Zero domain imports in presentation layer
- All frozen ADRs (21 total) fully implemented
- Legacy parity achieved

---

## 3. v2 Strategic Goals

### Goal 1: Multi-App-Type Platform

**Objective**: Support multiple document types without code modification.

**Approach**:
- Each document type is an "App Type" package
- App Types discovered at runtime from `app_types/` directory
- Manifest-driven configuration (schema, templates, extensions)
- Welcome screen presents app type selection

**Key Components**:
- `AppTypeDiscoveryService` - scans and validates app types
- `IAppTypeRegistry` - manages loaded app types
- `manifest.json` - declares app type capabilities

**User Impact**: Users can install new document types by dropping app type packages into the `app_types/` folder.

---

### Goal 2: Extensibility Framework

**Objective**: Enable domain-specific customizations per app type.

**Approach**:
- Extension loading for custom transformers
- Registry-based integration with existing patterns
- Secure execution within defined boundaries

**Key Components**:
- `ExtensionLoader` - loads Python modules from app type packages
- Extension interfaces for transformers (and potentially validators, widgets)
- Security constraints on extension execution

**User Impact**: App type developers can include custom logic for domain-specific transformations.

---

### Goal 3: Enhanced User Experience

**Objective**: Improve usability for power users and accessibility.

**Approach**:
- Dark mode theme support
- Auto-save with recovery
- Comprehensive keyboard navigation
- Document version history

**Key Components**:
- `IThemeProvider` with light/dark implementations
- `AutoSaveService` with recovery flow
- `KeyboardNavigationAdapter` for shortcut management
- `DocumentHistoryService` for version tracking

**User Impact**: Users gain productivity features expected in modern applications.

---

### Goal 4: Platform Maturity

**Objective**: Prepare for broader adoption and ecosystem growth.

**Approach**:
- Enhanced import/export (Excel mapping, merge support)
- Multi-language expansion beyond English/Arabic
- App type contribution guidelines
- Performance optimization for large projects

**User Impact**: Platform becomes suitable for enterprise deployment and third-party contributions.

---

## 4. Architectural Continuity

### What Remains Frozen

The following v1 architectural decisions carry forward unchanged:

| ADR | Decision | v2 Status |
|-----|----------|-----------|
| ADR-002 | Clean Architecture + DDD | FROZEN |
| ADR-003 | Framework-Independent Domain | FROZEN |
| ADR-004 | CQRS Pattern | FROZEN |
| ADR-005 | MVVM Pattern | FROZEN |
| ADR-007 | Repository Pattern | FROZEN |
| ADR-008 | Result Monad | FROZEN |
| ADR-009 | Strongly Typed IDs | FROZEN |
| ADR-010 | Immutable Value Objects | FROZEN |
| ADR-017 | Command-Based Undo | FROZEN |
| ADR-020 | DTO-Only MVVM | FROZEN |
| ADR-021 | UndoState DTO Isolation | FROZEN |

### What May Evolve

| Area | v1 State | v2 Evolution |
|------|----------|--------------|
| ADR-013 | Proposed | Accepted with implementation |
| Schema loading | Hardcoded path | Discovery service |
| Transformer registry | Built-in only | Extensions supported |
| Welcome view | Recent projects | App type selection |
| Field types | 12 frozen | Extensibility mechanism TBD |
| Themes | Light only | Light + Dark |

---

## 5. Implementation Phases

### Phase 2.0: Multi-App-Type Core (Foundation)

**Scope**:
- App type discovery service
- Manifest parsing and validation
- Welcome screen redesign
- Project-to-app-type association

**Estimated Effort**: 8-12 weeks

**Success Criteria**:
- Second app type loads without code changes
- App type selection UI functional
- Existing Soil Investigation projects continue working

---

### Phase 2.1: Extension Framework

**Scope**:
- Extension loader service
- Transformer extension interface
- Security boundary implementation
- Extension documentation

**Estimated Effort**: 6-8 weeks

**Success Criteria**:
- Custom transformer loads from app type package
- Extension security constraints enforced
- Developer documentation available

---

### Phase 2.2: UX Enhancements

**Scope**:
- Dark mode implementation
- Auto-save with recovery
- Keyboard navigation framework
- Document version history

**Estimated Effort**: 8-10 weeks

**Success Criteria**:
- Theme switching without restart
- Recovery prompts after crash
- Full keyboard operability
- Document history viewable

---

### Phase 2.3: Platform Maturity

**Scope**:
- Enhanced import/export
- Additional languages
- Performance optimization
- App type contribution tooling

**Estimated Effort**: 6-8 weeks

**Success Criteria**:
- Excel import functional
- 3+ languages supported
- Large project performance acceptable
- App type template available

---

## 6. Risk Assessment

### High Risk

| Risk | Mitigation |
|------|------------|
| Extension security vulnerabilities | Strict interface constraints, no filesystem/network access |
| Field type extensibility ripple effects | Option B approach (extend, don't replace) |
| Multi-app-type complexity | Incremental rollout, extensive testing |

### Medium Risk

| Risk | Mitigation |
|------|------------|
| Theme support in custom widgets | Widget testing matrix, style guidelines |
| Performance with large app type count | Lazy loading, caching |
| Migration path for v1 projects | Automatic migration, backward compatibility |

### Low Risk

| Risk | Mitigation |
|------|------------|
| Auto-save file corruption | Transactional saves, validation on recovery |
| Keyboard shortcut conflicts | Platform-aware defaults, user customization |
| Translation key growth | Namespacing, validation tooling |

---

## 7. Success Metrics

### Quantitative

| Metric | Target |
|--------|--------|
| App types supported | 3+ (Soil, Structural, Environmental) |
| Test coverage maintained | >85% domain, >75% application |
| Performance (project load) | <3 seconds |
| Auto-save recovery success | >99% |

### Qualitative

| Metric | Target |
|--------|--------|
| User satisfaction | Positive feedback on extensibility |
| Developer adoption | At least 1 third-party app type |
| Maintainability | Clean architecture preserved |

---

## 8. Non-Goals for v2

The following are explicitly **NOT** in scope for v2:

- **Cloud/SaaS deployment** - remains desktop application
- **Real-time collaboration** - single-user paradigm
- **Mobile application** - desktop only
- **AI-assisted content generation** - manual data entry focus
- **Version control integration** - file-based projects
- **Enterprise authentication** - local file access

---

## 9. Timeline Overview

```
2026 Q1: v1 Complete (current)
         │
2026 Q2: v2.0 Multi-App-Type Core
         │ App type discovery
         │ Welcome screen redesign
         │ Second app type validation
         │
2026 Q3: v2.1 Extension Framework
         │ Extension loader
         │ Security implementation
         │ Developer documentation
         │
2026 Q4: v2.2 UX Enhancements
         │ Dark mode
         │ Auto-save
         │ Keyboard navigation
         │
2027 Q1: v2.3 Platform Maturity
         │ Enhanced import/export
         │ Performance optimization
         │ App type tooling
         │
2027 Q2: v2 Complete
```

---

## 10. Decision Authority

### Requires No Approval

- Implementation within existing ADR boundaries
- Performance optimization
- Bug fixes
- Documentation improvements

### Requires Team Review

- New ADR proposals
- v2 phase scope adjustments
- Timeline changes

### Requires Project Lead Approval

- Modifications to frozen ADRs (per AGENT_RULES.md Section 14)
- Scope additions beyond v2 vision
- Resource allocation changes

---

## 11. Relationship to v1 Documentation

| Document | Role in v2 |
|----------|------------|
| [plan.md](../../plan.md) | v1 scope remains authoritative |
| [AGENT_RULES.md](../../AGENT_RULES.md) | Execution rules extended for v2 |
| [unified_upgrade_plan_FINAL.md](../../unified_upgrade_plan_FINAL.md) | v1 reference only |
| [ADR-013](../../adrs/ADR-013-multi-app-type-platform-vision.md) | Promoted to Accepted in v2 |
| This document | v2 strategic vision |

---

## 12. Conclusion

Doc Helper v2 builds on the solid architectural foundation of v1 to deliver a universal document generation platform. The clean architecture, DTO-only MVVM, and command-based undo patterns ensure that v2 extensions integrate cleanly without compromising maintainability.

The phased approach allows incremental delivery of value while managing risk. Multi-app-type support is the cornerstone feature, with extensibility framework and UX enhancements following.

Success depends on maintaining architectural discipline while embracing controlled expansion.

---

*This document is a DRAFT vision statement. It does not authorize any implementation work. v2 work begins only after explicit project lead approval.*

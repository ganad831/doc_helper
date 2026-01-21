# DRAFT: Doc Helper v2 Architecture Unfreeze Triggers

**Document Status**: DRAFT - Analysis Only
**Date**: 2026-01-21
**Author**: Strategic Planning Agent
**Purpose**: Define objective criteria for when architecture freeze should be reconsidered

---

## Purpose

This document defines **objective, measurable triggers** that would indicate the need to reconsider the current architecture freeze (AGENT_RULES.md Section 14). These are NOT recommendations to unfreeze; they are criteria for future evaluation.

---

## 1. Trigger Categories

### Category A: Business Requirement Triggers
Triggers driven by new product requirements that cannot be met within frozen architecture.

### Category B: Technical Debt Triggers
Triggers driven by accumulating complexity or maintainability concerns.

### Category C: Performance Triggers
Triggers driven by system performance degradation.

### Category D: Ecosystem Triggers
Triggers driven by external dependencies or technology shifts.

---

## 2. Category A: Business Requirement Triggers

### A1: Multi-App-Type Demand

**Trigger**: User requests or business decisions require supporting a second document type.

**Measurement**:
- Customer request documented
- Business case approved
- Timeline committed

**Frozen ADRs Affected**:
- ADR-013 (status change from Proposed to Accepted)

**Decision Path**:
1. Evaluate if v1 architecture supports the new type via configuration only
2. If code changes required, evaluate scope against ADR-013 vision
3. If ADR-013 vision is insufficient, propose ADR modifications
4. Obtain project lead authorization per AGENT_RULES.md Section 14

---

### A2: Custom Field Type Requirement

**Trigger**: A new app type requires a field type not in the frozen 12.

**Measurement**:
- Field type specification documented
- Cannot be implemented via existing 12 types
- Business justification provided

**Frozen ADRs Affected**:
- plan.md Section 2 (12 Field Types FROZEN)
- May require new ADR for field type extensibility

**Decision Path**:
1. Verify field cannot be composed from existing types
2. Document the new field type specification
3. Propose ADR for field type extensibility mechanism
4. Evaluate ripple effects (validators, widgets, transformers)

---

### A3: Plugin/Extension Requirement

**Trigger**: Third-party or customer-developed extensions needed.

**Measurement**:
- Extension use case documented
- Security review requirements defined
- API stability requirements specified

**Frozen ADRs Affected**:
- ADR-012 (Registry-Based Factory) - may need extension API
- ADR-013 - ExtensionLoader concept

**Decision Path**:
1. Define extension API scope (transformers only? validators? widgets?)
2. Document security model for extension execution
3. Propose ADR for extension loading mechanism

---

## 3. Category B: Technical Debt Triggers

### B1: Test Coverage Degradation

**Trigger**: Test coverage drops below acceptable thresholds.

**Measurement**:
- Domain layer: <85% coverage (current: ~90%)
- Application layer: <75% coverage (current: ~80%)
- Integration tests: <10 critical path tests failing

**Frozen ADRs Affected**:
- ADR-024 (Architectural Compliance Scanning)

**Decision Path**:
1. Identify coverage gaps
2. Add tests without architectural changes
3. If architecture prevents testability, document specific blocker
4. Propose minimal ADR modification to enable testing

---

### B2: Circular Dependency Detection

**Trigger**: Static analysis detects circular imports between layers.

**Measurement**:
- Any import cycle between domain/application/infrastructure/presentation
- Detected by linter or import checker

**Frozen ADRs Affected**:
- ADR-002 (Clean Architecture + DDD)
- ADR-003 (Framework-Independent Domain)

**Decision Path**:
1. Document the cycle with full import chain
2. Identify which file violates layer boundaries
3. Fix without ADR change if possible (usually a misplaced file)
4. If structural issue, propose ADR clarification

---

### B3: DTO Proliferation

**Trigger**: DTO count exceeds maintainable threshold.

**Measurement**:
- >50 DTOs in application/dto/
- >30% of DTOs have >10 fields
- DTO maintenance becomes primary development cost

**Frozen ADRs Affected**:
- ADR-020 (DTO-Only MVVM)
- ADR-021 (UndoState DTO Isolation)

**Decision Path**:
1. Audit DTOs for redundancy
2. Consider DTO inheritance/composition (allowed within ADR-020)
3. If fundamental issue, propose DTO consolidation strategy
4. Never relax DTO-only rule - find efficiency within constraints

---

### B4: God Object Emergence

**Trigger**: Any class exceeds anti-pattern thresholds.

**Measurement**:
- Lines of code: >500 LOC per class
- Methods: >15 public methods per class
- Dependencies: >7 constructor parameters

**Frozen ADRs Affected**:
- Anti-pattern checklist Section 16.1.2

**Decision Path**:
1. Identify the bloated class
2. Extract concerns into focused classes
3. Typically does not require ADR changes
4. If architectural pattern causes bloat, document for review

---

## 4. Category C: Performance Triggers

### C1: Formula Evaluation Bottleneck

**Trigger**: Formula computation time exceeds acceptable threshold.

**Measurement**:
- Single formula evaluation: >100ms
- Full project formula cascade: >2 seconds
- User-perceived lag on field edit

**Frozen ADRs Affected**:
- None directly - performance optimization allowed per AGENT_RULES.md Section 14

**Decision Path**:
1. Profile formula evaluation
2. Optimize within current architecture (caching, lazy evaluation)
3. If architectural constraint causes issue, document specific blocker
4. Performance optimization typically does not require ADR change

---

### C2: Database Query Degradation

**Trigger**: Database operations exceed acceptable thresholds.

**Measurement**:
- Project load time: >3 seconds
- Field save time: >500ms
- Memory usage: >500MB for single project

**Frozen ADRs Affected**:
- ADR-007 (Repository Pattern)
- ADR-011 (Unit of Work)

**Decision Path**:
1. Profile database operations
2. Add indexes, optimize queries
3. Consider caching within repository implementation
4. If repository interface prevents optimization, propose interface extension

---

### C3: UI Rendering Performance

**Trigger**: UI responsiveness degrades below acceptable threshold.

**Measurement**:
- Tab switch: >500ms
- Field render: >100ms
- Validation indicator update: >50ms

**Frozen ADRs Affected**:
- ADR-005 (MVVM Pattern)

**Decision Path**:
1. Profile UI rendering
2. Optimize ViewModel property change notifications
3. Consider virtualization for large field lists
4. Typically addressable within current MVVM pattern

---

## 5. Category D: Ecosystem Triggers

### D1: PyQt6 Major Version Change

**Trigger**: PyQt6 releases breaking changes or is deprecated.

**Measurement**:
- PyQt6 deprecation announcement
- Security vulnerability without patch
- Python version incompatibility

**Frozen ADRs Affected**:
- ADR-003 (Framework-Independent Domain) - domain unaffected
- ADR-005 (MVVM Pattern) - presentation impact

**Decision Path**:
1. Evaluate migration path (PyQt7, PySide6, etc.)
2. Domain layer should require zero changes (ADR-003 validation)
3. Presentation layer migration
4. ADR-003 should prevent cascade - validate this

---

### D2: Python Version Deprecation

**Trigger**: Target Python version reaches end-of-life.

**Measurement**:
- Python 3.x EOL announcement
- Dependency incompatibility
- Security vulnerabilities

**Frozen ADRs Affected**:
- None directly - Python version is infrastructure concern

**Decision Path**:
1. Test on new Python version
2. Update pyproject.toml dependencies
3. Fix any compatibility issues
4. Typically no ADR changes needed

---

### D3: Document Library Deprecation

**Trigger**: python-docx, xlwings, or PyMuPDF becomes unmaintained.

**Measurement**:
- No releases for >12 months
- Critical bugs unpatched
- Security vulnerabilities

**Frozen ADRs Affected**:
- Infrastructure layer adapters only

**Decision Path**:
1. Identify replacement library
2. Implement new adapter behind existing interface
3. ADR-007 repository/adapter pattern should isolate change
4. No domain changes required

---

## 6. Trigger Evaluation Process

### Step 1: Trigger Detection

```
[ ] Trigger condition observed
[ ] Measurement criteria documented
[ ] Evidence collected
```

### Step 2: Impact Assessment

```
[ ] Affected ADRs identified
[ ] Scope of change estimated
[ ] Risk assessment completed
```

### Step 3: Decision Path Selection

```
[ ] Can be resolved within frozen architecture?
    → Proceed without unfreeze
[ ] Requires ADR modification?
    → Follow unfreeze process (AGENT_RULES.md Section 14)
```

### Step 4: Unfreeze Request (if needed)

```
[ ] Formal proposal documented
[ ] Impact analysis completed
[ ] Project lead authorization obtained
[ ] Freeze status updated in AGENT_RULES.md
```

---

## 7. Trigger Priority Matrix

| Trigger ID | Category | Likelihood | Impact | Priority |
|------------|----------|------------|--------|----------|
| A1 | Business | HIGH | HIGH | P1 |
| A2 | Business | MEDIUM | HIGH | P2 |
| A3 | Business | LOW | MEDIUM | P3 |
| B1 | Tech Debt | LOW | MEDIUM | P3 |
| B2 | Tech Debt | LOW | HIGH | P2 |
| B3 | Tech Debt | MEDIUM | MEDIUM | P2 |
| B4 | Tech Debt | MEDIUM | MEDIUM | P2 |
| C1 | Performance | LOW | LOW | P4 |
| C2 | Performance | LOW | MEDIUM | P3 |
| C3 | Performance | LOW | LOW | P4 |
| D1 | Ecosystem | LOW | HIGH | P2 |
| D2 | Ecosystem | MEDIUM | LOW | P3 |
| D3 | Ecosystem | LOW | MEDIUM | P3 |

**Priority Legend**:
- P1: Immediate evaluation required
- P2: Evaluate within next planning cycle
- P3: Monitor and evaluate as needed
- P4: Low concern, standard maintenance

---

## 8. Current Status

**As of 2026-01-21**:

| Trigger | Status | Notes |
|---------|--------|-------|
| A1 (Multi-App-Type) | NOT TRIGGERED | No second app type requested |
| A2 (Custom Field Type) | NOT TRIGGERED | 12 types sufficient |
| A3 (Plugin Requirement) | NOT TRIGGERED | No extension requests |
| B1 (Test Coverage) | NOT TRIGGERED | Coverage above thresholds |
| B2 (Circular Deps) | NOT TRIGGERED | Clean layer boundaries |
| B3 (DTO Proliferation) | MONITORING | ~20 DTOs, within threshold |
| B4 (God Object) | NOT TRIGGERED | No classes exceed limits |
| C1-C3 (Performance) | NOT TRIGGERED | Performance acceptable |
| D1-D3 (Ecosystem) | NOT TRIGGERED | Dependencies stable |

---

## Conclusion

The architecture freeze (AGENT_RULES.md Section 14) remains valid. No triggers are currently activated that would require reconsidering the frozen ADRs.

The most likely future trigger is **A1 (Multi-App-Type Demand)**, which aligns with the deferred ADR-013 vision. When this trigger activates, the v2 strategic documents should guide the unfreeze evaluation.

---

*This document is for planning purposes only. No architecture changes are proposed or authorized.*

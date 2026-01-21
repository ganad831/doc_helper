# ADR-025: Validation Severity Levels

**Status**: Accepted

**Context**:

The current validation system treats all validation failures as equivalent. Every validation issue, regardless of severity or consequence, is recorded identically with no mechanism to distinguish critical problems from advisory information.

This uniform treatment creates several architectural problems:

### 1. Binary Pass/Fail Limitation

The validation system returns a binary result: valid or invalid. No distinction exists between:
- **Blocking conditions**: Requirements that prevent document generation
- **Advisory conditions**: Recommendations that merit user attention but allow continuation
- **Informational conditions**: Suggestions or best practices with no workflow impact

All validation failures currently block document generation equally.

### 2. Inadequate User Decision Support

Users receive validation feedback without context about severity. A missing required field and an optional field with an unusual value appear identical in validation results. Users cannot assess which issues demand immediate attention versus which allow informed decisions to proceed.

The pre-generation workflow presents all validation issues in a flat list with no prioritization or categorization, forcing users to treat every issue as equally critical.

### 3. Inflexible Workflow Control

Document generation follows a rigid rule: any validation failure prevents generation. No mechanism exists to:
- Require resolution of critical errors while allowing warnings
- Enable user acknowledgment of advisory issues before proceeding
- Present informational guidance without blocking workflows

This rigidity prevents users from making informed risk decisions about document generation.

### 4. Absence of Severity in Domain Model

The domain model lacks a concept of validation severity. All validation failures are modeled identically, with no property distinguishing their impact on workflows or their importance to data quality.

Validation constraints have no way to declare their severity characteristics. A constraint checking required field presence and a constraint validating optional field ranges are architecturally indistinguishable.

**Decision**:

Introduce validation severity as a first-class architectural concept with three distinct levels:

### 1. Severity Levels

**ERROR**: Represents critical validation failures that must be resolved before document generation. Blocks all generation workflows unconditionally.

**WARNING**: Represents advisory validation issues that merit user review but do not prevent document generation. Allows workflow continuation after explicit user acknowledgment.

**INFO**: Represents informational guidance with no workflow impact. Presented to users but never blocks or requires acknowledgment.

### 2. Architectural Rules

**Severity is Explicit**: Every validation failure carries an explicit severity designation. No inference or runtime determination of severity.

**ERROR Blocks Workflows**: The presence of any ERROR-severity validation failure unconditionally prevents document generation until resolved.

**WARNING Allows Continuation**: WARNING-severity failures enable workflow continuation after explicit user confirmation. Users acknowledge awareness and accept responsibility for proceeding.

**INFO Never Blocks**: INFO-severity notifications have zero workflow impact. Presentation for user awareness only.

**Domain Declares Severity**: Validation constraints declare their default severity as part of their domain semantics. Schema configuration may override default severity for specific fields.

**Presentation Consumes Severity**: Severity is exposed to the presentation layer exclusively through data transfer objects. The presentation layer interprets severity for visual representation and workflow control, but severity semantics are defined in the domain.

**Backward Compatibility**: Existing validation constraints default to ERROR severity, preserving current blocking behavior.

### 3. Layer Responsibilities

**Domain Layer**: Defines severity as an immutable value object. Validation constraints declare default severity. Validation results contain severity-annotated failures. Domain validation logic remains severity-agnostic beyond designation.

**Application Layer**: Workflow orchestration interprets severity for generation control. Determines whether validation results block workflows based on severity presence. Maps domain severity to data transfer objects for presentation consumption.

**Presentation Layer**: Receives severity via data transfer objects only. Interprets severity for visual differentiation and user interaction. Never imports domain severity concepts directly.

**Alternatives Considered**:

### Alternative 1: Maintain Single Severity (Status Quo)
All validation failures treated identically. Rejected: Too rigid for user needs, poor user experience, prevents informed decision-making.

### Alternative 2: Boolean Blocking Flag
Add a simple boolean flag indicating whether validation failure blocks workflows. Rejected: Only two levels (blocking/non-blocking), insufficient granularity, doesn't distinguish warnings from informational guidance.

### Alternative 3: Numeric Priority Scale
Use numeric severity (1-10 scale) to rank validation importance. Rejected: Arbitrary scale with unclear semantics, difficult to map to workflow rules, no standardized interpretation.

### Alternative 4: Extensible Severity System
Allow custom severity levels beyond ERROR/WARNING/INFO. Rejected: Over-engineering for current needs, three levels sufficient for foreseeable requirements, added complexity without clear benefit.

**Consequences**:

**Positive**:

- (+) **Improved Decision Support**: Users distinguish critical errors from advisory warnings at a glance, enabling informed decisions about document generation
- (+) **Flexible Workflow Control**: ERROR blocks unconditionally, WARNING allows continuation with confirmation, INFO never blocks
- (+) **Clear Semantic Model**: Three universally understood levels with explicit workflow implications
- (+) **Domain Semantic Richness**: Validation constraints express their severity characteristics as part of domain modeling
- (+) **Backward Compatible**: Existing constraints default to ERROR, preserving current behavior
- (+) **Schema Control**: Per-field severity overrides enable fine-tuning without code changes
- (+) **Architectural Compliance**: Severity exposed via DTOs maintains DTO-Only MVVM pattern, preserves Clean Architecture boundaries

**Costs**:

- (-) **Domain Model Expansion**: Validation value objects require additional severity property
- (-) **Breaking Change**: Validation result structure changes, requiring updates throughout application layer
- (-) **Increased Complexity**: Validation results need severity-aware query methods
- (-) **Migration Effort**: All validation constraint instantiations must specify severity
- (-) **Testing Scope**: Validation tests must cover all severity combinations and workflow implications
- (-) **Presentation Complexity**: User interfaces must interpret and represent three severity levels distinctly

**Mitigation**:

- Severity defaults to ERROR for all existing constraints during migration
- Domain migration occurs before application layer changes
- Comprehensive test coverage added before migration begins
- Presentation layer changes isolated behind data transfer object boundary

**Non-Goals**:

This decision does NOT address:

- **Severity-based filtering or search**: Deferred to presentation layer design
- **Custom severity levels beyond ERROR/WARNING/INFO**: Three levels sufficient for current scope
- **Severity persistence**: Severity determined at validation time, not stored in project data
- **Severity-based notifications or alerts**: Deferred to future notification system design

**Related**:

- **ADR-020: DTO-Only MVVM Enforcement**: Severity exposed exclusively via data transfer objects
- **ADR-002: Clean Architecture with DDD**: Severity as domain concept with presentation interpretation
- **CONTINUOUS_TECHNICAL_ROADMAP.md Section 4.2**: Near-Term Expansion UX Enhancements

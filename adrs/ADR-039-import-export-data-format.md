# ADR-039: Import/Export Data Format

**Status**: Accepted

**Context**:

The application stores project data in an internal database format designed for efficient persistence and querying. Projects are created through the application UI, modified through form interactions, and saved to project-specific databases. This internal format serves persistence needs but provides no mechanism for data interchange.

This lack of interchange capability creates several architectural problems:

### 1. Data Portability Gap

Projects exist only within the application's internal storage format. No mechanism exists to extract project data in a portable format that other systems can consume. Users cannot share project data with collaborators who lack the application, cannot inspect project data outside the application, and cannot migrate projects between environments (development, staging, production).

When users need to share findings, they must share generated documents (Word, Excel, PDF) rather than underlying data. Recipients see outputs but cannot access, validate, or reuse source data. Data becomes locked in the application with no export path.

### 2. Human Readability Absence

Internal database storage is opaque to humans. Users cannot open a project file in a text editor to inspect or understand its contents. Debugging data issues requires launching the application, navigating to specific fields, and manually recording values. Bulk analysis of field values across multiple projects is impossible without the application.

This opacity prevents users from understanding what the application stores, how data is organized, or whether data is correct. Trust in the application requires trusting the internal format, with no independent verification possible.

### 3. Bulk Operations Limitation

Creating projects requires manual interaction with the application UI. No mechanism exists for bulk project creation from external data sources. Users cannot prepare project data in spreadsheets, databases, or other tools and import that data to create projects automatically.

Organizations with hundreds or thousands of projects must create each project individually through the UI. Data entry becomes repetitive and error-prone. No automation path exists for high-volume project creation.

### 4. Migration Path Absence

Changing the internal database schema (adding fields, changing types, restructuring entities) requires careful migration logic embedded in the application. Users cannot export data in a stable format before schema changes, verify the export externally, and re-import after changes. Schema migrations are all-or-nothing operations within the application with no external verification step.

If schema migration fails or produces incorrect results, users have no fallback. The old schema is gone, and data may be corrupted. No independent migration verification path exists.

### 5. Integration Barrier

External systems cannot integrate with project data. No programmatic way exists for external tools to extract project data, analyze it, transform it, or feed results back into projects. Every integration requires custom database access, coupling external systems to internal storage format and risking data corruption.

Business intelligence tools, data pipelines, and custom scripts cannot access project data without reverse-engineering the internal format. Integration becomes fragile and maintenance-heavy.

**Decision**:

Introduce a standardized data interchange format for importing and exporting project data, enabling data portability, human readability, bulk operations, and external system integration while maintaining architectural boundaries and data integrity guarantees.

### 1. Format Characteristics

**Structured and Hierarchical**: The interchange format represents the hierarchical structure of project data (projects contain entities, entities contain fields, fields have values). Structure is explicit and self-describing.

**Human-Readable**: The format is text-based and human-readable. Users can open exported files in text editors, understand contents without specialized tools, and make manual edits if necessary.

**Machine-Parsable**: The format is unambiguous and parsable by machines. External tools can reliably read, validate, and transform interchange data without ambiguity.

**Schema-Inclusive**: Exported data includes schema information (field types, validation rules, relationships). Importers can validate data against schema without requiring the application to be running.

**Versioned**: The format includes version information. Future format changes are detectable, enabling backward compatibility handling and migration support.

**Portable**: The format is independent of the application's internal storage representation. Changes to internal storage do not break the interchange format.

### 2. Export Scope

**Complete Project Export**: Exporting includes all project data: field values, entity instances, metadata, overrides, relationships. The export represents the entire project state at export time.

**Structure and Data Together**: Exports include both schema structure (entity definitions, field definitions) and data (field values, entity instances). Importers do not require separate schema files.

**Metadata Inclusion**: Exports include project metadata: creation date, last modified date, application version that created the project. Importers use metadata for compatibility checks and version handling.

**No History Export**: Field history (ADR-027) is not included in exports. History is internal audit data, not interchange data. Exporting history would create ambiguity about whether import creates new history entries.

**No Undo Export**: Undo stack state (ADR-031) is not included in exports. Undo is session-specific and ephemeral. Imported projects begin with empty undo stacks.

### 3. Import Scope

**Project Creation from Import**: Importing creates a new project from interchange data. Import is a project creation operation, not a project modification operation.

**Validation Before Import**: All imported data is validated before project creation. Validation includes: schema compatibility, field type correctness, constraint satisfaction, referential integrity. Invalid data prevents project creation.

**Schema Version Compatibility**: Imports specify schema version. If the imported schema version differs from the application's current schema version, compatibility rules determine whether import proceeds, requires migration, or fails.

**Conflict Resolution Not Applicable**: Import creates new projects. No conflicts exist between imported data and existing data. Users who want to merge imported data into existing projects must do so manually through the application.

**No Partial Import**: Import is atomic. Either the entire project is created successfully, or no project is created. Partial imports that create incomplete projects are not permitted.

### 4. Validation Architecture

**Domain Validation Applied**: Imported data passes through the same domain validation as manually entered data. Imported field values must satisfy all validation rules, constraints, and business logic.

**Application Layer Orchestration**: The application layer coordinates import operations. Import flows through commands and queries (CQRS pattern), not through direct repository access.

**Infrastructure Parsing**: The infrastructure layer parses interchange format into domain entities. Parsing logic is isolated in infrastructure, not spread across layers.

**Presentation Isolation**: The presentation layer receives import results via data transfer objects (ADR-020). Presentation never directly parses or interprets interchange format.

### 5. Compatibility Guarantees

**Backward Compatibility**: Newer application versions can import data exported by older application versions. The application maintains import compatibility for data created by previous versions.

**Forward Compatibility Not Guaranteed**: Older application versions may not import data exported by newer versions. Schema evolution may introduce fields, types, or constraints that older versions do not understand.

**Version Detection**: Imports include version information. The application detects version mismatches and determines compatibility. If import is incompatible, the application reports specific incompatibility reasons.

**Graceful Degradation**: When importing data from older versions with missing fields, the application applies default values or treats fields as optional. Import succeeds with warnings rather than failing.

**Schema Evolution Support**: The interchange format accommodates schema evolution. Adding fields, adding entities, or relaxing constraints does not break imports. Removing fields, removing entities, or tightening constraints may break imports from newer versions.

### 6. Architectural Boundaries

**Project Scope**: Import and export operate at project granularity. One export produces one project's data. One import creates one project. No cross-project imports or exports.

**Domain Purity Preserved**: The domain layer remains unaware of interchange format. Domain entities do not implement serialization methods. Interchange is an infrastructure concern.

**Repository Pattern Maintained**: Import and export use repository interfaces. Repositories mediate between interchange format and domain entities. Infrastructure implements serialization/deserialization.

**Unit of Work Coordination**: Imports coordinate with the Unit of Work pattern (ADR-011). Import is a transaction: all data imported or none. Rollback on validation failure or persistence error.

**No Direct File Access in Domain**: The domain layer does not read or write files. File operations are infrastructure concerns. Domain entities operate on parsed data structures.

### 7. Use Cases Enabled

**Data Backup and Restore**: Users export projects for backup. Backups are human-readable and verifiable. Restoration imports backup data to recreate projects.

**Data Sharing and Collaboration**: Users export projects to share with colleagues. Recipients import to create local copies. No proprietary tools required to inspect data.

**Bulk Project Creation**: Users prepare data in external tools (spreadsheets, scripts). Bulk import creates multiple projects from prepared data. High-volume workflows become automated.

**Data Analysis and Reporting**: External tools import project data for analysis. Business intelligence tools, custom scripts, and data pipelines access project data without database coupling.

**Migration and Upgrades**: Users export data before application upgrades. Exports serve as stable fallback. If upgrade fails, users can reinstall old version and re-import.

**Alternatives Considered**:

### Alternative 1: Database Dumps

Export the internal database file directly. Import by copying database file to project location.

**Rejected**: Couples external tools to internal storage format. Database schema changes break all exports. Not human-readable. No validation during import (corrupted databases imported without detection). No version compatibility handling. Violates architectural principle that interchange should be independent of storage representation.

### Alternative 2: UI-Only Copy/Paste

Provide UI clipboard operations to copy field values and paste into new projects.

**Rejected**: Limited to visible fields in current UI view. No bulk operations (must copy/paste each field individually). Not automatable (requires manual UI interaction). No external tool access. Does not address backup, migration, or sharing use cases. No machine-readable format for external integration.

### Alternative 3: Proprietary Binary Format

Design a custom binary format optimized for fast serialization and small file size.

**Rejected**: Not human-readable (users cannot inspect or verify exports). Requires specialized tools to read/write. No external tool support without custom parsers. Difficult to debug (cannot open in text editor). Binary formats are fragile under schema changes. Violates "human-readable" requirement.

### Alternative 4: One-Way Export Only

Provide export capability without import. Users can extract data but never bring it back.

**Rejected**: Does not address bulk project creation use case. Does not support backup/restore workflows (users can export but not restore). No migration verification path (cannot export, verify externally, and re-import). Asymmetric capability creates user confusion ("why can I export but not import?"). Limits utility significantly.

### Alternative 5: Direct Database Access for Integration

Document internal database schema. Allow external tools to query database directly.

**Rejected**: Bypasses domain validation (external tools can insert invalid data). Breaks encapsulation (external tools coupled to internal storage). No backward compatibility guarantees (schema changes break all external tools). Risks data corruption (external tools may violate integrity constraints). Violates architectural layering (infrastructure accessed directly, bypassing application/domain layers).

### Alternative 6: Schema-Less Interchange Format

Use a flexible key-value format with no predefined schema. Import interprets data dynamically.

**Rejected**: No validation before import (malformed data creates corrupted projects). Type ambiguity (is "123" a number or string?). No structure enforcement (relationships not validated). Error-prone imports (typos in field names cause silent failures). Does not enable bulk creation (no schema to validate against). Fragile under schema evolution (no detection of incompatible changes).

### Alternative 7: Multiple Format Support (JSON, XML, CSV, YAML)

Support multiple interchange formats simultaneously. Users choose format based on preferences.

**Rejected**: Increases implementation complexity without proportional benefit. Multiple formats require multiple parsers, multiple validators, multiple test suites. Format differences create inconsistencies (what succeeds in JSON may fail in CSV). Users must understand format tradeoffs. Single canonical format provides consistency. Additional formats can be added later if demand justifies complexity cost.

**Consequences**:

**Positive**:

- (+) **Data Portability**: Projects exportable in human-readable, portable format independent of internal storage
- (+) **Human Readability**: Users can inspect, verify, and understand exported data without application
- (+) **Bulk Operations**: External tools can prepare data and import in bulk, automating high-volume workflows
- (+) **External Integration**: Business intelligence tools, scripts, and pipelines can access project data programmatically
- (+) **Migration Verification**: Users can export, verify externally, and re-import during schema migrations
- (+) **Backup and Restore**: Human-readable backups enable long-term data preservation independent of application
- (+) **Collaboration**: Data sharing without requiring recipients to have identical application versions
- (+) **Architectural Integrity**: Import/export respects domain boundaries, validation rules, and layering principles
- (+) **Version Compatibility**: Backward compatibility ensures older exports remain importable
- (+) **Validation Guarantees**: All imported data validated before project creation, preventing corrupted projects

**Costs**:

- (-) **Implementation Complexity**: Requires serialization/deserialization logic in infrastructure layer
- (-) **Format Maintenance**: Interchange format must evolve with schema while maintaining compatibility
- (-) **Validation Overhead**: Imports require full validation pass before project creation (performance cost)
- (-) **Version Management**: Must track format versions and implement compatibility rules
- (-) **Testing Burden**: Requires testing imports from all supported previous versions
- (-) **Storage Overhead**: Interchange format may be larger than internal database format
- (-) **Documentation Requirements**: Users need clear documentation of interchange format structure and validation rules
- (-) **Edge Case Handling**: Must handle invalid imports, version mismatches, and partial data gracefully

**Mitigation**:

- Implementation isolated to infrastructure layer (domain and application unchanged)
- Versioning strategy defined upfront (monotonic version numbers, compatibility matrix)
- Validation reuses existing domain validation logic (no duplication)
- Comprehensive test suite with exports from each previous version
- Import errors provide actionable feedback (which fields failed validation, why)
- Documentation auto-generated from schema definitions where possible
- Graceful degradation handles missing fields with defaults
- Atomic import ensures no partial project creation on failure

**Non-Goals**:

This decision does NOT address:

- **Export Filtering**: Selective export of specific entities or fields (export is always complete project)
- **Incremental Import**: Updating existing projects from import (import always creates new project)
- **Merge Strategies**: Combining imported data with existing project data (manual merge only)
- **Diff and Patch**: Calculating differences between exports or applying partial updates
- **Export Scheduling**: Automated periodic exports or backup workflows (user-triggered only)
- **Cloud Storage Integration**: Direct export to cloud storage services (file system only)
- **Compression**: Archive or compression of exports (users can compress files manually)
- **Encryption**: Encrypted exports for sensitive data (users can encrypt files manually)
- **Multi-Project Export**: Exporting multiple projects into single file (one export per project)
- **Template Export**: Exporting project structure without data for reuse (separate feature)
- **Plugin Formats**: Custom interchange formats for extensions (v2+ feature)

**Related**:

- **ADR-007: Repository Pattern**: Import/export uses repository interfaces for data access
- **ADR-011: Unit of Work**: Import operations coordinate with UoW for transactional integrity
- **ADR-004: CQRS Pattern**: Import implemented as command, export as query
- **ADR-020: DTO-Only MVVM Enforcement**: Presentation receives import results via DTOs
- **ADR-003: Framework-Independent Domain Layer**: Domain unaware of interchange format
- **ADR-027: Field History Storage**: History not included in exports (audit vs interchange)
- **ADR-031: Undo History Persistence**: Undo not included in exports (session-specific state)
- **CONTINUOUS_TECHNICAL_ROADMAP.md Section 4.3**: Near-Term Expansion Data Operations

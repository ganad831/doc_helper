# ADR-026: Search Architecture

**Status**: Accepted

**Context**:

The application presents complex forms with hundreds of fields distributed across multiple tabs and entity collections. Users must navigate this structure using tab-based navigation, which requires prior knowledge of schema organization and field locations.

This navigation model creates several usability challenges:

### 1. Discovery Problem

Users cannot discover field locations without exploring each tab sequentially. A user seeking a specific field must remember or guess which tab contains it. No mechanism exists to ask "where is the field for X?" and receive a direct answer.

Field labels may use domain-specific terminology that users remember differently. A user thinking "site address" must know the field is labeled "site_location" and located in the "Project Info" tab.

### 2. Context Switching Cost

Locating related fields across different tabs requires repeated navigation. Users investigating a calculation must manually navigate to each dependency field's tab to inspect values. This sequential process increases cognitive load and time to understanding.

Large forms with deep nesting (entity collections within tabs, grouped fields) amplify this cost. Users lose context when navigating between distant locations in the form structure.

### 3. Value Inspection Limitations

No capability exists to answer questions like "which fields contain empty values?" or "where is the value 'incomplete' used?" Users must visually scan every field in every tab to find specific values or patterns.

Validation errors reference field paths, but provide no direct navigation. Users see an error for "borehole_records.depth" and must manually locate the boreholes tab and scroll to the depth field.

### 4. Architectural Absence

No architectural component addresses information retrieval as a distinct concern. Navigation and data access are coupled: users navigate to see data, and must see data to find information. Search is conceptually orthogonal to navigation, but the architecture provides no separation.

**Decision**:

Introduce search as a first-class architectural capability, implemented as a read-only query operation within the CQRS pattern.

### 1. Search Scope

**Current Project Only**: Search operates within the currently open project. No cross-project search capability. When no project is open, search is unavailable.

**Field Definitions and Values**: Search covers field metadata (field labels, entity names, field identifiers) and field values (user-entered data, computed values, resolved override values).

**Respect Domain Visibility**: Search results respect field visibility rules from the control system. Hidden fields do not appear in search results, maintaining consistency with domain constraints.

### 2. Architectural Roles

**Search as Query Operation**: Search is a read-only query in the CQRS pattern. Search never modifies data. Search results enable navigation, not inline editing.

**Application Layer Orchestration**: The application layer coordinates search. Queries arrive from presentation, application orchestrates domain data access, and results are mapped to data transfer objects.

**Domain as Data Source**: The domain layer provides searchable data contracts through repository interfaces. The domain does not implement search logic or ranking.

**Infrastructure Implements Strategy**: Search implementation strategy (SQL LIKE queries, full-text indexes, caching) resides in the infrastructure layer. The application layer depends on abstractions, not concrete strategies.

**Presentation Consumes Results**: Search results flow to presentation exclusively via data transfer objects. Presentation interprets results for display and navigation actions.

### 3. Architectural Rules

**Read-Only Operation**: Search has zero side effects. No state changes, no event emissions, no workflow triggers.

**No Cross-Project Scope**: Search boundaries align with project boundaries. Each search query carries an implicit project context.

**Result Ranking Optional**: Result ordering may reflect relevance, field order, or alphabetical sorting. Ranking strategy is an infrastructure concern, not an architectural requirement.

**Navigation Decoupling**: Search results contain navigation hints (field paths, entity identifiers), but do not execute navigation directly. Presentation consumes hints to perform navigation through existing navigation mechanisms.

**Domain Rule Consistency**: Search respects all domain constraints. If a control rule hides a field, that field is not searchable. Search cannot bypass validation, override, or control system rules.

### 4. Layer Responsibilities

**Domain Layer**: Defines repository interfaces for searchable data access. Provides value resolution logic (override → formula → raw). Does not implement search or ranking.

**Application Layer**: Defines search query use cases. Orchestrates repository access. Filters and ranks results. Maps domain entities to search result data transfer objects.

**Infrastructure Layer**: Implements search repository interfaces. Chooses search strategy (SQL queries, indexes). Handles performance concerns (caching, query optimization).

**Presentation Layer**: Provides search user interface. Receives search results via data transfer objects. Executes navigation based on result selection. Never directly accesses domain or infrastructure search logic.

### 5. Search Result Characteristics

**Immutable Data Transfer Objects**: Search results are immutable DTOs containing: field path, field label, current value (if applicable), entity name, tab location.

**No Domain Entity Exposure**: Search results do not expose domain entities directly. Results contain primitive values and navigation hints only.

**Truncation for Large Result Sets**: Infrastructure may limit result count to avoid performance degradation. Application layer does not enforce result limits; this is an infrastructure optimization concern.

**Alternatives Considered**:

### Alternative 1: UI-Only Text Filtering
Implement search as client-side filtering of currently visible fields without domain or application involvement.

**Rejected**: Insufficient for multi-tab forms. Cannot search fields not currently loaded in UI. Cannot search across entity collections efficiently. Poor performance for large forms.

### Alternative 2: Domain-Layer Search Logic
Place search logic in domain services as part of domain behavior.

**Rejected**: Violates domain purity (ADR-003). Search is an infrastructure concern (querying, indexing, ranking), not a business rule. Domain should provide data contracts, not search implementations.

### Alternative 3: Full-Text Search Engine
Integrate external search engine (Elasticsearch, Solr) for indexing and querying.

**Rejected**: Over-engineering for current scope. Projects contain hundreds of fields, not millions of documents. Infrastructure SQL-based search is sufficient. Adds deployment complexity and external dependencies without proportional benefit.

### Alternative 4: Database-Only Search
Allow presentation layer to query database directly via SQL for search results.

**Rejected**: Violates architectural layering. Presentation must not depend on database schema. Domain logic (visibility rules, value resolution) would be bypassed. No abstraction for changing search strategy.

### Alternative 5: Search as Navigation Service Extension
Add search methods to existing navigation service rather than creating separate search architecture.

**Rejected**: Conflates two distinct concerns. Navigation manages current location and history. Search finds information regardless of current location. Separate concerns enable independent evolution.

### Alternative 6: Search Results Include Edit Capability
Allow users to edit field values directly from search results without navigation.

**Rejected**: Introduces complexity and state management. Search would become a command operation, violating CQRS. Users lose context when editing outside normal form flow. Validation and control effects harder to display correctly.

**Consequences**:

**Positive**:

- (+) **Improved Discoverability**: Users locate fields by partial name, label, or value without schema knowledge
- (+) **CQRS Alignment**: Search as query operation maintains clear command/query separation
- (+) **Layer Separation**: Each layer has clear responsibility, enabling independent testing and evolution
- (+) **Infrastructure Flexibility**: Search strategy can evolve (SQL → indexing) without architectural changes
- (+) **Domain Integrity**: Search respects visibility, validation, and override rules through application orchestration
- (+) **DTO Boundary Preserved**: Presentation never imports domain, maintaining ADR-020 compliance
- (+) **Testability**: Search logic testable independently of UI and database

**Costs**:

- (-) **New Query Infrastructure**: Requires search repository interface and implementation
- (-) **DTO Definition Overhead**: New SearchResultDTO and related transfer objects
- (-) **Application Layer Complexity**: Search orchestration requires coordination of multiple repositories
- (-) **Performance Concerns**: Large projects may require search optimization (caching, indexing)
- (-) **Result Limit Decisions**: Must determine appropriate result count limits for usability

**Non-Goals**:

This decision does NOT address:

- **Advanced Search Syntax**: Regular expressions, fuzzy matching, boolean operators (deferred)
- **Search History**: Tracking and recalling previous searches (deferred)
- **Saved Searches**: Persisting search queries for reuse (deferred)
- **Cross-Project Search**: Searching across multiple projects simultaneously (out of scope)
- **Search Highlighting**: Visual highlighting of matching text in form fields (presentation detail)
- **Search-Based Bulk Operations**: Using search results to perform batch updates (separate concern)

**Related**:

- **ADR-004: CQRS Pattern**: Search implemented as query operation
- **ADR-020: DTO-Only MVVM Enforcement**: Search results exposed via DTOs only
- **ADR-003: Framework-Independent Domain Layer**: Domain provides contracts, not search implementation
- **CONTINUOUS_TECHNICAL_ROADMAP.md Section 4.2**: Near-Term Expansion UX Enhancements

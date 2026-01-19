# ADR-007: Repository Pattern with Raw SQL Mappers

**Status**: Accepted

**Context**: The old system had direct SQL queries scattered throughout services with hardcoded table/column names. No abstraction existed between domain entities and database operations.

**Decision**: Define repository interfaces in domain layer. Implement with SQLite in infrastructure using explicit row-to-entity mappers. No ORM—just raw SQL with typed mappers.

**Consequences**:
- (+) Domain decoupled from persistence mechanism
- (+) Easy to test with in-memory fakes
- (+) Full control over SQL performance
- (+) No ORM magic or N+1 surprises
- (-) More manual mapping code
- (-) Schema changes require mapper updates

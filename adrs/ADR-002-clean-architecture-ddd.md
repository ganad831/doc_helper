# ADR-002: Clean Architecture with Domain-Driven Design

**Status**: Accepted

**Context**: The old system mixed business logic across UI, services, and persistence layers. Changes to one feature required modifications in 5+ files. No clear domain model existed—just data classes with services containing SQL.

**Decision**: Adopt Clean Architecture (Presentation → Application → Domain ← Infrastructure) combined with DDD tactical patterns (Aggregates, Value Objects, Domain Events, Repositories).

**Consequences**:
- (+) Clear separation of concerns
- (+) Domain logic testable in isolation
- (+) Infrastructure swappable without domain changes
- (+) Bounded contexts prevent feature entanglement
- (-) More files and indirection
- (-) Learning curve for DDD patterns

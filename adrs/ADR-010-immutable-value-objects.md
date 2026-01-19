# ADR-010: Immutable Value Objects

**Status**: Accepted

**Context**: The old system used mutable dictionaries and data classes throughout. Shared mutable state led to subtle bugs when objects were modified unexpectedly.

**Decision**: Use frozen dataclasses for all value objects. Value objects are immutable, compared by value, and have no identity. Updates return new instances.

**Consequences**:
- (+) Thread-safe by design
- (+) No defensive copying needed
- (+) Simpler reasoning about state
- (+) Natural fit for caching/memoization
- (-) Memory overhead from creating new objects
- (-) Verbose update syntax (replace() or with_*() methods)

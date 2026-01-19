# ADR-004: CQRS for Read/Write Separation

**Status**: Accepted

**Context**: The old system used the same code paths for reading and writing data, leading to complex methods that handled both concerns. Read operations often loaded more data than needed.

**Decision**: Separate Commands (write operations) from Queries (read operations). Commands modify state and return Result types. Queries return DTOs optimized for the caller's needs.

**Consequences**:
- (+) Read models optimized for display
- (+) Write operations focused on validation and business rules
- (+) Easier to reason about state changes
- (+) Clear audit trail of mutations
- (-) More classes (Command + Handler for each operation)
- (-) Potential for read/write model drift

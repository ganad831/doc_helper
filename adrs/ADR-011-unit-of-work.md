# ADR-011: Unit of Work for Transaction Management

**Status**: Accepted

**Context**: The old system committed database changes immediately within service methods. There was no way to group multiple repository operations into a single atomic transaction.

**Decision**: Implement Unit of Work pattern. Repositories obtained from UoW share a connection. Changes are tracked and committed atomically when UoW.commit() is called.

**Consequences**:
- (+) Atomic multi-repository operations
- (+) Automatic rollback on exceptions
- (+) Single commit point for consistency
- (+) Clear transaction boundaries
- (-) Must pass UoW to all repository operations
- (-) Longer-lived connections during transactions

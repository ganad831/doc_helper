# ADR-008: Result Monad for Error Handling

**Status**: Accepted

**Context**: The old system used exceptions for both unexpected errors and business rule violations. Error handling was inconsistent, and callers often forgot to handle specific exceptions.

**Decision**: Use Result[T, E] monad for operations that can fail expectedly. Return Result.success(value) or Result.failure(error). Reserve exceptions for truly unexpected conditions (bugs, infrastructure failures).

**Consequences**:
- (+) Explicit error handling at call sites
- (+) Cannot forget to handle failures (type system helps)
- (+) Composable with map/flatMap operations
- (+) Clear distinction: Result = expected failure, Exception = bug
- (-) More verbose than try/catch
- (-) Learning curve for functional patterns

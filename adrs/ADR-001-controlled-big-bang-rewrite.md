# ADR-001: Controlled Big Bang Rewrite Strategy

**Status**: Accepted

**Context**: The existing codebase has extreme coupling (core layer imports PyQt6), god objects (MainWindow 2024 LOC), two competing global state systems, and zero test coverage. Incremental refactoring would require maintaining backward compatibility with untested code while extracting components from tightly coupled classes.

**Decision**: Perform a controlled big bang rewrite, building the new application alongside the old one rather than modifying existing code. Use the old app as a behavioral oracle for testing.

**Consequences**:
- (+) Clean slate with proper architecture from day one
- (+) No backward compatibility constraints
- (+) Old app remains functional as reference
- (+) Feature parity verifiable through oracle testing
- (-) Temporary code duplication during transition
- (-) Cannot leverage existing code directly

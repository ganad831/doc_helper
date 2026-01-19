# ADR-003: Framework-Independent Domain Layer

**Status**: Accepted

**Context**: The old core layer imported PyQt6 throughout (QObject, pyqtSignal, QTimer, QUndoCommand). This made the domain untestable without Qt and impossible to reuse in non-Qt contexts.

**Decision**: Domain layer has ZERO external dependencies. No PyQt6, no SQLite, no file system. Only Python standard library. PyQt6 usage confined strictly to presentation layer.

**Consequences**:
- (+) 100% unit testable without mocking frameworks
- (+) Domain can be reused in CLI, web, or mobile contexts
- (+) Framework upgrades don't affect business logic
- (-) Cannot use convenient Qt patterns (signals) in domain
- (-) Requires event bus abstraction for communication

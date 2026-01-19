# ADR-006: In-Memory Event Bus Over PyQt Signals

**Status**: Accepted

**Context**: The old system used PyQt signals (pyqtSignal) throughout, including in the core layer. This coupled the domain to PyQt6 and made cross-context communication implicit.

**Decision**: Use a framework-independent in-memory event bus for domain/application events. Create a Qt adapter in the presentation layer that bridges domain events to Qt signals.

**Consequences**:
- (+) Domain events work without PyQt6
- (+) Explicit event subscription/publishing
- (+) Easy to add event logging/debugging
- (+) Can swap to async or distributed bus later
- (-) Less convenient than pyqtSignal
- (-) Extra adapter layer for Qt integration

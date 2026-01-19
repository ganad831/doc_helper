# ADR-005: MVVM Pattern for Presentation Layer

**Status**: Accepted

**Context**: The old MainWindow (2024 LOC) mixed UI rendering with business logic, state management, and persistence. UI logic couldn't be tested without rendering actual widgets.

**Decision**: Adopt Model-View-ViewModel (MVVM) pattern. ViewModels contain all UI state and logic, exposing observable properties. Views (PyQt6 widgets) bind to ViewModels but contain no logic.

**Consequences**:
- (+) UI logic testable without Qt
- (+) Views become thin and declarative
- (+) Clear data binding contract
- (+) ViewModels reusable across different views
- (-) Boilerplate for property change notification
- (-) Requires discipline to keep views logic-free

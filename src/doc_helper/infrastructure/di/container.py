"""Dependency injection container for Doc Helper.

This module implements a simple but effective DI container for managing
service lifetimes and dependencies.

ARCHITECTURAL RULES (AGENT_RULES.md):
- Domain layer has ZERO dependencies (not registered here)
- Application services use domain interfaces
- Infrastructure implements domain interfaces
- Presentation depends only on Application

LIFETIMES:
- Singleton: Created once, shared across application lifetime
- Scoped: Created once per project session
- Transient: Created on every resolution (rarely used)
"""

from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class Container:
    """Simple dependency injection container.

    Supports:
    - Constructor injection
    - Singleton, Scoped, and Transient lifetimes
    - Factory functions for complex construction
    - Manual registration of pre-built instances

    Example:
        container = Container()

        # Register singleton
        container.register_singleton(
            ISchemaRepository,
            lambda: SqliteSchemaRepository(db_path="config.db")
        )

        # Resolve service
        repo = container.resolve(ISchemaRepository)
    """

    def __init__(self) -> None:
        """Initialize empty container."""
        self._singletons: dict[type, Any] = {}
        self._scoped: dict[type, Any] = {}
        self._factories: dict[type, Callable[[], Any]] = {}
        self._lifetimes: dict[type, str] = {}  # "singleton", "scoped", "transient"

    def register_singleton(
        self,
        interface: type[T],
        factory: Callable[[], T],
    ) -> None:
        """Register singleton service.

        Service is created once on first resolution and reused.

        Args:
            interface: Service interface type
            factory: Factory function to create service

        Example:
            container.register_singleton(
                ISchemaRepository,
                lambda: SqliteSchemaRepository(db_path="config.db")
            )
        """
        if not callable(factory):
            raise TypeError("factory must be callable")

        self._factories[interface] = factory
        self._lifetimes[interface] = "singleton"

    def register_scoped(
        self,
        interface: type[T],
        factory: Callable[[], T],
    ) -> None:
        """Register scoped service.

        Service is created once per scope (e.g., per project session).
        Scope is cleared when begin_scope() is called.

        Args:
            interface: Service interface type
            factory: Factory function to create service

        Example:
            container.register_scoped(
                IProjectRepository,
                lambda: SqliteProjectRepository(db_path="current_project.db")
            )
        """
        if not callable(factory):
            raise TypeError("factory must be callable")

        self._factories[interface] = factory
        self._lifetimes[interface] = "scoped"

    def register_transient(
        self,
        interface: type[T],
        factory: Callable[[], T],
    ) -> None:
        """Register transient service.

        Service is created every time it is resolved.

        Args:
            interface: Service interface type
            factory: Factory function to create service
        """
        if not callable(factory):
            raise TypeError("factory must be callable")

        self._factories[interface] = factory
        self._lifetimes[interface] = "transient"

    def register_instance(
        self,
        interface: type[T],
        instance: T,
    ) -> None:
        """Register pre-built singleton instance.

        Args:
            interface: Service interface type
            instance: Service instance

        Example:
            registry = TransformerRegistry()
            container.register_instance(TransformerRegistry, registry)
        """
        self._singletons[interface] = instance
        self._lifetimes[interface] = "singleton"

    def resolve(self, interface: type[T]) -> T:
        """Resolve service instance.

        Args:
            interface: Service interface type

        Returns:
            Service instance

        Raises:
            KeyError: If service not registered
            Exception: If factory fails

        Example:
            repo = container.resolve(ISchemaRepository)
        """
        if interface not in self._lifetimes:
            raise KeyError(f"Service {interface.__name__} not registered")

        lifetime = self._lifetimes[interface]

        if lifetime == "singleton":
            # Return cached instance or create new
            if interface not in self._singletons:
                self._singletons[interface] = self._factories[interface]()
            return self._singletons[interface]

        elif lifetime == "scoped":
            # Return cached instance or create new
            if interface not in self._scoped:
                self._scoped[interface] = self._factories[interface]()
            return self._scoped[interface]

        elif lifetime == "transient":
            # Always create new
            return self._factories[interface]()

        else:
            raise ValueError(f"Unknown lifetime: {lifetime}")

    def begin_scope(self) -> None:
        """Begin new scope.

        Clears all scoped service instances.
        Used when opening a new project.

        Example:
            # User opens new project
            container.begin_scope()
            # All scoped services will be recreated
        """
        self._scoped.clear()

    def end_scope(self) -> None:
        """End current scope.

        Clears all scoped service instances.
        Used when closing a project.

        Example:
            # User closes project
            container.end_scope()
        """
        self._scoped.clear()

    def is_registered(self, interface: type) -> bool:
        """Check if service is registered.

        Args:
            interface: Service interface type

        Returns:
            True if registered, False otherwise
        """
        return interface in self._lifetimes

    def clear(self) -> None:
        """Clear all registrations.

        Used for testing or application shutdown.
        """
        self._singletons.clear()
        self._scoped.clear()
        self._factories.clear()
        self._lifetimes.clear()


def register_undo_services(
    container: Container,
    field_service: Any,
    override_service: Any,
) -> None:
    """Register undo/redo infrastructure services.

    Services registered:
    - UndoManager: Singleton (shared across application)
    - FieldUndoService: Singleton (wraps field operations with undo)
    - OverrideUndoService: Singleton (wraps override operations with undo)
    - HistoryAdapter: Singleton (Qt signal bridge for UI)

    Dependencies:
    - FieldUndoService requires: IFieldService, UndoManager
    - OverrideUndoService requires: IOverrideService, IFieldService, UndoManager
    - HistoryAdapter requires: UndoManager

    Args:
        container: DI container instance
        field_service: Concrete implementation of IFieldService protocol
        override_service: Concrete implementation of IOverrideService protocol

    Note:
        IFieldService and IOverrideService are structural protocols.
        Pass concrete implementations that match the protocol interface.

    Example:
        container = Container()
        field_svc = MockFieldService()  # implements IFieldService protocol
        override_svc = MockOverrideService()  # implements IOverrideService protocol
        register_undo_services(container, field_svc, override_svc)
        undo_manager = container.resolve(UndoManager)
    """
    from doc_helper.application.services.field_undo_service import FieldUndoService
    from doc_helper.application.services.override_undo_service import (
        OverrideUndoService,
    )
    from doc_helper.application.undo.undo_manager import UndoManager
    from doc_helper.presentation.adapters.history_adapter import HistoryAdapter

    # Register UndoManager as singleton (shared across application)
    container.register_singleton(
        UndoManager,
        lambda: UndoManager(),
    )

    # Register FieldUndoService (depends on IFieldService + UndoManager)
    # field_service parameter must implement IFieldService protocol
    container.register_singleton(
        FieldUndoService,
        lambda: FieldUndoService(
            field_service=field_service,
            undo_manager=container.resolve(UndoManager),
        ),
    )

    # Register OverrideUndoService (depends on IOverrideService + IFieldService + UndoManager)
    # override_service and field_service parameters must implement respective protocols
    container.register_singleton(
        OverrideUndoService,
        lambda: OverrideUndoService(
            override_service=override_service,
            field_service=field_service,
            undo_manager=container.resolve(UndoManager),
        ),
    )

    # Register HistoryAdapter (depends on UndoManager)
    container.register_singleton(
        HistoryAdapter,
        lambda: HistoryAdapter(
            undo_manager=container.resolve(UndoManager),
        ),
    )

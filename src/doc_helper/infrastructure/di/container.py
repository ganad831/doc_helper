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

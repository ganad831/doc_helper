"""AppType router interface and implementation.

Routes operations to the appropriate AppType based on project context.
"""

from abc import ABC, abstractmethod
from typing import Optional

from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata
from doc_helper.platform.discovery.manifest_parser import ParsedManifest
from doc_helper.platform.registry.interfaces import IAppTypeRegistry


class IAppTypeRouter(ABC):
    """Interface for routing operations to AppTypes.

    The router determines which AppType should handle an operation
    based on project identity or explicit app_type_id.

    Router Responsibilities:
    - Validate AppType availability
    - Track current active AppType (for open project)
    - Route operations to correct AppType

    Phase 1 Status:
        In Phase 1, there is no AppType migration yet, so routing
        is minimal. The interface is defined for Phase 2+ when
        multiple AppTypes exist.

    Phase 2+ Usage:
        router = AppTypeRouter(registry)

        # When opening a project
        router.set_current(project.app_type_id)

        # Get current AppType for operations
        current = router.get_current_manifest()
        schema_repo = current_app_type.get_schema_repository()
    """

    @abstractmethod
    def set_current(self, app_type_id: str) -> bool:
        """Set the current active AppType.

        Called when opening a project to establish the active AppType
        context for subsequent operations.

        Args:
            app_type_id: ID of AppType to set as current

        Returns:
            True if AppType exists and was set, False otherwise
        """
        pass

    @abstractmethod
    def clear_current(self) -> None:
        """Clear the current active AppType.

        Called when closing a project.
        """
        pass

    @abstractmethod
    def get_current_id(self) -> Optional[str]:
        """Get the current active app_type_id.

        Returns:
            Current app_type_id or None if no project open
        """
        pass

    @abstractmethod
    def get_current_manifest(self) -> Optional[ParsedManifest]:
        """Get the current active AppType manifest.

        Returns:
            Current ParsedManifest or None if no project open
        """
        pass

    @abstractmethod
    def get_current_metadata(self) -> Optional[AppTypeMetadata]:
        """Get metadata for current active AppType.

        Returns:
            Current AppTypeMetadata or None if no project open
        """
        pass

    @abstractmethod
    def is_valid_app_type(self, app_type_id: str) -> bool:
        """Check if app_type_id is valid (registered).

        Args:
            app_type_id: ID to validate

        Returns:
            True if app_type_id is registered
        """
        pass


class AppTypeRouter(IAppTypeRouter):
    """Router implementation for directing operations to AppTypes.

    Uses the AppTypeRegistry to validate and look up AppTypes.
    Tracks the current active AppType for an open project.

    Usage:
        registry = AppTypeRegistry()
        # ... populate registry ...

        router = AppTypeRouter(registry)

        # When opening a project with app_type_id
        if router.set_current("soil_investigation"):
            manifest = router.get_current_manifest()
            # Use manifest to get schema, templates, etc.
        else:
            # Handle unknown AppType

        # When closing project
        router.clear_current()
    """

    def __init__(self, registry: IAppTypeRegistry) -> None:
        """Initialize router with registry.

        Args:
            registry: AppType registry for lookups
        """
        self._registry = registry
        self._current_app_type_id: Optional[str] = None

    def set_current(self, app_type_id: str) -> bool:
        """Set the current active AppType.

        Args:
            app_type_id: ID of AppType to set as current

        Returns:
            True if AppType exists and was set, False otherwise
        """
        if not self._registry.exists(app_type_id):
            return False

        self._current_app_type_id = app_type_id
        return True

    def clear_current(self) -> None:
        """Clear the current active AppType."""
        self._current_app_type_id = None

    def get_current_id(self) -> Optional[str]:
        """Get the current active app_type_id.

        Returns:
            Current app_type_id or None if no project open
        """
        return self._current_app_type_id

    def get_current_manifest(self) -> Optional[ParsedManifest]:
        """Get the current active AppType manifest.

        Returns:
            Current ParsedManifest or None if no project open
        """
        if self._current_app_type_id is None:
            return None
        return self._registry.get(self._current_app_type_id)

    def get_current_metadata(self) -> Optional[AppTypeMetadata]:
        """Get metadata for current active AppType.

        Returns:
            Current AppTypeMetadata or None if no project open
        """
        if self._current_app_type_id is None:
            return None
        return self._registry.get_metadata(self._current_app_type_id)

    def is_valid_app_type(self, app_type_id: str) -> bool:
        """Check if app_type_id is valid (registered).

        Args:
            app_type_id: ID to validate

        Returns:
            True if app_type_id is registered
        """
        return self._registry.exists(app_type_id)

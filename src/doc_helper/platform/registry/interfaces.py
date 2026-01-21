"""Registry interfaces.

Interface definitions for AppType registry.
"""

from abc import ABC, abstractmethod
from typing import Optional

from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata
from doc_helper.platform.discovery.manifest_parser import ParsedManifest


class IAppTypeRegistry(ABC):
    """Interface for AppType registry.

    The registry maintains a collection of available AppTypes and
    provides lookup functionality for the Platform to route operations.

    Registry Responsibilities:
    - Store discovered AppType manifests
    - Provide lookup by app_type_id
    - List all registered AppTypes
    - Validate uniqueness of app_type_id

    Usage:
        registry = AppTypeRegistry()
        registry.register(manifest)

        # Lookup
        manifest = registry.get("soil_investigation")
        if manifest:
            print(f"Found: {manifest.metadata.name}")

        # List all
        for app_type_id in registry.list_app_type_ids():
            print(app_type_id)
    """

    @abstractmethod
    def register(self, manifest: ParsedManifest) -> None:
        """Register an AppType manifest.

        Args:
            manifest: Parsed and validated manifest to register

        Raises:
            ValueError: If app_type_id already registered
        """
        pass

    @abstractmethod
    def unregister(self, app_type_id: str) -> bool:
        """Unregister an AppType.

        Args:
            app_type_id: ID of AppType to unregister

        Returns:
            True if AppType was registered and removed, False otherwise
        """
        pass

    @abstractmethod
    def get(self, app_type_id: str) -> Optional[ParsedManifest]:
        """Get manifest by app_type_id.

        Args:
            app_type_id: Unique identifier of AppType

        Returns:
            ParsedManifest if found, None otherwise
        """
        pass

    @abstractmethod
    def get_metadata(self, app_type_id: str) -> Optional[AppTypeMetadata]:
        """Get only metadata by app_type_id.

        Convenience method for UI that only needs display information.

        Args:
            app_type_id: Unique identifier of AppType

        Returns:
            AppTypeMetadata if found, None otherwise
        """
        pass

    @abstractmethod
    def exists(self, app_type_id: str) -> bool:
        """Check if AppType is registered.

        Args:
            app_type_id: Unique identifier to check

        Returns:
            True if AppType is registered
        """
        pass

    @abstractmethod
    def list_app_type_ids(self) -> tuple[str, ...]:
        """Get all registered app_type_ids.

        Returns:
            Tuple of all registered app_type_ids
        """
        pass

    @abstractmethod
    def list_all(self) -> tuple[ParsedManifest, ...]:
        """Get all registered manifests.

        Returns:
            Tuple of all registered ParsedManifest objects
        """
        pass

    @abstractmethod
    def list_metadata(self) -> tuple[AppTypeMetadata, ...]:
        """Get metadata for all registered AppTypes.

        Convenience method for UI that needs to display all AppTypes.

        Returns:
            Tuple of AppTypeMetadata for all registered AppTypes
        """
        pass

    @property
    @abstractmethod
    def count(self) -> int:
        """Get number of registered AppTypes.

        Returns:
            Count of registered AppTypes
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Remove all registered AppTypes.

        Primarily for testing purposes.
        """
        pass

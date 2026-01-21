"""AppType registry implementation.

Concrete implementation of IAppTypeRegistry for managing available AppTypes.
"""

import logging
from typing import Optional

from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata
from doc_helper.platform.discovery.manifest_parser import ParsedManifest
from doc_helper.platform.registry.interfaces import IAppTypeRegistry


logger = logging.getLogger(__name__)


class AppTypeRegistry(IAppTypeRegistry):
    """Registry for managing available AppTypes.

    Provides registration, lookup, and listing of AppType manifests.
    Used by Platform to track discovered AppTypes.

    Thread Safety:
        This implementation is NOT thread-safe. If concurrent access
        is required, external synchronization must be used.

    Usage:
        registry = AppTypeRegistry()

        # Register from discovery
        discovery = AppTypeDiscoveryService()
        result = discovery.discover(app_types_path)
        for manifest in result.manifests:
            registry.register(manifest)

        # Lookup
        if registry.exists("soil_investigation"):
            manifest = registry.get("soil_investigation")
            print(f"Using: {manifest.metadata.name}")

        # List for UI
        for metadata in registry.list_metadata():
            print(f"- {metadata.name} ({metadata.app_type_id})")
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._manifests: dict[str, ParsedManifest] = {}

    def register(self, manifest: ParsedManifest) -> None:
        """Register an AppType manifest.

        Args:
            manifest: Parsed and validated manifest to register

        Raises:
            ValueError: If app_type_id already registered
        """
        app_type_id = manifest.metadata.app_type_id

        if app_type_id in self._manifests:
            raise ValueError(
                f"AppType '{app_type_id}' is already registered"
            )

        self._manifests[app_type_id] = manifest
        logger.info(
            f"Registered AppType: {manifest.metadata.name} "
            f"({app_type_id} v{manifest.metadata.version})"
        )

    def unregister(self, app_type_id: str) -> bool:
        """Unregister an AppType.

        Args:
            app_type_id: ID of AppType to unregister

        Returns:
            True if AppType was registered and removed, False otherwise
        """
        if app_type_id in self._manifests:
            del self._manifests[app_type_id]
            logger.info(f"Unregistered AppType: {app_type_id}")
            return True
        return False

    def get(self, app_type_id: str) -> Optional[ParsedManifest]:
        """Get manifest by app_type_id.

        Args:
            app_type_id: Unique identifier of AppType

        Returns:
            ParsedManifest if found, None otherwise
        """
        return self._manifests.get(app_type_id)

    def get_metadata(self, app_type_id: str) -> Optional[AppTypeMetadata]:
        """Get only metadata by app_type_id.

        Args:
            app_type_id: Unique identifier of AppType

        Returns:
            AppTypeMetadata if found, None otherwise
        """
        manifest = self._manifests.get(app_type_id)
        return manifest.metadata if manifest else None

    def exists(self, app_type_id: str) -> bool:
        """Check if AppType is registered.

        Args:
            app_type_id: Unique identifier to check

        Returns:
            True if AppType is registered
        """
        return app_type_id in self._manifests

    def list_app_type_ids(self) -> tuple[str, ...]:
        """Get all registered app_type_ids.

        Returns:
            Tuple of all registered app_type_ids (sorted alphabetically)
        """
        return tuple(sorted(self._manifests.keys()))

    def list_all(self) -> tuple[ParsedManifest, ...]:
        """Get all registered manifests.

        Returns:
            Tuple of all registered ParsedManifest objects (sorted by id)
        """
        return tuple(
            self._manifests[app_type_id]
            for app_type_id in sorted(self._manifests.keys())
        )

    def list_metadata(self) -> tuple[AppTypeMetadata, ...]:
        """Get metadata for all registered AppTypes.

        Returns:
            Tuple of AppTypeMetadata for all registered AppTypes (sorted by id)
        """
        return tuple(
            self._manifests[app_type_id].metadata
            for app_type_id in sorted(self._manifests.keys())
        )

    @property
    def count(self) -> int:
        """Get number of registered AppTypes.

        Returns:
            Count of registered AppTypes
        """
        return len(self._manifests)

    def clear(self) -> None:
        """Remove all registered AppTypes."""
        self._manifests.clear()
        logger.info("Cleared all registered AppTypes")

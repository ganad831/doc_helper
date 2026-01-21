"""IAppType interface.

Contract that all AppType modules must implement.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata

if TYPE_CHECKING:
    from doc_helper.app_types.contracts.i_platform_services import IPlatformServices
    from doc_helper.domain.document.transformer_registry import TransformerRegistry
    from doc_helper.domain.schema.schema_repository import ISchemaRepository


class IAppType(ABC):
    """Interface that all AppType modules must implement.

    This contract defines what the Platform Host expects from each AppType module.
    AppTypes implement this interface to provide domain-specific document generation.

    Responsibilities of an AppType:
    - Provide metadata (id, name, description, icon)
    - Provide access to its schema repository
    - Register its custom transformers
    - Initialize with platform services

    Dependency Rules (ADR-V2-001, ADR-V2-003):
    - AppType modules implement this interface
    - AppType modules receive IPlatformServices from Platform
    - AppType modules MUST NOT depend on Platform internals
    - AppType modules MUST NOT depend on other AppType modules

    Example Implementation:
        class SoilInvestigationAppType(IAppType):
            def __init__(self) -> None:
                self._metadata = AppTypeMetadata(
                    app_type_id="soil_investigation",
                    name="Soil Investigation Report",
                    version="1.0.0"
                )

            @property
            def app_type_id(self) -> str:
                return self._metadata.app_type_id

            @property
            def metadata(self) -> AppTypeMetadata:
                return self._metadata

            # ... implement other methods
    """

    @property
    @abstractmethod
    def app_type_id(self) -> str:
        """Unique identifier for this AppType.

        This ID is used for:
        - Project-to-AppType association (stored in project metadata)
        - AppType lookup in registry
        - Configuration file references

        Returns:
            Unique string identifier (lowercase, alphanumeric, underscores)

        Example:
            return "soil_investigation"
        """
        pass

    @property
    @abstractmethod
    def metadata(self) -> AppTypeMetadata:
        """Display metadata for this AppType.

        Used by Platform to show AppType information in UI:
        - Welcome screen cards
        - Project creation dialog
        - Recent projects list

        Returns:
            Immutable AppTypeMetadata value object
        """
        pass

    @abstractmethod
    def get_schema_repository(self) -> "ISchemaRepository":
        """Return schema repository for this AppType.

        The schema repository provides access to entity definitions
        and field definitions specific to this AppType.

        Returns:
            ISchemaRepository implementation for this AppType

        Note:
            Each AppType has its own schema (config.db or equivalent).
            The Platform uses this to load the correct schema when
            opening a project of this AppType.
        """
        pass

    @abstractmethod
    def register_transformers(self, registry: "TransformerRegistry") -> None:
        """Register AppType-specific transformers.

        Called by Platform during AppType initialization to allow
        the AppType to register its custom transformers.

        Args:
            registry: TransformerRegistry to register transformers into

        Example:
            def register_transformers(self, registry: TransformerRegistry) -> None:
                registry.register(GeoCoordinateTransformer())
                registry.register(SoilClassificationTransformer())

        Note:
            Built-in transformers are registered by Platform.
            AppTypes only register their custom transformers here.
        """
        pass

    @abstractmethod
    def initialize(self, platform_services: "IPlatformServices") -> None:
        """Initialize AppType with platform services.

        Called by Platform after AppType is discovered and registered.
        The AppType stores references to platform services it needs.

        Args:
            platform_services: Services provided by Platform

        Example:
            def initialize(self, platform_services: IPlatformServices) -> None:
                self._translation_service = platform_services.translation_service
                self._transformer_registry = platform_services.transformer_registry
        """
        pass

"""IPlatformServices interface.

Contract for services that Platform provides to AppType modules.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from doc_helper.domain.common.translation import ITranslationService
    from doc_helper.domain.document.transformer_registry import TransformerRegistry


class IPlatformServices(ABC):
    """Interface for services provided by Platform to AppType modules.

    This contract defines what services the Platform Host makes available
    to AppType modules. AppTypes receive an implementation of this interface
    during initialization.

    Purpose (ADR-V2-001):
    - Provide cross-cutting services to AppTypes
    - Decouple AppTypes from Platform internals
    - Allow AppTypes to use shared infrastructure

    Available Services:
    - translation_service: i18n translations
    - transformer_registry: Shared transformer registry

    Future Services (v2+):
    - event_bus: Domain event publishing
    - unit_of_work_factory: Transaction management

    Dependency Rules (ADR-V2-001):
    - Platform provides: IPlatformServices implementation
    - AppTypes receive: IPlatformServices at initialization
    - AppTypes MUST NOT depend on Platform internals directly

    Example Usage in AppType:
        class SoilInvestigationAppType(IAppType):
            def initialize(self, platform_services: IPlatformServices) -> None:
                self._i18n = platform_services.translation_service
                self._transformers = platform_services.transformer_registry

            def get_display_name(self) -> str:
                key = TranslationKey("app_type.soil_investigation.name")
                return self._i18n.get(key, self._i18n.get_current_language())
    """

    @property
    @abstractmethod
    def translation_service(self) -> "ITranslationService":
        """Get the translation service for i18n.

        Returns:
            ITranslationService implementation

        Example:
            key = TranslationKey("validation.required")
            message = platform_services.translation_service.get(key, Language.ENGLISH)
        """
        pass

    @property
    @abstractmethod
    def transformer_registry(self) -> "TransformerRegistry":
        """Get the shared transformer registry.

        AppTypes can use this to:
        - Access built-in transformers
        - Register custom transformers

        Returns:
            TransformerRegistry with built-in transformers pre-registered

        Example:
            registry = platform_services.transformer_registry
            transformer = registry.get("arabic_ordinal")
        """
        pass

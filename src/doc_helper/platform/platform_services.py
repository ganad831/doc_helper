"""PlatformServices implementation.

Provides cross-cutting services to AppType modules.
"""

from doc_helper.app_types.contracts.i_platform_services import IPlatformServices
from doc_helper.domain.common.translation import ITranslationService
from doc_helper.domain.document.transformer_registry import TransformerRegistry


class PlatformServices(IPlatformServices):
    """Concrete implementation of IPlatformServices.

    Provides translation and transformer services to AppType modules.

    Usage:
        platform_services = PlatformServices(
            translation_service=translation_service,
            transformer_registry=transformer_registry,
        )
        app_type.initialize(platform_services)
    """

    def __init__(
        self,
        translation_service: ITranslationService,
        transformer_registry: TransformerRegistry,
    ) -> None:
        """Initialize platform services.

        Args:
            translation_service: Translation service for i18n
            transformer_registry: Shared transformer registry
        """
        self._translation_service = translation_service
        self._transformer_registry = transformer_registry

    @property
    def translation_service(self) -> ITranslationService:
        """Get the translation service for i18n.

        Returns:
            ITranslationService implementation
        """
        return self._translation_service

    @property
    def transformer_registry(self) -> TransformerRegistry:
        """Get the shared transformer registry.

        Returns:
            TransformerRegistry with built-in transformers
        """
        return self._transformer_registry

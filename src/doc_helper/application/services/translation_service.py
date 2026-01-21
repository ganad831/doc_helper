"""Translation service for application layer.

Wraps domain ITranslationService and provides DTO-based interface
for presentation layer to use.

RULES (AGENT_RULES.md Section 3-4):
- Application service bridges domain → DTOs
- Presentation layer uses this service, not domain ITranslationService
- All return types are DTOs, not domain types
"""

from typing import Optional

from doc_helper.domain.common.i18n import Language, TextDirection, TranslationKey
from doc_helper.domain.common.translation import ITranslationService
from doc_helper.application.dto.i18n_dto import LanguageDTO, TextDirectionDTO


class TranslationApplicationService:
    """Application-layer translation service.

    Bridges domain ITranslationService to presentation layer using DTOs.
    Presentation layer imports THIS service, not domain ITranslationService.

    Example:
        service = TranslationApplicationService(domain_translation_service)
        text = service.translate("menu.file.open")  # Returns string
        service.set_language(LanguageDTO.ARABIC)  # Uses DTO, not domain Language
    """

    def __init__(self, translation_service: ITranslationService) -> None:
        """Initialize translation application service.

        Args:
            translation_service: Domain translation service to wrap
        """
        self._translation_service = translation_service

    def translate(self, key: str, **params) -> str:
        """Translate a string using current language.

        Args:
            key: Translation key string (e.g., "menu.file.open")
            **params: Optional parameters for string interpolation

        Returns:
            Translated string with parameters interpolated
        """
        translation_key = TranslationKey(key)
        current_language = self._translation_service.get_current_language()
        return self._translation_service.get(
            translation_key, current_language, params or None
        )

    def translate_with_language(
        self, key: str, language: LanguageDTO, **params
    ) -> str:
        """Translate a string using specific language.

        Args:
            key: Translation key string
            language: LanguageDTO to translate to
            **params: Optional parameters for string interpolation

        Returns:
            Translated string
        """
        # Convert DTO to domain type
        domain_language = self._language_dto_to_domain(language)
        translation_key = TranslationKey(key)
        return self._translation_service.get(translation_key, domain_language, params or None)

    def get_current_language(self) -> LanguageDTO:
        """Get the currently selected language.

        Returns:
            Current language as DTO
        """
        domain_language = self._translation_service.get_current_language()
        return self._language_domain_to_dto(domain_language)

    def set_language(self, language: LanguageDTO) -> None:
        """Change the application language.

        Args:
            language: New language to set (DTO)
        """
        domain_language = self._language_dto_to_domain(language)
        self._translation_service.set_language(domain_language)

    def get_text_direction(self, language: Optional[LanguageDTO] = None) -> TextDirectionDTO:
        """Get text direction for language.

        Args:
            language: Language to get direction for (if None, uses current language)

        Returns:
            TextDirectionDTO (LTR or RTL)
        """
        if language is None:
            domain_language = self._translation_service.get_current_language()
        else:
            domain_language = self._language_dto_to_domain(language)

        domain_direction = domain_language.text_direction
        return self._text_direction_domain_to_dto(domain_direction)

    def has_translation(self, key: str, language: Optional[LanguageDTO] = None) -> bool:
        """Check if translation exists for key.

        Args:
            key: Translation key string
            language: Language to check (if None, uses current language)

        Returns:
            True if translation exists
        """
        translation_key = TranslationKey(key)

        if language is None:
            domain_language = self._translation_service.get_current_language()
        else:
            domain_language = self._language_dto_to_domain(language)

        return self._translation_service.has_key(translation_key, domain_language)

    # --- Private conversion methods ---

    @staticmethod
    def _language_dto_to_domain(dto: LanguageDTO) -> Language:
        """Convert LanguageDTO to domain Language."""
        if dto == LanguageDTO.ENGLISH:
            return Language.ENGLISH
        elif dto == LanguageDTO.ARABIC:
            return Language.ARABIC
        else:
            raise ValueError(f"Unknown LanguageDTO: {dto}")

    @staticmethod
    def _language_domain_to_dto(domain: Language) -> LanguageDTO:
        """Convert domain Language to LanguageDTO."""
        if domain == Language.ENGLISH:
            return LanguageDTO.ENGLISH
        elif domain == Language.ARABIC:
            return LanguageDTO.ARABIC
        else:
            raise ValueError(f"Unknown Language: {domain}")

    @staticmethod
    def _text_direction_domain_to_dto(domain: TextDirection) -> TextDirectionDTO:
        """Convert domain TextDirection to TextDirectionDTO."""
        if domain == TextDirection.LTR:
            return TextDirectionDTO.LTR
        elif domain == TextDirection.RTL:
            return TextDirectionDTO.RTL
        else:
            raise ValueError(f"Unknown TextDirection: {domain}")

"""Translation service interface.

Domain-layer interface for i18n (infrastructure will implement).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from doc_helper.domain.common.i18n import Language, TranslationKey


class ITranslationService(ABC):
    """Interface for translation services.

    This interface lives in the domain layer (dependency inversion).
    Implementation will be in infrastructure layer (e.g., JsonTranslationService).

    RULES (IMPLEMENTATION_RULES.md Section 2.2):
    - Interface in domain, implementation in infrastructure
    - NO framework dependencies (no PyQt6!)
    - NO file I/O in domain (infrastructure handles loading)

    Usage:
        # In domain/application layer:
        error_key = TranslationKey("validation.required")
        message = translation_service.get(error_key, Language.ENGLISH)

        # In infrastructure layer:
        class JsonTranslationService(ITranslationService):
            def get(self, key: TranslationKey, language: Language) -> str:
                # Load from translations/en.json or translations/ar.json
                return self._translations[language.code][key.key]
    """

    @abstractmethod
    def get(
        self,
        key: TranslationKey,
        language: Language,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get translated string for key and language.

        Args:
            key: Translation key
            language: Target language
            params: Optional parameters for string interpolation

        Returns:
            Translated string

        Example:
            key = TranslationKey("validation.min_length")
            params = {"min": 5}
            message = service.get(key, Language.ENGLISH, params)
            # "Minimum length is 5 characters"
        """
        pass

    @abstractmethod
    def get_current_language(self) -> Language:
        """Get the currently selected language.

        Returns:
            Current language
        """
        pass

    @abstractmethod
    def set_language(self, language: Language) -> None:
        """Set the current language.

        Args:
            language: Language to set as current

        Note:
            This may trigger UI updates in presentation layer.
        """
        pass

    @abstractmethod
    def has_key(self, key: TranslationKey, language: Language) -> bool:
        """Check if translation exists for key and language.

        Args:
            key: Translation key
            language: Target language

        Returns:
            True if translation exists
        """
        pass

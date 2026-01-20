"""JSON-based translation service implementation.

RULES (AGENT_RULES.md Section 2):
- Infrastructure layer implementation
- NO PyQt6 dependencies
- NO presentation layer imports
- Thread-safe for concurrent access
"""

import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from doc_helper.domain.common.i18n import Language, TranslationKey
from doc_helper.domain.common.translation import ITranslationService


class JsonTranslationService(ITranslationService):
    """JSON file-based translation service.

    Loads translations from JSON files in the translations/ directory.
    Supports nested key lookup (e.g., "menu.file.open") and parameter
    interpolation (e.g., "Hello {name}").

    File structure:
        translations/
        ├── en.json  # English translations
        └── ar.json  # Arabic translations

    JSON structure:
        {
            "menu": {
                "file": "File",
                "file.open": "Open"
            },
            "validation": {
                "required": "This field is required",
                "min_length": "Minimum length is {min} characters"
            }
        }

    Usage:
        service = JsonTranslationService(translations_dir="translations")
        key = TranslationKey("menu.file.open")
        text = service.get(key, Language.ENGLISH)  # "Open"

    Thread Safety:
        Uses threading.Lock to protect current language state.
    """

    def __init__(self, translations_dir: Path) -> None:
        """Initialize translation service.

        Args:
            translations_dir: Directory containing translation JSON files

        Raises:
            FileNotFoundError: If translations directory doesn't exist
            ValueError: If required translation files are missing
        """
        self._translations_dir = Path(translations_dir)
        if not self._translations_dir.exists():
            raise FileNotFoundError(
                f"Translations directory not found: {self._translations_dir}"
            )

        # Load all translations into memory (v1: simple, no lazy loading)
        self._translations: Dict[Language, Dict[str, Any]] = {}
        self._load_translations()

        # Current language state (thread-safe)
        self._current_language = Language.ENGLISH
        self._lock = threading.Lock()

    def _load_translations(self) -> None:
        """Load all translation files from directory.

        Raises:
            ValueError: If required translation files are missing
        """
        for language in Language:
            file_path = self._translations_dir / f"{language.code}.json"
            if not file_path.exists():
                raise ValueError(
                    f"Missing translation file for {language.display_name}: {file_path}"
                )

            with open(file_path, "r", encoding="utf-8") as f:
                self._translations[language] = json.load(f)

    def _get_nested_value(
        self, data: Dict[str, Any], key: str
    ) -> Optional[str]:
        """Get value from nested dictionary using dot notation.

        Handles both dot-separated keys within nested dicts and fully nested paths.

        Args:
            data: Dictionary to search
            key: Dot-separated key (e.g., "menu.file.open")

        Returns:
            Translation string if found, None otherwise

        Example:
            data = {"menu": {"file": {"open": "Open"}}}
            _get_nested_value(data, "menu.file.open") → "Open"
        """
        # Try direct lookup first (for keys with dots in them)
        if key in data:
            value = data[key]
            return str(value) if value is not None else None

        # Try nested lookup
        parts = key.split(".")

        # Try progressive nested lookup: navigate some levels, then look for rest as key
        # For "menu.file.open", try:
        #   depth=1: data["menu"]["file.open"]
        #   depth=2: data["menu"]["file"]["open"]
        for depth in range(1, len(parts)):
            current = data

            # Navigate to the specified depth
            for part in parts[:depth]:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    break
            else:
                # Successfully navigated, check for remaining key
                remaining = ".".join(parts[depth:])
                if isinstance(current, dict) and remaining in current:
                    value = current[remaining]
                    return str(value) if value is not None else None

        # Final attempt: fully nested lookup (all dots are levels)
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        # Final value must be a string or convertible to string
        if current is not None:
            return str(current)

        return None

    def _interpolate_params(
        self, text: str, params: Optional[Dict[str, Any]]
    ) -> str:
        """Interpolate parameters into translation string.

        Args:
            text: Translation string with {param} placeholders
            params: Dictionary of parameter values

        Returns:
            String with parameters interpolated

        Example:
            text = "Hello {name}, you have {count} messages"
            params = {"name": "Alice", "count": 5}
            → "Hello Alice, you have 5 messages"
        """
        if not params:
            return text

        try:
            return text.format(**params)
        except KeyError as e:
            # Missing parameter - return text with placeholder intact
            # This is graceful degradation, not an error
            return text

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
            Translated string with parameters interpolated

        Fallback behavior:
            1. Look up key in requested language
            2. If not found, try English (fallback language)
            3. If still not found, return key itself (graceful degradation)

        Example:
            key = TranslationKey("validation.min_length")
            params = {"min": 5}
            text = service.get(key, Language.ARABIC, params)
            → "الحد الأدنى للطول هو 5 أحرف"
        """
        key_str = key.key

        # Try requested language
        if language in self._translations:
            value = self._get_nested_value(self._translations[language], key_str)
            if value is not None:
                return self._interpolate_params(value, params)

        # Fallback to English
        if language != Language.ENGLISH and Language.ENGLISH in self._translations:
            value = self._get_nested_value(
                self._translations[Language.ENGLISH], key_str
            )
            if value is not None:
                return self._interpolate_params(value, params)

        # Fallback to key itself (graceful degradation)
        return key_str

    def get_current_language(self) -> Language:
        """Get the currently selected language.

        Returns:
            Current language

        Thread-safe: Uses lock to read current language state.
        """
        with self._lock:
            return self._current_language

    def set_language(self, language: Language) -> None:
        """Set the current language.

        Args:
            language: Language to set as current

        Thread-safe: Uses lock to update current language state.

        Note:
            This method only updates the service state.
            UI updates must be handled by presentation layer.
        """
        with self._lock:
            self._current_language = language

    def has_key(self, key: TranslationKey, language: Language) -> bool:
        """Check if translation exists for key and language.

        Args:
            key: Translation key
            language: Target language

        Returns:
            True if translation exists in that language

        Example:
            key = TranslationKey("menu.file.open")
            service.has_key(key, Language.ENGLISH)  # True
            service.has_key(key, Language.ARABIC)   # True/False
        """
        if language not in self._translations:
            return False

        value = self._get_nested_value(self._translations[language], key.key)
        return value is not None

    def translate(self, key: str) -> str:
        """Convenience method: translate using current language.

        Args:
            key: Translation key string

        Returns:
            Translated string in current language

        Example:
            service.set_language(Language.ARABIC)
            service.translate("menu.file.open")  # Returns Arabic translation
        """
        translation_key = TranslationKey(key)
        return self.get(translation_key, self.get_current_language())

"""Internationalization (i18n) value objects.

Domain-level i18n concepts (v1: English and Arabic).
"""

from dataclasses import dataclass
from enum import Enum

from doc_helper.domain.common.value_object import ValueObject


class Language(str, Enum):
    """Supported languages (v1: English and Arabic).

    v1 Scope:
    - ENGLISH: English language (LTR)
    - ARABIC: Arabic language (RTL)

    v2+ may add more languages by extending this enum.
    """

    ENGLISH = "en"
    ARABIC = "ar"

    @property
    def code(self) -> str:
        """Get language code (e.g., 'en', 'ar')."""
        return self.value

    @property
    def display_name(self) -> str:
        """Get display name in the language itself."""
        return {
            Language.ENGLISH: "English",
            Language.ARABIC: "العربية",
        }[self]

    @property
    def text_direction(self) -> "TextDirection":
        """Get text direction for this language."""
        return {
            Language.ENGLISH: TextDirection.LTR,
            Language.ARABIC: TextDirection.RTL,
        }[self]

    @staticmethod
    def from_code(code: str) -> "Language":
        """Get Language from code string.

        Args:
            code: Language code ('en', 'ar')

        Returns:
            Language enum value

        Raises:
            ValueError: If code is not supported
        """
        try:
            return Language(code)
        except ValueError:
            raise ValueError(
                f"Unsupported language code: {code}. "
                f"Supported: {[lang.code for lang in Language]}"
            )


class TextDirection(str, Enum):
    """Text direction for UI layout.

    LTR: Left-to-right (English, etc.)
    RTL: Right-to-left (Arabic, Hebrew, etc.)
    """

    LTR = "ltr"
    RTL = "rtl"

    def is_ltr(self) -> bool:
        """Check if this is left-to-right."""
        return self == TextDirection.LTR

    def is_rtl(self) -> bool:
        """Check if this is right-to-left."""
        return self == TextDirection.RTL


@dataclass(frozen=True)
class TranslationKey(ValueObject):
    """Key for looking up translated strings.

    Translation keys follow dot notation: "context.subcontext.key"

    Examples:
        - "menu.file.open" → "Open"
        - "validation.required" → "This field is required"
        - "dialog.confirm.title" → "Confirm"

    RULES (IMPLEMENTATION_RULES.md Section 4):
    - Keys must follow dot notation
    - Keys are case-sensitive
    - Keys should be hierarchical (context.subcontext.key)
    - NO hardcoded UI strings in domain/application layers

    Usage:
        key = TranslationKey("validation.required")
        message = translation_service.get(key, language)
    """

    key: str

    def __post_init__(self) -> None:
        """Validate translation key format."""
        if not self.key:
            raise ValueError("Translation key cannot be empty")
        if not self.key.replace("_", "").replace(".", "").replace("-", "").isalnum():
            raise ValueError(
                f"Translation key contains invalid characters: {self.key}. "
                "Only alphanumeric, dots, hyphens, and underscores allowed."
            )

    def __str__(self) -> str:
        """String representation is the key itself."""
        return self.key

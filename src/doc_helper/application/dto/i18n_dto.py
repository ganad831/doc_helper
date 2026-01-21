"""Internationalization DTOs for UI display.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
"""

from dataclasses import dataclass
from enum import Enum


class LanguageDTO(str, Enum):
    """UI-facing language option for display.

    Represents supported languages in the UI (v1: English and Arabic).

    This is a simple mirror of domain.Language but without domain behavior.
    Presentation layer uses this DTO instead of importing domain types.
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
            LanguageDTO.ENGLISH: "English",
            LanguageDTO.ARABIC: "العربية",
        }[self]


class TextDirectionDTO(str, Enum):
    """UI-facing text direction for layout.

    LTR: Left-to-right (English, etc.)
    RTL: Right-to-left (Arabic, Hebrew, etc.)

    This is a simple mirror of domain.TextDirection but without domain behavior.
    Presentation layer uses this DTO instead of importing domain types.
    """

    LTR = "ltr"
    RTL = "rtl"

    def is_ltr(self) -> bool:
        """Check if this is left-to-right."""
        return self == TextDirectionDTO.LTR

    def is_rtl(self) -> bool:
        """Check if this is right-to-left."""
        return self == TextDirectionDTO.RTL


@dataclass(frozen=True)
class LanguageInfoDTO:
    """UI-facing language information for display.

    Combines language code, display name, and text direction
    for UI language selection and layout.
    """

    code: str  # Language code ("en", "ar")
    display_name: str  # Display name in the language itself
    text_direction: TextDirectionDTO  # LTR or RTL

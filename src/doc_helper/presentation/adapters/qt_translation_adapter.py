"""Qt adapter for translation service.

Bridges the application translation service to Qt-specific UI updates including:
- Text content updates via Qt signals
- Layout direction (LTR/RTL) switching
- Font and text alignment adjustments for RTL languages

RULES (AGENT_RULES.md Section 3-4):
- Presentation layer adapter
- Uses application service (DTO-based), NOT domain types
- Emits Qt signals for UI updates
- NO domain logic (pure adapter)
- NO domain imports (DTO-only MVVM)
"""

from typing import Optional

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget

from doc_helper.application.dto.i18n_dto import LanguageDTO, TextDirectionDTO
from doc_helper.application.services.translation_service import TranslationApplicationService


class QtTranslationAdapter(QObject):
    """Qt adapter for TranslationApplicationService.

    Responsibilities:
    - Wraps TranslationApplicationService with Qt signal emissions
    - Applies layout direction changes to Qt application
    - Provides convenience methods for translating UI strings
    - Emits signals when language changes for UI updates

    Usage:
        adapter = QtTranslationAdapter(translation_app_service)
        adapter.language_changed.connect(main_window.on_language_changed)

        # Change language (emits signal)
        adapter.change_language(LanguageDTO.ARABIC)

        # Translate strings
        text = adapter.translate("menu.file.open")  # Uses current language
    """

    # Signals
    language_changed = pyqtSignal(str)  # Emitted when language changes (language code)
    layout_direction_changed = pyqtSignal(Qt.LayoutDirection)  # LTR/RTL

    def __init__(
        self,
        translation_service: TranslationApplicationService,
        app: Optional[QApplication] = None,
    ) -> None:
        """Initialize Qt translation adapter.

        Args:
            translation_service: Application translation service (DTO-based)
            app: QApplication instance (if None, uses QApplication.instance())
        """
        super().__init__()
        self._translation_service = translation_service
        self._app = app or QApplication.instance()

        if self._app is None:
            raise RuntimeError(
                "No QApplication instance found. "
                "Create QApplication before QtTranslationAdapter."
            )

        # Set initial layout direction based on current language
        self._apply_layout_direction(self._translation_service.get_current_language())

    def get_current_language(self) -> LanguageDTO:
        """Get the currently selected language.

        Returns:
            Current language DTO from translation service
        """
        return self._translation_service.get_current_language()

    def change_language(self, language: LanguageDTO) -> None:
        """Change the application language.

        This method:
        1. Updates translation service
        2. Applies layout direction (LTR/RTL)
        3. Emits signals for UI updates

        Args:
            language: New language to set (DTO)

        Signals Emitted:
            - language_changed(str) - emits language code
            - layout_direction_changed(Qt.LayoutDirection)
        """
        if not isinstance(language, LanguageDTO):
            raise TypeError(f"language must be LanguageDTO enum, got {type(language)}")

        # Update translation service
        self._translation_service.set_language(language)

        # Apply layout direction
        self._apply_layout_direction(language)

        # Emit signals for UI updates (emit code as string)
        self.language_changed.emit(language.code)

    def _apply_layout_direction(self, language: LanguageDTO) -> None:
        """Apply layout direction based on language.

        Args:
            language: LanguageDTO to apply direction for

        Signals Emitted:
            - layout_direction_changed(Qt.LayoutDirection)
        """
        text_direction = self._translation_service.get_text_direction(language)

        # Convert DTO TextDirection to Qt LayoutDirection
        if text_direction == TextDirectionDTO.RTL:
            qt_direction = Qt.LayoutDirection.RightToLeft
        else:
            qt_direction = Qt.LayoutDirection.LeftToRight

        # Apply to application
        if self._app:
            self._app.setLayoutDirection(qt_direction)

        # Emit signal
        self.layout_direction_changed.emit(qt_direction)

    def translate(self, key: str, **params) -> str:
        """Translate a string using current language.

        Convenience method for translating with current language.

        Args:
            key: Translation key string (e.g., "menu.file.open")
            **params: Optional parameters for string interpolation

        Returns:
            Translated string with parameters interpolated

        Example:
            adapter.translate("validation.min_length", min=5)
            → "Minimum length is 5 characters" (English)
            → "الحد الأدنى للطول هو 5 أحرف" (Arabic)
        """
        return self._translation_service.translate(key, **params)

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

        Example:
            adapter.translate_with_language("menu.file", LanguageDTO.ARABIC)
            → "ملف"
        """
        return self._translation_service.translate_with_language(key, language, **params)

    def has_translation(self, key: str, language: Optional[LanguageDTO] = None) -> bool:
        """Check if translation exists for key.

        Args:
            key: Translation key string
            language: LanguageDTO to check (if None, uses current language)

        Returns:
            True if translation exists
        """
        return self._translation_service.has_translation(key, language)

    def apply_rtl_to_widget(self, widget: QWidget, language: Optional[LanguageDTO] = None) -> None:
        """Apply RTL-specific styling to a widget.

        Manually apply RTL styling to widgets that need special handling
        beyond automatic layout direction.

        Args:
            widget: Widget to apply RTL styling to
            language: LanguageDTO to use (if None, uses current language)

        Example:
            # Force right alignment for Arabic
            adapter.apply_rtl_to_widget(label, LanguageDTO.ARABIC)
        """
        text_direction = self._translation_service.get_text_direction(language)

        if text_direction == TextDirectionDTO.RTL:
            widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def get_text_direction(self, language: Optional[LanguageDTO] = None) -> TextDirectionDTO:
        """Get text direction for language.

        Args:
            language: LanguageDTO to get direction for (if None, uses current language)

        Returns:
            TextDirectionDTO (LTR or RTL)
        """
        return self._translation_service.get_text_direction(language)

    def is_rtl(self, language: Optional[LanguageDTO] = None) -> bool:
        """Check if language is right-to-left.

        Args:
            language: LanguageDTO to check (if None, uses current language)

        Returns:
            True if language is RTL
        """
        return self.get_text_direction(language).is_rtl()

    def get_qt_layout_direction(
        self, language: Optional[LanguageDTO] = None
    ) -> Qt.LayoutDirection:
        """Get Qt layout direction for language.

        Args:
            language: LanguageDTO to get direction for (if None, uses current language)

        Returns:
            Qt.LayoutDirection (LeftToRight or RightToLeft)
        """
        text_direction = self.get_text_direction(language)
        if text_direction == TextDirectionDTO.RTL:
            return Qt.LayoutDirection.RightToLeft
        else:
            return Qt.LayoutDirection.LeftToRight

"""Qt adapter for translation service.

Bridges the framework-independent ITranslationService from domain layer
to Qt-specific UI updates including:
- Text content updates via Qt signals
- Layout direction (LTR/RTL) switching
- Font and text alignment adjustments for RTL languages

RULES (AGENT_RULES.md Section 3):
- Presentation layer adapter
- Bridges domain ITranslationService → PyQt6 UI
- Emits Qt signals for UI updates
- NO domain logic (pure adapter)
"""

from typing import Optional

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget

from doc_helper.domain.common.i18n import Language, TextDirection, TranslationKey
from doc_helper.domain.common.translation import ITranslationService


class QtTranslationAdapter(QObject):
    """Qt adapter for ITranslationService.

    Responsibilities:
    - Wraps ITranslationService with Qt signal emissions
    - Applies layout direction changes to Qt application
    - Provides convenience methods for translating UI strings
    - Emits signals when language changes for UI updates

    Usage:
        adapter = QtTranslationAdapter(translation_service)
        adapter.language_changed.connect(main_window.on_language_changed)

        # Change language (emits signal)
        adapter.change_language(Language.ARABIC)

        # Translate strings
        text = adapter.translate("menu.file.open")  # Uses current language
    """

    # Signals
    language_changed = pyqtSignal(Language)  # Emitted when language changes
    layout_direction_changed = pyqtSignal(Qt.LayoutDirection)  # LTR/RTL

    def __init__(
        self,
        translation_service: ITranslationService,
        app: Optional[QApplication] = None,
    ) -> None:
        """Initialize Qt translation adapter.

        Args:
            translation_service: Domain translation service
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

    def get_current_language(self) -> Language:
        """Get the currently selected language.

        Returns:
            Current language from translation service
        """
        return self._translation_service.get_current_language()

    def change_language(self, language: Language) -> None:
        """Change the application language.

        This method:
        1. Updates translation service
        2. Applies layout direction (LTR/RTL)
        3. Emits signals for UI updates

        Args:
            language: New language to set

        Signals Emitted:
            - language_changed(Language)
            - layout_direction_changed(Qt.LayoutDirection)
        """
        if not isinstance(language, Language):
            raise TypeError(f"language must be Language enum, got {type(language)}")

        # Update translation service
        self._translation_service.set_language(language)

        # Apply layout direction
        self._apply_layout_direction(language)

        # Emit signals for UI updates
        self.language_changed.emit(language)

    def _apply_layout_direction(self, language: Language) -> None:
        """Apply layout direction based on language.

        Args:
            language: Language to apply direction for

        Signals Emitted:
            - layout_direction_changed(Qt.LayoutDirection)
        """
        text_direction = language.text_direction

        # Convert domain TextDirection to Qt LayoutDirection
        if text_direction == TextDirection.RTL:
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
        translation_key = TranslationKey(key)
        current_language = self._translation_service.get_current_language()
        return self._translation_service.get(
            translation_key, current_language, params or None
        )

    def translate_with_language(
        self, key: str, language: Language, **params
    ) -> str:
        """Translate a string using specific language.

        Args:
            key: Translation key string
            language: Language to translate to
            **params: Optional parameters for string interpolation

        Returns:
            Translated string

        Example:
            adapter.translate_with_language("menu.file", Language.ARABIC)
            → "ملف"
        """
        translation_key = TranslationKey(key)
        return self._translation_service.get(translation_key, language, params or None)

    def has_translation(self, key: str, language: Optional[Language] = None) -> bool:
        """Check if translation exists for key.

        Args:
            key: Translation key string
            language: Language to check (if None, uses current language)

        Returns:
            True if translation exists
        """
        translation_key = TranslationKey(key)
        lang = language or self._translation_service.get_current_language()
        return self._translation_service.has_key(translation_key, lang)

    def apply_rtl_to_widget(self, widget: QWidget, language: Optional[Language] = None) -> None:
        """Apply RTL-specific styling to a widget.

        Manually apply RTL styling to widgets that need special handling
        beyond automatic layout direction.

        Args:
            widget: Widget to apply RTL styling to
            language: Language to use (if None, uses current language)

        Example:
            # Force right alignment for Arabic
            adapter.apply_rtl_to_widget(label, Language.ARABIC)
        """
        lang = language or self._translation_service.get_current_language()
        text_direction = lang.text_direction

        if text_direction == TextDirection.RTL:
            widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def get_text_direction(self, language: Optional[Language] = None) -> TextDirection:
        """Get text direction for language.

        Args:
            language: Language to get direction for (if None, uses current language)

        Returns:
            TextDirection (LTR or RTL)
        """
        lang = language or self._translation_service.get_current_language()
        return lang.text_direction

    def is_rtl(self, language: Optional[Language] = None) -> bool:
        """Check if language is right-to-left.

        Args:
            language: Language to check (if None, uses current language)

        Returns:
            True if language is RTL
        """
        return self.get_text_direction(language).is_rtl()

    def get_qt_layout_direction(
        self, language: Optional[Language] = None
    ) -> Qt.LayoutDirection:
        """Get Qt layout direction for language.

        Args:
            language: Language to get direction for (if None, uses current language)

        Returns:
            Qt.LayoutDirection (LeftToRight or RightToLeft)
        """
        text_direction = self.get_text_direction(language)
        if text_direction == TextDirection.RTL:
            return Qt.LayoutDirection.RightToLeft
        else:
            return Qt.LayoutDirection.LeftToRight

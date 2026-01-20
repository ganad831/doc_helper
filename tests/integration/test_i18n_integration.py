"""Integration tests for i18n system with RTL support.

Tests the full i18n flow from translation files → adapter → UI updates.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from doc_helper.domain.common.i18n import Language, TextDirection
from doc_helper.infrastructure.i18n.json_translation_service import (
    JsonTranslationService,
)
from doc_helper.presentation.adapters.qt_translation_adapter import QtTranslationAdapter


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests (module scope to avoid multiple instances)."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't quit - other tests might need it


@pytest.fixture
def translation_service() -> JsonTranslationService:
    """Create real translation service with JSON files."""
    translations_dir = Path("translations")
    return JsonTranslationService(translations_dir=translations_dir)


@pytest.fixture
def qt_adapter(qapp: QApplication, translation_service: JsonTranslationService) -> QtTranslationAdapter:
    """Create QtTranslationAdapter with real dependencies."""
    return QtTranslationAdapter(translation_service, qapp)


class TestI18nIntegration:
    """Integration tests for i18n system."""

    def test_translation_service_loads_english_translations(
        self, translation_service: JsonTranslationService
    ):
        """Test that English translations load correctly from JSON."""
        # Set language to English
        translation_service.set_language(Language.ENGLISH)

        # Test menu translations
        file_menu = translation_service.translate("menu.file")
        assert file_menu == "File"

        edit_menu = translation_service.translate("menu.edit")
        assert edit_menu == "Edit"

        # Test project translations
        save_project = translation_service.translate("menu.file.save")
        assert save_project == "Save Project"

    def test_translation_service_loads_arabic_translations(
        self, translation_service: JsonTranslationService
    ):
        """Test that Arabic translations load correctly from JSON."""
        # Set language to Arabic
        translation_service.set_language(Language.ARABIC)

        # Test menu translations
        file_menu = translation_service.translate("menu.file")
        assert file_menu == "ملف"

        edit_menu = translation_service.translate("menu.edit")
        assert edit_menu == "تحرير"

        # Test project translations
        save_project = translation_service.translate("menu.file.save")
        assert save_project == "حفظ المشروع"

    def test_adapter_applies_ltr_for_english(
        self, qapp: QApplication, qt_adapter: QtTranslationAdapter
    ):
        """Test that English language applies LTR layout direction."""
        # Change to English
        qt_adapter.change_language(Language.ENGLISH)

        # Verify layout direction is LTR
        assert qapp.layoutDirection() == Qt.LayoutDirection.LeftToRight

    def test_adapter_applies_rtl_for_arabic(
        self, qapp: QApplication, qt_adapter: QtTranslationAdapter
    ):
        """Test that Arabic language applies RTL layout direction."""
        # Change to Arabic
        qt_adapter.change_language(Language.ARABIC)

        # Verify layout direction is RTL
        assert qapp.layoutDirection() == Qt.LayoutDirection.RightToLeft

    def test_adapter_emits_language_changed_signal(self, qt_adapter: QtTranslationAdapter):
        """Test that adapter emits language_changed signal when language changes."""
        # Setup signal spy
        signal_spy = Mock()
        qt_adapter.language_changed.connect(signal_spy)

        # Change language
        qt_adapter.change_language(Language.ARABIC)

        # Verify signal was emitted with correct language
        signal_spy.assert_called_once_with(Language.ARABIC)

    def test_adapter_emits_layout_direction_changed_signal(
        self, qt_adapter: QtTranslationAdapter
    ):
        """Test that adapter emits layout_direction_changed signal."""
        # Setup signal spy
        signal_spy = Mock()
        qt_adapter.layout_direction_changed.connect(signal_spy)

        # Change language
        qt_adapter.change_language(Language.ENGLISH)

        # Verify signal was emitted with correct direction
        signal_spy.assert_called_once_with(Qt.LayoutDirection.LeftToRight)

    def test_adapter_translates_using_current_language(
        self, qt_adapter: QtTranslationAdapter
    ):
        """Test that adapter translates using current language."""
        # Set to English
        qt_adapter.change_language(Language.ENGLISH)
        english_text = qt_adapter.translate("menu.file")
        assert english_text == "File"

        # Set to Arabic
        qt_adapter.change_language(Language.ARABIC)
        arabic_text = qt_adapter.translate("menu.file")
        assert arabic_text == "ملف"

    def test_language_switching_updates_ui_direction(
        self, qapp: QApplication, qt_adapter: QtTranslationAdapter
    ):
        """Test that language switching updates QApplication layout direction."""
        # Start with English (LTR)
        qt_adapter.change_language(Language.ENGLISH)
        assert qapp.layoutDirection() == Qt.LayoutDirection.LeftToRight

        # Switch to Arabic (RTL)
        qt_adapter.change_language(Language.ARABIC)
        assert qapp.layoutDirection() == Qt.LayoutDirection.RightToLeft

        # Switch back to English (LTR)
        qt_adapter.change_language(Language.ENGLISH)
        assert qapp.layoutDirection() == Qt.LayoutDirection.LeftToRight

    def test_adapter_has_translation_check(self, qt_adapter: QtTranslationAdapter):
        """Test that adapter can check if translation exists."""
        # Check existing translation
        assert qt_adapter.has_translation("menu.file", Language.ENGLISH) is True
        assert qt_adapter.has_translation("menu.file", Language.ARABIC) is True

        # Check non-existent translation
        assert qt_adapter.has_translation("menu.nonexistent", Language.ENGLISH) is False

    def test_adapter_get_text_direction(self, qt_adapter: QtTranslationAdapter):
        """Test that adapter returns correct text direction for languages."""
        # English is LTR
        assert qt_adapter.get_text_direction(Language.ENGLISH) == TextDirection.LTR

        # Arabic is RTL
        assert qt_adapter.get_text_direction(Language.ARABIC) == TextDirection.RTL

    def test_adapter_is_rtl_check(self, qt_adapter: QtTranslationAdapter):
        """Test that adapter correctly identifies RTL languages."""
        # English is not RTL
        assert qt_adapter.is_rtl(Language.ENGLISH) is False

        # Arabic is RTL
        assert qt_adapter.is_rtl(Language.ARABIC) is True

    def test_adapter_get_qt_layout_direction(self, qt_adapter: QtTranslationAdapter):
        """Test that adapter converts domain direction to Qt direction."""
        # English → LeftToRight
        assert qt_adapter.get_qt_layout_direction(Language.ENGLISH) == Qt.LayoutDirection.LeftToRight

        # Arabic → RightToLeft
        assert qt_adapter.get_qt_layout_direction(Language.ARABIC) == Qt.LayoutDirection.RightToLeft

    def test_translation_with_parameters(self, qt_adapter: QtTranslationAdapter):
        """Test that adapter interpolates translation parameters."""
        # Change to English
        qt_adapter.change_language(Language.ENGLISH)

        # Test parameter interpolation (if translations support it)
        # Note: This requires validation.min_length key in translations
        result = qt_adapter.translate("validation.min_length", min=5)
        assert "5" in result  # Should contain the interpolated value

    def test_adapter_persists_language_choice(
        self, qapp: QApplication, translation_service: JsonTranslationService
    ):
        """Test that language choice persists across adapter instances."""
        # Create first adapter, set language
        adapter1 = QtTranslationAdapter(translation_service, qapp)
        adapter1.change_language(Language.ARABIC)

        # Create second adapter, should have same language
        adapter2 = QtTranslationAdapter(translation_service, qapp)
        assert adapter2.get_current_language() == Language.ARABIC

    def test_full_i18n_workflow(
        self, qapp: QApplication, qt_adapter: QtTranslationAdapter
    ):
        """Test complete i18n workflow from user perspective.

        Simulates user:
        1. Opening app (default language)
        2. Changing to Arabic in settings
        3. Verifying UI updates
        4. Changing back to English
        """
        # Step 1: Default language (English)
        initial_language = qt_adapter.get_current_language()
        assert initial_language == Language.ENGLISH

        # Step 2: User opens settings, changes to Arabic
        signal_spy = Mock()
        qt_adapter.language_changed.connect(signal_spy)
        qt_adapter.change_language(Language.ARABIC)

        # Step 3: Verify UI updates
        assert qt_adapter.get_current_language() == Language.ARABIC
        assert qapp.layoutDirection() == Qt.LayoutDirection.RightToLeft
        assert qt_adapter.translate("menu.file") == "ملف"
        signal_spy.assert_called_once_with(Language.ARABIC)

        # Step 4: User changes back to English
        signal_spy.reset_mock()
        qt_adapter.change_language(Language.ENGLISH)

        # Verify
        assert qt_adapter.get_current_language() == Language.ENGLISH
        assert qapp.layoutDirection() == Qt.LayoutDirection.LeftToRight
        assert qt_adapter.translate("menu.file") == "File"
        signal_spy.assert_called_once_with(Language.ENGLISH)

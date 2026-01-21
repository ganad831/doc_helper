"""End-to-end workflow test for internationalization (i18n).

WORKFLOW 4: i18n Workflow (Language Switching & RTL Layout)
===========================================================

Tests complete i18n workflow from user perspective:
1. User opens app (default language: English)
2. User changes to Arabic in settings
3. Verify translations update
4. Verify layout direction changes to RTL
5. User changes back to English
6. Verify layout returns to LTR

This test exercises:
- Language switching via QtTranslationAdapter
- Translation loading via JsonTranslationService
- RTL layout via QApplication.layoutDirection()
- Signal emissions for UI updates
- Translation key resolution

RULES:
- E2E tests use REAL repositories (not mocks)
- E2E tests verify complete workflows end-to-end
- E2E tests exercise full stack: Domain → Application → Infrastructure → Presentation
"""

import sys
from pathlib import Path
from uuid import uuid4

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from doc_helper.domain.common.i18n import Language, TextDirection
from doc_helper.infrastructure.i18n.json_translation_service import (
    JsonTranslationService,
)
from doc_helper.application.services.translation_service import (
    TranslationApplicationService,
)
from doc_helper.application.dto.i18n_dto import LanguageDTO, TextDirectionDTO
from doc_helper.presentation.adapters.qt_translation_adapter import QtTranslationAdapter


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests (module scope to avoid multiple instances).

    NOTE: QApplication is a singleton - only one instance per process.
    Attempting to create multiple will raise RuntimeError.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't quit - other tests might need it


@pytest.fixture
def json_translation_service() -> JsonTranslationService:
    """Create real JSON translation service (infrastructure layer).

    NOTE: Uses REAL translation files from translations/ directory.
    This is an E2E test, not an integration test with mocks.
    """
    translations_dir = Path("translations")
    return JsonTranslationService(translations_dir=translations_dir)


@pytest.fixture
def translation_app_service(json_translation_service: JsonTranslationService) -> TranslationApplicationService:
    """Create translation application service (application layer).

    Wraps JSON translation service with DTO-based interface.
    Presentation layer uses this service, not the domain service directly.
    """
    return TranslationApplicationService(json_translation_service)


@pytest.fixture
def qt_adapter(qapp: QApplication, translation_app_service: TranslationApplicationService) -> QtTranslationAdapter:
    """Create QtTranslationAdapter with real dependencies.

    This adapter bridges application layer translation service to Qt UI updates.

    Architecture layers:
    - Infrastructure: JsonTranslationService (loads JSON files)
    - Application: TranslationApplicationService (DTO-based wrapper)
    - Presentation: QtTranslationAdapter (Qt signal bridge)
    """
    return QtTranslationAdapter(translation_app_service, qapp)


class TestI18nWorkflow:
    """End-to-end workflow tests for internationalization.

    These tests verify complete user workflows involving language switching,
    translation updates, and RTL layout changes.
    """

    def test_workflow_4a_language_switching_english_to_arabic(
        self,
        qapp: QApplication,
        qt_adapter: QtTranslationAdapter,
    ):
        """E2E Workflow 4a: User switches from English to Arabic.

        User Actions:
        1. Open app (default language: English)
        2. Open settings dialog
        3. Change language to Arabic
        4. Verify UI updates:
           - Layout direction changes to RTL
           - Menu translations display in Arabic
           - Current language is Arabic

        Verification Points:
        - QApplication.layoutDirection() == RightToLeft
        - Translations display in Arabic
        - Language change signal emitted
        - Layout direction change signal emitted
        """
        # ============================================================
        # STEP 1: Verify Initial State (English, LTR)
        # ============================================================

        # User opens app - default language should be English
        initial_language = qt_adapter.get_current_language()
        assert initial_language == LanguageDTO.ENGLISH, (
            f"Expected default language ENGLISH, got {initial_language}"
        )

        # Layout direction should be LTR for English
        initial_direction = qapp.layoutDirection()
        assert initial_direction == Qt.LayoutDirection.LeftToRight, (
            f"Expected LTR for English, got {initial_direction}"
        )

        # Verify English translations load
        file_menu = qt_adapter.translate("menu.file")
        assert file_menu == "File", f"Expected 'File', got '{file_menu}'"

        edit_menu = qt_adapter.translate("menu.edit")
        assert edit_menu == "Edit", f"Expected 'Edit', got '{edit_menu}'"

        # ============================================================
        # STEP 2: User Changes to Arabic in Settings
        # ============================================================

        # Track signal emissions
        language_changed_called = []
        layout_changed_called = []

        def on_language_changed(lang_code: str):
            language_changed_called.append(lang_code)

        def on_layout_changed(direction: Qt.LayoutDirection):
            layout_changed_called.append(direction)

        qt_adapter.language_changed.connect(on_language_changed)
        qt_adapter.layout_direction_changed.connect(on_layout_changed)

        # User selects Arabic in settings dialog
        qt_adapter.change_language(LanguageDTO.ARABIC)

        # ============================================================
        # STEP 3: Verify UI Updates to Arabic (RTL)
        # ============================================================

        # Current language should be Arabic
        current_language = qt_adapter.get_current_language()
        assert current_language == LanguageDTO.ARABIC, (
            f"Expected ARABIC after change, got {current_language}"
        )

        # Layout direction should change to RTL
        current_direction = qapp.layoutDirection()
        assert current_direction == Qt.LayoutDirection.RightToLeft, (
            f"Expected RTL for Arabic, got {current_direction}"
        )

        # Verify Arabic translations display
        file_menu_ar = qt_adapter.translate("menu.file")
        assert file_menu_ar == "ملف", f"Expected 'ملف', got '{file_menu_ar}'"

        edit_menu_ar = qt_adapter.translate("menu.edit")
        assert edit_menu_ar == "تحرير", f"Expected 'تحرير', got '{edit_menu_ar}'"

        save_project_ar = qt_adapter.translate("menu.file.save")
        assert save_project_ar == "حفظ المشروع", (
            f"Expected 'حفظ المشروع', got '{save_project_ar}'"
        )

        # Verify signals were emitted (signal emits language code as string)
        assert len(language_changed_called) == 1, (
            f"Expected 1 language_changed signal, got {len(language_changed_called)}"
        )
        assert language_changed_called[0] == "ar"  # Language code

        assert len(layout_changed_called) == 1, (
            f"Expected 1 layout_direction_changed signal, got {len(layout_changed_called)}"
        )
        assert layout_changed_called[0] == Qt.LayoutDirection.RightToLeft

    def test_workflow_4b_language_switching_arabic_to_english(
        self,
        qapp: QApplication,
        qt_adapter: QtTranslationAdapter,
    ):
        """E2E Workflow 4b: User switches from Arabic back to English.

        User Actions:
        1. Start with Arabic (from previous workflow or settings)
        2. Open settings dialog
        3. Change language to English
        4. Verify UI updates:
           - Layout direction changes to LTR
           - Menu translations display in English
           - Current language is English

        Verification Points:
        - QApplication.layoutDirection() == LeftToRight
        - Translations display in English
        - Language change signal emitted
        - Layout direction change signal emitted
        """
        # ============================================================
        # STEP 1: Set Initial State to Arabic
        # ============================================================

        qt_adapter.change_language(LanguageDTO.ARABIC)

        # Verify Arabic is active
        assert qt_adapter.get_current_language() == LanguageDTO.ARABIC
        assert qapp.layoutDirection() == Qt.LayoutDirection.RightToLeft

        # ============================================================
        # STEP 2: User Changes to English in Settings
        # ============================================================

        # Track signal emissions
        language_changed_called = []
        layout_changed_called = []

        def on_language_changed(lang_code: str):
            language_changed_called.append(lang_code)

        def on_layout_changed(direction: Qt.LayoutDirection):
            layout_changed_called.append(direction)

        qt_adapter.language_changed.connect(on_language_changed)
        qt_adapter.layout_direction_changed.connect(on_layout_changed)

        # User selects English in settings dialog
        qt_adapter.change_language(LanguageDTO.ENGLISH)

        # ============================================================
        # STEP 3: Verify UI Updates to English (LTR)
        # ============================================================

        # Current language should be English
        current_language = qt_adapter.get_current_language()
        assert current_language == LanguageDTO.ENGLISH, (
            f"Expected ENGLISH after change, got {current_language}"
        )

        # Layout direction should change to LTR
        current_direction = qapp.layoutDirection()
        assert current_direction == Qt.LayoutDirection.LeftToRight, (
            f"Expected LTR for English, got {current_direction}"
        )

        # Verify English translations display
        file_menu = qt_adapter.translate("menu.file")
        assert file_menu == "File", f"Expected 'File', got '{file_menu}'"

        edit_menu = qt_adapter.translate("menu.edit")
        assert edit_menu == "Edit", f"Expected 'Edit', got '{edit_menu}'"

        # Verify signals were emitted (signal emits language code as string)
        assert len(language_changed_called) == 1, (
            f"Expected 1 language_changed signal, got {len(language_changed_called)}"
        )
        assert language_changed_called[0] == "en"  # Language code

        assert len(layout_changed_called) == 1, (
            f"Expected 1 layout_direction_changed signal, got {len(layout_changed_called)}"
        )
        assert layout_changed_called[0] == Qt.LayoutDirection.LeftToRight

    def test_workflow_4c_text_direction_helpers(
        self,
        qt_adapter: QtTranslationAdapter,
        translation_app_service: TranslationApplicationService,
    ):
        """E2E Workflow 4c: Verify text direction helper methods.

        User Actions:
        1. Check text direction for languages via application service

        Verification Points:
        - English → LTR
        - Arabic → RTL

        NOTE: QtTranslationAdapter doesn't expose get_qt_layout_direction() or is_rtl().
        These are internal implementation details. We test via TranslationApplicationService.
        """
        # ============================================================
        # STEP 1: Verify Text Direction for English
        # ============================================================

        english_direction = translation_app_service.get_text_direction(LanguageDTO.ENGLISH)
        assert english_direction == TextDirectionDTO.LTR, (
            f"Expected LTR for English, got {english_direction}"
        )

        # ============================================================
        # STEP 2: Verify Text Direction for Arabic
        # ============================================================

        arabic_direction = translation_app_service.get_text_direction(LanguageDTO.ARABIC)
        assert arabic_direction == TextDirectionDTO.RTL, (
            f"Expected RTL for Arabic, got {arabic_direction}"
        )

    def test_workflow_4d_translation_parameter_interpolation(
        self,
        qt_adapter: QtTranslationAdapter,
    ):
        """E2E Workflow 4d: Verify translation with parameter interpolation.

        User Actions:
        1. Set language to English
        2. Translate key with parameters
        3. Verify parameters are interpolated

        Verification Points:
        - Parameters replaced in translation string
        - Translation maintains structure with parameters

        NOTE: This test assumes validation.min_length exists in translations.
        If not, it will test basic parameter passing mechanism.
        """
        # ============================================================
        # STEP 1: Set Language to English
        # ============================================================

        qt_adapter.change_language(LanguageDTO.ENGLISH)

        # ============================================================
        # STEP 2: Translate with Parameters
        # ============================================================

        # Test parameter interpolation (if translations support it)
        result = qt_adapter.translate("validation.min_length", min=5)

        # Verify parameter was interpolated
        assert "5" in result, (
            f"Expected '5' in result '{result}' from parameter interpolation"
        )

    def test_workflow_4e_translation_key_existence_check(
        self,
        translation_app_service: TranslationApplicationService,
    ):
        """E2E Workflow 4e: Verify translation key existence checking.

        User Actions:
        1. Check if translation keys exist
        2. Verify behavior for missing keys

        Verification Points:
        - has_translation() returns True for existing keys
        - has_translation() returns False for missing keys
        """
        # ============================================================
        # STEP 1: Check Existing Translation Keys
        # ============================================================

        # Check English translations
        assert translation_app_service.has_translation("menu.file", LanguageDTO.ENGLISH) is True
        assert translation_app_service.has_translation("menu.edit", LanguageDTO.ENGLISH) is True
        assert translation_app_service.has_translation("menu.file.save", LanguageDTO.ENGLISH) is True

        # Check Arabic translations
        assert translation_app_service.has_translation("menu.file", LanguageDTO.ARABIC) is True
        assert translation_app_service.has_translation("menu.edit", LanguageDTO.ARABIC) is True
        assert translation_app_service.has_translation("menu.file.save", LanguageDTO.ARABIC) is True

        # ============================================================
        # STEP 2: Check Non-Existent Translation Keys
        # ============================================================

        # These keys should not exist
        assert translation_app_service.has_translation("menu.nonexistent", LanguageDTO.ENGLISH) is False
        assert translation_app_service.has_translation("invalid.key", LanguageDTO.ARABIC) is False
        assert translation_app_service.has_translation("foo.bar.baz", LanguageDTO.ENGLISH) is False

    def test_workflow_4f_full_language_switching_cycle(
        self,
        qapp: QApplication,
        qt_adapter: QtTranslationAdapter,
    ):
        """E2E Workflow 4f: Complete language switching cycle.

        This test simulates a user's complete journey through language settings:
        1. App opens with default language (English)
        2. User switches to Arabic (observes RTL layout)
        3. User switches back to English (observes LTR layout)
        4. Verify all state is consistent

        Verification Points:
        - Language and layout direction stay in sync
        - Translations update correctly on each switch
        - No residual state from previous language
        - Signals emitted for each change
        """
        # ============================================================
        # STEP 1: Verify Default State (English, LTR)
        # ============================================================

        initial_language = qt_adapter.get_current_language()
        assert initial_language == LanguageDTO.ENGLISH

        initial_direction = qapp.layoutDirection()
        assert initial_direction == Qt.LayoutDirection.LeftToRight

        initial_translation = qt_adapter.translate("menu.file")
        assert initial_translation == "File"

        # ============================================================
        # STEP 2: User Switches to Arabic
        # ============================================================

        signal_count_lang = []
        signal_count_layout = []

        qt_adapter.language_changed.connect(lambda lang_code: signal_count_lang.append(lang_code))
        qt_adapter.layout_direction_changed.connect(lambda dir: signal_count_layout.append(dir))

        qt_adapter.change_language(LanguageDTO.ARABIC)

        # Verify Arabic state
        assert qt_adapter.get_current_language() == LanguageDTO.ARABIC
        assert qapp.layoutDirection() == Qt.LayoutDirection.RightToLeft
        assert qt_adapter.translate("menu.file") == "ملف"

        # Verify signals emitted (signal emits language code as string)
        assert len(signal_count_lang) == 1
        assert signal_count_lang[0] == "ar"  # Language code
        assert len(signal_count_layout) == 1
        assert signal_count_layout[0] == Qt.LayoutDirection.RightToLeft

        # ============================================================
        # STEP 3: User Switches Back to English
        # ============================================================

        signal_count_lang.clear()
        signal_count_layout.clear()

        qt_adapter.change_language(LanguageDTO.ENGLISH)

        # Verify English state restored
        assert qt_adapter.get_current_language() == LanguageDTO.ENGLISH
        assert qapp.layoutDirection() == Qt.LayoutDirection.LeftToRight
        assert qt_adapter.translate("menu.file") == "File"

        # Verify signals emitted (signal emits language code as string)
        assert len(signal_count_lang) == 1
        assert signal_count_lang[0] == "en"  # Language code
        assert len(signal_count_layout) == 1
        assert signal_count_layout[0] == Qt.LayoutDirection.LeftToRight

        # ============================================================
        # STEP 4: Verify No Residual State
        # ============================================================

        # Switch back to Arabic one more time to ensure no state corruption
        qt_adapter.change_language(LanguageDTO.ARABIC)
        assert qt_adapter.get_current_language() == LanguageDTO.ARABIC
        assert qapp.layoutDirection() == Qt.LayoutDirection.RightToLeft
        assert qt_adapter.translate("menu.edit") == "تحرير"

        # Switch back to English again
        qt_adapter.change_language(LanguageDTO.ENGLISH)
        assert qt_adapter.get_current_language() == LanguageDTO.ENGLISH
        assert qapp.layoutDirection() == Qt.LayoutDirection.LeftToRight
        assert qt_adapter.translate("menu.edit") == "Edit"


# ============================================================
# TEST EXECUTION SUMMARY
# ============================================================
# Run with: pytest tests/e2e/test_i18n_workflow.py -v
#
# Expected output:
# tests/e2e/test_i18n_workflow.py::TestI18nWorkflow::test_workflow_4a_language_switching_english_to_arabic PASSED
# tests/e2e/test_i18n_workflow.py::TestI18nWorkflow::test_workflow_4b_language_switching_arabic_to_english PASSED
# tests/e2e/test_i18n_workflow.py::TestI18nWorkflow::test_workflow_4c_text_direction_helpers PASSED
# tests/e2e/test_i18n_workflow.py::TestI18nWorkflow::test_workflow_4d_translation_parameter_interpolation PASSED
# tests/e2e/test_i18n_workflow.py::TestI18nWorkflow::test_workflow_4e_translation_key_existence_check PASSED
# tests/e2e/test_i18n_workflow.py::TestI18nWorkflow::test_workflow_4f_full_language_switching_cycle PASSED
#
# ============ 6 passed in X.XXs ============

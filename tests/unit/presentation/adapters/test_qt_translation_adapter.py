"""Unit tests for QtTranslationAdapter."""

from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from doc_helper.application.dto.i18n_dto import LanguageDTO, TextDirectionDTO
from doc_helper.application.services.translation_service import TranslationApplicationService
from doc_helper.presentation.adapters.qt_translation_adapter import QtTranslationAdapter


class TestQtTranslationAdapter:
    """Unit tests for QtTranslationAdapter."""

    @pytest.fixture
    def mock_translation_service(self) -> Mock:
        """Create mock translation application service."""
        service = Mock(spec=TranslationApplicationService)
        service.get_current_language.return_value = LanguageDTO.ENGLISH
        service.translate.return_value = "Translated text"
        service.has_translation.return_value = True

        # Make get_text_direction return correct value based on language
        def get_text_direction_side_effect(language=None):
            # If no language specified, use current language
            if language is None:
                language = service.get_current_language.return_value
            # Return RTL for Arabic, LTR for others
            if language == LanguageDTO.ARABIC:
                return TextDirectionDTO.RTL
            return TextDirectionDTO.LTR

        service.get_text_direction.side_effect = get_text_direction_side_effect
        return service

    @pytest.fixture
    def mock_app(self) -> Mock:
        """Create mock QApplication."""
        app = Mock(spec=QApplication)
        return app

    @pytest.fixture
    def adapter(self, mock_translation_service: Mock, mock_app: Mock) -> QtTranslationAdapter:
        """Create adapter with mocked dependencies."""
        return QtTranslationAdapter(mock_translation_service, mock_app)

    def test_initialization_sets_initial_layout_direction(
        self, mock_translation_service: Mock, mock_app: Mock
    ):
        """Test that initialization applies layout direction for current language."""
        # Setup: English is LTR
        mock_translation_service.get_current_language.return_value = LanguageDTO.ENGLISH

        # Act
        adapter = QtTranslationAdapter(mock_translation_service, mock_app)

        # Assert: Should set LTR direction
        mock_app.setLayoutDirection.assert_called_once_with(Qt.LayoutDirection.LeftToRight)

    def test_initialization_with_arabic_sets_rtl(
        self, mock_translation_service: Mock, mock_app: Mock
    ):
        """Test that Arabic language triggers RTL layout."""
        # Setup: Arabic is RTL
        mock_translation_service.get_current_language.return_value = LanguageDTO.ARABIC

        # Act
        adapter = QtTranslationAdapter(mock_translation_service, mock_app)

        # Assert: Should set RTL direction
        mock_app.setLayoutDirection.assert_called_once_with(Qt.LayoutDirection.RightToLeft)

    def test_initialization_without_app_uses_instance(
        self, mock_translation_service: Mock
    ):
        """Test that adapter uses QApplication.instance() if app not provided."""
        with patch("doc_helper.presentation.adapters.qt_translation_adapter.QApplication.instance") as mock_instance:
            mock_qapp = Mock()
            mock_instance.return_value = mock_qapp

            # Act
            adapter = QtTranslationAdapter(mock_translation_service)

            # Assert: Should use QApplication.instance()
            mock_qapp.setLayoutDirection.assert_called_once()

    def test_initialization_raises_if_no_qapplication(
        self, mock_translation_service: Mock
    ):
        """Test that adapter raises error if no QApplication exists."""
        with patch("doc_helper.presentation.adapters.qt_translation_adapter.QApplication.instance", return_value=None):
            # Act & Assert
            with pytest.raises(RuntimeError, match="No QApplication instance found"):
                QtTranslationAdapter(mock_translation_service)

    def test_get_current_language_delegates_to_service(
        self, adapter: QtTranslationAdapter, mock_translation_service: Mock
    ):
        """Test that get_current_language delegates to translation service."""
        # Reset mock (adapter initialization calls get_current_language)
        mock_translation_service.get_current_language.reset_mock()

        # Act
        result = adapter.get_current_language()

        # Assert
        mock_translation_service.get_current_language.assert_called_once()
        assert result == LanguageDTO.ENGLISH

    def test_change_language_updates_service(
        self, adapter: QtTranslationAdapter, mock_translation_service: Mock
    ):
        """Test that change_language updates translation service."""
        # Act
        adapter.change_language(LanguageDTO.ARABIC)

        # Assert
        mock_translation_service.set_language.assert_called_once_with(LanguageDTO.ARABIC)

    def test_change_language_applies_rtl_for_arabic(
        self, adapter: QtTranslationAdapter, mock_app: Mock
    ):
        """Test that changing to Arabic applies RTL layout."""
        # Act
        adapter.change_language(LanguageDTO.ARABIC)

        # Assert: Should set RTL (called twice: init + change)
        assert mock_app.setLayoutDirection.call_count == 2
        mock_app.setLayoutDirection.assert_called_with(Qt.LayoutDirection.RightToLeft)

    def test_change_language_applies_ltr_for_english(
        self, mock_translation_service: Mock, mock_app: Mock
    ):
        """Test that changing to English applies LTR layout."""
        # Setup: Start with Arabic
        mock_translation_service.get_current_language.return_value = LanguageDTO.ARABIC
        adapter = QtTranslationAdapter(mock_translation_service, mock_app)

        # Act
        adapter.change_language(LanguageDTO.ENGLISH)

        # Assert: Should set LTR
        mock_app.setLayoutDirection.assert_called_with(Qt.LayoutDirection.LeftToRight)

    def test_change_language_emits_language_changed_signal(
        self, adapter: QtTranslationAdapter
    ):
        """Test that change_language emits language_changed signal."""
        # Arrange
        signal_spy = Mock()
        adapter.language_changed.connect(signal_spy)

        # Act
        adapter.change_language(LanguageDTO.ARABIC)

        # Assert
        signal_spy.assert_called_once_with(LanguageDTO.ARABIC)

    def test_change_language_emits_layout_direction_changed_signal(
        self, adapter: QtTranslationAdapter
    ):
        """Test that change_language emits layout_direction_changed signal."""
        # Arrange
        signal_spy = Mock()
        adapter.layout_direction_changed.connect(signal_spy)

        # Act
        adapter.change_language(LanguageDTO.ARABIC)

        # Assert
        signal_spy.assert_called_once_with(Qt.LayoutDirection.RightToLeft)

    def test_change_language_raises_on_invalid_type(
        self, adapter: QtTranslationAdapter
    ):
        """Test that change_language raises TypeError for non-LanguageDTO argument."""
        # Act & Assert
        with pytest.raises(TypeError, match="language must be LanguageDTO enum"):
            adapter.change_language("ar")  # type: ignore

    def test_translate_uses_current_language(
        self, adapter: QtTranslationAdapter, mock_translation_service: Mock
    ):
        """Test that translate uses current language."""
        # Arrange
        mock_translation_service.translate.return_value = "Open"

        # Act
        result = adapter.translate("menu.file.open")

        # Assert
        mock_translation_service.translate.assert_called_once_with("menu.file.open")
        assert result == "Open"

    def test_translate_with_parameters(
        self, adapter: QtTranslationAdapter, mock_translation_service: Mock
    ):
        """Test that translate interpolates parameters."""
        # Arrange
        mock_translation_service.translate.return_value = "Minimum length is 5 characters"

        # Act
        result = adapter.translate("validation.min_length", min=5)

        # Assert
        mock_translation_service.translate.assert_called_once_with("validation.min_length", min=5)
        assert result == "Minimum length is 5 characters"

    def test_translate_with_language_uses_specified_language(
        self, adapter: QtTranslationAdapter, mock_translation_service: Mock
    ):
        """Test that translate_with_language uses specified language."""
        # Arrange
        mock_translation_service.translate_with_language.return_value = "ملف"

        # Act
        result = adapter.translate_with_language("menu.file", LanguageDTO.ARABIC)

        # Assert
        mock_translation_service.translate_with_language.assert_called_once_with("menu.file", LanguageDTO.ARABIC)
        assert result == "ملف"

    def test_has_translation_delegates_to_service(
        self, adapter: QtTranslationAdapter, mock_translation_service: Mock
    ):
        """Test that has_translation delegates to service."""
        # Arrange
        mock_translation_service.has_translation.return_value = True

        # Act
        result = adapter.has_translation("menu.file.open")

        # Assert
        mock_translation_service.has_translation.assert_called_once_with("menu.file.open", None)
        assert result is True

    def test_has_translation_with_specific_language(
        self, adapter: QtTranslationAdapter, mock_translation_service: Mock
    ):
        """Test that has_translation can check specific language."""
        # Arrange
        mock_translation_service.has_translation.return_value = False

        # Act
        result = adapter.has_translation("menu.file.open", LanguageDTO.ARABIC)

        # Assert
        mock_translation_service.has_translation.assert_called_once_with(
            "menu.file.open", LanguageDTO.ARABIC
        )
        assert result is False

    def test_apply_rtl_to_widget_for_arabic(
        self, adapter: QtTranslationAdapter
    ):
        """Test that apply_rtl_to_widget sets RTL for Arabic."""
        # Arrange
        mock_widget = Mock()

        # Act
        adapter.apply_rtl_to_widget(mock_widget, LanguageDTO.ARABIC)

        # Assert
        mock_widget.setLayoutDirection.assert_called_once_with(
            Qt.LayoutDirection.RightToLeft
        )

    def test_apply_rtl_to_widget_for_english(
        self, adapter: QtTranslationAdapter
    ):
        """Test that apply_rtl_to_widget sets LTR for English."""
        # Arrange
        mock_widget = Mock()

        # Act
        adapter.apply_rtl_to_widget(mock_widget, LanguageDTO.ENGLISH)

        # Assert
        mock_widget.setLayoutDirection.assert_called_once_with(
            Qt.LayoutDirection.LeftToRight
        )

    def test_apply_rtl_to_widget_uses_current_language(
        self, adapter: QtTranslationAdapter, mock_translation_service: Mock
    ):
        """Test that apply_rtl_to_widget uses current language if not specified."""
        # Arrange
        mock_widget = Mock()
        mock_translation_service.get_current_language.return_value = LanguageDTO.ARABIC

        # Act
        adapter.apply_rtl_to_widget(mock_widget)

        # Assert
        mock_widget.setLayoutDirection.assert_called_once_with(
            Qt.LayoutDirection.RightToLeft
        )

    def test_get_text_direction_for_english(
        self, adapter: QtTranslationAdapter
    ):
        """Test that get_text_direction returns LTR for English."""
        # Act
        result = adapter.get_text_direction(LanguageDTO.ENGLISH)

        # Assert
        assert result == TextDirectionDTO.LTR

    def test_get_text_direction_for_arabic(
        self, adapter: QtTranslationAdapter
    ):
        """Test that get_text_direction returns RTL for Arabic."""
        # Act
        result = adapter.get_text_direction(LanguageDTO.ARABIC)

        # Assert
        assert result == TextDirectionDTO.RTL

    def test_get_text_direction_uses_current_language(
        self, adapter: QtTranslationAdapter, mock_translation_service: Mock
    ):
        """Test that get_text_direction uses current language if not specified."""
        # Arrange
        mock_translation_service.get_current_language.return_value = LanguageDTO.ARABIC

        # Act
        result = adapter.get_text_direction()

        # Assert
        assert result == TextDirectionDTO.RTL

    def test_is_rtl_returns_true_for_arabic(
        self, adapter: QtTranslationAdapter
    ):
        """Test that is_rtl returns True for Arabic."""
        # Act
        result = adapter.is_rtl(LanguageDTO.ARABIC)

        # Assert
        assert result is True

    def test_is_rtl_returns_false_for_english(
        self, adapter: QtTranslationAdapter
    ):
        """Test that is_rtl returns False for English."""
        # Act
        result = adapter.is_rtl(LanguageDTO.ENGLISH)

        # Assert
        assert result is False

    def test_get_qt_layout_direction_for_arabic(
        self, adapter: QtTranslationAdapter
    ):
        """Test that get_qt_layout_direction returns RightToLeft for Arabic."""
        # Act
        result = adapter.get_qt_layout_direction(LanguageDTO.ARABIC)

        # Assert
        assert result == Qt.LayoutDirection.RightToLeft

    def test_get_qt_layout_direction_for_english(
        self, adapter: QtTranslationAdapter
    ):
        """Test that get_qt_layout_direction returns LeftToRight for English."""
        # Act
        result = adapter.get_qt_layout_direction(LanguageDTO.ENGLISH)

        # Assert
        assert result == Qt.LayoutDirection.LeftToRight

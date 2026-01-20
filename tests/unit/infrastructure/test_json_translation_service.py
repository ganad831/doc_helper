"""Tests for JSON translation service."""

import json
import tempfile
from pathlib import Path

import pytest

from doc_helper.domain.common.i18n import Language, TranslationKey
from doc_helper.infrastructure.i18n.json_translation_service import (
    JsonTranslationService,
)


@pytest.fixture
def temp_translations_dir(tmp_path):
    """Create temporary translations directory with test files."""
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()

    # English translations
    en_translations = {
        "app": {"name": "Doc Helper", "version": "1.0.0"},
        "menu": {
            "file": "File",
            "file.open": "Open File",
            "edit": "Edit",
        },
        "validation": {
            "required": "This field is required",
            "min_length": "Minimum length is {min} characters",
            "max_value": "Maximum value is {max}",
        },
        "welcome": {"title": "Welcome", "greeting": "Hello {name}!"},
    }

    # Arabic translations
    ar_translations = {
        "app": {"name": "مساعد المستندات", "version": "1.0.0"},
        "menu": {
            "file": "ملف",
            "file.open": "فتح ملف",
            "edit": "تحرير",
        },
        "validation": {
            "required": "هذا الحقل مطلوب",
            "min_length": "الحد الأدنى للطول هو {min} أحرف",
            # max_value intentionally missing to test fallback
        },
        "welcome": {"title": "مرحبا", "greeting": "مرحبا {name}!"},
    }

    # Write translation files
    with open(translations_dir / "en.json", "w", encoding="utf-8") as f:
        json.dump(en_translations, f, ensure_ascii=False, indent=2)

    with open(translations_dir / "ar.json", "w", encoding="utf-8") as f:
        json.dump(ar_translations, f, ensure_ascii=False, indent=2)

    return translations_dir


class TestJsonTranslationService:
    """Tests for JsonTranslationService."""

    def test_create_service_with_valid_directory(self, temp_translations_dir):
        """Test creating service with valid translations directory."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        assert service is not None

    def test_create_service_with_missing_directory(self):
        """Test creating service with non-existent directory raises error."""
        with pytest.raises(FileNotFoundError, match="Translations directory not found"):
            JsonTranslationService(translations_dir=Path("/nonexistent"))

    def test_create_service_with_missing_translation_file(self, tmp_path):
        """Test creating service with missing language file raises error."""
        translations_dir = tmp_path / "translations"
        translations_dir.mkdir()

        # Create only English file, missing Arabic
        with open(translations_dir / "en.json", "w", encoding="utf-8") as f:
            json.dump({"app": {"name": "Test"}}, f)

        with pytest.raises(ValueError, match="Missing translation file"):
            JsonTranslationService(translations_dir=translations_dir)

    def test_get_simple_key_english(self, temp_translations_dir):
        """Test getting simple key in English."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("menu.file")
        result = service.get(key, Language.ENGLISH)
        assert result == "File"

    def test_get_simple_key_arabic(self, temp_translations_dir):
        """Test getting simple key in Arabic."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("menu.file")
        result = service.get(key, Language.ARABIC)
        assert result == "ملف"

    def test_get_nested_key_english(self, temp_translations_dir):
        """Test getting nested key in English."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("menu.file.open")
        result = service.get(key, Language.ENGLISH)
        assert result == "Open File"

    def test_get_nested_key_arabic(self, temp_translations_dir):
        """Test getting nested key in Arabic."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("menu.file.open")
        result = service.get(key, Language.ARABIC)
        assert result == "فتح ملف"

    def test_get_with_parameter_interpolation(self, temp_translations_dir):
        """Test parameter interpolation."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("validation.min_length")
        result = service.get(key, Language.ENGLISH, params={"min": 5})
        assert result == "Minimum length is 5 characters"

    def test_get_with_multiple_parameters(self, temp_translations_dir):
        """Test interpolation with multiple parameters."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("welcome.greeting")
        result = service.get(key, Language.ENGLISH, params={"name": "Alice"})
        assert result == "Hello Alice!"

    def test_get_with_parameter_interpolation_arabic(self, temp_translations_dir):
        """Test parameter interpolation in Arabic."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("validation.min_length")
        result = service.get(key, Language.ARABIC, params={"min": 5})
        assert result == "الحد الأدنى للطول هو 5 أحرف"

    def test_get_with_missing_parameter(self, temp_translations_dir):
        """Test interpolation with missing parameter (graceful degradation)."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("validation.min_length")
        # Missing 'min' parameter
        result = service.get(key, Language.ENGLISH, params={})
        # Should return text with placeholder intact
        assert "{min}" in result

    def test_fallback_to_english_for_missing_key(self, temp_translations_dir):
        """Test fallback to English when key missing in target language."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("validation.max_value")
        # Key exists in English but not in Arabic
        result = service.get(key, Language.ARABIC)
        # Should fallback to English
        assert result == "Maximum value is {max}"

    def test_return_key_when_not_found_in_any_language(self, temp_translations_dir):
        """Test returning key itself when not found (graceful degradation)."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("nonexistent.key")
        result = service.get(key, Language.ENGLISH)
        # Should return key as fallback
        assert result == "nonexistent.key"

    def test_has_key_returns_true_when_exists(self, temp_translations_dir):
        """Test has_key returns True for existing key."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("menu.file")
        assert service.has_key(key, Language.ENGLISH) is True
        assert service.has_key(key, Language.ARABIC) is True

    def test_has_key_returns_false_when_missing(self, temp_translations_dir):
        """Test has_key returns False for missing key."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("nonexistent.key")
        assert service.has_key(key, Language.ENGLISH) is False
        assert service.has_key(key, Language.ARABIC) is False

    def test_has_key_language_specific(self, temp_translations_dir):
        """Test has_key is language-specific."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        key = TranslationKey("validation.max_value")
        # Exists in English but not Arabic
        assert service.has_key(key, Language.ENGLISH) is True
        assert service.has_key(key, Language.ARABIC) is False

    def test_get_current_language_default(self, temp_translations_dir):
        """Test default current language is English."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        assert service.get_current_language() == Language.ENGLISH

    def test_set_language(self, temp_translations_dir):
        """Test setting current language."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        service.set_language(Language.ARABIC)
        assert service.get_current_language() == Language.ARABIC

    def test_translate_convenience_method(self, temp_translations_dir):
        """Test translate convenience method uses current language."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)

        # Default is English
        result = service.translate("menu.file")
        assert result == "File"

        # Switch to Arabic
        service.set_language(Language.ARABIC)
        result = service.translate("menu.file")
        assert result == "ملف"

    def test_thread_safety_language_switching(self, temp_translations_dir):
        """Test language switching is thread-safe."""
        import threading

        service = JsonTranslationService(translations_dir=temp_translations_dir)
        errors = []

        def switch_language(language):
            try:
                for _ in range(100):
                    service.set_language(language)
                    current = service.get_current_language()
                    # Current should always be a valid Language
                    assert isinstance(current, Language)
            except Exception as e:
                errors.append(e)

        # Start multiple threads switching languages concurrently
        threads = [
            threading.Thread(target=switch_language, args=(Language.ENGLISH,))
            for _ in range(5)
        ] + [
            threading.Thread(target=switch_language, args=(Language.ARABIC,))
            for _ in range(5)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # No errors should occur
        assert len(errors) == 0

    def test_nested_structure_deep_lookup(self, temp_translations_dir):
        """Test deep nested structure lookup."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        # app.name is nested under "app"
        key = TranslationKey("app.name")
        result = service.get(key, Language.ENGLISH)
        assert result == "Doc Helper"

    def test_direct_key_with_dot_in_name(self, temp_translations_dir):
        """Test keys with dots in them (direct lookup)."""
        service = JsonTranslationService(translations_dir=temp_translations_dir)
        # "file.open" is a direct key under "menu", not nested
        key = TranslationKey("menu.file.open")
        result = service.get(key, Language.ENGLISH)
        assert result == "Open File"

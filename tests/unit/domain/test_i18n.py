"""Tests for i18n value objects."""

import pytest

from doc_helper.domain.common.i18n import Language, TextDirection, TranslationKey


class TestLanguage:
    """Tests for Language enum."""

    def test_language_codes(self) -> None:
        """Language should have correct codes."""
        assert Language.ENGLISH.code == "en"
        assert Language.ARABIC.code == "ar"

    def test_language_display_names(self) -> None:
        """Language should have display names."""
        assert Language.ENGLISH.display_name == "English"
        assert Language.ARABIC.display_name == "العربية"

    def test_language_text_direction(self) -> None:
        """Language should have correct text direction."""
        assert Language.ENGLISH.text_direction == TextDirection.LTR
        assert Language.ARABIC.text_direction == TextDirection.RTL

    def test_from_code_valid(self) -> None:
        """from_code should return Language for valid code."""
        assert Language.from_code("en") == Language.ENGLISH
        assert Language.from_code("ar") == Language.ARABIC

    def test_from_code_invalid(self) -> None:
        """from_code should raise ValueError for invalid code."""
        with pytest.raises(ValueError, match="Unsupported language code"):
            Language.from_code("fr")


class TestTextDirection:
    """Tests for TextDirection enum."""

    def test_ltr_direction(self) -> None:
        """TextDirection LTR should be left-to-right."""
        direction = TextDirection.LTR
        assert direction.is_ltr()
        assert not direction.is_rtl()

    def test_rtl_direction(self) -> None:
        """TextDirection RTL should be right-to-left."""
        direction = TextDirection.RTL
        assert direction.is_rtl()
        assert not direction.is_ltr()


class TestTranslationKey:
    """Tests for TranslationKey value object."""

    def test_valid_key(self) -> None:
        """TranslationKey should accept valid key."""
        key = TranslationKey("validation.required")
        assert key.key == "validation.required"
        assert str(key) == "validation.required"

    def test_empty_key_raises(self) -> None:
        """TranslationKey should reject empty key."""
        with pytest.raises(ValueError, match="cannot be empty"):
            TranslationKey("")

    def test_invalid_characters_raises(self) -> None:
        """TranslationKey should reject invalid characters."""
        with pytest.raises(ValueError, match="invalid characters"):
            TranslationKey("validation@required")

    def test_key_with_underscore(self) -> None:
        """TranslationKey should accept underscores."""
        key = TranslationKey("validation_error.min_length")
        assert key.key == "validation_error.min_length"

    def test_key_with_hyphen(self) -> None:
        """TranslationKey should accept hyphens."""
        key = TranslationKey("menu.file-operations.open")
        assert key.key == "menu.file-operations.open"

    def test_key_equality(self) -> None:
        """TranslationKey should compare by value."""
        key1 = TranslationKey("validation.required")
        key2 = TranslationKey("validation.required")
        key3 = TranslationKey("validation.optional")

        assert key1 == key2
        assert key1 != key3

    def test_key_immutability(self) -> None:
        """TranslationKey should be immutable."""
        key = TranslationKey("validation.required")
        with pytest.raises(AttributeError):
            key.key = "changed"  # type: ignore

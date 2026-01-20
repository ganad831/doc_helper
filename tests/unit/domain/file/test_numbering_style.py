"""Unit tests for NumberingStyle value object."""

import pytest

from doc_helper.domain.file.value_objects.numbering_style import NumberingStyle


class TestNumberingStyleArabic:
    """Test ARABIC numbering style."""

    def test_format_arabic_numbers(self):
        """Test Arabic number formatting."""
        style = NumberingStyle.ARABIC

        assert style.format(1) == "1"
        assert style.format(5) == "5"
        assert style.format(10) == "10"
        assert style.format(100) == "100"
        assert style.format(999) == "999"

    def test_display_name(self):
        """Test display name for Arabic style."""
        style = NumberingStyle.ARABIC
        assert style.display_name == "1, 2, 3"


class TestNumberingStyleRoman:
    """Test Roman numeral styles."""

    def test_format_roman_upper(self):
        """Test uppercase Roman numerals."""
        style = NumberingStyle.ROMAN_UPPER

        assert style.format(1) == "I"
        assert style.format(2) == "II"
        assert style.format(3) == "III"
        assert style.format(4) == "IV"
        assert style.format(5) == "V"
        assert style.format(6) == "VI"
        assert style.format(9) == "IX"
        assert style.format(10) == "X"
        assert style.format(40) == "XL"
        assert style.format(50) == "L"
        assert style.format(90) == "XC"
        assert style.format(100) == "C"
        assert style.format(400) == "CD"
        assert style.format(500) == "D"
        assert style.format(900) == "CM"
        assert style.format(1000) == "M"
        assert style.format(1984) == "MCMLXXXIV"
        assert style.format(3999) == "MMMCMXCIX"

    def test_format_roman_lower(self):
        """Test lowercase Roman numerals."""
        style = NumberingStyle.ROMAN_LOWER

        assert style.format(1) == "i"
        assert style.format(2) == "ii"
        assert style.format(3) == "iii"
        assert style.format(4) == "iv"
        assert style.format(5) == "v"
        assert style.format(10) == "x"
        assert style.format(50) == "l"
        assert style.format(100) == "c"
        assert style.format(500) == "d"
        assert style.format(1000) == "m"

    def test_roman_display_names(self):
        """Test display names for Roman styles."""
        assert NumberingStyle.ROMAN_UPPER.display_name == "I, II, III"
        assert NumberingStyle.ROMAN_LOWER.display_name == "i, ii, iii"


class TestNumberingStyleAlpha:
    """Test alphabetic styles."""

    def test_format_alpha_upper(self):
        """Test uppercase alphabetic numbering."""
        style = NumberingStyle.ALPHA_UPPER

        # Single letters
        assert style.format(1) == "A"
        assert style.format(2) == "B"
        assert style.format(3) == "C"
        assert style.format(26) == "Z"

        # Double letters
        assert style.format(27) == "AA"
        assert style.format(28) == "AB"
        assert style.format(52) == "AZ"
        assert style.format(53) == "BA"

        # Triple letters
        assert style.format(702) == "ZZ"
        assert style.format(703) == "AAA"

    def test_format_alpha_lower(self):
        """Test lowercase alphabetic numbering."""
        style = NumberingStyle.ALPHA_LOWER

        # Single letters
        assert style.format(1) == "a"
        assert style.format(2) == "b"
        assert style.format(3) == "c"
        assert style.format(26) == "z"

        # Double letters
        assert style.format(27) == "aa"
        assert style.format(28) == "ab"
        assert style.format(52) == "az"
        assert style.format(53) == "ba"

    def test_alpha_display_names(self):
        """Test display names for alphabetic styles."""
        assert NumberingStyle.ALPHA_UPPER.display_name == "A, B, C"
        assert NumberingStyle.ALPHA_LOWER.display_name == "a, b, c"


class TestNumberingStyleValidation:
    """Test validation and error handling."""

    def test_format_rejects_zero(self):
        """Test that number must be >= 1."""
        style = NumberingStyle.ARABIC

        with pytest.raises(ValueError, match="Number must be >= 1"):
            style.format(0)

    def test_format_rejects_negative(self):
        """Test that negative numbers are rejected."""
        style = NumberingStyle.ARABIC

        with pytest.raises(ValueError, match="Number must be >= 1"):
            style.format(-5)


class TestNumberingStyleStringRepresentation:
    """Test string representations."""

    def test_str_representation(self):
        """Test __str__ returns value."""
        assert str(NumberingStyle.ARABIC) == "arabic"
        assert str(NumberingStyle.ROMAN_UPPER) == "roman_upper"
        assert str(NumberingStyle.ALPHA_LOWER) == "alpha_lower"

    def test_repr_representation(self):
        """Test __repr__ returns debug string."""
        assert repr(NumberingStyle.ARABIC) == "NumberingStyle.ARABIC"
        assert repr(NumberingStyle.ROMAN_UPPER) == "NumberingStyle.ROMAN_UPPER"

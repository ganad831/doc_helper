"""Unit tests for NumberingFormat value object."""

import pytest

from doc_helper.domain.file.value_objects.numbering_format import NumberingFormat
from doc_helper.domain.file.value_objects.numbering_style import NumberingStyle


class TestNumberingFormatCreation:
    """Test NumberingFormat creation."""

    def test_create_with_defaults(self):
        """Test creating with default values."""
        format = NumberingFormat()

        assert format.style == NumberingStyle.ARABIC
        assert format.prefix == ""
        assert format.suffix == ""

    def test_create_with_prefix(self):
        """Test creating with prefix."""
        format = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="Fig. ",
            suffix=""
        )

        assert format.prefix == "Fig. "
        assert format.suffix == ""

    def test_create_with_suffix(self):
        """Test creating with suffix."""
        format = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="",
            suffix=")"
        )

        assert format.prefix == ""
        assert format.suffix == ")"

    def test_create_with_prefix_and_suffix(self):
        """Test creating with both prefix and suffix."""
        format = NumberingFormat(
            style=NumberingStyle.ROMAN_UPPER,
            prefix="(",
            suffix=")"
        )

        assert format.prefix == "("
        assert format.suffix == ")"

    def test_create_default_factory(self):
        """Test default() factory method."""
        format = NumberingFormat.default()

        assert format.style == NumberingStyle.ARABIC
        assert format.prefix == ""
        assert format.suffix == ""


class TestNumberingFormatValidation:
    """Test NumberingFormat validation."""

    def test_rejects_invalid_style(self):
        """Test that invalid style is rejected."""
        with pytest.raises(TypeError, match="style must be NumberingStyle"):
            NumberingFormat(
                style="arabic",  # type: ignore
                prefix="",
                suffix=""
            )

    def test_rejects_non_string_prefix(self):
        """Test that non-string prefix is rejected."""
        with pytest.raises(TypeError, match="prefix must be str"):
            NumberingFormat(
                style=NumberingStyle.ARABIC,
                prefix=123,  # type: ignore
                suffix=""
            )

    def test_rejects_non_string_suffix(self):
        """Test that non-string suffix is rejected."""
        with pytest.raises(TypeError, match="suffix must be str"):
            NumberingFormat(
                style=NumberingStyle.ARABIC,
                prefix="",
                suffix=456  # type: ignore
            )


class TestNumberingFormatFormatNumber:
    """Test format_number method."""

    def test_format_arabic_plain(self):
        """Test formatting with plain Arabic style."""
        format = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="",
            suffix=""
        )

        assert format.format_number(1) == "1"
        assert format.format_number(5) == "5"
        assert format.format_number(10) == "10"

    def test_format_with_prefix(self):
        """Test formatting with prefix."""
        format = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="Figure ",
            suffix=""
        )

        assert format.format_number(1) == "Figure 1"
        assert format.format_number(5) == "Figure 5"

    def test_format_with_suffix(self):
        """Test formatting with suffix."""
        format = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="",
            suffix="."
        )

        assert format.format_number(1) == "1."
        assert format.format_number(5) == "5."

    def test_format_with_prefix_and_suffix(self):
        """Test formatting with both prefix and suffix."""
        format = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="Fig. ",
            suffix="."
        )

        assert format.format_number(1) == "Fig. 1."
        assert format.format_number(5) == "Fig. 5."

    def test_format_roman_upper_with_prefix_suffix(self):
        """Test formatting Roman numerals with prefix/suffix."""
        format = NumberingFormat(
            style=NumberingStyle.ROMAN_UPPER,
            prefix="Appendix ",
            suffix=""
        )

        assert format.format_number(1) == "Appendix I"
        assert format.format_number(5) == "Appendix V"
        assert format.format_number(10) == "Appendix X"

    def test_format_alpha_lower_with_parentheses(self):
        """Test formatting alphabetic with parentheses."""
        format = NumberingFormat(
            style=NumberingStyle.ALPHA_LOWER,
            prefix="(",
            suffix=")"
        )

        assert format.format_number(1) == "(a)"
        assert format.format_number(2) == "(b)"
        assert format.format_number(26) == "(z)"
        assert format.format_number(27) == "(aa)"


class TestNumberingFormatStringRepresentation:
    """Test string representations."""

    def test_str_shows_example(self):
        """Test __str__ shows example formatted numbers."""
        format = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="Fig. ",
            suffix="."
        )

        str_repr = str(format)
        assert "Fig. 1." in str_repr
        assert "Fig. 2." in str_repr

    def test_repr_is_debuggable(self):
        """Test __repr__ shows all attributes."""
        format = NumberingFormat(
            style=NumberingStyle.ROMAN_UPPER,
            prefix="(",
            suffix=")"
        )

        repr_str = repr(format)
        assert "NumberingFormat" in repr_str
        assert "ROMAN_UPPER" in repr_str
        assert "'('" in repr_str
        assert "')'" in repr_str


class TestNumberingFormatImmutability:
    """Test NumberingFormat immutability."""

    def test_is_immutable(self):
        """Test that NumberingFormat is frozen."""
        format = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="Fig. ",
            suffix="."
        )

        with pytest.raises(AttributeError):
            format.prefix = "Image "  # type: ignore

    def test_equality(self):
        """Test equality comparison."""
        format1 = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="Fig. ",
            suffix="."
        )
        format2 = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="Fig. ",
            suffix="."
        )
        format3 = NumberingFormat(
            style=NumberingStyle.ROMAN_UPPER,
            prefix="Fig. ",
            suffix="."
        )

        assert format1 == format2
        assert format1 != format3

    def test_hashable(self):
        """Test that NumberingFormat is hashable."""
        format1 = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="Fig. ",
            suffix="."
        )
        format2 = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="Fig. ",
            suffix="."
        )

        # Can be used in sets
        format_set = {format1, format2}
        assert len(format_set) == 1

        # Can be used as dict keys
        format_dict = {format1: "value"}
        assert format_dict[format2] == "value"

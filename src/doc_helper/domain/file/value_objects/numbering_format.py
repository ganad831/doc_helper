"""Numbering format value object."""

from dataclasses import dataclass

from doc_helper.domain.file.value_objects.numbering_style import NumberingStyle


@dataclass(frozen=True)
class NumberingFormat:
    """Format specification for figure numbering.

    Combines numbering style with optional prefix and suffix.
    Used to format a sequence number into its final display form.

    Example:
        format = NumberingFormat(
            style=NumberingStyle.ARABIC,
            prefix="Fig. ",
            suffix=""
        )
        formatted = format.format_number(5)
        assert formatted == "Fig. 5"

        format = NumberingFormat(
            style=NumberingStyle.ROMAN_UPPER,
            prefix="",
            suffix=")"
        )
        formatted = format.format_number(5)
        assert formatted == "V)"
    """

    style: NumberingStyle = NumberingStyle.ARABIC
    prefix: str = ""
    suffix: str = ""

    def __post_init__(self) -> None:
        """Validate numbering format.

        Raises:
            TypeError: If style is not NumberingStyle
            TypeError: If prefix or suffix are not strings
        """
        if not isinstance(self.style, NumberingStyle):
            raise TypeError(f"style must be NumberingStyle, got {type(self.style)}")
        if not isinstance(self.prefix, str):
            raise TypeError(f"prefix must be str, got {type(self.prefix)}")
        if not isinstance(self.suffix, str):
            raise TypeError(f"suffix must be str, got {type(self.suffix)}")

    def format_number(self, sequence: int) -> str:
        """Format a sequence number according to this format.

        Args:
            sequence: 1-based sequence number to format

        Returns:
            Formatted string with prefix + styled number + suffix

        Example:
            format = NumberingFormat(
                style=NumberingStyle.ARABIC,
                prefix="Figure ",
                suffix="."
            )
            assert format.format_number(5) == "Figure 5."
        """
        styled_number = self.style.format(sequence)
        return f"{self.prefix}{styled_number}{self.suffix}"

    @classmethod
    def default(cls) -> "NumberingFormat":
        """Create default numbering format (Arabic, no prefix/suffix).

        Returns:
            Default NumberingFormat instance
        """
        return cls(
            style=NumberingStyle.ARABIC,
            prefix="",
            suffix="",
        )

    def __str__(self) -> str:
        """String representation showing example.

        Returns:
            Example formatted number
        """
        example = self.format_number(1)
        return f"NumberingFormat({example}, {example.replace('1', '2')}, ...)"

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"NumberingFormat("
            f"style={self.style!r}, "
            f"prefix={self.prefix!r}, "
            f"suffix={self.suffix!r})"
        )

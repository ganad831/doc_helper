"""Numbering style value object for figure numbers."""

from enum import Enum


class NumberingStyle(str, Enum):
    """Numbering style for figure numbers.

    Controls how numbers are formatted:
    - ARABIC: 1, 2, 3, 4, ...
    - ROMAN_UPPER: I, II, III, IV, ...
    - ROMAN_LOWER: i, ii, iii, iv, ...
    - ALPHA_UPPER: A, B, C, D, ..., Z, AA, AB, ...
    - ALPHA_LOWER: a, b, c, d, ..., z, aa, ab, ...

    Example:
        style = NumberingStyle.ARABIC
        formatted = style.format(5)
        assert formatted == "5"

        style = NumberingStyle.ROMAN_UPPER
        formatted = style.format(5)
        assert formatted == "V"
    """

    ARABIC = "arabic"
    ROMAN_UPPER = "roman_upper"
    ROMAN_LOWER = "roman_lower"
    ALPHA_UPPER = "alpha_upper"
    ALPHA_LOWER = "alpha_lower"

    def format(self, number: int) -> str:
        """Format a number according to this style.

        Args:
            number: Integer to format (1-based)

        Returns:
            Formatted string

        Raises:
            ValueError: If number is less than 1
        """
        if number < 1:
            raise ValueError(f"Number must be >= 1, got {number}")

        if self == NumberingStyle.ARABIC:
            return str(number)
        elif self == NumberingStyle.ROMAN_UPPER:
            return self._to_roman(number).upper()
        elif self == NumberingStyle.ROMAN_LOWER:
            return self._to_roman(number).lower()
        elif self == NumberingStyle.ALPHA_UPPER:
            return self._to_alpha(number).upper()
        elif self == NumberingStyle.ALPHA_LOWER:
            return self._to_alpha(number).lower()
        else:
            raise ValueError(f"Unknown numbering style: {self}")

    @staticmethod
    def _to_roman(num: int) -> str:
        """Convert integer to Roman numeral.

        Args:
            num: Integer to convert (1-3999)

        Returns:
            Roman numeral string
        """
        val = [
            1000, 900, 500, 400,
            100, 90, 50, 40,
            10, 9, 5, 4,
            1
        ]
        syms = [
            "M", "CM", "D", "CD",
            "C", "XC", "L", "XL",
            "X", "IX", "V", "IV",
            "I"
        ]
        roman_num = ""
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman_num += syms[i]
                num -= val[i]
            i += 1
        return roman_num

    @staticmethod
    def _to_alpha(num: int) -> str:
        """Convert integer to alphabetic sequence.

        Args:
            num: Integer to convert (1-based)

        Returns:
            Alphabetic string (A, B, ..., Z, AA, AB, ...)

        Examples:
            1 -> A
            26 -> Z
            27 -> AA
            28 -> AB
        """
        result = ""
        while num > 0:
            num -= 1  # Convert to 0-based
            result = chr(65 + (num % 26)) + result
            num //= 26
        return result

    @property
    def display_name(self) -> str:
        """Get display name for this style.

        Returns:
            Human-readable name
        """
        names = {
            NumberingStyle.ARABIC: "1, 2, 3",
            NumberingStyle.ROMAN_UPPER: "I, II, III",
            NumberingStyle.ROMAN_LOWER: "i, ii, iii",
            NumberingStyle.ALPHA_UPPER: "A, B, C",
            NumberingStyle.ALPHA_LOWER: "a, b, c",
        }
        return names[self]

    def __str__(self) -> str:
        """String representation (value)."""
        return self.value

    def __repr__(self) -> str:
        """Debug representation."""
        return f"NumberingStyle.{self.name}"

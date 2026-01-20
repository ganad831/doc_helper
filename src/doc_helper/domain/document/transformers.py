"""Built-in transformer implementations.

This module contains all v1 built-in transformers for formatting field values.

Transformers are organized by category:
- Text: uppercase, lowercase, capitalize, title
- Number: number, decimal, integer
- Date: date, datetime, time
- Currency: currency
- Boolean: boolean, yes_no
- String operations: concat, substring, replace
- Conditional: if_empty, if_null, conditional
- Math: add, subtract, multiply, divide

All transformers follow the ITransformer interface.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from doc_helper.domain.document.transformer import BaseTransformer


# ============================================================================
# Text Transformers
# ============================================================================


class UppercaseTransformer(BaseTransformer):
    """Transform text to uppercase.

    Example:
        transformer.transform("hello") → "HELLO"
    """

    @property
    def name(self) -> str:
        return "uppercase"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result
        return str(value).upper()


class LowercaseTransformer(BaseTransformer):
    """Transform text to lowercase.

    Example:
        transformer.transform("HELLO") → "hello"
    """

    @property
    def name(self) -> str:
        return "lowercase"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result
        return str(value).lower()


class CapitalizeTransformer(BaseTransformer):
    """Capitalize first letter of text.

    Example:
        transformer.transform("hello world") → "Hello world"
    """

    @property
    def name(self) -> str:
        return "capitalize"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result
        return str(value).capitalize()


class TitleTransformer(BaseTransformer):
    """Transform text to title case.

    Example:
        transformer.transform("hello world") → "Hello World"
    """

    @property
    def name(self) -> str:
        return "title"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result
        return str(value).title()


# ============================================================================
# Number Transformers
# ============================================================================


class NumberTransformer(BaseTransformer):
    """Format number with optional decimal places and thousands separator.

    Args:
        decimals: Number of decimal places (default: 2)
        thousands_sep: Thousands separator (default: ",")

    Example:
        transformer.transform(1234.5, decimals=2) → "1,234.50"
    """

    @property
    def name(self) -> str:
        return "number"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result

        decimals = kwargs.get("decimals", 2)
        thousands_sep = kwargs.get("thousands_sep", ",")

        try:
            num = float(value)
            # Format with decimals
            formatted = f"{num:,.{decimals}f}"
            # Replace comma with custom separator
            if thousands_sep != ",":
                formatted = formatted.replace(",", thousands_sep)
            return formatted
        except (ValueError, TypeError):
            return self._to_str(value)


class DecimalTransformer(BaseTransformer):
    """Format decimal number.

    Args:
        decimals: Number of decimal places (default: 2)

    Example:
        transformer.transform(123.456, decimals=2) → "123.46"
    """

    @property
    def name(self) -> str:
        return "decimal"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result

        decimals = kwargs.get("decimals", 2)

        try:
            num = Decimal(str(value))
            return f"{num:.{decimals}f}"
        except (ValueError, TypeError):
            return self._to_str(value)


class IntegerTransformer(BaseTransformer):
    """Format as integer (no decimal places).

    Example:
        transformer.transform(123.456) → "123"
    """

    @property
    def name(self) -> str:
        return "integer"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result

        try:
            return str(int(float(value)))
        except (ValueError, TypeError):
            return self._to_str(value)


# ============================================================================
# Date Transformers
# ============================================================================


class DateTransformer(BaseTransformer):
    """Format date value.

    Args:
        format: Date format string (default: "%Y-%m-%d")

    Example:
        transformer.transform(date(2024, 1, 15), format="%d/%m/%Y") → "15/01/2024"
    """

    @property
    def name(self) -> str:
        return "date"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result

        date_format = kwargs.get("format", "%Y-%m-%d")

        if isinstance(value, datetime):
            return value.strftime(date_format)
        elif isinstance(value, date):
            return value.strftime(date_format)
        elif isinstance(value, str):
            # Try to parse string as date
            try:
                dt = datetime.fromisoformat(value)
                return dt.strftime(date_format)
            except ValueError:
                return value

        return self._to_str(value)


class DateTimeTransformer(BaseTransformer):
    """Format datetime value.

    Args:
        format: DateTime format string (default: "%Y-%m-%d %H:%M:%S")

    Example:
        transformer.transform(datetime(2024, 1, 15, 14, 30)) → "2024-01-15 14:30:00"
    """

    @property
    def name(self) -> str:
        return "datetime"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result

        datetime_format = kwargs.get("format", "%Y-%m-%d %H:%M:%S")

        if isinstance(value, datetime):
            return value.strftime(datetime_format)
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return dt.strftime(datetime_format)
            except ValueError:
                return value

        return self._to_str(value)


class TimeTransformer(BaseTransformer):
    """Format time value.

    Args:
        format: Time format string (default: "%H:%M:%S")

    Example:
        transformer.transform(datetime(2024, 1, 15, 14, 30)) → "14:30:00"
    """

    @property
    def name(self) -> str:
        return "time"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result

        time_format = kwargs.get("format", "%H:%M:%S")

        if isinstance(value, datetime):
            return value.strftime(time_format)
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return dt.strftime(time_format)
            except ValueError:
                return value

        return self._to_str(value)


# ============================================================================
# Currency Transformer
# ============================================================================


class CurrencyTransformer(BaseTransformer):
    """Format as currency.

    Args:
        symbol: Currency symbol (default: "$")
        decimals: Decimal places (default: 2)
        position: Symbol position "before" or "after" (default: "before")

    Example:
        transformer.transform(1234.56, symbol="$") → "$1,234.56"
    """

    @property
    def name(self) -> str:
        return "currency"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result

        symbol = kwargs.get("symbol", "$")
        decimals = kwargs.get("decimals", 2)
        position = kwargs.get("position", "before")

        try:
            num = float(value)
            formatted = f"{num:,.{decimals}f}"

            if position == "after":
                return f"{formatted}{symbol}"
            else:
                return f"{symbol}{formatted}"
        except (ValueError, TypeError):
            return self._to_str(value)


# ============================================================================
# Boolean Transformers
# ============================================================================


class BooleanTransformer(BaseTransformer):
    """Format boolean as True/False.

    Example:
        transformer.transform(True) → "True"
        transformer.transform(1) → "True"
        transformer.transform("") → "False"
    """

    @property
    def name(self) -> str:
        return "boolean"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value, "False")
        if result is not None:
            return result

        return "True" if value else "False"


class YesNoTransformer(BaseTransformer):
    """Format boolean as Yes/No.

    Args:
        yes_text: Text for true value (default: "Yes")
        no_text: Text for false value (default: "No")

    Example:
        transformer.transform(True) → "Yes"
        transformer.transform(False) → "No"
    """

    @property
    def name(self) -> str:
        return "yes_no"

    def transform(self, value: Any, **kwargs) -> str:
        yes_text = kwargs.get("yes_text", "Yes")
        no_text = kwargs.get("no_text", "No")

        result = self._handle_none(value, no_text)
        if result is not None:
            return result

        return yes_text if value else no_text


# ============================================================================
# String Operation Transformers
# ============================================================================


class ConcatTransformer(BaseTransformer):
    """Concatenate values with separator.

    Args:
        separator: String to join values (default: " ")
        values: Additional values to concatenate

    Example:
        transformer.transform("Hello", values=["World"], separator=" ") → "Hello World"
    """

    @property
    def name(self) -> str:
        return "concat"

    def transform(self, value: Any, **kwargs) -> str:
        separator = kwargs.get("separator", " ")
        additional_values = kwargs.get("values", [])

        parts = [self._to_str(value)]
        parts.extend([self._to_str(v) for v in additional_values])

        return separator.join(parts)


class SubstringTransformer(BaseTransformer):
    """Extract substring.

    Args:
        start: Start index (default: 0)
        length: Length to extract (default: None = to end)

    Example:
        transformer.transform("Hello World", start=0, length=5) → "Hello"
    """

    @property
    def name(self) -> str:
        return "substring"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result

        start = kwargs.get("start", 0)
        length = kwargs.get("length")

        text = self._to_str(value)

        if length is None:
            return text[start:]
        else:
            return text[start : start + length]


class ReplaceTransformer(BaseTransformer):
    """Replace text.

    Args:
        find: Text to find
        replace: Replacement text

    Example:
        transformer.transform("Hello World", find="World", replace="Python") → "Hello Python"
    """

    @property
    def name(self) -> str:
        return "replace"

    def transform(self, value: Any, **kwargs) -> str:
        result = self._handle_none(value)
        if result is not None:
            return result

        find = kwargs.get("find", "")
        replace_with = kwargs.get("replace", "")

        text = self._to_str(value)
        return text.replace(find, replace_with)


# ============================================================================
# Conditional Transformers
# ============================================================================


class IfEmptyTransformer(BaseTransformer):
    """Return default if value is empty.

    Args:
        default: Default value if empty

    Example:
        transformer.transform("", default="N/A") → "N/A"
        transformer.transform("Hello", default="N/A") → "Hello"
    """

    @property
    def name(self) -> str:
        return "if_empty"

    def transform(self, value: Any, **kwargs) -> str:
        default = kwargs.get("default", "")

        if value is None or (isinstance(value, str) and not value.strip()):
            return default

        return self._to_str(value)


class IfNullTransformer(BaseTransformer):
    """Return default if value is None.

    Args:
        default: Default value if None

    Example:
        transformer.transform(None, default="N/A") → "N/A"
        transformer.transform("Hello", default="N/A") → "Hello"
    """

    @property
    def name(self) -> str:
        return "if_null"

    def transform(self, value: Any, **kwargs) -> str:
        default = kwargs.get("default", "")

        if value is None:
            return default

        return self._to_str(value)


# ============================================================================
# Transformer Registry
# ============================================================================


def get_all_transformers() -> list[BaseTransformer]:
    """Get all built-in transformers.

    Returns:
        List of all transformer instances
    """
    return [
        # Text
        UppercaseTransformer(),
        LowercaseTransformer(),
        CapitalizeTransformer(),
        TitleTransformer(),
        # Number
        NumberTransformer(),
        DecimalTransformer(),
        IntegerTransformer(),
        # Date
        DateTransformer(),
        DateTimeTransformer(),
        TimeTransformer(),
        # Currency
        CurrencyTransformer(),
        # Boolean
        BooleanTransformer(),
        YesNoTransformer(),
        # String operations
        ConcatTransformer(),
        SubstringTransformer(),
        ReplaceTransformer(),
        # Conditional
        IfEmptyTransformer(),
        IfNullTransformer(),
    ]

"""Unit tests for built-in transformers."""

from datetime import date, datetime

import pytest

from doc_helper.domain.document.transformers import (
    BooleanTransformer,
    CapitalizeTransformer,
    ConcatTransformer,
    CurrencyTransformer,
    DateTimeTransformer,
    DateTransformer,
    DecimalTransformer,
    IfEmptyTransformer,
    IfNullTransformer,
    IntegerTransformer,
    LowercaseTransformer,
    NumberTransformer,
    ReplaceTransformer,
    SubstringTransformer,
    TimeTransformer,
    TitleTransformer,
    UppercaseTransformer,
    YesNoTransformer,
)


class TestTextTransformers:
    """Tests for text transformers."""

    def test_uppercase(self) -> None:
        """uppercase should convert to uppercase."""
        transformer = UppercaseTransformer()
        assert transformer.transform("hello") == "HELLO"
        assert transformer.transform("HeLLo") == "HELLO"
        assert transformer.transform("") == ""
        assert transformer.transform(None) == ""

    def test_lowercase(self) -> None:
        """lowercase should convert to lowercase."""
        transformer = LowercaseTransformer()
        assert transformer.transform("HELLO") == "hello"
        assert transformer.transform("HeLLo") == "hello"
        assert transformer.transform("") == ""
        assert transformer.transform(None) == ""

    def test_capitalize(self) -> None:
        """capitalize should capitalize first letter."""
        transformer = CapitalizeTransformer()
        assert transformer.transform("hello world") == "Hello world"
        assert transformer.transform("HELLO") == "Hello"
        assert transformer.transform("") == ""
        assert transformer.transform(None) == ""

    def test_title(self) -> None:
        """title should convert to title case."""
        transformer = TitleTransformer()
        assert transformer.transform("hello world") == "Hello World"
        assert transformer.transform("hello") == "Hello"
        assert transformer.transform("") == ""
        assert transformer.transform(None) == ""


class TestNumberTransformers:
    """Tests for number transformers."""

    def test_number_default(self) -> None:
        """number should format with default decimals."""
        transformer = NumberTransformer()
        assert transformer.transform(1234.5) == "1,234.50"
        assert transformer.transform(1234) == "1,234.00"
        assert transformer.transform(0) == "0.00"

    def test_number_custom_decimals(self) -> None:
        """number should format with custom decimals."""
        transformer = NumberTransformer()
        assert transformer.transform(1234.567, decimals=1) == "1,234.6"
        assert transformer.transform(1234.567, decimals=3) == "1,234.567"

    def test_number_custom_separator(self) -> None:
        """number should format with custom separator."""
        transformer = NumberTransformer()
        assert transformer.transform(1234.5, thousands_sep=" ") == "1 234.50"
        assert transformer.transform(1234.5, thousands_sep=".") == "1.234.50"

    def test_decimal(self) -> None:
        """decimal should format decimal numbers."""
        transformer = DecimalTransformer()
        assert transformer.transform(123.456, decimals=2) == "123.46"
        assert transformer.transform(123.4, decimals=2) == "123.40"
        assert transformer.transform(None) == ""

    def test_integer(self) -> None:
        """integer should format as integer."""
        transformer = IntegerTransformer()
        assert transformer.transform(123.456) == "123"
        assert transformer.transform(123.9) == "123"
        assert transformer.transform(123) == "123"
        assert transformer.transform(None) == ""


class TestDateTransformers:
    """Tests for date/time transformers."""

    def test_date_default_format(self) -> None:
        """date should format with default format."""
        transformer = DateTransformer()
        test_date = date(2024, 1, 15)
        assert transformer.transform(test_date) == "2024-01-15"

    def test_date_custom_format(self) -> None:
        """date should format with custom format."""
        transformer = DateTransformer()
        test_date = date(2024, 1, 15)
        assert transformer.transform(test_date, format="%d/%m/%Y") == "15/01/2024"

    def test_date_from_datetime(self) -> None:
        """date should format datetime objects."""
        transformer = DateTransformer()
        test_datetime = datetime(2024, 1, 15, 14, 30, 45)
        assert transformer.transform(test_datetime) == "2024-01-15"

    def test_date_from_string(self) -> None:
        """date should parse string dates."""
        transformer = DateTransformer()
        assert transformer.transform("2024-01-15") == "2024-01-15"

    def test_datetime(self) -> None:
        """datetime should format datetime."""
        transformer = DateTimeTransformer()
        test_datetime = datetime(2024, 1, 15, 14, 30, 45)
        assert transformer.transform(test_datetime) == "2024-01-15 14:30:45"

    def test_datetime_custom_format(self) -> None:
        """datetime should format with custom format."""
        transformer = DateTimeTransformer()
        test_datetime = datetime(2024, 1, 15, 14, 30)
        assert (
            transformer.transform(test_datetime, format="%d/%m/%Y %H:%M")
            == "15/01/2024 14:30"
        )

    def test_time(self) -> None:
        """time should format time."""
        transformer = TimeTransformer()
        test_datetime = datetime(2024, 1, 15, 14, 30, 45)
        assert transformer.transform(test_datetime) == "14:30:45"


class TestCurrencyTransformer:
    """Tests for currency transformer."""

    def test_currency_default(self) -> None:
        """currency should format with default settings."""
        transformer = CurrencyTransformer()
        assert transformer.transform(1234.56) == "$1,234.56"

    def test_currency_custom_symbol(self) -> None:
        """currency should format with custom symbol."""
        transformer = CurrencyTransformer()
        assert transformer.transform(1234.56, symbol="€") == "€1,234.56"

    def test_currency_after(self) -> None:
        """currency should place symbol after value."""
        transformer = CurrencyTransformer()
        assert transformer.transform(1234.56, position="after") == "1,234.56$"

    def test_currency_custom_decimals(self) -> None:
        """currency should format with custom decimals."""
        transformer = CurrencyTransformer()
        assert transformer.transform(1234.567, decimals=3) == "$1,234.567"


class TestBooleanTransformers:
    """Tests for boolean transformers."""

    def test_boolean(self) -> None:
        """boolean should format as True/False."""
        transformer = BooleanTransformer()
        assert transformer.transform(True) == "True"
        assert transformer.transform(False) == "False"
        assert transformer.transform(1) == "True"
        assert transformer.transform(0) == "False"
        assert transformer.transform("") == "False"
        assert transformer.transform(None) == "False"

    def test_yes_no_default(self) -> None:
        """yes_no should format as Yes/No."""
        transformer = YesNoTransformer()
        assert transformer.transform(True) == "Yes"
        assert transformer.transform(False) == "No"
        assert transformer.transform(1) == "Yes"
        assert transformer.transform(0) == "No"
        assert transformer.transform(None) == "No"

    def test_yes_no_custom(self) -> None:
        """yes_no should use custom text."""
        transformer = YesNoTransformer()
        assert (
            transformer.transform(True, yes_text="Oui", no_text="Non") == "Oui"
        )
        assert (
            transformer.transform(False, yes_text="Oui", no_text="Non") == "Non"
        )


class TestStringOperationTransformers:
    """Tests for string operation transformers."""

    def test_concat(self) -> None:
        """concat should concatenate values."""
        transformer = ConcatTransformer()
        assert transformer.transform("Hello", values=["World"]) == "Hello World"
        assert (
            transformer.transform("A", values=["B", "C"], separator="-") == "A-B-C"
        )

    def test_substring(self) -> None:
        """substring should extract substring."""
        transformer = SubstringTransformer()
        assert transformer.transform("Hello World", start=0, length=5) == "Hello"
        assert transformer.transform("Hello World", start=6) == "World"
        assert transformer.transform("Hello World", start=0, length=100) == "Hello World"

    def test_replace(self) -> None:
        """replace should replace text."""
        transformer = ReplaceTransformer()
        assert (
            transformer.transform("Hello World", find="World", replace="Python")
            == "Hello Python"
        )
        assert transformer.transform("aaa", find="a", replace="b") == "bbb"


class TestConditionalTransformers:
    """Tests for conditional transformers."""

    def test_if_empty(self) -> None:
        """if_empty should return default for empty values."""
        transformer = IfEmptyTransformer()
        assert transformer.transform("", default="N/A") == "N/A"
        assert transformer.transform("   ", default="N/A") == "N/A"
        assert transformer.transform("Hello", default="N/A") == "Hello"
        assert transformer.transform(None, default="N/A") == "N/A"

    def test_if_null(self) -> None:
        """if_null should return default for None."""
        transformer = IfNullTransformer()
        assert transformer.transform(None, default="N/A") == "N/A"
        assert transformer.transform("", default="N/A") == ""
        assert transformer.transform("Hello", default="N/A") == "Hello"


class TestTransformerNames:
    """Tests for transformer name property."""

    def test_all_transformers_have_names(self) -> None:
        """All transformers should have unique names."""
        from doc_helper.domain.document.transformers import get_all_transformers

        transformers = get_all_transformers()
        names = [t.name for t in transformers]

        # Check all names are present
        assert len(names) > 0

        # Check all names are unique
        assert len(names) == len(set(names))

        # Check all names are strings
        assert all(isinstance(name, str) for name in names)

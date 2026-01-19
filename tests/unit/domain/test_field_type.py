"""Tests for FieldType enum."""

import pytest

from doc_helper.domain.schema.field_type import FieldType


class TestFieldType:
    """Tests for FieldType enum."""

    def test_all_12_types_exist(self) -> None:
        """FieldType should have exactly 12 types."""
        all_types = list(FieldType)
        assert len(all_types) == 12

    def test_field_type_values(self) -> None:
        """FieldType should have correct string values."""
        assert FieldType.TEXT.value == "text"
        assert FieldType.TEXTAREA.value == "textarea"
        assert FieldType.NUMBER.value == "number"
        assert FieldType.DATE.value == "date"
        assert FieldType.DROPDOWN.value == "dropdown"
        assert FieldType.CHECKBOX.value == "checkbox"
        assert FieldType.RADIO.value == "radio"
        assert FieldType.CALCULATED.value == "calculated"
        assert FieldType.LOOKUP.value == "lookup"
        assert FieldType.FILE.value == "file"
        assert FieldType.IMAGE.value == "image"
        assert FieldType.TABLE.value == "table"

    def test_display_names(self) -> None:
        """FieldType should have display names."""
        assert FieldType.TEXT.display_name == "Text"
        assert FieldType.TEXTAREA.display_name == "Text Area"
        assert FieldType.NUMBER.display_name == "Number"
        assert FieldType.DATE.display_name == "Date"
        assert FieldType.DROPDOWN.display_name == "Dropdown"
        assert FieldType.CHECKBOX.display_name == "Checkbox"
        assert FieldType.RADIO.display_name == "Radio Button"
        assert FieldType.CALCULATED.display_name == "Calculated"
        assert FieldType.LOOKUP.display_name == "Lookup"
        assert FieldType.FILE.display_name == "File"
        assert FieldType.IMAGE.display_name == "Image"
        assert FieldType.TABLE.display_name == "Table"

    def test_supports_constraints(self) -> None:
        """FieldType should indicate constraint support."""
        # Most fields support constraints
        assert FieldType.TEXT.supports_constraints
        assert FieldType.NUMBER.supports_constraints
        assert FieldType.DATE.supports_constraints

        # Calculated fields don't support constraints (read-only)
        assert not FieldType.CALCULATED.supports_constraints

    def test_is_numeric(self) -> None:
        """FieldType should identify numeric types."""
        assert FieldType.NUMBER.is_numeric
        assert not FieldType.TEXT.is_numeric
        assert not FieldType.DATE.is_numeric

    def test_is_text(self) -> None:
        """FieldType should identify text types."""
        assert FieldType.TEXT.is_text
        assert FieldType.TEXTAREA.is_text
        assert not FieldType.NUMBER.is_text
        assert not FieldType.DATE.is_text

    def test_is_date(self) -> None:
        """FieldType should identify date types."""
        assert FieldType.DATE.is_date
        assert not FieldType.TEXT.is_date
        assert not FieldType.NUMBER.is_date

    def test_is_choice(self) -> None:
        """FieldType should identify choice types."""
        assert FieldType.DROPDOWN.is_choice
        assert FieldType.RADIO.is_choice
        assert not FieldType.TEXT.is_choice
        assert not FieldType.CHECKBOX.is_choice

    def test_is_file(self) -> None:
        """FieldType should identify file types."""
        assert FieldType.FILE.is_file
        assert FieldType.IMAGE.is_file
        assert not FieldType.TEXT.is_file

    def test_is_collection(self) -> None:
        """FieldType should identify collection types."""
        assert FieldType.TABLE.is_collection
        assert not FieldType.TEXT.is_collection
        assert not FieldType.DROPDOWN.is_collection

    def test_from_string_valid(self) -> None:
        """from_string should parse valid field type strings."""
        assert FieldType.from_string("text") == FieldType.TEXT
        assert FieldType.from_string("number") == FieldType.NUMBER
        assert FieldType.from_string("date") == FieldType.DATE
        assert FieldType.from_string("dropdown") == FieldType.DROPDOWN

    def test_from_string_case_insensitive(self) -> None:
        """from_string should be case insensitive."""
        assert FieldType.from_string("TEXT") == FieldType.TEXT
        assert FieldType.from_string("Number") == FieldType.NUMBER
        assert FieldType.from_string("DaTe") == FieldType.DATE

    def test_from_string_invalid(self) -> None:
        """from_string should raise ValueError for invalid types."""
        with pytest.raises(ValueError, match="Invalid field type"):
            FieldType.from_string("invalid")

        with pytest.raises(ValueError, match="Invalid field type"):
            FieldType.from_string("string")

        with pytest.raises(ValueError, match="Invalid field type"):
            FieldType.from_string("")

    def test_field_type_equality(self) -> None:
        """FieldType should support equality comparison."""
        assert FieldType.TEXT == FieldType.TEXT
        assert FieldType.TEXT != FieldType.NUMBER

    def test_field_type_in_collection(self) -> None:
        """FieldType should work in collections."""
        types = {FieldType.TEXT, FieldType.NUMBER, FieldType.DATE}
        assert FieldType.TEXT in types
        assert FieldType.DROPDOWN not in types

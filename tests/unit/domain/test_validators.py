"""Tests for field validators."""

import pytest
from datetime import date, datetime

from doc_helper.domain.validation.constraints import (
    AllowedValuesConstraint,
    FileExtensionConstraint,
    MaxFileSizeConstraint,
    MaxLengthConstraint,
    MaxValueConstraint,
    MinLengthConstraint,
    MinValueConstraint,
    PatternConstraint,
    RequiredConstraint,
)
from doc_helper.domain.validation.validators import (
    CalculatedValidator,
    CheckboxValidator,
    DateValidator,
    DropdownValidator,
    FileValidator,
    ImageValidator,
    LookupValidator,
    NumberValidator,
    RadioValidator,
    TableValidator,
    TextAreaValidator,
    TextValidator,
)


class TestTextValidator:
    """Tests for TextValidator."""

    def test_valid_text(self) -> None:
        """TextValidator should accept valid text."""
        validator = TextValidator()
        result = validator.validate("name", "John Doe")
        assert result.is_valid()

    def test_required_constraint_fail(self) -> None:
        """TextValidator should fail on empty required field."""
        validator = TextValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("name", "")
        assert result.is_invalid()
        assert result.error_count == 1
        assert result.errors[0].constraint_type == "RequiredConstraint"

    def test_required_constraint_pass(self) -> None:
        """TextValidator should pass on non-empty required field."""
        validator = TextValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("name", "John")
        assert result.is_valid()

    def test_min_length_constraint_fail(self) -> None:
        """TextValidator should fail on too-short text."""
        validator = TextValidator(constraints=(MinLengthConstraint(min_length=5),))
        result = validator.validate("name", "Jo")
        assert result.is_invalid()
        assert result.error_count == 1
        assert result.errors[0].constraint_type == "MinLengthConstraint"

    def test_min_length_constraint_pass(self) -> None:
        """TextValidator should pass on long-enough text."""
        validator = TextValidator(constraints=(MinLengthConstraint(min_length=5),))
        result = validator.validate("name", "John Doe")
        assert result.is_valid()

    def test_max_length_constraint_fail(self) -> None:
        """TextValidator should fail on too-long text."""
        validator = TextValidator(constraints=(MaxLengthConstraint(max_length=10),))
        result = validator.validate("name", "This is a very long name")
        assert result.is_invalid()
        assert result.error_count == 1
        assert result.errors[0].constraint_type == "MaxLengthConstraint"

    def test_max_length_constraint_pass(self) -> None:
        """TextValidator should pass on short-enough text."""
        validator = TextValidator(constraints=(MaxLengthConstraint(max_length=10),))
        result = validator.validate("name", "John")
        assert result.is_valid()

    def test_pattern_constraint_fail(self) -> None:
        """TextValidator should fail on pattern mismatch."""
        validator = TextValidator(constraints=(PatternConstraint(pattern=r"^\d{3}-\d{3}-\d{4}$"),))
        result = validator.validate("phone", "123-456")
        assert result.is_invalid()
        assert result.error_count == 1
        assert result.errors[0].constraint_type == "PatternConstraint"

    def test_pattern_constraint_pass(self) -> None:
        """TextValidator should pass on pattern match."""
        validator = TextValidator(constraints=(PatternConstraint(pattern=r"^\d{3}-\d{3}-\d{4}$"),))
        result = validator.validate("phone", "123-456-7890")
        assert result.is_valid()

    def test_multiple_constraints_all_pass(self) -> None:
        """TextValidator should pass all constraints."""
        validator = TextValidator(constraints=(
            RequiredConstraint(),
            MinLengthConstraint(min_length=3),
            MaxLengthConstraint(max_length=10),
        ))
        result = validator.validate("name", "John")
        assert result.is_valid()

    def test_multiple_constraints_multiple_fail(self) -> None:
        """TextValidator should collect multiple errors."""
        validator = TextValidator(constraints=(
            MinLengthConstraint(min_length=5),
            PatternConstraint(pattern=r"^\d+$"),
        ))
        result = validator.validate("field", "abc")
        assert result.is_invalid()
        assert result.error_count == 2

    def test_non_string_value_fails(self) -> None:
        """TextValidator should reject non-string values."""
        validator = TextValidator()
        result = validator.validate("field", 123)
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "TypeCheck"

    def test_empty_non_required_passes(self) -> None:
        """TextValidator should pass empty non-required field."""
        validator = TextValidator(constraints=(MinLengthConstraint(min_length=5),))
        result = validator.validate("field", "")
        assert result.is_valid()


class TestNumberValidator:
    """Tests for NumberValidator."""

    def test_valid_number(self) -> None:
        """NumberValidator should accept valid number."""
        validator = NumberValidator()
        result = validator.validate("age", 25)
        assert result.is_valid()

    def test_valid_float(self) -> None:
        """NumberValidator should accept float."""
        validator = NumberValidator()
        result = validator.validate("price", 19.99)
        assert result.is_valid()

    def test_required_constraint_fail(self) -> None:
        """NumberValidator should fail on None required field."""
        validator = NumberValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("age", None)
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "RequiredConstraint"

    def test_min_value_constraint_fail(self) -> None:
        """NumberValidator should fail on too-small value."""
        validator = NumberValidator(constraints=(MinValueConstraint(min_value=0),))
        result = validator.validate("score", -5)
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "MinValueConstraint"

    def test_min_value_constraint_pass(self) -> None:
        """NumberValidator should pass on acceptable value."""
        validator = NumberValidator(constraints=(MinValueConstraint(min_value=0),))
        result = validator.validate("score", 100)
        assert result.is_valid()

    def test_max_value_constraint_fail(self) -> None:
        """NumberValidator should fail on too-large value."""
        validator = NumberValidator(constraints=(MaxValueConstraint(max_value=100),))
        result = validator.validate("score", 150)
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "MaxValueConstraint"

    def test_max_value_constraint_pass(self) -> None:
        """NumberValidator should pass on acceptable value."""
        validator = NumberValidator(constraints=(MaxValueConstraint(max_value=100),))
        result = validator.validate("score", 50)
        assert result.is_valid()

    def test_non_numeric_value_fails(self) -> None:
        """NumberValidator should reject non-numeric values."""
        validator = NumberValidator()
        result = validator.validate("age", "twenty")
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "TypeCheck"


class TestDateValidator:
    """Tests for DateValidator."""

    def test_valid_date(self) -> None:
        """DateValidator should accept valid date."""
        validator = DateValidator()
        result = validator.validate("birthdate", date(1990, 1, 1))
        assert result.is_valid()

    def test_valid_datetime(self) -> None:
        """DateValidator should accept datetime."""
        validator = DateValidator()
        result = validator.validate("timestamp", datetime(2020, 5, 15, 10, 30))
        assert result.is_valid()

    def test_required_constraint_fail(self) -> None:
        """DateValidator should fail on None required field."""
        validator = DateValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("date", None)
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "RequiredConstraint"

    def test_min_value_constraint_fail(self) -> None:
        """DateValidator should fail on too-early date."""
        min_date = date(2020, 1, 1)
        validator = DateValidator(constraints=(MinValueConstraint(min_value=min_date.toordinal()),))
        result = validator.validate("date", date(2019, 12, 31))
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "MinValueConstraint"

    def test_min_value_constraint_pass(self) -> None:
        """DateValidator should pass on acceptable date."""
        min_date = date(2020, 1, 1)
        validator = DateValidator(constraints=(MinValueConstraint(min_value=min_date.toordinal()),))
        result = validator.validate("date", date(2020, 6, 15))
        assert result.is_valid()

    def test_max_value_constraint_fail(self) -> None:
        """DateValidator should fail on too-late date."""
        max_date = date(2025, 12, 31)
        validator = DateValidator(constraints=(MaxValueConstraint(max_value=max_date.toordinal()),))
        result = validator.validate("date", date(2026, 1, 1))
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "MaxValueConstraint"

    def test_non_date_value_fails(self) -> None:
        """DateValidator should reject non-date values."""
        validator = DateValidator()
        result = validator.validate("date", "2020-01-01")
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "TypeCheck"


class TestDropdownValidator:
    """Tests for DropdownValidator."""

    def test_valid_option(self) -> None:
        """DropdownValidator should accept valid option."""
        validator = DropdownValidator(constraints=(
            AllowedValuesConstraint(allowed_values=("small", "medium", "large")),
        ))
        result = validator.validate("size", "medium")
        assert result.is_valid()

    def test_invalid_option_fails(self) -> None:
        """DropdownValidator should reject invalid option."""
        validator = DropdownValidator(constraints=(
            AllowedValuesConstraint(allowed_values=("small", "medium", "large")),
        ))
        result = validator.validate("size", "extra-large")
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "AllowedValuesConstraint"

    def test_required_constraint_fail(self) -> None:
        """DropdownValidator should fail on empty required field."""
        validator = DropdownValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("size", None)
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "RequiredConstraint"

    def test_empty_non_required_passes(self) -> None:
        """DropdownValidator should pass empty non-required field."""
        validator = DropdownValidator(constraints=(
            AllowedValuesConstraint(allowed_values=("small", "medium")),
        ))
        result = validator.validate("size", None)
        assert result.is_valid()


class TestCheckboxValidator:
    """Tests for CheckboxValidator."""

    def test_checked_checkbox(self) -> None:
        """CheckboxValidator should accept True."""
        validator = CheckboxValidator()
        result = validator.validate("agree", True)
        assert result.is_valid()

    def test_unchecked_checkbox(self) -> None:
        """CheckboxValidator should accept False."""
        validator = CheckboxValidator()
        result = validator.validate("agree", False)
        assert result.is_valid()

    def test_required_constraint_fail(self) -> None:
        """CheckboxValidator should fail on unchecked required field."""
        validator = CheckboxValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("agree", False)
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "RequiredConstraint"

    def test_required_constraint_pass(self) -> None:
        """CheckboxValidator should pass on checked required field."""
        validator = CheckboxValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("agree", True)
        assert result.is_valid()

    def test_non_boolean_value_fails(self) -> None:
        """CheckboxValidator should reject non-boolean values."""
        validator = CheckboxValidator()
        result = validator.validate("agree", "yes")
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "TypeCheck"


class TestRadioValidator:
    """Tests for RadioValidator."""

    def test_valid_option(self) -> None:
        """RadioValidator should accept valid option."""
        validator = RadioValidator(constraints=(
            AllowedValuesConstraint(allowed_values=("yes", "no", "maybe")),
        ))
        result = validator.validate("answer", "yes")
        assert result.is_valid()

    def test_invalid_option_fails(self) -> None:
        """RadioValidator should reject invalid option."""
        validator = RadioValidator(constraints=(
            AllowedValuesConstraint(allowed_values=("yes", "no")),
        ))
        result = validator.validate("answer", "maybe")
        assert result.is_invalid()


class TestCalculatedValidator:
    """Tests for CalculatedValidator."""

    def test_any_value_passes(self) -> None:
        """CalculatedValidator should accept any value."""
        validator = CalculatedValidator()
        result = validator.validate("total", 100)
        assert result.is_valid()

    def test_none_passes(self) -> None:
        """CalculatedValidator should accept None."""
        validator = CalculatedValidator()
        result = validator.validate("total", None)
        assert result.is_valid()


class TestLookupValidator:
    """Tests for LookupValidator."""

    def test_valid_lookup(self) -> None:
        """LookupValidator should accept valid value."""
        validator = LookupValidator()
        result = validator.validate("category_id", 123)
        assert result.is_valid()

    def test_required_constraint_fail(self) -> None:
        """LookupValidator should fail on None required field."""
        validator = LookupValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("category_id", None)
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "RequiredConstraint"


class TestFileValidator:
    """Tests for FileValidator."""

    def test_valid_file_string(self) -> None:
        """FileValidator should accept file path string."""
        validator = FileValidator()
        result = validator.validate("attachment", "document.pdf")
        assert result.is_valid()

    def test_valid_file_metadata(self) -> None:
        """FileValidator should accept file metadata dict."""
        validator = FileValidator()
        result = validator.validate("attachment", {"filename": "document.pdf", "size": 1024})
        assert result.is_valid()

    def test_required_constraint_fail(self) -> None:
        """FileValidator should fail on empty required field."""
        validator = FileValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("attachment", None)
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "RequiredConstraint"

    def test_file_extension_constraint_fail(self) -> None:
        """FileValidator should fail on invalid extension."""
        validator = FileValidator(constraints=(
            FileExtensionConstraint(allowed_extensions=(".pdf", ".docx")),
        ))
        result = validator.validate("attachment", "document.txt")
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "FileExtensionConstraint"

    def test_file_extension_constraint_pass(self) -> None:
        """FileValidator should pass on valid extension."""
        validator = FileValidator(constraints=(
            FileExtensionConstraint(allowed_extensions=(".pdf", ".docx")),
        ))
        result = validator.validate("attachment", "document.pdf")
        assert result.is_valid()

    def test_max_file_size_constraint_fail(self) -> None:
        """FileValidator should fail on too-large file."""
        validator = FileValidator(constraints=(
            MaxFileSizeConstraint(max_size_bytes=1024),
        ))
        result = validator.validate("attachment", {"filename": "large.pdf", "size": 2048})
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "MaxFileSizeConstraint"

    def test_max_file_size_constraint_pass(self) -> None:
        """FileValidator should pass on acceptable file size."""
        validator = FileValidator(constraints=(
            MaxFileSizeConstraint(max_size_bytes=1024),
        ))
        result = validator.validate("attachment", {"filename": "small.pdf", "size": 512})
        assert result.is_valid()


class TestImageValidator:
    """Tests for ImageValidator."""

    def test_valid_image(self) -> None:
        """ImageValidator should accept image file."""
        validator = ImageValidator()
        result = validator.validate("photo", "image.jpg")
        assert result.is_valid()

    def test_image_extension_constraint(self) -> None:
        """ImageValidator should validate image extensions."""
        validator = ImageValidator(constraints=(
            FileExtensionConstraint(allowed_extensions=(".jpg", ".png", ".gif")),
        ))
        result = validator.validate("photo", "image.bmp")
        assert result.is_invalid()


class TestTableValidator:
    """Tests for TableValidator."""

    def test_valid_table(self) -> None:
        """TableValidator should accept list of records."""
        validator = TableValidator()
        result = validator.validate("items", [{"id": 1}, {"id": 2}])
        assert result.is_valid()

    def test_empty_list(self) -> None:
        """TableValidator should accept empty list if not required."""
        validator = TableValidator()
        result = validator.validate("items", [])
        assert result.is_valid()

    def test_required_constraint_fail(self) -> None:
        """TableValidator should fail on empty required table."""
        validator = TableValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("items", [])
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "RequiredConstraint"

    def test_required_constraint_pass(self) -> None:
        """TableValidator should pass on non-empty required table."""
        validator = TableValidator(constraints=(RequiredConstraint(),))
        result = validator.validate("items", [{"id": 1}])
        assert result.is_valid()

    def test_non_list_value_fails(self) -> None:
        """TableValidator should reject non-list values."""
        validator = TableValidator()
        result = validator.validate("items", "not a list")
        assert result.is_invalid()
        assert result.errors[0].constraint_type == "TypeCheck"


class TestTextAreaValidator:
    """Tests for TextAreaValidator."""

    def test_valid_textarea(self) -> None:
        """TextAreaValidator should accept multiline text."""
        validator = TextAreaValidator()
        result = validator.validate("description", "Line 1\nLine 2\nLine 3")
        assert result.is_valid()

    def test_textarea_uses_text_validator_logic(self) -> None:
        """TextAreaValidator should use same validation as TextValidator."""
        validator = TextAreaValidator(constraints=(
            RequiredConstraint(),
            MinLengthConstraint(min_length=10),
        ))
        result = validator.validate("description", "Short")
        assert result.is_invalid()
        assert result.error_count == 1

"""Tests for validation constraints."""

import pytest

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


class TestRequiredConstraint:
    """Tests for RequiredConstraint."""

    def test_required_constraint_creation(self) -> None:
        """RequiredConstraint should be created successfully."""
        constraint = RequiredConstraint()
        assert constraint is not None

    def test_required_constraint_immutable(self) -> None:
        """RequiredConstraint should be immutable."""
        constraint = RequiredConstraint()
        with pytest.raises(AttributeError):
            constraint.new_field = "value"  # type: ignore


class TestMinLengthConstraint:
    """Tests for MinLengthConstraint."""

    def test_valid_min_length(self) -> None:
        """MinLengthConstraint should accept valid min_length."""
        constraint = MinLengthConstraint(min_length=5)
        assert constraint.min_length == 5

    def test_zero_min_length(self) -> None:
        """MinLengthConstraint should accept zero."""
        constraint = MinLengthConstraint(min_length=0)
        assert constraint.min_length == 0

    def test_negative_min_length_raises(self) -> None:
        """MinLengthConstraint should reject negative values."""
        with pytest.raises(ValueError, match="min_length must be >= 0"):
            MinLengthConstraint(min_length=-1)

    def test_min_length_immutable(self) -> None:
        """MinLengthConstraint should be immutable."""
        constraint = MinLengthConstraint(min_length=5)
        with pytest.raises(AttributeError):
            constraint.min_length = 10  # type: ignore


class TestMaxLengthConstraint:
    """Tests for MaxLengthConstraint."""

    def test_valid_max_length(self) -> None:
        """MaxLengthConstraint should accept valid max_length."""
        constraint = MaxLengthConstraint(max_length=100)
        assert constraint.max_length == 100

    def test_negative_max_length_raises(self) -> None:
        """MaxLengthConstraint should reject negative values."""
        with pytest.raises(ValueError, match="max_length must be >= 0"):
            MaxLengthConstraint(max_length=-1)

    def test_max_length_immutable(self) -> None:
        """MaxLengthConstraint should be immutable."""
        constraint = MaxLengthConstraint(max_length=100)
        with pytest.raises(AttributeError):
            constraint.max_length = 200  # type: ignore


class TestMinValueConstraint:
    """Tests for MinValueConstraint."""

    def test_valid_min_value_int(self) -> None:
        """MinValueConstraint should accept integer min_value."""
        constraint = MinValueConstraint(min_value=0)
        assert constraint.min_value == 0

    def test_valid_min_value_float(self) -> None:
        """MinValueConstraint should accept float min_value."""
        constraint = MinValueConstraint(min_value=0.5)
        assert constraint.min_value == 0.5

    def test_negative_min_value(self) -> None:
        """MinValueConstraint should accept negative values."""
        constraint = MinValueConstraint(min_value=-10)
        assert constraint.min_value == -10

    def test_min_value_immutable(self) -> None:
        """MinValueConstraint should be immutable."""
        constraint = MinValueConstraint(min_value=0)
        with pytest.raises(AttributeError):
            constraint.min_value = 100  # type: ignore


class TestMaxValueConstraint:
    """Tests for MaxValueConstraint."""

    def test_valid_max_value_int(self) -> None:
        """MaxValueConstraint should accept integer max_value."""
        constraint = MaxValueConstraint(max_value=100)
        assert constraint.max_value == 100

    def test_valid_max_value_float(self) -> None:
        """MaxValueConstraint should accept float max_value."""
        constraint = MaxValueConstraint(max_value=99.9)
        assert constraint.max_value == 99.9

    def test_max_value_immutable(self) -> None:
        """MaxValueConstraint should be immutable."""
        constraint = MaxValueConstraint(max_value=100)
        with pytest.raises(AttributeError):
            constraint.max_value = 200  # type: ignore


class TestPatternConstraint:
    """Tests for PatternConstraint."""

    def test_valid_pattern(self) -> None:
        """PatternConstraint should accept valid regex pattern."""
        constraint = PatternConstraint(pattern=r"^\d{3}-\d{3}-\d{4}$")
        assert constraint.pattern == r"^\d{3}-\d{3}-\d{4}$"

    def test_pattern_with_description(self) -> None:
        """PatternConstraint should accept optional description."""
        constraint = PatternConstraint(
            pattern=r"^\d{3}$",
            description="Three digits"
        )
        assert constraint.description == "Three digits"

    def test_empty_pattern_raises(self) -> None:
        """PatternConstraint should reject empty pattern."""
        with pytest.raises(ValueError, match="pattern cannot be empty"):
            PatternConstraint(pattern="")

    def test_invalid_regex_raises(self) -> None:
        """PatternConstraint should reject invalid regex."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            PatternConstraint(pattern=r"[invalid(")

    def test_pattern_immutable(self) -> None:
        """PatternConstraint should be immutable."""
        constraint = PatternConstraint(pattern=r"^\d+$")
        with pytest.raises(AttributeError):
            constraint.pattern = r"^[a-z]+$"  # type: ignore


class TestAllowedValuesConstraint:
    """Tests for AllowedValuesConstraint."""

    def test_valid_allowed_values(self) -> None:
        """AllowedValuesConstraint should accept tuple of values."""
        constraint = AllowedValuesConstraint(allowed_values=("small", "medium", "large"))
        assert constraint.allowed_values == ("small", "medium", "large")

    def test_empty_allowed_values_raises(self) -> None:
        """AllowedValuesConstraint should reject empty tuple."""
        with pytest.raises(ValueError, match="allowed_values cannot be empty"):
            AllowedValuesConstraint(allowed_values=())

    def test_non_tuple_raises(self) -> None:
        """AllowedValuesConstraint should reject non-tuple."""
        with pytest.raises(ValueError, match="must be a tuple"):
            AllowedValuesConstraint(allowed_values=["small", "medium"])  # type: ignore

    def test_allowed_values_immutable(self) -> None:
        """AllowedValuesConstraint should be immutable."""
        constraint = AllowedValuesConstraint(allowed_values=("a", "b"))
        with pytest.raises(AttributeError):
            constraint.allowed_values = ("c", "d")  # type: ignore


class TestFileExtensionConstraint:
    """Tests for FileExtensionConstraint."""

    def test_valid_extensions(self) -> None:
        """FileExtensionConstraint should accept valid extensions."""
        constraint = FileExtensionConstraint(allowed_extensions=(".pdf", ".docx", ".txt"))
        assert constraint.allowed_extensions == (".pdf", ".docx", ".txt")

    def test_empty_extensions_raises(self) -> None:
        """FileExtensionConstraint should reject empty tuple."""
        with pytest.raises(ValueError, match="allowed_extensions cannot be empty"):
            FileExtensionConstraint(allowed_extensions=())

    def test_non_tuple_raises(self) -> None:
        """FileExtensionConstraint should reject non-tuple."""
        with pytest.raises(ValueError, match="must be a tuple"):
            FileExtensionConstraint(allowed_extensions=[".pdf"])  # type: ignore

    def test_extension_without_dot_raises(self) -> None:
        """FileExtensionConstraint should reject extensions without dot."""
        with pytest.raises(ValueError, match="Extension must start with '.'"):
            FileExtensionConstraint(allowed_extensions=("pdf", ".docx"))

    def test_extensions_immutable(self) -> None:
        """FileExtensionConstraint should be immutable."""
        constraint = FileExtensionConstraint(allowed_extensions=(".pdf",))
        with pytest.raises(AttributeError):
            constraint.allowed_extensions = (".docx",)  # type: ignore


class TestMaxFileSizeConstraint:
    """Tests for MaxFileSizeConstraint."""

    def test_valid_max_size(self) -> None:
        """MaxFileSizeConstraint should accept valid size."""
        constraint = MaxFileSizeConstraint(max_size_bytes=5 * 1024 * 1024)
        assert constraint.max_size_bytes == 5 * 1024 * 1024

    def test_zero_size_raises(self) -> None:
        """MaxFileSizeConstraint should reject zero size."""
        with pytest.raises(ValueError, match="max_size_bytes must be > 0"):
            MaxFileSizeConstraint(max_size_bytes=0)

    def test_negative_size_raises(self) -> None:
        """MaxFileSizeConstraint should reject negative size."""
        with pytest.raises(ValueError, match="max_size_bytes must be > 0"):
            MaxFileSizeConstraint(max_size_bytes=-1)

    def test_max_size_immutable(self) -> None:
        """MaxFileSizeConstraint should be immutable."""
        constraint = MaxFileSizeConstraint(max_size_bytes=1024)
        with pytest.raises(AttributeError):
            constraint.max_size_bytes = 2048  # type: ignore

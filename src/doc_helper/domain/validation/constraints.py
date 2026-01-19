"""Field validation constraints.

Constraints are immutable value objects that define validation rules.
"""

from abc import ABC
from dataclasses import dataclass
from typing import Optional, Pattern as RegexPattern

from doc_helper.domain.common.value_object import ValueObject


@dataclass(frozen=True)
class FieldConstraint(ValueObject, ABC):
    """Base class for field validation constraints.

    Constraints are declarative rules that define what makes a field value valid.
    They are immutable and can be composed.

    RULES (IMPLEMENTATION_RULES.md Section 3.3):
    - Constraints are value objects (immutable)
    - NO validation logic in constraints (validators apply them)
    - Constraints only store the rule parameters
    """
    pass


@dataclass(frozen=True)
class RequiredConstraint(FieldConstraint):
    """Field value must not be empty/null.

    Applies to: All field types

    Example:
        constraint = RequiredConstraint()
        # Field value cannot be None, empty string, empty list, etc.
    """
    pass


@dataclass(frozen=True)
class MinLengthConstraint(FieldConstraint):
    """Field value must have minimum character length.

    Applies to: TEXT, TEXTAREA

    Example:
        constraint = MinLengthConstraint(min_length=5)
        # "Hello" is valid, "Hi" is invalid
    """
    min_length: int

    def __post_init__(self) -> None:
        """Validate constraint parameters."""
        if self.min_length < 0:
            raise ValueError(f"min_length must be >= 0, got {self.min_length}")


@dataclass(frozen=True)
class MaxLengthConstraint(FieldConstraint):
    """Field value must not exceed maximum character length.

    Applies to: TEXT, TEXTAREA

    Example:
        constraint = MaxLengthConstraint(max_length=100)
        # Strings up to 100 characters are valid
    """
    max_length: int

    def __post_init__(self) -> None:
        """Validate constraint parameters."""
        if self.max_length < 0:
            raise ValueError(f"max_length must be >= 0, got {self.max_length}")


@dataclass(frozen=True)
class MinValueConstraint(FieldConstraint):
    """Field value must be >= minimum value.

    Applies to: NUMBER, DATE

    Example:
        constraint = MinValueConstraint(min_value=0)
        # Only non-negative numbers are valid
    """
    min_value: float

    def __post_init__(self) -> None:
        """Validate constraint parameters."""
        if not isinstance(self.min_value, (int, float)):
            raise ValueError(f"min_value must be numeric, got {type(self.min_value)}")


@dataclass(frozen=True)
class MaxValueConstraint(FieldConstraint):
    """Field value must be <= maximum value.

    Applies to: NUMBER, DATE

    Example:
        constraint = MaxValueConstraint(max_value=100)
        # Only values up to 100 are valid
    """
    max_value: float

    def __post_init__(self) -> None:
        """Validate constraint parameters."""
        if not isinstance(self.max_value, (int, float)):
            raise ValueError(f"max_value must be numeric, got {type(self.max_value)}")


@dataclass(frozen=True)
class PatternConstraint(FieldConstraint):
    r"""Field value must match regex pattern.

    Applies to: TEXT, TEXTAREA

    Example:
        constraint = PatternConstraint(
            pattern=r"^\d{3}-\d{3}-\d{4}$",
            description="Phone number (XXX-XXX-XXXX)"
        )
    """
    pattern: str
    description: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate constraint parameters."""
        if not self.pattern:
            raise ValueError("pattern cannot be empty")
        # Test that pattern compiles
        import re
        try:
            re.compile(self.pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")


@dataclass(frozen=True)
class AllowedValuesConstraint(FieldConstraint):
    """Field value must be one of the allowed values.

    Applies to: DROPDOWN, RADIO

    Example:
        constraint = AllowedValuesConstraint(
            allowed_values=("small", "medium", "large")
        )
    """
    allowed_values: tuple  # Must be tuple (immutable)

    def __post_init__(self) -> None:
        """Validate constraint parameters."""
        if not self.allowed_values:
            raise ValueError("allowed_values cannot be empty")
        if not isinstance(self.allowed_values, tuple):
            raise ValueError("allowed_values must be a tuple (immutable)")


@dataclass(frozen=True)
class FileExtensionConstraint(FieldConstraint):
    """File must have one of the allowed extensions.

    Applies to: FILE, IMAGE

    Example:
        constraint = FileExtensionConstraint(
            allowed_extensions=(".pdf", ".docx", ".txt")
        )
    """
    allowed_extensions: tuple  # Must be tuple (immutable)

    def __post_init__(self) -> None:
        """Validate constraint parameters."""
        if not self.allowed_extensions:
            raise ValueError("allowed_extensions cannot be empty")
        if not isinstance(self.allowed_extensions, tuple):
            raise ValueError("allowed_extensions must be a tuple (immutable)")
        # Ensure all extensions start with '.'
        for ext in self.allowed_extensions:
            if not ext.startswith('.'):
                raise ValueError(f"Extension must start with '.', got: {ext}")


@dataclass(frozen=True)
class MaxFileSizeConstraint(FieldConstraint):
    """File size must not exceed maximum bytes.

    Applies to: FILE, IMAGE

    Example:
        constraint = MaxFileSizeConstraint(
            max_size_bytes=5 * 1024 * 1024  # 5 MB
        )
    """
    max_size_bytes: int

    def __post_init__(self) -> None:
        """Validate constraint parameters."""
        if self.max_size_bytes <= 0:
            raise ValueError(f"max_size_bytes must be > 0, got {self.max_size_bytes}")

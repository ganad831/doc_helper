"""Validation results and errors.

ValidationResult holds the outcome of validating field values.
"""

from dataclasses import dataclass
from typing import Any, Optional

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.value_object import ValueObject


@dataclass(frozen=True)
class ValidationError(ValueObject):
    """Represents a single validation error.

    Validation errors are immutable value objects that describe why
    a field value failed validation.

    RULES (IMPLEMENTATION_RULES.md Section 3.3):
    - Errors are value objects (immutable)
    - Use TranslationKey for i18n support
    - NO hardcoded error messages

    Example:
        error = ValidationError(
            field_path="project.site_location",
            message_key=TranslationKey("validation.required"),
            constraint_type="RequiredConstraint",
            current_value=None
        )
    """

    field_path: str  # Dot-notation path to field (e.g., "project.site_location")
    message_key: TranslationKey  # Translation key for error message
    constraint_type: str  # Name of constraint that failed (e.g., "RequiredConstraint")
    current_value: Any  # The value that failed validation
    constraint_params: Optional[dict] = None  # Parameters for message interpolation

    def __post_init__(self) -> None:
        """Validate error parameters."""
        if not self.field_path:
            raise ValueError("field_path cannot be empty")
        if not self.constraint_type:
            raise ValueError("constraint_type cannot be empty")


@dataclass(frozen=True)
class ValidationResult(ValueObject):
    """Result of validating one or more fields.

    ValidationResult is immutable and contains a collection of errors.

    RULES (IMPLEMENTATION_RULES.md Section 3.3):
    - Result is a value object (immutable)
    - Errors stored as tuple (immutable collection)
    - v1: Simple pass/fail (NO severity levels like ERROR/WARNING)

    Usage:
        # Success case
        result = ValidationResult.success()
        assert result.is_valid()

        # Failure case
        errors = (
            ValidationError(...),
            ValidationError(...),
        )
        result = ValidationResult.failure(errors)
        assert not result.is_valid()
        assert result.error_count == 2
    """

    errors: tuple  # Tuple of ValidationError (immutable)

    def __post_init__(self) -> None:
        """Validate result parameters."""
        if not isinstance(self.errors, tuple):
            raise ValueError("errors must be a tuple (immutable)")
        # Verify all items are ValidationError
        for error in self.errors:
            if not isinstance(error, ValidationError):
                raise ValueError(f"All errors must be ValidationError, got {type(error)}")

    @staticmethod
    def success() -> "ValidationResult":
        """Create a successful validation result (no errors).

        Returns:
            ValidationResult with empty errors tuple
        """
        return ValidationResult(errors=())

    @staticmethod
    def failure(errors: tuple) -> "ValidationResult":
        """Create a failed validation result with errors.

        Args:
            errors: Tuple of ValidationError objects

        Returns:
            ValidationResult with the provided errors
        """
        return ValidationResult(errors=errors)

    def is_valid(self) -> bool:
        """Check if validation passed (no errors).

        Returns:
            True if no errors, False otherwise
        """
        return len(self.errors) == 0

    def is_invalid(self) -> bool:
        """Check if validation failed (has errors).

        Returns:
            True if has errors, False otherwise
        """
        return len(self.errors) > 0

    @property
    def error_count(self) -> int:
        """Get the number of validation errors.

        Returns:
            Count of errors
        """
        return len(self.errors)

    def get_errors_for_field(self, field_path: str) -> tuple:
        """Get all errors for a specific field.

        Args:
            field_path: Dot-notation path to field

        Returns:
            Tuple of ValidationError for the field
        """
        return tuple(error for error in self.errors if error.field_path == field_path)

    def has_errors_for_field(self, field_path: str) -> bool:
        """Check if a specific field has errors.

        Args:
            field_path: Dot-notation path to field

        Returns:
            True if field has errors
        """
        return any(error.field_path == field_path for error in self.errors)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge with another validation result.

        Args:
            other: Another ValidationResult to merge

        Returns:
            New ValidationResult with errors from both
        """
        return ValidationResult(errors=self.errors + other.errors)

"""Validation results and errors.

ValidationResult holds the outcome of validating field values.
"""

from dataclasses import dataclass
from typing import Any, Optional

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.value_object import ValueObject
from doc_helper.domain.validation.severity import Severity


@dataclass(frozen=True)
class ValidationError(ValueObject):
    """Represents a single validation error.

    Validation errors are immutable value objects that describe why
    a field value failed validation.

    RULES (IMPLEMENTATION_RULES.md Section 3.3):
    - Errors are value objects (immutable)
    - Use TranslationKey for i18n support
    - NO hardcoded error messages
    - ADR-025: Each error has explicit severity (ERROR/WARNING/INFO)

    Example:
        error = ValidationError(
            field_path="project.site_location",
            message_key=TranslationKey("validation.required"),
            constraint_type="RequiredConstraint",
            current_value=None,
            severity=Severity.ERROR
        )
    """

    field_path: str  # Dot-notation path to field (e.g., "project.site_location")
    message_key: TranslationKey  # Translation key for error message
    constraint_type: str  # Name of constraint that failed (e.g., "RequiredConstraint")
    current_value: Any  # The value that failed validation
    constraint_params: Optional[dict] = None  # Parameters for message interpolation
    severity: Severity = Severity.ERROR  # Severity level (ADR-025, default: ERROR for backward compatibility)

    def __post_init__(self) -> None:
        """Validate error parameters."""
        if not self.field_path:
            raise ValueError("field_path cannot be empty")
        if not self.constraint_type:
            raise ValueError("constraint_type cannot be empty")
        if not isinstance(self.severity, Severity):
            raise ValueError(f"severity must be a Severity enum, got {type(self.severity)}")


@dataclass(frozen=True)
class ValidationResult(ValueObject):
    """Result of validating one or more fields.

    ValidationResult is immutable and contains a collection of errors.

    RULES (IMPLEMENTATION_RULES.md Section 3.3):
    - Result is a value object (immutable)
    - Errors stored as tuple (immutable collection)
    - ADR-025: Supports severity levels (ERROR/WARNING/INFO)
    - Severity determines workflow control behavior

    Usage:
        # Success case
        result = ValidationResult.success()
        assert result.is_valid()

        # Failure case
        errors = (
            ValidationError(..., severity=Severity.ERROR),
            ValidationError(..., severity=Severity.WARNING),
        )
        result = ValidationResult.failure(errors)
        assert not result.is_valid()
        assert result.error_count == 2
        assert result.has_blocking_errors()  # Has ERROR
        assert result.has_warnings()  # Has WARNING
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

    def has_blocking_errors(self) -> bool:
        """Check if result contains any ERROR-level errors that block workflows.

        ADR-025: ERROR severity blocks workflow unconditionally.

        Returns:
            True if has any ERROR severity errors
        """
        return any(error.severity == Severity.ERROR for error in self.errors)

    def has_warnings(self) -> bool:
        """Check if result contains any WARNING-level errors.

        ADR-025: WARNING severity requires user confirmation to proceed.

        Returns:
            True if has any WARNING severity errors
        """
        return any(error.severity == Severity.WARNING for error in self.errors)

    def has_info(self) -> bool:
        """Check if result contains any INFO-level errors.

        ADR-025: INFO severity is informational only, never blocks.

        Returns:
            True if has any INFO severity errors
        """
        return any(error.severity == Severity.INFO for error in self.errors)

    def get_errors_by_severity(self, severity: Severity) -> tuple:
        """Get all errors with a specific severity level.

        Args:
            severity: The severity level to filter by

        Returns:
            Tuple of ValidationError with matching severity
        """
        return tuple(error for error in self.errors if error.severity == severity)

    def blocks_workflow(self) -> bool:
        """Check if this result should block workflow continuation.

        ADR-025: Workflows are blocked if there are any ERROR-level errors.
        WARNING and INFO do not block unconditionally.

        Returns:
            True if workflow should be blocked (has ERROR-level errors)
        """
        return self.has_blocking_errors()

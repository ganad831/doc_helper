"""Validation DTOs for UI display.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationErrorDTO:
    """UI-facing validation error for display.

    Represents a single validation error with display-ready message.
    """

    field_id: str  # Field ID as string
    message: str  # Translated error message for display
    constraint_type: str  # Type of constraint that failed (e.g., "REQUIRED", "MIN_LENGTH")


@dataclass(frozen=True)
class ValidationResultDTO:
    """UI-facing validation result for display.

    Represents the validation state of a field or project.

    FORBIDDEN in this DTO:
    - Domain value objects (ValidationResult, ValidationError)
    - Previous validation states for undo
    """

    is_valid: bool  # Whether validation passed
    errors: tuple[ValidationErrorDTO, ...]  # Tuple of validation errors (empty if valid)
    field_id: str | None = None  # Field ID if field-level validation (None for project-level)

    @property
    def error_count(self) -> int:
        """Get count of validation errors."""
        return len(self.errors)

    @property
    def error_messages(self) -> tuple[str, ...]:
        """Get tuple of error messages."""
        return tuple(error.message for error in self.errors)

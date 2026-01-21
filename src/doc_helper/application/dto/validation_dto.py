"""Validation DTOs for UI display.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)
- ADR-025: Include severity as primitive string (ERROR/WARNING/INFO)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationErrorDTO:
    """UI-facing validation error for display.

    Represents a single validation error with display-ready message.
    ADR-025: Each error includes severity level for UI differentiation.
    """

    field_id: str  # Field ID as string
    message: str  # Translated error message for display
    constraint_type: str  # Type of constraint that failed (e.g., "REQUIRED", "MIN_LENGTH")
    severity: str = "ERROR"  # Severity level: "ERROR", "WARNING", or "INFO" (default: "ERROR" for backward compatibility)


@dataclass(frozen=True)
class ValidationResultDTO:
    """UI-facing validation result for display.

    Represents the validation state of a field or project.
    ADR-025: Supports severity-based workflow control.

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

    def has_blocking_errors(self) -> bool:
        """Check if result contains ERROR-level errors that block workflows.

        ADR-025: ERROR severity blocks workflow unconditionally.

        Returns:
            True if has any ERROR severity errors
        """
        return any(error.severity == "ERROR" for error in self.errors)

    def has_warnings(self) -> bool:
        """Check if result contains WARNING-level errors.

        ADR-025: WARNING severity requires user confirmation to proceed.

        Returns:
            True if has any WARNING severity errors
        """
        return any(error.severity == "WARNING" for error in self.errors)

    def has_info(self) -> bool:
        """Check if result contains INFO-level errors.

        ADR-025: INFO severity is informational only, never blocks.

        Returns:
            True if has any INFO severity errors
        """
        return any(error.severity == "INFO" for error in self.errors)

    def blocks_workflow(self) -> bool:
        """Check if this result should block workflow continuation.

        ADR-025: Workflows are blocked if there are any ERROR-level errors.
        WARNING and INFO do not block unconditionally.

        Returns:
            True if workflow should be blocked (has ERROR-level errors)
        """
        return self.has_blocking_errors()

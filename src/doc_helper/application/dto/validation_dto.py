"""Validation DTOs for UI display.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2-H3):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior, NO computation (Phase H-3)
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)
- ADR-025: Include severity as primitive string (ERROR/WARNING/INFO)
- Phase H-3: All pre-computed fields MUST be provided at construction
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
    - __post_init__ computation (Phase H-3)

    Phase H-3: All fields MUST be provided at construction time.
    Only ValidationMapper or authorized adapters may construct this DTO.
    """

    # Required core fields
    is_valid: bool  # Whether validation passed
    errors: tuple[ValidationErrorDTO, ...]  # Tuple of validation errors (empty if valid)
    # Pre-computed fields (Phase H-3: MUST be provided, no computation)
    _error_count: int  # Count of validation errors
    _error_messages: tuple[str, ...]  # Tuple of error messages
    _has_blocking_errors: bool  # True if has any ERROR severity errors
    _has_warnings: bool  # True if has any WARNING severity errors
    _has_info: bool  # True if has any INFO severity errors
    # Optional field
    field_id: str | None = None  # Field ID if field-level validation (None for project-level)

    @property
    def error_count(self) -> int:
        """Get count of validation errors."""
        return self._error_count

    @property
    def error_messages(self) -> tuple[str, ...]:
        """Get tuple of error messages."""
        return self._error_messages

    def has_blocking_errors(self) -> bool:
        """Check if result contains ERROR-level errors that block workflows.

        ADR-025: ERROR severity blocks workflow unconditionally.

        Returns:
            True if has any ERROR severity errors
        """
        return self._has_blocking_errors

    def has_warnings(self) -> bool:
        """Check if result contains WARNING-level errors.

        ADR-025: WARNING severity requires user confirmation to proceed.

        Returns:
            True if has any WARNING severity errors
        """
        return self._has_warnings

    def has_info(self) -> bool:
        """Check if result contains INFO-level errors.

        ADR-025: INFO severity is informational only, never blocks.

        Returns:
            True if has any INFO severity errors
        """
        return self._has_info

    def blocks_workflow(self) -> bool:
        """Check if this result should block workflow continuation.

        ADR-025: Workflows are blocked if there are any ERROR-level errors.
        WARNING and INFO do not block unconditionally.

        Returns:
            True if workflow should be blocked (has ERROR-level errors)
        """
        return self._has_blocking_errors

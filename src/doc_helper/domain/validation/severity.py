"""Validation severity levels.

Severity defines three levels of validation issues: ERROR, WARNING, INFO.
Introduced by ADR-025: Validation Severity Levels.
"""

from enum import Enum

from doc_helper.domain.common.value_object import ValueObject


class Severity(str, Enum):
    """Validation severity level.

    Defines the impact of a validation failure on workflow control:
    - ERROR: Blocks workflows unconditionally (must be resolved)
    - WARNING: Allows continuation with explicit user confirmation
    - INFO: Informational only, never blocks workflows

    ADR-025 Rules:
    - Severity is explicit (not inferred at runtime)
    - Domain constraints declare default severity
    - Backward compatible: existing constraints default to ERROR

    Usage:
        # Error-level validation (blocks generation)
        error = ValidationError(..., severity=Severity.ERROR)

        # Warning-level validation (allows generation after confirmation)
        warning = ValidationError(..., severity=Severity.WARNING)

        # Info-level validation (never blocks)
        info = ValidationError(..., severity=Severity.INFO)
    """

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

    def blocks_workflow(self) -> bool:
        """Check if this severity level blocks workflows unconditionally.

        Returns:
            True if ERROR (blocks unconditionally), False otherwise
        """
        return self == Severity.ERROR

    def requires_confirmation(self) -> bool:
        """Check if this severity level requires user confirmation.

        Returns:
            True if WARNING (requires confirmation), False otherwise
        """
        return self == Severity.WARNING

    def is_informational(self) -> bool:
        """Check if this severity level is informational only.

        Returns:
            True if INFO (never blocks), False otherwise
        """
        return self == Severity.INFO

    @classmethod
    def default(cls) -> "Severity":
        """Get the default severity level.

        Backward Compatibility (ADR-025):
        Existing validation constraints default to ERROR to preserve
        current blocking behavior.

        Returns:
            Severity.ERROR (default for backward compatibility)
        """
        return cls.ERROR

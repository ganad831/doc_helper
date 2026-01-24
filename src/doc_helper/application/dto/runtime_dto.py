"""Runtime Evaluation DTOs (Phase R-1, R-2, R-3).

Data Transfer Objects for runtime evaluation:
- Control rule evaluation (Phase R-1)
- Output mapping evaluation (Phase R-1)
- Validation constraint evaluation (Phase R-2)
- Orchestrated runtime evaluation (Phase R-3)

ADR-050 Compliance:
- Pull-based evaluation (caller provides all inputs)
- Deterministic (no side effects, no persistence)
- Explicit failure handling
- Read-only (no mutations)
"""

from dataclasses import dataclass
from typing import Any, Optional


# ============================================================================
# Control Rule Evaluation DTOs
# ============================================================================


@dataclass(frozen=True)
class ControlRuleEvaluationRequestDTO:
    """Request DTO for evaluating control rules at runtime (Phase R-1).

    ADR-050 Compliance:
        - Pull-based: Caller provides all inputs
        - Single-entity scope only (no cross-entity)
        - Field values passed as snapshot (read-only)
    """

    entity_id: str
    """Entity containing the field with control rules."""

    field_id: str
    """Field whose control rules should be evaluated."""

    field_values: dict[str, Any]
    """Current field values for the entity instance (snapshot)."""


@dataclass(frozen=True)
class ControlRuleEvaluationResultDTO:
    """Result DTO for control rule evaluation at runtime (Phase R-1).

    ADR-050 Compliance:
        - Explicit success/failure
        - Boolean results only
        - Default states on failure
        - No persistence side effects
    """

    success: bool
    """Whether evaluation completed without errors."""

    visible: bool
    """Whether the field should be visible (default: True)."""

    enabled: bool
    """Whether the field should be enabled (default: True)."""

    required: bool
    """Whether the field is required (default: False)."""

    error_message: Optional[str] = None
    """Error message if evaluation failed (None if success)."""

    @staticmethod
    def default() -> "ControlRuleEvaluationResultDTO":
        """Return default field state (visible, enabled, not required).

        Used when no control rules exist or all rules fail evaluation.
        """
        return ControlRuleEvaluationResultDTO(
            success=True,
            visible=True,
            enabled=True,
            required=False,
            error_message=None,
        )

    @staticmethod
    def failure(error_message: str) -> "ControlRuleEvaluationResultDTO":
        """Return failure result with default field state.

        ADR-050: Control rule failures do NOT block form interaction.
        """
        return ControlRuleEvaluationResultDTO(
            success=False,
            visible=True,
            enabled=True,
            required=False,
            error_message=error_message,
        )


# ============================================================================
# Output Mapping Evaluation DTOs
# ============================================================================


@dataclass(frozen=True)
class OutputMappingEvaluationRequestDTO:
    """Request DTO for evaluating output mappings at runtime (Phase R-1).

    ADR-050 Compliance:
        - Pull-based: Caller provides all inputs
        - Single-entity scope only (no cross-entity)
        - Document generation context only
    """

    entity_id: str
    """Entity containing the field with output mappings."""

    field_id: str
    """Field whose output mappings should be evaluated."""

    field_values: dict[str, Any]
    """Current field values for the entity instance (snapshot)."""


@dataclass(frozen=True)
class OutputMappingEvaluationResultDTO:
    """Result DTO for output mapping evaluation at runtime (Phase R-1).

    ADR-050 Compliance:
        - Explicit success/failure
        - Strict type enforcement (TEXT/NUMBER/BOOLEAN)
        - No silent coercion
        - Blocking failure (no partial results)
    """

    success: bool
    """Whether evaluation completed without errors."""

    target: str
    """Output target type (TEXT, NUMBER, BOOLEAN)."""

    value: Any
    """Computed output value (type matches target)."""

    error_message: Optional[str] = None
    """Error message if evaluation failed (None if success)."""

    @staticmethod
    def text_result(value: str) -> "OutputMappingEvaluationResultDTO":
        """Create successful TEXT output result."""
        return OutputMappingEvaluationResultDTO(
            success=True,
            target="TEXT",
            value=value,
            error_message=None,
        )

    @staticmethod
    def number_result(value: float) -> "OutputMappingEvaluationResultDTO":
        """Create successful NUMBER output result."""
        return OutputMappingEvaluationResultDTO(
            success=True,
            target="NUMBER",
            value=value,
            error_message=None,
        )

    @staticmethod
    def boolean_result(value: bool) -> "OutputMappingEvaluationResultDTO":
        """Create successful BOOLEAN output result."""
        return OutputMappingEvaluationResultDTO(
            success=True,
            target="BOOLEAN",
            value=value,
            error_message=None,
        )

    @staticmethod
    def failure(
        target: str, error_message: str
    ) -> "OutputMappingEvaluationResultDTO":
        """Create failure result.

        ADR-050: Output mapping failures BLOCK document generation.
        """
        return OutputMappingEvaluationResultDTO(
            success=False,
            target=target,
            value=None,
            error_message=error_message,
        )


# ============================================================================
# Validation Rule Evaluation DTOs (Phase R-2)
# ============================================================================


@dataclass(frozen=True)
class ValidationIssueDTO:
    """A single validation issue found during constraint evaluation (Phase R-2).

    ADR-050 Compliance:
        - Immutable issue record
        - Severity-based categorization
        - Human-readable message
        - Machine-readable code
    """

    field_id: str
    """Field identifier that failed validation."""

    field_label: str
    """Translated human-readable field label."""

    constraint_type: str
    """Type of constraint that failed (e.g., 'RequiredConstraint', 'MinLengthConstraint')."""

    severity: str
    """Severity level: 'ERROR', 'WARNING', or 'INFO'."""

    message: str
    """Translated human-readable error message."""

    code: str
    """Machine-readable error code (e.g., 'REQUIRED_FIELD_EMPTY', 'VALUE_TOO_SMALL')."""

    details: Optional[dict] = None
    """Optional constraint-specific details (e.g., {"min_length": 5, "actual_length": 3})."""


@dataclass(frozen=True)
class ValidationEvaluationRequestDTO:
    """Request DTO for evaluating validation constraints at runtime (Phase R-2).

    ADR-050 Compliance:
        - Pull-based: Caller provides all inputs
        - Single-entity scope only (no cross-entity)
        - Field values passed as snapshot (read-only)
    """

    entity_id: str
    """Entity whose fields should be validated."""

    field_values: dict[str, Any]
    """Current field values for the entity instance (snapshot).
    Keys are field IDs, values are raw field values."""


@dataclass(frozen=True)
class ValidationEvaluationResultDTO:
    """Result DTO for validation constraint evaluation at runtime (Phase R-2).

    ADR-050 Compliance:
        - Explicit success/failure
        - Severity-based issue categorization
        - Blocking determination based on ERROR severity
        - No persistence side effects
    """

    success: bool
    """Whether evaluation completed without exceptions.
    True even if validation issues found (check blocking flag instead)."""

    errors: tuple[ValidationIssueDTO, ...]
    """Validation issues with ERROR severity (blocking)."""

    warnings: tuple[ValidationIssueDTO, ...]
    """Validation issues with WARNING severity (non-blocking)."""

    info: tuple[ValidationIssueDTO, ...]
    """Validation issues with INFO severity (informational only)."""

    blocking: bool
    """Whether any ERROR severity issues were found.
    True if len(errors) > 0, False otherwise."""

    evaluated_fields: tuple[str, ...]
    """Field IDs that were evaluated (had values in field_values dict)."""

    failed_fields: tuple[str, ...]
    """Field IDs that had ERROR severity issues."""

    error_message: Optional[str] = None
    """Error message if evaluation failed due to exception (None if success)."""

    @staticmethod
    def success_result(
        errors: tuple[ValidationIssueDTO, ...],
        warnings: tuple[ValidationIssueDTO, ...],
        info: tuple[ValidationIssueDTO, ...],
        evaluated_fields: tuple[str, ...],
        failed_fields: tuple[str, ...],
    ) -> "ValidationEvaluationResultDTO":
        """Create successful validation result (may still have validation issues).

        Args:
            errors: ERROR severity issues
            warnings: WARNING severity issues
            info: INFO severity issues
            evaluated_fields: Field IDs that were evaluated
            failed_fields: Field IDs with ERROR issues

        Returns:
            ValidationEvaluationResultDTO with blocking flag set based on errors
        """
        return ValidationEvaluationResultDTO(
            success=True,
            errors=errors,
            warnings=warnings,
            info=info,
            blocking=len(errors) > 0,
            evaluated_fields=evaluated_fields,
            failed_fields=failed_fields,
            error_message=None,
        )

    @staticmethod
    def failure(error_message: str) -> "ValidationEvaluationResultDTO":
        """Create failure result due to exception.

        ADR-050: Evaluation failures (exceptions) return empty results.
        """
        return ValidationEvaluationResultDTO(
            success=False,
            errors=(),
            warnings=(),
            info=(),
            blocking=False,
            evaluated_fields=(),
            failed_fields=(),
            error_message=error_message,
        )


# ============================================================================
# Runtime Orchestrator DTOs (Phase R-3)
# ============================================================================


@dataclass(frozen=True)
class RuntimeEvaluationRequestDTO:
    """Request DTO for orchestrated runtime evaluation (Phase R-3).

    ADR-050 Compliance:
        - Pull-based: Caller provides all inputs
        - Single-entity scope only (no cross-entity)
        - Field values passed as snapshot (read-only)

    Phase R-3: Orchestrates evaluation of:
        1. Control rules (R-1)
        2. Validation rules (R-2)
        3. Output mappings (R-1)
    """

    entity_id: str
    """Entity whose rules should be evaluated."""

    field_values: dict[str, Any]
    """Current field values for the entity instance (snapshot).
    Keys are field IDs, values are raw field values."""


@dataclass(frozen=True)
class RuntimeEvaluationResultDTO:
    """Result DTO for orchestrated runtime evaluation (Phase R-3).

    ADR-050 Compliance:
        - Explicit success/failure
        - Aggregates results from all runtime evaluations
        - Blocking determination based on component rules
        - No persistence side effects

    Blocking Rules (Phase R-3):
        - Control Rules: Never blocking
        - Validation Rules: Blocks if any ERROR severity issues
        - Output Mappings: Always blocking on failure
        - Overall blocking: True if ANY component blocks
    """

    control_rules_result: ControlRuleEvaluationResultDTO
    """Result from control rule evaluation (R-1)."""

    validation_result: ValidationEvaluationResultDTO
    """Result from validation constraint evaluation (R-2)."""

    output_mappings_result: Optional[OutputMappingEvaluationResultDTO]
    """Result from output mapping evaluation (R-1).
    None if not evaluated (validation blocked)."""

    is_blocked: bool
    """Whether runtime evaluation is blocked.
    True if validation has ERROR issues OR output mapping failed."""

    blocking_reason: Optional[str]
    """Human-readable reason for blocking (None if not blocked)."""

    @staticmethod
    def success(
        control_rules_result: ControlRuleEvaluationResultDTO,
        validation_result: ValidationEvaluationResultDTO,
        output_mappings_result: Optional[OutputMappingEvaluationResultDTO],
        is_blocked: bool,
        blocking_reason: Optional[str],
    ) -> "RuntimeEvaluationResultDTO":
        """Create successful runtime evaluation result.

        Args:
            control_rules_result: Control rule evaluation result
            validation_result: Validation evaluation result
            output_mappings_result: Output mapping evaluation result (may be None if blocked)
            is_blocked: Whether evaluation is blocked
            blocking_reason: Reason for blocking (if blocked)

        Returns:
            RuntimeEvaluationResultDTO with all results aggregated
        """
        return RuntimeEvaluationResultDTO(
            control_rules_result=control_rules_result,
            validation_result=validation_result,
            output_mappings_result=output_mappings_result,
            is_blocked=is_blocked,
            blocking_reason=blocking_reason,
        )

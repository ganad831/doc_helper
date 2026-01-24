"""Runtime Evaluation DTOs (Phase R-1).

Data Transfer Objects for runtime control rule and output mapping evaluation.

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

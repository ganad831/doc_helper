"""Runtime Evaluation DTOs (Phase R-1, R-2, R-3, R-4, R-4.5, R-5).

Data Transfer Objects for runtime evaluation:
- Control rule evaluation (Phase R-1)
- Output mapping evaluation (Phase R-1)
- Validation constraint evaluation (Phase R-2)
- Orchestrated runtime evaluation (Phase R-3)
- Entity-level control rules aggregation (Phase R-4)
- Form runtime state adapter (Phase R-4.5)
- Entity-level output mappings aggregation (Phase R-5)

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
    """Result DTO for orchestrated runtime evaluation (Phase R-3, updated in R-4).

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

    Phase R-4 Update:
        - control_rules_result now uses entity-level aggregation (EntityControlRulesEvaluationResultDTO)
    """

    control_rules_result: "EntityControlRulesEvaluationResultDTO"
    """Result from entity-level control rule evaluation (R-4).
    Updated in Phase R-4 from field-level (R-1) to entity-level aggregation."""

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
        control_rules_result: "EntityControlRulesEvaluationResultDTO",
        validation_result: ValidationEvaluationResultDTO,
        output_mappings_result: Optional[OutputMappingEvaluationResultDTO],
        is_blocked: bool,
        blocking_reason: Optional[str],
    ) -> "RuntimeEvaluationResultDTO":
        """Create successful runtime evaluation result.

        Args:
            control_rules_result: Entity-level control rule evaluation result (R-4)
            validation_result: Validation evaluation result (R-2)
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


# ============================================================================
# Entity-Level Control Rules Aggregation DTOs (Phase R-4)
# ============================================================================


@dataclass(frozen=True)
class EntityControlRuleEvaluationDTO:
    """Per-field control rule evaluation result for entity aggregation (Phase R-4).

    ADR-050 Compliance:
        - Immutable field-level control state
        - Single-entity scope only
        - No domain object leakage
    """

    field_id: str
    """Field identifier."""

    visibility: bool
    """Whether the field should be visible (True) or hidden (False)."""

    enabled: bool
    """Whether the field should be enabled (True) or disabled (False)."""

    required: bool
    """Whether the field is required (True) or optional (False)."""


@dataclass(frozen=True)
class EntityControlRulesEvaluationResultDTO:
    """Aggregated control rule evaluation result for an entire entity (Phase R-4).

    ADR-050 Compliance:
        - Immutable entity-level aggregation
        - Pull-based evaluation (caller provides all inputs)
        - Deterministic (same inputs → same outputs)
        - Read-only (no mutations)
        - Single-entity scope only

    Phase R-4: Bridges field-level control rules (R-1) with entity-level orchestration (R-3).
    """

    entity_id: str
    """Entity whose control rules were evaluated."""

    field_results: tuple[EntityControlRuleEvaluationDTO, ...]
    """Per-field control rule evaluation results.
    Tuple ordered by field evaluation order."""

    has_any_rule: bool
    """Whether any control rules exist for fields in this entity.
    False if all fields use default states."""

    @staticmethod
    def from_field_results(
        entity_id: str,
        field_results: tuple[EntityControlRuleEvaluationDTO, ...],
    ) -> "EntityControlRulesEvaluationResultDTO":
        """Create entity-level result from field-level results.

        Args:
            entity_id: Entity identifier
            field_results: Tuple of per-field control rule results

        Returns:
            EntityControlRulesEvaluationResultDTO with aggregated results
        """
        # Determine if any rules exist (not all defaults)
        has_any_rule = any(
            not (result.visibility and result.enabled and not result.required)
            for result in field_results
        )

        return EntityControlRulesEvaluationResultDTO(
            entity_id=entity_id,
            field_results=field_results,
            has_any_rule=has_any_rule,
        )

    @staticmethod
    def default(entity_id: str) -> "EntityControlRulesEvaluationResultDTO":
        """Create default result (no fields, no rules).

        Args:
            entity_id: Entity identifier

        Returns:
            EntityControlRulesEvaluationResultDTO with empty results
        """
        return EntityControlRulesEvaluationResultDTO(
            entity_id=entity_id,
            field_results=(),
            has_any_rule=False,
        )


# ============================================================================
# Form Runtime State DTOs (Phase R-4.5)
# ============================================================================


@dataclass(frozen=True)
class FormFieldRuntimeStateDTO:
    """Runtime state for a single form field (Phase R-4.5).

    Presentation-ready representation of field runtime state.
    Combines control rules and validation results without UI logic.

    ADR-050 Compliance:
        - Immutable field state snapshot
        - Pull-based (derived from runtime evaluation results)
        - No domain object leakage
        - Presentation-agnostic (no UI imports)
    """

    field_id: str
    """Field identifier."""

    visible: bool
    """Whether the field should be visible (from control rules)."""

    enabled: bool
    """Whether the field should be enabled (from control rules)."""

    required: bool
    """Whether the field is required (from control rules)."""

    validation_errors: tuple[str, ...]
    """Validation error messages (ERROR severity - blocking)."""

    validation_warnings: tuple[str, ...]
    """Validation warning messages (WARNING severity - non-blocking)."""

    validation_info: tuple[str, ...]
    """Validation info messages (INFO severity - informational)."""


@dataclass(frozen=True)
class FormRuntimeStateDTO:
    """Runtime state for an entire form (Phase R-4.5).

    Aggregates per-field runtime state for UI consumption.
    Converts runtime evaluation results into presentation-ready form state.

    ADR-050 Compliance:
        - Immutable entity-level form state
        - Pull-based (derived from R-3 orchestration results)
        - Deterministic (same inputs → same outputs)
        - Read-only (no persistence)
        - Single-entity scope only

    Phase R-4.5: Adapter between runtime evaluation and UI layer.
    """

    entity_id: str
    """Entity whose form state is represented."""

    fields: tuple[FormFieldRuntimeStateDTO, ...]
    """Per-field runtime state (ordered by field evaluation order)."""

    has_blocking_errors: bool
    """Whether any field has ERROR severity validation issues.
    True if form submission should be blocked."""

    @staticmethod
    def from_runtime_result(
        entity_id: str,
        runtime_result: "RuntimeEvaluationResultDTO",
    ) -> "FormRuntimeStateDTO":
        """Create form runtime state from R-3 orchestration result.

        Args:
            entity_id: Entity identifier
            runtime_result: RuntimeEvaluationResultDTO from Phase R-3

        Returns:
            FormRuntimeStateDTO with per-field states
        """
        # Extract control rules from R-4 entity-level aggregation
        control_rules_result = runtime_result.control_rules_result

        # Extract validation results from R-2
        validation_result = runtime_result.validation_result

        # Build validation lookup: field_id → (errors, warnings, info)
        validation_by_field: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {}

        # Group validation issues by field_id
        for error in validation_result.errors:
            if error.field_id not in validation_by_field:
                validation_by_field[error.field_id] = ((), (), ())
            current = validation_by_field[error.field_id]
            validation_by_field[error.field_id] = (
                current[0] + (error.message,),
                current[1],
                current[2],
            )

        for warning in validation_result.warnings:
            if warning.field_id not in validation_by_field:
                validation_by_field[warning.field_id] = ((), (), ())
            current = validation_by_field[warning.field_id]
            validation_by_field[warning.field_id] = (
                current[0],
                current[1] + (warning.message,),
                current[2],
            )

        for info in validation_result.info:
            if info.field_id not in validation_by_field:
                validation_by_field[info.field_id] = ((), (), ())
            current = validation_by_field[info.field_id]
            validation_by_field[info.field_id] = (
                current[0],
                current[1],
                current[2] + (info.message,),
            )

        # Build per-field runtime state
        field_states: list[FormFieldRuntimeStateDTO] = []

        for field_control in control_rules_result.field_results:
            # Get validation messages for this field (or empty tuples)
            field_validation = validation_by_field.get(
                field_control.field_id,
                ((), (), ()),
            )

            field_state = FormFieldRuntimeStateDTO(
                field_id=field_control.field_id,
                visible=field_control.visibility,
                enabled=field_control.enabled,
                required=field_control.required,
                validation_errors=field_validation[0],
                validation_warnings=field_validation[1],
                validation_info=field_validation[2],
            )
            field_states.append(field_state)

        # Determine if form has blocking errors
        has_blocking_errors = validation_result.blocking

        return FormRuntimeStateDTO(
            entity_id=entity_id,
            fields=tuple(field_states),
            has_blocking_errors=has_blocking_errors,
        )

    @staticmethod
    def default(entity_id: str) -> "FormRuntimeStateDTO":
        """Create default form state (no fields, no errors).

        Args:
            entity_id: Entity identifier

        Returns:
            FormRuntimeStateDTO with empty state
        """
        return FormRuntimeStateDTO(
            entity_id=entity_id,
            fields=(),
            has_blocking_errors=False,
        )


# ============================================================================
# Entity-Level Output Mappings Aggregation DTOs (Phase R-5)
# ============================================================================


@dataclass(frozen=True)
class EntityOutputMappingResultDTO:
    """Result of entity-level output mapping evaluation (Phase R-5).

    Contains aggregated output values ready for document generation.

    ADR-050 Compliance:
        - Immutable result
        - Blocking on any failure
        - No silent coercion
        - Dictionary of target → value mappings
    """

    success: bool
    """Whether all output mapping evaluations succeeded."""

    values: dict[str, Any]
    """Aggregated output values: {target → value}.
    Example: {"TEXT": "5.0 - 10.0", "NUMBER": 7.5, "BOOLEAN": True}
    Empty dict if no output mappings or if failed."""

    error: Optional[str] = None
    """Error message if any output mapping failed (None if success)."""

    @staticmethod
    def success_result(values: dict[str, Any]) -> "EntityOutputMappingResultDTO":
        """Create successful result with aggregated values.

        Args:
            values: Aggregated output values {target → value}

        Returns:
            EntityOutputMappingResultDTO with success=True
        """
        return EntityOutputMappingResultDTO(
            success=True,
            values=values,
            error=None,
        )

    @staticmethod
    def failure(error: str) -> "EntityOutputMappingResultDTO":
        """Create failure result.

        ADR-050: Output mapping failures BLOCK document generation.

        Args:
            error: Error message describing the failure

        Returns:
            EntityOutputMappingResultDTO with success=False
        """
        return EntityOutputMappingResultDTO(
            success=False,
            values={},
            error=error,
        )

    @staticmethod
    def empty() -> "EntityOutputMappingResultDTO":
        """Create empty success result (no output mappings).

        Returns:
            EntityOutputMappingResultDTO with success=True and empty values
        """
        return EntityOutputMappingResultDTO(
            success=True,
            values={},
            error=None,
        )


@dataclass(frozen=True)
class EntityOutputMappingsEvaluationDTO:
    """Entity-level output mappings evaluation result (Phase R-5).

    Aggregates output mapping evaluation for all fields in an entity.

    ADR-050 Compliance:
        - Immutable entity-level aggregation
        - Pull-based (derived from field-level evaluations)
        - Deterministic (same inputs → same outputs)
        - Read-only (no persistence)
        - Blocking on any failure
        - Single-entity scope only

    Phase R-5: Bridges field-level output mappings (R-1) with runtime orchestration (R-3).
    """

    entity_id: str
    """Entity whose output mappings were evaluated."""

    result: EntityOutputMappingResultDTO
    """Aggregated output mapping result (success or failure)."""

    @staticmethod
    def success_result(
        entity_id: str,
        values: dict[str, Any],
    ) -> "EntityOutputMappingsEvaluationDTO":
        """Create successful evaluation result.

        Args:
            entity_id: Entity identifier
            values: Aggregated output values {target → value}

        Returns:
            EntityOutputMappingsEvaluationDTO with success result
        """
        return EntityOutputMappingsEvaluationDTO(
            entity_id=entity_id,
            result=EntityOutputMappingResultDTO.success_result(values),
        )

    @staticmethod
    def failure(entity_id: str, error: str) -> "EntityOutputMappingsEvaluationDTO":
        """Create failure result.

        Args:
            entity_id: Entity identifier
            error: Error message describing the failure

        Returns:
            EntityOutputMappingsEvaluationDTO with failure result
        """
        return EntityOutputMappingsEvaluationDTO(
            entity_id=entity_id,
            result=EntityOutputMappingResultDTO.failure(error),
        )

    @staticmethod
    def empty(entity_id: str) -> "EntityOutputMappingsEvaluationDTO":
        """Create empty success result (no output mappings).

        Args:
            entity_id: Entity identifier

        Returns:
            EntityOutputMappingsEvaluationDTO with empty success result
        """
        return EntityOutputMappingsEvaluationDTO(
            entity_id=entity_id,
            result=EntityOutputMappingResultDTO.empty(),
        )

"""Formula Editor ViewModel (Phase F-1, F-3, F-4, F-5, F-6, F-7: Formula Editor).

Manages presentation state for the Formula Editor UI.
Provides live formula validation with syntax highlighting and error display.

PHASE F-1 SCOPE:
- Hold formula text as observable state
- Validate formula in real-time
- Display validation errors/warnings
- Display inferred result type
- Display field references

PHASE F-3 SCOPE (ADR-040):
- Analyze formula dependencies (field references)
- Expose dependencies and unknown_fields for UI display
- Read-only, deterministic analysis

PHASE F-4 SCOPE (ADR-041):
- Detect circular dependencies in formula fields
- Expose cycle information for UI display
- Read-only, deterministic analysis
- Same-entity scope only

PHASE F-5 SCOPE (Diagnostics & UX Visualization):
- Aggregate all diagnostic information from F-1 through F-4
- Provide display-ready grouped properties for UI
- Human-readable status messages
- NO new logic - only consume existing DTO data

PHASE F-6 SCOPE (Governance & Enforcement):
- Expose governance evaluation results from use-case
- Read-only governance status and properties
- NO new governance logic (use-case owns logic)
- NO blocking behavior (informational only)

PHASE F-7 SCOPE (Formula Binding & Persistence Rules):
- Hold binding target state (CALCULATED_FIELD, etc.)
- Expose binding status based on governance
- Expose binding block reasons
- NO persistence (ViewModel state only)
- NO schema mutation
- NO auto-execution

PHASE F-1/F-3/F-4/F-5/F-6/F-7 CONSTRAINTS:
- Read-only with respect to schema
- NO schema mutation
- NO formula persistence
- NO formula execution
- NO dependency graph/DAG execution
- NO topological sorting
- NO cycle prevention (analysis-only)
- NO new analysis logic (F-5: aggregation only)
- NO binding persistence (F-7: in-memory only)

INVARIANT - FORMULA DESIGN-TIME SEMANTICS:
    FormulaEditorViewModel holds formula text for EDITING; execution NEVER occurs here.
    This ViewModel provides:
    - F-1: Syntax validation and field reference checking (for UX feedback)
    - F-3: Dependency discovery (analysis only)
    - F-4: Cycle detection (analysis only)
    - F-5: Diagnostic aggregation (display only)
    - F-6: Governance evaluation (informational only)
    - F-7: Binding policy (no persistence)

    Formula EXECUTION (F-2) is FORBIDDEN in this ViewModel.
    FormulaUseCases.execute_formula() must NEVER be called from any ViewModel.
    Formula execution is a runtime/export responsibility only.

ARCHITECTURE ENFORCEMENT (Rule 0 Compliance):
- ViewModel depends ONLY on FormulaUseCases (Application layer use-case)
- NO command imports
- NO query imports
- NO repository access
- NO domain object imports
- Schema passed as DTOs (read-only snapshot)
"""

from typing import Optional

from doc_helper.application.dto.formula_dto import (
    # Phase F-4
    FormulaCycleAnalysisResultDTO,
    FormulaCycleDTO,
    # Phase F-3
    FormulaDependencyAnalysisResultDTO,
    FormulaDependencyDTO,
    # Phase F-6
    FormulaGovernanceResultDTO,
    FormulaGovernanceStatus,
    # Phase F-1
    FormulaResultType,
    FormulaValidationResultDTO,
    SchemaFieldInfoDTO,
    # Phase F-7: Formula Binding
    FormulaBindingResultDTO,
    FormulaBindingStatus,
    FormulaBindingTarget,
)
from doc_helper.application.usecases.formula_usecases import FormulaUseCases
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


class FormulaEditorViewModel(BaseViewModel):
    """ViewModel for Formula Editor.

    Responsibilities:
    - Hold formula text state
    - Perform live validation via use-case
    - Expose validation result to UI
    - Track available fields from schema
    - Analyze formula dependencies (Phase F-3)
    - Detect formula cycles (Phase F-4)
    - Aggregate diagnostics for UI display (Phase F-5)
    - Expose governance evaluation (Phase F-6)
    - Manage binding target and status (Phase F-7)

    Phase F-1 Compliance:
    - Read-only schema access (DTOs)
    - No schema mutation
    - No formula execution
    - No persistence

    Phase F-3 Compliance (ADR-040):
    - Read-only dependency analysis
    - Deterministic: same inputs → same output
    - No DAG/graph construction
    - No cycle detection
    - No execution logic

    Phase F-4 Compliance (ADR-041):
    - Read-only cycle analysis
    - Deterministic: same inputs → same output
    - No DAG execution or topological sorting
    - No cycle prevention (analysis-only)
    - Same-entity scope only

    Phase F-5 Compliance (Diagnostics & UX):
    - Aggregation only - no new logic
    - Consumes existing DTO data
    - Human-readable message formatting
    - Read-only, deterministic

    Phase F-6 Compliance (Governance & Enforcement):
    - Exposes governance evaluation from use-case
    - Read-only governance properties
    - No governance logic in ViewModel
    - Non-blocking (informational only)

    Phase F-7 Compliance (Formula Binding):
    - Hold binding target state
    - Expose binding eligibility from use-case
    - No binding persistence (ViewModel state only)
    - No schema mutation
    - No auto-execution

    Usage:
        vm = FormulaEditorViewModel(formula_usecases)
        vm.set_schema_context(schema_fields)
        vm.set_formula("field1 + field2")
        result = vm.validation_result  # FormulaValidationResultDTO
        is_valid = vm.is_valid
        result_type = vm.inferred_type
        deps = vm.dependencies  # Phase F-3: FormulaDependencyDTO tuple
        unknown = vm.unknown_fields  # Phase F-3: unknown field IDs

        # Phase F-4: Cycle detection (entity-wide)
        vm.analyze_entity_cycles({"field_a": ("field_b",), "field_b": ("field_a",)})
        has_cycles = vm.has_cycles
        cycles = vm.cycles

        # Phase F-5: Aggregated diagnostics
        all_errors = vm.all_diagnostic_errors  # All errors from F-1 to F-4
        all_warnings = vm.all_diagnostic_warnings  # All warnings
        status = vm.diagnostic_status  # Overall status

    Observable Properties:
        - formula_text: Current formula text
        - validation_result: Latest validation result DTO
        - is_valid: Whether formula is valid
        - inferred_type: Inferred result type string
        - field_references: Fields referenced in formula
        - errors: Error messages
        - warnings: Warning messages
        - dependency_analysis_result: Dependency analysis DTO (Phase F-3)
        - dependencies: FormulaDependencyDTO tuple (Phase F-3)
        - unknown_fields: Unknown field IDs (Phase F-3)
        - has_unknown_fields: Whether unknown fields exist (Phase F-3)
        - cycle_analysis_result: Cycle analysis DTO (Phase F-4)
        - has_cycles: Whether cycles exist (Phase F-4)
        - cycles: FormulaCycleDTO tuple (Phase F-4)
        - cycle_count: Number of cycles (Phase F-4)
        - all_cycle_field_ids: All fields in cycles (Phase F-4)
        - cycle_errors: Human-readable cycle errors (Phase F-4)
        - all_diagnostic_errors: Aggregated errors (Phase F-5)
        - all_diagnostic_warnings: Aggregated warnings (Phase F-5)
        - all_diagnostic_info: Aggregated info messages (Phase F-5)
        - diagnostic_status: Overall status (Phase F-5)
        - status_message: Human-readable status (Phase F-5)
        - governance_result: Governance evaluation DTO (Phase F-6)
        - governance_status: Governance status enum value (Phase F-6)
        - is_formula_allowed: Whether formula is allowed (Phase F-6)
        - is_formula_blocked: Whether formula is blocked (Phase F-6)
        - governance_message: Human-readable governance message (Phase F-6)
        - binding_target: Current binding target type (Phase F-7)
        - binding_target_id: Current binding target ID (Phase F-7)
        - is_binding_allowed: Whether binding is allowed (Phase F-7)
        - binding_block_reason: Reason binding is blocked (Phase F-7)
        - binding_status: Binding status enum value (Phase F-7)
        - binding_status_message: Human-readable binding status (Phase F-7)
        - can_save_binding: Whether binding can be saved (Phase F-7)
    """

    def __init__(
        self,
        formula_usecases: FormulaUseCases,
    ) -> None:
        """Initialize Formula Editor ViewModel.

        Args:
            formula_usecases: Use-case class for formula validation

        Architecture Compliance:
            ViewModel receives ONLY use-case class via DI.
            NO commands, queries, or repositories are injected.
        """
        super().__init__()
        self._formula_usecases = formula_usecases

        # State
        self._formula_text: str = ""
        self._validation_result: Optional[FormulaValidationResultDTO] = None
        self._dependency_analysis_result: Optional[FormulaDependencyAnalysisResultDTO] = None
        self._cycle_analysis_result: Optional[FormulaCycleAnalysisResultDTO] = None
        self._governance_result: Optional[FormulaGovernanceResultDTO] = None
        self._schema_fields: tuple[SchemaFieldInfoDTO, ...] = ()
        # Phase F-7: Binding state
        self._binding_target: Optional[FormulaBindingTarget] = None
        self._binding_target_id: str = ""

    # =========================================================================
    # Properties (Observable)
    # =========================================================================

    @property
    def formula_text(self) -> str:
        """Get current formula text."""
        return self._formula_text

    @property
    def validation_result(self) -> Optional[FormulaValidationResultDTO]:
        """Get latest validation result."""
        return self._validation_result

    @property
    def is_valid(self) -> bool:
        """Check if current formula is valid."""
        if self._validation_result is None:
            return False
        return self._validation_result.is_valid

    @property
    def inferred_type(self) -> str:
        """Get inferred result type."""
        if self._validation_result is None:
            return FormulaResultType.UNKNOWN.value
        return self._validation_result.inferred_type

    @property
    def field_references(self) -> tuple[str, ...]:
        """Get field references in current formula."""
        if self._validation_result is None:
            return ()
        return self._validation_result.field_references

    @property
    def errors(self) -> tuple[str, ...]:
        """Get validation errors."""
        if self._validation_result is None:
            return ()
        return self._validation_result.errors

    @property
    def warnings(self) -> tuple[str, ...]:
        """Get validation warnings."""
        if self._validation_result is None:
            return ()
        return self._validation_result.warnings

    @property
    def available_fields(self) -> tuple[SchemaFieldInfoDTO, ...]:
        """Get available schema fields for autocomplete."""
        return self._schema_fields

    @property
    def available_functions(self) -> tuple[str, ...]:
        """Get available formula functions."""
        return self._formula_usecases.get_available_functions()

    @property
    def has_formula(self) -> bool:
        """Check if formula text is non-empty."""
        return bool(self._formula_text.strip())

    @property
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        if self._validation_result is None:
            return False
        return self._validation_result.has_errors

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        if self._validation_result is None:
            return False
        return self._validation_result.has_warnings

    # =========================================================================
    # Phase F-3 Properties (Dependency Analysis)
    # =========================================================================

    @property
    def dependency_analysis_result(self) -> Optional[FormulaDependencyAnalysisResultDTO]:
        """Get latest dependency analysis result (Phase F-3).

        Returns:
            FormulaDependencyAnalysisResultDTO or None if not analyzed
        """
        return self._dependency_analysis_result

    @property
    def dependencies(self) -> tuple[FormulaDependencyDTO, ...]:
        """Get all formula dependencies (Phase F-3).

        Returns:
            Tuple of FormulaDependencyDTO for all referenced fields
        """
        if self._dependency_analysis_result is None:
            return ()
        return self._dependency_analysis_result.dependencies

    @property
    def known_dependencies(self) -> tuple[FormulaDependencyDTO, ...]:
        """Get only known (valid) dependencies (Phase F-3).

        Returns:
            Tuple of FormulaDependencyDTO for known fields only
        """
        if self._dependency_analysis_result is None:
            return ()
        return self._dependency_analysis_result.known_dependencies

    @property
    def unknown_fields(self) -> tuple[str, ...]:
        """Get unknown field IDs referenced in formula (Phase F-3).

        Returns:
            Tuple of field IDs not found in schema context
        """
        if self._dependency_analysis_result is None:
            return ()
        return self._dependency_analysis_result.unknown_fields

    @property
    def has_unknown_fields(self) -> bool:
        """Check if formula references unknown fields (Phase F-3).

        Returns:
            True if any referenced field is not in schema context
        """
        if self._dependency_analysis_result is None:
            return False
        return self._dependency_analysis_result.has_unknown_fields

    @property
    def dependency_count(self) -> int:
        """Get total count of dependencies (Phase F-3).

        Returns:
            Number of unique fields referenced in formula
        """
        if self._dependency_analysis_result is None:
            return 0
        return self._dependency_analysis_result.dependency_count

    @property
    def unknown_count(self) -> int:
        """Get count of unknown field references (Phase F-3).

        Returns:
            Number of unknown fields referenced in formula
        """
        if self._dependency_analysis_result is None:
            return 0
        return self._dependency_analysis_result.unknown_count

    # =========================================================================
    # Phase F-4 Properties (Cycle Detection)
    # =========================================================================

    @property
    def cycle_analysis_result(self) -> Optional[FormulaCycleAnalysisResultDTO]:
        """Get latest cycle analysis result (Phase F-4).

        Returns:
            FormulaCycleAnalysisResultDTO or None if not analyzed
        """
        return self._cycle_analysis_result

    @property
    def has_cycles(self) -> bool:
        """Check if any cycles were detected (Phase F-4).

        Returns:
            True if cycles exist in the analyzed formula dependencies
        """
        if self._cycle_analysis_result is None:
            return False
        return self._cycle_analysis_result.has_cycles

    @property
    def cycles(self) -> tuple[FormulaCycleDTO, ...]:
        """Get all detected cycles (Phase F-4).

        Returns:
            Tuple of FormulaCycleDTO for each detected cycle
        """
        if self._cycle_analysis_result is None:
            return ()
        return self._cycle_analysis_result.cycles

    @property
    def cycle_count(self) -> int:
        """Get count of detected cycles (Phase F-4).

        Returns:
            Number of cycles detected
        """
        if self._cycle_analysis_result is None:
            return 0
        return self._cycle_analysis_result.cycle_count

    @property
    def all_cycle_field_ids(self) -> tuple[str, ...]:
        """Get all field IDs involved in cycles (Phase F-4).

        Returns:
            Tuple of field IDs that are part of any cycle
        """
        if self._cycle_analysis_result is None:
            return ()
        return self._cycle_analysis_result.all_cycle_field_ids

    @property
    def cycle_errors(self) -> tuple[str, ...]:
        """Get human-readable cycle error messages (Phase F-4).

        Returns:
            Tuple of error messages describing each cycle
        """
        if self._cycle_analysis_result is None:
            return ()
        return self._cycle_analysis_result.cycle_errors

    @property
    def analyzed_field_count(self) -> int:
        """Get count of formula fields analyzed (Phase F-4).

        Returns:
            Number of formula fields included in cycle analysis
        """
        if self._cycle_analysis_result is None:
            return 0
        return self._cycle_analysis_result.analyzed_field_count

    # =========================================================================
    # Phase F-5 Properties (Diagnostic Aggregation)
    # =========================================================================

    @property
    def all_diagnostic_errors(self) -> tuple[str, ...]:
        """Get all errors aggregated from F-1 through F-4 (Phase F-5).

        Aggregates errors from:
        - Validation errors (F-1)
        - Unknown field references (F-3)
        - Cycle detection errors (F-4)

        Returns:
            Tuple of human-readable error messages

        Phase F-5 Compliance:
            Aggregation only - no new logic or analysis.

        Note:
            Returns empty tuple if no formula text (better UX - no scary
            errors when user hasn't typed anything yet).
        """
        # UX: Don't show errors if there's no formula yet
        if not self.has_formula:
            return ()

        errors: list[str] = []

        # F-1: Validation errors
        if self._validation_result is not None:
            for error in self._validation_result.errors:
                errors.append(f"Syntax: {error}")

        # F-3: Unknown field errors (these are errors, not warnings)
        if self._dependency_analysis_result is not None:
            for field_id in self._dependency_analysis_result.unknown_fields:
                errors.append(f"Unknown field: {field_id}")

        # F-4: Cycle errors
        if self._cycle_analysis_result is not None:
            for cycle in self._cycle_analysis_result.cycles:
                errors.append(f"Circular dependency: {cycle.cycle_path}")

        return tuple(errors)

    @property
    def all_diagnostic_warnings(self) -> tuple[str, ...]:
        """Get all warnings aggregated from F-1 through F-4 (Phase F-5).

        Aggregates warnings from:
        - Type mismatch warnings (F-1)
        - Other validation warnings (F-1)

        Returns:
            Tuple of human-readable warning messages

        Phase F-5 Compliance:
            Aggregation only - no new logic or analysis.

        Note:
            Returns empty tuple if no formula text (consistent with errors).
        """
        # UX: Don't show warnings if there's no formula yet
        if not self.has_formula:
            return ()

        warnings: list[str] = []

        # F-1: Validation warnings
        if self._validation_result is not None:
            for warning in self._validation_result.warnings:
                warnings.append(f"Type: {warning}")

        return tuple(warnings)

    @property
    def all_diagnostic_info(self) -> tuple[str, ...]:
        """Get all info messages aggregated from F-1 through F-4 (Phase F-5).

        Aggregates informational messages from:
        - Inferred result type (F-1)
        - Dependencies list (F-3)
        - Analyzed field count (F-4)

        Returns:
            Tuple of human-readable info messages

        Phase F-5 Compliance:
            Aggregation only - no new logic or analysis.

        Note:
            Returns empty tuple if no formula text (consistent with errors).
        """
        # UX: Don't show info if there's no formula yet
        if not self.has_formula:
            return ()

        info: list[str] = []

        # F-1: Inferred type
        if self._validation_result is not None:
            info.append(f"Result type: {self._validation_result.inferred_type}")

        # F-3: Dependencies
        if self._dependency_analysis_result is not None:
            known_deps = self._dependency_analysis_result.known_dependencies
            if known_deps:
                dep_names = ", ".join(d.field_id for d in known_deps)
                info.append(f"Depends on: {dep_names}")

        # F-4: Analysis summary (only if cycle analysis was performed)
        if self._cycle_analysis_result is not None:
            count = self._cycle_analysis_result.analyzed_field_count
            if count > 0:
                info.append(f"Analyzed {count} formula field(s)")

        return tuple(info)

    @property
    def diagnostic_status(self) -> str:
        """Get overall diagnostic status (Phase F-5).

        Returns one of:
        - "empty": No formula entered
        - "error": Has errors (validation, unknown fields, or cycles)
        - "warning": Has warnings but no errors
        - "valid": No errors or warnings

        Phase F-5 Compliance:
            Aggregation only - reads existing properties.
        """
        if not self.has_formula:
            return "empty"

        # Check for any errors
        if len(self.all_diagnostic_errors) > 0:
            return "error"

        # Check for any warnings
        if len(self.all_diagnostic_warnings) > 0:
            return "warning"

        return "valid"

    @property
    def status_message(self) -> str:
        """Get human-readable status message (Phase F-5).

        Returns a concise status message suitable for inline display.

        Phase F-5 Compliance:
            Aggregation only - maps existing status to message.
        """
        status = self.diagnostic_status

        if status == "empty":
            return ""
        elif status == "error":
            error_count = len(self.all_diagnostic_errors)
            return f"Formula has {error_count} error(s)"
        elif status == "warning":
            warning_count = len(self.all_diagnostic_warnings)
            return f"Formula has {warning_count} warning(s)"
        else:
            return "Formula is valid"

    @property
    def has_diagnostics(self) -> bool:
        """Check if any diagnostics exist (Phase F-5).

        Returns:
            True if there are any errors, warnings, or info messages
        """
        return (
            len(self.all_diagnostic_errors) > 0
            or len(self.all_diagnostic_warnings) > 0
            or len(self.all_diagnostic_info) > 0
        )

    @property
    def diagnostic_error_count(self) -> int:
        """Get total count of diagnostic errors (Phase F-5)."""
        return len(self.all_diagnostic_errors)

    @property
    def diagnostic_warning_count(self) -> int:
        """Get total count of diagnostic warnings (Phase F-5)."""
        return len(self.all_diagnostic_warnings)

    # =========================================================================
    # Phase F-6 Properties (Governance & Enforcement)
    # =========================================================================

    @property
    def governance_result(self) -> Optional[FormulaGovernanceResultDTO]:
        """Get latest governance evaluation result (Phase F-6).

        Returns:
            FormulaGovernanceResultDTO or None if not evaluated
        """
        return self._governance_result

    @property
    def governance_status(self) -> FormulaGovernanceStatus:
        """Get governance status (Phase F-6).

        Returns:
            FormulaGovernanceStatus enum value. Returns EMPTY if not evaluated.
        """
        if self._governance_result is None:
            return FormulaGovernanceStatus.EMPTY
        return self._governance_result.status

    @property
    def is_formula_allowed(self) -> bool:
        """Check if formula is allowed by governance (Phase F-6).

        A formula is allowed if:
        - No formula text (EMPTY status)
        - Valid with no issues (VALID status)
        - Valid with warnings (VALID_WITH_WARNINGS status)

        Only INVALID status blocks the formula.

        Returns:
            True if formula is allowed (not blocked)
        """
        if self._governance_result is None:
            return True  # No evaluation = allowed (empty/neutral)
        return self._governance_result.is_allowed

    @property
    def is_formula_blocked(self) -> bool:
        """Check if formula is blocked by governance (Phase F-6).

        A formula is blocked only if it has INVALID status due to:
        - Syntax errors
        - Unknown field references
        - Circular dependencies

        Returns:
            True if formula is blocked (INVALID status)
        """
        if self._governance_result is None:
            return False  # No evaluation = not blocked
        return self._governance_result.is_blocked

    @property
    def governance_message(self) -> str:
        """Get human-readable governance message (Phase F-6).

        Returns a concise summary message describing the governance decision.

        Returns:
            Human-readable governance summary
        """
        if self._governance_result is None:
            return ""
        return self._governance_result.summary_message

    @property
    def governance_blocking_reasons(self) -> tuple[str, ...]:
        """Get blocking reasons from governance (Phase F-6).

        Returns:
            Tuple of reasons why formula is blocked (empty if not blocked)
        """
        if self._governance_result is None:
            return ()
        return self._governance_result.blocking_reasons

    @property
    def governance_warning_reasons(self) -> tuple[str, ...]:
        """Get warning reasons from governance (Phase F-6).

        Returns:
            Tuple of warning reasons (non-blocking issues)
        """
        if self._governance_result is None:
            return ()
        return self._governance_result.warning_reasons

    # =========================================================================
    # Phase F-7 Properties (Formula Binding)
    # =========================================================================

    @property
    def binding_target(self) -> Optional[FormulaBindingTarget]:
        """Get current binding target type (Phase F-7).

        Returns:
            FormulaBindingTarget or None if no target set
        """
        return self._binding_target

    @property
    def binding_target_id(self) -> str:
        """Get current binding target ID (Phase F-7).

        Returns:
            Target ID (e.g., field_id) or empty string if not set
        """
        return self._binding_target_id

    @property
    def is_binding_allowed(self) -> bool:
        """Check if formula can be bound to current target (Phase F-7).

        Evaluates binding rules:
        - CALCULATED_FIELD: Allowed if governance is not INVALID
        - VALIDATION_RULE/OUTPUT_MAPPING: FORBIDDEN in Phase F-7

        Returns:
            True if binding is allowed, False otherwise

        Phase F-7 Compliance:
            Pure property - reads governance state and target.
            No side effects.
        """
        if self._binding_target is None:
            return False

        if self._governance_result is None:
            return False

        # Use use-case to evaluate binding eligibility
        result = self._formula_usecases.can_bind_formula(
            target_type=self._binding_target,
            governance_result=self._governance_result,
        )
        return result.is_allowed

    @property
    def binding_block_reason(self) -> Optional[str]:
        """Get reason why binding is blocked (Phase F-7).

        Returns:
            Block reason string, or None if binding is allowed

        Phase F-7 Compliance:
            Pure property - reads governance state and target.
            No side effects.
        """
        if self._binding_target is None:
            return "No binding target set"

        if self._governance_result is None:
            return "Governance not evaluated"

        result = self._formula_usecases.can_bind_formula(
            target_type=self._binding_target,
            governance_result=self._governance_result,
        )
        return result.block_reason

    @property
    def binding_status(self) -> FormulaBindingStatus:
        """Get current binding status (Phase F-7).

        Returns:
            FormulaBindingStatus enum value

        Phase F-7 Compliance:
            Pure property - reads governance state and target.
            No side effects.
        """
        if self._binding_target is None:
            return FormulaBindingStatus.BLOCKED_UNSUPPORTED_TARGET

        if self._governance_result is None:
            # If formula is empty (cleared), return CLEARED status
            if not self._formula_text or not self._formula_text.strip():
                return FormulaBindingStatus.CLEARED
            return FormulaBindingStatus.BLOCKED_INVALID_FORMULA

        result = self._formula_usecases.can_bind_formula(
            target_type=self._binding_target,
            governance_result=self._governance_result,
        )
        return result.status

    @property
    def binding_status_message(self) -> str:
        """Get human-readable binding status message (Phase F-7).

        Returns:
            Human-readable status message describing binding eligibility

        Phase F-7 Compliance:
            Pure property - reads binding status and formats message.
            No side effects.
        """
        if self._binding_target is None:
            return "No binding target configured"

        if self._governance_result is None:
            return "Formula not validated"

        result = self._formula_usecases.can_bind_formula(
            target_type=self._binding_target,
            governance_result=self._governance_result,
        )
        return result.status_message

    @property
    def can_save_binding(self) -> bool:
        """Check if binding can be saved (Phase F-7).

        A binding can be saved if:
        - Binding target is set
        - Binding is allowed (or formula is empty/cleared)

        Returns:
            True if binding can be saved

        Phase F-7 Compliance:
            Pure property - no persistence occurs here.
            Caller is responsible for actual persistence.
        """
        if self._binding_target is None:
            return False

        status = self.binding_status
        return status in (
            FormulaBindingStatus.ALLOWED,
            FormulaBindingStatus.CLEARED,
        )

    # =========================================================================
    # Commands (User Actions)
    # =========================================================================

    def set_schema_context(
        self,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Set schema context for validation.

        This provides the schema snapshot for formula validation.
        Must be called before validation can check field references.

        Args:
            schema_fields: Read-only schema field snapshot (DTOs)

        Phase F-1 Compliance:
            Schema is passed as DTOs (read-only snapshot).
            No schema mutation occurs.
        """
        self._schema_fields = schema_fields
        self.notify_change("available_fields")

        # Re-validate if formula exists
        if self._formula_text.strip():
            self._validate_formula()

    def set_formula(self, formula_text: str) -> None:
        """Set formula text and validate.

        Args:
            formula_text: New formula text

        Triggers validation and notifies all observers.
        """
        self._formula_text = formula_text
        self.notify_change("formula_text")
        self.notify_change("has_formula")

        # Validate the formula
        self._validate_formula()

    def clear_formula(self) -> None:
        """Clear formula text, validation result, dependency analysis, cycle analysis, governance, and binding."""
        self._formula_text = ""
        self._validation_result = None
        self._dependency_analysis_result = None
        self._cycle_analysis_result = None
        self._governance_result = None
        # Note: binding target is NOT cleared - it's context, not formula data

        self.notify_change("formula_text")
        self.notify_change("has_formula")
        self.notify_change("validation_result")
        self.notify_change("is_valid")
        self.notify_change("inferred_type")
        self.notify_change("field_references")
        self.notify_change("errors")
        self.notify_change("warnings")
        self.notify_change("has_errors")
        self.notify_change("has_warnings")
        # Phase F-3 notifications
        self.notify_change("dependency_analysis_result")
        self.notify_change("dependencies")
        self.notify_change("known_dependencies")
        self.notify_change("unknown_fields")
        self.notify_change("has_unknown_fields")
        self.notify_change("dependency_count")
        self.notify_change("unknown_count")
        # Phase F-4 notifications
        self.notify_change("cycle_analysis_result")
        self.notify_change("has_cycles")
        self.notify_change("cycles")
        self.notify_change("cycle_count")
        self.notify_change("all_cycle_field_ids")
        self.notify_change("cycle_errors")
        self.notify_change("analyzed_field_count")
        # Phase F-5 notifications (diagnostic aggregation)
        self.notify_change("all_diagnostic_errors")
        self.notify_change("all_diagnostic_warnings")
        self.notify_change("all_diagnostic_info")
        self.notify_change("diagnostic_status")
        self.notify_change("status_message")
        self.notify_change("has_diagnostics")
        self.notify_change("diagnostic_error_count")
        self.notify_change("diagnostic_warning_count")
        # Phase F-6 notifications (governance)
        self.notify_change("governance_result")
        self.notify_change("governance_status")
        self.notify_change("is_formula_allowed")
        self.notify_change("is_formula_blocked")
        self.notify_change("governance_message")
        self.notify_change("governance_blocking_reasons")
        self.notify_change("governance_warning_reasons")
        # Phase F-7 notifications (binding status may change with cleared formula)
        self.notify_change("is_binding_allowed")
        self.notify_change("binding_block_reason")
        self.notify_change("binding_status")
        self.notify_change("binding_status_message")
        self.notify_change("can_save_binding")

    def validate(self) -> FormulaValidationResultDTO:
        """Manually trigger validation.

        Returns:
            FormulaValidationResultDTO with validation results
        """
        self._validate_formula()
        return self._validation_result or FormulaValidationResultDTO(
            is_valid=False,
            errors=("No formula to validate",),
            warnings=(),
            inferred_type=FormulaResultType.UNKNOWN.value,
            field_references=(),
        )

    # =========================================================================
    # Phase F-7 Commands (Binding Actions)
    # =========================================================================

    def set_binding_target(
        self,
        target_type: FormulaBindingTarget,
        target_id: str,
    ) -> None:
        """Set the binding target for formula (Phase F-7).

        Args:
            target_type: The binding target type (CALCULATED_FIELD, etc.)
            target_id: ID of the target (e.g., field_id for CALCULATED_FIELD)

        Phase F-7 Compliance:
            Sets binding context for subsequent binding operations.
            No persistence occurs here.
        """
        self._binding_target = target_type
        self._binding_target_id = target_id

        # Notify binding-related properties
        self.notify_change("binding_target")
        self.notify_change("binding_target_id")
        self.notify_change("is_binding_allowed")
        self.notify_change("binding_block_reason")
        self.notify_change("binding_status")
        self.notify_change("binding_status_message")
        self.notify_change("can_save_binding")

    def clear_binding_target(self) -> None:
        """Clear the binding target (Phase F-7).

        Resets binding context to no target.

        Phase F-7 Compliance:
            Clears binding context only.
            No persistence occurs here.
        """
        self._binding_target = None
        self._binding_target_id = ""

        # Notify binding-related properties
        self.notify_change("binding_target")
        self.notify_change("binding_target_id")
        self.notify_change("is_binding_allowed")
        self.notify_change("binding_block_reason")
        self.notify_change("binding_status")
        self.notify_change("binding_status_message")
        self.notify_change("can_save_binding")

    def get_binding_result(self) -> FormulaBindingResultDTO:
        """Get the binding result for current formula and target (Phase F-7).

        Returns a FormulaBindingResultDTO indicating whether binding is
        allowed and, if so, contains the binding DTO to be persisted.

        Returns:
            FormulaBindingResultDTO with:
            - status: ALLOWED, BLOCKED_*, or CLEARED
            - binding: FormulaBindingDTO if allowed, None otherwise
            - block_reason: Reason if blocked

        Phase F-7 Compliance:
            Pure operation - creates binding result DTO.
            No persistence occurs here.
            Caller is responsible for actual persistence.

        Usage:
            vm.set_binding_target(FormulaBindingTarget.CALCULATED_FIELD, "total")
            vm.set_formula("price * quantity")
            result = vm.get_binding_result()
            if result.is_allowed:
                binding = result.binding
                # Persist binding to schema
            else:
                # Show block reason
                print(result.block_reason)
        """
        if self._binding_target is None:
            return FormulaBindingResultDTO(
                status=FormulaBindingStatus.BLOCKED_UNSUPPORTED_TARGET,
                binding=None,
                block_reason="No binding target set",
            )

        if self._governance_result is None:
            return FormulaBindingResultDTO(
                status=FormulaBindingStatus.BLOCKED_INVALID_FORMULA,
                binding=None,
                block_reason="Formula not validated",
            )

        # Use use-case to create binding
        return self._formula_usecases.bind_formula(
            target_type=self._binding_target,
            target_id=self._binding_target_id,
            formula_text=self._formula_text,
            governance_result=self._governance_result,
        )

    def analyze_entity_cycles(
        self,
        formula_dependencies: dict[str, tuple[str, ...]],
    ) -> FormulaCycleAnalysisResultDTO:
        """Analyze cycles in entity-wide formula dependencies (Phase F-4).

        This method analyzes the entire formula dependency graph for an entity
        to detect circular dependencies. Call this when the entity's formula
        field definitions are available.

        Args:
            formula_dependencies: Mapping from formula field ID to its
                dependency field IDs. Only include CALCULATED fields.
                Example: {"total": ("subtotal", "tax"), "tax": ("subtotal",)}

        Returns:
            FormulaCycleAnalysisResultDTO with cycle information

        Phase F-4 Compliance (ADR-041):
        - Read-only analysis (no mutation)
        - Deterministic output
        - No DAG execution or topological sorting
        - No cycle prevention (analysis-only)
        - Does NOT block saves or edits

        Usage:
            # Collect formula dependencies from entity schema
            deps = {
                "field_a": ("field_b",),
                "field_b": ("field_a",),  # Creates a cycle
            }
            result = vm.analyze_entity_cycles(deps)
            if result.has_cycles:
                for cycle in result.cycles:
                    print(f"Cycle detected: {cycle.cycle_path}")
        """
        self._cycle_analysis_result = self._formula_usecases.detect_cycles(
            formula_dependencies=formula_dependencies,
        )

        # Re-evaluate governance after cycle analysis (Phase F-6)
        # Cycles affect governance status
        self._governance_result = self._formula_usecases.evaluate_governance(
            formula_text=self._formula_text,
            validation_result=self._validation_result,
            cycle_result=self._cycle_analysis_result,
        )

        # Notify observers of cycle-related property changes
        self.notify_change("cycle_analysis_result")
        self.notify_change("has_cycles")
        self.notify_change("cycles")
        self.notify_change("cycle_count")
        self.notify_change("all_cycle_field_ids")
        self.notify_change("cycle_errors")
        self.notify_change("analyzed_field_count")
        # Phase F-5 notifications (cycle changes affect diagnostics)
        self.notify_change("all_diagnostic_errors")
        self.notify_change("all_diagnostic_info")
        self.notify_change("diagnostic_status")
        self.notify_change("status_message")
        self.notify_change("has_diagnostics")
        self.notify_change("diagnostic_error_count")
        # Phase F-6 notifications (cycle changes affect governance)
        self.notify_change("governance_result")
        self.notify_change("governance_status")
        self.notify_change("is_formula_allowed")
        self.notify_change("is_formula_blocked")
        self.notify_change("governance_message")
        self.notify_change("governance_blocking_reasons")
        self.notify_change("governance_warning_reasons")

        return self._cycle_analysis_result

    def clear_cycle_analysis(self) -> None:
        """Clear cycle analysis result (Phase F-4).

        Use this to reset cycle state when navigating away from an entity
        or when the formula dependencies have changed significantly.
        """
        self._cycle_analysis_result = None

        # Re-evaluate governance without cycle data (Phase F-6)
        self._governance_result = self._formula_usecases.evaluate_governance(
            formula_text=self._formula_text,
            validation_result=self._validation_result,
            cycle_result=None,
        )

        self.notify_change("cycle_analysis_result")
        self.notify_change("has_cycles")
        self.notify_change("cycles")
        self.notify_change("cycle_count")
        self.notify_change("all_cycle_field_ids")
        self.notify_change("cycle_errors")
        self.notify_change("analyzed_field_count")
        # Phase F-5 notifications (cycle changes affect diagnostics)
        self.notify_change("all_diagnostic_errors")
        self.notify_change("all_diagnostic_info")
        self.notify_change("diagnostic_status")
        self.notify_change("status_message")
        self.notify_change("has_diagnostics")
        self.notify_change("diagnostic_error_count")
        # Phase F-6 notifications (cycle changes affect governance)
        self.notify_change("governance_result")
        self.notify_change("governance_status")
        self.notify_change("is_formula_allowed")
        self.notify_change("is_formula_blocked")
        self.notify_change("governance_message")
        self.notify_change("governance_blocking_reasons")
        self.notify_change("governance_warning_reasons")

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _validate_formula(self) -> None:
        """Validate current formula text, analyze dependencies, and evaluate governance.

        Internal method that:
        1. Calls use-case for validation (Phase F-1)
        2. Calls use-case for dependency analysis (Phase F-3)
        3. Calls use-case for governance evaluation (Phase F-6)
        4. Updates all result states
        5. Notifies all relevant observers
        """
        # Validate via use-case (Phase F-1)
        self._validation_result = self._formula_usecases.validate_formula(
            formula_text=self._formula_text,
            schema_fields=self._schema_fields,
        )

        # Analyze dependencies via use-case (Phase F-3)
        self._dependency_analysis_result = self._formula_usecases.analyze_dependencies(
            formula_text=self._formula_text,
            schema_fields=self._schema_fields,
        )

        # Evaluate governance via use-case (Phase F-6)
        # Note: Cycle analysis is handled separately via analyze_entity_cycles()
        # so we pass None for cycle_result here. Entity-wide governance
        # evaluation should be triggered by calling evaluate_entity_governance().
        self._governance_result = self._formula_usecases.evaluate_governance(
            formula_text=self._formula_text,
            validation_result=self._validation_result,
            cycle_result=self._cycle_analysis_result,
        )

        # Notify all observers
        self.notify_change("validation_result")
        self.notify_change("is_valid")
        self.notify_change("inferred_type")
        self.notify_change("field_references")
        self.notify_change("errors")
        self.notify_change("warnings")
        self.notify_change("has_errors")
        self.notify_change("has_warnings")
        # Phase F-3 notifications
        self.notify_change("dependency_analysis_result")
        self.notify_change("dependencies")
        self.notify_change("known_dependencies")
        self.notify_change("unknown_fields")
        self.notify_change("has_unknown_fields")
        self.notify_change("dependency_count")
        self.notify_change("unknown_count")
        # Phase F-5 notifications (diagnostic aggregation)
        self.notify_change("all_diagnostic_errors")
        self.notify_change("all_diagnostic_warnings")
        self.notify_change("all_diagnostic_info")
        self.notify_change("diagnostic_status")
        self.notify_change("status_message")
        self.notify_change("has_diagnostics")
        self.notify_change("diagnostic_error_count")
        self.notify_change("diagnostic_warning_count")
        # Phase F-6 notifications (governance)
        self.notify_change("governance_result")
        self.notify_change("governance_status")
        self.notify_change("is_formula_allowed")
        self.notify_change("is_formula_blocked")
        self.notify_change("governance_message")
        self.notify_change("governance_blocking_reasons")
        self.notify_change("governance_warning_reasons")

    def dispose(self) -> None:
        """Clean up resources."""
        super().dispose()
        self._formula_text = ""
        self._validation_result = None
        self._dependency_analysis_result = None
        self._cycle_analysis_result = None
        self._governance_result = None
        self._schema_fields = ()
        # Phase F-7: Clear binding state
        self._binding_target = None
        self._binding_target_id = ""

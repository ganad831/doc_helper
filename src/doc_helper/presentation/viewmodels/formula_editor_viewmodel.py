"""Formula Editor ViewModel (Phase F-1, F-3, F-4: Formula Editor).

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

PHASE F-1/F-3/F-4 CONSTRAINTS:
- Read-only with respect to schema
- NO schema mutation
- NO formula persistence
- NO formula execution
- NO dependency graph/DAG execution
- NO topological sorting
- NO cycle prevention (analysis-only)

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
    FormulaCycleAnalysisResultDTO,
    FormulaCycleDTO,
    FormulaDependencyAnalysisResultDTO,
    FormulaDependencyDTO,
    FormulaResultType,
    FormulaValidationResultDTO,
    SchemaFieldInfoDTO,
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
        self._schema_fields: tuple[SchemaFieldInfoDTO, ...] = ()

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
        """Clear formula text, validation result, dependency analysis, and cycle analysis."""
        self._formula_text = ""
        self._validation_result = None
        self._dependency_analysis_result = None
        self._cycle_analysis_result = None

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

        # Notify observers of cycle-related property changes
        self.notify_change("cycle_analysis_result")
        self.notify_change("has_cycles")
        self.notify_change("cycles")
        self.notify_change("cycle_count")
        self.notify_change("all_cycle_field_ids")
        self.notify_change("cycle_errors")
        self.notify_change("analyzed_field_count")

        return self._cycle_analysis_result

    def clear_cycle_analysis(self) -> None:
        """Clear cycle analysis result (Phase F-4).

        Use this to reset cycle state when navigating away from an entity
        or when the formula dependencies have changed significantly.
        """
        self._cycle_analysis_result = None

        self.notify_change("cycle_analysis_result")
        self.notify_change("has_cycles")
        self.notify_change("cycles")
        self.notify_change("cycle_count")
        self.notify_change("all_cycle_field_ids")
        self.notify_change("cycle_errors")
        self.notify_change("analyzed_field_count")

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _validate_formula(self) -> None:
        """Validate current formula text and analyze dependencies.

        Internal method that:
        1. Calls use-case for validation
        2. Calls use-case for dependency analysis (Phase F-3)
        3. Updates validation and dependency result states
        4. Notifies all relevant observers
        """
        # Validate via use-case
        self._validation_result = self._formula_usecases.validate_formula(
            formula_text=self._formula_text,
            schema_fields=self._schema_fields,
        )

        # Analyze dependencies via use-case (Phase F-3)
        self._dependency_analysis_result = self._formula_usecases.analyze_dependencies(
            formula_text=self._formula_text,
            schema_fields=self._schema_fields,
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

    def dispose(self) -> None:
        """Clean up resources."""
        super().dispose()
        self._formula_text = ""
        self._validation_result = None
        self._dependency_analysis_result = None
        self._cycle_analysis_result = None
        self._schema_fields = ()

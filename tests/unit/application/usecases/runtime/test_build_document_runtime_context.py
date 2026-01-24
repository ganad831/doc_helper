"""Unit tests for BuildDocumentRuntimeContextUseCase (Phase R-6).

Tests document runtime context building following ADR-050 requirements:
- Pull-based evaluation
- Deterministic behavior
- Blocking semantics preserved
- Single-entity scope
- No rendering or IO logic
"""

from doc_helper.application.dto.runtime_dto import (
    DocumentRuntimeContextDTO,
    EntityOutputMappingResultDTO,
    EntityOutputMappingsEvaluationDTO,
    FormFieldRuntimeStateDTO,
    FormRuntimeStateDTO,
)
from doc_helper.application.usecases.runtime.build_document_runtime_context import (
    BuildDocumentRuntimeContextUseCase,
)


# =============================================================================
# Test 1: Successful document context build - all components present
# =============================================================================


def test_successful_document_context_build():
    """Test: Complete document context built from runtime results.

    ADR-050: All runtime results merged into document-ready context.
    """
    # Arrange: Create form state with one field
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="name",
                visible=True,
                enabled=True,
                required=True,
                validation_errors=(),
                validation_warnings=(),
                validation_info=(),
            ),
        ),
        has_blocking_errors=False,
    )

    # Create output mappings result
    output_mappings = EntityOutputMappingsEvaluationDTO.success_result(
        entity_id="project",
        values={"TEXT": "Test Project"},
    )

    # Create field values
    field_values = {"name": "Test Project"}

    # Create use case
    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert context.entity_id == "project"
    assert len(context.fields) == 1
    assert context.fields[0].field_id == "name"
    assert context.fields[0].value == "Test Project"
    assert context.fields[0].visible is True
    assert context.fields[0].enabled is True
    assert context.fields[0].required is True
    assert context.output_values == {"TEXT": "Test Project"}
    assert context.has_blocking_errors is False


# =============================================================================
# Test 2: Field visibility respected
# =============================================================================


def test_field_visibility_respected():
    """Test: Hidden fields marked as not visible in document context.

    ADR-050: Control rule visibility state propagated to document context.
    """
    # Arrange: Create form state with hidden field
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="hidden_field",
                visible=False,  # Hidden by control rule
                enabled=True,
                required=False,
                validation_errors=(),
                validation_warnings=(),
                validation_info=(),
            ),
        ),
        has_blocking_errors=False,
    )

    output_mappings = EntityOutputMappingsEvaluationDTO.empty(entity_id="project")
    field_values = {"hidden_field": "secret"}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert len(context.fields) == 1
    assert context.fields[0].field_id == "hidden_field"
    assert context.fields[0].visible is False
    assert context.fields[0].value == "secret"


# =============================================================================
# Test 3: Disabled fields preserved
# =============================================================================


def test_disabled_fields_preserved():
    """Test: Disabled fields marked as not enabled in document context.

    ADR-050: Control rule enabled state propagated to document context.
    """
    # Arrange: Create form state with disabled field
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="readonly_field",
                visible=True,
                enabled=False,  # Disabled by control rule
                required=False,
                validation_errors=(),
                validation_warnings=(),
                validation_info=(),
            ),
        ),
        has_blocking_errors=False,
    )

    output_mappings = EntityOutputMappingsEvaluationDTO.empty(entity_id="project")
    field_values = {"readonly_field": "immutable"}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert len(context.fields) == 1
    assert context.fields[0].field_id == "readonly_field"
    assert context.fields[0].enabled is False
    assert context.fields[0].value == "immutable"


# =============================================================================
# Test 4: Required fields preserved
# =============================================================================


def test_required_fields_preserved():
    """Test: Required fields marked as required in document context.

    ADR-050: Control rule required state propagated to document context.
    """
    # Arrange: Create form state with required field
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="mandatory_field",
                visible=True,
                enabled=True,
                required=True,  # Required by control rule
                validation_errors=(),
                validation_warnings=(),
                validation_info=(),
            ),
        ),
        has_blocking_errors=False,
    )

    output_mappings = EntityOutputMappingsEvaluationDTO.empty(entity_id="project")
    field_values = {"mandatory_field": "must_exist"}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert len(context.fields) == 1
    assert context.fields[0].field_id == "mandatory_field"
    assert context.fields[0].required is True
    assert context.fields[0].value == "must_exist"


# =============================================================================
# Test 5: Validation errors propagate
# =============================================================================


def test_validation_errors_propagate():
    """Test: Validation errors included in document context.

    ADR-050: ERROR severity validation issues propagate to document context.
    """
    # Arrange: Create form state with validation error
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="invalid_field",
                visible=True,
                enabled=True,
                required=True,
                validation_errors=("Field is required",),  # ERROR
                validation_warnings=(),
                validation_info=(),
            ),
        ),
        has_blocking_errors=True,  # Blocked by ERROR
    )

    output_mappings = EntityOutputMappingsEvaluationDTO.empty(entity_id="project")
    field_values = {"invalid_field": ""}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert len(context.fields) == 1
    assert context.fields[0].field_id == "invalid_field"
    assert context.fields[0].validation_errors == ("Field is required",)
    assert context.has_blocking_errors is True  # Blocked by validation error


# =============================================================================
# Test 6: Validation warnings propagate
# =============================================================================


def test_validation_warnings_propagate():
    """Test: Validation warnings included but don't block.

    ADR-050: WARNING severity validation issues propagate but are non-blocking.
    """
    # Arrange: Create form state with validation warning
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="warning_field",
                visible=True,
                enabled=True,
                required=False,
                validation_errors=(),
                validation_warnings=("Value is suspicious",),  # WARNING
                validation_info=(),
            ),
        ),
        has_blocking_errors=False,  # Not blocked by WARNING
    )

    output_mappings = EntityOutputMappingsEvaluationDTO.empty(entity_id="project")
    field_values = {"warning_field": "odd_value"}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert len(context.fields) == 1
    assert context.fields[0].field_id == "warning_field"
    assert context.fields[0].validation_warnings == ("Value is suspicious",)
    assert context.has_blocking_errors is False  # Warnings don't block


# =============================================================================
# Test 7: Output values included correctly
# =============================================================================


def test_output_values_included():
    """Test: Output mapping values from R-5 included in context.

    ADR-050: Output values from Phase R-5 merged into document context.
    """
    # Arrange: Create form state
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="depth",
                visible=True,
                enabled=True,
                required=False,
                validation_errors=(),
                validation_warnings=(),
                validation_info=(),
            ),
        ),
        has_blocking_errors=False,
    )

    # Create output mappings with multiple values
    output_mappings = EntityOutputMappingsEvaluationDTO.success_result(
        entity_id="project",
        values={
            "NUMBER": 10.5,
            "TEXT": "10.5 meters",
            "BOOLEAN": True,
        },
    )

    field_values = {"depth": 10.5}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert context.output_values == {
        "NUMBER": 10.5,
        "TEXT": "10.5 meters",
        "BOOLEAN": True,
    }
    assert context.has_blocking_errors is False


# =============================================================================
# Test 8: Blocking output mapping blocks document
# =============================================================================


def test_output_mapping_failure_blocks():
    """Test: Output mapping failure sets has_blocking_errors=True.

    ADR-050: Output mapping failures BLOCK document generation.
    """
    # Arrange: Create form state (no validation errors)
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="depth",
                visible=True,
                enabled=True,
                required=False,
                validation_errors=(),
                validation_warnings=(),
                validation_info=(),
            ),
        ),
        has_blocking_errors=False,  # No validation errors
    )

    # Create FAILED output mappings
    output_mappings = EntityOutputMappingsEvaluationDTO.failure(
        entity_id="project",
        error="Output mapping evaluation failed",
    )

    field_values = {"depth": 10.5}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert context.output_values == {}  # Empty due to failure
    assert context.has_blocking_errors is True  # Blocked by output mapping failure


# =============================================================================
# Test 9: Determinism - same inputs yield same outputs
# =============================================================================


def test_determinism():
    """Test: Determinism - same inputs → identical outputs.

    ADR-050: Same inputs produce identical results on multiple calls.
    """
    # Arrange
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="name",
                visible=True,
                enabled=True,
                required=False,
                validation_errors=(),
                validation_warnings=(),
                validation_info=(),
            ),
        ),
        has_blocking_errors=False,
    )

    output_mappings = EntityOutputMappingsEvaluationDTO.success_result(
        entity_id="project",
        values={"TEXT": "Test"},
    )

    field_values = {"name": "Test"}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act: Execute twice with same inputs
    context1 = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )
    context2 = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert: Both results identical
    assert context1.entity_id == context2.entity_id
    assert context1.fields == context2.fields
    assert context1.output_values == context2.output_values
    assert context1.has_blocking_errors == context2.has_blocking_errors


# =============================================================================
# Test 10: Empty output mappings handled correctly
# =============================================================================


def test_empty_output_mappings():
    """Test: Empty output mappings → empty output_values, not blocked.

    ADR-050: No output mappings is NOT an error (empty dict, not blocking).
    """
    # Arrange: Create form state
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="name",
                visible=True,
                enabled=True,
                required=False,
                validation_errors=(),
                validation_warnings=(),
                validation_info=(),
            ),
        ),
        has_blocking_errors=False,
    )

    # Create EMPTY output mappings (no mappings, not failure)
    output_mappings = EntityOutputMappingsEvaluationDTO.empty(entity_id="project")

    field_values = {"name": "Test"}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert context.output_values == {}  # Empty dict
    assert context.has_blocking_errors is False  # Not blocked


# =============================================================================
# Test 11: Field value None when not in field_values dict
# =============================================================================


def test_field_value_none_when_missing():
    """Test: Field value is None if not present in field_values dict.

    ADR-050: Missing field values handled gracefully (None, not error).
    """
    # Arrange: Create form state with field
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="optional_field",
                visible=True,
                enabled=True,
                required=False,
                validation_errors=(),
                validation_warnings=(),
                validation_info=(),
            ),
        ),
        has_blocking_errors=False,
    )

    output_mappings = EntityOutputMappingsEvaluationDTO.empty(entity_id="project")

    # Field not in field_values dict
    field_values = {}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert len(context.fields) == 1
    assert context.fields[0].field_id == "optional_field"
    assert context.fields[0].value is None  # None when missing


# =============================================================================
# Test 12: Multiple validation severity levels combined
# =============================================================================


def test_multiple_validation_severities():
    """Test: Field with ERROR, WARNING, INFO all preserved.

    ADR-050: All validation severity levels propagated independently.
    """
    # Arrange: Create form state with multiple validation issues
    form_state = FormRuntimeStateDTO(
        entity_id="project",
        fields=(
            FormFieldRuntimeStateDTO(
                field_id="complex_field",
                visible=True,
                enabled=True,
                required=True,
                validation_errors=("Error 1", "Error 2"),
                validation_warnings=("Warning 1",),
                validation_info=("Info 1", "Info 2", "Info 3"),
            ),
        ),
        has_blocking_errors=True,  # Blocked by ERRORs
    )

    output_mappings = EntityOutputMappingsEvaluationDTO.empty(entity_id="project")
    field_values = {"complex_field": "invalid"}

    use_case = BuildDocumentRuntimeContextUseCase()

    # Act
    context = use_case.execute(
        entity_id="project",
        field_values=field_values,
        form_state=form_state,
        output_mappings=output_mappings,
    )

    # Assert
    assert len(context.fields) == 1
    field = context.fields[0]
    assert field.validation_errors == ("Error 1", "Error 2")
    assert field.validation_warnings == ("Warning 1",)
    assert field.validation_info == ("Info 1", "Info 2", "Info 3")
    assert context.has_blocking_errors is True

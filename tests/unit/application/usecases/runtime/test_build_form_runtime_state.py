"""Tests for BuildFormRuntimeStateUseCase (Phase R-4.5).

Tests form runtime state adapter (runtime results → UI-consumable state).
"""

import pytest

from doc_helper.application.dto.runtime_dto import (
    EntityControlRuleEvaluationDTO,
    EntityControlRulesEvaluationResultDTO,
    FormFieldRuntimeStateDTO,
    FormRuntimeStateDTO,
    RuntimeEvaluationResultDTO,
    ValidationEvaluationResultDTO,
    ValidationIssueDTO,
)
from doc_helper.application.usecases.runtime.build_form_runtime_state import (
    BuildFormRuntimeStateUseCase,
)


# =============================================================================
# Test 1: Visible field state
# =============================================================================


def test_visible_field():
    """Test field with visibility=True."""
    # Setup: Control rules with visible field
    control_rules_result = EntityControlRulesEvaluationResultDTO(
        entity_id="test_entity",
        field_results=(
            EntityControlRuleEvaluationDTO(
                field_id="field1",
                visibility=True,
                enabled=True,
                required=False,
            ),
        ),
        has_any_rule=False,
    )

    # Validation: No issues
    validation_result = ValidationEvaluationResultDTO(
        success=True,
        errors=(),
        warnings=(),
        info=(),
        blocking=False,
        evaluated_fields=("field1",),
        failed_fields=(),  # No failed fields
    )

    runtime_result = RuntimeEvaluationResultDTO.success(
        control_rules_result=control_rules_result,
        validation_result=validation_result,
        output_mappings_result=None,
        is_blocked=False,
        blocking_reason=None,
    )

    # Execute
    use_case = BuildFormRuntimeStateUseCase()
    form_state = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "value1"},
        runtime_result=runtime_result,
    )

    # Assert
    assert isinstance(form_state, FormRuntimeStateDTO)
    assert form_state.entity_id == "test_entity"
    assert len(form_state.fields) == 1
    assert form_state.fields[0].field_id == "field1"
    assert form_state.fields[0].visible is True
    assert form_state.fields[0].enabled is True
    assert form_state.fields[0].required is False
    assert form_state.fields[0].validation_errors == ()
    assert form_state.fields[0].validation_warnings == ()
    assert form_state.fields[0].validation_info == ()
    assert form_state.has_blocking_errors is False


# =============================================================================
# Test 2: Hidden field state
# =============================================================================


def test_hidden_field():
    """Test field with visibility=False."""
    # Setup: Control rules with hidden field
    control_rules_result = EntityControlRulesEvaluationResultDTO(
        entity_id="test_entity",
        field_results=(
            EntityControlRuleEvaluationDTO(
                field_id="field1",
                visibility=False,  # Hidden
                enabled=True,
                required=False,
            ),
        ),
        has_any_rule=True,
    )

    validation_result = ValidationEvaluationResultDTO(
        success=True,
        errors=(),
        warnings=(),
        info=(),
        blocking=False,
        evaluated_fields=("field1",),
        failed_fields=(),  # No failed fields
    )

    runtime_result = RuntimeEvaluationResultDTO.success(
        control_rules_result=control_rules_result,
        validation_result=validation_result,
        output_mappings_result=None,
        is_blocked=False,
        blocking_reason=None,
    )

    # Execute
    use_case = BuildFormRuntimeStateUseCase()
    form_state = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "value1"},
        runtime_result=runtime_result,
    )

    # Assert
    assert form_state.fields[0].visible is False
    assert form_state.fields[0].enabled is True
    assert form_state.fields[0].required is False


# =============================================================================
# Test 3: Disabled field state
# =============================================================================


def test_disabled_field():
    """Test field with enabled=False."""
    # Setup: Control rules with disabled field
    control_rules_result = EntityControlRulesEvaluationResultDTO(
        entity_id="test_entity",
        field_results=(
            EntityControlRuleEvaluationDTO(
                field_id="field1",
                visibility=True,
                enabled=False,  # Disabled
                required=False,
            ),
        ),
        has_any_rule=True,
    )

    validation_result = ValidationEvaluationResultDTO(
        success=True,
        errors=(),
        warnings=(),
        info=(),
        blocking=False,
        evaluated_fields=("field1",),
        failed_fields=(),
    )

    runtime_result = RuntimeEvaluationResultDTO.success(
        control_rules_result=control_rules_result,
        validation_result=validation_result,
        output_mappings_result=None,
        is_blocked=False,
        blocking_reason=None,
    )

    # Execute
    use_case = BuildFormRuntimeStateUseCase()
    form_state = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "value1"},
        runtime_result=runtime_result,
    )

    # Assert
    assert form_state.fields[0].visible is True
    assert form_state.fields[0].enabled is False
    assert form_state.fields[0].required is False


# =============================================================================
# Test 4: Required field state
# =============================================================================


def test_required_field():
    """Test field with required=True."""
    # Setup: Control rules with required field
    control_rules_result = EntityControlRulesEvaluationResultDTO(
        entity_id="test_entity",
        field_results=(
            EntityControlRuleEvaluationDTO(
                field_id="field1",
                visibility=True,
                enabled=True,
                required=True,  # Required
            ),
        ),
        has_any_rule=True,
    )

    validation_result = ValidationEvaluationResultDTO(
        success=True,
        errors=(),
        warnings=(),
        info=(),
        blocking=False,
        evaluated_fields=("field1",),
        failed_fields=(),
    )

    runtime_result = RuntimeEvaluationResultDTO.success(
        control_rules_result=control_rules_result,
        validation_result=validation_result,
        output_mappings_result=None,
        is_blocked=False,
        blocking_reason=None,
    )

    # Execute
    use_case = BuildFormRuntimeStateUseCase()
    form_state = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "value1"},
        runtime_result=runtime_result,
    )

    # Assert
    assert form_state.fields[0].visible is True
    assert form_state.fields[0].enabled is True
    assert form_state.fields[0].required is True


# =============================================================================
# Test 5: Validation error blocks form
# =============================================================================


def test_validation_error_blocks_form():
    """Test validation ERROR blocks form submission."""
    # Setup: Control rules (default state)
    control_rules_result = EntityControlRulesEvaluationResultDTO(
        entity_id="test_entity",
        field_results=(
            EntityControlRuleEvaluationDTO(
                field_id="field1",
                visibility=True,
                enabled=True,
                required=True,
            ),
        ),
        has_any_rule=True,
    )

    # Validation: ERROR severity issue
    error_issue = ValidationIssueDTO(
        field_id="field1",
        field_label="Field 1",
        constraint_type="RequiredConstraint",
        severity="ERROR",
        message="Field 1 is required",
        code="REQUIRED_FIELD_EMPTY",
        details=None,
    )

    validation_result = ValidationEvaluationResultDTO(
        success=True,
        errors=(error_issue,),
        warnings=(),
        info=(),
        blocking=True,  # Blocked by ERROR
        evaluated_fields=("field1",),
        failed_fields=("field1",),  # field1 has ERROR
    )

    runtime_result = RuntimeEvaluationResultDTO.success(
        control_rules_result=control_rules_result,
        validation_result=validation_result,
        output_mappings_result=None,
        is_blocked=True,
        blocking_reason="Validation failed with 1 ERROR severity issue(s)",
    )

    # Execute
    use_case = BuildFormRuntimeStateUseCase()
    form_state = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": ""},
        runtime_result=runtime_result,
    )

    # Assert
    assert form_state.has_blocking_errors is True
    assert len(form_state.fields[0].validation_errors) == 1
    assert form_state.fields[0].validation_errors[0] == "Field 1 is required"
    assert form_state.fields[0].validation_warnings == ()
    assert form_state.fields[0].validation_info == ()


# =============================================================================
# Test 6: Validation warning does not block
# =============================================================================


def test_validation_warning_does_not_block():
    """Test validation WARNING does not block form submission."""
    # Setup: Control rules (default state)
    control_rules_result = EntityControlRulesEvaluationResultDTO(
        entity_id="test_entity",
        field_results=(
            EntityControlRuleEvaluationDTO(
                field_id="field1",
                visibility=True,
                enabled=True,
                required=False,
            ),
        ),
        has_any_rule=False,
    )

    # Validation: WARNING severity issue
    warning_issue = ValidationIssueDTO(
        field_id="field1",
        field_label="Field 1",
        constraint_type="RecommendedLengthConstraint",
        severity="WARNING",
        message="Field 1 should be at least 5 characters",
        code="RECOMMENDED_LENGTH_WARNING",
        details={"recommended_length": 5, "actual_length": 3},
    )

    validation_result = ValidationEvaluationResultDTO(
        success=True,
        errors=(),
        warnings=(warning_issue,),
        info=(),
        blocking=False,  # Not blocked by WARNING
        evaluated_fields=("field1",),
        failed_fields=(),  # Warnings don't fail fields
    )

    runtime_result = RuntimeEvaluationResultDTO.success(
        control_rules_result=control_rules_result,
        validation_result=validation_result,
        output_mappings_result=None,
        is_blocked=False,
        blocking_reason=None,
    )

    # Execute
    use_case = BuildFormRuntimeStateUseCase()
    form_state = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "abc"},
        runtime_result=runtime_result,
    )

    # Assert
    assert form_state.has_blocking_errors is False
    assert form_state.fields[0].validation_errors == ()
    assert len(form_state.fields[0].validation_warnings) == 1
    assert (
        form_state.fields[0].validation_warnings[0]
        == "Field 1 should be at least 5 characters"
    )
    assert form_state.fields[0].validation_info == ()


# =============================================================================
# Test 7: Determinism (same input → same output)
# =============================================================================


def test_deterministic_evaluation():
    """Test determinism: same inputs → identical outputs."""
    # Setup: Control rules + validation
    control_rules_result = EntityControlRulesEvaluationResultDTO(
        entity_id="test_entity",
        field_results=(
            EntityControlRuleEvaluationDTO(
                field_id="field1",
                visibility=True,
                enabled=True,
                required=True,
            ),
        ),
        has_any_rule=True,
    )

    validation_result = ValidationEvaluationResultDTO(
        success=True,
        errors=(),
        warnings=(),
        info=(),
        blocking=False,
        evaluated_fields=("field1",),
        failed_fields=(),
    )

    runtime_result = RuntimeEvaluationResultDTO.success(
        control_rules_result=control_rules_result,
        validation_result=validation_result,
        output_mappings_result=None,
        is_blocked=False,
        blocking_reason=None,
    )

    # Execute twice with same inputs
    use_case = BuildFormRuntimeStateUseCase()
    form_state1 = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "value1"},
        runtime_result=runtime_result,
    )
    form_state2 = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "value1"},
        runtime_result=runtime_result,
    )

    # Assert: Results identical
    assert form_state1.entity_id == form_state2.entity_id
    assert len(form_state1.fields) == len(form_state2.fields)
    assert form_state1.has_blocking_errors == form_state2.has_blocking_errors

    for field1, field2 in zip(form_state1.fields, form_state2.fields):
        assert field1.field_id == field2.field_id
        assert field1.visible == field2.visible
        assert field1.enabled == field2.enabled
        assert field1.required == field2.required
        assert field1.validation_errors == field2.validation_errors
        assert field1.validation_warnings == field2.validation_warnings
        assert field1.validation_info == field2.validation_info


# =============================================================================
# Test 8: Empty form behavior
# =============================================================================


def test_empty_form():
    """Test form with no fields."""
    # Setup: No fields
    control_rules_result = EntityControlRulesEvaluationResultDTO(
        entity_id="empty_entity",
        field_results=(),  # No fields
        has_any_rule=False,
    )

    validation_result = ValidationEvaluationResultDTO(
        success=True,
        errors=(),
        warnings=(),
        info=(),
        blocking=False,
        evaluated_fields=(),
        failed_fields=(),
    )

    runtime_result = RuntimeEvaluationResultDTO.success(
        control_rules_result=control_rules_result,
        validation_result=validation_result,
        output_mappings_result=None,
        is_blocked=False,
        blocking_reason=None,
    )

    # Execute
    use_case = BuildFormRuntimeStateUseCase()
    form_state = use_case.execute(
        entity_id="empty_entity",
        field_values={},
        runtime_result=runtime_result,
    )

    # Assert
    assert form_state.entity_id == "empty_entity"
    assert len(form_state.fields) == 0
    assert form_state.has_blocking_errors is False


# =============================================================================
# Test 9: Mixed control + validation behavior
# =============================================================================


def test_mixed_control_and_validation():
    """Test multiple fields with mixed control states and validation."""
    # Setup: 3 fields with different states
    control_rules_result = EntityControlRulesEvaluationResultDTO(
        entity_id="test_entity",
        field_results=(
            EntityControlRuleEvaluationDTO(
                field_id="field1",
                visibility=True,
                enabled=True,
                required=True,
            ),
            EntityControlRuleEvaluationDTO(
                field_id="field2",
                visibility=False,  # Hidden
                enabled=True,
                required=False,
            ),
            EntityControlRuleEvaluationDTO(
                field_id="field3",
                visibility=True,
                enabled=False,  # Disabled
                required=False,
            ),
        ),
        has_any_rule=True,
    )

    # Validation: field1 has ERROR, field3 has WARNING
    error_issue = ValidationIssueDTO(
        field_id="field1",
        field_label="Field 1",
        constraint_type="RequiredConstraint",
        severity="ERROR",
        message="Field 1 is required",
        code="REQUIRED_FIELD_EMPTY",
        details=None,
    )

    warning_issue = ValidationIssueDTO(
        field_id="field3",
        field_label="Field 3",
        constraint_type="RecommendedConstraint",
        severity="WARNING",
        message="Field 3 should not be empty",
        code="RECOMMENDED_VALUE_WARNING",
        details=None,
    )

    info_issue = ValidationIssueDTO(
        field_id="field3",
        field_label="Field 3",
        constraint_type="InfoConstraint",
        severity="INFO",
        message="Field 3 accepts numeric values",
        code="FIELD_INFO",
        details=None,
    )

    validation_result = ValidationEvaluationResultDTO(
        success=True,
        errors=(error_issue,),
        warnings=(warning_issue,),
        info=(info_issue,),
        blocking=True,
        evaluated_fields=("field1", "field2", "field3"),
        failed_fields=("field1",),  # Only field1 has ERROR
    )

    runtime_result = RuntimeEvaluationResultDTO.success(
        control_rules_result=control_rules_result,
        validation_result=validation_result,
        output_mappings_result=None,
        is_blocked=True,
        blocking_reason="Validation failed with 1 ERROR severity issue(s)",
    )

    # Execute
    use_case = BuildFormRuntimeStateUseCase()
    form_state = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "", "field2": "value2", "field3": ""},
        runtime_result=runtime_result,
    )

    # Assert: Form state
    assert form_state.entity_id == "test_entity"
    assert len(form_state.fields) == 3
    assert form_state.has_blocking_errors is True

    # Assert: field1 (visible, enabled, required, has ERROR)
    field1 = form_state.fields[0]
    assert field1.field_id == "field1"
    assert field1.visible is True
    assert field1.enabled is True
    assert field1.required is True
    assert len(field1.validation_errors) == 1
    assert field1.validation_errors[0] == "Field 1 is required"
    assert field1.validation_warnings == ()
    assert field1.validation_info == ()

    # Assert: field2 (hidden, no validation issues)
    field2 = form_state.fields[1]
    assert field2.field_id == "field2"
    assert field2.visible is False
    assert field2.enabled is True
    assert field2.required is False
    assert field2.validation_errors == ()
    assert field2.validation_warnings == ()
    assert field2.validation_info == ()

    # Assert: field3 (visible, disabled, has WARNING + INFO)
    field3 = form_state.fields[2]
    assert field3.field_id == "field3"
    assert field3.visible is True
    assert field3.enabled is False
    assert field3.required is False
    assert field3.validation_errors == ()
    assert len(field3.validation_warnings) == 1
    assert field3.validation_warnings[0] == "Field 3 should not be empty"
    assert len(field3.validation_info) == 1
    assert field3.validation_info[0] == "Field 3 accepts numeric values"


# =============================================================================
# Test 10: Multiple validation issues per field
# =============================================================================


def test_multiple_validation_issues_per_field():
    """Test field with multiple validation issues of same severity."""
    # Setup: Control rules
    control_rules_result = EntityControlRulesEvaluationResultDTO(
        entity_id="test_entity",
        field_results=(
            EntityControlRuleEvaluationDTO(
                field_id="field1",
                visibility=True,
                enabled=True,
                required=True,
            ),
        ),
        has_any_rule=True,
    )

    # Validation: Multiple ERRORs for same field
    error1 = ValidationIssueDTO(
        field_id="field1",
        field_label="Field 1",
        constraint_type="RequiredConstraint",
        severity="ERROR",
        message="Field 1 is required",
        code="REQUIRED_FIELD_EMPTY",
        details=None,
    )

    error2 = ValidationIssueDTO(
        field_id="field1",
        field_label="Field 1",
        constraint_type="MinLengthConstraint",
        severity="ERROR",
        message="Field 1 must be at least 5 characters",
        code="MIN_LENGTH_NOT_MET",
        details={"min_length": 5, "actual_length": 0},
    )

    validation_result = ValidationEvaluationResultDTO(
        success=True,
        errors=(error1, error2),
        warnings=(),
        info=(),
        blocking=True,
        evaluated_fields=("field1",),
        failed_fields=("field1",),  # field1 has multiple ERRORs
    )

    runtime_result = RuntimeEvaluationResultDTO.success(
        control_rules_result=control_rules_result,
        validation_result=validation_result,
        output_mappings_result=None,
        is_blocked=True,
        blocking_reason="Validation failed with 2 ERROR severity issue(s)",
    )

    # Execute
    use_case = BuildFormRuntimeStateUseCase()
    form_state = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": ""},
        runtime_result=runtime_result,
    )

    # Assert: Both errors present
    assert form_state.has_blocking_errors is True
    assert len(form_state.fields[0].validation_errors) == 2
    assert "Field 1 is required" in form_state.fields[0].validation_errors
    assert (
        "Field 1 must be at least 5 characters"
        in form_state.fields[0].validation_errors
    )

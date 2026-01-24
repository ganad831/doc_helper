"""Unit tests for EvaluateControlRulesUseCase (Phase R-1).

Tests runtime control rule evaluation following ADR-050 requirements:
- Pull-based evaluation
- Deterministic behavior
- Non-blocking failures
- Default state fallback
- Boolean formula evaluation
"""

import pytest

from doc_helper.application.dto.export_dto import ControlRuleExportDTO
from doc_helper.application.dto.runtime_dto import (
    ControlRuleEvaluationRequestDTO,
    ControlRuleEvaluationResultDTO,
)
from doc_helper.application.usecases.formula_usecases import FormulaUseCases
from doc_helper.application.usecases.runtime.evaluate_control_rules import (
    EvaluateControlRulesUseCase,
)


class MockSchemaUseCases:
    """Mock SchemaUseCases for testing."""

    def __init__(self, control_rules: tuple[ControlRuleExportDTO, ...] | None = None):
        self.control_rules = control_rules or ()
        self.should_fail = False

    def list_control_rules_for_field(self, entity_id: str, field_id: str):
        """Mock list_control_rules_for_field.

        Returns tuple directly (not wrapped in OperationResultDTO).
        Raises exception on failure instead of returning error result.
        """
        if self.should_fail:
            raise RuntimeError("Schema fetch failed")
        return self.control_rules


# ============================================================================
# ADR-050 Compliance Tests: Default State & No Rules
# ============================================================================


def test_no_control_rules_returns_default_state():
    """Test: No control rules → default state (visible=True, enabled=True, required=False).

    ADR-050: When no control rules exist, use default field state.
    """
    # Arrange
    mock_schema = MockSchemaUseCases(control_rules=())
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert isinstance(result, ControlRuleEvaluationResultDTO)
    assert result.success is True
    assert result.visible is True
    assert result.enabled is True
    assert result.required is False
    assert result.error_message is None


def test_schema_fetch_failure_returns_failure_with_default_state():
    """Test: Schema fetch failure → failure result with default state.

    ADR-050: Control rule failures do NOT block form interaction.
    """
    # Arrange
    mock_schema = MockSchemaUseCases()
    mock_schema.should_fail = True
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert isinstance(result, ControlRuleEvaluationResultDTO)
    assert result.success is False
    assert result.visible is True  # Default state
    assert result.enabled is True  # Default state
    assert result.required is False  # Default state
    assert result.error_message is not None
    assert "Failed to fetch control rules" in result.error_message


# ============================================================================
# ADR-050 Compliance Tests: VISIBILITY Rules
# ============================================================================


def test_visibility_rule_true_makes_field_visible():
    """Test: VISIBILITY rule evaluating to True → visible=True.

    ADR-050: VISIBILITY rule with result=True → target field visible.
    """
    # Arrange
    control_rules = (
        ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="secret_field",
            formula_text="user_role == 'admin'",
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="secret_field",
        field_values={"user_role": "admin"},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.visible is True
    assert result.enabled is True  # Not affected
    assert result.required is False  # Not affected
    assert result.error_message is None


def test_visibility_rule_false_makes_field_hidden():
    """Test: VISIBILITY rule evaluating to False → visible=False.

    ADR-050: VISIBILITY rule with result=False → target field hidden.
    """
    # Arrange
    control_rules = (
        ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="secret_field",
            formula_text="user_role == 'admin'",
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="secret_field",
        field_values={"user_role": "user"},  # Not admin
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.visible is False  # Hidden
    assert result.enabled is True  # Not affected
    assert result.required is False  # Not affected
    assert result.error_message is None


# ============================================================================
# ADR-050 Compliance Tests: ENABLED Rules
# ============================================================================


def test_enabled_rule_true_makes_field_enabled():
    """Test: ENABLED rule evaluating to True → enabled=True.

    ADR-050: ENABLED rule with result=True → target field enabled.
    """
    # Arrange
    control_rules = (
        ControlRuleExportDTO(
            rule_type="ENABLED",
            target_field_id="edit_field",
            formula_text="status == 'draft'",
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="edit_field",
        field_values={"status": "draft"},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.visible is True  # Not affected
    assert result.enabled is True
    assert result.required is False  # Not affected
    assert result.error_message is None


def test_enabled_rule_false_makes_field_disabled():
    """Test: ENABLED rule evaluating to False → enabled=False.

    ADR-050: ENABLED rule with result=False → target field disabled (read-only).
    """
    # Arrange
    control_rules = (
        ControlRuleExportDTO(
            rule_type="ENABLED",
            target_field_id="edit_field",
            formula_text="status == 'draft'",
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="edit_field",
        field_values={"status": "published"},  # Not draft
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.visible is True  # Not affected
    assert result.enabled is False  # Disabled
    assert result.required is False  # Not affected
    assert result.error_message is None


# ============================================================================
# ADR-050 Compliance Tests: REQUIRED Rules
# ============================================================================


def test_required_rule_true_makes_field_required():
    """Test: REQUIRED rule evaluating to True → required=True.

    ADR-050: REQUIRED rule with result=True → target field required.
    """
    # Arrange
    control_rules = (
        ControlRuleExportDTO(
            rule_type="REQUIRED",
            target_field_id="tax_id",
            formula_text="owner_type == 'company'",
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="tax_id",
        field_values={"owner_type": "company"},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.visible is True  # Not affected
    assert result.enabled is True  # Not affected
    assert result.required is True
    assert result.error_message is None


def test_required_rule_false_makes_field_optional():
    """Test: REQUIRED rule evaluating to False → required=False.

    ADR-050: REQUIRED rule with result=False → target field optional.
    """
    # Arrange
    control_rules = (
        ControlRuleExportDTO(
            rule_type="REQUIRED",
            target_field_id="tax_id",
            formula_text="owner_type == 'company'",
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="tax_id",
        field_values={"owner_type": "individual"},  # Not company
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.visible is True  # Not affected
    assert result.enabled is True  # Not affected
    assert result.required is False  # Optional
    assert result.error_message is None


# ============================================================================
# ADR-050 Compliance Tests: Formula Failure Handling
# ============================================================================


def test_formula_failure_uses_default_state():
    """Test: Formula evaluation failure → use default state (non-blocking).

    ADR-050: Control rule failures do NOT block form interaction.
    Formula failure → target field uses default state.
    """
    # Arrange - Formula with syntax error
    control_rules = (
        ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="invalid syntax {{",
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={},
    )

    # Act
    result = use_case.execute(request)

    # Assert - Rule failed, but default state is used (non-blocking)
    assert result.success is True
    assert result.visible is True  # Default
    assert result.enabled is True  # Default
    assert result.required is False  # Default
    assert result.error_message is None


def test_formula_with_missing_field_uses_default_state():
    """Test: Formula referencing missing field → use default state.

    ADR-050: Formula evaluation failure → target field uses default state.
    """
    # Arrange - Formula references non-existent field
    control_rules = (
        ControlRuleExportDTO(
            rule_type="ENABLED",
            target_field_id="test_field",
            formula_text="nonexistent_field == 'value'",
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={"other_field": "value"},  # Missing nonexistent_field
    )

    # Act
    result = use_case.execute(request)

    # Assert - Rule failed, but default state is used (non-blocking)
    assert result.success is True
    assert result.visible is True  # Default
    assert result.enabled is True  # Default
    assert result.required is False  # Default
    assert result.error_message is None


# ============================================================================
# ADR-050 Compliance Tests: Multiple Rules (Aggregation)
# ============================================================================


def test_multiple_rules_all_evaluated():
    """Test: Multiple rules → all evaluated and aggregated.

    ADR-050: All applicable control rules are evaluated.
    """
    # Arrange - Multiple rules affecting different properties
    control_rules = (
        ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="show_field == true",
        ),
        ControlRuleExportDTO(
            rule_type="ENABLED",
            target_field_id="test_field",
            formula_text="allow_edit == true",
        ),
        ControlRuleExportDTO(
            rule_type="REQUIRED",
            target_field_id="test_field",
            formula_text="is_required == true",
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={
            "show_field": True,
            "allow_edit": False,
            "is_required": True,
        },
    )

    # Act
    result = use_case.execute(request)

    # Assert - All rules evaluated
    assert result.success is True
    assert result.visible is True  # show_field == true
    assert result.enabled is False  # allow_edit == false
    assert result.required is True  # is_required == true
    assert result.error_message is None


# ============================================================================
# ADR-050 Compliance Tests: Determinism
# ============================================================================


def test_determinism_same_inputs_same_outputs():
    """Test: Determinism - same inputs → same outputs.

    ADR-050: Runtime evaluation MUST be deterministic.
    """
    # Arrange
    control_rules = (
        ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="value > 10",
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={"value": 15},
    )

    # Act - Evaluate multiple times with same inputs
    result1 = use_case.execute(request)
    result2 = use_case.execute(request)
    result3 = use_case.execute(request)

    # Assert - All results identical
    assert result1.success == result2.success == result3.success is True
    assert result1.visible == result2.visible == result3.visible is True
    assert result1.enabled == result2.enabled == result3.enabled is True
    assert result1.required == result2.required == result3.required is False


# ============================================================================
# ADR-050 Compliance Tests: Truthy/Falsy Coercion
# ============================================================================


def test_truthy_value_coerced_to_true():
    """Test: Non-boolean truthy value → coerced to True.

    ADR-050: Control rules handle edge cases gracefully with truthy/falsy evaluation.
    """
    # Arrange - Formula returns number (truthy)
    control_rules = (
        ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="count",  # Returns number
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={"count": 5},  # Truthy
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.visible is True  # Truthy → True
    assert result.error_message is None


def test_falsy_value_coerced_to_false():
    """Test: Non-boolean falsy value → coerced to False.

    ADR-050: Control rules handle edge cases gracefully with truthy/falsy evaluation.
    """
    # Arrange - Formula returns 0 (falsy)
    control_rules = (
        ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="count",  # Returns number
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={"count": 0},  # Falsy
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.visible is False  # Falsy → False
    assert result.error_message is None


def test_none_value_coerced_to_false():
    """Test: None value → coerced to False.

    ADR-050: Control rules handle edge cases gracefully with truthy/falsy evaluation.
    """
    # Arrange - Formula returns None (field exists with None value)
    control_rules = (
        ControlRuleExportDTO(
            rule_type="ENABLED",
            target_field_id="test_field",
            formula_text="nullable_field",  # Field exists but has None value
        ),
    )
    mock_schema = MockSchemaUseCases(control_rules=control_rules)
    use_case = EvaluateControlRulesUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )
    request = ControlRuleEvaluationRequestDTO(
        entity_id="project",
        field_id="test_field",
        field_values={"nullable_field": None},  # Field exists with None value
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.success is True
    assert result.enabled is False  # None → False
    assert result.error_message is None

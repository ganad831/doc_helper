"""Unit tests for ControlRuleEditorViewModel (Phase F-8: Control Rules).

Tests control rule editor ViewModel behavior:
- Control rule editor shows error on invalid input
- Control rule editor blocks non-boolean formulas
- Control rule editor allows boolean formulas
- Control rule editor does NOT modify schema
- Control rule editor exposes diagnostics for display
- Control rule editor exposes governance state
- Control rule editor provides clear_rule method

PHASE F-8 CONSTRAINTS:
- Control Rules use BOOLEAN formulas only
- Non-boolean result type -> Rule BLOCKED
- Read-only with respect to schema
- NO persistence
- NO execution against real data
- NO runtime observers
- NO DAG building
- NO schema mutation

TEST REQUIREMENTS (from spec):
- Boolean acceptance: boolean formula -> ALLOWED
- Non-boolean blocking: non-boolean formula -> BLOCKED
- Governance: INVALID -> blocked, VALID/VALID_WITH_WARNINGS -> allowed
- Determinism: same input -> same output
"""

import pytest

from doc_helper.application.dto.control_rule_dto import (
    ControlRuleStatus,
    ControlRuleType,
)
from doc_helper.application.dto.formula_dto import (
    FormulaGovernanceStatus,
    SchemaFieldInfoDTO,
)
from doc_helper.application.usecases.control_rule_usecases import ControlRuleUseCases
from doc_helper.application.usecases.formula_usecases import FormulaUseCases
from doc_helper.presentation.viewmodels.control_rule_editor_viewmodel import (
    ControlRuleEditorViewModel,
)


class TestControlRuleEditorViewModel:
    """Tests for ControlRuleEditorViewModel."""

    @pytest.fixture
    def formula_usecases(self) -> FormulaUseCases:
        """Create FormulaUseCases instance."""
        return FormulaUseCases()

    @pytest.fixture
    def control_rule_usecases(
        self, formula_usecases: FormulaUseCases
    ) -> ControlRuleUseCases:
        """Create ControlRuleUseCases instance."""
        return ControlRuleUseCases(formula_usecases=formula_usecases)

    @pytest.fixture
    def viewmodel(
        self, control_rule_usecases: ControlRuleUseCases
    ) -> ControlRuleEditorViewModel:
        """Create ControlRuleEditorViewModel instance."""
        return ControlRuleEditorViewModel(control_rule_usecases)

    @pytest.fixture
    def schema_fields(self) -> tuple[SchemaFieldInfoDTO, ...]:
        """Create sample schema fields."""
        return (
            SchemaFieldInfoDTO(
                field_id="is_admin",
                field_type="CHECKBOX",
                entity_id="test_entity",
                label="Is Admin",
            ),
            SchemaFieldInfoDTO(
                field_id="user_role",
                field_type="TEXT",
                entity_id="test_entity",
                label="User Role",
            ),
            SchemaFieldInfoDTO(
                field_id="age",
                field_type="NUMBER",
                entity_id="test_entity",
                label="Age",
            ),
            SchemaFieldInfoDTO(
                field_id="has_permission",
                field_type="CHECKBOX",
                entity_id="test_entity",
                label="Has Permission",
            ),
        )

    # =========================================================================
    # Test: Boolean formulas are ALLOWED
    # =========================================================================

    def test_boolean_formula_allowed(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Boolean formula should be allowed."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_rule_type(ControlRuleType.VISIBILITY)
        viewmodel.set_target_field_id("target_field")
        viewmodel.set_formula("is_admin == true")

        assert viewmodel.is_rule_allowed is True
        assert viewmodel.is_rule_blocked is False
        assert viewmodel.rule_status == ControlRuleStatus.ALLOWED
        assert viewmodel.is_boolean_formula is True

    def test_comparison_formula_allowed(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Comparison expression should be allowed."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("age > 18")

        assert viewmodel.is_rule_allowed is True
        assert viewmodel.inferred_type == "BOOLEAN"

    def test_logical_and_formula_allowed(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Logical AND expression should be allowed."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_admin and has_permission")

        assert viewmodel.is_rule_allowed is True

    def test_logical_or_formula_allowed(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Logical OR expression should be allowed."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_admin or has_permission")

        assert viewmodel.is_rule_allowed is True

    def test_logical_not_formula_allowed(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Logical NOT expression should be allowed."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("not is_admin")

        assert viewmodel.is_rule_allowed is True

    def test_is_empty_function_allowed(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """is_empty() function should be allowed (returns boolean)."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_empty(user_role)")

        assert viewmodel.is_rule_allowed is True
        assert viewmodel.is_boolean_formula is True

    # =========================================================================
    # Test: Non-boolean formulas are BLOCKED
    # =========================================================================

    def test_number_formula_blocked(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Number formula should be blocked."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("age + 10")

        assert viewmodel.is_rule_blocked is True
        assert viewmodel.is_rule_allowed is False
        assert viewmodel.rule_status == ControlRuleStatus.BLOCKED
        assert viewmodel.is_boolean_formula is False
        assert viewmodel.blocking_reason is not None
        assert "BOOLEAN" in viewmodel.blocking_reason

    def test_text_formula_blocked(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Text formula should be blocked."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("upper(user_role)")

        assert viewmodel.is_rule_blocked is True
        assert viewmodel.inferred_type == "TEXT"
        assert "TEXT" in viewmodel.blocking_reason

    def test_arithmetic_formula_blocked(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Arithmetic formula should be blocked."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("age * 2")

        assert viewmodel.is_rule_blocked is True

    # =========================================================================
    # Test: Invalid formulas are BLOCKED (governance INVALID)
    # =========================================================================

    def test_syntax_error_blocked(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Syntax error should block the rule."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_admin ==")  # Missing right operand

        assert viewmodel.is_rule_blocked is True
        assert viewmodel.blocking_reason is not None
        assert "error" in viewmodel.blocking_reason.lower()

    def test_unknown_field_blocked(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Unknown field should block the rule."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field == true")

        assert viewmodel.is_rule_blocked is True
        assert "Unknown field" in viewmodel.blocking_reason

    def test_unknown_function_blocked(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Unknown function should block the rule."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_function(is_admin)")

        assert viewmodel.is_rule_blocked is True
        assert "Unknown function" in viewmodel.blocking_reason

    # =========================================================================
    # Test: Empty formula is CLEARED
    # =========================================================================

    def test_empty_formula_cleared(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Empty formula should result in CLEARED status."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("")

        assert viewmodel.is_rule_cleared is True
        assert viewmodel.is_rule_allowed is False
        assert viewmodel.is_rule_blocked is False
        assert viewmodel.rule_status == ControlRuleStatus.CLEARED

    def test_whitespace_formula_cleared(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Whitespace-only formula should result in CLEARED status."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("   ")

        assert viewmodel.is_rule_cleared is True

    # =========================================================================
    # Test: clear_rule method
    # =========================================================================

    def test_clear_rule_clears_formula(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """clear_rule should clear the formula and return CLEARED result."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_admin == true")
        assert viewmodel.is_rule_allowed is True

        result = viewmodel.clear_rule()

        assert result.is_cleared is True
        assert viewmodel.formula_text == ""
        assert viewmodel.has_formula is False
        assert viewmodel.is_rule_cleared is True

    # =========================================================================
    # Test: Rule type and target field
    # =========================================================================

    def test_set_rule_type(
        self,
        viewmodel: ControlRuleEditorViewModel,
    ) -> None:
        """set_rule_type should update rule type."""
        viewmodel.set_rule_type(ControlRuleType.ENABLED)
        assert viewmodel.rule_type == ControlRuleType.ENABLED

        viewmodel.set_rule_type(ControlRuleType.REQUIRED)
        assert viewmodel.rule_type == ControlRuleType.REQUIRED

        viewmodel.set_rule_type(ControlRuleType.VISIBILITY)
        assert viewmodel.rule_type == ControlRuleType.VISIBILITY

    def test_set_target_field_id(
        self,
        viewmodel: ControlRuleEditorViewModel,
    ) -> None:
        """set_target_field_id should update target field."""
        viewmodel.set_target_field_id("my_field")
        assert viewmodel.target_field_id == "my_field"

    def test_rule_type_in_result(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Rule type should be included in result."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_rule_type(ControlRuleType.ENABLED)
        viewmodel.set_target_field_id("target_field")
        viewmodel.set_formula("is_admin == true")

        result = viewmodel.get_rule_result()
        assert result.rule.rule_type == ControlRuleType.ENABLED

    def test_target_field_in_result(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Target field ID should be included in result."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_target_field_id("my_target")
        viewmodel.set_formula("is_admin == true")

        result = viewmodel.get_rule_result()
        assert result.rule.target_field_id == "my_target"

    # =========================================================================
    # Test: Diagnostics
    # =========================================================================

    def test_diagnostics_populated(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Diagnostics should be populated for valid rule."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_admin == true")

        diagnostics = viewmodel.diagnostics
        assert diagnostics is not None
        assert diagnostics.has_validation is True
        assert diagnostics.has_dependencies is True
        assert diagnostics.has_governance is True

    def test_diagnostics_error_count(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Error count should reflect diagnostics."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field == true")

        assert viewmodel.error_count > 0

    def test_diagnostics_warning_count(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Warning count should reflect diagnostics."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_admin == true")

        # Valid formula should have 0 errors
        assert viewmodel.error_count == 0

    # =========================================================================
    # Test: Governance status
    # =========================================================================

    def test_governance_status_valid(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Valid boolean formula should have VALID governance status."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_admin == true")

        assert viewmodel.governance_status in (
            FormulaGovernanceStatus.VALID,
            FormulaGovernanceStatus.VALID_WITH_WARNINGS,
        )

    def test_governance_status_invalid_formula(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Invalid formula should have INVALID governance status."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("unknown_field == true")

        assert viewmodel.governance_status == FormulaGovernanceStatus.INVALID

    # =========================================================================
    # Test: Status message
    # =========================================================================

    def test_status_message_allowed(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """ALLOWED status should have appropriate message."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_admin == true")

        assert "valid" in viewmodel.status_message.lower()

    def test_status_message_blocked(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """BLOCKED status should have appropriate message."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("age + 10")

        assert "blocked" in viewmodel.status_message.lower()

    def test_status_message_cleared(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """CLEARED status should have appropriate message."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("")

        assert "cleared" in viewmodel.status_message.lower()

    # =========================================================================
    # Test: has_formula property
    # =========================================================================

    def test_has_formula_true(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """has_formula should be True when formula exists."""
        viewmodel.set_formula("is_admin == true")
        assert viewmodel.has_formula is True

    def test_has_formula_false_empty(
        self,
        viewmodel: ControlRuleEditorViewModel,
    ) -> None:
        """has_formula should be False for empty formula."""
        viewmodel.set_formula("")
        assert viewmodel.has_formula is False

    def test_has_formula_false_whitespace(
        self,
        viewmodel: ControlRuleEditorViewModel,
    ) -> None:
        """has_formula should be False for whitespace-only formula."""
        viewmodel.set_formula("   ")
        assert viewmodel.has_formula is False

    # =========================================================================
    # Test: Validate method
    # =========================================================================

    def test_validate_method(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """validate() should trigger validation and return result."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_rule_type(ControlRuleType.VISIBILITY)
        viewmodel.set_target_field_id("target_field")
        viewmodel._formula_text = "is_admin == true"  # Set without auto-validate

        result = viewmodel.validate()

        assert result.is_allowed is True

    # =========================================================================
    # Test: get_rule_result method
    # =========================================================================

    def test_get_rule_result_allowed(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """get_rule_result should return rule for allowed formula."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_rule_type(ControlRuleType.ENABLED)
        viewmodel.set_target_field_id("target_field")
        viewmodel.set_formula("is_admin == true")

        result = viewmodel.get_rule_result()

        assert result.is_allowed is True
        assert result.rule is not None
        assert result.rule.formula_text == "is_admin == true"

    def test_get_rule_result_blocked(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """get_rule_result should return block reason for blocked formula."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("age + 10")

        result = viewmodel.get_rule_result()

        assert result.is_blocked is True
        assert result.block_reason is not None

    def test_get_rule_result_cleared(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """get_rule_result should return CLEARED for empty formula."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("")

        result = viewmodel.get_rule_result()

        assert result.is_cleared is True

    # =========================================================================
    # Test: Property change notification
    # =========================================================================

    def test_formula_change_notifies_observers(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Formula change should notify observers."""
        notifications = []

        def handler():
            notifications.append("formula_text")

        viewmodel.subscribe("formula_text", handler)
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_admin == true")

        assert "formula_text" in notifications

    def test_rule_type_change_notifies_observers(
        self,
        viewmodel: ControlRuleEditorViewModel,
    ) -> None:
        """Rule type change should notify observers."""
        notifications = []

        def handler():
            notifications.append("rule_type")

        viewmodel.subscribe("rule_type", handler)
        viewmodel.set_rule_type(ControlRuleType.REQUIRED)

        assert "rule_type" in notifications

    # =========================================================================
    # Test: Dispose cleanup
    # =========================================================================

    def test_dispose_clears_state(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """dispose() should clear internal state."""
        viewmodel.set_schema_context(schema_fields)
        viewmodel.set_formula("is_admin == true")
        viewmodel.set_target_field_id("target_field")

        viewmodel.dispose()

        assert viewmodel.formula_text == ""
        assert viewmodel.target_field_id == ""
        assert viewmodel._schema_fields == ()
        assert viewmodel._rule_result is None

    # =========================================================================
    # Test: Re-validation on context change
    # =========================================================================

    def test_revalidates_on_schema_change(
        self,
        viewmodel: ControlRuleEditorViewModel,
        schema_fields: tuple[SchemaFieldInfoDTO, ...],
    ) -> None:
        """Formula should revalidate when schema context changes."""
        # Set formula referencing unknown field
        viewmodel.set_formula("new_field == true")
        assert viewmodel.is_rule_blocked is True

        # Now add the field to schema
        new_schema = schema_fields + (
            SchemaFieldInfoDTO(
                field_id="new_field",
                field_type="CHECKBOX",
                entity_id="test_entity",
                label="New Field",
            ),
        )
        viewmodel.set_schema_context(new_schema)

        # Should now be valid
        assert viewmodel.is_rule_allowed is True

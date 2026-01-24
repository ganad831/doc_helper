"""Unit tests for ControlRuleUseCases (Phase F-8 + F-9: Control Rules).

Tests control rule validation use-case methods:
- validate_control_rule: Validates formula and checks boolean requirement
- can_apply_control_rule: Checks if rule can be applied
- clear_control_rule: Clears/removes a control rule
- preview_control_rule: Preview control rule with temporary field values (F-9)

PHASE F-8 CONSTRAINTS:
- Control Rules use BOOLEAN formulas only
- Non-boolean result type -> Rule BLOCKED
- Read-only with respect to schema
- NO persistence
- NO execution against real data
- NO runtime observers
- NO DAG building
- NO schema mutation

PHASE F-9 CONSTRAINTS:
- Preview-only capability, NO persistence
- Uses FormulaUseCases.execute_formula() for execution
- In-memory field values only
- UI-only preview effects (VISIBILITY, ENABLED, REQUIRED)

TEST REQUIREMENTS (from spec):
- Boolean acceptance: boolean formula -> ALLOWED
- Non-boolean blocking: non-boolean formula -> BLOCKED
- Governance: INVALID -> blocked, VALID/VALID_WITH_WARNINGS -> allowed
- Determinism: same input -> same output
- Preview execution: formula evaluated with temporary field values
"""

import pytest

from doc_helper.application.dto.control_rule_dto import (
    ControlRuleDiagnosticsDTO,
    ControlRuleDTO,
    ControlRuleResultDTO,
    ControlRuleStatus,
    ControlRuleType,
)
from doc_helper.application.dto.control_rule_preview_dto import (
    ControlRulePreviewInputDTO,
    ControlRulePreviewResultDTO,
)
from doc_helper.application.dto.formula_dto import (
    FormulaGovernanceStatus,
    SchemaFieldInfoDTO,
)
from doc_helper.application.usecases.control_rule_usecases import ControlRuleUseCases
from doc_helper.application.usecases.formula_usecases import FormulaUseCases


class TestControlRuleUseCases:
    """Tests for ControlRuleUseCases."""

    @pytest.fixture
    def formula_usecases(self) -> FormulaUseCases:
        """Create FormulaUseCases instance."""
        return FormulaUseCases()

    @pytest.fixture
    def usecases(self, formula_usecases: FormulaUseCases) -> ControlRuleUseCases:
        """Create ControlRuleUseCases instance."""
        return ControlRuleUseCases(formula_usecases=formula_usecases)

    @pytest.fixture
    def schema_fields(self) -> tuple[SchemaFieldInfoDTO, ...]:
        """Create sample schema fields for validation."""
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
    # Test: Boolean acceptance - boolean formula -> ALLOWED
    # =========================================================================

    def test_validate_control_rule_boolean_formula_allowed(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Boolean formula should result in ALLOWED status."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="secret_field",
            formula_text="is_admin == true",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.ALLOWED
        assert result.is_allowed is True
        assert result.is_blocked is False
        assert result.block_reason is None
        assert result.rule is not None
        assert result.rule.rule_type == ControlRuleType.VISIBILITY
        assert result.rule.target_field_id == "secret_field"
        assert result.rule.formula_text == "is_admin == true"

    def test_validate_control_rule_comparison_boolean_allowed(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Comparison expression returning boolean should be ALLOWED."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.ENABLED,
            target_field_id="target_field",
            formula_text="age > 18",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.ALLOWED
        assert result.is_allowed is True
        assert result.rule is not None
        assert result.rule.inferred_type == "BOOLEAN"

    def test_validate_control_rule_logical_and_boolean_allowed(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Logical AND expression returning boolean should be ALLOWED."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.REQUIRED,
            target_field_id="target_field",
            formula_text="is_admin and has_permission",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.ALLOWED
        assert result.is_allowed is True

    def test_validate_control_rule_logical_or_boolean_allowed(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Logical OR expression returning boolean should be ALLOWED."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin or has_permission",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.ALLOWED
        assert result.is_allowed is True

    def test_validate_control_rule_logical_not_boolean_allowed(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Logical NOT expression returning boolean should be ALLOWED."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="not is_admin",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.ALLOWED
        assert result.is_allowed is True

    def test_validate_control_rule_is_empty_function_boolean_allowed(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """is_empty() function returning boolean should be ALLOWED."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.REQUIRED,
            target_field_id="target_field",
            formula_text="is_empty(user_role)",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.ALLOWED
        assert result.is_allowed is True

    # =========================================================================
    # Test: Non-boolean blocking - non-boolean formula -> BLOCKED
    # =========================================================================

    def test_validate_control_rule_number_formula_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Number formula should result in BLOCKED status."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="age + 10",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.BLOCKED
        assert result.is_blocked is True
        assert result.is_allowed is False
        assert result.block_reason is not None
        assert "BOOLEAN" in result.block_reason
        assert "NUMBER" in result.block_reason

    def test_validate_control_rule_text_formula_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Text formula should result in BLOCKED status."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.ENABLED,
            target_field_id="target_field",
            formula_text="upper(user_role)",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.BLOCKED
        assert result.is_blocked is True
        assert "BOOLEAN" in result.block_reason
        assert "TEXT" in result.block_reason

    def test_validate_control_rule_arithmetic_formula_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Arithmetic formula should result in BLOCKED status."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.REQUIRED,
            target_field_id="target_field",
            formula_text="age * 2",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.BLOCKED
        assert result.is_blocked is True

    def test_validate_control_rule_concat_function_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """concat() function returning text should be BLOCKED."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="concat(user_role, 'test')",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.BLOCKED
        assert result.is_blocked is True
        assert "TEXT" in result.block_reason

    # =========================================================================
    # Test: Governance - INVALID -> blocked
    # =========================================================================

    def test_validate_control_rule_syntax_error_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula with syntax error should be BLOCKED (governance INVALID)."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin ==",  # Missing right operand
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.BLOCKED
        assert result.is_blocked is True
        assert result.block_reason is not None
        assert "error" in result.block_reason.lower()

    def test_validate_control_rule_unknown_field_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula with unknown field should be BLOCKED (governance INVALID)."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.ENABLED,
            target_field_id="target_field",
            formula_text="unknown_field == true",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.BLOCKED
        assert result.is_blocked is True
        assert "Unknown field" in result.block_reason

    def test_validate_control_rule_unknown_function_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Formula with unknown function should be BLOCKED (governance INVALID)."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.REQUIRED,
            target_field_id="target_field",
            formula_text="unknown_function(is_admin)",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.BLOCKED
        assert result.is_blocked is True
        assert "Unknown function" in result.block_reason

    # =========================================================================
    # Test: Empty formula -> CLEARED
    # =========================================================================

    def test_validate_control_rule_empty_formula_cleared(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Empty formula should result in CLEARED status."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.CLEARED
        assert result.is_cleared is True
        assert result.is_allowed is False
        assert result.is_blocked is False
        assert result.rule is None

    def test_validate_control_rule_whitespace_formula_cleared(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Whitespace-only formula should result in CLEARED status."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.ENABLED,
            target_field_id="target_field",
            formula_text="   ",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.CLEARED
        assert result.is_cleared is True

    # =========================================================================
    # Test: Diagnostics are populated
    # =========================================================================

    def test_validate_control_rule_has_diagnostics(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Valid rule should have populated diagnostics."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin == true",
            schema_fields=schema_fields,
        )

        assert result.rule is not None
        assert result.rule.diagnostics is not None
        diagnostics = result.rule.diagnostics
        assert diagnostics.has_validation is True
        assert diagnostics.has_dependencies is True
        assert diagnostics.has_governance is True
        assert diagnostics.inferred_type == "BOOLEAN"
        assert diagnostics.is_boolean is True

    def test_validate_control_rule_diagnostics_error_count(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Blocked rule should have error count in diagnostics."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="unknown_field == true",
            schema_fields=schema_fields,
        )

        assert result.rule is not None
        assert result.rule.diagnostics is not None
        assert result.rule.diagnostics.error_count > 0

    # =========================================================================
    # Test: All rule types work
    # =========================================================================

    def test_validate_control_rule_visibility_type(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """VISIBILITY rule type should work."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin == true",
            schema_fields=schema_fields,
        )

        assert result.is_allowed is True
        assert result.rule.rule_type == ControlRuleType.VISIBILITY

    def test_validate_control_rule_enabled_type(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """ENABLED rule type should work."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.ENABLED,
            target_field_id="target_field",
            formula_text="age >= 18",
            schema_fields=schema_fields,
        )

        assert result.is_allowed is True
        assert result.rule.rule_type == ControlRuleType.ENABLED

    def test_validate_control_rule_required_type(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """REQUIRED rule type should work."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.REQUIRED,
            target_field_id="target_field",
            formula_text="has_permission == true",
            schema_fields=schema_fields,
        )

        assert result.is_allowed is True
        assert result.rule.rule_type == ControlRuleType.REQUIRED

    # =========================================================================
    # Test: Determinism - same input -> same output
    # =========================================================================

    def test_validate_control_rule_deterministic(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Same input should produce same output (determinism)."""
        result1 = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin == true",
            schema_fields=schema_fields,
        )

        result2 = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin == true",
            schema_fields=schema_fields,
        )

        assert result1.status == result2.status
        assert result1.is_allowed == result2.is_allowed
        assert result1.block_reason == result2.block_reason

    # =========================================================================
    # Test: can_apply_control_rule
    # =========================================================================

    def test_can_apply_control_rule_boolean_allowed(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """can_apply_control_rule should return ALLOWED for boolean formula."""
        result = usecases.can_apply_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            formula_text="is_admin == true",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.ALLOWED
        assert result.is_allowed is True
        assert result.rule is None  # can_apply doesn't create rule

    def test_can_apply_control_rule_non_boolean_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """can_apply_control_rule should return BLOCKED for non-boolean formula."""
        result = usecases.can_apply_control_rule(
            rule_type=ControlRuleType.ENABLED,
            formula_text="age + 10",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.BLOCKED
        assert result.is_blocked is True
        assert "BOOLEAN" in result.block_reason

    def test_can_apply_control_rule_empty_cleared(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """can_apply_control_rule should return CLEARED for empty formula."""
        result = usecases.can_apply_control_rule(
            rule_type=ControlRuleType.REQUIRED,
            formula_text="",
            schema_fields=schema_fields,
        )

        assert result.status == ControlRuleStatus.CLEARED
        assert result.is_cleared is True

    # =========================================================================
    # Test: clear_control_rule
    # =========================================================================

    def test_clear_control_rule_returns_cleared(
        self, usecases: ControlRuleUseCases
    ) -> None:
        """clear_control_rule should return CLEARED result."""
        result = usecases.clear_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
        )

        assert result.status == ControlRuleStatus.CLEARED
        assert result.is_cleared is True
        assert result.rule is None
        assert result.block_reason is None

    def test_clear_control_rule_all_types(
        self, usecases: ControlRuleUseCases
    ) -> None:
        """clear_control_rule should work for all rule types."""
        for rule_type in ControlRuleType:
            result = usecases.clear_control_rule(
                rule_type=rule_type,
                target_field_id="target_field",
            )
            assert result.status == ControlRuleStatus.CLEARED

    # =========================================================================
    # Test: Status message
    # =========================================================================

    def test_status_message_allowed(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """ALLOWED status should have appropriate message."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin == true",
            schema_fields=schema_fields,
        )

        assert "valid" in result.status_message.lower()

    def test_status_message_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """BLOCKED status should have appropriate message."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="age + 10",
            schema_fields=schema_fields,
        )

        assert "blocked" in result.status_message.lower()

    def test_status_message_cleared(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """CLEARED status should have appropriate message."""
        result = usecases.validate_control_rule(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="",
            schema_fields=schema_fields,
        )

        assert "cleared" in result.status_message.lower()

    # =========================================================================
    # Test: preview_control_rule (Phase F-9)
    # =========================================================================

    def test_preview_control_rule_valid_formula_returns_result(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview with valid boolean formula returns execution result."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin == true",
        )

        result = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={"is_admin": True},
        )

        assert result.validation_status == ControlRuleStatus.ALLOWED
        assert result.is_allowed is True
        assert result.is_blocked is False
        assert result.execution_result is True
        assert result.execution_error is None

    def test_preview_control_rule_formula_evaluates_to_false(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview formula can evaluate to False."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin == true",
        )

        result = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={"is_admin": False},
        )

        assert result.is_allowed is True
        assert result.execution_result is False

    def test_preview_control_rule_blocked_formula_no_execution(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview with blocked formula returns blocked status without execution."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.ENABLED,
            target_field_id="target_field",
            formula_text="age + 10",  # Non-boolean -> BLOCKED
        )

        result = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={"age": 25},
        )

        assert result.validation_status == ControlRuleStatus.BLOCKED
        assert result.is_blocked is True
        assert result.is_allowed is False
        assert result.execution_result is None  # No execution for blocked
        assert result.block_reason is not None
        assert "BOOLEAN" in result.block_reason

    def test_preview_control_rule_empty_formula_cleared(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview with empty formula returns CLEARED status."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.REQUIRED,
            target_field_id="target_field",
            formula_text="",
        )

        result = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={},
        )

        assert result.validation_status == ControlRuleStatus.CLEARED
        assert result.is_allowed is False
        assert result.is_blocked is False
        assert result.execution_result is None

    def test_preview_control_rule_whitespace_formula_cleared(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview with whitespace-only formula returns CLEARED status."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="   ",
        )

        result = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={},
        )

        assert result.validation_status == ControlRuleStatus.CLEARED

    def test_preview_control_rule_uses_field_values(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview executes formula with provided field_values."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.ENABLED,
            target_field_id="target_field",
            formula_text="age >= 18",
        )

        # Test with age = 20 (should be True)
        result1 = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={"age": 20},
        )
        assert result1.execution_result is True

        # Test with age = 15 (should be False)
        result2 = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={"age": 15},
        )
        assert result2.execution_result is False

    def test_preview_control_rule_complex_expression(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview handles complex boolean expressions."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin and has_permission",
        )

        # Both True
        result1 = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={"is_admin": True, "has_permission": True},
        )
        assert result1.execution_result is True

        # One False
        result2 = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={"is_admin": True, "has_permission": False},
        )
        assert result2.execution_result is False

    def test_preview_control_rule_deterministic(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview is deterministic: same input -> same output."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin == true",
        )
        field_values = {"is_admin": True}

        result1 = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values=field_values,
        )

        result2 = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values=field_values,
        )

        assert result1.validation_status == result2.validation_status
        assert result1.is_allowed == result2.is_allowed
        assert result1.execution_result == result2.execution_result

    def test_preview_control_rule_all_rule_types(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview works with all control rule types."""
        for rule_type in ControlRuleType:
            rule_input = ControlRulePreviewInputDTO(
                rule_type=rule_type,
                target_field_id="target_field",
                formula_text="is_admin == true",
            )

            result = usecases.preview_control_rule(
                rule_input=rule_input,
                schema_fields=schema_fields,
                field_values={"is_admin": True},
            )

            assert result.is_allowed is True
            assert result.execution_result is True

    def test_preview_control_rule_preserves_input(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview result includes the input rule."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.REQUIRED,
            target_field_id="my_field",
            formula_text="has_permission == true",
        )

        result = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={"has_permission": True},
        )

        assert result.rule_input == rule_input
        assert result.rule_input.rule_type == ControlRuleType.REQUIRED
        assert result.rule_input.target_field_id == "my_field"
        assert result.rule_input.formula_text == "has_permission == true"

    def test_preview_control_rule_governance_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview with invalid governance (syntax error) returns blocked."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin ==",  # Syntax error
        )

        result = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={"is_admin": True},
        )

        assert result.is_blocked is True
        assert result.execution_result is None
        assert "error" in result.block_reason.lower()

    def test_preview_control_rule_unknown_field_blocked(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview with unknown field reference returns blocked."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.ENABLED,
            target_field_id="target_field",
            formula_text="unknown_field == true",
        )

        result = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={"unknown_field": True},
        )

        assert result.is_blocked is True
        assert "Unknown field" in result.block_reason

    def test_preview_control_rule_missing_field_value(
        self, usecases: ControlRuleUseCases, schema_fields: tuple[SchemaFieldInfoDTO, ...]
    ) -> None:
        """Preview with missing field value handles gracefully."""
        rule_input = ControlRulePreviewInputDTO(
            rule_type=ControlRuleType.VISIBILITY,
            target_field_id="target_field",
            formula_text="is_admin == true",
        )

        result = usecases.preview_control_rule(
            rule_input=rule_input,
            schema_fields=schema_fields,
            field_values={},  # Missing is_admin
        )

        # Should still be allowed (formula is valid)
        assert result.is_allowed is True
        # Execution may fail or return None-ish value
        # The important thing is it doesn't crash

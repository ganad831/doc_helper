"""Tests for control effect evaluator."""

import pytest

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.control.control_effect import ControlEffect, ControlType
from doc_helper.domain.control.control_rule import ControlRule, ControlRuleId
from doc_helper.domain.control.effect_evaluator import (
    ControlEffectEvaluator,
    EvaluationResult,
)
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class TestEvaluationResult:
    """Tests for EvaluationResult."""

    def test_create_evaluation_result(self) -> None:
        """EvaluationResult should be created with effects and errors."""
        effect1 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        result = EvaluationResult(effects=(effect1,), errors=())
        assert len(result.effects) == 1
        assert len(result.errors) == 0

    def test_evaluation_result_with_errors(self) -> None:
        """EvaluationResult should store errors."""
        result = EvaluationResult(effects=(), errors=("Error 1", "Error 2"))
        assert len(result.effects) == 0
        assert len(result.errors) == 2

    def test_has_effects(self) -> None:
        """has_effects should return True when effects exist."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        result1 = EvaluationResult(effects=(effect,), errors=())
        assert result1.has_effects is True

        result2 = EvaluationResult(effects=(), errors=())
        assert result2.has_effects is False

    def test_has_errors(self) -> None:
        """has_errors should return True when errors exist."""
        result1 = EvaluationResult(effects=(), errors=("Error",))
        assert result1.has_errors is True

        result2 = EvaluationResult(effects=(), errors=())
        assert result2.has_errors is False

    def test_get_effects_for_field(self) -> None:
        """get_effects_for_field should filter effects by target field."""
        effect1 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        effect2 = ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("field2"),
            value=False,
        )
        effect3 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=200,
        )
        result = EvaluationResult(effects=(effect1, effect2, effect3), errors=())

        field1_effects = result.get_effects_for_field(FieldDefinitionId("field1"))
        assert len(field1_effects) == 2
        assert effect1 in field1_effects
        assert effect3 in field1_effects

        field2_effects = result.get_effects_for_field(FieldDefinitionId("field2"))
        assert len(field2_effects) == 1
        assert effect2 in field2_effects

        field3_effects = result.get_effects_for_field(FieldDefinitionId("field3"))
        assert len(field3_effects) == 0

    def test_get_effects_for_field_requires_field_definition_id(self) -> None:
        """get_effects_for_field should require FieldDefinitionId."""
        result = EvaluationResult(effects=(), errors=())
        with pytest.raises(TypeError, match="field_id must be a FieldDefinitionId"):
            result.get_effects_for_field("field1")  # type: ignore

    def test_evaluation_result_effects_must_be_tuple(self) -> None:
        """EvaluationResult should require tuple for effects."""
        with pytest.raises(TypeError, match="effects must be a tuple"):
            EvaluationResult(effects=[], errors=())  # type: ignore

    def test_evaluation_result_errors_must_be_tuple(self) -> None:
        """EvaluationResult should require tuple for errors."""
        with pytest.raises(TypeError, match="errors must be a tuple"):
            EvaluationResult(effects=(), errors=[])  # type: ignore

    def test_evaluation_result_effects_must_contain_control_effects(self) -> None:
        """EvaluationResult should require ControlEffect instances."""
        with pytest.raises(TypeError, match="effects must contain only ControlEffect"):
            EvaluationResult(effects=("invalid",), errors=())  # type: ignore

    def test_evaluation_result_errors_must_contain_strings(self) -> None:
        """EvaluationResult should require string errors."""
        with pytest.raises(TypeError, match="errors must contain only strings"):
            EvaluationResult(effects=(), errors=(123,))  # type: ignore

    def test_evaluation_result_is_immutable(self) -> None:
        """EvaluationResult should be immutable."""
        result = EvaluationResult(effects=(), errors=())
        with pytest.raises(Exception):  # FrozenInstanceError
            result.effects = ()  # type: ignore


class TestControlEffectEvaluator:
    """Tests for ControlEffectEvaluator."""

    def test_evaluate_empty_rules(self) -> None:
        """Evaluator should handle empty rule list."""
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(rules=[], field_values={})
        assert len(result.effects) == 0
        assert len(result.errors) == 0

    def test_evaluate_rule_with_true_condition(self) -> None:
        """Evaluator should apply effect when condition is true."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("total"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_1"),
            name_key=TranslationKey("rule.set_total"),
            condition="field1 > 50",
            effect=effect,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(
            rules=[rule], field_values={"field1": 60}  # Condition true
        )
        assert len(result.effects) == 1
        assert result.effects[0] == effect

    def test_evaluate_rule_with_false_condition(self) -> None:
        """Evaluator should not apply effect when condition is false."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("total"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_2"),
            name_key=TranslationKey("rule.set_total"),
            condition="field1 > 50",
            effect=effect,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(
            rules=[rule], field_values={"field1": 30}  # Condition false
        )
        assert len(result.effects) == 0

    def test_evaluate_disabled_rule(self) -> None:
        """Evaluator should skip disabled rules."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("total"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_3"),
            name_key=TranslationKey("rule.set_total"),
            condition="true",  # Would be true
            effect=effect,
            enabled=False,  # But disabled
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(rules=[rule], field_values={})
        assert len(result.effects) == 0

    def test_evaluate_multiple_rules(self) -> None:
        """Evaluator should evaluate multiple rules."""
        effect1 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        effect2 = ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("field2"),
            value=False,
        )
        rule1 = ControlRule(
            id=ControlRuleId("rule_4"),
            name_key=TranslationKey("rule.1"),
            condition="x > 10",
            effect=effect1,
        )
        rule2 = ControlRule(
            id=ControlRuleId("rule_5"),
            name_key=TranslationKey("rule.2"),
            condition="y == null",
            effect=effect2,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(
            rules=[rule1, rule2], field_values={"x": 20, "y": None}  # Both true
        )
        assert len(result.effects) == 2
        assert effect1 in result.effects
        assert effect2 in result.effects

    def test_evaluate_rules_respects_priority(self) -> None:
        """Evaluator should evaluate higher priority rules first."""
        effect1 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        effect2 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=200,
        )
        rule1 = ControlRule(
            id=ControlRuleId("rule_6"),
            name_key=TranslationKey("rule.1"),
            condition="true",
            effect=effect1,
            priority=5,
        )
        rule2 = ControlRule(
            id=ControlRuleId("rule_7"),
            name_key=TranslationKey("rule.2"),
            condition="true",
            effect=effect2,
            priority=10,  # Higher priority
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(rules=[rule1, rule2], field_values={})
        # Both effects should be present, but rule2's effect should come first
        assert len(result.effects) == 2
        assert result.effects[0] == effect2  # Higher priority first
        assert result.effects[1] == effect1

    def test_evaluate_rule_with_functions(self) -> None:
        """Evaluator should support functions in conditions."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("result"),
            value=True,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_8"),
            name_key=TranslationKey("rule.test"),
            condition="min(a, b) > 10",
            effect=effect,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(
            rules=[rule], field_values={"a": 20, "b": 15}, functions={"min": min}
        )
        assert len(result.effects) == 1

    def test_evaluate_rule_with_invalid_condition(self) -> None:
        """Evaluator should capture errors for invalid conditions."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_9"),
            name_key=TranslationKey("rule.test"),
            condition="invalid syntax!@#",
            effect=effect,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(rules=[rule], field_values={})
        assert len(result.effects) == 0
        assert len(result.errors) == 1
        assert "rule_9" in result.errors[0]

    def test_evaluate_rule_with_missing_field(self) -> None:
        """Evaluator should capture errors for missing fields."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_10"),
            name_key=TranslationKey("rule.test"),
            condition="unknown_field > 10",
            effect=effect,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(rules=[rule], field_values={})
        assert len(result.effects) == 0
        assert len(result.errors) == 1
        assert "rule_10" in result.errors[0]

    def test_evaluate_rule_with_non_boolean_condition(self) -> None:
        """Evaluator should reject non-boolean condition results."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_11"),
            name_key=TranslationKey("rule.test"),
            condition="field1 + 10",  # Returns number, not boolean
            effect=effect,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(rules=[rule], field_values={"field1": 5})
        assert len(result.effects) == 0
        assert len(result.errors) == 1
        assert "must evaluate to boolean" in result.errors[0]

    def test_evaluate_single_rule(self) -> None:
        """Evaluator should evaluate a single rule."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("total"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_12"),
            name_key=TranslationKey("rule.test"),
            condition="field1 > 50",
            effect=effect,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rule(rule=rule, field_values={"field1": 60})
        assert isinstance(result, Success)
        assert result.value is True

    def test_evaluate_single_rule_false_condition(self) -> None:
        """Evaluator should return Success(False) for false condition."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("total"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_13"),
            name_key=TranslationKey("rule.test"),
            condition="field1 > 50",
            effect=effect,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rule(rule=rule, field_values={"field1": 30})
        assert isinstance(result, Success)
        assert result.value is False

    def test_evaluate_single_rule_disabled(self) -> None:
        """Evaluator should return Success(False) for disabled rule."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("total"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_14"),
            name_key=TranslationKey("rule.test"),
            condition="true",
            effect=effect,
            enabled=False,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rule(rule=rule, field_values={})
        assert isinstance(result, Success)
        assert result.value is False

    def test_evaluate_single_rule_error(self) -> None:
        """Evaluator should return Failure for rule evaluation error."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("total"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_15"),
            name_key=TranslationKey("rule.test"),
            condition="unknown_field > 10",
            effect=effect,
        )
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rule(rule=rule, field_values={})
        assert isinstance(result, Failure)

    def test_resolve_conflicts_no_conflicts(self) -> None:
        """resolve_conflicts should keep all effects when no conflicts."""
        effect1 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        effect2 = ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("field2"),
            value=False,
        )
        evaluator = ControlEffectEvaluator()
        resolved = evaluator.resolve_conflicts([effect1, effect2])
        assert len(resolved) == 2
        assert effect1 in resolved
        assert effect2 in resolved

    def test_resolve_conflicts_with_conflicts(self) -> None:
        """resolve_conflicts should keep first effect when multiple target same field."""
        effect1 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        effect2 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=200,
        )
        effect3 = ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("field2"),
            value=False,
        )
        evaluator = ControlEffectEvaluator()
        resolved = evaluator.resolve_conflicts([effect1, effect2, effect3])
        assert len(resolved) == 2
        assert effect1 in resolved  # First effect for field1
        assert effect2 not in resolved  # Conflict, removed
        assert effect3 in resolved

    def test_evaluate_rules_requires_list(self) -> None:
        """evaluate_rules should require list of rules."""
        evaluator = ControlEffectEvaluator()
        with pytest.raises(TypeError, match="rules must be a list"):
            evaluator.evaluate_rules(rules="invalid", field_values={})  # type: ignore

    def test_evaluate_rules_requires_control_rules(self) -> None:
        """evaluate_rules should require ControlRule instances."""
        evaluator = ControlEffectEvaluator()
        with pytest.raises(TypeError, match="rules must contain only ControlRule"):
            evaluator.evaluate_rules(rules=["invalid"], field_values={})  # type: ignore

    def test_evaluate_rules_requires_dict_field_values(self) -> None:
        """evaluate_rules should require dict for field_values."""
        evaluator = ControlEffectEvaluator()
        with pytest.raises(TypeError, match="field_values must be a dict"):
            evaluator.evaluate_rules(rules=[], field_values=[])  # type: ignore

    def test_evaluate_rules_requires_dict_functions(self) -> None:
        """evaluate_rules should require dict for functions if provided."""
        evaluator = ControlEffectEvaluator()
        with pytest.raises(TypeError, match="functions must be a dict or None"):
            evaluator.evaluate_rules(rules=[], field_values={}, functions=[])  # type: ignore

    def test_evaluate_rule_requires_control_rule(self) -> None:
        """evaluate_rule should require ControlRule."""
        evaluator = ControlEffectEvaluator()
        with pytest.raises(TypeError, match="rule must be a ControlRule"):
            evaluator.evaluate_rule(rule="invalid", field_values={})  # type: ignore

    def test_resolve_conflicts_requires_list(self) -> None:
        """resolve_conflicts should require list of effects."""
        evaluator = ControlEffectEvaluator()
        with pytest.raises(TypeError, match="effects must be a list"):
            evaluator.resolve_conflicts("invalid")  # type: ignore

    def test_resolve_conflicts_requires_control_effects(self) -> None:
        """resolve_conflicts should require ControlEffect instances."""
        evaluator = ControlEffectEvaluator()
        with pytest.raises(TypeError, match="effects must contain only ControlEffect"):
            evaluator.resolve_conflicts(["invalid"])  # type: ignore

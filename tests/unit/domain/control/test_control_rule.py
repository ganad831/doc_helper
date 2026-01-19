"""Tests for control rules."""

import pytest

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.control.control_effect import ControlEffect, ControlType
from doc_helper.domain.control.control_rule import ControlRule, ControlRuleId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class TestControlRuleId:
    """Tests for ControlRuleId."""

    def test_create_control_rule_id(self) -> None:
        """ControlRuleId should be created with valid string."""
        rule_id = ControlRuleId("rule_123")
        assert rule_id.value == "rule_123"

    def test_control_rule_id_allows_alphanumeric(self) -> None:
        """ControlRuleId should allow alphanumeric characters."""
        rule_id = ControlRuleId("rule123ABC")
        assert rule_id.value == "rule123ABC"

    def test_control_rule_id_allows_underscore(self) -> None:
        """ControlRuleId should allow underscores."""
        rule_id = ControlRuleId("rule_with_underscore")
        assert rule_id.value == "rule_with_underscore"

    def test_control_rule_id_allows_hyphen(self) -> None:
        """ControlRuleId should allow hyphens."""
        rule_id = ControlRuleId("rule-with-hyphen")
        assert rule_id.value == "rule-with-hyphen"

    def test_control_rule_id_requires_string(self) -> None:
        """ControlRuleId should require string value."""
        with pytest.raises(TypeError, match="ControlRuleId value must be a string"):
            ControlRuleId(123)  # type: ignore

    def test_control_rule_id_cannot_be_empty(self) -> None:
        """ControlRuleId cannot be empty."""
        with pytest.raises(ValueError, match="ControlRuleId cannot be empty"):
            ControlRuleId("")

    def test_control_rule_id_rejects_special_chars(self) -> None:
        """ControlRuleId should reject special characters."""
        with pytest.raises(
            ValueError, match="can only contain alphanumeric, underscore, and hyphen"
        ):
            ControlRuleId("rule@invalid")

    def test_control_rule_id_equality(self) -> None:
        """ControlRuleId should support equality comparison."""
        id1 = ControlRuleId("rule_1")
        id2 = ControlRuleId("rule_1")
        id3 = ControlRuleId("rule_2")
        assert id1 == id2
        assert id1 != id3

    def test_control_rule_id_inequality_with_other_types(self) -> None:
        """ControlRuleId should not equal other types."""
        rule_id = ControlRuleId("rule_1")
        assert rule_id != "rule_1"
        assert rule_id != 123

    def test_control_rule_id_hashable(self) -> None:
        """ControlRuleId should be hashable."""
        id1 = ControlRuleId("rule_1")
        id2 = ControlRuleId("rule_2")
        rule_set = {id1, id2, id1}
        assert len(rule_set) == 2

    def test_control_rule_id_repr(self) -> None:
        """ControlRuleId should have string representation."""
        rule_id = ControlRuleId("rule_1")
        assert repr(rule_id) == "ControlRuleId('rule_1')"


class TestControlRule:
    """Tests for ControlRule entity."""

    def test_create_control_rule(self) -> None:
        """ControlRule should be created with required fields."""
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
        assert rule.id == ControlRuleId("rule_1")
        assert rule.name_key == TranslationKey("rule.set_total")
        assert rule.condition == "field1 > 50"
        assert rule.effect == effect
        assert rule.enabled is True  # Default
        assert rule.priority == 0  # Default

    def test_create_control_rule_with_description(self) -> None:
        """ControlRule should accept optional description."""
        effect = ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("optional_field"),
            value=False,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_2"),
            name_key=TranslationKey("rule.hide_optional"),
            condition="required_field == null",
            effect=effect,
            description_key=TranslationKey("rule.hide_optional.desc"),
        )
        assert rule.description_key == TranslationKey("rule.hide_optional.desc")

    def test_create_control_rule_with_priority(self) -> None:
        """ControlRule should accept priority."""
        effect = ControlEffect(
            control_type=ControlType.ENABLE,
            target_field_id=FieldDefinitionId("field1"),
            value=True,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_3"),
            name_key=TranslationKey("rule.enable_field"),
            condition="other_field != null",
            effect=effect,
            priority=10,
        )
        assert rule.priority == 10

    def test_control_rule_disabled_by_default(self) -> None:
        """ControlRule should be enabled by default."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_4"),
            name_key=TranslationKey("rule.test"),
            condition="true",
            effect=effect,
        )
        assert rule.enabled is True
        assert rule.is_enabled is True
        assert rule.is_disabled is False

    def test_control_rule_can_be_disabled(self) -> None:
        """ControlRule should accept enabled=False."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_5"),
            name_key=TranslationKey("rule.test"),
            condition="true",
            effect=effect,
            enabled=False,
        )
        assert rule.enabled is False
        assert rule.is_enabled is False
        assert rule.is_disabled is True

    def test_enable_control_rule(self) -> None:
        """ControlRule.enable() should enable the rule."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_6"),
            name_key=TranslationKey("rule.test"),
            condition="true",
            effect=effect,
            enabled=False,
        )
        rule.enable()
        assert rule.enabled is True
        assert rule.is_enabled is True

    def test_disable_control_rule(self) -> None:
        """ControlRule.disable() should disable the rule."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_7"),
            name_key=TranslationKey("rule.test"),
            condition="true",
            effect=effect,
        )
        rule.disable()
        assert rule.enabled is False
        assert rule.is_disabled is True

    def test_enable_touches_entity(self) -> None:
        """ControlRule.enable() should update modified timestamp."""
        import time

        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_8"),
            name_key=TranslationKey("rule.test"),
            condition="true",
            effect=effect,
            enabled=False,
        )
        original_modified = rule.modified_at
        time.sleep(0.001)  # Ensure timestamp difference
        rule.enable()
        assert rule.modified_at > original_modified

    def test_disable_touches_entity(self) -> None:
        """ControlRule.disable() should update modified timestamp."""
        import time

        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_9"),
            name_key=TranslationKey("rule.test"),
            condition="true",
            effect=effect,
        )
        original_modified = rule.modified_at
        time.sleep(0.001)  # Ensure timestamp difference
        rule.disable()
        assert rule.modified_at > original_modified

    def test_target_field_id_property(self) -> None:
        """ControlRule should expose target_field_id from effect."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("total"),
            value=100,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_10"),
            name_key=TranslationKey("rule.test"),
            condition="true",
            effect=effect,
        )
        assert rule.target_field_id == FieldDefinitionId("total")

    def test_control_type_property(self) -> None:
        """ControlRule should expose control_type from effect."""
        effect = ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("field1"),
            value=False,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_11"),
            name_key=TranslationKey("rule.test"),
            condition="true",
            effect=effect,
        )
        assert rule.control_type == ControlType.VISIBILITY

    def test_control_rule_requires_name_key(self) -> None:
        """ControlRule should require TranslationKey for name_key."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        with pytest.raises(TypeError, match="name_key must be a TranslationKey"):
            ControlRule(
                id=ControlRuleId("rule_12"),
                name_key="invalid",  # type: ignore
                condition="true",
                effect=effect,
            )

    def test_control_rule_requires_condition_string(self) -> None:
        """ControlRule should require string for condition."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        with pytest.raises(TypeError, match="condition must be a string"):
            ControlRule(
                id=ControlRuleId("rule_13"),
                name_key=TranslationKey("rule.test"),
                condition=123,  # type: ignore
                effect=effect,
            )

    def test_control_rule_condition_cannot_be_empty(self) -> None:
        """ControlRule should reject empty condition."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        with pytest.raises(ValueError, match="condition cannot be empty"):
            ControlRule(
                id=ControlRuleId("rule_14"),
                name_key=TranslationKey("rule.test"),
                condition="",
                effect=effect,
            )

    def test_control_rule_requires_control_effect(self) -> None:
        """ControlRule should require ControlEffect for effect."""
        with pytest.raises(TypeError, match="effect must be a ControlEffect"):
            ControlRule(
                id=ControlRuleId("rule_15"),
                name_key=TranslationKey("rule.test"),
                condition="true",
                effect="invalid",  # type: ignore
            )

    def test_control_rule_requires_bool_enabled(self) -> None:
        """ControlRule should require bool for enabled."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        with pytest.raises(TypeError, match="enabled must be a bool"):
            ControlRule(
                id=ControlRuleId("rule_16"),
                name_key=TranslationKey("rule.test"),
                condition="true",
                effect=effect,
                enabled="yes",  # type: ignore
            )

    def test_control_rule_requires_int_priority(self) -> None:
        """ControlRule should require int for priority."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        with pytest.raises(TypeError, match="priority must be an int"):
            ControlRule(
                id=ControlRuleId("rule_17"),
                name_key=TranslationKey("rule.test"),
                condition="true",
                effect=effect,
                priority="high",  # type: ignore
            )

    def test_control_rule_description_key_optional(self) -> None:
        """ControlRule should accept None for description_key."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        rule = ControlRule(
            id=ControlRuleId("rule_18"),
            name_key=TranslationKey("rule.test"),
            condition="true",
            effect=effect,
            description_key=None,
        )
        assert rule.description_key is None

    def test_control_rule_description_key_requires_translation_key(self) -> None:
        """ControlRule should require TranslationKey for description_key if provided."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=0,
        )
        with pytest.raises(TypeError, match="description_key must be a TranslationKey or None"):
            ControlRule(
                id=ControlRuleId("rule_19"),
                name_key=TranslationKey("rule.test"),
                condition="true",
                effect=effect,
                description_key="invalid",  # type: ignore
            )

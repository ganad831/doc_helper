"""Tests for control effects."""

import pytest

from doc_helper.domain.control.control_effect import ControlEffect, ControlType
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class TestControlType:
    """Tests for ControlType enum."""

    def test_value_set_type(self) -> None:
        """ControlType.VALUE_SET should exist."""
        assert ControlType.VALUE_SET == "value_set"

    def test_visibility_type(self) -> None:
        """ControlType.VISIBILITY should exist."""
        assert ControlType.VISIBILITY == "visibility"

    def test_enable_type(self) -> None:
        """ControlType.ENABLE should exist."""
        assert ControlType.ENABLE == "enable"

    def test_is_value_setter(self) -> None:
        """is_value_setter should return True only for VALUE_SET."""
        assert ControlType.VALUE_SET.is_value_setter is True
        assert ControlType.VISIBILITY.is_value_setter is False
        assert ControlType.ENABLE.is_value_setter is False

    def test_is_visibility_control(self) -> None:
        """is_visibility_control should return True only for VISIBILITY."""
        assert ControlType.VALUE_SET.is_visibility_control is False
        assert ControlType.VISIBILITY.is_visibility_control is True
        assert ControlType.ENABLE.is_visibility_control is False

    def test_is_enable_control(self) -> None:
        """is_enable_control should return True only for ENABLE."""
        assert ControlType.VALUE_SET.is_enable_control is False
        assert ControlType.VISIBILITY.is_enable_control is False
        assert ControlType.ENABLE.is_enable_control is True


class TestControlEffect:
    """Tests for ControlEffect value object."""

    def test_create_value_set_effect(self) -> None:
        """ControlEffect should be created with VALUE_SET type."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("total"),
            value=100,
        )
        assert effect.control_type == ControlType.VALUE_SET
        assert effect.target_field_id == FieldDefinitionId("total")
        assert effect.value == 100

    def test_create_visibility_effect(self) -> None:
        """ControlEffect should be created with VISIBILITY type."""
        effect = ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("optional_field"),
            value=False,
        )
        assert effect.control_type == ControlType.VISIBILITY
        assert effect.target_field_id == FieldDefinitionId("optional_field")
        assert effect.value is False

    def test_create_enable_effect(self) -> None:
        """ControlEffect should be created with ENABLE type."""
        effect = ControlEffect(
            control_type=ControlType.ENABLE,
            target_field_id=FieldDefinitionId("readonly_field"),
            value=False,
        )
        assert effect.control_type == ControlType.ENABLE
        assert effect.target_field_id == FieldDefinitionId("readonly_field")
        assert effect.value is False

    def test_effect_is_immutable(self) -> None:
        """ControlEffect should be immutable."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=42,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            effect.value = 100  # type: ignore

    def test_effect_requires_control_type(self) -> None:
        """ControlEffect should require ControlType."""
        with pytest.raises(TypeError, match="control_type must be a ControlType"):
            ControlEffect(
                control_type="invalid",  # type: ignore
                target_field_id=FieldDefinitionId("field1"),
                value=100,
            )

    def test_effect_requires_field_definition_id(self) -> None:
        """ControlEffect should require FieldDefinitionId."""
        with pytest.raises(TypeError, match="target_field_id must be a FieldDefinitionId"):
            ControlEffect(
                control_type=ControlType.VALUE_SET,
                target_field_id="field1",  # type: ignore
                value=100,
            )

    def test_visibility_effect_requires_bool_value(self) -> None:
        """VISIBILITY effect should require bool value."""
        with pytest.raises(TypeError, match="VISIBILITY control value must be bool"):
            ControlEffect(
                control_type=ControlType.VISIBILITY,
                target_field_id=FieldDefinitionId("field1"),
                value="invalid",  # type: ignore
            )

    def test_enable_effect_requires_bool_value(self) -> None:
        """ENABLE effect should require bool value."""
        with pytest.raises(TypeError, match="ENABLE control value must be bool"):
            ControlEffect(
                control_type=ControlType.ENABLE,
                target_field_id=FieldDefinitionId("field1"),
                value=123,  # type: ignore
            )

    def test_value_set_effect_allows_any_value(self) -> None:
        """VALUE_SET effect should allow any value type."""
        # Integer
        effect1 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        assert effect1.value == 100

        # String
        effect2 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field2"),
            value="test",
        )
        assert effect2.value == "test"

        # Boolean
        effect3 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field3"),
            value=True,
        )
        assert effect3.value is True

        # None
        effect4 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field4"),
            value=None,
        )
        assert effect4.value is None

    def test_effect_is_value_setter(self) -> None:
        """is_value_setter should return True only for VALUE_SET effects."""
        effect1 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        assert effect1.is_value_setter is True

        effect2 = ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("field2"),
            value=True,
        )
        assert effect2.is_value_setter is False

    def test_effect_is_visibility_effect(self) -> None:
        """is_visibility_effect should return True only for VISIBILITY effects."""
        effect1 = ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("field1"),
            value=True,
        )
        assert effect1.is_visibility_effect is True

        effect2 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field2"),
            value=100,
        )
        assert effect2.is_visibility_effect is False

    def test_effect_is_enable_effect(self) -> None:
        """is_enable_effect should return True only for ENABLE effects."""
        effect1 = ControlEffect(
            control_type=ControlType.ENABLE,
            target_field_id=FieldDefinitionId("field1"),
            value=True,
        )
        assert effect1.is_enable_effect is True

        effect2 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field2"),
            value=100,
        )
        assert effect2.is_enable_effect is False

    def test_effect_equality(self) -> None:
        """ControlEffect should support equality comparison."""
        effect1 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        effect2 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=100,
        )
        effect3 = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field1"),
            value=200,
        )
        assert effect1 == effect2
        assert effect1 != effect3

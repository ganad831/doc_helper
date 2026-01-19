"""Control effects.

Defines what happens when a control rule condition is satisfied.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from doc_helper.domain.common.value_object import ValueObject
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class ControlType(str, Enum):
    """Types of control effects.

    Controls determine how fields behave based on conditions.
    """

    VALUE_SET = "value_set"  # Set field value when condition is true
    VISIBILITY = "visibility"  # Show/hide field based on condition
    ENABLE = "enable"  # Enable/disable field based on condition

    @property
    def is_value_setter(self) -> bool:
        """Check if this control type sets a value.

        Returns:
            True if control type is VALUE_SET
        """
        return self == ControlType.VALUE_SET

    @property
    def is_visibility_control(self) -> bool:
        """Check if this control type affects visibility.

        Returns:
            True if control type is VISIBILITY
        """
        return self == ControlType.VISIBILITY

    @property
    def is_enable_control(self) -> bool:
        """Check if this control type affects enabled state.

        Returns:
            True if control type is ENABLE
        """
        return self == ControlType.ENABLE


@dataclass(frozen=True)
class ControlEffect(ValueObject):
    """Effect to apply when control condition is satisfied.

    A ControlEffect defines what happens to a target field when a condition is true.

    Examples:
        # Set field value
        ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("total"),
            value=100
        )

        # Hide field
        ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("optional_field"),
            value=False  # False means hide
        )

        # Disable field
        ControlEffect(
            control_type=ControlType.ENABLE,
            target_field_id=FieldDefinitionId("readonly_field"),
            value=False  # False means disable
        )
    """

    control_type: ControlType
    target_field_id: FieldDefinitionId
    value: Any  # Value to set (for VALUE_SET) or bool (for VISIBILITY/ENABLE)

    def __post_init__(self) -> None:
        """Validate control effect."""
        if not isinstance(self.control_type, ControlType):
            raise TypeError("control_type must be a ControlType")
        if not isinstance(self.target_field_id, FieldDefinitionId):
            raise TypeError("target_field_id must be a FieldDefinitionId")

        # Validate value based on control type
        if self.control_type == ControlType.VISIBILITY:
            if not isinstance(self.value, bool):
                raise TypeError("VISIBILITY control value must be bool (True=visible, False=hidden)")
        elif self.control_type == ControlType.ENABLE:
            if not isinstance(self.value, bool):
                raise TypeError("ENABLE control value must be bool (True=enabled, False=disabled)")
        # VALUE_SET can be any type

    @property
    def is_value_setter(self) -> bool:
        """Check if this effect sets a field value.

        Returns:
            True if effect type is VALUE_SET
        """
        return self.control_type.is_value_setter

    @property
    def is_visibility_effect(self) -> bool:
        """Check if this effect controls visibility.

        Returns:
            True if effect type is VISIBILITY
        """
        return self.control_type.is_visibility_control

    @property
    def is_enable_effect(self) -> bool:
        """Check if this effect controls enabled state.

        Returns:
            True if effect type is ENABLE
        """
        return self.control_type.is_enable_control

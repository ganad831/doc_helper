"""Control rule entity.

A control rule applies an effect when a condition is satisfied.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from doc_helper.domain.common.entity import Entity
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.control.control_effect import ControlEffect


@dataclass
class ControlRuleId:
    """Strongly-typed ID for ControlRule."""

    value: str

    def __post_init__(self) -> None:
        """Validate control rule ID."""
        if not isinstance(self.value, str):
            raise TypeError("ControlRuleId value must be a string")
        if not self.value:
            raise ValueError("ControlRuleId cannot be empty")
        # Allow alphanumeric, underscore, hyphen
        if not all(c.isalnum() or c in ("_", "-") for c in self.value):
            raise ValueError("ControlRuleId can only contain alphanumeric, underscore, and hyphen")

    def __eq__(self, other: object) -> bool:
        """Compare ControlRuleIds."""
        if not isinstance(other, ControlRuleId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.value)

    def __repr__(self) -> str:
        """String representation."""
        return f"ControlRuleId({self.value!r})"


@dataclass(kw_only=True)
class ControlRule(Entity[ControlRuleId]):
    """Control rule that applies effects based on conditions.

    A ControlRule evaluates a formula (condition) and applies an effect when true.

    RULES:
    - ControlRule is an entity (has identity, lifecycle)
    - Condition is a formula string (evaluated by formula engine)
    - Effect defines what happens when condition is true
    - Rules can be enabled/disabled

    Examples:
        # Set total to 100 when field1 > 50
        ControlRule(
            id=ControlRuleId("rule_set_total"),
            name_key=TranslationKey("rule.set_total"),
            condition="field1 > 50",
            effect=ControlEffect(
                control_type=ControlType.VALUE_SET,
                target_field_id=FieldDefinitionId("total"),
                value=100
            ),
            enabled=True
        )

        # Hide optional_field when required_field is empty
        ControlRule(
            id=ControlRuleId("rule_hide_optional"),
            name_key=TranslationKey("rule.hide_optional"),
            condition="required_field == null",
            effect=ControlEffect(
                control_type=ControlType.VISIBILITY,
                target_field_id=FieldDefinitionId("optional_field"),
                value=False
            )
        )
    """

    name_key: TranslationKey  # Display name translation key
    condition: str  # Formula that determines when effect applies
    effect: ControlEffect  # Effect to apply when condition is true
    enabled: bool = True  # Whether rule is active
    description_key: Optional[TranslationKey] = None  # Optional description
    priority: int = 0  # Execution priority (higher = earlier, for conflict resolution)

    def __post_init__(self) -> None:
        """Validate control rule."""
        if not isinstance(self.name_key, TranslationKey):
            raise TypeError("name_key must be a TranslationKey")
        if not isinstance(self.condition, str):
            raise TypeError("condition must be a string (formula)")
        if not self.condition:
            raise ValueError("condition cannot be empty")
        if not isinstance(self.effect, ControlEffect):
            raise TypeError("effect must be a ControlEffect")
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")
        if self.description_key is not None and not isinstance(
            self.description_key, TranslationKey
        ):
            raise TypeError("description_key must be a TranslationKey or None")
        if not isinstance(self.priority, int):
            raise TypeError("priority must be an int")

    def enable(self) -> None:
        """Enable this control rule."""
        self.enabled = True
        self._touch()

    def disable(self) -> None:
        """Disable this control rule."""
        self.enabled = False
        self._touch()

    @property
    def is_enabled(self) -> bool:
        """Check if rule is enabled.

        Returns:
            True if rule is enabled
        """
        return self.enabled

    @property
    def is_disabled(self) -> bool:
        """Check if rule is disabled.

        Returns:
            True if rule is disabled
        """
        return not self.enabled

    @property
    def target_field_id(self):
        """Get the target field ID from the effect.

        Returns:
            FieldDefinitionId that this rule affects
        """
        return self.effect.target_field_id

    @property
    def control_type(self):
        """Get the control type from the effect.

        Returns:
            ControlType of this rule's effect
        """
        return self.effect.control_type

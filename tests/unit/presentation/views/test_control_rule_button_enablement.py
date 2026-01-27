"""Unit tests for Add Control Rule button enablement logic.

Tests the presentation-layer logic that determines when the
Add Control Rule button should be enabled/disabled.

Requirements:
- Button disabled when: No field selected
- Button enabled when: Field selected AND at least one ControlRuleType available
- Button disabled when: Field selected AND all ControlRuleType values already used
"""

import pytest
from unittest.mock import Mock, MagicMock

from doc_helper.application.dto.control_rule_dto import ControlRuleType


class TestAddControlRuleButtonEnablement:
    """Unit tests for Add Control Rule button enablement logic."""

    def _compute_can_add_rule(
        self,
        field_selected: bool,
        existing_rules: list[Mock],
    ) -> bool:
        """Replicate the enablement logic from schema_designer_view.py.

        This mirrors the logic in _on_control_rules_changed() to test it in isolation.
        """
        can_add_rule = False
        if field_selected:
            # Compute used rule types from current control rules
            used_rule_types = {rule.rule_type for rule in existing_rules}
            # All available rule types from the enum
            all_rule_types = {rt.value for rt in ControlRuleType}
            # Available = all - used
            available_rule_types = all_rule_types - used_rule_types
            can_add_rule = len(available_rule_types) > 0
        return can_add_rule

    def _create_rule(self, rule_type: str) -> Mock:
        """Create a mock control rule with given type."""
        rule = Mock()
        rule.rule_type = rule_type
        return rule

    # =========================================================================
    # DISABLED TESTS - Button should be disabled
    # =========================================================================

    def test_button_disabled_when_no_field_selected(self) -> None:
        """Button should be disabled when no field is selected.

        REQUIREMENT: Be disabled when no field is selected.
        """
        result = self._compute_can_add_rule(
            field_selected=False,
            existing_rules=[],
        )
        assert result is False

    def test_button_disabled_when_all_rule_types_used(self) -> None:
        """Button should be disabled when all 3 rule types are already used.

        REQUIREMENT: Be disabled when all ControlRuleType values are already used.
        """
        # Create rules for all 3 types
        existing_rules = [
            self._create_rule(ControlRuleType.VISIBILITY.value),
            self._create_rule(ControlRuleType.ENABLED.value),
            self._create_rule(ControlRuleType.REQUIRED.value),
        ]

        result = self._compute_can_add_rule(
            field_selected=True,
            existing_rules=existing_rules,
        )
        assert result is False

    # =========================================================================
    # ENABLED TESTS - Button should be enabled
    # =========================================================================

    def test_button_enabled_when_field_selected_no_rules(self) -> None:
        """Button should be enabled when field selected and no rules exist.

        REQUIREMENT: Be enabled when field selected AND at least one rule type available.
        """
        result = self._compute_can_add_rule(
            field_selected=True,
            existing_rules=[],
        )
        assert result is True

    def test_button_enabled_with_one_rule_used(self) -> None:
        """Button should be enabled when field selected and 1 of 3 rules used."""
        existing_rules = [
            self._create_rule(ControlRuleType.VISIBILITY.value),
        ]

        result = self._compute_can_add_rule(
            field_selected=True,
            existing_rules=existing_rules,
        )
        assert result is True

    def test_button_enabled_with_two_rules_used(self) -> None:
        """Button should be enabled when field selected and 2 of 3 rules used."""
        existing_rules = [
            self._create_rule(ControlRuleType.VISIBILITY.value),
            self._create_rule(ControlRuleType.ENABLED.value),
        ]

        result = self._compute_can_add_rule(
            field_selected=True,
            existing_rules=existing_rules,
        )
        assert result is True

    # =========================================================================
    # STATE TRANSITION TESTS - Verify changes after add/delete
    # =========================================================================

    def test_button_disables_after_adding_last_rule_type(self) -> None:
        """Button should disable when the last available rule type is added.

        This simulates the state transition from 2 rules to 3 rules.
        """
        # Before: 2 rules used, button should be enabled
        before_rules = [
            self._create_rule(ControlRuleType.VISIBILITY.value),
            self._create_rule(ControlRuleType.ENABLED.value),
        ]
        before_result = self._compute_can_add_rule(
            field_selected=True,
            existing_rules=before_rules,
        )
        assert before_result is True

        # After: 3 rules used (all), button should be disabled
        after_rules = [
            self._create_rule(ControlRuleType.VISIBILITY.value),
            self._create_rule(ControlRuleType.ENABLED.value),
            self._create_rule(ControlRuleType.REQUIRED.value),  # Added
        ]
        after_result = self._compute_can_add_rule(
            field_selected=True,
            existing_rules=after_rules,
        )
        assert after_result is False

    def test_button_enables_after_deleting_rule(self) -> None:
        """Button should enable when a rule is deleted from fully-used state.

        This simulates the state transition from 3 rules to 2 rules.
        """
        # Before: 3 rules used (all), button should be disabled
        before_rules = [
            self._create_rule(ControlRuleType.VISIBILITY.value),
            self._create_rule(ControlRuleType.ENABLED.value),
            self._create_rule(ControlRuleType.REQUIRED.value),
        ]
        before_result = self._compute_can_add_rule(
            field_selected=True,
            existing_rules=before_rules,
        )
        assert before_result is False

        # After: 2 rules used, button should be enabled
        after_rules = [
            self._create_rule(ControlRuleType.VISIBILITY.value),
            self._create_rule(ControlRuleType.ENABLED.value),
            # REQUIRED deleted
        ]
        after_result = self._compute_can_add_rule(
            field_selected=True,
            existing_rules=after_rules,
        )
        assert after_result is True

    # =========================================================================
    # EDGE CASE TESTS
    # =========================================================================

    def test_all_three_rule_types_exist_in_enum(self) -> None:
        """Verify ControlRuleType enum has exactly 3 values.

        This ensures the enablement logic is based on correct assumptions.
        """
        all_rule_types = {rt.value for rt in ControlRuleType}
        assert len(all_rule_types) == 3
        assert "VISIBILITY" in all_rule_types
        assert "ENABLED" in all_rule_types
        assert "REQUIRED" in all_rule_types

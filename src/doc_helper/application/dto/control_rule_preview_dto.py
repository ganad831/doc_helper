"""Control Rule Preview DTOs (Phase F-9).

DTOs for control rule preview functionality in Schema Designer.
Preview is UI-only, in-memory, with no persistence.

PHASE F-9 CONSTRAINTS:
- Preview values are in-memory only
- Control rules are in-memory only
- No persistence
- No schema mutation
- UI visual effects only
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from doc_helper.application.dto.control_rule_dto import (
    ControlRuleStatus,
    ControlRuleType,
)


class PreviewEffectType(Enum):
    """Type of visual effect to apply in preview.

    VISIBILITY: Show/hide field row in UI
    ENABLED: Enable/disable field row editor controls
    REQUIRED: Show required indicator badge (visual only)
    """

    VISIBILITY = "VISIBILITY"
    ENABLED = "ENABLED"
    REQUIRED = "REQUIRED"


@dataclass(frozen=True)
class ControlRulePreviewInputDTO:
    """Input for a control rule preview.

    Attributes:
        rule_type: Type of control rule (VISIBILITY, ENABLED, REQUIRED)
        target_field_id: ID of the field this rule applies to
        formula_text: Boolean formula expression
    """

    rule_type: ControlRuleType
    target_field_id: str
    formula_text: str


@dataclass(frozen=True)
class ControlRulePreviewResultDTO:
    """Result of control rule preview evaluation.

    Combines validation status and execution result.

    Attributes:
        rule_input: The input rule that was evaluated
        validation_status: ALLOWED, BLOCKED, or CLEARED from F-8 governance
        is_allowed: True if rule passed F-8 validation (boolean formula)
        is_blocked: True if rule failed F-8 validation
        block_reason: Reason for blocking (if blocked)
        execution_result: Boolean result of formula execution (if allowed and executed)
        execution_error: Error message if execution failed
    """

    rule_input: ControlRulePreviewInputDTO
    validation_status: ControlRuleStatus
    is_allowed: bool
    is_blocked: bool
    block_reason: Optional[str]
    execution_result: Optional[bool]
    execution_error: Optional[str]

    @property
    def is_executed(self) -> bool:
        """Check if formula was executed successfully."""
        return self.is_allowed and self.execution_result is not None

    @property
    def effect_value(self) -> Optional[bool]:
        """Get the effect value to apply.

        Returns the execution result if allowed and executed,
        None otherwise.
        """
        if self.is_executed:
            return self.execution_result
        return None


@dataclass(frozen=True)
class FieldPreviewStateDTO:
    """Preview state to apply to a field in the UI.

    Represents the visual effects to apply based on control rules.

    Attributes:
        field_id: ID of the field
        is_visible: Whether field should be visible (VISIBILITY rule effect)
        is_enabled: Whether field should be enabled (ENABLED rule effect)
        show_required_indicator: Whether to show required badge (REQUIRED rule effect)
        applied_rules: List of rule types that were applied to this field
        blocked_rules: List of rules that were blocked (with reasons)
    """

    field_id: str
    is_visible: bool = True
    is_enabled: bool = True
    show_required_indicator: bool = False
    applied_rules: tuple[ControlRuleType, ...] = ()
    blocked_rules: tuple[tuple[ControlRuleType, str], ...] = ()


@dataclass(frozen=True)
class PreviewModeStateDTO:
    """State of preview mode in Schema Designer.

    Tracks all in-memory preview data.

    Attributes:
        is_enabled: Whether preview mode is ON
        entity_id: Entity being previewed (or None if none selected)
        field_values: Temporary field values entered by user
        control_rules: Control rules configured for preview
        field_states: Computed visual states for fields
    """

    is_enabled: bool = False
    entity_id: Optional[str] = None
    field_values: tuple[tuple[str, Any], ...] = ()
    control_rules: tuple[ControlRulePreviewInputDTO, ...] = ()
    field_states: tuple[FieldPreviewStateDTO, ...] = ()

    def get_field_value(self, field_id: str) -> Any:
        """Get preview value for a field."""
        for fid, value in self.field_values:
            if fid == field_id:
                return value
        return None

    def get_field_state(self, field_id: str) -> Optional[FieldPreviewStateDTO]:
        """Get preview state for a field."""
        for state in self.field_states:
            if state.field_id == field_id:
                return state
        return None

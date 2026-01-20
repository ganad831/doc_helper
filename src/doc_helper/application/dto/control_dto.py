"""Control DTOs for UI display.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ControlEffectDTO:
    """UI-facing control effect data for display.

    Represents the effect of a control rule on a field.
    """

    control_type: str  # "value_set", "visibility", "enable"
    target_field_id: str  # Field ID as string
    value: Any  # Value to set or bool for visibility/enable


@dataclass(frozen=True)
class EvaluationResultDTO:
    """UI-facing control evaluation result for display.

    Contains the effects that should be applied based on rule evaluation.
    """

    effects: tuple[ControlEffectDTO, ...]  # Effects to apply
    errors: tuple[str, ...]  # Evaluation errors (non-fatal)

    @property
    def has_effects(self) -> bool:
        """Check if any effects should be applied.

        Returns:
            True if there are effects to apply
        """
        return len(self.effects) > 0

    @property
    def has_errors(self) -> bool:
        """Check if there were evaluation errors.

        Returns:
            True if there were errors
        """
        return len(self.errors) > 0

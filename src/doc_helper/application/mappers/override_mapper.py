"""Override mapper - Domain → DTO conversion.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- ONE-WAY mapping: Domain → DTO only
- NO to_domain() or from_dto() methods
"""

from typing import Any

from doc_helper.application.dto import OverrideDTO
from doc_helper.domain.override.override_entity import Override
from doc_helper.domain.override.override_state import OverrideState


def _format_value(value: Any) -> str:
    """Format any value for display.

    Args:
        value: Raw value

    Returns:
        String representation for display
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


class OverrideMapper:
    """Maps Override domain entity to OverrideDTO for UI display.

    This mapper is ONE-WAY: Domain → DTO only.
    There is NO reverse mapping (to_domain, from_dto).
    Undo functionality uses UndoState DTOs, not reverse mapping.
    """

    @staticmethod
    def to_dto(override: Override, field_label: str) -> OverrideDTO:
        """Convert Override domain entity to OverrideDTO.

        Args:
            override: Override domain entity
            field_label: Human-readable field label (pre-translated)

        Returns:
            OverrideDTO for UI display
        """
        return OverrideDTO(
            id=str(override.id.value),
            field_id=str(override.field_id.value),
            field_label=field_label,
            system_value=_format_value(override.original_value),
            report_value=_format_value(override.override_value),
            state=override.state.value,
            can_accept=override.state.can_accept(),
            can_reject=override.state.is_pending,
        )

    # ❌ FORBIDDEN: No to_domain() method
    # ❌ FORBIDDEN: No from_dto() method
    # ❌ FORBIDDEN: No reverse mapping
    # Reason: Mappers are one-way only (unified_upgrade_plan.md H3)
    # Undo uses UndoOverrideState DTOs in application/undo/, NOT reverse mapping

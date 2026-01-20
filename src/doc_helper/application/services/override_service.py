"""Concrete override service implementing IOverrideService protocol.

STUB IMPLEMENTATION for Phase 7 DI container wiring.
Full implementation deferred to override UI integration milestone.

RULES (unified_upgrade_plan_FINAL.md U6 Phase 7):
- Implements IOverrideService protocol for OverrideUndoService
- Currently returns stub values - override functionality not yet exposed in ViewModel
- Will be fully implemented when override UI is added

NOTE: T3 temporal test was skipped pending this integration.
"""

from typing import Any

from doc_helper.domain.common.result import Failure, Result, Success


class OverrideService:
    """Stub override service for Phase 7 DI wiring.

    Implements IOverrideService protocol required by OverrideUndoService.
    Returns stub values until override functionality is fully integrated.

    Example:
        override_service = OverrideService()

        # Get override state (stub)
        result = override_service.get_override_state("project-123", "override-456")
        # Returns Failure("Override functionality not yet integrated")
    """

    def __init__(self) -> None:
        """Initialize OverrideService stub."""
        pass

    def get_override_state(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[str, str]:
        """Get current override state (STUB).

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            Failure indicating override functionality not yet integrated
        """
        return Failure("Override functionality not yet integrated in ViewModel")

    def get_override_field_id(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[str, str]:
        """Get field ID associated with override (STUB).

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            Failure indicating override functionality not yet integrated
        """
        return Failure("Override functionality not yet integrated in ViewModel")

    def get_override_value(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[Any, str]:
        """Get override's proposed value (STUB).

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            Failure indicating override functionality not yet integrated
        """
        return Failure("Override functionality not yet integrated in ViewModel")

    def accept_override(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        """Accept an override (STUB).

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            False (not yet implemented)
        """
        return False

    def reject_override(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        """Reject an override (STUB).

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            False (not yet implemented)
        """
        return False

    def restore_override_to_pending(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        """Restore an override to pending state (STUB).

        Args:
            project_id: Project identifier
            override_id: Override identifier

        Returns:
            False (not yet implemented)
        """
        return False

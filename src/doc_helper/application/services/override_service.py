"""Concrete override service implementing IOverrideService protocol.

PARTIAL IMPLEMENTATION:
- Phase 7 (U6): Basic methods for undo integration (stubs)
- Phase 8 (U8): Added cleanup_synced_overrides for document generation
- Full implementation deferred to override UI integration milestone

RULES (unified_upgrade_plan_FINAL.md):
- U6: Implements IOverrideService protocol for OverrideUndoService
- U8: Cleanup SYNCED (non-formula) overrides after document generation
- Preserves SYNCED_FORMULA overrides across generations

NOTE: Most methods still stubs until override UI is integrated.
"""

from typing import Any

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.override.repositories import IOverrideRepository
from doc_helper.domain.project.project_ids import ProjectId


class OverrideService:
    """Override service for managing override lifecycle and cleanup.

    PARTIAL IMPLEMENTATION:
    - cleanup_synced_overrides: Full implementation (U8)
    - Other methods: Stubs (pending override UI integration)

    Implements IOverrideService protocol required by OverrideUndoService.

    Dependencies:
        - IOverrideRepository: For persisting and querying override entities

    Example:
        override_repo = SqliteOverrideRepository(...)
        override_service = OverrideService(override_repo)

        # U8: Cleanup after document generation
        result = override_service.cleanup_synced_overrides(project_id)
        if isinstance(result, Success):
            print(f"Cleaned up {result.value} overrides")
    """

    def __init__(self, override_repository: IOverrideRepository) -> None:
        """Initialize OverrideService.

        Args:
            override_repository: Repository for override persistence
        """
        self._override_repository = override_repository

    def cleanup_synced_overrides(self, project_id: ProjectId) -> Result[int, str]:
        """Clean up SYNCED (non-formula) overrides after document generation.

        U8 Behavior: After successful document generation:
        - Delete overrides in SYNCED state (should_cleanup_after_generation = True)
        - Preserve overrides in SYNCED_FORMULA state

        Args:
            project_id: Project identifier

        Returns:
            Success(count) with number of overrides cleaned up
            Failure(error) if cleanup failed
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId instance")

        # Get all overrides for this project
        overrides_result = self._override_repository.list_by_project(project_id)
        if not overrides_result.is_success:
            return Failure(f"Failed to list overrides: {overrides_result.error}")

        overrides = overrides_result.value
        cleanup_count = 0

        # Filter overrides that should be cleaned up (SYNCED state)
        for override in overrides:
            if override.should_cleanup_after_generation:
                # Delete this override
                delete_result = self._override_repository.delete(override.id)
                if delete_result.is_success:
                    cleanup_count += 1
                # Continue even if delete fails - try to clean up as many as possible

        return Success(cleanup_count)

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

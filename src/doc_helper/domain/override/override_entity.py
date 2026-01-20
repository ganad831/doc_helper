"""Override entity with state machine."""

from dataclasses import dataclass
from typing import Any, Optional

from doc_helper.domain.common.entity import Entity
from doc_helper.domain.override.override_ids import OverrideId
from doc_helper.domain.override.override_state import OverrideState
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


@dataclass(kw_only=True)
class Override(Entity[OverrideId]):
    """Override entity tracking user overrides of computed/controlled values.

    Override represents a user's decision to override a computed or controlled
    field value. It tracks the override lifecycle through state transitions.

    State Machine (U8 - with cleanup):
        PENDING → ACCEPTED → SYNCED → cleanup (non-formula)
             ↓                  ↓
          INVALID         SYNCED_FORMULA (preserved)

    RULES:
    - Override is an entity (has identity, lifecycle)
    - State transitions are enforced (can't skip states)
    - Tracks both the override value and reason
    - Links to project and field
    - SYNCED overrides cleaned up after document generation
    - SYNCED_FORMULA overrides preserved across generations

    Example:
        from uuid import uuid4

        # User overrides computed value
        override = Override(
            id=OverrideId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            original_value=1500,
            reason="Manual adjustment for special case",
            state=OverrideState.PENDING,
            conflict_type="formula"  # Indicates formula conflict
        )

        # User accepts override
        override.accept()  # PENDING → ACCEPTED

        # System syncs override (formula)
        override.mark_synced_formula()  # ACCEPTED → SYNCED_FORMULA
        # Will be preserved after document generation

        # Check state
        assert override.is_accepted
        assert override.state == OverrideState.SYNCED_FORMULA
    """

    project_id: ProjectId  # Project containing the field
    field_id: FieldDefinitionId  # Field being overridden
    override_value: Any  # Value set by user
    original_value: Any  # Original computed/controlled value
    state: OverrideState = OverrideState.PENDING  # Current state
    reason: Optional[str] = None  # Optional reason for override
    conflict_type: Optional[str] = None  # Type of conflict (formula/control)

    def __post_init__(self) -> None:
        """Validate override."""
        if not isinstance(self.project_id, ProjectId):
            raise TypeError("project_id must be a ProjectId")
        if not isinstance(self.field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")
        if not isinstance(self.state, OverrideState):
            raise TypeError("state must be an OverrideState")
        if self.reason is not None and not isinstance(self.reason, str):
            raise TypeError("reason must be a string or None")
        if self.conflict_type is not None and not isinstance(self.conflict_type, str):
            raise TypeError("conflict_type must be a string or None")

    def accept(self) -> None:
        """Accept the override (PENDING → ACCEPTED).

        Raises:
            ValueError: If override is not in PENDING state
        """
        if not self.state.can_accept():
            raise ValueError(
                f"Cannot accept override in state {self.state.value}. "
                f"Override must be PENDING."
            )
        self.state = OverrideState.ACCEPTED
        self._touch()

    def mark_invalid(self) -> None:
        """Mark override as invalid (PENDING → INVALID).

        Called when validation fails for the override value.

        Raises:
            ValueError: If override is not in PENDING state
        """
        if not self.state.can_mark_invalid():
            raise ValueError(
                f"Cannot mark override invalid in state {self.state.value}. "
                f"Override must be PENDING."
            )
        self.state = OverrideState.INVALID
        self._touch()

    def mark_synced(self) -> None:
        """Mark override as synced (ACCEPTED → SYNCED).

        For non-formula overrides. These will be cleaned up after document generation.

        Raises:
            ValueError: If override is not in ACCEPTED state
        """
        if not self.state.can_sync():
            raise ValueError(
                f"Cannot sync override in state {self.state.value}. "
                f"Override must be ACCEPTED."
            )
        self.state = OverrideState.SYNCED
        self._touch()

    def mark_synced_formula(self) -> None:
        """Mark override as synced with formula value (ACCEPTED → SYNCED_FORMULA).

        For formula overrides. These are preserved across document generations.

        Raises:
            ValueError: If override is not in ACCEPTED state
        """
        if not self.state.can_sync_formula():
            raise ValueError(
                f"Cannot sync formula override in state {self.state.value}. "
                f"Override must be ACCEPTED."
            )
        self.state = OverrideState.SYNCED_FORMULA
        self._touch()

    def update_reason(self, reason: Optional[str]) -> None:
        """Update the reason for this override.

        Args:
            reason: New reason or None to clear

        Raises:
            TypeError: If reason is not string or None
        """
        if reason is not None and not isinstance(reason, str):
            raise TypeError("reason must be a string or None")
        self.reason = reason
        self._touch()

    def mark_conflict(self, conflict_type: str) -> None:
        """Mark this override as having a conflict.

        Args:
            conflict_type: Type of conflict (e.g., "formula", "control")

        Raises:
            TypeError: If conflict_type is not a string
            ValueError: If conflict_type is empty
        """
        if not isinstance(conflict_type, str):
            raise TypeError("conflict_type must be a string")
        if not conflict_type.strip():
            raise ValueError("conflict_type cannot be empty")
        self.conflict_type = conflict_type
        self._touch()

    def clear_conflict(self) -> None:
        """Clear the conflict marker."""
        self.conflict_type = None
        self._touch()

    @property
    def is_pending(self) -> bool:
        """Check if override is pending.

        Returns:
            True if state is PENDING
        """
        return self.state.is_pending

    @property
    def is_accepted(self) -> bool:
        """Check if override is accepted.

        Returns:
            True if state is ACCEPTED
        """
        return self.state.is_accepted

    @property
    def is_invalid(self) -> bool:
        """Check if override is invalid.

        Returns:
            True if state is INVALID
        """
        return self.state.is_invalid

    @property
    def is_synced(self) -> bool:
        """Check if override is synced (non-formula).

        Returns:
            True if state is SYNCED
        """
        return self.state.is_synced

    @property
    def is_synced_formula(self) -> bool:
        """Check if override is synced with formula value.

        Returns:
            True if state is SYNCED_FORMULA
        """
        return self.state.is_synced_formula

    @property
    def should_cleanup_after_generation(self) -> bool:
        """Check if override should be cleaned up after document generation.

        Returns:
            True if SYNCED (non-formula overrides are deleted)
            False if SYNCED_FORMULA (formula overrides preserved)
        """
        return self.state.should_cleanup_after_generation()

    @property
    def has_conflict(self) -> bool:
        """Check if override has a conflict.

        Returns:
            True if conflict_type is set
        """
        return self.conflict_type is not None

    @property
    def has_reason(self) -> bool:
        """Check if override has a reason.

        Returns:
            True if reason is set
        """
        return self.reason is not None

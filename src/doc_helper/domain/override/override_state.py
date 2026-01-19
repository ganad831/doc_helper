"""Override state enumeration."""

from enum import Enum


class OverrideState(str, Enum):
    """States in the override lifecycle.

    The override state machine tracks the lifecycle of a user override:

    PENDING → ACCEPTED → SYNCED
         ↓
      (reject)

    States:
    - PENDING: Override created, awaiting user confirmation
    - ACCEPTED: User confirmed the override, will be applied
    - SYNCED: Override synchronized with computed/controlled value

    Transitions:
    - accept(): PENDING → ACCEPTED
    - sync(): ACCEPTED → SYNCED
    - reject(): PENDING → (removed)

    Example:
        # User overrides computed value
        override = Override(state=OverrideState.PENDING, ...)

        # User accepts the override
        override.accept()  # PENDING → ACCEPTED

        # System synchronizes
        override.mark_synced()  # ACCEPTED → SYNCED
    """

    PENDING = "pending"  # Override created, awaiting confirmation
    ACCEPTED = "accepted"  # Override accepted by user
    SYNCED = "synced"  # Override synced with computed value

    @property
    def is_pending(self) -> bool:
        """Check if override is pending.

        Returns:
            True if state is PENDING
        """
        return self == OverrideState.PENDING

    @property
    def is_accepted(self) -> bool:
        """Check if override is accepted.

        Returns:
            True if state is ACCEPTED
        """
        return self == OverrideState.ACCEPTED

    @property
    def is_synced(self) -> bool:
        """Check if override is synced.

        Returns:
            True if state is SYNCED
        """
        return self == OverrideState.SYNCED

    def can_accept(self) -> bool:
        """Check if override can be accepted.

        Returns:
            True if state is PENDING
        """
        return self == OverrideState.PENDING

    def can_sync(self) -> bool:
        """Check if override can be synced.

        Returns:
            True if state is ACCEPTED
        """
        return self == OverrideState.ACCEPTED

    def can_reject(self) -> bool:
        """Check if override can be rejected.

        Returns:
            True if state is PENDING
        """
        return self == OverrideState.PENDING

"""Override state enumeration."""

from enum import Enum


class OverrideState(str, Enum):
    """States in the override lifecycle.

    The override state machine tracks the lifecycle of a user override:

    PENDING → ACCEPTED → SYNCED → cleanup (non-formula)
         ↓                  ↓
      (reject)            SYNCED_FORMULA (preserved)
         ↓
      INVALID

    States:
    - PENDING: Override created, awaiting user confirmation
    - ACCEPTED: User confirmed the override, will be applied
    - INVALID: Override failed validation (cannot be accepted)
    - SYNCED: Override synchronized with computed value (non-formula)
    - SYNCED_FORMULA: Override synchronized with formula value (preserved)

    Transitions:
    - accept(): PENDING → ACCEPTED
    - mark_invalid(): PENDING → INVALID
    - sync(): ACCEPTED → SYNCED
    - sync_formula(): ACCEPTED → SYNCED_FORMULA
    - reject(): PENDING → (removed)

    Cleanup Rules (U8):
    - SYNCED (non-formula) overrides: deleted after document generation
    - SYNCED_FORMULA overrides: preserved across document generations

    Example:
        # User overrides computed value
        override = Override(state=OverrideState.PENDING, ...)

        # User accepts the override
        override.accept()  # PENDING → ACCEPTED

        # System synchronizes (non-formula)
        override.mark_synced()  # ACCEPTED → SYNCED
        # Will be cleaned up after document generation

        # System synchronizes (formula)
        override.mark_synced_formula()  # ACCEPTED → SYNCED_FORMULA
        # Preserved across document generations
    """

    PENDING = "pending"  # Override created, awaiting confirmation
    ACCEPTED = "accepted"  # Override accepted by user
    INVALID = "invalid"  # Override failed validation
    SYNCED = "synced"  # Override synced with computed value (non-formula)
    SYNCED_FORMULA = "synced_formula"  # Override synced with formula value

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
    def is_invalid(self) -> bool:
        """Check if override is invalid.

        Returns:
            True if state is INVALID
        """
        return self == OverrideState.INVALID

    @property
    def is_synced(self) -> bool:
        """Check if override is synced (non-formula).

        Returns:
            True if state is SYNCED
        """
        return self == OverrideState.SYNCED

    @property
    def is_synced_formula(self) -> bool:
        """Check if override is synced with formula value.

        Returns:
            True if state is SYNCED_FORMULA
        """
        return self == OverrideState.SYNCED_FORMULA

    def can_accept(self) -> bool:
        """Check if override can be accepted.

        Returns:
            True if state is PENDING
        """
        return self == OverrideState.PENDING

    def can_mark_invalid(self) -> bool:
        """Check if override can be marked invalid.

        Returns:
            True if state is PENDING
        """
        return self == OverrideState.PENDING

    def can_sync(self) -> bool:
        """Check if override can be synced (non-formula).

        Returns:
            True if state is ACCEPTED
        """
        return self == OverrideState.ACCEPTED

    def can_sync_formula(self) -> bool:
        """Check if override can be synced with formula value.

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

    def should_cleanup_after_generation(self) -> bool:
        """Check if override should be cleaned up after document generation.

        Returns:
            True if state is SYNCED (non-formula overrides are deleted)
            False if state is SYNCED_FORMULA (formula overrides preserved)
        """
        return self == OverrideState.SYNCED

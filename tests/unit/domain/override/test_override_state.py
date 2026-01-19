"""Tests for override state."""

import pytest

from doc_helper.domain.override.override_state import OverrideState


class TestOverrideState:
    """Tests for OverrideState enum."""

    def test_pending_state(self) -> None:
        """OverrideState.PENDING should exist."""
        assert OverrideState.PENDING == "pending"

    def test_accepted_state(self) -> None:
        """OverrideState.ACCEPTED should exist."""
        assert OverrideState.ACCEPTED == "accepted"

    def test_synced_state(self) -> None:
        """OverrideState.SYNCED should exist."""
        assert OverrideState.SYNCED == "synced"

    def test_is_pending(self) -> None:
        """is_pending should return True only for PENDING."""
        assert OverrideState.PENDING.is_pending is True
        assert OverrideState.ACCEPTED.is_pending is False
        assert OverrideState.SYNCED.is_pending is False

    def test_is_accepted(self) -> None:
        """is_accepted should return True only for ACCEPTED."""
        assert OverrideState.PENDING.is_accepted is False
        assert OverrideState.ACCEPTED.is_accepted is True
        assert OverrideState.SYNCED.is_accepted is False

    def test_is_synced(self) -> None:
        """is_synced should return True only for SYNCED."""
        assert OverrideState.PENDING.is_synced is False
        assert OverrideState.ACCEPTED.is_synced is False
        assert OverrideState.SYNCED.is_synced is True

    def test_can_accept(self) -> None:
        """can_accept should return True only for PENDING."""
        assert OverrideState.PENDING.can_accept() is True
        assert OverrideState.ACCEPTED.can_accept() is False
        assert OverrideState.SYNCED.can_accept() is False

    def test_can_sync(self) -> None:
        """can_sync should return True only for ACCEPTED."""
        assert OverrideState.PENDING.can_sync() is False
        assert OverrideState.ACCEPTED.can_sync() is True
        assert OverrideState.SYNCED.can_sync() is False

    def test_can_reject(self) -> None:
        """can_reject should return True only for PENDING."""
        assert OverrideState.PENDING.can_reject() is True
        assert OverrideState.ACCEPTED.can_reject() is False
        assert OverrideState.SYNCED.can_reject() is False

"""Unit tests for field history value objects.

ADR-027: Field History Storage
Tests for FieldHistoryEntry and ChangeSource.
"""

import pytest
from datetime import datetime
from uuid import UUID

from doc_helper.domain.project.field_history import (
    ChangeSource,
    FieldHistoryEntry,
)


class TestChangeSource:
    """Test ChangeSource enum."""

    def test_all_change_sources_exist(self):
        """Test that all expected change sources are defined."""
        assert ChangeSource.USER_EDIT.value == "USER_EDIT"
        assert ChangeSource.FORMULA_RECOMPUTATION.value == "FORMULA_RECOMPUTATION"
        assert ChangeSource.OVERRIDE_ACCEPTANCE.value == "OVERRIDE_ACCEPTANCE"
        assert ChangeSource.CONTROL_EFFECT.value == "CONTROL_EFFECT"
        assert ChangeSource.UNDO_OPERATION.value == "UNDO_OPERATION"
        assert ChangeSource.REDO_OPERATION.value == "REDO_OPERATION"

    def test_change_source_from_string(self):
        """Test creating ChangeSource from string value."""
        source = ChangeSource("USER_EDIT")
        assert source == ChangeSource.USER_EDIT

    def test_change_source_equality(self):
        """Test ChangeSource enum equality."""
        source1 = ChangeSource.USER_EDIT
        source2 = ChangeSource.USER_EDIT
        source3 = ChangeSource.FORMULA_RECOMPUTATION

        assert source1 == source2
        assert source1 != source3


class TestFieldHistoryEntry:
    """Test FieldHistoryEntry value object."""

    def test_create_with_required_fields(self):
        """Test creating entry with all required fields."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
        )

        assert entry.project_id == "proj-123"
        assert entry.field_id == "field-456"
        assert entry.previous_value == "100"
        assert entry.new_value == "150"
        assert entry.change_source == ChangeSource.USER_EDIT
        assert entry.user_id is None
        assert isinstance(entry.history_id, UUID)
        assert isinstance(entry.timestamp, datetime)

    def test_create_with_user_id(self):
        """Test creating entry with optional user_id."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-789",
        )

        assert entry.user_id == "user-789"

    def test_create_generates_unique_ids(self):
        """Test that each created entry has a unique ID."""
        entry1 = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
        )

        entry2 = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="150",
            new_value="200",
            change_source=ChangeSource.USER_EDIT,
        )

        assert entry1.history_id != entry2.history_id

    def test_create_generates_current_timestamp(self):
        """Test that created entry has a recent timestamp."""
        before = datetime.utcnow()
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
        )
        after = datetime.utcnow()

        assert before <= entry.timestamp <= after

    def test_immutability(self):
        """Test that FieldHistoryEntry is immutable (frozen dataclass)."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
        )

        with pytest.raises(AttributeError):
            entry.new_value = "200"  # type: ignore

        with pytest.raises(AttributeError):
            entry.change_source = ChangeSource.FORMULA_RECOMPUTATION  # type: ignore

    def test_is_user_initiated_for_user_edit(self):
        """Test is_user_initiated returns True for USER_EDIT."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
        )

        assert entry.is_user_initiated() is True
        assert entry.is_system_initiated() is False

    def test_is_user_initiated_for_undo_operation(self):
        """Test is_user_initiated returns True for UNDO_OPERATION."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="150",
            new_value="100",
            change_source=ChangeSource.UNDO_OPERATION,
        )

        assert entry.is_user_initiated() is True
        assert entry.is_system_initiated() is False

    def test_is_user_initiated_for_redo_operation(self):
        """Test is_user_initiated returns True for REDO_OPERATION."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.REDO_OPERATION,
        )

        assert entry.is_user_initiated() is True
        assert entry.is_system_initiated() is False

    def test_is_system_initiated_for_formula_recomputation(self):
        """Test is_system_initiated returns True for FORMULA_RECOMPUTATION."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.FORMULA_RECOMPUTATION,
        )

        assert entry.is_system_initiated() is True
        assert entry.is_user_initiated() is False

    def test_is_system_initiated_for_override_acceptance(self):
        """Test is_system_initiated returns True for OVERRIDE_ACCEPTANCE."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.OVERRIDE_ACCEPTANCE,
        )

        assert entry.is_system_initiated() is True
        assert entry.is_user_initiated() is False

    def test_is_system_initiated_for_control_effect(self):
        """Test is_system_initiated returns True for CONTROL_EFFECT."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.CONTROL_EFFECT,
        )

        assert entry.is_system_initiated() is True
        assert entry.is_user_initiated() is False

    def test_equality_based_on_all_fields(self):
        """Test that two entries with same data are equal."""
        from uuid import UUID as UUID_class
        from datetime import datetime as datetime_class

        # Create two entries with identical data
        history_id = UUID_class("12345678-1234-5678-1234-567812345678")
        timestamp = datetime_class(2026, 1, 21, 10, 30, 0)

        entry1 = FieldHistoryEntry(
            history_id=history_id,
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-789",
            timestamp=timestamp,
        )

        entry2 = FieldHistoryEntry(
            history_id=history_id,
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-789",
            timestamp=timestamp,
        )

        assert entry1 == entry2

    def test_inequality_for_different_values(self):
        """Test that entries with different values are not equal."""
        from uuid import UUID as UUID_class
        from datetime import datetime as datetime_class

        history_id1 = UUID_class("12345678-1234-5678-1234-567812345678")
        history_id2 = UUID_class("87654321-4321-8765-4321-876543218765")
        timestamp = datetime_class(2026, 1, 21, 10, 30, 0)

        entry1 = FieldHistoryEntry(
            history_id=history_id1,
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-789",
            timestamp=timestamp,
        )

        entry2 = FieldHistoryEntry(
            history_id=history_id2,  # Different ID
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-789",
            timestamp=timestamp,
        )

        assert entry1 != entry2

    def test_handles_none_previous_value(self):
        """Test creating entry with None as previous value (field was unset)."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value=None,
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
        )

        assert entry.previous_value is None
        assert entry.new_value == "150"

    def test_handles_complex_value_types(self):
        """Test creating entry with complex value types (lists, dicts)."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value={"key": "value1"},
            new_value=["item1", "item2"],
            change_source=ChangeSource.USER_EDIT,
        )

        assert entry.previous_value == {"key": "value1"}
        assert entry.new_value == ["item1", "item2"]

    def test_hash_consistency(self):
        """Test that entry can be hashed and used in sets/dicts."""
        from uuid import UUID as UUID_class
        from datetime import datetime as datetime_class

        history_id = UUID_class("12345678-1234-5678-1234-567812345678")
        timestamp = datetime_class(2026, 1, 21, 10, 30, 0)

        entry1 = FieldHistoryEntry(
            history_id=history_id,
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-789",
            timestamp=timestamp,
        )

        entry2 = FieldHistoryEntry(
            history_id=history_id,
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-789",
            timestamp=timestamp,
        )

        # Test that equal entries have same hash
        assert hash(entry1) == hash(entry2)

        # Test that entry can be added to set
        entry_set = {entry1, entry2}
        assert len(entry_set) == 1  # Same entry, so only one in set

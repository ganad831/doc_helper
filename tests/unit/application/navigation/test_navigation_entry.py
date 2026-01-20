"""Unit tests for NavigationEntry value object."""

import pytest

from doc_helper.application.navigation.navigation_entry import NavigationEntry


class TestNavigationEntry:
    """Test NavigationEntry value object."""

    def test_create_entity_only(self):
        """Test creating entry with entity only."""
        entry = NavigationEntry(entity_id="project_info")

        assert entry.entity_id == "project_info"
        assert entry.group_id is None
        assert entry.field_id is None

    def test_create_with_group(self):
        """Test creating entry with entity and group."""
        entry = NavigationEntry(entity_id="borehole", group_id="location")

        assert entry.entity_id == "borehole"
        assert entry.group_id == "location"
        assert entry.field_id is None

    def test_create_with_all(self):
        """Test creating entry with all identifiers."""
        entry = NavigationEntry(
            entity_id="borehole", group_id="location", field_id="depth"
        )

        assert entry.entity_id == "borehole"
        assert entry.group_id == "location"
        assert entry.field_id == "depth"

    def test_empty_entity_id_raises_error(self):
        """Test that empty entity_id raises ValueError."""
        with pytest.raises(ValueError, match="entity_id cannot be empty"):
            NavigationEntry(entity_id="")

    def test_is_same_entity(self):
        """Test is_same_entity comparison."""
        entry1 = NavigationEntry(entity_id="borehole", group_id="location")
        entry2 = NavigationEntry(entity_id="borehole", group_id="details")
        entry3 = NavigationEntry(entity_id="project_info")

        assert entry1.is_same_entity(entry2)
        assert not entry1.is_same_entity(entry3)

    def test_is_same_group(self):
        """Test is_same_group comparison."""
        entry1 = NavigationEntry(
            entity_id="borehole", group_id="location", field_id="depth"
        )
        entry2 = NavigationEntry(
            entity_id="borehole", group_id="location", field_id="coordinates"
        )
        entry3 = NavigationEntry(entity_id="borehole", group_id="details")

        assert entry1.is_same_group(entry2)
        assert not entry1.is_same_group(entry3)

    def test_equality(self):
        """Test entry equality."""
        entry1 = NavigationEntry(
            entity_id="borehole", group_id="location", field_id="depth"
        )
        entry2 = NavigationEntry(
            entity_id="borehole", group_id="location", field_id="depth"
        )
        entry3 = NavigationEntry(
            entity_id="borehole", group_id="location", field_id="coordinates"
        )

        assert entry1 == entry2
        assert entry1 != entry3

    def test_hash(self):
        """Test entry hashing for use in sets/dicts."""
        entry1 = NavigationEntry(entity_id="borehole", group_id="location")
        entry2 = NavigationEntry(entity_id="borehole", group_id="location")

        # Same entries should have same hash
        assert hash(entry1) == hash(entry2)

        # Can be used in sets
        entries = {entry1, entry2}
        assert len(entries) == 1  # Should have only one unique entry

    def test_frozen(self):
        """Test that entry is immutable (frozen)."""
        entry = NavigationEntry(entity_id="project_info")

        with pytest.raises(AttributeError):
            entry.entity_id = "something_else"  # type: ignore

    def test_to_dict(self):
        """Test serialization to dictionary."""
        entry = NavigationEntry(
            entity_id="borehole", group_id="location", field_id="depth"
        )

        data = entry.to_dict()

        assert data == {
            "entity_id": "borehole",
            "group_id": "location",
            "field_id": "depth",
        }

    def test_to_dict_with_nones(self):
        """Test serialization with None values."""
        entry = NavigationEntry(entity_id="project_info")

        data = entry.to_dict()

        assert data == {
            "entity_id": "project_info",
            "group_id": None,
            "field_id": None,
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "entity_id": "borehole",
            "group_id": "location",
            "field_id": "depth",
        }

        entry = NavigationEntry.from_dict(data)

        assert entry.entity_id == "borehole"
        assert entry.group_id == "location"
        assert entry.field_id == "depth"

    def test_from_dict_with_missing_optionals(self):
        """Test deserialization with missing optional fields."""
        data = {"entity_id": "project_info"}

        entry = NavigationEntry.from_dict(data)

        assert entry.entity_id == "project_info"
        assert entry.group_id is None
        assert entry.field_id is None

    def test_round_trip_serialization(self):
        """Test that serialization->deserialization preserves entry."""
        original = NavigationEntry(
            entity_id="borehole", group_id="location", field_id="depth"
        )

        data = original.to_dict()
        restored = NavigationEntry.from_dict(data)

        assert restored == original

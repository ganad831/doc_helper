"""Integration tests for SqliteFieldHistoryRepository.

ADR-027: Field History Storage
Tests for field history persistence with real SQLite database.
"""

import pytest
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.project.field_history import (
    ChangeSource,
    FieldHistoryEntry,
)
from doc_helper.infrastructure.persistence.sqlite_field_history_repository import (
    SqliteFieldHistoryRepository,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create a temporary database file."""
    return tmp_path / "test_history.db"


@pytest.fixture
def repository(temp_db: Path) -> SqliteFieldHistoryRepository:
    """Create a repository instance with temp database."""
    return SqliteFieldHistoryRepository(temp_db)


class TestSqliteFieldHistoryRepository:
    """Test SqliteFieldHistoryRepository with real database."""

    def test_add_entry_success(self, repository: SqliteFieldHistoryRepository):
        """Test adding a history entry successfully."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-789",
        )

        result = repository.add_entry(entry)

        assert isinstance(result, Success)
        assert result.value is None

    def test_add_entry_invalid_type(self, repository: SqliteFieldHistoryRepository):
        """Test adding invalid entry type returns Failure."""
        result = repository.add_entry("not an entry")  # type: ignore

        assert isinstance(result, Failure)
        assert "must be a FieldHistoryEntry" in result.error

    def test_add_multiple_entries(self, repository: SqliteFieldHistoryRepository):
        """Test adding multiple history entries."""
        entries = [
            FieldHistoryEntry.create(
                project_id="proj-123",
                field_id="field-456",
                previous_value=str(i * 10),
                new_value=str((i + 1) * 10),
                change_source=ChangeSource.USER_EDIT,
            )
            for i in range(5)
        ]

        for entry in entries:
            result = repository.add_entry(entry)
            assert isinstance(result, Success)

    def test_get_by_field_success(self, repository: SqliteFieldHistoryRepository):
        """Test retrieving entries for a specific field."""
        from datetime import timedelta

        base_time = datetime(2026, 1, 21, 10, 0, 0)

        # Add entries for the field with explicit timestamps
        for i in range(3):
            entry = FieldHistoryEntry(
                history_id=uuid4(),
                project_id="proj-123",
                field_id="field-456",
                previous_value=str(i * 10),
                new_value=str((i + 1) * 10),
                change_source=ChangeSource.USER_EDIT,
                user_id=None,
                timestamp=base_time + timedelta(minutes=i),
            )
            repository.add_entry(entry)

        # Retrieve entries
        result = repository.get_by_field(
            project_id="proj-123", field_id="field-456"
        )

        assert isinstance(result, Success)
        retrieved_entries = result.value
        assert len(retrieved_entries) == 3
        # Should be ordered newest first
        assert retrieved_entries[0].new_value == "30"  # Last added (i=2)
        assert retrieved_entries[2].new_value == "10"  # First added (i=0)

    def test_get_by_field_empty(self, repository: SqliteFieldHistoryRepository):
        """Test retrieving entries for field with no history."""
        result = repository.get_by_field(
            project_id="proj-999", field_id="field-999"
        )

        assert isinstance(result, Success)
        assert result.value == []

    def test_get_by_field_with_pagination(
        self, repository: SqliteFieldHistoryRepository
    ):
        """Test retrieving entries with limit and offset."""
        # Add 10 entries
        for i in range(10):
            entry = FieldHistoryEntry.create(
                project_id="proj-123",
                field_id="field-456",
                previous_value=str(i * 10),
                new_value=str((i + 1) * 10),
                change_source=ChangeSource.USER_EDIT,
            )
            repository.add_entry(entry)

        # Get first page (limit=3, offset=0)
        result = repository.get_by_field(
            project_id="proj-123", field_id="field-456", limit=3, offset=0
        )
        assert isinstance(result, Success)
        assert len(result.value) == 3

        # Get second page (limit=3, offset=3)
        result = repository.get_by_field(
            project_id="proj-123", field_id="field-456", limit=3, offset=3
        )
        assert isinstance(result, Success)
        assert len(result.value) == 3

        # Get third page (limit=3, offset=6)
        result = repository.get_by_field(
            project_id="proj-123", field_id="field-456", limit=3, offset=6
        )
        assert isinstance(result, Success)
        assert len(result.value) == 3

        # Get fourth page (limit=3, offset=9) - only 1 entry left
        result = repository.get_by_field(
            project_id="proj-123", field_id="field-456", limit=3, offset=9
        )
        assert isinstance(result, Success)
        assert len(result.value) == 1

    def test_get_by_project_success(self, repository: SqliteFieldHistoryRepository):
        """Test retrieving all entries for a project."""
        # Add entries for multiple fields
        entry1 = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-1",
            previous_value="A",
            new_value="B",
            change_source=ChangeSource.USER_EDIT,
        )
        entry2 = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-2",
            previous_value="C",
            new_value="D",
            change_source=ChangeSource.USER_EDIT,
        )
        entry3 = FieldHistoryEntry.create(
            project_id="proj-456",  # Different project
            field_id="field-1",
            previous_value="E",
            new_value="F",
            change_source=ChangeSource.USER_EDIT,
        )

        repository.add_entry(entry1)
        repository.add_entry(entry2)
        repository.add_entry(entry3)

        # Retrieve entries for proj-123
        result = repository.get_by_project(project_id="proj-123")

        assert isinstance(result, Success)
        entries = result.value
        assert len(entries) == 2
        assert all(e.project_id == "proj-123" for e in entries)

    def test_get_by_project_empty(self, repository: SqliteFieldHistoryRepository):
        """Test retrieving entries for project with no history."""
        result = repository.get_by_project(project_id="proj-999")

        assert isinstance(result, Success)
        assert result.value == []

    def test_get_by_project_with_pagination(
        self, repository: SqliteFieldHistoryRepository
    ):
        """Test retrieving project entries with pagination."""
        # Add 5 entries for same project, different fields
        for i in range(5):
            entry = FieldHistoryEntry.create(
                project_id="proj-123",
                field_id=f"field-{i}",
                previous_value=str(i),
                new_value=str(i + 1),
                change_source=ChangeSource.USER_EDIT,
            )
            repository.add_entry(entry)

        # Get first page
        result = repository.get_by_project(
            project_id="proj-123", limit=2, offset=0
        )
        assert isinstance(result, Success)
        assert len(result.value) == 2

        # Get second page
        result = repository.get_by_project(
            project_id="proj-123", limit=2, offset=2
        )
        assert isinstance(result, Success)
        assert len(result.value) == 2

    def test_count_by_field_success(self, repository: SqliteFieldHistoryRepository):
        """Test counting entries for a specific field."""
        # Add 3 entries for the field
        for i in range(3):
            entry = FieldHistoryEntry.create(
                project_id="proj-123",
                field_id="field-456",
                previous_value=str(i),
                new_value=str(i + 1),
                change_source=ChangeSource.USER_EDIT,
            )
            repository.add_entry(entry)

        result = repository.count_by_field(
            project_id="proj-123", field_id="field-456"
        )

        assert isinstance(result, Success)
        assert result.value == 3

    def test_count_by_field_zero(self, repository: SqliteFieldHistoryRepository):
        """Test counting entries for field with no history."""
        result = repository.count_by_field(
            project_id="proj-999", field_id="field-999"
        )

        assert isinstance(result, Success)
        assert result.value == 0

    def test_count_by_project_success(
        self, repository: SqliteFieldHistoryRepository
    ):
        """Test counting all entries for a project."""
        # Add entries for multiple fields in same project
        for i in range(5):
            entry = FieldHistoryEntry.create(
                project_id="proj-123",
                field_id=f"field-{i}",
                previous_value=str(i),
                new_value=str(i + 1),
                change_source=ChangeSource.USER_EDIT,
            )
            repository.add_entry(entry)

        result = repository.count_by_project(project_id="proj-123")

        assert isinstance(result, Success)
        assert result.value == 5

    def test_count_by_project_zero(self, repository: SqliteFieldHistoryRepository):
        """Test counting entries for project with no history."""
        result = repository.count_by_project(project_id="proj-999")

        assert isinstance(result, Success)
        assert result.value == 0

    def test_delete_by_project_success(
        self, repository: SqliteFieldHistoryRepository
    ):
        """Test deleting all entries for a project."""
        # Add entries for two projects
        entry1 = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-1",
            previous_value="A",
            new_value="B",
            change_source=ChangeSource.USER_EDIT,
        )
        entry2 = FieldHistoryEntry.create(
            project_id="proj-456",
            field_id="field-1",
            previous_value="C",
            new_value="D",
            change_source=ChangeSource.USER_EDIT,
        )

        repository.add_entry(entry1)
        repository.add_entry(entry2)

        # Delete proj-123 history
        result = repository.delete_by_project(project_id="proj-123")

        assert isinstance(result, Success)

        # Verify proj-123 history deleted
        count_result = repository.count_by_project(project_id="proj-123")
        assert count_result.value == 0

        # Verify proj-456 history still exists
        count_result = repository.count_by_project(project_id="proj-456")
        assert count_result.value == 1

    def test_delete_by_project_nonexistent(
        self, repository: SqliteFieldHistoryRepository
    ):
        """Test deleting entries for project with no history."""
        result = repository.delete_by_project(project_id="proj-999")

        assert isinstance(result, Success)

    def test_round_trip_serialization_complex_values(
        self, repository: SqliteFieldHistoryRepository
    ):
        """Test round-trip serialization of complex value types."""
        # Test list value
        entry_list = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value=["item1", "item2"],
            new_value=["item1", "item2", "item3"],
            change_source=ChangeSource.USER_EDIT,
        )
        repository.add_entry(entry_list)

        # Test dict value
        entry_dict = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-789",
            previous_value={"key1": "value1"},
            new_value={"key1": "value1", "key2": "value2"},
            change_source=ChangeSource.USER_EDIT,
        )
        repository.add_entry(entry_dict)

        # Retrieve and verify
        result = repository.get_by_project(project_id="proj-123")
        assert isinstance(result, Success)
        entries = result.value

        # Find entries by field_id (newest first, so dict entry is first)
        dict_entry = next(e for e in entries if e.field_id == "field-789")
        list_entry = next(e for e in entries if e.field_id == "field-456")

        assert dict_entry.previous_value == {"key1": "value1"}
        assert dict_entry.new_value == {"key1": "value1", "key2": "value2"}

        assert list_entry.previous_value == ["item1", "item2"]
        assert list_entry.new_value == ["item1", "item2", "item3"]

    def test_round_trip_serialization_none_value(
        self, repository: SqliteFieldHistoryRepository
    ):
        """Test round-trip serialization of None value."""
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value=None,
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
        )

        repository.add_entry(entry)

        result = repository.get_by_field(
            project_id="proj-123", field_id="field-456"
        )
        assert isinstance(result, Success)
        retrieved_entry = result.value[0]

        assert retrieved_entry.previous_value is None
        assert retrieved_entry.new_value == "150"

    def test_round_trip_all_change_sources(
        self, repository: SqliteFieldHistoryRepository
    ):
        """Test round-trip serialization of all ChangeSource values."""
        change_sources = [
            ChangeSource.USER_EDIT,
            ChangeSource.FORMULA_RECOMPUTATION,
            ChangeSource.OVERRIDE_ACCEPTANCE,
            ChangeSource.CONTROL_EFFECT,
            ChangeSource.UNDO_OPERATION,
            ChangeSource.REDO_OPERATION,
        ]

        for i, source in enumerate(change_sources):
            entry = FieldHistoryEntry.create(
                project_id="proj-123",
                field_id=f"field-{i}",
                previous_value=str(i),
                new_value=str(i + 1),
                change_source=source,
            )
            repository.add_entry(entry)

        result = repository.get_by_project(project_id="proj-123")
        assert isinstance(result, Success)
        entries = result.value

        assert len(entries) == len(change_sources)
        retrieved_sources = {e.change_source for e in entries}
        assert retrieved_sources == set(change_sources)

    def test_schema_creation(self, temp_db: Path):
        """Test that schema is created on repository initialization."""
        # Create repository (should create schema)
        repository = SqliteFieldHistoryRepository(temp_db)

        # Verify table exists by adding an entry
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="A",
            new_value="B",
            change_source=ChangeSource.USER_EDIT,
        )

        result = repository.add_entry(entry)
        assert isinstance(result, Success)

    def test_ordering_newest_first(self, repository: SqliteFieldHistoryRepository):
        """Test that entries are returned newest first."""
        # Add entries with explicit timestamps
        from datetime import timedelta

        base_time = datetime(2026, 1, 21, 10, 0, 0)

        for i in range(5):
            entry = FieldHistoryEntry(
                history_id=uuid4(),
                project_id="proj-123",
                field_id="field-456",
                previous_value=str(i),
                new_value=str(i + 1),
                change_source=ChangeSource.USER_EDIT,
                user_id=None,
                timestamp=base_time + timedelta(minutes=i),
            )
            repository.add_entry(entry)

        result = repository.get_by_field(
            project_id="proj-123", field_id="field-456"
        )
        assert isinstance(result, Success)
        entries = result.value

        # Verify newest first
        assert entries[0].new_value == "5"  # Last entry (i=4, new_value=5)
        assert entries[4].new_value == "1"  # First entry (i=0, new_value=1)

        # Verify timestamps are in descending order
        for i in range(len(entries) - 1):
            assert entries[i].timestamp > entries[i + 1].timestamp

    def test_user_id_preservation(self, repository: SqliteFieldHistoryRepository):
        """Test that user_id is preserved in round-trip."""
        entry_with_user = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-456",
            previous_value="A",
            new_value="B",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-789",
        )

        entry_without_user = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="field-789",
            previous_value="C",
            new_value="D",
            change_source=ChangeSource.FORMULA_RECOMPUTATION,
            user_id=None,
        )

        repository.add_entry(entry_with_user)
        repository.add_entry(entry_without_user)

        result = repository.get_by_project(project_id="proj-123")
        assert isinstance(result, Success)
        entries = result.value

        # Find entries by field_id
        with_user = next(e for e in entries if e.field_id == "field-456")
        without_user = next(e for e in entries if e.field_id == "field-789")

        assert with_user.user_id == "user-789"
        assert without_user.user_id is None

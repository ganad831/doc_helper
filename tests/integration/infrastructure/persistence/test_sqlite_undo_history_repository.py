"""Integration tests for SqliteUndoHistoryRepository.

ADR-031: Undo History Persistence
- Tests database schema creation
- Tests save/load/delete operations
- Tests JSON serialization/deserialization
- Tests best-effort restoration behavior
"""

import tempfile
from pathlib import Path

import pytest

from doc_helper.domain.common.result import Failure, Success
from doc_helper.application.undo.undo_persistence_dto import (
    UndoCommandPersistenceDTO,
    UndoHistoryPersistenceDTO,
)
from doc_helper.application.undo.undo_state_dto import UndoFieldState
from doc_helper.infrastructure.persistence.sqlite_undo_history_repository import (
    SqliteUndoHistoryRepository,
)


class TestSqliteUndoHistoryRepository:
    """Tests for SqliteUndoHistoryRepository."""

    @pytest.fixture
    def temp_db(self) -> Path:
        """Create temporary database file."""
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()
        yield temp_path
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def repository(self, temp_db: Path) -> SqliteUndoHistoryRepository:
        """Create repository instance."""
        return SqliteUndoHistoryRepository(temp_db)

    @pytest.fixture
    def sample_history(self) -> UndoHistoryPersistenceDTO:
        """Create sample undo history for testing."""
        # Create sample undo commands
        cmd1 = UndoCommandPersistenceDTO.from_field_state(
            UndoFieldState.create(
                field_id="site_location",
                previous_value="123 Main St",
                new_value="456 Oak Ave",
                was_formula_computed=False,
            )
        )
        cmd2 = UndoCommandPersistenceDTO.from_field_state(
            UndoFieldState.create(
                field_id="project_name",
                previous_value="Old Project",
                new_value="New Project",
                was_formula_computed=False,
            )
        )

        # Create sample redo command
        cmd3 = UndoCommandPersistenceDTO.from_field_state(
            UndoFieldState.create(
                field_id="owner_name",
                previous_value="John Doe",
                new_value="Jane Smith",
                was_formula_computed=False,
            )
        )

        return UndoHistoryPersistenceDTO(
            project_id="proj-123",
            undo_stack=(cmd1, cmd2),
            redo_stack=(cmd3,),
            max_stack_depth=50,
            last_modified="2026-01-21T10:00:00.000Z",
        )

    def test_create_repository(self, temp_db: Path) -> None:
        """Repository should be created and initialize schema."""
        repo = SqliteUndoHistoryRepository(temp_db)
        assert repo.db_path == temp_db
        assert temp_db.exists()

    def test_create_repository_requires_path(self) -> None:
        """Repository should require database path."""
        with pytest.raises(TypeError):
            SqliteUndoHistoryRepository(None)  # type: ignore

    def test_save_new_undo_history(
        self,
        repository: SqliteUndoHistoryRepository,
        sample_history: UndoHistoryPersistenceDTO,
    ) -> None:
        """save should save new undo history."""
        # Act
        result = repository.save(sample_history)

        # Assert
        assert isinstance(result, Success)

        # Verify saved
        load_result = repository.load(sample_history.project_id)
        assert isinstance(load_result, Success)
        loaded_history = load_result.value
        assert loaded_history is not None
        assert loaded_history.project_id == sample_history.project_id
        assert len(loaded_history.undo_stack) == 2
        assert len(loaded_history.redo_stack) == 1
        assert loaded_history.max_stack_depth == 50

    def test_save_requires_undo_history_instance(
        self, repository: SqliteUndoHistoryRepository
    ) -> None:
        """save should require UndoHistoryPersistenceDTO instance."""
        result = repository.save("not a history")  # type: ignore
        assert isinstance(result, Failure)
        assert "UndoHistoryPersistenceDTO instance" in result.error

    def test_save_update_existing_undo_history(
        self,
        repository: SqliteUndoHistoryRepository,
        sample_history: UndoHistoryPersistenceDTO,
    ) -> None:
        """save should update existing undo history (upsert)."""
        # Save initial
        repository.save(sample_history)

        # Create updated history with different stacks
        updated_cmd = UndoCommandPersistenceDTO.from_field_state(
            UndoFieldState.create(
                field_id="new_field",
                previous_value="A",
                new_value="B",
                was_formula_computed=False,
            )
        )
        updated_history = UndoHistoryPersistenceDTO(
            project_id=sample_history.project_id,
            undo_stack=(updated_cmd,),
            redo_stack=(),
            max_stack_depth=100,
            last_modified="2026-01-21T12:00:00.000Z",
        )

        # Act: Save updated history
        result = repository.save(updated_history)
        assert isinstance(result, Success)

        # Assert: Verify updated (not duplicated)
        load_result = repository.load(sample_history.project_id)
        assert isinstance(load_result, Success)
        loaded_history = load_result.value
        assert loaded_history is not None
        assert len(loaded_history.undo_stack) == 1  # Updated, not original 2
        assert len(loaded_history.redo_stack) == 0  # Updated, not original 1
        assert loaded_history.max_stack_depth == 100  # Updated

    def test_load_existing_undo_history(
        self,
        repository: SqliteUndoHistoryRepository,
        sample_history: UndoHistoryPersistenceDTO,
    ) -> None:
        """load should return undo history if exists."""
        # Arrange
        repository.save(sample_history)

        # Act
        result = repository.load(sample_history.project_id)

        # Assert
        assert isinstance(result, Success)
        loaded_history = result.value
        assert loaded_history is not None
        assert loaded_history.project_id == sample_history.project_id
        assert len(loaded_history.undo_stack) == len(sample_history.undo_stack)
        assert len(loaded_history.redo_stack) == len(sample_history.redo_stack)

    def test_load_nonexistent_undo_history(
        self, repository: SqliteUndoHistoryRepository
    ) -> None:
        """load should return Success(None) if undo history doesn't exist."""
        # Act
        result = repository.load(project_id="nonexistent-proj")

        # Assert
        assert isinstance(result, Success)
        assert result.value is None  # No undo history found

    def test_load_requires_project_id(
        self, repository: SqliteUndoHistoryRepository
    ) -> None:
        """load should require valid project_id."""
        result = repository.load(project_id="")
        assert isinstance(result, Failure)
        assert "non-empty string" in result.error

    def test_load_handles_corrupted_json(
        self,
        repository: SqliteUndoHistoryRepository,
        sample_history: UndoHistoryPersistenceDTO,
    ) -> None:
        """load should return Success(None) for corrupted JSON (best-effort)."""
        # Arrange: Save valid history first
        repository.save(sample_history)

        # Act: Manually corrupt the JSON in database
        with repository._connection as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE undo_history SET undo_stack_json = ? WHERE project_id = ?",
                ("{invalid json", sample_history.project_id),
            )

        # Assert: Should return Success(None) instead of Failure (ADR-031: best-effort)
        result = repository.load(sample_history.project_id)
        assert isinstance(result, Success)
        assert result.value is None  # Corrupted data treated as missing

    def test_delete_existing_undo_history(
        self,
        repository: SqliteUndoHistoryRepository,
        sample_history: UndoHistoryPersistenceDTO,
    ) -> None:
        """delete should remove undo history."""
        # Arrange
        repository.save(sample_history)

        # Act
        result = repository.delete(sample_history.project_id)

        # Assert
        assert isinstance(result, Success)

        # Verify deleted
        load_result = repository.load(sample_history.project_id)
        assert isinstance(load_result, Success)
        assert load_result.value is None

    def test_delete_nonexistent_undo_history(
        self, repository: SqliteUndoHistoryRepository
    ) -> None:
        """delete should succeed even if undo history doesn't exist."""
        # Act
        result = repository.delete(project_id="nonexistent-proj")

        # Assert: No error (idempotent operation)
        assert isinstance(result, Success)

    def test_delete_requires_project_id(
        self, repository: SqliteUndoHistoryRepository
    ) -> None:
        """delete should require valid project_id."""
        result = repository.delete(project_id="")
        assert isinstance(result, Failure)
        assert "non-empty string" in result.error

    def test_exists_with_existing_undo_history(
        self,
        repository: SqliteUndoHistoryRepository,
        sample_history: UndoHistoryPersistenceDTO,
    ) -> None:
        """exists should return True if undo history exists."""
        # Arrange
        repository.save(sample_history)

        # Act
        result = repository.exists(sample_history.project_id)

        # Assert
        assert isinstance(result, Success)
        assert result.value is True

    def test_exists_with_nonexistent_undo_history(
        self, repository: SqliteUndoHistoryRepository
    ) -> None:
        """exists should return False if undo history doesn't exist."""
        # Act
        result = repository.exists(project_id="nonexistent-proj")

        # Assert
        assert isinstance(result, Success)
        assert result.value is False

    def test_exists_requires_project_id(
        self, repository: SqliteUndoHistoryRepository
    ) -> None:
        """exists should require valid project_id."""
        result = repository.exists(project_id="")
        assert isinstance(result, Failure)
        assert "non-empty string" in result.error

    def test_round_trip_field_values(
        self, repository: SqliteUndoHistoryRepository
    ) -> None:
        """Field values should survive round-trip serialization."""
        # Arrange: Create history with various field types
        cmd1 = UndoCommandPersistenceDTO.from_field_state(
            UndoFieldState.create(
                field_id="number_field",
                previous_value=100,
                new_value=150,
            )
        )
        cmd2 = UndoCommandPersistenceDTO.from_field_state(
            UndoFieldState.create(
                field_id="text_field",
                previous_value="Hello",
                new_value="World",
            )
        )
        cmd3 = UndoCommandPersistenceDTO.from_field_state(
            UndoFieldState.create(
                field_id="bool_field",
                previous_value=True,
                new_value=False,
            )
        )

        history = UndoHistoryPersistenceDTO(
            project_id="proj-456",
            undo_stack=(cmd1, cmd2, cmd3),
            redo_stack=(),
            max_stack_depth=50,
            last_modified="2026-01-21T10:00:00.000Z",
        )

        # Act: Save and load
        repository.save(history)
        result = repository.load("proj-456")

        # Assert: Values preserved
        assert isinstance(result, Success)
        loaded = result.value
        assert loaded is not None
        assert len(loaded.undo_stack) == 3

        # Check number field
        state1 = loaded.undo_stack[0].to_field_state()
        assert state1.field_id == "number_field"
        assert state1.previous_value == 100
        assert state1.new_value == 150

        # Check text field
        state2 = loaded.undo_stack[1].to_field_state()
        assert state2.field_id == "text_field"
        assert state2.previous_value == "Hello"
        assert state2.new_value == "World"

        # Check bool field
        state3 = loaded.undo_stack[2].to_field_state()
        assert state3.field_id == "bool_field"
        assert state3.previous_value is True
        assert state3.new_value is False

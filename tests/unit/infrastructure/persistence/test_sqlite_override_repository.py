"""Unit tests for SqliteOverrideRepository.

Tests all 7 repository interface methods with comprehensive coverage.
"""

import json
import sqlite3
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from doc_helper.domain.override.override_entity import Override
from doc_helper.domain.override.override_ids import OverrideId
from doc_helper.domain.override.override_state import OverrideState
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId
from doc_helper.infrastructure.persistence.sqlite_override_repository import (
    SqliteOverrideRepository,
)


# Fixtures


@pytest.fixture
def temp_db_path():
    """Create temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_overrides.db"


# Fixed project IDs for testing (used by sample_override fixtures)
TEST_PROJECT_ID_1 = uuid4()
TEST_PROJECT_ID_2 = uuid4()


def _create_projects_table(db_path: Path) -> None:
    """Create projects table required by foreign key constraint.

    The SqliteOverrideRepository has a FOREIGN KEY constraint referencing
    projects(project_id). Tests must create this table first.
    """
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    # Insert test project records that will be referenced
    conn.execute(
        "INSERT OR IGNORE INTO projects (project_id, name) VALUES (?, ?)",
        (str(TEST_PROJECT_ID_1), "Test Project 1")
    )
    conn.execute(
        "INSERT OR IGNORE INTO projects (project_id, name) VALUES (?, ?)",
        (str(TEST_PROJECT_ID_2), "Test Project 2")
    )
    conn.commit()
    conn.close()


@pytest.fixture
def repository(temp_db_path):
    """Create repository instance with projects table for FK constraint."""
    # Create projects table BEFORE repository (FK constraint requires it)
    _create_projects_table(temp_db_path)
    return SqliteOverrideRepository(temp_db_path)


@pytest.fixture
def sample_override():
    """Create sample override for testing.

    Uses TEST_PROJECT_ID_1 which exists in the projects table.
    """
    return Override(
        id=OverrideId(uuid4()),
        project_id=ProjectId(TEST_PROJECT_ID_1),
        field_id=FieldDefinitionId("test_field"),
        override_value=100,
        original_value=50,
        state=OverrideState.PENDING,
        reason="Test reason",
        conflict_type="formula",
    )


@pytest.fixture
def sample_override_2():
    """Create second sample override for testing.

    Uses TEST_PROJECT_ID_2 which exists in the projects table.
    """
    return Override(
        id=OverrideId(uuid4()),
        project_id=ProjectId(TEST_PROJECT_ID_2),
        field_id=FieldDefinitionId("test_field_2"),
        override_value="test_value",
        original_value="original_value",
        state=OverrideState.ACCEPTED,
        reason=None,
        conflict_type=None,
    )


# Initialization Tests


def test_init_creates_schema(temp_db_path):
    """Test that initialization creates database schema."""
    repo = SqliteOverrideRepository(temp_db_path)

    # Verify database file was created
    assert temp_db_path.exists()

    # Verify table exists
    conn = sqlite3.connect(str(temp_db_path))
    cursor = conn.cursor()

    # Check overrides table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='overrides'"
    )
    assert cursor.fetchone() is not None

    # Check indexes exist
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_overrides_project'"
    )
    assert cursor.fetchone() is not None

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_overrides_project_field'"
    )
    assert cursor.fetchone() is not None

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_overrides_state'"
    )
    assert cursor.fetchone() is not None

    conn.close()


def test_init_with_invalid_path():
    """Test that initialization with invalid path raises TypeError."""
    with pytest.raises(TypeError, match="db_path must be a string or Path"):
        SqliteOverrideRepository(123)


# get_by_id Tests


def test_get_by_id_success(repository, sample_override):
    """Test getting existing override by ID."""
    # Save override first
    save_result = repository.save(sample_override)
    assert save_result.is_success

    # Get by ID
    result = repository.get_by_id(sample_override.id)

    assert result.is_success
    override = result.value
    assert override.id == sample_override.id
    assert override.project_id == sample_override.project_id
    assert override.field_id == sample_override.field_id
    assert override.override_value == sample_override.override_value
    assert override.original_value == sample_override.original_value
    assert override.state == sample_override.state
    assert override.reason == sample_override.reason
    assert override.conflict_type == sample_override.conflict_type


def test_get_by_id_not_found(repository):
    """Test getting non-existent override returns Failure."""
    non_existent_id = OverrideId(uuid4())
    result = repository.get_by_id(non_existent_id)

    assert result.is_failure
    assert "not found" in result.error.lower()


# get_by_project_and_field Tests


def test_get_by_project_and_field_success(repository, sample_override):
    """Test getting override by project and field."""
    # Save override first
    save_result = repository.save(sample_override)
    assert save_result.is_success

    # Get by project and field
    result = repository.get_by_project_and_field(
        sample_override.project_id, sample_override.field_id
    )

    assert result.is_success
    override = result.value
    assert override is not None
    assert override.id == sample_override.id
    assert override.project_id == sample_override.project_id
    assert override.field_id == sample_override.field_id


def test_get_by_project_and_field_not_found(repository):
    """Test getting non-existent override returns Success(None)."""
    non_existent_project = ProjectId(uuid4())
    non_existent_field = FieldDefinitionId("non_existent")

    result = repository.get_by_project_and_field(non_existent_project, non_existent_field)

    assert result.is_success
    assert result.value is None


# list_by_project Tests


def test_list_by_project_multiple(repository, sample_override, sample_override_2):
    """Test listing multiple overrides for same project."""
    # Use same project_id for both overrides
    sample_override_2.project_id = sample_override.project_id

    # Save both overrides
    assert repository.save(sample_override).is_success
    assert repository.save(sample_override_2).is_success

    # List by project
    result = repository.list_by_project(sample_override.project_id)

    assert result.is_success
    overrides = result.value
    assert len(overrides) == 2
    assert sample_override.id in [o.id for o in overrides]
    assert sample_override_2.id in [o.id for o in overrides]


def test_list_by_project_empty(repository):
    """Test listing overrides for project with no overrides returns empty tuple."""
    non_existent_project = ProjectId(uuid4())

    result = repository.list_by_project(non_existent_project)

    assert result.is_success
    assert result.value == ()


def test_list_by_project_filters_correctly(repository, sample_override, sample_override_2):
    """Test that list_by_project only returns overrides for specified project."""
    # Ensure different project IDs
    assert sample_override.project_id != sample_override_2.project_id

    # Save both overrides
    assert repository.save(sample_override).is_success
    assert repository.save(sample_override_2).is_success

    # List by first project
    result = repository.list_by_project(sample_override.project_id)

    assert result.is_success
    overrides = result.value
    assert len(overrides) == 1
    assert overrides[0].id == sample_override.id

    # List by second project
    result2 = repository.list_by_project(sample_override_2.project_id)

    assert result2.is_success
    overrides2 = result2.value
    assert len(overrides2) == 1
    assert overrides2[0].id == sample_override_2.id


# save Tests


def test_save_new_override(repository, sample_override):
    """Test saving a new override."""
    result = repository.save(sample_override)

    assert result.is_success

    # Verify saved
    get_result = repository.get_by_id(sample_override.id)
    assert get_result.is_success
    saved = get_result.value
    assert saved.id == sample_override.id
    assert saved.override_value == sample_override.override_value


def test_save_update_existing(repository, sample_override):
    """Test updating an existing override."""
    # Save initial override
    assert repository.save(sample_override).is_success

    # Modify and save again
    sample_override.state = OverrideState.ACCEPTED
    sample_override.reason = "Updated reason"
    result = repository.save(sample_override)

    assert result.is_success

    # Verify updated
    get_result = repository.get_by_id(sample_override.id)
    assert get_result.is_success
    saved = get_result.value
    assert saved.state == OverrideState.ACCEPTED
    assert saved.reason == "Updated reason"


def test_save_json_serialization(repository):
    """Test that complex types are serialized correctly as JSON."""
    override = Override(
        id=OverrideId(uuid4()),
        project_id=ProjectId(TEST_PROJECT_ID_1),
        field_id=FieldDefinitionId("complex_field"),
        override_value={"nested": {"dict": [1, 2, 3]}, "list": ["a", "b"]},
        original_value=[100, 200, 300],
        state=OverrideState.PENDING,
    )

    # Save
    result = repository.save(override)
    assert result.is_success

    # Retrieve and verify
    get_result = repository.get_by_id(override.id)
    assert get_result.is_success
    saved = get_result.value
    assert saved.override_value == {"nested": {"dict": [1, 2, 3]}, "list": ["a", "b"]}
    assert saved.original_value == [100, 200, 300]


def test_save_invalid_type(repository):
    """Test that save with invalid type returns Failure."""
    result = repository.save("not an override")

    assert result.is_failure
    assert "Override instance" in result.error


# delete Tests


def test_delete_success(repository, sample_override):
    """Test deleting existing override."""
    # Save first
    assert repository.save(sample_override).is_success

    # Delete
    result = repository.delete(sample_override.id)

    assert result.is_success

    # Verify deleted
    get_result = repository.get_by_id(sample_override.id)
    assert get_result.is_failure


def test_delete_not_found(repository):
    """Test deleting non-existent override returns Failure."""
    non_existent_id = OverrideId(uuid4())

    result = repository.delete(non_existent_id)

    assert result.is_failure
    assert "not found" in result.error.lower()


# delete_by_project_and_field Tests


def test_delete_by_project_and_field_success(repository, sample_override):
    """Test deleting override by project and field."""
    # Save first
    assert repository.save(sample_override).is_success

    # Delete by project and field
    result = repository.delete_by_project_and_field(
        sample_override.project_id, sample_override.field_id
    )

    assert result.is_success

    # Verify deleted
    get_result = repository.get_by_project_and_field(
        sample_override.project_id, sample_override.field_id
    )
    assert get_result.is_success
    assert get_result.value is None


def test_delete_by_project_and_field_idempotent(repository):
    """Test that delete_by_project_and_field succeeds even if no override exists."""
    non_existent_project = ProjectId(uuid4())
    non_existent_field = FieldDefinitionId("non_existent")

    # Should succeed even though nothing to delete
    result = repository.delete_by_project_and_field(non_existent_project, non_existent_field)

    assert result.is_success


# exists Tests


def test_exists_true(repository, sample_override):
    """Test exists returns True when override exists."""
    # Save first
    assert repository.save(sample_override).is_success

    # Check existence
    result = repository.exists(sample_override.id)

    assert result.is_success
    assert result.value is True


def test_exists_false(repository):
    """Test exists returns False when override does not exist."""
    non_existent_id = OverrideId(uuid4())

    result = repository.exists(non_existent_id)

    assert result.is_success
    assert result.value is False


# Edge Case Tests


def test_save_with_none_optional_fields(repository):
    """Test saving override with None optional fields."""
    override = Override(
        id=OverrideId(uuid4()),
        project_id=ProjectId(TEST_PROJECT_ID_1),
        field_id=FieldDefinitionId("test_field"),
        override_value=100,
        original_value=50,
        state=OverrideState.PENDING,
        reason=None,
        conflict_type=None,
    )

    result = repository.save(override)
    assert result.is_success

    # Verify None values preserved
    get_result = repository.get_by_id(override.id)
    assert get_result.is_success
    saved = get_result.value
    assert saved.reason is None
    assert saved.conflict_type is None


def test_multiple_overrides_different_states(repository):
    """Test saving and retrieving overrides with different states."""
    project_id = ProjectId(TEST_PROJECT_ID_1)

    overrides = [
        Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("field_1"),
            override_value=100,
            original_value=50,
            state=OverrideState.PENDING,
        ),
        Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("field_2"),
            override_value=200,
            original_value=150,
            state=OverrideState.ACCEPTED,
        ),
        Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("field_3"),
            override_value=300,
            original_value=250,
            state=OverrideState.SYNCED,
        ),
        Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("field_4"),
            override_value=400,
            original_value=350,
            state=OverrideState.SYNCED_FORMULA,
        ),
        Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("field_5"),
            override_value=500,
            original_value=450,
            state=OverrideState.INVALID,
        ),
    ]

    # Save all overrides
    for override in overrides:
        assert repository.save(override).is_success

    # Retrieve all for project
    result = repository.list_by_project(project_id)
    assert result.is_success
    retrieved = result.value
    assert len(retrieved) == 5

    # Verify all states preserved
    states = [o.state for o in retrieved]
    assert OverrideState.PENDING in states
    assert OverrideState.ACCEPTED in states
    assert OverrideState.SYNCED in states
    assert OverrideState.SYNCED_FORMULA in states
    assert OverrideState.INVALID in states

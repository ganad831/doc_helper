"""Integration tests for SqliteProjectRepository."""

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.infrastructure.persistence.sqlite_project_repository import (
    SqliteProjectRepository,
)


class TestSqliteProjectRepository:
    """Tests for SqliteProjectRepository."""

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
    def repository(self, temp_db: Path) -> SqliteProjectRepository:
        """Create repository instance."""
        return SqliteProjectRepository(temp_db)

    @pytest.fixture
    def sample_project(self) -> Project:
        """Create sample project for testing."""
        project_id = ProjectId(uuid4())
        entity_id = EntityDefinitionId("project")

        field_values = {
            FieldDefinitionId("name"): FieldValue(
                field_id=FieldDefinitionId("name"), value="Test Project"
            ),
            FieldDefinitionId("total"): FieldValue(
                field_id=FieldDefinitionId("total"),
                value=1500,
                is_computed=True,
                computed_from="base + tax",
            ),
        }

        return Project(
            id=project_id,
            name="Test Project",
            entity_definition_id=entity_id,
            field_values=field_values,
            description="Test description",
        )

    def test_create_repository(self, temp_db: Path) -> None:
        """Repository should be created and initialize schema."""
        repo = SqliteProjectRepository(temp_db)
        assert repo.db_path == temp_db
        assert temp_db.exists()

    def test_create_repository_requires_path(self) -> None:
        """Repository should require database path."""
        with pytest.raises(TypeError):
            SqliteProjectRepository(None)  # type: ignore

    def test_save_new_project(
        self, repository: SqliteProjectRepository, sample_project: Project
    ) -> None:
        """save should save new project."""
        result = repository.save(sample_project)
        assert isinstance(result, Success)

        # Verify saved
        get_result = repository.get_by_id(sample_project.id)
        assert isinstance(get_result, Success)
        loaded_project = get_result.value
        assert loaded_project is not None
        assert loaded_project.id == sample_project.id
        assert loaded_project.name == sample_project.name

    def test_save_requires_project_instance(
        self, repository: SqliteProjectRepository
    ) -> None:
        """save should require Project instance."""
        result = repository.save("not a project")  # type: ignore
        assert isinstance(result, Failure)
        assert "Project instance" in result.error

    def test_save_update_existing_project(
        self, repository: SqliteProjectRepository, sample_project: Project
    ) -> None:
        """save should update existing project."""
        # Save initial
        repository.save(sample_project)

        # Update project
        sample_project.name = "Updated Project"
        result = repository.save(sample_project)
        assert isinstance(result, Success)

        # Verify updated
        get_result = repository.get_by_id(sample_project.id)
        assert isinstance(get_result, Success)
        loaded_project = get_result.value
        assert loaded_project.name == "Updated Project"

    def test_get_by_id_existing_project(
        self, repository: SqliteProjectRepository, sample_project: Project
    ) -> None:
        """get_by_id should return project if exists."""
        repository.save(sample_project)
        result = repository.get_by_id(sample_project.id)
        assert isinstance(result, Success)
        assert result.value is not None
        assert result.value.id == sample_project.id

    def test_get_by_id_nonexistent_project(
        self, repository: SqliteProjectRepository
    ) -> None:
        """get_by_id should return None for non-existent project."""
        result = repository.get_by_id(ProjectId(uuid4()))
        assert isinstance(result, Success)
        assert result.value is None

    def test_get_by_id_requires_project_id(
        self, repository: SqliteProjectRepository
    ) -> None:
        """get_by_id should require ProjectId."""
        result = repository.get_by_id("not-a-uuid")  # type: ignore
        assert isinstance(result, Failure)
        assert "ProjectId" in result.error

    def test_get_all_empty_repository(
        self, repository: SqliteProjectRepository
    ) -> None:
        """get_all should return empty list for empty repository."""
        result = repository.get_all()
        assert isinstance(result, Success)
        assert result.value == []

    def test_get_all_with_projects(
        self, repository: SqliteProjectRepository, sample_project: Project
    ) -> None:
        """get_all should return all projects."""
        repository.save(sample_project)

        result = repository.get_all()
        assert isinstance(result, Success)
        projects = result.value
        assert len(projects) == 1
        assert projects[0].id == sample_project.id

    def test_delete_existing_project(
        self, repository: SqliteProjectRepository, sample_project: Project
    ) -> None:
        """delete should delete existing project."""
        repository.save(sample_project)

        result = repository.delete(sample_project.id)
        assert isinstance(result, Success)

        # Verify deleted
        get_result = repository.get_by_id(sample_project.id)
        assert isinstance(get_result, Success)
        assert get_result.value is None

    def test_delete_nonexistent_project(
        self, repository: SqliteProjectRepository
    ) -> None:
        """delete should return Failure for non-existent project."""
        result = repository.delete(ProjectId(uuid4()))
        assert isinstance(result, Failure)
        assert "not found" in result.error.lower()

    def test_delete_requires_project_id(
        self, repository: SqliteProjectRepository
    ) -> None:
        """delete should require ProjectId."""
        result = repository.delete("not-a-uuid")  # type: ignore
        assert isinstance(result, Failure)
        assert "ProjectId" in result.error

    def test_exists_for_existing_project(
        self, repository: SqliteProjectRepository, sample_project: Project
    ) -> None:
        """exists should return True for existing project."""
        repository.save(sample_project)
        result = repository.exists(sample_project.id)
        assert isinstance(result, Success)
        assert result.value is True

    def test_exists_for_nonexistent_project(
        self, repository: SqliteProjectRepository
    ) -> None:
        """exists should return False for non-existent project."""
        result = repository.exists(ProjectId(uuid4()))
        assert isinstance(result, Success)
        assert result.value is False

    def test_exists_requires_project_id(
        self, repository: SqliteProjectRepository
    ) -> None:
        """exists should require ProjectId."""
        result = repository.exists("not-a-uuid")  # type: ignore
        assert isinstance(result, Failure)
        assert "ProjectId" in result.error

    def test_get_recent_empty_repository(
        self, repository: SqliteProjectRepository
    ) -> None:
        """get_recent should return empty list for empty repository."""
        result = repository.get_recent(limit=10)
        assert isinstance(result, Success)
        assert result.value == []

    def test_get_recent_with_limit(
        self, repository: SqliteProjectRepository, sample_project: Project
    ) -> None:
        """get_recent should respect limit parameter."""
        # Save multiple projects
        for i in range(5):
            project = Project(
                id=ProjectId(uuid4()),
                name=f"Project {i}",
                entity_definition_id=EntityDefinitionId("project"),
            )
            repository.save(project)

        result = repository.get_recent(limit=3)
        assert isinstance(result, Success)
        projects = result.value
        assert len(projects) == 3

    def test_get_recent_invalid_limit(
        self, repository: SqliteProjectRepository
    ) -> None:
        """get_recent should reject invalid limit."""
        result = repository.get_recent(limit=0)
        assert isinstance(result, Failure)
        assert "positive integer" in result.error.lower()

    def test_field_values_preserved(
        self, repository: SqliteProjectRepository, sample_project: Project
    ) -> None:
        """Field values should be preserved after save/load."""
        repository.save(sample_project)

        result = repository.get_by_id(sample_project.id)
        assert isinstance(result, Success)
        loaded_project = result.value

        # Verify field values
        assert len(loaded_project.field_values) == len(sample_project.field_values)

        for field_id, orig_value in sample_project.field_values.items():
            loaded_value = loaded_project.field_values[field_id]
            assert loaded_value.value == orig_value.value
            assert loaded_value.is_computed == orig_value.is_computed
            assert loaded_value.computed_from == orig_value.computed_from

    def test_timestamps_preserved(
        self, repository: SqliteProjectRepository, sample_project: Project
    ) -> None:
        """Timestamps should be preserved after save/load."""
        repository.save(sample_project)

        result = repository.get_by_id(sample_project.id)
        assert isinstance(result, Success)
        loaded_project = result.value

        assert loaded_project.created_at == sample_project.created_at
        assert loaded_project.modified_at == sample_project.modified_at

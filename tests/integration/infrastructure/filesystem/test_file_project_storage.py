"""Integration tests for FileProjectStorage."""

import json
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.infrastructure.filesystem.file_project_storage import (
    FileProjectStorage,
)


class TestFileProjectStorage:
    """Tests for FileProjectStorage."""

    @pytest.fixture
    def temp_file(self) -> Path:
        """Create temporary .dhproj file."""
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".dhproj", delete=False, mode="w"
        )
        temp_path = Path(temp_file.name)
        temp_file.close()
        yield temp_path
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def storage(self) -> FileProjectStorage:
        """Create storage instance."""
        return FileProjectStorage()

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
            FieldDefinitionId("status"): FieldValue(
                field_id=FieldDefinitionId("status"),
                value="active",
                is_computed=False,
                is_override=True,
                original_computed_value="inactive",
            ),
        }

        return Project(
            id=project_id,
            name="Test Project",
            app_type_id="soil_investigation",
            entity_definition_id=entity_id,
            field_values=field_values,
            description="Test description",
        )

    def test_create_storage(self) -> None:
        """Storage should be created."""
        storage = FileProjectStorage()
        assert storage.VERSION == "1.0"

    def test_save_project(
        self, storage: FileProjectStorage, sample_project: Project, temp_file: Path
    ) -> None:
        """save should save project to .dhproj file."""
        result = storage.save(sample_project, temp_file)
        assert isinstance(result, Success)
        assert temp_file.exists()

        # Verify file is valid JSON
        with open(temp_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["version"] == "1.0"
            assert data["name"] == "Test Project"

    def test_save_requires_project_instance(
        self, storage: FileProjectStorage, temp_file: Path
    ) -> None:
        """save should require Project instance."""
        result = storage.save("not a project", temp_file)  # type: ignore
        assert isinstance(result, Failure)
        assert "Project instance" in result.error

    def test_save_requires_valid_path(
        self, storage: FileProjectStorage, sample_project: Project
    ) -> None:
        """save should require valid file path."""
        result = storage.save(sample_project, None)  # type: ignore
        assert isinstance(result, Failure)
        assert "file_path" in result.error.lower()

    def test_save_requires_dhproj_extension(
        self, storage: FileProjectStorage, sample_project: Project
    ) -> None:
        """save should require .dhproj extension."""
        temp_file = Path(tempfile.mktemp(suffix=".txt"))
        result = storage.save(sample_project, temp_file)
        assert isinstance(result, Failure)
        assert ".dhproj" in result.error

    def test_load_project(
        self, storage: FileProjectStorage, sample_project: Project, temp_file: Path
    ) -> None:
        """load should load project from .dhproj file."""
        # Save first
        storage.save(sample_project, temp_file)

        # Load
        result = storage.load(temp_file)
        assert isinstance(result, Success)
        loaded_project = result.value
        assert loaded_project.id == sample_project.id
        assert loaded_project.name == sample_project.name
        assert loaded_project.description == sample_project.description

    def test_load_nonexistent_file(self, storage: FileProjectStorage) -> None:
        """load should return Failure for non-existent file."""
        result = storage.load("nonexistent.dhproj")
        assert isinstance(result, Failure)
        assert "not found" in result.error.lower()

    def test_load_requires_valid_path(self, storage: FileProjectStorage) -> None:
        """load should require valid file path."""
        result = storage.load(None)  # type: ignore
        assert isinstance(result, Failure)
        assert "file_path" in result.error.lower()

    def test_load_requires_dhproj_extension(
        self, storage: FileProjectStorage
    ) -> None:
        """load should require .dhproj extension."""
        temp_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        try:
            result = storage.load(temp_path)
            assert isinstance(result, Failure)
            assert ".dhproj" in result.error
        finally:
            temp_path.unlink()

    def test_field_values_preserved(
        self, storage: FileProjectStorage, sample_project: Project, temp_file: Path
    ) -> None:
        """Field values should be preserved after save/load."""
        storage.save(sample_project, temp_file)
        result = storage.load(temp_file)
        assert isinstance(result, Success)
        loaded_project = result.value

        # Verify field values
        assert len(loaded_project.field_values) == len(sample_project.field_values)

        for field_id, orig_value in sample_project.field_values.items():
            loaded_value = loaded_project.field_values[field_id]
            assert loaded_value.value == orig_value.value
            assert loaded_value.is_computed == orig_value.is_computed
            assert loaded_value.computed_from == orig_value.computed_from
            assert loaded_value.is_override == orig_value.is_override
            assert (
                loaded_value.original_computed_value
                == orig_value.original_computed_value
            )

    def test_timestamps_preserved(
        self, storage: FileProjectStorage, sample_project: Project, temp_file: Path
    ) -> None:
        """Timestamps should be preserved after save/load."""
        storage.save(sample_project, temp_file)
        result = storage.load(temp_file)
        assert isinstance(result, Success)
        loaded_project = result.value

        assert loaded_project.created_at == sample_project.created_at
        assert loaded_project.modified_at == sample_project.modified_at

    def test_exists_for_existing_file(
        self, storage: FileProjectStorage, sample_project: Project, temp_file: Path
    ) -> None:
        """exists should return True for existing .dhproj file."""
        storage.save(sample_project, temp_file)
        assert storage.exists(temp_file) is True

    def test_exists_for_nonexistent_file(self, storage: FileProjectStorage) -> None:
        """exists should return False for non-existent file."""
        assert storage.exists("nonexistent.dhproj") is False

    def test_exists_for_wrong_extension(self, storage: FileProjectStorage) -> None:
        """exists should return False for wrong extension."""
        temp_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        try:
            assert storage.exists(temp_path) is False
        finally:
            temp_path.unlink()

    def test_delete_existing_file(
        self, storage: FileProjectStorage, sample_project: Project, temp_file: Path
    ) -> None:
        """delete should delete existing .dhproj file."""
        storage.save(sample_project, temp_file)
        result = storage.delete(temp_file)
        assert isinstance(result, Success)
        assert not temp_file.exists()

    def test_delete_nonexistent_file(self, storage: FileProjectStorage) -> None:
        """delete should return Failure for non-existent file."""
        result = storage.delete("nonexistent.dhproj")
        assert isinstance(result, Failure)
        assert "not found" in result.error.lower()

    def test_delete_requires_valid_path(self, storage: FileProjectStorage) -> None:
        """delete should require valid file path."""
        result = storage.delete(None)  # type: ignore
        assert isinstance(result, Failure)
        assert "file_path" in result.error.lower()

    def test_get_project_name(
        self, storage: FileProjectStorage, sample_project: Project, temp_file: Path
    ) -> None:
        """get_project_name should return project name from file."""
        storage.save(sample_project, temp_file)
        result = storage.get_project_name(temp_file)
        assert isinstance(result, Success)
        assert result.value == "Test Project"

    def test_get_project_name_nonexistent_file(
        self, storage: FileProjectStorage
    ) -> None:
        """get_project_name should return Failure for non-existent file."""
        result = storage.get_project_name("nonexistent.dhproj")
        assert isinstance(result, Failure)
        assert "not found" in result.error.lower()

    def test_get_project_name_requires_valid_path(
        self, storage: FileProjectStorage
    ) -> None:
        """get_project_name should require valid file path."""
        result = storage.get_project_name(None)  # type: ignore
        assert isinstance(result, Failure)
        assert "file_path" in result.error.lower()

    def test_load_invalid_json(
        self, storage: FileProjectStorage, temp_file: Path
    ) -> None:
        """load should return Failure for invalid JSON."""
        # Write invalid JSON
        with open(temp_file, "w") as f:
            f.write("not valid json {")

        result = storage.load(temp_file)
        assert isinstance(result, Failure)
        assert "json" in result.error.lower()

    def test_load_unsupported_version(
        self, storage: FileProjectStorage, temp_file: Path
    ) -> None:
        """load should return Failure for unsupported version."""
        # Write file with wrong version
        data = {
            "version": "99.0",
            "project_id": str(uuid4()),
            "name": "Test",
            "entity_definition_id": "project",
            "created_at": "2024-01-01T00:00:00",
            "modified_at": "2024-01-01T00:00:00",
            "field_values": {},
        }
        with open(temp_file, "w") as f:
            json.dump(data, f)

        result = storage.load(temp_file)
        assert isinstance(result, Failure)
        assert "version" in result.error.lower()

    def test_file_contains_correct_structure(
        self, storage: FileProjectStorage, sample_project: Project, temp_file: Path
    ) -> None:
        """Saved file should contain all expected fields."""
        storage.save(sample_project, temp_file)

        with open(temp_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "version" in data
        assert "project_id" in data
        assert "name" in data
        assert "entity_definition_id" in data
        assert "description" in data
        assert "created_at" in data
        assert "modified_at" in data
        assert "field_values" in data

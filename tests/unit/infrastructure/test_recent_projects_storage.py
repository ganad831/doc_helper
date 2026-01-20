"""Tests for RecentProjectsStorage."""

import json
from pathlib import Path

import pytest

from doc_helper.application.dto.project_dto import ProjectSummaryDTO
from doc_helper.domain.common.result import Failure, Success
from doc_helper.infrastructure.filesystem.recent_projects_storage import (
    RecentProjectsStorage,
)


@pytest.fixture
def temp_storage_file(tmp_path):
    """Create temporary storage file path."""
    return tmp_path / "recent_projects.json"


@pytest.fixture
def storage(temp_storage_file):
    """Create RecentProjectsStorage instance."""
    return RecentProjectsStorage(temp_storage_file)


@pytest.fixture
def sample_project_summary():
    """Create sample ProjectSummaryDTO."""
    return ProjectSummaryDTO(
        id="project-1",
        name="Test Project",
        file_path="/path/to/project.dhproj",
        is_saved=True,
    )


class TestRecentProjectsStorage:
    """Tests for RecentProjectsStorage."""

    def test_create_storage(self, temp_storage_file):
        """Test creating storage instance."""
        storage = RecentProjectsStorage(temp_storage_file)
        assert storage is not None

    def test_add_project_to_empty_list(self, storage, sample_project_summary):
        """Test adding project to empty recent projects list."""
        result = storage.add(sample_project_summary)
        assert isinstance(result, Success)

        # Verify project was added
        recent_result = storage.get_recent()
        assert isinstance(recent_result, Success)
        recent = recent_result.value
        assert len(recent) == 1
        assert recent[0]["id"] == sample_project_summary.id
        assert recent[0]["name"] == sample_project_summary.name

    def test_add_multiple_projects(self, storage):
        """Test adding multiple projects."""
        # Add 3 projects
        for i in range(3):
            project = ProjectSummaryDTO(
                id=f"project-{i}",
                name=f"Project {i}",
                file_path=f"/path/to/project{i}.dhproj",
                is_saved=True,
            )
            result = storage.add(project)
            assert isinstance(result, Success)

        # Verify all projects added
        recent_result = storage.get_recent()
        assert isinstance(recent_result, Success)
        recent = recent_result.value
        assert len(recent) == 3

        # Verify order (most recent first)
        assert recent[0]["id"] == "project-2"
        assert recent[1]["id"] == "project-1"
        assert recent[2]["id"] == "project-0"

    def test_add_moves_existing_to_top(self, storage):
        """Test that re-adding existing project moves it to top."""
        # Add projects 1, 2, 3
        for i in range(1, 4):
            project = ProjectSummaryDTO(
                id=f"project-{i}",
                name=f"Project {i}",
                file_path=f"/path/to/project{i}.dhproj",
                is_saved=True,
            )
            storage.add(project)

        # Re-add project 1
        project_1 = ProjectSummaryDTO(
            id="project-1",
            name="Project 1 Updated",
            file_path="/path/to/project1.dhproj",
            is_saved=True,
        )
        result = storage.add(project_1)
        assert isinstance(result, Success)

        # Verify project 1 moved to top
        recent_result = storage.get_recent()
        recent = recent_result.value
        assert len(recent) == 3  # Still 3 projects
        assert recent[0]["id"] == "project-1"
        assert recent[0]["name"] == "Project 1 Updated"
        assert recent[1]["id"] == "project-3"
        assert recent[2]["id"] == "project-2"

    def test_max_recent_projects_limit(self, storage):
        """Test that only MAX_RECENT_PROJECTS (5) are kept."""
        # Add 7 projects
        for i in range(7):
            project = ProjectSummaryDTO(
                id=f"project-{i}",
                name=f"Project {i}",
                file_path=f"/path/to/project{i}.dhproj",
                is_saved=True,
            )
            storage.add(project)

        # Verify only 5 most recent kept
        recent_result = storage.get_recent()
        recent = recent_result.value
        assert len(recent) == 5

        # Verify correct projects kept (6, 5, 4, 3, 2)
        assert recent[0]["id"] == "project-6"
        assert recent[1]["id"] == "project-5"
        assert recent[2]["id"] == "project-4"
        assert recent[3]["id"] == "project-3"
        assert recent[4]["id"] == "project-2"

    def test_get_recent_empty_list(self, storage):
        """Test getting recent projects from empty list."""
        result = storage.get_recent()
        assert isinstance(result, Success)
        assert result.value == []

    def test_get_recent_nonexistent_file(self, tmp_path):
        """Test getting recent projects when file doesn't exist."""
        nonexistent_path = tmp_path / "nonexistent" / "recent_projects.json"
        storage = RecentProjectsStorage(nonexistent_path)

        result = storage.get_recent()
        assert isinstance(result, Success)
        assert result.value == []

    def test_remove_project(self, storage):
        """Test removing project from recent list."""
        # Add 3 projects
        for i in range(3):
            project = ProjectSummaryDTO(
                id=f"project-{i}",
                name=f"Project {i}",
                file_path=f"/path/to/project{i}.dhproj",
                is_saved=True,
            )
            storage.add(project)

        # Remove project-1
        result = storage.remove("project-1")
        assert isinstance(result, Success)

        # Verify project removed
        recent_result = storage.get_recent()
        recent = recent_result.value
        assert len(recent) == 2
        assert recent[0]["id"] == "project-2"
        assert recent[1]["id"] == "project-0"

    def test_remove_nonexistent_project(self, storage, sample_project_summary):
        """Test removing project that doesn't exist."""
        # Add one project
        storage.add(sample_project_summary)

        # Remove different project
        result = storage.remove("nonexistent-id")
        assert isinstance(result, Success)

        # Verify original project still there
        recent_result = storage.get_recent()
        recent = recent_result.value
        assert len(recent) == 1
        assert recent[0]["id"] == sample_project_summary.id

    def test_clear(self, storage):
        """Test clearing all recent projects."""
        # Add 3 projects
        for i in range(3):
            project = ProjectSummaryDTO(
                id=f"project-{i}",
                name=f"Project {i}",
                file_path=f"/path/to/project{i}.dhproj",
                is_saved=True,
            )
            storage.add(project)

        # Clear
        result = storage.clear()
        assert isinstance(result, Success)

        # Verify list empty
        recent_result = storage.get_recent()
        assert isinstance(recent_result, Success)
        assert recent_result.value == []

    def test_cleanup_missing_files(self, storage, tmp_path):
        """Test cleanup of projects with missing files."""
        # Create actual temp files for some projects
        existing_file_1 = tmp_path / "project1.dhproj"
        existing_file_1.write_text("{}")
        existing_file_2 = tmp_path / "project2.dhproj"
        existing_file_2.write_text("{}")

        # Add projects: 1 (exists), 2 (missing), 3 (exists), 4 (missing)
        storage.add(
            ProjectSummaryDTO(
                id="project-1",
                name="Project 1",
                file_path=str(existing_file_1),
                is_saved=True,
            )
        )
        storage.add(
            ProjectSummaryDTO(
                id="project-2",
                name="Project 2",
                file_path="/nonexistent/project2.dhproj",
                is_saved=True,
            )
        )
        storage.add(
            ProjectSummaryDTO(
                id="project-3",
                name="Project 3",
                file_path=str(existing_file_2),
                is_saved=True,
            )
        )
        storage.add(
            ProjectSummaryDTO(
                id="project-4",
                name="Project 4",
                file_path="/nonexistent/project4.dhproj",
                is_saved=True,
            )
        )

        # Cleanup
        result = storage.cleanup_missing()
        assert isinstance(result, Success)
        assert result.value == 2  # 2 projects removed

        # Verify only existing files remain
        recent_result = storage.get_recent()
        recent = recent_result.value
        assert len(recent) == 2
        assert recent[0]["id"] == "project-3"
        assert recent[1]["id"] == "project-1"

    def test_file_persistence(self, storage, sample_project_summary, temp_storage_file):
        """Test that recent projects persist across storage instances."""
        # Add project
        storage.add(sample_project_summary)

        # Create new storage instance
        new_storage = RecentProjectsStorage(temp_storage_file)

        # Verify project persisted
        result = new_storage.get_recent()
        assert isinstance(result, Success)
        recent = result.value
        assert len(recent) == 1
        assert recent[0]["id"] == sample_project_summary.id

    def test_file_format_validation(self, temp_storage_file):
        """Test validation of file format version."""
        # Write invalid version
        data = {"version": "0.5", "projects": []}
        with open(temp_storage_file, "w") as f:
            json.dump(data, f)

        storage = RecentProjectsStorage(temp_storage_file)
        result = storage.get_recent()

        assert isinstance(result, Failure)
        assert "Unsupported file version" in result.error

    def test_corrupted_json_handling(self, temp_storage_file):
        """Test handling of corrupted JSON file."""
        # Write invalid JSON
        with open(temp_storage_file, "w") as f:
            f.write("{ invalid json }")

        storage = RecentProjectsStorage(temp_storage_file)
        result = storage.get_recent()

        assert isinstance(result, Failure)
        assert "Invalid JSON" in result.error

    def test_add_invalid_type(self, storage):
        """Test adding non-ProjectSummaryDTO raises error."""
        result = storage.add("not a dto")
        assert isinstance(result, Failure)
        assert "ProjectSummaryDTO" in result.error

    def test_remove_invalid_type(self, storage):
        """Test removing with invalid project_id type."""
        result = storage.remove(123)  # Not a string
        assert isinstance(result, Failure)
        assert "must be a string" in result.error

    def test_last_accessed_timestamp(self, storage, sample_project_summary):
        """Test that last_accessed timestamp is recorded."""
        storage.add(sample_project_summary)

        recent_result = storage.get_recent()
        recent = recent_result.value
        assert "last_accessed" in recent[0]
        # Verify ISO format (will raise ValueError if invalid)
        from datetime import datetime

        datetime.fromisoformat(recent[0]["last_accessed"])

    def test_project_fields_preserved(self, storage):
        """Test that all ProjectSummaryDTO fields are preserved."""
        project = ProjectSummaryDTO(
            id="test-id", name="Test Name", file_path="/test/path.dhproj", is_saved=False
        )

        storage.add(project)

        recent_result = storage.get_recent()
        recent = recent_result.value
        assert recent[0]["id"] == "test-id"
        assert recent[0]["name"] == "Test Name"
        assert recent[0]["file_path"] == "/test/path.dhproj"
        assert recent[0]["is_saved"] is False

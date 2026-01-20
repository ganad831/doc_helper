"""Unit tests for SaveProjectCommand."""

from typing import Optional
from uuid import uuid4

import pytest

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.application.commands.save_project_command import SaveProjectCommand


class InMemoryProjectRepository(IProjectRepository):
    """In-memory project repository for testing."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._projects: dict[ProjectId, Project] = {}

    def save(self, project: Project) -> Result[None, str]:
        """Save project."""
        self._projects[project.id] = project
        return Success(None)

    def get_by_id(self, project_id: ProjectId) -> Result[Optional[Project], str]:
        """Get project by ID."""
        return Success(self._projects.get(project_id))

    def get_all(self) -> Result[list, str]:
        """Get all projects."""
        return Success(list(self._projects.values()))

    def get_recent(self, limit: int) -> Result[list, str]:
        """Get recent projects."""
        projects = sorted(
            self._projects.values(),
            key=lambda p: p.modified_at,
            reverse=True,
        )
        return Success(projects[:limit])

    def delete(self, project_id: ProjectId) -> Result[None, str]:
        """Delete project."""
        if project_id in self._projects:
            del self._projects[project_id]
        return Success(None)

    def exists(self, project_id: ProjectId) -> Result[bool, str]:
        """Check if project exists."""
        return Success(project_id in self._projects)


class TestSaveProjectCommand:
    """Tests for SaveProjectCommand."""

    @pytest.fixture
    def repository(self) -> InMemoryProjectRepository:
        """Create in-memory project repository."""
        return InMemoryProjectRepository()

    @pytest.fixture
    def command(
        self, repository: InMemoryProjectRepository
    ) -> SaveProjectCommand:
        """Create save project command."""
        return SaveProjectCommand(repository)

    @pytest.fixture
    def project(self) -> Project:
        """Create sample project."""
        return Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=EntityDefinitionId("test_entity"),
            field_values={},
        )

    def test_execute_saves_project(
        self,
        command: SaveProjectCommand,
        project: Project,
        repository: InMemoryProjectRepository,
    ) -> None:
        """execute should save project to repository."""
        # First save the project so it can be loaded by the command
        repository.save(project)

        # Execute command with project_id (new signature)
        result = command.execute(project.id)

        assert isinstance(result, Success)
        assert result.value is None

        # Verify project was saved
        saved_result = repository.get_by_id(project.id)
        assert isinstance(saved_result, Success)
        assert saved_result.value == project

    def test_execute_requires_project_id(
        self, command: SaveProjectCommand
    ) -> None:
        """execute should require ProjectId instance."""
        result = command.execute("not a project_id")  # type: ignore

        assert isinstance(result, Failure)
        assert "project_id" in result.error.lower()

    def test_execute_fails_for_nonexistent_project(
        self, command: SaveProjectCommand
    ) -> None:
        """execute should return Failure if project not found."""
        nonexistent_id = ProjectId(uuid4())
        result = command.execute(nonexistent_id)

        assert isinstance(result, Failure)
        assert "not found" in result.error.lower()

    def test_execute_handles_repository_error(
        self, project: Project
    ) -> None:
        """execute should return Failure if repository save fails."""
        # Create repository that always fails on save but succeeds on get
        class FailingRepository(InMemoryProjectRepository):
            def __init__(self, project: Project) -> None:
                super().__init__()
                self._projects[project.id] = project

            def save(self, project: Project) -> Result[None, str]:
                return Failure("Repository error")

        repository = FailingRepository(project)
        command = SaveProjectCommand(repository)

        result = command.execute(project.id)

        assert isinstance(result, Failure)
        assert "repository error" in result.error.lower()

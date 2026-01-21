"""Unit tests for ExportProjectCommand.

ADR-039: Import/Export Data Format
Tests for project export to JSON interchange format.
"""

from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import pytest

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.application.commands.export_project_command import ExportProjectCommand
from doc_helper.application.dto import ExportResultDTO


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
        return Success(list(self._projects.values())[:limit])

    def delete(self, project_id: ProjectId) -> Result[None, str]:
        """Delete project."""
        if project_id in self._projects:
            del self._projects[project_id]
        return Success(None)

    def exists(self, project_id: ProjectId) -> Result[bool, str]:
        """Check if project exists."""
        return Success(project_id in self._projects)


class InMemorySchemaRepository(ISchemaRepository):
    """In-memory schema repository for testing."""

    def __init__(self, entity_definitions: Optional[tuple[EntityDefinition, ...]] = None) -> None:
        """Initialize repository."""
        self._entity_definitions = entity_definitions if entity_definitions is not None else ()

    def get_all(self) -> Result[tuple, str]:
        """Get all entity definitions."""
        return Success(self._entity_definitions)

    def get_by_id(self, entity_id: EntityDefinitionId) -> Result[EntityDefinition, str]:
        """Get entity definition by ID."""
        for entity in self._entity_definitions:
            if entity.id == entity_id:
                return Success(entity)
        return Failure(f"Entity not found: {entity_id.value}")

    def get_root_entity(self) -> Result[EntityDefinition, str]:
        """Get root entity."""
        if self._entity_definitions:
            return Success(self._entity_definitions[0])
        return Failure("No root entity found")

    def exists(self, entity_id: EntityDefinitionId) -> bool:
        """Check if entity exists."""
        return any(entity.id == entity_id for entity in self._entity_definitions)

    def get_child_entities(self, parent_entity_id: EntityDefinitionId) -> Result[tuple, str]:
        """Get child entities."""
        return Success(())


class FakeProjectExporter:
    """Fake project exporter for testing."""

    def __init__(self, should_fail: bool = False) -> None:
        """Initialize fake exporter."""
        self.should_fail = should_fail
        self.last_project = None
        self.last_entity_definitions = None
        self.last_output_path = None

    def export_to_file(
        self,
        project: Project,
        entity_definitions: tuple[EntityDefinition, ...],
        output_path: Path,
    ) -> Result[dict[str, Any], str]:
        """Fake export to file."""
        self.last_project = project
        self.last_entity_definitions = entity_definitions
        self.last_output_path = output_path

        if self.should_fail:
            return Failure("Export failed for testing")

        return Success({
            "format_version": "1.0",
            "entity_count": 2,
            "record_count": 3,
            "field_value_count": 10,
        })


class TestExportProjectCommand:
    """Tests for ExportProjectCommand."""

    @pytest.fixture
    def project_repository(self) -> InMemoryProjectRepository:
        """Create in-memory project repository."""
        return InMemoryProjectRepository()

    @pytest.fixture
    def schema_repository(self) -> InMemorySchemaRepository:
        """Create in-memory schema repository."""
        # Create minimal entity definitions tuple for testing
        test_entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("test_entity"),
            description_key=TranslationKey("test_entity.description"),
            fields={},  # Empty dict - no fields needed for testing
            is_root_entity=True,
            parent_entity_id=None,
        )
        entity_definitions = (test_entity,)
        return InMemorySchemaRepository(entity_definitions)

    @pytest.fixture
    def project_exporter(self) -> FakeProjectExporter:
        """Create fake project exporter."""
        return FakeProjectExporter()

    @pytest.fixture
    def command(
        self,
        project_repository: InMemoryProjectRepository,
        schema_repository: InMemorySchemaRepository,
        project_exporter: FakeProjectExporter,
    ) -> ExportProjectCommand:
        """Create export project command."""
        return ExportProjectCommand(
            project_repository=project_repository,
            schema_repository=schema_repository,
            project_exporter=project_exporter,
        )

    @pytest.fixture
    def project(self) -> Project:
        """Create sample project."""
        return Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=EntityDefinitionId("test_entity"),
            field_values={},
        )

    @pytest.fixture
    def output_path(self, tmp_path: Path) -> Path:
        """Create temporary output path."""
        return tmp_path / "export.json"

    def test_execute_exports_project_successfully(
        self,
        command: ExportProjectCommand,
        project: Project,
        project_repository: InMemoryProjectRepository,
        project_exporter: FakeProjectExporter,
        output_path: Path,
    ) -> None:
        """execute should export project to file and return ExportResultDTO."""
        # Arrange: Save project to repository
        project_repository.save(project)

        # Act: Execute export command
        result = command.execute(
            project_id=project.id,
            output_file_path=output_path,
        )

        # Assert: Command succeeded
        assert isinstance(result, Success)
        export_dto = result.value
        assert isinstance(export_dto, ExportResultDTO)
        assert export_dto.success is True
        assert export_dto.project_id == str(project.id.value)
        assert export_dto.project_name == "Test Project"
        assert export_dto.error_message is None
        assert export_dto.format_version == "1.0"
        assert export_dto.entity_count == 2
        assert export_dto.record_count == 3
        assert export_dto.field_value_count == 10

        # Assert: Exporter was called with correct arguments
        assert project_exporter.last_project == project
        assert project_exporter.last_entity_definitions is not None
        assert project_exporter.last_output_path == output_path

    def test_execute_fails_for_invalid_project_id(
        self,
        command: ExportProjectCommand,
        output_path: Path,
    ) -> None:
        """execute should return Failure if project_id is not a ProjectId."""
        # Act: Execute with invalid project_id
        result = command.execute(
            project_id="not-a-project-id",  # type: ignore
            output_file_path=output_path,
        )

        # Assert: Command failed
        assert isinstance(result, Failure)
        assert "project_id must be a ProjectId" in result.error

    def test_execute_fails_for_empty_output_path(
        self,
        command: ExportProjectCommand,
        project: Project,
        project_repository: InMemoryProjectRepository,
    ) -> None:
        """execute should return Failure if output_file_path is empty."""
        # Arrange: Save project
        project_repository.save(project)

        # Act: Execute with empty output path
        result = command.execute(
            project_id=project.id,
            output_file_path="",
        )

        # Assert: Command failed
        assert isinstance(result, Failure)
        assert "output_file_path must not be empty" in result.error

    def test_execute_fails_if_project_not_found(
        self,
        command: ExportProjectCommand,
        output_path: Path,
    ) -> None:
        """execute should return Failure if project not found in repository."""
        # Arrange: Create non-existent project ID
        non_existent_id = ProjectId(uuid4())

        # Act: Execute export for non-existent project
        result = command.execute(
            project_id=non_existent_id,
            output_file_path=output_path,
        )

        # Assert: Command failed
        assert isinstance(result, Failure)
        assert "Project not found" in result.error

    def test_execute_fails_if_schema_not_found(
        self,
        project_repository: InMemoryProjectRepository,
        project_exporter: FakeProjectExporter,
        project: Project,
        output_path: Path,
    ) -> None:
        """execute should return Failure if schema not found."""
        # Arrange: Repository with no entity definitions
        schema_repository = InMemorySchemaRepository(entity_definitions=())
        command = ExportProjectCommand(
            project_repository=project_repository,
            schema_repository=schema_repository,
            project_exporter=project_exporter,
        )
        project_repository.save(project)

        # Act: Execute export
        result = command.execute(
            project_id=project.id,
            output_file_path=output_path,
        )

        # Assert: Command failed
        assert isinstance(result, Failure)
        assert "Schema not found" in result.error

    def test_execute_fails_if_exporter_fails(
        self,
        project_repository: InMemoryProjectRepository,
        schema_repository: InMemorySchemaRepository,
        project: Project,
        output_path: Path,
    ) -> None:
        """execute should return Failure if project exporter fails."""
        # Arrange: Exporter that always fails
        failing_exporter = FakeProjectExporter(should_fail=True)
        command = ExportProjectCommand(
            project_repository=project_repository,
            schema_repository=schema_repository,
            project_exporter=failing_exporter,
        )
        project_repository.save(project)

        # Act: Execute export
        result = command.execute(
            project_id=project.id,
            output_file_path=output_path,
        )

        # Assert: Command failed
        assert isinstance(result, Failure)
        assert "Failed to export project" in result.error

    def test_execute_creates_parent_directory(
        self,
        command: ExportProjectCommand,
        project: Project,
        project_repository: InMemoryProjectRepository,
        tmp_path: Path,
    ) -> None:
        """execute should create parent directory if it doesn't exist."""
        # Arrange: Output path with non-existent parent
        output_path = tmp_path / "nested" / "directory" / "export.json"
        assert not output_path.parent.exists()
        project_repository.save(project)

        # Act: Execute export
        result = command.execute(
            project_id=project.id,
            output_file_path=output_path,
        )

        # Assert: Command succeeded and directory was created
        assert isinstance(result, Success)
        assert output_path.parent.exists()

    def test_execute_accepts_string_or_path(
        self,
        command: ExportProjectCommand,
        project: Project,
        project_repository: InMemoryProjectRepository,
        output_path: Path,
    ) -> None:
        """execute should accept output_file_path as string or Path."""
        # Arrange: Save project
        project_repository.save(project)

        # Act & Assert: Execute with Path object
        result_path = command.execute(
            project_id=project.id,
            output_file_path=output_path,
        )
        assert isinstance(result_path, Success)

        # Act & Assert: Execute with string
        result_str = command.execute(
            project_id=project.id,
            output_file_path=str(output_path),
        )
        assert isinstance(result_str, Success)

    def test_constructor_validates_project_repository_type(
        self,
        schema_repository: InMemorySchemaRepository,
        project_exporter: FakeProjectExporter,
    ) -> None:
        """__init__ should raise TypeError if project_repository is not IProjectRepository."""
        with pytest.raises(TypeError, match="project_repository must implement IProjectRepository"):
            ExportProjectCommand(
                project_repository="not-a-repository",  # type: ignore
                schema_repository=schema_repository,
                project_exporter=project_exporter,
            )

    def test_constructor_validates_schema_repository_type(
        self,
        project_repository: InMemoryProjectRepository,
        project_exporter: FakeProjectExporter,
    ) -> None:
        """__init__ should raise TypeError if schema_repository is not ISchemaRepository."""
        with pytest.raises(TypeError, match="schema_repository must implement ISchemaRepository"):
            ExportProjectCommand(
                project_repository=project_repository,
                schema_repository="not-a-repository",  # type: ignore
                project_exporter=project_exporter,
            )

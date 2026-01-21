"""Integration tests for AppType lifecycle enforcement (v2 Phase 3).

Tests that project creation and opening enforce AppType existence validation.
"""

import pytest
from pathlib import Path
from uuid import uuid4

from doc_helper.application.commands.create_project_command import CreateProjectCommand
from doc_helper.application.commands.open_project_command import OpenProjectCommand
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.platform.registry.app_type_registry import AppTypeRegistry
from doc_helper.platform.discovery.manifest_parser import (
    ParsedManifest,
    ManifestSchema,
    ManifestTemplates,
    ManifestCapabilities,
)
from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata


class FakeProjectRepository(IProjectRepository):
    """Fake project repository for testing."""

    def __init__(self):
        self._projects = {}

    def save(self, project: Project):
        self._projects[project.id] = project
        return Success(None)

    def get_by_id(self, project_id: ProjectId):
        project = self._projects.get(project_id)
        return Success(project)

    def get_all(self):
        return Success(list(self._projects.values()))

    def delete(self, project_id: ProjectId):
        if project_id in self._projects:
            del self._projects[project_id]
            return Success(None)
        return Failure("Project not found")

    def exists(self, project_id: ProjectId):
        return Success(project_id in self._projects)

    def get_recent(self, limit: int = 10):
        projects = list(self._projects.values())
        return Success(projects[:limit])


class TestCreateProjectAppTypeValidation:
    """Test CreateProjectCommand AppType validation."""

    @pytest.fixture
    def registry(self):
        """Create registry with sample AppTypes."""
        registry = AppTypeRegistry()

        # Register soil_investigation AppType
        soil_manifest = ParsedManifest(
            metadata=AppTypeMetadata(
                app_type_id="soil_investigation",
                name="Soil Investigation",
                version="1.0.0",
                description="Soil investigation reports",
            ),
            schema=ManifestSchema(
                source="config.db",
                schema_type="sqlite",
            ),
            templates=ManifestTemplates(),
            capabilities=ManifestCapabilities(),
            manifest_path=Path("app_types/soil_investigation/manifest.json"),
        )
        registry.register(soil_manifest)

        # Register test_report AppType
        test_manifest = ParsedManifest(
            metadata=AppTypeMetadata(
                app_type_id="test_report",
                name="Test Report",
                version="1.0.0",
                description="Test reports",
            ),
            schema=ManifestSchema(
                source="config.db",
                schema_type="sqlite",
            ),
            templates=ManifestTemplates(),
            capabilities=ManifestCapabilities(),
            manifest_path=Path("app_types/test_report/manifest.json"),
        )
        registry.register(test_manifest)

        return registry

    @pytest.fixture
    def repository(self):
        """Create fake project repository."""
        return FakeProjectRepository()

    @pytest.fixture
    def command(self, repository, registry):
        """Create CreateProjectCommand with dependencies."""
        return CreateProjectCommand(
            project_repository=repository,
            app_type_registry=registry,
        )

    def test_create_project_with_valid_apptype_succeeds(self, command):
        """Test that creating project with valid AppType succeeds."""
        result = command.execute(
            name="Test Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("project"),
        )

        assert isinstance(result, Success)
        assert isinstance(result.value, ProjectId)

    def test_create_project_with_invalid_apptype_fails(self, command):
        """Test that creating project with invalid AppType fails."""
        result = command.execute(
            name="Test Project",
            app_type_id="nonexistent_apptype",
            entity_definition_id=EntityDefinitionId("project"),
        )

        assert isinstance(result, Failure)
        assert "AppType 'nonexistent_apptype' not found" in result.error
        assert "Available AppTypes:" in result.error
        assert "soil_investigation" in result.error
        assert "test_report" in result.error

    def test_create_project_with_default_apptype_when_missing_from_registry_fails(
        self, repository
    ):
        """Test that creating project with default AppType fails if not registered."""
        # Create empty registry
        empty_registry = AppTypeRegistry()

        command = CreateProjectCommand(
            project_repository=repository,
            app_type_registry=empty_registry,
        )

        # Don't provide app_type_id - should use default "soil_investigation"
        result = command.execute(
            name="Test Project",
            entity_definition_id=EntityDefinitionId("project"),
        )

        assert isinstance(result, Failure)
        assert "AppType 'soil_investigation' not found" in result.error

    def test_create_project_lists_available_apptypes_in_error(self, command):
        """Test that error message lists all available AppTypes."""
        result = command.execute(
            name="Test Project",
            app_type_id="invalid",
            entity_definition_id=EntityDefinitionId("project"),
        )

        assert isinstance(result, Failure)
        # Should list both registered AppTypes alphabetically
        assert "soil_investigation, test_report" in result.error

    def test_create_project_with_empty_registry_shows_none_available(self, repository):
        """Test that error message shows 'none' when registry is empty."""
        empty_registry = AppTypeRegistry()
        command = CreateProjectCommand(
            project_repository=repository,
            app_type_registry=empty_registry,
        )

        result = command.execute(
            name="Test Project",
            app_type_id="any",
            entity_definition_id=EntityDefinitionId("project"),
        )

        assert isinstance(result, Failure)
        assert "Available AppTypes: none" in result.error

    def test_create_project_with_second_apptype_succeeds(self, command):
        """Test that creating project with test_report AppType succeeds."""
        result = command.execute(
            name="Test Project",
            app_type_id="test_report",
            entity_definition_id=EntityDefinitionId("report_info"),
        )

        assert isinstance(result, Success)
        assert isinstance(result.value, ProjectId)


class TestOpenProjectAppTypeValidation:
    """Test OpenProjectCommand AppType validation."""

    @pytest.fixture
    def registry(self):
        """Create registry with sample AppTypes."""
        registry = AppTypeRegistry()

        # Register soil_investigation AppType
        soil_manifest = ParsedManifest(
            metadata=AppTypeMetadata(
                app_type_id="soil_investigation",
                name="Soil Investigation",
                version="1.0.0",
                description="Soil investigation reports",
            ),
            schema=ManifestSchema(
                source="config.db",
                schema_type="sqlite",
            ),
            templates=ManifestTemplates(),
            capabilities=ManifestCapabilities(),
            manifest_path=Path("app_types/soil_investigation/manifest.json"),
        )
        registry.register(soil_manifest)

        return registry

    @pytest.fixture
    def repository_with_projects(self):
        """Create fake repository with sample projects."""
        repo = FakeProjectRepository()

        # Create project with soil_investigation AppType
        soil_project_id = ProjectId(uuid4())
        soil_project = Project(
            id=soil_project_id,
            name="Soil Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={},
        )
        repo.save(soil_project)

        # Create project with test_report AppType (not in registry)
        test_project_id = ProjectId(uuid4())
        test_project = Project(
            id=test_project_id,
            name="Test Project",
            app_type_id="test_report",
            entity_definition_id=EntityDefinitionId("report_info"),
            field_values={},
        )
        repo.save(test_project)

        return repo, soil_project_id, test_project_id

    @pytest.fixture
    def command(self, repository_with_projects, registry):
        """Create OpenProjectCommand with dependencies."""
        repo, _, _ = repository_with_projects
        return OpenProjectCommand(
            project_repository=repo,
            app_type_registry=registry,
        )

    def test_open_project_with_valid_apptype_succeeds(
        self, command, repository_with_projects
    ):
        """Test that opening project with valid AppType succeeds."""
        _, soil_project_id, _ = repository_with_projects

        result = command.execute(soil_project_id)

        assert isinstance(result, Success)
        assert result.value.name == "Soil Project"
        assert result.value.app_type_id == "soil_investigation"

    def test_open_project_with_missing_apptype_fails(
        self, command, repository_with_projects
    ):
        """Test that opening project with missing AppType fails."""
        _, _, test_project_id = repository_with_projects

        result = command.execute(test_project_id)

        assert isinstance(result, Failure)
        assert "Cannot open project: AppType 'test_report' not found" in result.error
        assert "Available AppTypes:" in result.error
        assert "soil_investigation" in result.error

    def test_open_project_error_explains_requirement(
        self, command, repository_with_projects
    ):
        """Test that error message explains why project can't be opened."""
        _, _, test_project_id = repository_with_projects

        result = command.execute(test_project_id)

        assert isinstance(result, Failure)
        assert "requires AppType 'test_report' which is not installed" in result.error

    def test_open_nonexistent_project_fails_before_apptype_check(self, command):
        """Test that nonexistent project fails before AppType validation."""
        nonexistent_id = ProjectId(uuid4())

        result = command.execute(nonexistent_id)

        assert isinstance(result, Failure)
        assert "Project not found" in result.error

    def test_open_project_with_empty_registry_shows_none_available(
        self, repository_with_projects
    ):
        """Test that error message shows 'none' when registry is empty."""
        repo, _, test_project_id = repository_with_projects
        empty_registry = AppTypeRegistry()

        command = OpenProjectCommand(
            project_repository=repo,
            app_type_registry=empty_registry,
        )

        result = command.execute(test_project_id)

        assert isinstance(result, Failure)
        assert "Available AppTypes: none" in result.error


class TestBackwardCompatibility:
    """Test backward compatibility with existing projects."""

    def test_old_projects_with_default_apptype_open_successfully(self):
        """Test that old projects using default AppType open successfully."""
        # Setup registry with default AppType
        registry = AppTypeRegistry()
        soil_manifest = ParsedManifest(
            metadata=AppTypeMetadata(
                app_type_id="soil_investigation",
                name="Soil Investigation",
                version="1.0.0",
                description="Soil investigation reports",
            ),
            schema=ManifestSchema(
                source="config.db",
                schema_type="sqlite",
            ),
            templates=ManifestTemplates(),
            capabilities=ManifestCapabilities(),
            manifest_path=Path("app_types/soil_investigation/manifest.json"),
        )
        registry.register(soil_manifest)

        # Setup repository with old project
        repo = FakeProjectRepository()
        old_project_id = ProjectId(uuid4())
        old_project = Project(
            id=old_project_id,
            name="Old Project",
            app_type_id="soil_investigation",  # v1 default
            entity_definition_id=EntityDefinitionId("project"),
            field_values={},
        )
        repo.save(old_project)

        # Open project
        command = OpenProjectCommand(
            project_repository=repo,
            app_type_registry=registry,
        )
        result = command.execute(old_project_id)

        # Should succeed
        assert isinstance(result, Success)
        assert result.value.name == "Old Project"
        assert result.value.app_type_id == "soil_investigation"

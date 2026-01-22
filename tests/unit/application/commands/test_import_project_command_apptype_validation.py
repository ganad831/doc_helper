"""Tests for ImportProjectCommand AppType validation (v2 PHASE 4).

Ensures that ImportProjectCommand validates app_type_id against registry,
enforcing same invariant as CreateProjectCommand and OpenProjectCommand.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

from doc_helper.application.commands.import_project_command import ImportProjectCommand
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.platform.registry.interfaces import IAppTypeRegistry


@pytest.fixture
def mock_project_repository():
    """Create mock project repository."""
    return Mock(spec=IProjectRepository)


@pytest.fixture
def mock_schema_repository():
    """Create mock schema repository with entity definitions."""
    repo = Mock(spec=ISchemaRepository)

    # Mock entity definition (just mock it, don't construct real one)
    entity_def = Mock()
    entity_def.id = EntityDefinitionId("project_info")

    repo.get_all.return_value = Success((entity_def,))
    return repo


@pytest.fixture
def mock_project_importer():
    """Create mock project importer."""
    return Mock()


@pytest.fixture
def mock_validation_service():
    """Create mock validation service."""
    service = Mock(spec=ValidationService)
    # Mock validation always passes (we're testing AppType validation, not field validation)
    validation_dto = Mock()
    validation_dto.has_blocking_errors.return_value = False
    service.validate_project.return_value = Success(validation_dto)
    return service


@pytest.fixture
def mock_app_type_registry_with_soil():
    """Create mock registry with soil_investigation registered."""
    registry = Mock(spec=IAppTypeRegistry)
    registry.exists.side_effect = lambda app_type_id: app_type_id == "soil_investigation"
    registry.list_app_type_ids.return_value = ("soil_investigation",)
    return registry


@pytest.fixture
def mock_app_type_registry_empty():
    """Create mock registry with no AppTypes."""
    registry = Mock(spec=IAppTypeRegistry)
    registry.exists.return_value = False
    registry.list_app_type_ids.return_value = ()
    return registry


class TestImportProjectCommandAppTypeValidation:
    """Test ImportProjectCommand validates app_type_id against registry."""

    def test_import_with_valid_apptype_succeeds(
        self,
        mock_project_repository,
        mock_schema_repository,
        mock_project_importer,
        mock_validation_service,
        mock_app_type_registry_with_soil,
        tmp_path,
    ):
        """Test: Importing project with valid app_type_id succeeds."""
        # Setup: Create project with valid app_type_id
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            app_type_id="soil_investigation",  # Valid AppType
            entity_definition_id=EntityDefinitionId("project_info"),
        )

        # Mock importer returns project
        import_file_path = tmp_path / "import.json"
        import_file_path.write_text("{}")  # Create dummy file

        mock_project_importer.import_from_file.return_value = Success({
            "project": project,
            "format_version": "1.0",
            "source_app_version": "1.0.0",
            "project_name": "Test Project",
            "warnings": [],
        })

        # Mock repository save succeeds
        mock_project_repository.save.return_value = Success(None)

        # Create command
        command = ImportProjectCommand(
            project_repository=mock_project_repository,
            schema_repository=mock_schema_repository,
            project_importer=mock_project_importer,
            validation_service=mock_validation_service,
            app_type_registry=mock_app_type_registry_with_soil,
        )

        # Execute
        result = command.execute(input_file_path=str(import_file_path))

        # Assert: Success
        assert isinstance(result, Success)
        import_dto = result.value
        assert import_dto.success is True
        assert import_dto.project_id == str(project.id.value)
        assert import_dto.error_message is None

        # Verify project was saved
        mock_project_repository.save.assert_called_once_with(project)

    def test_import_with_invalid_apptype_fails(
        self,
        mock_project_repository,
        mock_schema_repository,
        mock_project_importer,
        mock_validation_service,
        mock_app_type_registry_with_soil,
        tmp_path,
    ):
        """Test: Importing project with non-existent app_type_id fails gracefully."""
        # Setup: Create project with INVALID app_type_id
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            app_type_id="nonexistent_app",  # Invalid AppType!
            entity_definition_id=EntityDefinitionId("project_info"),
        )

        # Mock importer returns project
        import_file_path = tmp_path / "import.json"
        import_file_path.write_text("{}")

        mock_project_importer.import_from_file.return_value = Success({
            "project": project,
            "format_version": "1.0",
            "source_app_version": "1.0.0",
            "project_name": "Test Project",
            "warnings": [],
        })

        # Create command
        command = ImportProjectCommand(
            project_repository=mock_project_repository,
            schema_repository=mock_schema_repository,
            project_importer=mock_project_importer,
            validation_service=mock_validation_service,
            app_type_registry=mock_app_type_registry_with_soil,
        )

        # Execute
        result = command.execute(input_file_path=str(import_file_path))

        # Assert: Success wrapper with failure DTO
        assert isinstance(result, Success)
        import_dto = result.value

        # Import failed due to invalid AppType
        assert import_dto.success is False
        assert import_dto.project_id is None
        assert "Cannot import project: AppType 'nonexistent_app' not found" in import_dto.error_message
        assert "Available AppTypes: soil_investigation" in import_dto.error_message

        # Verify project was NOT saved
        mock_project_repository.save.assert_not_called()

        # Verify validation service was NOT called (AppType check happens first)
        mock_validation_service.validate_project.assert_not_called()

    def test_import_with_empty_registry_fails(
        self,
        mock_project_repository,
        mock_schema_repository,
        mock_project_importer,
        mock_validation_service,
        mock_app_type_registry_empty,
        tmp_path,
    ):
        """Test: Importing when no AppTypes registered fails with clear message."""
        # Setup: Create project
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("project_info"),
        )

        # Mock importer returns project
        import_file_path = tmp_path / "import.json"
        import_file_path.write_text("{}")

        mock_project_importer.import_from_file.return_value = Success({
            "project": project,
            "format_version": "1.0",
            "source_app_version": "1.0.0",
            "project_name": "Test Project",
            "warnings": [],
        })

        # Create command with EMPTY registry
        command = ImportProjectCommand(
            project_repository=mock_project_repository,
            schema_repository=mock_schema_repository,
            project_importer=mock_project_importer,
            validation_service=mock_validation_service,
            app_type_registry=mock_app_type_registry_empty,
        )

        # Execute
        result = command.execute(input_file_path=str(import_file_path))

        # Assert: Failure
        assert isinstance(result, Success)
        import_dto = result.value
        assert import_dto.success is False
        assert "Cannot import project: AppType 'soil_investigation' not found" in import_dto.error_message
        assert "Available AppTypes: none" in import_dto.error_message

        # Verify project was NOT saved
        mock_project_repository.save.assert_not_called()

    def test_import_with_corrupted_apptype_id_fails(
        self,
        mock_project_repository,
        mock_schema_repository,
        mock_project_importer,
        mock_validation_service,
        mock_app_type_registry_with_soil,
        tmp_path,
    ):
        """Test: Importing project with SQL injection attempt in app_type_id fails."""
        # Setup: Create project with malicious app_type_id
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            app_type_id="'; DROP TABLE projects; --",  # SQL injection attempt
            entity_definition_id=EntityDefinitionId("project_info"),
        )

        # Mock importer returns project (importer doesn't validate)
        import_file_path = tmp_path / "import.json"
        import_file_path.write_text("{}")

        mock_project_importer.import_from_file.return_value = Success({
            "project": project,
            "format_version": "1.0",
            "source_app_version": "1.0.0",
            "project_name": "Test Project",
            "warnings": [],
        })

        # Create command
        command = ImportProjectCommand(
            project_repository=mock_project_repository,
            schema_repository=mock_schema_repository,
            project_importer=mock_project_importer,
            validation_service=mock_validation_service,
            app_type_registry=mock_app_type_registry_with_soil,
        )

        # Execute
        result = command.execute(input_file_path=str(import_file_path))

        # Assert: Rejected due to invalid AppType
        assert isinstance(result, Success)
        import_dto = result.value
        assert import_dto.success is False
        assert "'; DROP TABLE projects; --" in import_dto.error_message
        assert "not found" in import_dto.error_message

        # Verify project was NOT saved (SQL injection prevented)
        mock_project_repository.save.assert_not_called()

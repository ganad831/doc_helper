"""Unit tests for ImportProjectCommand.

ADR-039: Import/Export Data Format
Tests for project import from JSON interchange format.
"""

from pathlib import Path
from typing import Any, Optional
from unittest.mock import Mock
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
from doc_helper.application.commands.import_project_command import ImportProjectCommand
from doc_helper.application.dto import ImportResultDTO
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.platform.registry.interfaces import IAppTypeRegistry
from doc_helper.platform.discovery.manifest_parser import ParsedManifest


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


class FakeProjectImporter:
    """Fake project importer for testing."""

    def __init__(self, should_fail: bool = False, project: Optional[Project] = None) -> None:
        """Initialize fake importer."""
        self.should_fail = should_fail
        self._project = project
        self.last_input_path = None
        self.last_entity_definitions = None

    def import_from_file(
        self,
        input_path: Path,
        entity_definitions: tuple[EntityDefinition, ...],
    ) -> Result[dict[str, Any], str]:
        """Fake import from file."""
        self.last_input_path = input_path
        self.last_entity_definitions = entity_definitions

        if self.should_fail:
            return Failure("Import failed for testing")

        return Success({
            "project": self._project,
            "format_version": "1.0",
            "source_app_version": "1.0.0",
            "project_name": "Imported Project",
            "warnings": [],
        })


class FakeValidationService(ValidationService):
    """Fake validation service for testing."""

    def __init__(self, has_errors: bool = False) -> None:
        """Initialize fake service."""
        self.has_errors = has_errors
        self.last_project = None

    def validate_project(self, project: Project) -> Result[Any, str]:
        """Fake validation."""
        self.last_project = project

        # Create mock validation result DTO
        class MockValidationDTO:
            def __init__(self, has_errors: bool):
                self.has_errors_flag = has_errors
                self.errors = []

            def has_blocking_errors(self) -> bool:
                return self.has_errors_flag

        return Success(MockValidationDTO(self.has_errors))


class TestImportProjectCommand:
    """Tests for ImportProjectCommand."""

    @pytest.fixture
    def project_repository(self) -> InMemoryProjectRepository:
        """Create in-memory project repository."""
        return InMemoryProjectRepository()

    @pytest.fixture
    def schema_repository(self) -> InMemorySchemaRepository:
        """Create in-memory schema repository."""
        # Create minimal entity definition for testing
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
    def project(self) -> Project:
        """Create sample project for import."""
        return Project(
            id=ProjectId(uuid4()),
            name="Imported Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("test_entity"),
            field_values={},
        )

    @pytest.fixture
    def project_importer(self, project: Project) -> FakeProjectImporter:
        """Create fake project importer."""
        return FakeProjectImporter(project=project)

    @pytest.fixture
    def validation_service(self) -> FakeValidationService:
        """Create fake validation service."""
        return FakeValidationService()

    @pytest.fixture
    def app_type_registry(self):
        """Create fake app type registry that accepts all app_type_ids."""
        registry = Mock(spec=IAppTypeRegistry)
        registry.exists.return_value = True  # Accept all for existing tests
        registry.list_app_type_ids.return_value = ("soil_investigation",)
        return registry

    @pytest.fixture
    def command(
        self,
        project_repository: InMemoryProjectRepository,
        schema_repository: InMemorySchemaRepository,
        project_importer: FakeProjectImporter,
        validation_service: FakeValidationService,
        app_type_registry,
    ) -> ImportProjectCommand:
        """Create import project command."""
        return ImportProjectCommand(
            project_repository=project_repository,
            schema_repository=schema_repository,
            project_importer=project_importer,
            validation_service=validation_service,
            app_type_registry=app_type_registry,
        )

    @pytest.fixture
    def input_file(self, tmp_path: Path) -> Path:
        """Create temporary input file."""
        input_path = tmp_path / "import.json"
        input_path.write_text('{"format_version": "1.0"}')
        return input_path

    def test_execute_imports_project_successfully(
        self,
        command: ImportProjectCommand,
        project_importer: FakeProjectImporter,
        validation_service: FakeValidationService,
        input_file: Path,
        project: Project,
    ) -> None:
        """execute should import project from file and return ImportResultDTO."""
        # Act: Execute import command
        result = command.execute(input_file_path=input_file)

        # Assert: Command succeeded
        assert isinstance(result, Success)
        import_dto = result.value
        assert isinstance(import_dto, ImportResultDTO)
        assert import_dto.success is True
        assert import_dto.project_id == str(project.id.value)
        assert import_dto.project_name == "Imported Project"
        assert import_dto.error_message is None
        assert import_dto.format_version == "1.0"
        assert len(import_dto.validation_errors) == 0

        # Assert: Importer was called
        assert project_importer.last_input_path == input_file

        # Assert: Validation was performed
        assert validation_service.last_project == project

    def test_execute_fails_for_empty_input_path(
        self,
        command: ImportProjectCommand,
    ) -> None:
        """execute should return ImportResultDTO with failure if input_file_path is empty."""
        # Act: Execute with empty input path
        result = command.execute(input_file_path="")

        # Assert: Returns Success with failed ImportResultDTO
        assert isinstance(result, Success)
        import_dto = result.value
        assert import_dto.success is False
        assert "input_file_path must not be empty" in import_dto.error_message

    def test_execute_fails_if_file_not_found(
        self,
        command: ImportProjectCommand,
    ) -> None:
        """execute should return ImportResultDTO with failure if file doesn't exist."""
        # Arrange: Non-existent file path
        non_existent_path = Path("/nonexistent/import.json")

        # Act: Execute import
        result = command.execute(input_file_path=non_existent_path)

        # Assert: Returns Success with failed ImportResultDTO
        assert isinstance(result, Success)
        import_dto = result.value
        assert import_dto.success is False
        assert "Import file not found" in import_dto.error_message

    def test_execute_fails_if_schema_not_found(
        self,
        project_repository: InMemoryProjectRepository,
        project_importer: FakeProjectImporter,
        validation_service: FakeValidationService,
        app_type_registry,
        input_file: Path,
    ) -> None:
        """execute should return ImportResultDTO with failure if schema not found."""
        # Arrange: Repository with no schema
        schema_repository = InMemorySchemaRepository(entity_definitions=None)
        command = ImportProjectCommand(
            project_repository=project_repository,
            schema_repository=schema_repository,
            project_importer=project_importer,
            validation_service=validation_service,
            app_type_registry=app_type_registry,
        )

        # Act: Execute import
        result = command.execute(input_file_path=input_file)

        # Assert: Returns Success with failed ImportResultDTO
        assert isinstance(result, Success)
        import_dto = result.value
        assert import_dto.success is False
        assert "Schema not found" in import_dto.error_message

    def test_execute_fails_if_importer_fails(
        self,
        project_repository: InMemoryProjectRepository,
        schema_repository: InMemorySchemaRepository,
        validation_service: FakeValidationService,
        app_type_registry,
        input_file: Path,
    ) -> None:
        """execute should return ImportResultDTO with failure if importer fails."""
        # Arrange: Importer that always fails
        failing_importer = FakeProjectImporter(should_fail=True)
        command = ImportProjectCommand(
            project_repository=project_repository,
            schema_repository=schema_repository,
            project_importer=failing_importer,
            validation_service=validation_service,
            app_type_registry=app_type_registry,
        )

        # Act: Execute import
        result = command.execute(input_file_path=input_file)

        # Assert: Returns Success with failed ImportResultDTO
        assert isinstance(result, Success)
        import_dto = result.value
        assert import_dto.success is False
        assert "Failed to parse import file" in import_dto.error_message

    def test_execute_fails_if_validation_has_blocking_errors(
        self,
        project_repository: InMemoryProjectRepository,
        schema_repository: InMemorySchemaRepository,
        project: Project,
        app_type_registry,
        input_file: Path,
    ) -> None:
        """execute should return ImportResultDTO with failure if validation fails (ADR-039: atomic import)."""
        # Arrange: Validation service that always fails
        failing_validation = FakeValidationService(has_errors=True)
        project_importer = FakeProjectImporter(project=project)
        command = ImportProjectCommand(
            project_repository=project_repository,
            schema_repository=schema_repository,
            project_importer=project_importer,
            validation_service=failing_validation,
            app_type_registry=app_type_registry,
        )

        # Act: Execute import
        result = command.execute(input_file_path=input_file)

        # Assert: Returns Success with failed ImportResultDTO
        assert isinstance(result, Success)
        import_dto = result.value
        assert import_dto.success is False
        assert "Import validation failed" in import_dto.error_message

        # Assert: Project was NOT saved (atomic import)
        saved_projects = project_repository.get_all().value
        assert len(saved_projects) == 0

    def test_execute_saves_project_only_after_validation_passes(
        self,
        command: ImportProjectCommand,
        project_repository: InMemoryProjectRepository,
        input_file: Path,
        project: Project,
    ) -> None:
        """execute should save project only after validation passes (ADR-039: atomic import)."""
        # Act: Execute import
        result = command.execute(input_file_path=input_file)

        # Assert: Command succeeded
        assert isinstance(result, Success)
        import_dto = result.value
        assert import_dto.success is True

        # Assert: Project was saved
        saved_projects = project_repository.get_all().value
        assert len(saved_projects) == 1
        assert saved_projects[0].id == project.id

    def test_execute_accepts_string_or_path(
        self,
        command: ImportProjectCommand,
        input_file: Path,
    ) -> None:
        """execute should accept input_file_path as string or Path."""
        # Act & Assert: Execute with Path object
        result_path = command.execute(input_file_path=input_file)
        assert isinstance(result_path, Success)
        assert result_path.value.success is True

        # Act & Assert: Execute with string
        result_str = command.execute(input_file_path=str(input_file))
        assert isinstance(result_str, Success)
        assert result_str.value.success is True

    def test_execute_preserves_warnings_from_importer(
        self,
        project_repository: InMemoryProjectRepository,
        schema_repository: InMemorySchemaRepository,
        validation_service: FakeValidationService,
        project: Project,
        app_type_registry,
        input_file: Path,
    ) -> None:
        """execute should preserve warnings from importer in ImportResultDTO."""
        # Arrange: Importer that returns warnings
        class ImporterWithWarnings(FakeProjectImporter):
            def import_from_file(self, input_path: Path, entity_definitions: tuple[EntityDefinition, ...]) -> Result[dict[str, Any], str]:
                return Success({
                    "project": project,
                    "format_version": "1.0",
                    "source_app_version": "1.0.0",
                    "project_name": "Imported Project",
                    "warnings": ["Field 'old_field' not found in current schema", "Entity 'old_entity' ignored"],
                })

        importer = ImporterWithWarnings()
        command = ImportProjectCommand(
            project_repository=project_repository,
            schema_repository=schema_repository,
            project_importer=importer,
            validation_service=validation_service,
            app_type_registry=app_type_registry,
        )

        # Act: Execute import
        result = command.execute(input_file_path=input_file)

        # Assert: Warnings preserved
        assert isinstance(result, Success)
        import_dto = result.value
        assert import_dto.success is True
        assert len(import_dto.warnings) == 2
        assert "old_field" in import_dto.warnings[0]
        assert "old_entity" in import_dto.warnings[1]

    def test_constructor_validates_project_repository_type(
        self,
        schema_repository: InMemorySchemaRepository,
        project_importer: FakeProjectImporter,
        validation_service: FakeValidationService,
        app_type_registry,
    ) -> None:
        """__init__ should raise TypeError if project_repository is not IProjectRepository."""
        with pytest.raises(TypeError, match="project_repository must implement IProjectRepository"):
            ImportProjectCommand(
                project_repository="not-a-repository",  # type: ignore
                schema_repository=schema_repository,
                project_importer=project_importer,
                validation_service=validation_service,
                app_type_registry=app_type_registry,
            )

    def test_constructor_validates_schema_repository_type(
        self,
        project_repository: InMemoryProjectRepository,
        project_importer: FakeProjectImporter,
        validation_service: FakeValidationService,
        app_type_registry,
    ) -> None:
        """__init__ should raise TypeError if schema_repository is not ISchemaRepository."""
        with pytest.raises(TypeError, match="schema_repository must implement ISchemaRepository"):
            ImportProjectCommand(
                project_repository=project_repository,
                schema_repository="not-a-repository",  # type: ignore
                project_importer=project_importer,
                validation_service=validation_service,
                app_type_registry=app_type_registry,
            )

    def test_constructor_validates_validation_service_type(
        self,
        project_repository: InMemoryProjectRepository,
        schema_repository: InMemorySchemaRepository,
        project_importer: FakeProjectImporter,
        app_type_registry,
    ) -> None:
        """__init__ should raise TypeError if validation_service is not ValidationService."""
        with pytest.raises(TypeError, match="validation_service must be a ValidationService instance"):
            ImportProjectCommand(
                project_repository=project_repository,
                schema_repository=schema_repository,
                project_importer=project_importer,
                validation_service="not-a-service",  # type: ignore
                app_type_registry=app_type_registry,
            )

"""Unit tests for GenerateDocumentCommand U8 enhancements.

U8 BEHAVIOR TESTED:
- Auto-save project before document generation
- Override cleanup after successful generation
- Cleanup failures don't block generation
"""

from pathlib import Path
from unittest.mock import Mock, create_autospec
from uuid import uuid4

import pytest

from doc_helper.application.commands.generate_document_command import (
    GenerateDocumentCommand,
)
from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.document.document_generation_service import (
    DocumentGenerationService,
)
from doc_helper.application.services.override_service import OverrideService
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository


class FakeProjectRepository(IProjectRepository):
    """Fake project repository for testing."""

    def __init__(self):
        self._projects: dict[ProjectId, Project] = {}

    def get_by_id(self, project_id: ProjectId):
        project = self._projects.get(project_id)
        if project:
            return Success(project)
        return Failure(f"Project {project_id} not found")

    def save(self, project: Project):
        self._projects[project.id] = project
        return Success(None)

    def delete(self, project_id: ProjectId):
        if project_id in self._projects:
            del self._projects[project_id]
            return Success(None)
        return Failure(f"Project {project_id} not found")

    def exists(self, project_id: ProjectId):
        return Success(project_id in self._projects)

    def list_all(self):
        return Success(tuple(self._projects.values()))

    def get_all(self):
        """Get all projects."""
        return Success(tuple(self._projects.values()))

    def get_recent(self, limit: int = 5):
        """Get recent projects (stub for testing)."""
        projects = list(self._projects.values())
        return Success(tuple(projects[:limit]))




class TestGenerateDocumentCommandU8:
    """Test GenerateDocumentCommand with U8 enhancements."""

    @pytest.fixture
    def project_id(self):
        """Create project ID for testing."""
        return ProjectId(uuid4())

    @pytest.fixture
    def project(self, project_id):
        """Create project for testing."""
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId

        return Project(
            id=project_id,
            name="Test Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("project"),
        )

    @pytest.fixture
    def project_repository(self, project, project_id):
        """Create fake project repository with test project."""
        repo = FakeProjectRepository()
        repo._projects[project_id] = project
        return repo

    @pytest.fixture
    def save_command(self):
        """Create mock save command."""
        mock = create_autospec(SaveProjectCommand, instance=True)
        mock.execute.return_value = Success(None)
        return mock

    @pytest.fixture
    def document_service(self):
        """Create mock document service."""
        mock = create_autospec(DocumentGenerationService, instance=True)
        mock.generate.return_value = Success(Path("output.docx"))
        return mock

    @pytest.fixture
    def override_service(self):
        """Create mock override service."""
        mock = create_autospec(OverrideService, instance=True)
        mock.cleanup_synced_overrides.return_value = Success(0)
        return mock

    @pytest.fixture
    def validation_service(self):
        """Create mock validation service."""
        from doc_helper.domain.validation.validation_result import ValidationResult

        mock = create_autospec(ValidationService, instance=True)
        # Default: validation passes (no errors)
        mock.validate_by_project_id.return_value = Success(ValidationResult.success())
        return mock

    @pytest.fixture
    def command(
        self, project_repository, save_command, document_service, override_service, validation_service
    ):
        """Create generate document command with all dependencies."""
        return GenerateDocumentCommand(
            project_repository=project_repository,
            save_command=save_command,
            document_service=document_service,
            override_service=override_service,
            validation_service=validation_service,
        )

    def test_auto_save_called_before_generation(
        self,
        command,
        project_id,
        save_command,
        document_service,
        override_service,
    ):
        """Test that auto-save is called before document generation."""
        # Generate document
        result = command.execute(
            project_id=project_id,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        # Verify success
        assert isinstance(result, Success)

        # Verify save was called
        save_command.execute.assert_called_once_with(project_id)

    def test_auto_save_failure_blocks_generation(
        self,
        command,
        project_id,
        save_command,
        document_service,
        override_service,
    ):
        """Test that auto-save failure prevents document generation."""
        # Set save to fail
        save_command.execute.return_value = Failure("Save failed")

        # Attempt generation
        result = command.execute(
            project_id=project_id,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        # Verify failure
        assert isinstance(result, Failure)
        assert "Auto-save before generation failed" in result.error

        # Verify generation was NOT called
        document_service.generate.assert_not_called()

        # Verify cleanup was NOT called
        override_service.cleanup_synced_overrides.assert_not_called()

    def test_cleanup_called_after_successful_generation(
        self,
        command,
        project_id,
        save_command,
        document_service,
        override_service,
    ):
        """Test that cleanup is called after successful document generation."""
        # Set cleanup to return count
        override_service.cleanup_synced_overrides.return_value = Success(3)

        # Generate document
        result = command.execute(
            project_id=project_id,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        # Verify success
        assert isinstance(result, Success)

        # Verify cleanup was called
        override_service.cleanup_synced_overrides.assert_called_once_with(project_id)

    def test_cleanup_not_called_if_generation_fails(
        self,
        command,
        project_id,
        save_command,
        document_service,
        override_service,
    ):
        """Test that cleanup is NOT called if document generation fails."""
        # Set generation to fail
        document_service.generate.return_value = Failure("Generation failed")

        # Attempt generation
        result = command.execute(
            project_id=project_id,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        # Verify failure
        assert isinstance(result, Failure)

        # Verify cleanup was NOT called
        override_service.cleanup_synced_overrides.assert_not_called()

    def test_cleanup_failure_does_not_fail_generation(
        self,
        command,
        project_id,
        save_command,
        document_service,
        override_service,
    ):
        """Test that cleanup failure does NOT fail the generation.

        U8 requirement: Cleanup is best-effort, failures should not block generation.
        """
        # Set cleanup to fail
        override_service.cleanup_synced_overrides.return_value = Failure("Cleanup failed")

        # Generate document
        result = command.execute(
            project_id=project_id,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        # Verify generation still succeeds
        assert isinstance(result, Success)
        assert result.value == Path("output.docx")

        # Verify cleanup was attempted
        override_service.cleanup_synced_overrides.assert_called_once_with(project_id)

    def test_full_workflow_sequence(
        self,
        command,
        project_id,
        save_command,
        document_service,
        override_service,
    ):
        """Test the complete U8 workflow: save → generate → cleanup."""
        # Set cleanup to return count
        override_service.cleanup_synced_overrides.return_value = Success(5)

        # Generate document
        result = command.execute(
            project_id=project_id,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        # Verify success
        assert isinstance(result, Success)
        assert result.value == Path("output.docx")

        # Verify workflow sequence - all were called
        save_command.execute.assert_called_once()
        document_service.generate.assert_called_once()
        override_service.cleanup_synced_overrides.assert_called_once()

    def test_invalid_project_id_type_fails(self, command):
        """Test that invalid project_id type returns failure."""
        result = command.execute(
            project_id="not_a_project_id",
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        assert isinstance(result, Failure)
        assert "project_id must be a ProjectId" in result.error

    def test_invalid_format_type_fails(self, command, project_id):
        """Test that invalid format type returns failure."""
        result = command.execute(
            project_id=project_id,
            template_path="template.docx",
            output_path="output.docx",
            format="word",  # Should be DocumentFormat enum
        )

        assert isinstance(result, Failure)
        assert "format must be a DocumentFormat" in result.error

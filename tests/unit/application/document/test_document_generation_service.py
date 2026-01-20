"""Unit tests for DocumentGenerationService."""

from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.document.document_adapter import IDocumentAdapter
from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.domain.document.transformer_registry import TransformerRegistry
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.application.document.document_generation_service import (
    DocumentGenerationService,
)


class TestDocumentGenerationService:
    """Tests for DocumentGenerationService."""

    @pytest.fixture
    def mock_adapter(self) -> Mock:
        """Create mock document adapter."""
        adapter = Mock(spec=IDocumentAdapter)
        adapter.format = DocumentFormat.WORD
        adapter.validate_template.return_value = Success(None)
        adapter.generate.return_value = Success(None)
        return adapter

    @pytest.fixture
    def transformer_registry(self) -> TransformerRegistry:
        """Create empty transformer registry."""
        return TransformerRegistry()

    @pytest.fixture
    def service(
        self, mock_adapter: Mock, transformer_registry: TransformerRegistry
    ) -> DocumentGenerationService:
        """Create document generation service."""
        return DocumentGenerationService(
            adapters={"word": mock_adapter},
            transformer_registry=transformer_registry,
        )

    @pytest.fixture
    def sample_project(self) -> Project:
        """Create sample project for testing."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=EntityDefinitionId("test_entity"),
            field_values={
                FieldDefinitionId("field1"): FieldValue(
                    field_id=FieldDefinitionId("field1"),
                    value="value1",
                ),
                FieldDefinitionId("field2"): FieldValue(
                    field_id=FieldDefinitionId("field2"),
                    value="value2",
                ),
            },
        )
        return project

    def test_create_service(
        self, mock_adapter: Mock, transformer_registry: TransformerRegistry
    ) -> None:
        """Service should be created with adapters and registry."""
        service = DocumentGenerationService(
            adapters={"word": mock_adapter},
            transformer_registry=transformer_registry,
        )
        assert service is not None

    def test_create_service_requires_adapters_dict(
        self, transformer_registry: TransformerRegistry
    ) -> None:
        """Service should require adapters to be a dict."""
        with pytest.raises(TypeError):
            DocumentGenerationService(
                adapters="not a dict",  # type: ignore
                transformer_registry=transformer_registry,
            )

    def test_create_service_requires_transformer_registry(
        self, mock_adapter: Mock
    ) -> None:
        """Service should require transformer registry."""
        with pytest.raises(TypeError):
            DocumentGenerationService(
                adapters={"word": mock_adapter},
                transformer_registry="not a registry",  # type: ignore
            )

    def test_generate_document_success(
        self, service: DocumentGenerationService, sample_project: Project
    ) -> None:
        """generate should successfully generate document."""
        result = service.generate(
            project=sample_project,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        assert isinstance(result, Success)
        assert result.value == Path("output.docx")

    def test_generate_validates_template(
        self,
        service: DocumentGenerationService,
        sample_project: Project,
        mock_adapter: Mock,
    ) -> None:
        """generate should validate template before generation."""
        service.generate(
            project=sample_project,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        mock_adapter.validate_template.assert_called_once_with("template.docx")

    def test_generate_calls_adapter(
        self,
        service: DocumentGenerationService,
        sample_project: Project,
        mock_adapter: Mock,
    ) -> None:
        """generate should call adapter with correct parameters."""
        service.generate(
            project=sample_project,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        mock_adapter.generate.assert_called_once()
        call_args = mock_adapter.generate.call_args
        assert call_args[1]["template_path"] == "template.docx"
        assert call_args[1]["output_path"] == "output.docx"
        assert "field_values" in call_args[1]

    def test_generate_prepares_field_values(
        self,
        service: DocumentGenerationService,
        sample_project: Project,
        mock_adapter: Mock,
    ) -> None:
        """generate should prepare field values from project."""
        service.generate(
            project=sample_project,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        call_args = mock_adapter.generate.call_args
        field_values = call_args[1]["field_values"]

        assert "field1" in field_values
        assert field_values["field1"] == "value1"
        assert "field2" in field_values
        assert field_values["field2"] == "value2"

    def test_generate_with_invalid_project(
        self, service: DocumentGenerationService
    ) -> None:
        """generate should fail with invalid project."""
        result = service.generate(
            project="not a project",  # type: ignore
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        assert isinstance(result, Failure)
        assert "Project" in result.error

    def test_generate_with_invalid_format(
        self, service: DocumentGenerationService, sample_project: Project
    ) -> None:
        """generate should fail with invalid format."""
        result = service.generate(
            project=sample_project,
            template_path="template.docx",
            output_path="output.docx",
            format="not a format",  # type: ignore
        )

        assert isinstance(result, Failure)
        assert "DocumentFormat" in result.error

    def test_generate_with_unsupported_format(
        self, service: DocumentGenerationService, sample_project: Project
    ) -> None:
        """generate should fail with unsupported format."""
        result = service.generate(
            project=sample_project,
            template_path="template.pdf",
            output_path="output.pdf",
            format=DocumentFormat.PDF,  # Not in adapters
        )

        assert isinstance(result, Failure)
        assert "adapter" in result.error.lower()

    def test_generate_with_invalid_template(
        self,
        service: DocumentGenerationService,
        sample_project: Project,
        mock_adapter: Mock,
    ) -> None:
        """generate should fail with invalid template."""
        mock_adapter.validate_template.return_value = Failure("Template not found")

        result = service.generate(
            project=sample_project,
            template_path="invalid.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        assert isinstance(result, Failure)
        assert result.error == "Template not found"

    def test_generate_with_adapter_error(
        self,
        service: DocumentGenerationService,
        sample_project: Project,
        mock_adapter: Mock,
    ) -> None:
        """generate should fail when adapter fails."""
        mock_adapter.generate.return_value = Failure("Generation failed")

        result = service.generate(
            project=sample_project,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD,
        )

        assert isinstance(result, Failure)
        assert result.error == "Generation failed"

    def test_get_supported_formats(
        self, transformer_registry: TransformerRegistry
    ) -> None:
        """get_supported_formats should return available formats."""
        mock_word = Mock(spec=IDocumentAdapter)
        mock_excel = Mock(spec=IDocumentAdapter)

        service = DocumentGenerationService(
            adapters={"word": mock_word, "excel": mock_excel},
            transformer_registry=transformer_registry,
        )

        formats = service.get_supported_formats()

        assert DocumentFormat.WORD in formats
        assert DocumentFormat.EXCEL in formats
        assert len(formats) == 2

    def test_get_supported_formats_empty(
        self, transformer_registry: TransformerRegistry
    ) -> None:
        """get_supported_formats should return empty list when no adapters."""
        service = DocumentGenerationService(
            adapters={},
            transformer_registry=transformer_registry,
        )

        formats = service.get_supported_formats()

        assert formats == []

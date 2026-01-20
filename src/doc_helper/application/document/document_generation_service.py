"""Document generation service."""

from pathlib import Path
from typing import Any

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.document.document_adapter import IDocumentAdapter
from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.domain.document.transformer_registry import TransformerRegistry
from doc_helper.domain.project.project import Project


class DocumentGenerationService:
    """Service for generating documents from projects.

    Orchestrates the document generation process by:
    1. Preparing field values with appropriate transformations
    2. Selecting the correct document adapter
    3. Generating the document

    Example:
        service = DocumentGenerationService(
            adapters={"word": word_adapter, "excel": excel_adapter},
            transformer_registry=registry
        )
        result = service.generate(
            project=project,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD
        )
    """

    def __init__(
        self,
        adapters: dict[str, IDocumentAdapter],
        transformer_registry: TransformerRegistry,
    ) -> None:
        """Initialize document generation service.

        Args:
            adapters: Dictionary of format_name -> adapter instance
            transformer_registry: Registry of available transformers
        """
        if not isinstance(adapters, dict):
            raise TypeError("adapters must be a dictionary")
        if not isinstance(transformer_registry, TransformerRegistry):
            raise TypeError("transformer_registry must be a TransformerRegistry")

        self._adapters = adapters
        self._transformer_registry = transformer_registry

    def generate(
        self,
        project: Project,
        template_path: str | Path,
        output_path: str | Path,
        format: DocumentFormat,
    ) -> Result[Path, str]:
        """Generate document from project.

        Args:
            project: Project to generate document from
            template_path: Path to template file
            output_path: Path for generated document
            format: Document format to generate

        Returns:
            Success(output_path) if generated, Failure(error) otherwise
        """
        if not isinstance(project, Project):
            return Failure("project must be a Project instance")
        if not isinstance(format, DocumentFormat):
            return Failure("format must be a DocumentFormat")

        # Get adapter for format
        adapter = self._adapters.get(format.value)
        if adapter is None:
            return Failure(f"No adapter available for format: {format.value}")

        # Validate template
        validation_result = adapter.validate_template(template_path)
        if isinstance(validation_result, Failure):
            return validation_result

        # Prepare field values (convert FieldValue objects to raw values)
        field_values = self._prepare_field_values(project)

        # Generate document
        generation_result = adapter.generate(
            template_path=template_path,
            output_path=output_path,
            field_values=field_values,
        )

        if isinstance(generation_result, Failure):
            return generation_result

        return Success(Path(output_path))

    def _prepare_field_values(self, project: Project) -> dict[str, Any]:
        """Prepare field values for document generation.

        Converts FieldValue objects to raw values suitable for templates.

        Args:
            project: Project to extract values from

        Returns:
            Dictionary of field_name -> raw value
        """
        field_values = {}

        for field_id, field_value in project.field_values.items():
            # Use field ID as key (templates use field IDs)
            field_name = field_id.value
            field_values[field_name] = field_value.value

        return field_values

    def get_supported_formats(self) -> list[DocumentFormat]:
        """Get list of supported document formats.

        Returns:
            List of supported formats based on available adapters
        """
        formats = []
        for format_name in self._adapters.keys():
            try:
                formats.append(DocumentFormat(format_name))
            except ValueError:
                # Skip invalid format names
                continue
        return formats

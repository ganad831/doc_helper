"""Facade for document generation with primitive/DTO parameters.

This facade wraps GenerateDocumentCommand to accept primitives and DTOs
instead of domain types, enabling Clean Architecture compliance.

ARCHITECTURAL FIX:
- Presentation layer passes string IDs and DTOs
- This facade converts to domain types (ProjectId, DocumentFormat)
- Domain type construction stays in Application layer
"""

from pathlib import Path
from typing import Union

from doc_helper.application.commands.generate_document_command import (
    GenerateDocumentCommand,
)
from doc_helper.application.dto import DocumentFormatDTO
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.domain.project.project_ids import ProjectId


class GenerateDocumentFacade:
    """Facade for document generation accepting primitives/DTOs.

    This facade:
    - Accepts string project_id instead of ProjectId
    - Accepts DocumentFormatDTO instead of DocumentFormat enum
    - Converts to domain types before calling the underlying command
    - Keeps domain type construction in Application layer

    Usage:
        facade = GenerateDocumentFacade(generate_command)
        result = facade.execute(
            project_id="project-123",
            template_path=Path("template.docx"),
            output_path=Path("output.docx"),
            format_dto=DocumentFormatDTO(id="DOCX", name="Word Document", extension=".docx")
        )
    """

    def __init__(self, command: GenerateDocumentCommand) -> None:
        """Initialize facade.

        Args:
            command: Underlying GenerateDocumentCommand
        """
        self._command = command

    def execute(
        self,
        project_id: str,
        template_path: Union[str, Path],
        output_path: Union[str, Path],
        format_dto: DocumentFormatDTO,
    ) -> Result[Path, str]:
        """Execute document generation with primitive/DTO parameters.

        Args:
            project_id: Project ID as string
            template_path: Path to template file
            output_path: Path for generated document
            format_dto: Document format as DTO

        Returns:
            Success(output_path) if generated, Failure(error) otherwise
        """
        # Validate inputs
        if not project_id:
            return Failure("project_id cannot be empty")

        # Convert string to domain ID (Application layer responsibility)
        domain_project_id = ProjectId(project_id)

        # Convert DTO to domain enum (Application layer responsibility)
        domain_format_result = self._convert_format_dto_to_domain(format_dto)
        if domain_format_result.is_failure():
            return Failure(domain_format_result.error)

        domain_format = domain_format_result.value

        # Delegate to underlying command
        return self._command.execute(
            project_id=domain_project_id,
            template_path=template_path,
            output_path=output_path,
            format=domain_format,
        )

    @staticmethod
    def _convert_format_dto_to_domain(dto: DocumentFormatDTO) -> Result[DocumentFormat, str]:
        """Convert DocumentFormatDTO to domain DocumentFormat.

        Args:
            dto: DocumentFormatDTO to convert

        Returns:
            Success(DocumentFormat) or Failure(error)
        """
        # Map DTO id to domain enum
        format_map = {
            "DOCX": DocumentFormat.WORD,
            "XLSX": DocumentFormat.EXCEL,
            "PDF": DocumentFormat.PDF,
        }

        domain_format = format_map.get(dto.id)
        if domain_format is None:
            return Failure(f"Unknown document format: {dto.id}")

        return Success(domain_format)

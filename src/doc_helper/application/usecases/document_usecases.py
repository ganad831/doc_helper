"""Document Use Cases (Architecture Enforcement Phase).

Application layer use-case class that encapsulates ALL document operations.

RULE 0 ENFORCEMENT:
- Presentation ONLY calls use-case methods
- All domain type construction happens HERE
- All command/query orchestration happens HERE
- Returns primitives/DTOs to Presentation (no domain types)

This class wraps:
- GenerateDocumentCommand (generate document)
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


class DocumentUseCases:
    """Use-case class for ALL document operations.

    This class provides a clean boundary between Presentation and Application layers.

    RULE 0 COMPLIANCE:
        - Presentation receives ONLY this use-case class via DI
        - NO commands, queries, or repositories are exposed
        - All domain type construction happens internally

    Usage in ViewModel:
        # ViewModel __init__ receives DocumentUseCases via DI
        def __init__(self, document_usecases: DocumentUseCases, ...):
            self._document_usecases = document_usecases

        # ViewModel calls use-case methods with primitives/DTOs
        def generate(self, project_id: str, ...):
            return self._document_usecases.generate_document(project_id, ...)
    """

    def __init__(
        self,
        generate_document_command: GenerateDocumentCommand,
    ) -> None:
        """Initialize DocumentUseCases.

        Args:
            generate_document_command: Command for generating documents
        """
        self._generate_document_command = generate_document_command

    def generate_document(
        self,
        project_id: str,
        template_path: Union[str, Path],
        output_path: Union[str, Path],
        format_dto: DocumentFormatDTO,
    ) -> Result[Path, str]:
        """Generate a document with primitive/DTO parameters.

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
        return self._generate_document_command.execute(
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

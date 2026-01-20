"""Command for generating a document from a project."""

from pathlib import Path

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.application.document.document_generation_service import (
    DocumentGenerationService,
)


class GenerateDocumentCommand:
    """Command to generate a document from a project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands modify state and return Result[None, str]
    - Coordinates domain services and infrastructure

    Example:
        command = GenerateDocumentCommand(
            project_repository=repo,
            document_service=doc_service
        )
        result = command.execute(
            project_id=project_id,
            template_path="template.docx",
            output_path="output.docx",
            format=DocumentFormat.WORD
        )
        if isinstance(result, Success):
            print(f"Document generated: {result.value}")
    """

    def __init__(
        self,
        project_repository: IProjectRepository,
        document_service: DocumentGenerationService,
    ) -> None:
        """Initialize command.

        Args:
            project_repository: Repository for loading projects
            document_service: Service for generating documents
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        if not isinstance(document_service, DocumentGenerationService):
            raise TypeError(
                "document_service must be a DocumentGenerationService instance"
            )

        self._project_repository = project_repository
        self._document_service = document_service

    def execute(
        self,
        project_id: ProjectId,
        template_path: str | Path,
        output_path: str | Path,
        format: DocumentFormat,
    ) -> Result[Path, str]:
        """Execute generate document command.

        Args:
            project_id: Project to generate document for
            template_path: Path to template file
            output_path: Path for generated document
            format: Document format to generate

        Returns:
            Success(output_path) if generated, Failure(error) otherwise
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")
        if not isinstance(format, DocumentFormat):
            return Failure("format must be a DocumentFormat")

        # Load project
        load_result = self._project_repository.get_by_id(project_id)
        if isinstance(load_result, Failure):
            return Failure(f"Failed to load project: {load_result.error}")

        project = load_result.value
        if project is None:
            return Failure(f"Project not found: {project_id.value}")

        # Generate document
        generation_result = self._document_service.generate(
            project=project,
            template_path=template_path,
            output_path=output_path,
            format=format,
        )

        if isinstance(generation_result, Failure):
            return Failure(f"Failed to generate document: {generation_result.error}")

        return Success(generation_result.value)

"""Command for generating a document from a project.

U8 ENHANCEMENTS:
- Auto-save project before document generation
- Cleanup SYNCED (non-formula) overrides after successful generation
- Preserve SYNCED_FORMULA overrides across document generations
"""

from pathlib import Path

from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.services.override_service import OverrideService
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

    U8 BEHAVIOR:
    - Project auto-saved before generation
    - SYNCED (non-formula) overrides cleaned up after successful generation
    - SYNCED_FORMULA overrides preserved

    Example:
        command = GenerateDocumentCommand(
            project_repository=repo,
            save_command=save_cmd,
            document_service=doc_service,
            override_service=override_svc
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
        save_command: SaveProjectCommand,
        document_service: DocumentGenerationService,
        override_service: OverrideService,
    ) -> None:
        """Initialize command.

        Args:
            project_repository: Repository for loading projects
            save_command: Command for auto-saving project (U8)
            document_service: Service for generating documents
            override_service: Service for managing overrides (U8)
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        if not isinstance(save_command, SaveProjectCommand):
            raise TypeError("save_command must be a SaveProjectCommand instance")
        if not isinstance(document_service, DocumentGenerationService):
            raise TypeError(
                "document_service must be a DocumentGenerationService instance"
            )
        if not isinstance(override_service, OverrideService):
            raise TypeError("override_service must be an OverrideService instance")

        self._project_repository = project_repository
        self._save_command = save_command
        self._document_service = document_service
        self._override_service = override_service

    def execute(
        self,
        project_id: ProjectId,
        template_path: str | Path,
        output_path: str | Path,
        format: DocumentFormat,
    ) -> Result[Path, str]:
        """Execute generate document command.

        U8 WORKFLOW:
        1. Auto-save project before generation
        2. Load project from repository
        3. Generate document via service
        4. Cleanup SYNCED overrides after successful generation

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

        # U8: Auto-save project before generation
        save_result = self._save_command.execute(project_id)
        if isinstance(save_result, Failure):
            return Failure(f"Auto-save before generation failed: {save_result.error}")

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

        # U8: Cleanup SYNCED (non-formula) overrides after successful generation
        cleanup_result = self._override_service.cleanup_synced_overrides(project_id)
        if isinstance(cleanup_result, Failure):
            # Log warning but don't fail generation - cleanup is not critical
            # (In production, would use proper logging)
            # Cleanup failures don't affect the document generation result
            pass

        return Success(generation_result.value)

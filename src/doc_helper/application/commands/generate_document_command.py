"""Command for generating a document from a project.

U8 ENHANCEMENTS:
- Auto-save project before document generation
- Cleanup SYNCED (non-formula) overrides after successful generation
- Preserve SYNCED_FORMULA overrides across document generations

ADR-025 ENHANCEMENTS:
- Validation with severity levels before generation
- Block generation if ERROR-level validation failures exist
- Allow generation with WARNING/INFO-level failures
"""

from pathlib import Path

from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.services.override_service import OverrideService
from doc_helper.application.services.validation_service import ValidationService
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

    ADR-025 BEHAVIOR:
    - Validates project before generation
    - Blocks generation if ERROR-level validation failures exist
    - Allows generation with WARNING/INFO-level failures only

    Example:
        command = GenerateDocumentCommand(
            project_repository=repo,
            save_command=save_cmd,
            document_service=doc_service,
            override_service=override_svc,
            validation_service=validation_svc
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
        validation_service: ValidationService,
    ) -> None:
        """Initialize command.

        Args:
            project_repository: Repository for loading projects
            save_command: Command for auto-saving project (U8)
            document_service: Service for generating documents
            override_service: Service for managing overrides (U8)
            validation_service: Service for validating projects (ADR-025)
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
        if not isinstance(validation_service, ValidationService):
            raise TypeError("validation_service must be a ValidationService instance")

        self._project_repository = project_repository
        self._save_command = save_command
        self._document_service = document_service
        self._override_service = override_service
        self._validation_service = validation_service

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
        3. ADR-025: Validate project and block if ERROR-level failures
        4. Generate document via service
        5. Cleanup SYNCED overrides after successful generation

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

        # ADR-025: Validate project before generation
        validation_result = self._validation_service.validate_by_project_id(project_id)
        if isinstance(validation_result, Failure):
            return Failure(f"Validation failed: {validation_result.error}")

        validation = validation_result.value

        # ADR-025: Block generation if ERROR-level validation failures exist
        if validation.has_blocking_errors():
            error_count = len(validation.get_errors_by_severity(
                __import__('doc_helper.domain.validation.severity', fromlist=['Severity']).Severity.ERROR
            ))
            return Failure(
                f"Cannot generate document: {error_count} ERROR-level validation "
                f"failure(s) must be resolved before generation"
            )

        # WARNING and INFO level failures do not block generation
        # (User confirmation for warnings is handled in presentation layer)

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

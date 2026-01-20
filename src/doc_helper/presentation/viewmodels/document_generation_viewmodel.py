"""ViewModel for Document Generation.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md):
- Presentation layer uses DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary
- Simple enums (DocumentFormat) and IDs (ProjectId) can cross boundaries
"""

from pathlib import Path
from typing import Optional

from doc_helper.application.commands.generate_document_command import (
    GenerateDocumentCommand,
)
from doc_helper.application.dto import ValidationResultDTO
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


class DocumentGenerationViewModel(BaseViewModel):
    """ViewModel for Document Generation.

    Coordinates document generation process including:
    - Template selection
    - Format selection (Word, Excel, PDF)
    - Output path selection
    - Pre-generation validation
    - Generation progress

    v1 Scope:
    - Basic Word/Excel/PDF generation
    - Simple output naming (project name based)
    - Pre-generation validation checklist (errors only)

    v2+ Deferred:
    - Advanced naming patterns with tokens
    - Document version tracking
    - Batch generation

    Example:
        vm = DocumentGenerationViewModel(generate_command)
        vm.set_project(project_id, entity_def_id, validation_result)
        if vm.can_generate:
            vm.generate_document(template_path, output_path, DocumentFormat.WORD)
    """

    def __init__(
        self,
        generate_document_command: GenerateDocumentCommand,
    ) -> None:
        """Initialize DocumentGenerationViewModel.

        Args:
            generate_document_command: Command for generating documents
        """
        super().__init__()
        self._generate_document_command = generate_document_command

        # Store IDs and DTOs, NOT domain objects
        self._project_id: Optional[str] = None
        self._entity_definition_id: Optional[str] = None
        self._validation_result: Optional[ValidationResultDTO] = None

        self._is_generating = False
        self._generation_progress = 0.0
        self._error_message: Optional[str] = None
        self._success_message: Optional[str] = None

    @property
    def is_generating(self) -> bool:
        """Check if document generation is in progress.

        Returns:
            True if generating
        """
        return self._is_generating

    @property
    def generation_progress(self) -> float:
        """Get generation progress.

        Returns:
            Progress value between 0.0 and 1.0
        """
        return self._generation_progress

    @property
    def error_message(self) -> Optional[str]:
        """Get current error message.

        Returns:
            Error message if any
        """
        return self._error_message

    @property
    def success_message(self) -> Optional[str]:
        """Get success message.

        Returns:
            Success message if any
        """
        return self._success_message

    @property
    def can_generate(self) -> bool:
        """Check if document can be generated.

        Returns:
            True if all requirements are met
        """
        if not self._project_id or not self._entity_definition_id:
            return False

        # v1: Only check if there are no validation errors
        if self._validation_result and not self._validation_result.is_valid:
            return False

        return True

    @property
    def validation_errors(self) -> list[str]:
        """Get validation error messages.

        Returns:
            List of validation error messages
        """
        if not self._validation_result:
            return []

        return [error.message for error in self._validation_result.errors]

    def set_project(
        self,
        project_id: str,
        entity_definition_id: str,
        validation_result: ValidationResultDTO,
    ) -> None:
        """Set current project for generation.

        Args:
            project_id: Project ID (string)
            entity_definition_id: Entity definition ID (string)
            validation_result: Current validation result DTO
        """
        self._project_id = project_id
        self._entity_definition_id = entity_definition_id
        self._validation_result = validation_result

        self.notify_change("can_generate")
        self.notify_change("validation_errors")

    def generate_document(
        self,
        template_path: Path,
        output_path: Path,
        document_format: DocumentFormat,
    ) -> bool:
        """Generate document.

        Args:
            template_path: Path to template file
            output_path: Path for output file
            document_format: Format to generate (Word, Excel, PDF)

        Returns:
            True if generation succeeded
        """
        if not self.can_generate:
            self._error_message = "Cannot generate: validation errors exist"
            self.notify_change("error_message")
            return False

        if not self._project_id:
            self._error_message = "No project set"
            self.notify_change("error_message")
            return False

        self._is_generating = True
        self._generation_progress = 0.0
        self._error_message = None
        self._success_message = None

        self.notify_change("is_generating")
        self.notify_change("generation_progress")
        self.notify_change("error_message")
        self.notify_change("success_message")

        try:
            # Convert string ID to typed ID for command
            project_id = ProjectId(self._project_id)

            # v1: Simple generation without progress tracking
            result = self._generate_document_command.execute(
                project_id=project_id,
                template_path=template_path,
                output_path=output_path,
                format=document_format,
            )

            if isinstance(result, Success):
                self._generation_progress = 1.0
                self._success_message = f"Document generated successfully: {output_path}"
                self.notify_change("generation_progress")
                self.notify_change("success_message")
                return True
            else:
                self._error_message = f"Generation failed: {result.error}"
                self.notify_change("error_message")
                return False

        except Exception as e:
            self._error_message = f"Error during generation: {str(e)}"
            self.notify_change("error_message")
            return False

        finally:
            self._is_generating = False
            self.notify_change("is_generating")

    def clear_messages(self) -> None:
        """Clear all messages."""
        self._error_message = None
        self._success_message = None
        self.notify_change("error_message")
        self.notify_change("success_message")

    def dispose(self) -> None:
        """Clean up resources."""
        super().dispose()
        self._project_id = None
        self._entity_definition_id = None
        self._validation_result = None

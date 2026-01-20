"""ViewModel for Document Generation."""

from pathlib import Path
from typing import Optional

from doc_helper.application.commands.generate_document_command import (
    GenerateDocumentCommand,
)
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.domain.project.project import Project
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.validation.validation_result import ValidationResult
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
        vm.set_project(project, entity_def)
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

        self._project: Optional[Project] = None
        self._entity_definition: Optional[EntityDefinition] = None
        self._validation_result: Optional[ValidationResult] = None

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
        if not self._project or not self._entity_definition:
            return False

        # v1: Only check if there are no validation errors
        if self._validation_result and self._validation_result.is_invalid():
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
        project: Project,
        entity_definition: EntityDefinition,
        validation_result: ValidationResult,
    ) -> None:
        """Set current project for generation.

        Args:
            project: Project to generate document for
            entity_definition: Entity definition
            validation_result: Current validation result
        """
        self._project = project
        self._entity_definition = entity_definition
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

        if not self._project:
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
            # v1: Simple generation without progress tracking
            result = self._generate_document_command.execute(
                project=self._project,
                template_path=template_path,
                output_path=output_path,
                document_format=document_format,
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
        self._project = None
        self._entity_definition = None
        self._validation_result = None

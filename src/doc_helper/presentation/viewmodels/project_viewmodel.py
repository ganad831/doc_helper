"""ViewModel for Project management.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md):
- Presentation layer uses DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary
- Simple IDs (ProjectId, FieldDefinitionId) can cross boundaries
"""

from typing import Any, Optional

from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.commands.update_field_command import UpdateFieldCommand
from doc_helper.application.dto import (
    EntityDefinitionDTO,
    EvaluationResultDTO,
    ProjectDTO,
    ValidationErrorDTO,
    ValidationResultDTO,
)
from doc_helper.application.mappers import EvaluationResultMapper, ValidationMapper
from doc_helper.application.queries.get_project_query import GetProjectQuery
from doc_helper.application.services.control_service import ControlService
from doc_helper.application.services.formula_service import FormulaService
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


class ProjectViewModel(BaseViewModel):
    """ViewModel for Project management.

    Coordinates project editing, validation, formulas, and controls.

    Responsibilities:
    - Load and save projects
    - Update field values
    - Trigger formula evaluation
    - Trigger control rule evaluation
    - Track unsaved changes
    - Provide validation status

    NOTE: This ViewModel stores DTOs, not domain objects.
    Domain objects are handled internally by commands/queries.

    Example:
        vm = ProjectViewModel(services...)
        vm.load_project(project_id, entity_definition_dto)
        vm.update_field(field_id, new_value)
        vm.save_project()
    """

    def __init__(
        self,
        get_project_query: GetProjectQuery,
        save_project_command: SaveProjectCommand,
        update_field_command: UpdateFieldCommand,
        validation_service: ValidationService,
        formula_service: FormulaService,
        control_service: ControlService,
    ) -> None:
        """Initialize ProjectViewModel.

        Args:
            get_project_query: Query for loading projects
            save_project_command: Command for saving projects
            update_field_command: Command for updating field values
            validation_service: Service for validation
            formula_service: Service for formula evaluation
            control_service: Service for control rule evaluation
        """
        super().__init__()
        self._get_project_query = get_project_query
        self._save_project_command = save_project_command
        self._update_field_command = update_field_command
        self._validation_service = validation_service
        self._formula_service = formula_service
        self._control_service = control_service

        # Store IDs and DTOs, NOT domain objects
        self._project_id: Optional[str] = None
        self._project_dto: Optional[ProjectDTO] = None
        self._entity_definition_dto: Optional[EntityDefinitionDTO] = None
        self._has_unsaved_changes = False
        self._is_loading = False
        self._error_message: Optional[str] = None

    @property
    def project_id(self) -> Optional[str]:
        """Get current project ID.

        Returns:
            Project ID as string or None
        """
        return self._project_id

    @property
    def current_project(self) -> Optional[ProjectDTO]:
        """Get currently loaded project DTO.

        Returns:
            Current ProjectDTO or None
        """
        return self._project_dto

    @property
    def entity_definition(self) -> Optional[EntityDefinitionDTO]:
        """Get entity definition DTO for current project.

        Returns:
            EntityDefinitionDTO or None
        """
        return self._entity_definition_dto

    @property
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes.

        Returns:
            True if project has unsaved changes
        """
        return self._has_unsaved_changes

    @property
    def is_loading(self) -> bool:
        """Check if project is being loaded.

        Returns:
            True if loading
        """
        return self._is_loading

    @property
    def error_message(self) -> Optional[str]:
        """Get current error message.

        Returns:
            Error message if any
        """
        return self._error_message

    @property
    def project_name(self) -> str:
        """Get current project name.

        Returns:
            Project name or empty string
        """
        return self._project_dto.name if self._project_dto else ""

    def load_project(
        self,
        project_id: ProjectId,
        entity_definition: EntityDefinitionDTO,
    ) -> bool:
        """Load a project.

        Args:
            project_id: ID of project to load
            entity_definition: Entity definition DTO for the project

        Returns:
            True if loaded successfully
        """
        self._is_loading = True
        self._error_message = None
        self.notify_change("is_loading")
        self.notify_change("error_message")

        try:
            result = self._get_project_query.execute(project_id)

            if isinstance(result, Success):
                project_dto = result.value
                if project_dto is None:
                    self._error_message = f"Project not found: {project_id}"
                    return False

                # Store IDs and DTOs
                self._project_id = str(project_id.value)
                self._project_dto = project_dto
                self._entity_definition_dto = entity_definition
                self._has_unsaved_changes = False

                self.notify_change("project_id")
                self.notify_change("current_project")
                self.notify_change("entity_definition")
                self.notify_change("has_unsaved_changes")
                self.notify_change("project_name")

                return True
            else:
                self._error_message = f"Failed to load project: {result.error}"
                return False

        except Exception as e:
            self._error_message = f"Error loading project: {str(e)}"
            return False

        finally:
            self._is_loading = False
            self.notify_change("is_loading")
            self.notify_change("error_message")

    def update_field(
        self,
        field_id: FieldDefinitionId,
        value: Any,
    ) -> bool:
        """Update a field value.

        Args:
            field_id: Field to update
            value: New value

        Returns:
            True if updated successfully
        """
        if not self._project_id:
            self._error_message = "No project loaded"
            self.notify_change("error_message")
            return False

        try:
            # Convert string ID to typed ID
            project_id = ProjectId(self._project_id)

            result = self._update_field_command.execute(
                project_id=project_id,
                field_id=field_id,
                value=value,
            )

            if isinstance(result, Success):
                # Reload project DTO to get updated state
                reload_result = self._get_project_query.execute(project_id)
                if isinstance(reload_result, Success) and reload_result.value:
                    self._project_dto = reload_result.value

                self._has_unsaved_changes = True
                self.notify_change("current_project")
                self.notify_change("has_unsaved_changes")
                return True
            else:
                self._error_message = f"Failed to update field: {result.error}"
                self.notify_change("error_message")
                return False

        except Exception as e:
            self._error_message = f"Error updating field: {str(e)}"
            self.notify_change("error_message")
            return False

    def save_project(self) -> bool:
        """Save current project.

        Returns:
            True if saved successfully
        """
        if not self._project_id:
            self._error_message = "No project loaded"
            self.notify_change("error_message")
            return False

        try:
            # Convert string ID to typed ID
            project_id = ProjectId(self._project_id)

            result = self._save_project_command.execute(project_id)

            if isinstance(result, Success):
                self._has_unsaved_changes = False
                self._error_message = None
                self.notify_change("has_unsaved_changes")
                self.notify_change("error_message")
                return True
            else:
                self._error_message = f"Failed to save project: {result.error}"
                self.notify_change("error_message")
                return False

        except Exception as e:
            self._error_message = f"Error saving project: {str(e)}"
            self.notify_change("error_message")
            return False

    def validate_project(self) -> ValidationResultDTO:
        """Validate current project.

        Returns:
            ValidationResultDTO with errors
        """
        if not self._project_id or not self._entity_definition_dto:
            return ValidationResultDTO(
                is_valid=False,
                errors=(
                    ValidationErrorDTO(
                        field_id=None, field_path="", message="No project loaded"
                    ),
                ),
            )

        # Convert string ID to typed ID and call service
        project_id = ProjectId(self._project_id)

        # NOTE: validation_service needs method to validate by project_id
        # For now, the service may need updating
        result = self._validation_service.validate_by_project_id(project_id)

        if isinstance(result, Failure):
            return ValidationResultDTO(
                is_valid=False,
                errors=(
                    ValidationErrorDTO(
                        field_id=None,
                        field_path="",
                        message=f"Validation failed: {result.error}",
                    ),
                ),
            )

        # Map domain result to DTO
        return ValidationMapper.to_dto(result.value)

    def evaluate_controls(self) -> Optional[EvaluationResultDTO]:
        """Evaluate control rules for current project.

        Returns:
            EvaluationResultDTO if successful, None otherwise
        """
        if not self._project_id or not self._entity_definition_dto:
            return None

        # Convert string ID to typed ID
        project_id = ProjectId(self._project_id)

        # NOTE: control_service needs method to evaluate by project_id
        # For now, the service may need updating
        result = self._control_service.evaluate_by_project_id(project_id)

        if isinstance(result, Success):
            # Map domain result to DTO
            return EvaluationResultMapper.to_dto(result.value)
        return None

    def clear_error(self) -> None:
        """Clear current error message."""
        self._error_message = None
        self.notify_change("error_message")

    def dispose(self) -> None:
        """Clean up resources."""
        super().dispose()
        self._project_id = None
        self._project_dto = None
        self._entity_definition_dto = None

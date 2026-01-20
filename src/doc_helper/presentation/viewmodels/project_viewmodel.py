"""ViewModel for Project management."""

from typing import Any, Optional

from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.commands.update_field_command import UpdateFieldCommand
from doc_helper.application.queries.get_project_query import GetProjectQuery
from doc_helper.application.services.control_service import ControlService
from doc_helper.application.services.formula_service import FormulaService
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.control.effect_evaluator import EvaluationResult
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.schema_ids import FieldDefinitionId
from doc_helper.domain.validation.validation_result import ValidationResult
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

    Example:
        vm = ProjectViewModel(services...)
        vm.load_project(project_id)
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

        self._current_project: Optional[Project] = None
        self._entity_definition: Optional[EntityDefinition] = None
        self._has_unsaved_changes = False
        self._is_loading = False
        self._error_message: Optional[str] = None

    @property
    def current_project(self) -> Optional[Project]:
        """Get currently loaded project.

        Returns:
            Current Project or None
        """
        return self._current_project

    @property
    def entity_definition(self) -> Optional[EntityDefinition]:
        """Get entity definition for current project.

        Returns:
            EntityDefinition or None
        """
        return self._entity_definition

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
        return self._current_project.name if self._current_project else ""

    def load_project(
        self,
        project_id: ProjectId,
        entity_definition: EntityDefinition,
    ) -> bool:
        """Load a project.

        Args:
            project_id: ID of project to load
            entity_definition: Entity definition for the project

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
                project = result.value
                if project is None:
                    self._error_message = f"Project not found: {project_id}"
                    return False

                self._current_project = project
                self._entity_definition = entity_definition
                self._has_unsaved_changes = False

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
        if not self._current_project:
            self._error_message = "No project loaded"
            self.notify_change("error_message")
            return False

        try:
            result = self._update_field_command.execute(
                project=self._current_project,
                field_id=field_id,
                value=value,
            )

            if isinstance(result, Success):
                # Note: update_field_command modifies project in place
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
        if not self._current_project:
            self._error_message = "No project loaded"
            self.notify_change("error_message")
            return False

        try:
            result = self._save_project_command.execute(self._current_project)

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

    def validate_project(self) -> ValidationResult:
        """Validate current project.

        Returns:
            ValidationResult with errors
        """
        if not self._current_project or not self._entity_definition:
            from doc_helper.domain.validation.validation_error import ValidationError
            return ValidationResult(
                errors=(ValidationError(field_path="", message="No project loaded"),)
            )

        return self._validation_service.validate_project(
            self._current_project,
            self._entity_definition,
        )

    def evaluate_controls(self) -> Optional[EvaluationResult]:
        """Evaluate control rules for current project.

        Returns:
            EvaluationResult if successful, None otherwise
        """
        if not self._current_project or not self._entity_definition:
            return None

        result = self._control_service.evaluate_controls(
            self._current_project,
            self._entity_definition,
        )

        if isinstance(result, Success):
            return result.value
        return None

    def clear_error(self) -> None:
        """Clear current error message."""
        self._error_message = None
        self.notify_change("error_message")

    def dispose(self) -> None:
        """Clean up resources."""
        super().dispose()
        self._current_project = None
        self._entity_definition = None

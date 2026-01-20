"""Command for updating a field value in a project."""

from typing import Any

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class UpdateFieldCommand:
    """Command to update a field value in a project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands modify state and return Result[None, str]
    - Load-modify-save pattern for aggregates

    Example:
        command = UpdateFieldCommand(project_repository=repo)
        result = command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("site_location"),
            value="123 Main St"
        )
        if isinstance(result, Success):
            print("Field updated")
    """

    def __init__(self, project_repository: IProjectRepository) -> None:
        """Initialize command.

        Args:
            project_repository: Repository for persisting projects
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        self._project_repository = project_repository

    def execute(
        self,
        project_id: ProjectId,
        field_id: FieldDefinitionId,
        value: Any,
    ) -> Result[None, str]:
        """Execute update field command.

        Args:
            project_id: Project to update
            field_id: Field to update
            value: New field value

        Returns:
            Success(None) if updated, Failure(error) otherwise
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")
        if not isinstance(field_id, FieldDefinitionId):
            return Failure("field_id must be a FieldDefinitionId")

        # Load project
        load_result = self._project_repository.get_by_id(project_id)
        if isinstance(load_result, Failure):
            return Failure(f"Failed to load project: {load_result.error}")

        project = load_result.value
        if project is None:
            return Failure(f"Project not found: {project_id.value}")

        # Update field value
        project.set_field_value(field_id, value)

        # Save project
        save_result = self._project_repository.save(project)
        if isinstance(save_result, Failure):
            return Failure(f"Failed to save project: {save_result.error}")

        return Success(None)

"""Command for creating a new project."""

from typing import Optional
from uuid import uuid4

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId


class CreateProjectCommand:
    """Command to create a new project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands modify state and return Result[None, str]
    - CQRS pattern: commands don't return data (use queries for that)

    Example:
        command = CreateProjectCommand(project_repository=repo)
        result = command.execute(
            name="New Soil Investigation",
            entity_definition_id=EntityDefinitionId("project")
        )
        if isinstance(result, Success):
            print("Project created")
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
        name: str,
        entity_definition_id: EntityDefinitionId,
        description: Optional[str] = None,
    ) -> Result[ProjectId, str]:
        """Execute create project command.

        Args:
            name: Project name
            entity_definition_id: Entity definition for the project
            description: Optional project description

        Returns:
            Success(project_id) if created, Failure(error) otherwise
        """
        if not isinstance(name, str):
            return Failure("name must be a string")
        if not name.strip():
            return Failure("name cannot be empty")
        if not isinstance(entity_definition_id, EntityDefinitionId):
            return Failure("entity_definition_id must be an EntityDefinitionId")

        # Create new project
        project_id = ProjectId(uuid4())
        project = Project(
            id=project_id,
            name=name,
            entity_definition_id=entity_definition_id,
            field_values={},
            description=description,
        )

        # Save project
        save_result = self._project_repository.save(project)
        if isinstance(save_result, Failure):
            return Failure(f"Failed to create project: {save_result.error}")

        return Success(project_id)

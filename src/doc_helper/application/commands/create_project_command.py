"""Command for creating a new project.

v2 PHASE 3: AppType-aware project lifecycle enforcement.
Projects must be associated with a valid, registered AppType.
"""

from typing import Optional
from uuid import uuid4

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.platform.registry.interfaces import IAppTypeRegistry


class CreateProjectCommand:
    """Command to create a new project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands modify state and return Result[None, str]
    - CQRS pattern: commands don't return data (use queries for that)

    v2 PHASE 3 (AGENT_RULES.md Section 16):
    - Validates that app_type_id exists in registry before creation
    - Returns clear error if AppType not found or invalid
    - Enforces AppType as first-class invariant of project lifecycle

    Example:
        command = CreateProjectCommand(
            project_repository=repo,
            app_type_registry=registry
        )
        result = command.execute(
            name="New Soil Investigation",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("project")
        )
        if isinstance(result, Success):
            print("Project created")
    """

    # Default app_type_id for v1 compatibility
    DEFAULT_APP_TYPE_ID = "soil_investigation"

    def __init__(
        self,
        project_repository: IProjectRepository,
        app_type_registry: IAppTypeRegistry,
    ) -> None:
        """Initialize command.

        Args:
            project_repository: Repository for persisting projects
            app_type_registry: Registry for validating AppType existence
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        if not isinstance(app_type_registry, IAppTypeRegistry):
            raise TypeError("app_type_registry must implement IAppTypeRegistry")
        self._project_repository = project_repository
        self._app_type_registry = app_type_registry

    def execute(
        self,
        name: str,
        entity_definition_id: EntityDefinitionId,
        description: Optional[str] = None,
        app_type_id: Optional[str] = None,
    ) -> Result[ProjectId, str]:
        """Execute create project command.

        v2 PHASE 3: Validates AppType existence before creating project.

        Args:
            name: Project name
            entity_definition_id: Entity definition for the project
            description: Optional project description
            app_type_id: AppType identifier (defaults to "soil_investigation" for v1)

        Returns:
            Success(project_id) if created, Failure(error) otherwise

        Validation Failures:
            - "name must be a string" - Invalid name type
            - "name cannot be empty" - Empty name
            - "entity_definition_id must be an EntityDefinitionId" - Invalid entity ID
            - "AppType '{id}' not found. Available: ..." - AppType not registered
            - "Failed to create project: ..." - Repository save failed
        """
        if not isinstance(name, str):
            return Failure("name must be a string")
        if not name.strip():
            return Failure("name cannot be empty")
        if not isinstance(entity_definition_id, EntityDefinitionId):
            return Failure("entity_definition_id must be an EntityDefinitionId")

        # Use default app_type_id if not provided (v1 compatibility)
        effective_app_type_id = app_type_id or self.DEFAULT_APP_TYPE_ID

        # v2 PHASE 3: Validate AppType exists in registry
        if not self._app_type_registry.exists(effective_app_type_id):
            available = self._app_type_registry.list_app_type_ids()
            available_str = ", ".join(sorted(available)) if available else "none"
            return Failure(
                f"AppType '{effective_app_type_id}' not found. "
                f"Available AppTypes: {available_str}"
            )

        # Create new project
        project_id = ProjectId(uuid4())
        project = Project(
            id=project_id,
            name=name,
            app_type_id=effective_app_type_id,
            entity_definition_id=entity_definition_id,
            field_values={},
            description=description,
        )

        # Save project
        save_result = self._project_repository.save(project)
        if isinstance(save_result, Failure):
            return Failure(f"Failed to create project: {save_result.error}")

        return Success(project_id)

    def execute_with_str_ids(
        self,
        name: str,
        entity_definition_id_str: str,
        description: Optional[str] = None,
        app_type_id: Optional[str] = None,
    ) -> Result[ProjectId, str]:
        """Execute create project command with string IDs.

        PHASE 6C: String-accepting variant for Presentation layer.
        Converts string to domain ID internally.

        Args:
            name: Project name
            entity_definition_id_str: Entity definition ID as string
            description: Optional project description
            app_type_id: AppType identifier (defaults to "soil_investigation" for v1)

        Returns:
            Success(project_id) if created, Failure(error) otherwise
        """
        if not entity_definition_id_str:
            return Failure("entity_definition_id cannot be empty")

        # Convert string to domain ID (Application layer responsibility)
        entity_definition_id = EntityDefinitionId(entity_definition_id_str)

        # Delegate to main execute method
        return self.execute(
            name=name,
            entity_definition_id=entity_definition_id,
            description=description,
            app_type_id=app_type_id,
        )

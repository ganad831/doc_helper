"""Create Entity Command (Phase 2 Step 2).

Command for creating new entity definitions in the schema.
"""

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class CreateEntityCommand:
    """Command to create a new entity definition.

    Phase 2 Step 2 Scope:
    - Create new entities with basic metadata
    - Entity starts with empty fields dict
    - Fields added separately via AddFieldCommand

    NOT in Step 2:
    - Editing existing entities
    - Deleting entities
    - Creating relationships
    - Creating validation rules

    Usage:
        command = CreateEntityCommand(schema_repository)
        result = command.execute(
            entity_id="soil_sample",
            name_key="entity.soil_sample",
            description_key="entity.soil_sample.description",
            is_root_entity=False,
            parent_entity_id="borehole"
        )
    """

    def __init__(self, schema_repository: ISchemaRepository) -> None:
        """Initialize command.

        Args:
            schema_repository: Repository for schema persistence
        """
        self._schema_repository = schema_repository

    def execute(
        self,
        entity_id: str,
        name_key: str,
        description_key: str = None,
        is_root_entity: bool = False,
        parent_entity_id: str = None,
    ) -> Result[EntityDefinitionId, str]:
        """Execute command to create entity.

        Args:
            entity_id: Unique identifier for entity (e.g., "soil_sample")
            name_key: Translation key for entity name (e.g., "entity.soil_sample")
            description_key: Translation key for description (optional)
            is_root_entity: Whether this is a root entity (default: False)
            parent_entity_id: Parent entity ID for child entities (optional)

        Returns:
            Result containing created EntityDefinitionId or error message

        Validation:
            - entity_id must be unique
            - name_key must be provided
            - If is_root_entity=True, parent_entity_id must be None
            - If is_root_entity=False, parent_entity_id should be provided
        """
        # Validate inputs
        if not entity_id:
            return Failure("entity_id is required")

        if not name_key:
            return Failure("name_key is required")

        # Validate root entity constraints
        if is_root_entity and parent_entity_id:
            return Failure("Root entity cannot have a parent")

        # Check if entity already exists
        entity_definition_id = EntityDefinitionId(entity_id)
        if self._schema_repository.exists(entity_definition_id):
            return Failure(f"Entity '{entity_id}' already exists")

        # Create EntityDefinition
        try:
            entity = EntityDefinition(
                id=entity_definition_id,
                name_key=TranslationKey(name_key),
                description_key=TranslationKey(description_key) if description_key else None,
                fields={},  # Empty fields dict - fields added separately
                is_root_entity=is_root_entity,
                parent_entity_id=EntityDefinitionId(parent_entity_id) if parent_entity_id else None,
            )
        except (ValueError, TypeError) as e:
            return Failure(f"Invalid entity data: {e}")

        # Save to repository
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return Failure(f"Failed to save entity: {save_result.error}")

        return Success(entity_definition_id)

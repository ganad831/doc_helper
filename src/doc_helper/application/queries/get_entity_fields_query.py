"""Query for retrieving entity field definitions."""

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class GetEntityFieldsQuery:
    """Query to retrieve field definitions for an entity.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return data and don't modify state

    Example:
        query = GetEntityFieldsQuery(schema_repository=repo)
        result = query.execute(entity_id=EntityDefinitionId("project"))
        if isinstance(result, Success):
            fields = result.value
    """

    def __init__(self, schema_repository: ISchemaRepository) -> None:
        """Initialize query.

        Args:
            schema_repository: Repository for loading schema definitions
        """
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        self._schema_repository = schema_repository

    def execute(
        self, entity_id: EntityDefinitionId
    ) -> Result[dict[FieldDefinitionId, FieldDefinition], str]:
        """Execute get entity fields query.

        Args:
            entity_id: Entity ID to get fields for

        Returns:
            Success(dict of field_id -> FieldDefinition) if successful,
            Failure(error) otherwise
        """
        if not isinstance(entity_id, EntityDefinitionId):
            return Failure("entity_id must be an EntityDefinitionId")

        # Load entity definition
        entity_result = self._schema_repository.get_by_id(entity_id)
        if isinstance(entity_result, Failure):
            return Failure(f"Failed to load entity: {entity_result.error}")

        entity = entity_result.value
        return Success(entity.fields)


class GetEntityDefinitionQuery:
    """Query to retrieve an entity definition.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return data and don't modify state

    Example:
        query = GetEntityDefinitionQuery(schema_repository=repo)
        result = query.execute(entity_id=EntityDefinitionId("project"))
        if isinstance(result, Success):
            entity_def = result.value
    """

    def __init__(self, schema_repository: ISchemaRepository) -> None:
        """Initialize query.

        Args:
            schema_repository: Repository for loading schema definitions
        """
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        self._schema_repository = schema_repository

    def execute(
        self, entity_id: EntityDefinitionId
    ) -> Result[EntityDefinition, str]:
        """Execute get entity definition query.

        Args:
            entity_id: Entity ID to retrieve

        Returns:
            Success(EntityDefinition) if found, Failure(error) otherwise
        """
        if not isinstance(entity_id, EntityDefinitionId):
            return Failure("entity_id must be an EntityDefinitionId")

        return self._schema_repository.get_by_id(entity_id)


class GetRootEntityQuery:
    """Query to retrieve the root entity definition.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return data and don't modify state

    Example:
        query = GetRootEntityQuery(schema_repository=repo)
        result = query.execute()
        if isinstance(result, Success):
            root_entity = result.value
    """

    def __init__(self, schema_repository: ISchemaRepository) -> None:
        """Initialize query.

        Args:
            schema_repository: Repository for loading schema definitions
        """
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        self._schema_repository = schema_repository

    def execute(self) -> Result[EntityDefinition, str]:
        """Execute get root entity query.

        Returns:
            Success(EntityDefinition) if successful, Failure(error) otherwise
        """
        return self._schema_repository.get_root_entity()

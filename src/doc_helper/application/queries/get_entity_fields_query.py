"""Query for retrieving entity field definitions.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- Queries return DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary
- Use mappers to convert Domain → DTO
"""

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.common.translation import ITranslationService
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.application.dto import FieldDefinitionDTO, EntityDefinitionDTO
from doc_helper.application.mappers import FieldDefinitionMapper, EntityDefinitionMapper


class GetEntityFieldsQuery:
    """Query to retrieve field definitions for an entity.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return DTOs, not domain objects

    Example:
        query = GetEntityFieldsQuery(schema_repository=repo, translation_service=ts)
        result = query.execute(entity_id=EntityDefinitionId("project"))
        if isinstance(result, Success):
            field_dtos = result.value  # Tuple of FieldDefinitionDTO
    """

    def __init__(
        self,
        schema_repository: ISchemaRepository,
        translation_service: ITranslationService,
    ) -> None:
        """Initialize query.

        Args:
            schema_repository: Repository for loading schema definitions
            translation_service: Service for translating i18n keys
        """
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        self._schema_repository = schema_repository
        self._field_mapper = FieldDefinitionMapper(translation_service)

    def execute(
        self, entity_id: EntityDefinitionId
    ) -> Result[tuple[FieldDefinitionDTO, ...], str]:
        """Execute get entity fields query.

        Args:
            entity_id: Entity ID to get fields for

        Returns:
            Success(tuple of FieldDefinitionDTO) if successful,
            Failure(error) otherwise
        """
        if not isinstance(entity_id, EntityDefinitionId):
            return Failure("entity_id must be an EntityDefinitionId")

        # Load entity definition
        entity_result = self._schema_repository.get_by_id(entity_id)
        if isinstance(entity_result, Failure):
            return Failure(f"Failed to load entity: {entity_result.error}")

        entity = entity_result.value

        # Map to DTOs before returning
        field_dtos = tuple(
            self._field_mapper.to_dto(field_def)
            for field_def in entity.get_all_fields()
        )
        return Success(field_dtos)


class GetEntityDefinitionQuery:
    """Query to retrieve an entity definition.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return DTOs, not domain objects

    Example:
        query = GetEntityDefinitionQuery(schema_repository=repo, translation_service=ts)
        result = query.execute(entity_id=EntityDefinitionId("project"))
        if isinstance(result, Success):
            entity_dto = result.value  # Returns EntityDefinitionDTO
    """

    def __init__(
        self,
        schema_repository: ISchemaRepository,
        translation_service: ITranslationService,
    ) -> None:
        """Initialize query.

        Args:
            schema_repository: Repository for loading schema definitions
            translation_service: Service for translating i18n keys
        """
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        self._schema_repository = schema_repository
        self._entity_mapper = EntityDefinitionMapper(translation_service)

    def execute(
        self, entity_id: EntityDefinitionId
    ) -> Result["EntityDefinitionDTO", str]:
        """Execute get entity definition query.

        Args:
            entity_id: Entity ID to retrieve

        Returns:
            Success(EntityDefinitionDTO) if found, Failure(error) otherwise
        """
        if not isinstance(entity_id, EntityDefinitionId):
            return Failure("entity_id must be an EntityDefinitionId")

        result = self._schema_repository.get_by_id(entity_id)
        if isinstance(result, Failure):
            return result

        # Map to DTO before returning
        return Success(self._entity_mapper.to_dto(result.value))


class GetRootEntityQuery:
    """Query to retrieve the root entity definition.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return DTOs, not domain objects

    Example:
        query = GetRootEntityQuery(schema_repository=repo, translation_service=ts)
        result = query.execute()
        if isinstance(result, Success):
            root_entity_dto = result.value  # Returns EntityDefinitionDTO
    """

    def __init__(
        self,
        schema_repository: ISchemaRepository,
        translation_service: ITranslationService,
    ) -> None:
        """Initialize query.

        Args:
            schema_repository: Repository for loading schema definitions
            translation_service: Service for translating i18n keys
        """
        if not isinstance(schema_repository, ISchemaRepository):
            raise TypeError("schema_repository must implement ISchemaRepository")
        self._schema_repository = schema_repository
        self._entity_mapper = EntityDefinitionMapper(translation_service)

    def execute(self) -> Result[EntityDefinitionDTO, str]:
        """Execute get root entity query.

        Returns:
            Success(EntityDefinitionDTO) if successful, Failure(error) otherwise
        """
        result = self._schema_repository.get_root_entity()
        if isinstance(result, Failure):
            return result

        # Map to DTO before returning
        return Success(self._entity_mapper.to_dto(result.value))

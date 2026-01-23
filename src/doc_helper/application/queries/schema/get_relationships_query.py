"""Get Relationships Query (Phase 6A - ADR-022).

Query for retrieving relationship definitions from the schema.
"""

from dataclasses import dataclass
from typing import Optional

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.relationship_repository import IRelationshipRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId


@dataclass(frozen=True)
class RelationshipDTO:
    """Data Transfer Object for relationship information.

    Provides a simple, serializable representation of a relationship
    for use in application and presentation layers.
    """

    id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    name_key: str
    description_key: Optional[str]
    inverse_name_key: Optional[str]


class GetRelationshipsQuery:
    """Query to retrieve relationship definitions.

    ADR-022 Behavior:
    - If entity_id provided: return relationships involving that entity
    - If entity_id omitted: return all relationships

    Usage:
        query = GetRelationshipsQuery(relationship_repository)

        # Get all relationships
        result = query.execute()

        # Get relationships for a specific entity
        result = query.execute(entity_id="project")

        if result.is_success():
            for relationship_dto in result.value:
                print(f"{relationship_dto.source_entity_id} -> {relationship_dto.target_entity_id}")
    """

    def __init__(self, relationship_repository: IRelationshipRepository) -> None:
        """Initialize query.

        Args:
            relationship_repository: Repository for reading relationships
        """
        self._relationship_repository = relationship_repository

    def execute(
        self,
        entity_id: Optional[str] = None,
    ) -> Result[tuple[RelationshipDTO, ...], str]:
        """Execute query to retrieve relationships.

        Args:
            entity_id: Optional entity ID to filter by.
                       If provided, returns relationships where entity is source OR target.
                       If omitted, returns all relationships.

        Returns:
            Result containing tuple of RelationshipDTO objects or error message
        """
        if entity_id:
            # Get relationships involving specific entity
            try:
                ent_id = EntityDefinitionId(entity_id)
            except ValueError as e:
                return Failure(f"Invalid entity_id: {e}")

            result = self._relationship_repository.get_by_entity(ent_id)
        else:
            # Get all relationships
            result = self._relationship_repository.get_all()

        if result.is_failure():
            return Failure(result.error)

        # Convert to DTOs
        relationships: tuple[RelationshipDefinition, ...] = result.value
        dtos = tuple(
            self._to_dto(relationship) for relationship in relationships
        )

        return Success(dtos)

    def execute_by_source(
        self,
        source_entity_id: str,
    ) -> Result[tuple[RelationshipDTO, ...], str]:
        """Get relationships where the given entity is the source.

        Args:
            source_entity_id: Source entity ID

        Returns:
            Result containing tuple of RelationshipDTO objects or error message
        """
        try:
            ent_id = EntityDefinitionId(source_entity_id)
        except ValueError as e:
            return Failure(f"Invalid source_entity_id: {e}")

        result = self._relationship_repository.get_by_source_entity(ent_id)

        if result.is_failure():
            return Failure(result.error)

        relationships: tuple[RelationshipDefinition, ...] = result.value
        dtos = tuple(
            self._to_dto(relationship) for relationship in relationships
        )

        return Success(dtos)

    def execute_by_target(
        self,
        target_entity_id: str,
    ) -> Result[tuple[RelationshipDTO, ...], str]:
        """Get relationships where the given entity is the target.

        Args:
            target_entity_id: Target entity ID

        Returns:
            Result containing tuple of RelationshipDTO objects or error message
        """
        try:
            ent_id = EntityDefinitionId(target_entity_id)
        except ValueError as e:
            return Failure(f"Invalid target_entity_id: {e}")

        result = self._relationship_repository.get_by_target_entity(ent_id)

        if result.is_failure():
            return Failure(result.error)

        relationships: tuple[RelationshipDefinition, ...] = result.value
        dtos = tuple(
            self._to_dto(relationship) for relationship in relationships
        )

        return Success(dtos)

    def _to_dto(self, relationship: RelationshipDefinition) -> RelationshipDTO:
        """Convert RelationshipDefinition to DTO.

        Args:
            relationship: Domain relationship definition

        Returns:
            RelationshipDTO for application/presentation use
        """
        return RelationshipDTO(
            id=str(relationship.id.value),
            source_entity_id=str(relationship.source_entity_id.value),
            target_entity_id=str(relationship.target_entity_id.value),
            relationship_type=relationship.relationship_type.value,
            name_key=relationship.name_key.key,
            description_key=(
                relationship.description_key.key
                if relationship.description_key
                else None
            ),
            inverse_name_key=(
                relationship.inverse_name_key.key
                if relationship.inverse_name_key
                else None
            ),
        )

"""Create Relationship Command (Phase 6A - ADR-022).

Command for creating new relationship definitions in the schema.
Follows ADD-ONLY semantics - relationships cannot be updated or deleted.
"""

from typing import Optional

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.relationship_repository import IRelationshipRepository
from doc_helper.domain.schema.relationship_type import RelationshipType
from doc_helper.domain.schema.schema_ids import (
    EntityDefinitionId,
    RelationshipDefinitionId,
)
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class CreateRelationshipCommand:
    """Command to create a new relationship definition.

    ADR-022 Compliance:
    - ADD-ONLY semantics (no update/delete)
    - Validates source and target entities exist
    - Validates relationship type is valid
    - Marks schema as modified (dirty flag) on success

    Preconditions:
        - Source entity must exist
        - Target entity must exist
        - Relationship ID must be unique
        - Relationship type must be valid (CONTAINS, REFERENCES, ASSOCIATES)

    Postconditions:
        - RelationshipDefinition persisted
        - Schema marked as modified (dirty flag)

    Usage:
        command = CreateRelationshipCommand(
            relationship_repository,
            schema_repository,
        )
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.project_boreholes",
            description_key="relationship.project_boreholes.description",
            inverse_name_key="relationship.borehole_project",
        )
    """

    def __init__(
        self,
        relationship_repository: IRelationshipRepository,
        schema_repository: ISchemaRepository,
    ) -> None:
        """Initialize command.

        Args:
            relationship_repository: Repository for relationship persistence
            schema_repository: Repository for entity validation
        """
        self._relationship_repository = relationship_repository
        self._schema_repository = schema_repository

    def execute(
        self,
        relationship_id: str,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        name_key: str,
        description_key: Optional[str] = None,
        inverse_name_key: Optional[str] = None,
    ) -> Result[RelationshipDefinitionId, str]:
        """Execute command to create relationship.

        Args:
            relationship_id: Unique identifier for relationship
            source_entity_id: Entity where relationship originates
            target_entity_id: Entity where relationship points
            relationship_type: Type (CONTAINS, REFERENCES, ASSOCIATES)
            name_key: Translation key for relationship name
            description_key: Translation key for description (optional)
            inverse_name_key: Translation key for inverse name (optional)

        Returns:
            Result containing created RelationshipDefinitionId or error message

        Validation:
            - relationship_id must be unique
            - source_entity_id must exist
            - target_entity_id must exist
            - source and target must be different entities
            - relationship_type must be valid
            - name_key must be provided
        """
        # Validate required inputs
        if not relationship_id:
            return Failure("relationship_id is required")

        if not source_entity_id:
            return Failure("source_entity_id is required")

        if not target_entity_id:
            return Failure("target_entity_id is required")

        if not relationship_type:
            return Failure("relationship_type is required")

        if not name_key:
            return Failure("name_key is required")

        # Validate source and target are different
        if source_entity_id == target_entity_id:
            return Failure(
                f"Source and target entity must be different. Got: {source_entity_id}"
            )

        # Validate relationship type
        try:
            rel_type = RelationshipType(relationship_type)
        except ValueError:
            valid_types = ", ".join(t.value for t in RelationshipType)
            return Failure(
                f"Invalid relationship_type: '{relationship_type}'. "
                f"Must be one of: {valid_types}"
            )

        # Create strongly typed IDs
        try:
            rel_id = RelationshipDefinitionId(relationship_id)
        except ValueError as e:
            return Failure(f"Invalid relationship_id: {e}")

        try:
            source_id = EntityDefinitionId(source_entity_id)
        except ValueError as e:
            return Failure(f"Invalid source_entity_id: {e}")

        try:
            target_id = EntityDefinitionId(target_entity_id)
        except ValueError as e:
            return Failure(f"Invalid target_entity_id: {e}")

        # Check if relationship already exists
        if self._relationship_repository.exists(rel_id):
            return Failure(
                f"Relationship '{relationship_id}' already exists. "
                "Relationships are ADD-ONLY and cannot be updated."
            )

        # Validate source entity exists
        if not self._schema_repository.exists(source_id):
            return Failure(f"Source entity '{source_entity_id}' does not exist")

        # Validate target entity exists
        if not self._schema_repository.exists(target_id):
            return Failure(f"Target entity '{target_entity_id}' does not exist")

        # Create RelationshipDefinition
        try:
            relationship = RelationshipDefinition(
                id=rel_id,
                source_entity_id=source_id,
                target_entity_id=target_id,
                relationship_type=rel_type,
                name_key=TranslationKey(name_key),
                description_key=(
                    TranslationKey(description_key) if description_key else None
                ),
                inverse_name_key=(
                    TranslationKey(inverse_name_key) if inverse_name_key else None
                ),
            )
        except (ValueError, TypeError) as e:
            return Failure(f"Invalid relationship data: {e}")

        # Save to repository
        save_result = self._relationship_repository.save(relationship)
        if save_result.is_failure():
            return Failure(f"Failed to save relationship: {save_result.error}")

        return Success(rel_id)

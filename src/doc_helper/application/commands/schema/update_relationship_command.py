"""Update Relationship Command (Phase A4.2).

Command for updating relationship metadata in the schema.
DESIGN-TIME ONLY: Does not affect runtime behavior.

INVARIANTS:
- Relationships are design-time constructs
- Editing does NOT imply runtime behavior
- Source and target entity cannot be changed
- Only metadata fields can be updated (name_key, description_key, inverse_name_key)
- Deletion does NOT cascade (handled by separate command)
- Runtime semantics are deferred to later phases
"""

from typing import Optional

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.relationship_repository import IRelationshipRepository
from doc_helper.domain.schema.relationship_type import RelationshipType
from doc_helper.domain.schema.schema_ids import RelationshipDefinitionId


class UpdateRelationshipCommand:
    """Command to update relationship metadata (DESIGN-TIME ONLY).

    INVARIANT: Relationships are design-time constructs.
    - This command updates METADATA ONLY
    - Source entity ID cannot be changed
    - Target entity ID cannot be changed
    - Editing does NOT imply runtime behavior
    - Runtime semantics are deferred to later phases

    Preconditions:
        - Relationship must exist
        - source_entity_id in request must match existing relationship
        - target_entity_id in request must match existing relationship

    Postconditions:
        - Relationship metadata updated in repository
        - No cascade effects on fields or entities

    Usage:
        command = UpdateRelationshipCommand(relationship_repository)
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",  # Must match existing
            target_entity_id="borehole",  # Must match existing
            relationship_type="CONTAINS",
            name_key="relationship.project_boreholes.updated",
            description_key="relationship.project_boreholes.desc",
        )
    """

    def __init__(
        self,
        relationship_repository: IRelationshipRepository,
    ) -> None:
        """Initialize command.

        Args:
            relationship_repository: Repository for relationship persistence
        """
        self._relationship_repository = relationship_repository

    def execute(
        self,
        relationship_id: str,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        name_key: str,
        description_key: Optional[str] = None,
        inverse_name_key: Optional[str] = None,
    ) -> Result[None, str]:
        """Execute command to update relationship metadata.

        Args:
            relationship_id: ID of relationship to update (must exist)
            source_entity_id: Source entity (must match existing - cannot change)
            target_entity_id: Target entity (must match existing - cannot change)
            relationship_type: Type (CONTAINS, REFERENCES, ASSOCIATES)
            name_key: Updated translation key for relationship name
            description_key: Updated translation key for description (optional)
            inverse_name_key: Updated translation key for inverse name (optional)

        Returns:
            Result with None on success or error message

        Validation:
            - relationship_id must exist
            - source_entity_id must match existing relationship
            - target_entity_id must match existing relationship
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

        # Validate relationship type
        try:
            rel_type = RelationshipType(relationship_type)
        except ValueError:
            valid_types = ", ".join(t.value for t in RelationshipType)
            return Failure(
                f"Invalid relationship_type: '{relationship_type}'. "
                f"Must be one of: {valid_types}"
            )

        # Create strongly typed ID
        try:
            rel_id = RelationshipDefinitionId(relationship_id)
        except ValueError as e:
            return Failure(f"Invalid relationship_id: {e}")

        # Verify relationship exists
        if not self._relationship_repository.exists(rel_id):
            return Failure(f"Relationship '{relationship_id}' does not exist")

        # Get existing relationship to validate source/target match
        get_result = self._relationship_repository.get_by_id(rel_id)
        if get_result.is_failure():
            return Failure(f"Failed to load relationship: {get_result.error}")

        existing = get_result.value

        # Validate source entity matches (cannot change)
        if existing.source_entity_id.value != source_entity_id:
            return Failure(
                f"Cannot change source_entity_id from '{existing.source_entity_id.value}' "
                f"to '{source_entity_id}'. Delete and recreate instead."
            )

        # Validate target entity matches (cannot change)
        if existing.target_entity_id.value != target_entity_id:
            return Failure(
                f"Cannot change target_entity_id from '{existing.target_entity_id.value}' "
                f"to '{target_entity_id}'. Delete and recreate instead."
            )

        # Create updated RelationshipDefinition with new metadata
        try:
            updated_relationship = RelationshipDefinition(
                id=rel_id,
                source_entity_id=existing.source_entity_id,
                target_entity_id=existing.target_entity_id,
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

        # Update in repository
        update_result = self._relationship_repository.update(updated_relationship)
        if update_result.is_failure():
            return Failure(f"Failed to update relationship: {update_result.error}")

        return Success(None)

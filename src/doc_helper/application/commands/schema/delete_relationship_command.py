"""Delete Relationship Command (Phase A4.2).

Command for deleting relationship definitions from the schema.
DESIGN-TIME ONLY: Does not affect runtime behavior or cascade.

INVARIANTS:
- Relationships are design-time constructs
- Deletion does NOT cascade to fields
- Deletion does NOT cascade to entities
- Deletion does NOT modify other relationships
- Runtime semantics are deferred to later phases
"""

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.schema.relationship_repository import IRelationshipRepository
from doc_helper.domain.schema.schema_ids import RelationshipDefinitionId


class DeleteRelationshipCommand:
    """Command to delete a relationship definition (DESIGN-TIME ONLY).

    INVARIANT: Relationships are design-time constructs.
    - Deletion does NOT cascade to fields
    - Deletion does NOT cascade to entities
    - Deletion does NOT modify other relationships
    - Runtime semantics are deferred to later phases

    Preconditions:
        - Relationship must exist

    Postconditions:
        - Relationship removed from repository
        - No cascade effects on fields
        - No cascade effects on entities
        - No modifications to other relationships

    Usage:
        command = DeleteRelationshipCommand(relationship_repository)
        result = command.execute(relationship_id="project_contains_boreholes")
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
    ) -> Result[None, str]:
        """Execute command to delete relationship.

        INVARIANT: Deletion does NOT cascade.
        - Fields are NOT affected
        - Entities are NOT affected
        - Other relationships are NOT affected

        Args:
            relationship_id: ID of relationship to delete

        Returns:
            Result with None on success or error message

        Validation:
            - relationship_id must be provided
            - relationship must exist
        """
        # Validate required input
        if not relationship_id:
            return Failure("relationship_id is required")

        # Create strongly typed ID
        try:
            rel_id = RelationshipDefinitionId(relationship_id)
        except ValueError as e:
            return Failure(f"Invalid relationship_id: {e}")

        # Verify relationship exists
        if not self._relationship_repository.exists(rel_id):
            return Failure(f"Relationship '{relationship_id}' does not exist")

        # Delete from repository (no cascade - design-time only)
        delete_result = self._relationship_repository.delete(rel_id)
        if delete_result.is_failure():
            return Failure(f"Failed to delete relationship: {delete_result.error}")

        return Success(None)

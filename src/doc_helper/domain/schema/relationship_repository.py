"""Relationship repository interface (Phase 6A - ADR-022).

Domain-layer interface for relationship persistence.
Infrastructure layer will provide implementation.

ADR-022 DECISIONS:
- Interface defined in domain layer (dependency inversion)
- Implementation in infrastructure layer
- NO update method (ADD-ONLY semantics)
- NO delete method (ADD-ONLY semantics)
- Must validate entity references exist before save
"""

from abc import ABC, abstractmethod

from doc_helper.domain.common.result import Result
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.schema_ids import (
    EntityDefinitionId,
    RelationshipDefinitionId,
)


class IRelationshipRepository(ABC):
    """Interface for relationship persistence.

    This interface lives in the domain layer (dependency inversion).
    Implementation will be in infrastructure layer (SqliteRelationshipRepository).

    RULES (ADR-022):
    - Interface in domain, implementation in infrastructure
    - NO framework dependencies
    - Returns Result[T, E] for error handling
    - ADD-ONLY: No update or delete methods

    Usage:
        # In application layer:
        result = relationship_repo.get_by_id(
            RelationshipDefinitionId("project_contains_boreholes")
        )
        if result.is_success():
            relationship = result.value
            # Use relationship...

        # Get relationships for an entity
        result = relationship_repo.get_by_source_entity(
            EntityDefinitionId("project")
        )
        if result.is_success():
            relationships = result.value
            # Process relationships...
    """

    @abstractmethod
    def get_by_id(
        self, relationship_id: RelationshipDefinitionId
    ) -> Result[RelationshipDefinition, str]:
        """Get relationship definition by ID.

        Args:
            relationship_id: Relationship definition ID

        Returns:
            Result containing RelationshipDefinition or error message

        Example:
            result = repo.get_by_id(
                RelationshipDefinitionId("project_contains_boreholes")
            )
            if result.is_success():
                relationship = result.value
        """
        pass

    @abstractmethod
    def get_all(self) -> Result[tuple[RelationshipDefinition, ...], str]:
        """Get all relationship definitions.

        Returns:
            Result containing tuple of RelationshipDefinition objects or error

        Example:
            result = repo.get_all()
            if result.is_success():
                for relationship in result.value:
                    print(relationship.name_key)
        """
        pass

    @abstractmethod
    def get_by_source_entity(
        self, entity_id: EntityDefinitionId
    ) -> Result[tuple[RelationshipDefinition, ...], str]:
        """Get relationships where the given entity is the source.

        Args:
            entity_id: Source entity definition ID

        Returns:
            Result containing tuple of RelationshipDefinition objects or error

        Example:
            result = repo.get_by_source_entity(EntityDefinitionId("project"))
            if result.is_success():
                # All relationships originating from "project"
                relationships = result.value
        """
        pass

    @abstractmethod
    def get_by_target_entity(
        self, entity_id: EntityDefinitionId
    ) -> Result[tuple[RelationshipDefinition, ...], str]:
        """Get relationships where the given entity is the target.

        Args:
            entity_id: Target entity definition ID

        Returns:
            Result containing tuple of RelationshipDefinition objects or error

        Example:
            result = repo.get_by_target_entity(EntityDefinitionId("borehole"))
            if result.is_success():
                # All relationships pointing to "borehole"
                relationships = result.value
        """
        pass

    @abstractmethod
    def get_by_entity(
        self, entity_id: EntityDefinitionId
    ) -> Result[tuple[RelationshipDefinition, ...], str]:
        """Get all relationships involving the given entity (source or target).

        Args:
            entity_id: Entity definition ID

        Returns:
            Result containing tuple of RelationshipDefinition objects or error

        Example:
            result = repo.get_by_entity(EntityDefinitionId("borehole"))
            if result.is_success():
                # All relationships where borehole is source OR target
                relationships = result.value
        """
        pass

    @abstractmethod
    def exists(self, relationship_id: RelationshipDefinitionId) -> bool:
        """Check if relationship definition exists.

        Args:
            relationship_id: Relationship definition ID

        Returns:
            True if relationship exists

        Example:
            if repo.exists(RelationshipDefinitionId("project_contains_boreholes")):
                # Relationship exists
        """
        pass

    @abstractmethod
    def save(self, relationship: RelationshipDefinition) -> Result[None, str]:
        """Save new relationship definition (ADD-ONLY).

        This method ONLY creates new relationships. It does not update
        existing relationships (ADD-ONLY semantics per ADR-022).

        Args:
            relationship: Relationship definition to save

        Returns:
            Result with None on success or error message

        Validation (enforced by implementation):
            - Source entity must exist
            - Target entity must exist
            - Relationship ID must be unique
            - Relationship type must be valid

        Raises:
            - Failure if relationship already exists
            - Failure if source entity does not exist
            - Failure if target entity does not exist

        Example:
            result = repo.save(relationship_definition)
            if result.is_success():
                # Relationship saved successfully
        """
        pass

    # -------------------------------------------------------------------------
    # Design-Time Editing Operations (Phase A4.2)
    # -------------------------------------------------------------------------
    #
    # INVARIANT: Relationships are DESIGN-TIME constructs only.
    # These methods enable Schema Designer editing capabilities.
    # Editing does NOT imply runtime behavior.
    # Deletion does NOT cascade to fields or entities.
    # Runtime semantics are deferred to later phases.
    # -------------------------------------------------------------------------

    @abstractmethod
    def update(self, relationship: RelationshipDefinition) -> Result[None, str]:
        """Update relationship metadata (DESIGN-TIME ONLY).

        This method updates relationship metadata (name_key, description_key,
        inverse_name_key). It does NOT allow changing the relationship's
        identity (source_entity_id, target_entity_id).

        INVARIANT: Relationships are design-time constructs.
        - Editing does NOT imply runtime behavior
        - Source and target entity cannot be changed
        - Only metadata fields can be updated

        Args:
            relationship: Updated relationship definition

        Returns:
            Result with None on success or error message

        Validation:
            - Relationship must exist
            - source_entity_id must match existing relationship
            - target_entity_id must match existing relationship

        Example:
            result = repo.update(updated_relationship)
            if result.is_success():
                # Relationship metadata updated
        """
        pass

    @abstractmethod
    def delete(self, relationship_id: RelationshipDefinitionId) -> Result[None, str]:
        """Delete relationship definition (DESIGN-TIME ONLY).

        This method removes a relationship from the schema.
        It does NOT cascade to fields or entities.

        INVARIANT: Relationships are design-time constructs.
        - Deletion does NOT cascade to fields
        - Deletion does NOT cascade to entities
        - Deletion does NOT modify other relationships
        - Runtime semantics are deferred to later phases

        Args:
            relationship_id: ID of relationship to delete

        Returns:
            Result with None on success or error message

        Validation:
            - Relationship must exist

        Example:
            result = repo.delete(RelationshipDefinitionId("project_contains_boreholes"))
            if result.is_success():
                # Relationship deleted
        """
        pass

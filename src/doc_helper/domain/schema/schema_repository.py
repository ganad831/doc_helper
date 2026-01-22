"""Schema repository interface.

Domain-layer interface for schema persistence (infrastructure will implement).
"""

from abc import ABC, abstractmethod
from typing import Optional

from doc_helper.domain.common.result import Result
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.schema_ids import EntityDefinitionId


class ISchemaRepository(ABC):
    """Interface for schema persistence.

    This interface lives in the domain layer (dependency inversion).
    Implementation will be in infrastructure layer (e.g., SqliteSchemaRepository).

    RULES (IMPLEMENTATION_RULES.md Section 2.2):
    - Interface in domain, implementation in infrastructure
    - NO framework dependencies (no PyQt6!)
    - NO database access in domain (infrastructure handles persistence)
    - Returns Result[T, E] for error handling

    v1 Implementation:
        Schema is loaded from config.db (SQLite database).
        Schema is read-only in v1 (no schema editing).

    Usage:
        # In application layer:
        result = schema_repo.get_by_id(EntityDefinitionId("project"))
        if isinstance(result, Success):
            entity_def = result.value
            # Use entity definition...
        else:
            # Handle error...

        # Get all entities
        result = schema_repo.get_all()
        if isinstance(result, Success):
            entities = result.value
            # Process entities...
    """

    @abstractmethod
    def get_by_id(self, entity_id: EntityDefinitionId) -> Result[EntityDefinition, str]:
        """Get entity definition by ID.

        Args:
            entity_id: Entity definition ID

        Returns:
            Result containing EntityDefinition or error message

        Example:
            result = repo.get_by_id(EntityDefinitionId("project"))
            if isinstance(result, Success):
                entity = result.value
        """
        pass

    @abstractmethod
    def get_all(self) -> Result[tuple, str]:
        """Get all entity definitions.

        Returns:
            Result containing tuple of EntityDefinition objects or error message

        Example:
            result = repo.get_all()
            if isinstance(result, Success):
                entities = result.value
                for entity in entities:
                    print(entity.name_key)
        """
        pass

    @abstractmethod
    def get_root_entity(self) -> Result[EntityDefinition, str]:
        """Get the root entity definition (e.g., Project).

        The root entity is the top-level entity in the schema hierarchy.
        In v1 (Soil Investigation), this is the Project entity.

        Returns:
            Result containing root EntityDefinition or error message

        Example:
            result = repo.get_root_entity()
            if isinstance(result, Success):
                project_entity = result.value
        """
        pass

    @abstractmethod
    def exists(self, entity_id: EntityDefinitionId) -> bool:
        """Check if entity definition exists.

        Args:
            entity_id: Entity definition ID

        Returns:
            True if entity exists

        Example:
            if repo.exists(EntityDefinitionId("project")):
                # Entity exists
        """
        pass

    @abstractmethod
    def get_child_entities(self, parent_entity_id: EntityDefinitionId) -> Result[tuple, str]:
        """Get all child entities of a parent entity.

        Child entities are entities referenced in TABLE fields.

        Args:
            parent_entity_id: Parent entity definition ID

        Returns:
            Result containing tuple of child EntityDefinition objects or error message

        Example:
            result = repo.get_child_entities(EntityDefinitionId("project"))
            if isinstance(result, Success):
                children = result.value  # e.g., (borehole, lab_test)
        """
        pass

    @abstractmethod
    def save(self, entity: EntityDefinition) -> Result[None, str]:
        """Save entity definition (create or add fields).

        Phase 2 Step 2 Behavior:
        - If entity does NOT exist: CREATE new entity with all fields
        - If entity EXISTS: ADD only new fields (does not modify existing fields)

        Args:
            entity: Entity definition to save

        Returns:
            Result with None on success or error message

        Validation (enforced by implementation):
            - Entity name must be unique within schema
            - Field names must be unique within entity
            - All field types must be valid

        Example:
            result = repo.save(entity_definition)
            if isinstance(result, Success):
                # Entity saved successfully
        """
        pass

    @abstractmethod
    def update(self, entity: EntityDefinition) -> Result[None, str]:
        """Update entity definition metadata (Phase 2 Step 3).

        Updates entity metadata: name_key, description_key, is_root_entity, parent_entity_id.
        Does NOT add/remove fields (use save() for adding fields).

        Args:
            entity: Entity definition with updated metadata

        Returns:
            Result with None on success or error message

        Validation (enforced by application layer):
            - Entity must already exist
            - Parent entity must exist (if provided)
            - Cannot violate root entity constraints

        Example:
            entity = repo.get_by_id(entity_id).value
            entity.name_key = TranslationKey("entity.updated_name")
            result = repo.update(entity)
        """
        pass

    @abstractmethod
    def get_entity_dependencies(self, entity_id: EntityDefinitionId) -> Result[dict, str]:
        """Get all dependencies on an entity (Phase 2 Step 3 - Decision 4).

        Identifies what would break if this entity were deleted:
        - Entities with TABLE fields referencing this entity (child_entity_id)
        - Fields with LOOKUP referencing this entity (lookup_entity_id)
        - Entities with parent_entity_id pointing to this entity

        Args:
            entity_id: Entity definition ID to check dependencies for

        Returns:
            Result containing dict with dependency info:
            {
                "referenced_by_table_fields": [(entity_id, field_id), ...],
                "referenced_by_lookup_fields": [(entity_id, field_id), ...],
                "child_entities": [entity_id, ...],  # Entities with parent_entity_id = this entity
            }
            or error message

        Example:
            result = repo.get_entity_dependencies(EntityDefinitionId("borehole"))
            if isinstance(result, Success):
                deps = result.value
                if deps["referenced_by_table_fields"]:
                    # Cannot delete - entity is referenced by TABLE fields
        """
        pass

    @abstractmethod
    def get_field_dependencies(
        self, entity_id: EntityDefinitionId, field_id: "FieldDefinitionId"
    ) -> Result[dict, str]:
        """Get all dependencies on a field (Phase 2 Step 3 - Decision 4).

        Identifies what would break if this field were deleted:
        - Formulas that reference this field ({{field_id}})
        - Control rules where this field is source or target
        - LOOKUP fields using this field as lookup_display_field

        Args:
            entity_id: Parent entity definition ID
            field_id: Field definition ID to check dependencies for

        Returns:
            Result containing dict with dependency info:
            {
                "referenced_by_formulas": [(entity_id, field_id), ...],
                "referenced_by_controls_source": [(entity_id, field_id), ...],
                "referenced_by_controls_target": [(entity_id, field_id), ...],
                "referenced_by_lookup_display": [(entity_id, field_id), ...],
            }
            or error message

        Example:
            result = repo.get_field_dependencies(
                EntityDefinitionId("project"),
                FieldDefinitionId("site_location")
            )
            if isinstance(result, Success):
                deps = result.value
                if deps["referenced_by_formulas"]:
                    # Cannot delete - field is used in formulas
        """
        pass

    @abstractmethod
    def delete(self, entity_id: EntityDefinitionId) -> Result[None, str]:
        """Delete entity definition from schema (Phase 2 Step 3).

        IMPORTANT: Caller MUST check dependencies using get_entity_dependencies()
        before calling delete(). This method does NOT check dependencies.

        Args:
            entity_id: Entity definition ID to delete

        Returns:
            Result with None on success or error message

        Cascade Behavior:
            - Deletes entity definition
            - Deletes all field definitions belonging to this entity
            - Deletes all control relations where entity is source or target
            - Deletes all validation rules for this entity's fields

        Validation (enforced by implementation):
            - Entity must exist
            - Cannot delete if dependencies exist (caller responsibility to check)

        Example:
            # Check dependencies first
            deps_result = repo.get_entity_dependencies(entity_id)
            if deps_result.is_success() and not has_dependencies(deps_result.value):
                result = repo.delete(entity_id)
                if isinstance(result, Success):
                    # Entity deleted successfully
        """
        pass

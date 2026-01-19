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

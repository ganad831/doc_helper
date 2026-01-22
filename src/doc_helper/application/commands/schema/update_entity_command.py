"""Update entity command (Phase 2 Step 3).

Allows updating EntityDefinition metadata while protecting Phase 1 invariants.
"""

from typing import Optional

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class UpdateEntityCommand:
    """Update existing EntityDefinition metadata.

    Phase 2 Step 3 Scope:
    - Update name_key (display name)
    - Update description_key (display description)
    - Change is_root_entity flag (with validation)
    - Change parent_entity_id (with circular reference check)

    Protected Invariants:
    - Cannot change entity_id (identity is immutable)
    - Only one root entity allowed
    - Non-root entities must have parent_entity_id
    - No circular parent references
    - Parent entity must exist
    """

    def __init__(self, schema_repository: ISchemaRepository) -> None:
        """Initialize command.

        Args:
            schema_repository: Schema repository for persistence
        """
        self._schema_repository = schema_repository

    def execute(
        self,
        entity_id: str,
        name_key: Optional[str] = None,
        description_key: Optional[str] = None,
        is_root_entity: Optional[bool] = None,
        parent_entity_id: Optional[str] = None,
    ) -> Result[EntityDefinitionId, str]:
        """Update entity metadata.

        Args:
            entity_id: Entity ID to update (required)
            name_key: New name translation key (optional)
            description_key: New description translation key (optional, empty string clears)
            is_root_entity: New root entity status (optional)
            parent_entity_id: New parent entity ID (optional, empty string clears for root)

        Returns:
            Result with updated EntityDefinitionId on success, error message on failure

        Validations:
            - entity_id must not be empty
            - Entity must exist
            - If changing to root: no other root entity must exist
            - If changing to non-root: parent_entity_id must be provided and exist
            - parent_entity_id must not equal entity_id (no self-reference)
            - parent_entity_id must not create circular reference
        """
        # Validate entity_id
        if not entity_id or not entity_id.strip():
            return Failure("entity_id is required and cannot be empty")

        # Check if entity exists
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return Failure(f"Entity '{entity_id}' does not exist")

        # Load existing entity
        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return Failure(f"Failed to load entity: {load_result.error}")

        entity = load_result.value

        # Apply updates
        try:
            # Update name_key if provided
            if name_key is not None:
                if not name_key.strip():
                    return Failure("name_key cannot be empty")
                entity.name_key = TranslationKey(name_key.strip())

            # Update description_key if provided
            if description_key is not None:
                if description_key.strip():
                    entity.description_key = TranslationKey(description_key.strip())
                else:
                    entity.description_key = None

            # Update is_root_entity if provided
            if is_root_entity is not None:
                # Validate root entity change
                validation_result = self._validate_root_entity_change(
                    entity_id_obj, entity.is_root_entity, is_root_entity
                )
                if validation_result.is_failure():
                    return validation_result

                entity.is_root_entity = is_root_entity

                # If becoming root, clear parent
                if is_root_entity:
                    entity.parent_entity_id = None

            # Update parent_entity_id if provided
            # Note: parent_entity_id=None or empty string means "clear parent" (for root entities)
            if parent_entity_id is not None or (is_root_entity is not None and not is_root_entity):
                if parent_entity_id is not None:
                    parent_entity_id = parent_entity_id.strip()

                # Validate parent_entity_id change
                validation_result = self._validate_parent_entity_change(
                    entity_id_obj,
                    entity.is_root_entity,
                    parent_entity_id
                )
                if validation_result.is_failure():
                    return validation_result

                if parent_entity_id:
                    entity.parent_entity_id = EntityDefinitionId(parent_entity_id)
                else:
                    entity.parent_entity_id = None

        except Exception as e:
            return Failure(f"Failed to apply updates: {e}")

        # Save updated entity
        save_result = self._schema_repository.update(entity)
        if save_result.is_failure():
            return Failure(f"Failed to save entity: {save_result.error}")

        return Success(entity_id_obj)

    def _validate_root_entity_change(
        self,
        entity_id: EntityDefinitionId,
        current_is_root: bool,
        new_is_root: bool
    ) -> Result[None, str]:
        """Validate root entity status change.

        Args:
            entity_id: Entity being updated
            current_is_root: Current root status
            new_is_root: New root status

        Returns:
            Result with None on success, error message on failure
        """
        # If no change, allow
        if current_is_root == new_is_root:
            return Success(None)

        # If changing to root, check if another root exists
        if new_is_root:
            root_result = self._schema_repository.get_root_entity()
            if root_result.is_success():
                existing_root = root_result.value
                if existing_root.id != entity_id:
                    return Failure(
                        f"Cannot set as root entity: another root entity '{existing_root.id.value}' already exists. "
                        "Only one root entity is allowed."
                    )

        # If changing from root to non-root, must provide parent
        # (validated in _validate_parent_entity_change)

        return Success(None)

    def _validate_parent_entity_change(
        self,
        entity_id: EntityDefinitionId,
        is_root_entity: bool,
        new_parent_id: Optional[str]
    ) -> Result[None, str]:
        """Validate parent entity ID change.

        Args:
            entity_id: Entity being updated
            is_root_entity: Whether entity is root
            new_parent_id: New parent entity ID (None or empty = no parent)

        Returns:
            Result with None on success, error message on failure
        """
        # Root entities cannot have parent
        if is_root_entity:
            if new_parent_id is not None and new_parent_id.strip():
                return Failure("Root entities cannot have a parent entity")
            return Success(None)

        # Non-root entities must have parent
        if not new_parent_id or not new_parent_id.strip():
            return Failure("Non-root entities must have a parent entity")

        parent_id_obj = EntityDefinitionId(new_parent_id.strip())

        # Parent cannot be self
        if parent_id_obj == entity_id:
            return Failure("Entity cannot be its own parent (circular reference)")

        # Parent must exist
        if not self._schema_repository.exists(parent_id_obj):
            return Failure(f"Parent entity '{new_parent_id}' does not exist")

        # Check for circular reference
        if self._has_circular_reference(entity_id, parent_id_obj):
            return Failure(
                f"Setting parent to '{new_parent_id}' would create a circular reference. "
                "An entity cannot have itself as an ancestor."
            )

        return Success(None)

    def _has_circular_reference(
        self,
        entity_id: EntityDefinitionId,
        new_parent_id: EntityDefinitionId
    ) -> bool:
        """Check if setting parent would create circular reference.

        Uses depth-first search to detect cycles in parent chain.

        Args:
            entity_id: Entity being updated
            new_parent_id: Proposed new parent

        Returns:
            True if circular reference detected, False otherwise
        """
        visited = set()
        current = new_parent_id

        while current is not None:
            # If we encounter the entity itself, circular reference detected
            if current == entity_id:
                return True

            # If we've seen this entity before, there's a cycle (but not involving entity_id)
            if current in visited:
                break  # Cycle exists elsewhere, but doesn't affect this entity

            visited.add(current)

            # Get parent of current entity
            result = self._schema_repository.get_by_id(current)
            if result.is_failure():
                break  # Parent doesn't exist, stop traversal

            parent_entity = result.value
            current = parent_entity.parent_entity_id

        return False

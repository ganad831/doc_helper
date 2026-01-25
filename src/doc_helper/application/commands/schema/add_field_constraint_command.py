"""Add field constraint command (Phase 2 Step 3).

Allows adding validation constraints to fields.
"""

from dataclasses import replace

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.validation.constraints import FieldConstraint


class AddFieldConstraintCommand:
    """Add validation constraint to field.

    Phase 2 Step 3 Scope (Decision 3):
    - Add new constraints to fields
    - Validate constraint is compatible with field type
    - Prevent duplicate constraints of same type with same parameters

    Protected Invariants:
    - Constraints are immutable value objects
    - Constraints stored as tuple (immutable collection)
    - Each constraint type has specific field type applicability
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
        field_id: str,
        constraint: FieldConstraint,
    ) -> Result[FieldDefinitionId, str]:
        """Add constraint to field.

        Args:
            entity_id: Parent entity ID (required)
            field_id: Field ID to add constraint to (required)
            constraint: FieldConstraint instance to add (required)

        Returns:
            Result with FieldDefinitionId on success, error message on failure

        Validations:
            - entity_id and field_id must not be empty
            - constraint must be a FieldConstraint instance
            - Parent entity must exist
            - Field must exist
            - Constraint must not be a duplicate (same type with same parameters)
        """
        # Validate inputs
        if not entity_id or not entity_id.strip():
            return Failure("entity_id is required and cannot be empty")

        if not field_id or not field_id.strip():
            return Failure("field_id is required and cannot be empty")

        if not isinstance(constraint, FieldConstraint):
            return Failure(
                f"constraint must be a FieldConstraint instance, got {type(constraint).__name__}"
            )

        # Check if parent entity exists
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return Failure(f"Parent entity '{entity_id}' does not exist")

        # Load parent entity
        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return Failure(f"Failed to load parent entity: {load_result.error}")

        entity = load_result.value

        # Get field from entity
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return Failure(f"Field '{field_id}' not found in entity '{entity_id}'")

        field_def = entity.fields[field_id_obj]

        # Check for duplicate constraint
        # Two constraints are considered duplicates if they are the same type
        # and have the same parameters (value object equality)
        if constraint in field_def.constraints:
            return Failure(
                f"Constraint {type(constraint).__name__} with the same parameters already exists on field '{field_id}'. "
                "Duplicate constraints are not allowed."
            )

        # Add constraint to field's constraints tuple
        updated_constraints = field_def.constraints + (constraint,)

        # Create updated field with new constraints
        try:
            updated_field_def = replace(field_def, constraints=updated_constraints)
        except Exception as e:
            return Failure(f"Failed to create updated field: {e}")

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field_def)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return Failure(f"Failed to save field constraint: {save_result.error}")

        return Success(field_id_obj)

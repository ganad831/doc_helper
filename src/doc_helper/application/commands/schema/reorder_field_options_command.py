"""Reorder field options command (Phase 2 Step 3).

Allows reordering options in choice fields.
"""

from dataclasses import replace
from typing import List

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class ReorderFieldOptionsCommand:
    """Reorder options in choice field (DROPDOWN, RADIO).

    Phase 2 Step 3 Scope (Decision 5):
    - Reorder options while preserving all option values and labels
    - Validate new order contains exactly the same options
    - No duplicates, no missing options, no extra options

    Protected Invariants:
    - Only choice fields (DROPDOWN, RADIO) can have options
    - Option values and label_keys remain unchanged
    - Options are immutable tuples (new tuple created with new order)
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
        new_option_order: List[str],
    ) -> Result[FieldDefinitionId, str]:
        """Reorder options in choice field.

        Args:
            entity_id: Parent entity ID (required)
            field_id: Field ID to reorder options in (required)
            new_option_order: List of option values in desired order (required)

        Returns:
            Result with FieldDefinitionId on success, error message on failure

        Validations:
            - entity_id, field_id, new_option_order must not be empty
            - Parent entity must exist
            - Field must exist
            - Field must be a choice type (DROPDOWN, RADIO)
            - new_option_order must contain exactly the same option values (no duplicates, no missing, no extras)
        """
        # Validate inputs
        if not entity_id or not entity_id.strip():
            return Failure("entity_id is required and cannot be empty")

        if not field_id or not field_id.strip():
            return Failure("field_id is required and cannot be empty")

        if not new_option_order:
            return Failure("new_option_order is required and cannot be empty")

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

        # Validate field is a choice type
        if not field_def.is_choice_field:
            return Failure(
                f"Cannot reorder options for field type '{field_def.field_type.value}'. "
                f"Options can only be reordered for choice fields (DROPDOWN, RADIO)."
            )

        # Get existing option values
        existing_values = field_def.get_option_values()
        existing_values_set = set(existing_values)

        # Strip all values in new_option_order
        new_option_order_stripped = [value.strip() for value in new_option_order]

        # Validate new order contains exactly the same options
        new_order_set = set(new_option_order_stripped)

        # Check for duplicates in new order
        if len(new_option_order_stripped) != len(new_order_set):
            return Failure(
                "new_option_order contains duplicate values. Each option value must appear exactly once."
            )

        # Check for missing options
        missing_options = existing_values_set - new_order_set
        if missing_options:
            missing_str = ", ".join(sorted(missing_options))
            return Failure(
                f"new_option_order is missing existing option values: {missing_str}. "
                "All existing options must be included in the new order."
            )

        # Check for extra options (not in existing)
        extra_options = new_order_set - existing_values_set
        if extra_options:
            extra_str = ", ".join(sorted(extra_options))
            return Failure(
                f"new_option_order contains unknown option values: {extra_str}. "
                "Cannot add new options via reorder (use AddFieldOptionCommand)."
            )

        # Create options dict for lookup
        options_dict = {value: label_key for value, label_key in field_def.options}

        # Create new options tuple in specified order
        try:
            reordered_options = tuple(
                (value, options_dict[value]) for value in new_option_order_stripped
            )
        except KeyError as e:
            return Failure(f"Internal error: Option value {e} not found in field options")

        # Create updated field with reordered options
        try:
            updated_field_def = replace(field_def, options=reordered_options)
        except Exception as e:
            return Failure(f"Failed to create updated field: {e}")

        # Update entity's fields dict
        entity.fields[field_id_obj] = updated_field_def

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return Failure(f"Failed to save field option reorder: {save_result.error}")

        return Success(field_id_obj)

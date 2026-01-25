"""Add field option command (Phase 2 Step 3).

Allows adding new options to choice fields.
"""

from dataclasses import replace
from typing import Optional

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class AddFieldOptionCommand:
    """Add option to choice field (DROPDOWN, RADIO).

    Phase 2 Step 3 Scope (Decision 5):
    - Add new options to choice fields
    - Validate field is a choice type
    - Prevent duplicate option values
    - Maintain option order

    Protected Invariants:
    - Only choice fields (DROPDOWN, RADIO) can have options
    - Option values must be unique within field
    - Options are immutable tuples (new tuple created on add)
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
        option_value: str,
        option_label_key: str,
    ) -> Result[FieldDefinitionId, str]:
        """Add option to choice field.

        Args:
            entity_id: Parent entity ID (required)
            field_id: Field ID to add option to (required)
            option_value: Option value (unique identifier) (required)
            option_label_key: Translation key for option label (required)

        Returns:
            Result with FieldDefinitionId on success, error message on failure

        Validations:
            - entity_id, field_id, option_value, option_label_key must not be empty
            - Parent entity must exist
            - Field must exist
            - Field must be a choice type (DROPDOWN, RADIO, CHECKBOX)
            - Option value must not already exist in field
        """
        # Validate inputs
        if not entity_id or not entity_id.strip():
            return Failure("entity_id is required and cannot be empty")

        if not field_id or not field_id.strip():
            return Failure("field_id is required and cannot be empty")

        if not option_value or not option_value.strip():
            return Failure("option_value is required and cannot be empty")

        if not option_label_key or not option_label_key.strip():
            return Failure("option_label_key is required and cannot be empty")

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
                f"Cannot add option to field type '{field_def.field_type.value}'. "
                f"Options are only valid for choice fields (DROPDOWN, RADIO)."
            )

        # Validate option value doesn't already exist
        option_value_stripped = option_value.strip()
        existing_values = field_def.get_option_values()
        if option_value_stripped in existing_values:
            return Failure(
                f"Option value '{option_value_stripped}' already exists in field '{field_id}'. "
                "Option values must be unique."
            )

        # Create new option tuple (options are immutable)
        new_option = (option_value_stripped, TranslationKey(option_label_key.strip()))
        updated_options = field_def.options + (new_option,)

        # Create updated field with new options
        try:
            updated_field_def = replace(field_def, options=updated_options)
        except Exception as e:
            return Failure(f"Failed to create updated field: {e}")

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field_def)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return Failure(f"Failed to save field option: {save_result.error}")

        return Success(field_id_obj)

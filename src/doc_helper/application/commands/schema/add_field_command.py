"""Add Field Command (Phase 2 Step 2).

Command for adding field definitions to existing entities.
"""

from typing import Optional

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.entity_definition import EntityDefinition


class AddFieldCommand:
    """Command to add a field to an existing entity.

    Phase 2 Step 2 Scope:
    - Add new fields to existing entities
    - Simple field metadata only (label, type, required)
    - No constraints, formulas, or control rules

    NOT in Step 2:
    - Editing existing fields
    - Deleting fields
    - Adding validation rules
    - Adding formulas
    - Adding control rules

    Usage:
        command = AddFieldCommand(schema_repository)
        result = command.execute(
            entity_id="soil_sample",
            field_id="depth",
            field_type="NUMBER",
            label_key="field.depth",
            required=True
        )
    """

    def __init__(self, schema_repository: ISchemaRepository) -> None:
        """Initialize command.

        Args:
            schema_repository: Repository for schema persistence
        """
        self._schema_repository = schema_repository

    def execute(
        self,
        entity_id: str,
        field_id: str,
        field_type: str,
        label_key: str,
        help_text_key: Optional[str] = None,
        required: bool = False,
        default_value: Optional[str] = None,
    ) -> Result[FieldDefinitionId, str]:
        """Execute command to add field to entity.

        Args:
            entity_id: Entity to add field to
            field_id: Unique identifier for field within entity
            field_type: Field type (TEXT, NUMBER, DATE, etc.)
            label_key: Translation key for field label
            help_text_key: Translation key for help text (optional)
            required: Whether field is required (default: False)
            default_value: Default value for field (optional)

        Returns:
            Result containing created FieldDefinitionId or error message

        Validation:
            - entity_id must exist
            - field_id must be unique within entity
            - field_type must be valid
            - label_key must be provided
        """
        # Validate inputs
        if not entity_id:
            return Failure("entity_id is required")

        if not field_id:
            return Failure("field_id is required")

        if not field_type:
            return Failure("field_type is required")

        if not label_key:
            return Failure("label_key is required")

        # Check if entity exists
        entity_definition_id = EntityDefinitionId(entity_id)
        if not self._schema_repository.exists(entity_definition_id):
            return Failure(f"Entity '{entity_id}' does not exist")

        # Load entity
        entity_result = self._schema_repository.get_by_id(entity_definition_id)
        if entity_result.is_failure():
            return Failure(f"Failed to load entity: {entity_result.error}")

        entity = entity_result.value

        # Check if field already exists
        field_definition_id = FieldDefinitionId(field_id)
        if entity.has_field(field_definition_id):
            return Failure(f"Field '{field_id}' already exists in entity '{entity_id}'")

        # Validate field type
        try:
            field_type_enum = FieldType(field_type)
        except ValueError:
            valid_types = [ft.value for ft in FieldType]
            return Failure(
                f"Invalid field_type '{field_type}'. Valid types: {', '.join(valid_types)}"
            )

        # Create FieldDefinition
        try:
            field_def = FieldDefinition(
                id=field_definition_id,
                field_type=field_type_enum,
                label_key=TranslationKey(label_key),
                help_text_key=TranslationKey(help_text_key) if help_text_key else None,
                required=required,
                default_value=default_value,
                constraints=(),  # No constraints in Phase 2 Step 2
                options=(),  # No options yet
                formula=None,  # No formulas in Phase 2 Step 2
                lookup_entity_id=None,
                lookup_display_field=None,
                child_entity_id=None,
                control_rules=(),  # No control rules in Phase 2 Step 2
            )
        except (ValueError, TypeError) as e:
            return Failure(f"Invalid field data: {e}")

        # Add field to entity via aggregate method
        entity.add_field(field_def)

        # Save updated entity through repository
        # Phase 2 Step 2: save() now handles both CREATE and ADD FIELDS scenarios
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return Failure(f"Failed to save field: {save_result.error}")

        return Success(field_definition_id)

"""Update field command (Phase 2 Step 3).

Allows updating FieldDefinition metadata while protecting Phase 1 invariants.
"""

from dataclasses import replace
from typing import Optional

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.validation.constraints import RequiredConstraint
from doc_helper.domain.validation.lookup_display_field import (
    validate_lookup_display_field,
)


class UpdateFieldCommand:
    """Update existing FieldDefinition metadata.

    Phase 2 Step 3 Scope:
    - Update label_key, help_text_key, required, default_value
    - Update type-specific properties (formula, lookup_entity_id, etc.)
    - REJECT field type changes (Decision 1: Field type immutability)
    - REJECT incompatible property updates (Decision 6)

    Protected Invariants:
    - Field type is immutable (cannot be changed)
    - Type-specific properties only valid for their field types
    - Parent entity must exist

    INVARIANT - SELF-ENTITY LOOKUP:
        LOOKUP fields may only reference foreign entities.
        A LOOKUP field cannot reference its own entity. This is a defensive
        safety net - primary enforcement is at the UseCases layer.

    INVARIANT - FORMULA DESIGN-TIME SEMANTICS:
        Formula is stored as an OPAQUE STRING. This command performs:
        - NO formula parsing
        - NO formula validation (syntax or field references)
        - NO formula execution
        Formula validation and evaluation are runtime/export responsibilities.
        Schema Designer stores formulas as opaque strings.
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
        label_key: Optional[str] = None,
        help_text_key: Optional[str] = None,
        required: Optional[bool] = None,
        default_value: Optional[str] = None,
        formula: Optional[str] = None,
        lookup_entity_id: Optional[str] = None,
        lookup_display_field: Optional[str] = None,
        child_entity_id: Optional[str] = None,
    ) -> Result[FieldDefinitionId, str]:
        """Update field metadata.

        Args:
            entity_id: Parent entity ID (required)
            field_id: Field ID to update (required)
            label_key: New label translation key (optional)
            help_text_key: New help text translation key (optional, empty string clears)
            required: New required flag (optional)
            default_value: New default value (optional, empty string clears)
            formula: New formula expression (optional, only for CALCULATED fields)
            lookup_entity_id: New lookup entity ID (optional, only for LOOKUP fields)
            lookup_display_field: New lookup display field (optional, only for LOOKUP fields)
            child_entity_id: New child entity ID (optional, only for TABLE fields)

        Returns:
            Result with updated FieldDefinitionId on success, error message on failure

        Validations:
            - entity_id and field_id must not be empty
            - Parent entity must exist
            - Field must exist
            - Type-specific properties must match field type
            - label_key cannot be empty
        """
        # Validate entity_id
        if not entity_id or not entity_id.strip():
            return Failure("entity_id is required and cannot be empty")

        # Validate field_id
        if not field_id or not field_id.strip():
            return Failure("field_id is required and cannot be empty")

        # Check if parent entity exists
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return Failure(f"Parent entity '{entity_id}' does not exist")

        # Load parent entity to access field
        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return Failure(f"Failed to load parent entity: {load_result.error}")

        entity = load_result.value

        # Get field from entity
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return Failure(f"Field '{field_id}' not found in entity '{entity_id}'")

        field_def = entity.fields[field_id_obj]

        # Build updates dict (FieldDefinition is immutable, so use replace())
        updates = {}

        # Validate label_key before adding to updates
        if label_key is not None:
            if not label_key.strip():
                return Failure("label_key cannot be empty")
            updates["label_key"] = TranslationKey(label_key.strip())

        # Update help_text_key if provided
        if help_text_key is not None:
            if help_text_key.strip():
                updates["help_text_key"] = TranslationKey(help_text_key.strip())
            else:
                updates["help_text_key"] = None

        # Update required if provided - MUST synchronize constraints
        # =====================================================================
        # CALCULATED FIELD INVARIANT: CALCULATED fields NEVER have constraints.
        # Force required=False and constraints=() for CALCULATED fields.
        # =====================================================================
        if required is not None:
            if field_def.field_type == FieldType.CALCULATED:
                # INVARIANT: CALCULATED fields cannot be required and have no constraints
                updates["required"] = False
                # Strip ALL constraints from CALCULATED fields (not just RequiredConstraint)
                updates["constraints"] = ()
            else:
                updates["required"] = required
                # Synchronize RequiredConstraint with required flag
                current_constraints = list(field_def.constraints)
                has_required_constraint = any(
                    isinstance(c, RequiredConstraint) for c in current_constraints
                )
                if required and not has_required_constraint:
                    # Add RequiredConstraint
                    current_constraints.append(RequiredConstraint())
                elif not required and has_required_constraint:
                    # Remove RequiredConstraint
                    current_constraints = [
                        c for c in current_constraints if not isinstance(c, RequiredConstraint)
                    ]
                updates["constraints"] = tuple(current_constraints)

        # Update default_value if provided
        if default_value is not None:
            if default_value.strip():
                updates["default_value"] = default_value.strip()
            else:
                updates["default_value"] = None

        # =====================================================================
        # SELF-ENTITY LOOKUP INVARIANT (DEFENSIVE): LOOKUP fields cannot reference
        # their own entity. Primary enforcement is at UseCases layer; this is a
        # safety net to catch any bypass.
        # =====================================================================
        if lookup_entity_id is not None:
            if lookup_entity_id.strip() == entity_id.strip():
                return Failure("A LOOKUP field cannot reference its own entity.")

        # Validate and collect type-specific property updates
        type_specific_result = self._validate_and_get_type_specific_updates(
            field_def,
            formula=formula,
            lookup_entity_id=lookup_entity_id,
            lookup_display_field=lookup_display_field,
            child_entity_id=child_entity_id,
        )
        if type_specific_result.is_failure():
            return type_specific_result

        # Merge type-specific updates
        updates.update(type_specific_result.value)

        # Create new FieldDefinition with updates (FieldDefinition is frozen)
        try:
            updated_field_def = replace(field_def, **updates)
        except Exception as e:
            return Failure(f"Failed to create updated field: {e}")

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field_def)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return Failure(f"Failed to save field updates: {save_result.error}")

        return Success(field_id_obj)

    def _validate_and_get_type_specific_updates(
        self,
        field_def,
        formula: Optional[str] = None,
        lookup_entity_id: Optional[str] = None,
        lookup_display_field: Optional[str] = None,
        child_entity_id: Optional[str] = None,
    ) -> Result[dict, str]:
        """Validate and return type-specific property updates.

        Args:
            field_def: Current field definition
            formula: New formula (CALCULATED only)
            lookup_entity_id: New lookup entity (LOOKUP only)
            lookup_display_field: New lookup display field (LOOKUP only)
            child_entity_id: New child entity (TABLE only)

        Returns:
            Result with dict of updates on success, error message on failure

        Decision 6: Incompatible property updates must fail with explicit errors.
        """
        updates = {}
        field_type = field_def.field_type

        # Validate formula (CALCULATED only)
        if formula is not None:
            if field_type != FieldType.CALCULATED:
                return Failure(
                    f"Cannot set formula on field type '{field_type.value}'. "
                    f"Formula is only valid for CALCULATED fields."
                )
            updates["formula"] = formula.strip() if formula.strip() else None

        # Validate lookup properties (LOOKUP only)
        if lookup_entity_id is not None or lookup_display_field is not None:
            if field_type != FieldType.LOOKUP:
                return Failure(
                    f"Cannot set lookup properties on field type '{field_type.value}'. "
                    f"Lookup properties are only valid for LOOKUP fields."
                )

            if lookup_entity_id is not None:
                # Validate lookup entity exists
                lookup_entity_id_stripped = lookup_entity_id.strip()
                if lookup_entity_id_stripped:
                    lookup_entity_id_obj = EntityDefinitionId(lookup_entity_id_stripped)
                    if not self._schema_repository.exists(lookup_entity_id_obj):
                        return Failure(f"Lookup entity '{lookup_entity_id}' does not exist")
                    updates["lookup_entity_id"] = lookup_entity_id_stripped
                else:
                    updates["lookup_entity_id"] = None

            if lookup_display_field is not None:
                lookup_display_stripped = lookup_display_field.strip() if lookup_display_field.strip() else None
                # =====================================================================
                # LOOKUP DISPLAY FIELD INVARIANT (DEFENSIVE): lookup_display_field must
                # reference a valid field in the lookup entity. Primary enforcement is at
                # UseCases layer; this is a safety net to catch any bypass.
                # =====================================================================
                if lookup_display_stripped:
                    # Determine the lookup entity to validate against
                    # Use new value if provided, otherwise use existing value
                    target_lookup_entity = (
                        lookup_entity_id.strip() if lookup_entity_id and lookup_entity_id.strip()
                        else field_def.lookup_entity_id
                    )
                    if target_lookup_entity:
                        lookup_entity_id_obj = EntityDefinitionId(target_lookup_entity)
                        lookup_entity_result = self._schema_repository.get_by_id(lookup_entity_id_obj)
                        if lookup_entity_result.is_success():
                            lookup_entity = lookup_entity_result.value
                            available_fields = {
                                field.id.value: field.field_type
                                for field in lookup_entity.fields.values()
                            }
                            validation_result = validate_lookup_display_field(
                                lookup_display_field=lookup_display_stripped,
                                available_fields=available_fields,
                            )
                            if not validation_result.is_valid:
                                return Failure(validation_result.error_message)

                updates["lookup_display_field"] = lookup_display_stripped

        # Validate child_entity_id (TABLE only)
        if child_entity_id is not None:
            if field_type != FieldType.TABLE:
                return Failure(
                    f"Cannot set child_entity_id on field type '{field_type.value}'. "
                    f"child_entity_id is only valid for TABLE fields."
                )

            child_entity_id_stripped = child_entity_id.strip()
            if child_entity_id_stripped:
                child_entity_id_obj = EntityDefinitionId(child_entity_id_stripped)
                if not self._schema_repository.exists(child_entity_id_obj):
                    return Failure(f"Child entity '{child_entity_id}' does not exist")
                updates["child_entity_id"] = child_entity_id_stripped
            else:
                updates["child_entity_id"] = None

        return Success(updates)

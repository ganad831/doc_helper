"""Update control rule command (Phase A5.1).

Design-time CRUD for control rules.

INVARIANTS (enforced by this command):
- Control rules are DESIGN-TIME metadata only
- NO runtime execution occurs in this command
- Rule type (identity) cannot be changed - only formula_text can be updated
- Only metadata (formula_text) can be updated
- Rule must exist before updating

DEFERRED TO FUTURE PHASES:
- Runtime rule execution
- Runtime observers/listeners
- DAG building
- Auto-recompute
"""

from dataclasses import replace

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.application.dto.export_dto import ControlRuleExportDTO


class UpdateControlRuleCommand:
    """Update control rule on a field (DESIGN-TIME ONLY).

    This command updates the formula_text of an existing control rule.
    Control rules govern UI behavior (visibility, enabled state, required state).

    DESIGN-TIME ONLY:
    - This command updates metadata only
    - NO rule evaluation occurs
    - NO runtime behavior is triggered
    - Execution semantics are deferred to future phases

    INVARIANTS:
    - Rule type is identity - cannot be changed (use delete + add instead)
    - Only formula_text can be updated
    - Rule must already exist on the field
    - Formula text is stored as-is (validation is caller's responsibility)

    Usage:
        command = UpdateControlRuleCommand(schema_repository)
        result = command.execute(
            entity_id="project",
            field_id="optional_field",
            rule_type="VISIBILITY",
            formula_text="is_advanced_mode == true && user_level > 5"
        )
    """

    # Valid control rule types
    VALID_RULE_TYPES = frozenset({"VISIBILITY", "ENABLED", "REQUIRED"})

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
        rule_type: str,
        formula_text: str,
    ) -> Result[FieldDefinitionId, str]:
        """Update control rule formula (DESIGN-TIME ONLY).

        This updates the control rule metadata. NO execution occurs.

        Args:
            entity_id: Parent entity ID (required)
            field_id: Target field ID (required)
            rule_type: Rule type to update - VISIBILITY, ENABLED, or REQUIRED (required)
            formula_text: New boolean formula expression (required)

        Returns:
            Result with FieldDefinitionId on success, error message on failure

        Validations:
            - All parameters must be non-empty
            - Entity must exist
            - Field must exist
            - Rule type must be valid
            - Rule of specified type must exist on field

        DESIGN-TIME ONLY - NO cascade effects, NO runtime behavior.
        """
        # Validate inputs
        if not entity_id or not entity_id.strip():
            return Failure("entity_id is required and cannot be empty")

        if not field_id or not field_id.strip():
            return Failure("field_id is required and cannot be empty")

        if not rule_type or not rule_type.strip():
            return Failure("rule_type is required and cannot be empty")

        if not formula_text or not formula_text.strip():
            return Failure("formula_text is required and cannot be empty")

        # Normalize rule type
        rule_type_normalized = rule_type.strip().upper()
        if rule_type_normalized not in self.VALID_RULE_TYPES:
            return Failure(
                f"Invalid rule_type '{rule_type}'. "
                f"Must be one of: {', '.join(sorted(self.VALID_RULE_TYPES))}"
            )

        # Check if parent entity exists
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return Failure(f"Entity '{entity_id}' does not exist")

        # Load parent entity
        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return Failure(f"Failed to load entity: {load_result.error}")

        entity = load_result.value

        # Get field from entity
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return Failure(f"Field '{field_id}' not found in entity '{entity_id}'")

        field_def = entity.fields[field_id_obj]

        # Find existing rule to update
        rule_found = False
        rule_index = -1
        for i, existing_rule in enumerate(field_def.control_rules):
            if isinstance(existing_rule, ControlRuleExportDTO):
                if existing_rule.rule_type == rule_type_normalized:
                    rule_found = True
                    rule_index = i
                    break

        if not rule_found:
            return Failure(
                f"No {rule_type_normalized} control rule found on field '{field_id}'. "
                "Use AddControlRuleCommand to create one."
            )

        # Create updated control rule DTO
        updated_rule_dto = ControlRuleExportDTO(
            rule_type=rule_type_normalized,
            target_field_id=field_id.strip(),
            formula_text=formula_text.strip(),
        )

        # Replace the rule in the tuple
        rules_list = list(field_def.control_rules)
        rules_list[rule_index] = updated_rule_dto
        new_control_rules = tuple(rules_list)

        # Update field with modified control rules
        updated_field = replace(field_def, control_rules=new_control_rules)

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return Failure(f"Failed to update control rule: {save_result.error}")

        return Success(field_id_obj)

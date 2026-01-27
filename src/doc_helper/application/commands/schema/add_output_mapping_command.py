"""Add output mapping command (Phase A6.1).

Design-time CRUD for output mappings.

INVARIANTS (enforced by this command):
- Output mappings are DESIGN-TIME metadata only
- NO runtime execution occurs in this command
- Output mappings are stored in the field's output_mappings tuple
- Target type (TEXT, NUMBER, BOOLEAN) determines output format
- Formula describes how to transform field value for document output
- Only one mapping of each target type per field

DEFERRED TO FUTURE PHASES:
- Runtime mapping execution
- Runtime observers/listeners
- Document rendering
- Format validation
"""

from dataclasses import replace

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.application.dto.export_dto import OutputMappingExportDTO


class AddOutputMappingCommand:
    """Add output mapping to a field (DESIGN-TIME ONLY).

    This command adds an output mapping to a field's output_mappings tuple.
    Output mappings define how field values are transformed for document output.

    DESIGN-TIME ONLY:
    - This command stores metadata only
    - NO mapping execution occurs
    - NO runtime behavior is triggered
    - Execution semantics are deferred to future phases

    INVARIANTS:
    - One mapping per target type per field (no duplicates)
    - Target must be TEXT, NUMBER, or BOOLEAN
    - Formula text is stored as-is (validation is caller's responsibility)
    - No cascade effects

    Usage:
        command = AddOutputMappingCommand(schema_repository)
        result = command.execute(
            entity_id="project",
            field_id="depth_range",
            target="TEXT",
            formula_text="{{depth_from}} - {{depth_to}}"
        )
    """

    # Valid output target types
    VALID_TARGET_TYPES = frozenset({"TEXT", "NUMBER", "BOOLEAN"})

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
        target: str,
        formula_text: str,
    ) -> Result[FieldDefinitionId, str]:
        """Add output mapping to a field (DESIGN-TIME ONLY).

        This stores the output mapping metadata. NO execution occurs.

        Args:
            entity_id: Parent entity ID (required)
            field_id: Target field ID (required)
            target: Output target type - TEXT, NUMBER, or BOOLEAN (required)
            formula_text: Formula expression for output transformation (required)

        Returns:
            Result with FieldDefinitionId on success, error message on failure

        Validations:
            - All parameters must be non-empty
            - Entity must exist
            - Field must exist
            - Target type must be valid
            - No duplicate target type on field

        DESIGN-TIME ONLY - NO cascade effects, NO runtime behavior.
        """
        # Validate inputs
        if not entity_id or not entity_id.strip():
            return Failure("entity_id is required and cannot be empty")

        if not field_id or not field_id.strip():
            return Failure("field_id is required and cannot be empty")

        if not target or not target.strip():
            return Failure("target is required and cannot be empty")

        if not formula_text or not formula_text.strip():
            return Failure("formula_text is required and cannot be empty")

        # Normalize target type
        target_normalized = target.strip().upper()
        if target_normalized not in self.VALID_TARGET_TYPES:
            return Failure(
                f"Invalid target '{target}'. "
                f"Must be one of: {', '.join(sorted(self.VALID_TARGET_TYPES))}"
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

        # Check for duplicate target type
        for existing_mapping in field_def.output_mappings:
            if isinstance(existing_mapping, OutputMappingExportDTO):
                if existing_mapping.target == target_normalized:
                    return Failure(
                        f"Field '{field_id}' already has an output mapping for target {target_normalized}. "
                        "Use UpdateOutputMappingCommand to modify it."
                    )

        # Create output mapping DTO
        output_mapping_dto = OutputMappingExportDTO(
            target=target_normalized,
            formula_text=formula_text.strip(),
        )

        # Update field with new output mapping
        new_output_mappings = field_def.output_mappings + (output_mapping_dto,)
        updated_field = replace(field_def, output_mappings=new_output_mappings)

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return Failure(f"Failed to add output mapping: {save_result.error}")

        return Success(field_id_obj)

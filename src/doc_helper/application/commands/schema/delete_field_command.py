"""Delete field command (Phase 2 Step 3).

Allows deleting fields with dependency checking.
"""

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class DeleteFieldCommand:
    """Delete field from entity (with dependency checking).

    Phase 2 Step 3 Scope (Decision 4):
    - Delete field only if no dependencies exist
    - Check formulas, controls, lookup_display_field references
    - Return detailed error if dependencies found

    Protected Invariants:
    - Cannot delete field referenced by formulas
    - Cannot delete field referenced by control rules
    - Cannot delete field used as lookup_display_field
    - Must check dependencies before deletion
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
    ) -> Result[None, str]:
        """Delete field from entity.

        Args:
            entity_id: Parent entity ID (required)
            field_id: Field ID to delete (required)

        Returns:
            Result with None on success, error message on failure

        Validations:
            - entity_id and field_id must not be empty
            - Parent entity must exist
            - Field must exist in entity
            - Field must have no dependencies (formulas, controls, lookups)

        Dependency Check (Decision 4):
            Before deletion, checks:
            - Formulas referencing this field
            - Control rules with this field as source or target
            - LOOKUP fields using this field as lookup_display_field

            If any dependencies found, deletion is blocked and error lists all dependencies.
        """
        # Validate inputs
        if not entity_id or not entity_id.strip():
            return Failure("entity_id is required and cannot be empty")

        if not field_id or not field_id.strip():
            return Failure("field_id is required and cannot be empty")

        # Check if parent entity exists
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return Failure(f"Parent entity '{entity_id}' does not exist")

        # Load parent entity to verify field exists
        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return Failure(f"Failed to load parent entity: {load_result.error}")

        entity = load_result.value

        # Get field from entity
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return Failure(f"Field '{field_id}' not found in entity '{entity_id}'")

        # Check dependencies (Decision 4: Pre-delete dependency checking required)
        deps_result = self._schema_repository.get_field_dependencies(entity_id_obj, field_id_obj)
        if deps_result.is_failure():
            return Failure(f"Failed to check dependencies: {deps_result.error}")

        deps = deps_result.value

        # Check if any dependencies exist
        has_dependencies = (
            deps["referenced_by_formulas"]
            or deps["referenced_by_controls_source"]
            or deps["referenced_by_controls_target"]
            or deps["referenced_by_lookup_display"]
        )

        if has_dependencies:
            # Build detailed error message listing all dependencies
            error_lines = [
                f"Cannot delete field '{field_id}' from entity '{entity_id}' because it is referenced by:"
            ]

            if deps["referenced_by_formulas"]:
                error_lines.append(f"  - {len(deps['referenced_by_formulas'])} formula(s):")
                for ent_id, fld_id in deps["referenced_by_formulas"][:5]:  # Show max 5
                    error_lines.append(f"      {ent_id}.{fld_id}")
                if len(deps["referenced_by_formulas"]) > 5:
                    error_lines.append(f"      ... and {len(deps['referenced_by_formulas']) - 5} more")

            if deps["referenced_by_controls_source"]:
                error_lines.append(f"  - {len(deps['referenced_by_controls_source'])} control rule(s) (as source):")
                for ent_id, fld_id in deps["referenced_by_controls_source"][:5]:
                    error_lines.append(f"      {ent_id}.{fld_id}")
                if len(deps["referenced_by_controls_source"]) > 5:
                    error_lines.append(f"      ... and {len(deps['referenced_by_controls_source']) - 5} more")

            if deps["referenced_by_controls_target"]:
                error_lines.append(f"  - {len(deps['referenced_by_controls_target'])} control rule(s) (as target):")
                for ent_id, fld_id in deps["referenced_by_controls_target"][:5]:
                    error_lines.append(f"      {ent_id}.{fld_id}")
                if len(deps["referenced_by_controls_target"]) > 5:
                    error_lines.append(f"      ... and {len(deps['referenced_by_controls_target']) - 5} more")

            if deps["referenced_by_lookup_display"]:
                error_lines.append(f"  - {len(deps['referenced_by_lookup_display'])} LOOKUP field(s) (as display field):")
                for ent_id, fld_id in deps["referenced_by_lookup_display"][:5]:
                    error_lines.append(f"      {ent_id}.{fld_id}")
                if len(deps["referenced_by_lookup_display"]) > 5:
                    error_lines.append(f"      ... and {len(deps['referenced_by_lookup_display']) - 5} more")

            error_lines.append("Remove these references before deleting this field.")

            return Failure("\n".join(error_lines))

        # No dependencies - safe to delete
        # Remove field from entity via aggregate method
        entity.remove_field(field_id_obj)

        # Save updated entity (field will be removed from database)
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return Failure(f"Failed to delete field: {save_result.error}")

        return Success(None)

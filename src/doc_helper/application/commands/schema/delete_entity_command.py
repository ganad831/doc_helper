"""Delete entity command (Phase 2 Step 3).

This command implements entity deletion with comprehensive dependency checking
as required by Decision 4 (Pre-delete dependency checking required).
"""

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId


class DeleteEntityCommand:
    """Delete entity from schema (with dependency checking).

    Phase 2 Step 3 Scope (Decision 4):
    - Delete entity only if no dependencies exist
    - Check TABLE fields, LOOKUP fields, child entities
    - Return detailed error if dependencies found

    Dependencies checked:
    - referenced_by_table_fields: Other entities have TABLE fields pointing to this entity
    - referenced_by_lookup_fields: Other entities have LOOKUP fields pointing to this entity
    - child_entities: This entity has child entities (parent_entity_id relationship)

    Examples:
        >>> command = DeleteEntityCommand(schema_repository)
        >>> result = command.execute(entity_id="standalone_entity")
        >>> # Success if no dependencies

        >>> result = command.execute(entity_id="borehole")
        >>> # Failure if project.boreholes_table references it
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
    ) -> Result[None, str]:
        """Execute delete entity command.

        Args:
            entity_id: ID of entity to delete

        Returns:
            Success(None) if deletion successful
            Failure(error_message) if:
            - entity_id is empty
            - Entity does not exist
            - Entity has dependencies (TABLE fields, LOOKUP fields, child entities)
            - Repository save fails

        Business Rules (Decision 4):
        - Must check dependencies before deletion
        - Deletion blocked if any dependency exists
        - Error message must list all dependencies found
        """
        # Validate inputs
        if not entity_id or not entity_id.strip():
            return Failure("entity_id is required and cannot be empty")

        entity_id_stripped = entity_id.strip()
        entity_id_obj = EntityDefinitionId(entity_id_stripped)

        # Check if entity exists
        if not self._schema_repository.exists(entity_id_obj):
            return Failure(
                f"Entity '{entity_id_stripped}' does not exist. Cannot delete non-existent entity."
            )

        # Check dependencies (Decision 4: Pre-delete dependency checking required)
        deps_result = self._schema_repository.get_entity_dependencies(entity_id_obj)
        if deps_result.is_failure():
            return Failure(f"Failed to check dependencies: {deps_result.error}")

        deps = deps_result.value

        # Check if any dependencies exist
        has_dependencies = (
            deps["referenced_by_table_fields"]
            or deps["referenced_by_lookup_fields"]
            or deps["child_entities"]
        )

        if has_dependencies:
            # Build detailed error message listing all dependencies
            error_lines = [
                f"Cannot delete entity '{entity_id_stripped}' because it is referenced by:"
            ]

            # List TABLE field dependencies
            if deps["referenced_by_table_fields"]:
                error_lines.append(
                    f"  - {len(deps['referenced_by_table_fields'])} TABLE field(s):"
                )
                # Show up to 5 examples
                for ent_id, fld_id in deps["referenced_by_table_fields"][:5]:
                    error_lines.append(f"      {ent_id}.{fld_id} (TABLE field)")
                if len(deps["referenced_by_table_fields"]) > 5:
                    remaining = len(deps["referenced_by_table_fields"]) - 5
                    error_lines.append(f"      ... and {remaining} more")

            # List LOOKUP field dependencies
            if deps["referenced_by_lookup_fields"]:
                error_lines.append(
                    f"  - {len(deps['referenced_by_lookup_fields'])} LOOKUP field(s):"
                )
                # Show up to 5 examples
                for ent_id, fld_id in deps["referenced_by_lookup_fields"][:5]:
                    error_lines.append(f"      {ent_id}.{fld_id} (LOOKUP field)")
                if len(deps["referenced_by_lookup_fields"]) > 5:
                    remaining = len(deps["referenced_by_lookup_fields"]) - 5
                    error_lines.append(f"      ... and {remaining} more")

            # List child entity dependencies
            if deps["child_entities"]:
                error_lines.append(
                    f"  - {len(deps['child_entities'])} child entit{'y' if len(deps['child_entities']) == 1 else 'ies'}:"
                )
                # Show up to 5 examples
                for child_id in deps["child_entities"][:5]:
                    error_lines.append(f"      {child_id} (child entity)")
                if len(deps["child_entities"]) > 5:
                    remaining = len(deps["child_entities"]) - 5
                    error_lines.append(f"      ... and {remaining} more")

            error_lines.append("")
            error_lines.append("Remove these references before deleting this entity.")

            return Failure("\n".join(error_lines))

        # No dependencies - safe to delete
        delete_result = self._schema_repository.delete(entity_id_obj)

        if delete_result.is_failure():
            return Failure(
                f"Failed to delete entity '{entity_id_stripped}': {delete_result.error}"
            )

        return Success(None)

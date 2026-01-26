"""Schema Use Cases (Architecture Enforcement Phase, updated Phase F-10, Phase F-12.5, Phase F-14).

Application layer use-case class that encapsulates all schema operations.
Presentation layer MUST use this class instead of directly accessing
commands, queries, or repositories.

RULE 0 ENFORCEMENT:
- Presentation ONLY calls use-case methods
- All domain type construction happens HERE
- All command/query orchestration happens HERE
- Returns OperationResult or DTOs to Presentation

This class wraps:
- GetSchemaEntitiesQuery (read entities)
- GetRelationshipsQuery (read relationships)
- CreateEntityCommand (create entity)
- UpdateEntityCommand (update entity metadata)
- DeleteEntityCommand (delete entity with dependency check)
- AddFieldCommand (add field)
- UpdateFieldCommand (update field metadata)
- DeleteFieldCommand (delete field with dependency check)
- AddFieldConstraintCommand (add constraint to field)
- CreateRelationshipCommand (create relationship)
- UpdateRelationshipCommand (update relationship metadata - design-time only)
- DeleteRelationshipCommand (delete relationship - design-time only, no cascade)
- ExportSchemaCommand (export schema)
- ImportSchemaCommand (import schema)

Phase F-10 Control Rule Methods:
- add_control_rule(): Add control rule with governance validation
- update_control_rule(): Update control rule with re-validation
- delete_control_rule(): Delete control rule
- list_control_rules_for_field(): List all control rules for a field

Phase F-12.5 Output Mapping Methods:
- add_output_mapping(): Add output mapping to a field
- update_output_mapping(): Update existing output mapping
- delete_output_mapping(): Delete output mapping
- list_output_mappings_for_field(): List all output mappings for a field

Phase F-14 Field Option Methods (DROPDOWN/RADIO):
- add_field_option(): Add option to choice field
- update_field_option(): Update option label key
- delete_field_option(): Delete option from choice field
- reorder_field_options(): Reorder options in choice field
- list_field_options(): List all options for a field
"""

from pathlib import Path
from typing import Optional

from doc_helper.application.commands.schema.add_field_command import AddFieldCommand
from doc_helper.application.commands.schema.add_field_constraint_command import (
    AddFieldConstraintCommand,
)
from doc_helper.application.commands.schema.add_field_option_command import (
    AddFieldOptionCommand,
)
from doc_helper.application.commands.schema.delete_field_option_command import (
    DeleteFieldOptionCommand,
)
from doc_helper.application.commands.schema.reorder_field_options_command import (
    ReorderFieldOptionsCommand,
)
from doc_helper.application.commands.schema.update_field_option_command import (
    UpdateFieldOptionCommand,
)
from doc_helper.application.commands.schema.delete_field_command import (
    DeleteFieldCommand,
)
from doc_helper.application.commands.schema.update_field_command import (
    UpdateFieldCommand,
)
from doc_helper.application.commands.schema.create_entity_command import (
    CreateEntityCommand,
)
from doc_helper.application.commands.schema.create_relationship_command import (
    CreateRelationshipCommand,
)
from doc_helper.application.commands.schema.update_relationship_command import (
    UpdateRelationshipCommand,
)
from doc_helper.application.commands.schema.delete_relationship_command import (
    DeleteRelationshipCommand,
)
from doc_helper.application.commands.schema.delete_entity_command import (
    DeleteEntityCommand,
)
from doc_helper.application.commands.schema.export_schema_command import (
    ExportSchemaCommand,
)
from doc_helper.application.commands.schema.import_schema_command import (
    ImportSchemaCommand,
)
from doc_helper.application.commands.schema.update_entity_command import (
    UpdateEntityCommand,
)
from doc_helper.application.dto.control_rule_dto import (
    ControlRuleResultDTO,
    ControlRuleStatus,
    ControlRuleType,
)
from doc_helper.application.dto.export_dto import (
    ConstraintExportDTO,
    ControlRuleExportDTO,
    ExportResult,
    FieldOptionExportDTO,
    OutputMappingExportDTO,
)
from doc_helper.application.dto.formula_dto import SchemaFieldInfoDTO
from doc_helper.application.dto.import_dto import (
    EnforcementPolicy,
    IdenticalSchemaAction,
    ImportResult,
)
from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.dto.relationship_dto import RelationshipDTO
from doc_helper.application.dto.schema_dto import EntityDefinitionDTO
from doc_helper.application.usecases.control_rule_usecases import ControlRuleUseCases
from doc_helper.application.queries.schema.get_relationships_query import (
    GetRelationshipsQuery,
)
from doc_helper.application.queries.schema.get_schema_entities_query import (
    GetSchemaEntitiesQuery,
)
from doc_helper.domain.schema.relationship_repository import IRelationshipRepository
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.validation.constraints import (
    AllowedValuesConstraint,
    FileExtensionConstraint,
    MaxFileSizeConstraint,
    MaxLengthConstraint,
    MaxValueConstraint,
    MinLengthConstraint,
    MinValueConstraint,
    PatternConstraint,
    RequiredConstraint,
)
from doc_helper.domain.validation.lookup_display_field import (
    validate_lookup_display_field,
)
from doc_helper.domain.validation.severity import Severity


class SchemaUseCases:
    """Use-case class for all schema operations.

    This class provides a clean boundary between Presentation and Application layers.
    Presentation layer injects this class and calls its methods with primitives/DTOs.
    All domain type construction and command/query orchestration happens here.

    Usage in ViewModel:
        # ViewModel __init__ receives SchemaUseCases via DI
        def __init__(self, schema_usecases: SchemaUseCases, ...):
            self._schema_usecases = schema_usecases

        # ViewModel calls use-case methods with primitives
        def create_entity(self, entity_id: str, name_key: str, ...):
            return self._schema_usecases.create_entity(entity_id, name_key, ...)

    This replaces:
        # OLD (FORBIDDEN): ViewModel instantiates command with reach-through
        command = CreateEntityCommand(self._schema_query._schema_repository)
        result = command.execute(...)
        return OperationResult.ok(result.value.value)  # unwrap domain ID
    """

    def __init__(
        self,
        schema_repository: ISchemaRepository,
        relationship_repository: Optional[IRelationshipRepository],
        translation_service,  # ITranslationService
    ) -> None:
        """Initialize SchemaUseCases.

        Args:
            schema_repository: Repository for schema persistence (Domain interface)
            relationship_repository: Repository for relationship persistence (Domain interface)
            translation_service: Service for translating labels/descriptions

        Note:
            Repositories are injected HERE (Application layer), not in Presentation.
            This is the composition root pattern.
        """
        self._schema_repository = schema_repository
        self._relationship_repository = relationship_repository
        self._translation_service = translation_service

        # Create queries (internal - not exposed to Presentation)
        self._schema_query = GetSchemaEntitiesQuery(
            schema_repository, translation_service
        )
        self._relationship_query: Optional[GetRelationshipsQuery] = None
        if relationship_repository:
            self._relationship_query = GetRelationshipsQuery(relationship_repository)

        # Create commands (internal - not exposed to Presentation)
        self._create_entity_command = CreateEntityCommand(schema_repository)
        self._add_field_command = AddFieldCommand(schema_repository)
        self._create_relationship_command: Optional[CreateRelationshipCommand] = None
        self._update_relationship_command: Optional[UpdateRelationshipCommand] = None
        self._delete_relationship_command: Optional[DeleteRelationshipCommand] = None
        if relationship_repository:
            self._create_relationship_command = CreateRelationshipCommand(
                relationship_repository=relationship_repository,
                schema_repository=schema_repository,
            )
            self._update_relationship_command = UpdateRelationshipCommand(
                relationship_repository=relationship_repository,
            )
            self._delete_relationship_command = DeleteRelationshipCommand(
                relationship_repository=relationship_repository,
            )
        self._export_command = ExportSchemaCommand(
            schema_repository, relationship_repository
        )
        self._import_command = ImportSchemaCommand(
            schema_repository=schema_repository,
            relationship_repository=relationship_repository,
        )
        self._add_constraint_command = AddFieldConstraintCommand(schema_repository)
        self._update_entity_command = UpdateEntityCommand(schema_repository)
        self._delete_entity_command = DeleteEntityCommand(schema_repository)
        self._update_field_command = UpdateFieldCommand(schema_repository)
        self._delete_field_command = DeleteFieldCommand(schema_repository)

        # Phase F-14: Field Option commands
        self._add_field_option_command = AddFieldOptionCommand(schema_repository)
        self._update_field_option_command = UpdateFieldOptionCommand(schema_repository)
        self._delete_field_option_command = DeleteFieldOptionCommand(schema_repository)
        self._reorder_field_options_command = ReorderFieldOptionsCommand(schema_repository)

        # Phase F-10: Control Rule UseCases for validation
        self._control_rule_usecases = ControlRuleUseCases()

    # =========================================================================
    # Private Validation Helpers
    # =========================================================================

    def _validate_lookup_display_field(
        self,
        lookup_entity_id: str,
        lookup_display_field: str,
    ) -> OperationResult:
        """Validate that lookup_display_field references a valid field.

        INVARIANT: lookup_display_field must:
        1. Reference an existing field in lookup_entity_id
        2. NOT be a CALCULATED, TABLE, FILE, or IMAGE field type
        3. Be a user-readable scalar field

        Args:
            lookup_entity_id: The entity ID being referenced
            lookup_display_field: The field ID to validate

        Returns:
            OperationResult.ok(None) if valid, OperationResult.fail(message) if invalid
        """
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId

        # Load the lookup entity to get its fields
        lookup_entity_id_obj = EntityDefinitionId(lookup_entity_id.strip())
        load_result = self._schema_repository.get_by_id(lookup_entity_id_obj)

        if load_result.is_failure():
            return OperationResult.fail(
                f"Cannot validate lookup_display_field: lookup entity '{lookup_entity_id}' not found."
            )

        lookup_entity = load_result.value

        # Build mapping of field_id -> FieldType for validation
        available_fields = {
            field.id.value: field.field_type
            for field in lookup_entity.fields.values()
        }

        # Use pure domain validation function
        validation_result = validate_lookup_display_field(
            lookup_display_field=lookup_display_field.strip(),
            available_fields=available_fields,
        )

        if not validation_result.is_valid:
            return OperationResult.fail(validation_result.error_message)

        return OperationResult.ok(None)

    # =========================================================================
    # Query Operations (READ)
    # =========================================================================

    def get_all_entities(self) -> tuple[EntityDefinitionDTO, ...]:
        """Get all entity definitions.

        Returns:
            Tuple of EntityDefinitionDTOs (empty tuple on error)
        """
        result = self._schema_query.execute()
        if result.is_success():
            return result.value
        return ()

    def get_all_relationships(self) -> tuple[RelationshipDTO, ...]:
        """Get all relationship definitions.

        Returns:
            Tuple of RelationshipDTOs (empty tuple if not available or error)
        """
        if not self._relationship_query:
            return ()

        result = self._relationship_query.execute()
        if result.is_success():
            return result.value
        return ()

    def get_field_validation_rules(
        self,
        entity_id: str,
        field_id: str,
    ) -> tuple[str, ...]:
        """Get formatted validation rules for a field.

        Args:
            entity_id: Entity ID (string)
            field_id: Field ID (string)

        Returns:
            Tuple of human-readable constraint descriptions
        """
        return self._schema_query.get_field_validation_rules(entity_id, field_id)

    def get_valid_lookup_display_fields(
        self,
        entity_id: str,
    ) -> tuple[tuple[str, str], ...]:
        """Get fields valid for use as lookup_display_field.

        Returns fields that are user-readable scalars (not CALCULATED, TABLE,
        FILE, or IMAGE) for use in the lookup display field dropdown.

        Args:
            entity_id: Entity ID to get fields from

        Returns:
            Tuple of (field_id, field_label) tuples for valid display fields.
            Empty tuple if entity not found or has no valid fields.

        INVARIANT: Only returns fields with types that are valid for display:
        - TEXT, TEXTAREA, NUMBER, DATE, DROPDOWN, RADIO, CHECKBOX, LOOKUP
        """
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId
        from doc_helper.domain.validation.lookup_display_field import (
            is_valid_display_field_type,
        )

        if not entity_id or not entity_id.strip():
            return ()

        entity_id_obj = EntityDefinitionId(entity_id.strip())
        load_result = self._schema_repository.get_by_id(entity_id_obj)

        if load_result.is_failure():
            return ()

        entity = load_result.value
        valid_fields = []

        for field_def in entity.fields.values():
            if is_valid_display_field_type(field_def.field_type):
                # Get translated label for display
                label = self._translation_service.translate(field_def.label_key.key)
                valid_fields.append((field_def.id.value, label))

        return tuple(valid_fields)

    # =========================================================================
    # Command Operations (WRITE)
    # =========================================================================

    def create_entity(
        self,
        entity_id: str,
        name_key: str,
        description_key: Optional[str] = None,
        is_root_entity: bool = False,
    ) -> OperationResult:
        """Create a new entity.

        Args:
            entity_id: Unique entity identifier
            name_key: Translation key for entity name
            description_key: Translation key for description (optional)
            is_root_entity: Whether this is a root entity

        Returns:
            OperationResult with entity ID string on success, error message on failure
        """
        result = self._create_entity_command.execute(
            entity_id=entity_id,
            name_key=name_key,
            description_key=description_key,
            is_root_entity=is_root_entity,
            parent_entity_id=None,
        )

        if result.is_success():
            # Unwrap domain ID to string HERE (not in Presentation)
            return OperationResult.ok(result.value.value)
        else:
            return OperationResult.fail(result.error)

    def update_entity(
        self,
        entity_id: str,
        name_key: Optional[str] = None,
        description_key: Optional[str] = None,
        is_root_entity: Optional[bool] = None,
        parent_entity_id: Optional[str] = None,
    ) -> OperationResult:
        """Update entity metadata.

        Args:
            entity_id: Entity ID to update (required, immutable)
            name_key: New name translation key (optional)
            description_key: New description translation key (optional, empty string clears)
            is_root_entity: New root entity status (optional)
            parent_entity_id: New parent entity ID (optional, empty string clears for root)

        Returns:
            OperationResult with entity ID string on success, error message on failure
        """
        result = self._update_entity_command.execute(
            entity_id=entity_id,
            name_key=name_key,
            description_key=description_key,
            is_root_entity=is_root_entity,
            parent_entity_id=parent_entity_id,
        )

        if result.is_success():
            # Unwrap domain ID to string HERE (not in Presentation)
            return OperationResult.ok(result.value.value)
        else:
            return OperationResult.fail(result.error)

    def delete_entity(self, entity_id: str) -> OperationResult:
        """Delete an entity.

        Args:
            entity_id: Entity ID to delete

        Returns:
            OperationResult with None on success, error message on failure.
            Failure includes dependency details if entity is referenced by:
            - TABLE fields in other entities
            - LOOKUP fields in other entities
            - Child entities (parent_entity_id relationship)
        """
        result = self._delete_entity_command.execute(entity_id=entity_id)

        if result.is_success():
            return OperationResult.ok(None)
        else:
            return OperationResult.fail(result.error)

    def add_field(
        self,
        entity_id: str,
        field_id: str,
        field_type: str,
        label_key: str,
        help_text_key: Optional[str] = None,
        required: bool = False,
        default_value: Optional[str] = None,
        lookup_entity_id: Optional[str] = None,
        lookup_display_field: Optional[str] = None,
    ) -> OperationResult:
        """Add a field to an entity.

        Args:
            entity_id: Entity to add field to
            field_id: Unique field identifier
            field_type: Field type (TEXT, NUMBER, etc.)
            label_key: Translation key for field label
            help_text_key: Translation key for help text (optional)
            required: Whether field is required
            default_value: Default value (optional)
            lookup_entity_id: Entity ID for LOOKUP fields (required for LOOKUP)
            lookup_display_field: Field to display for LOOKUP fields (optional)

        Returns:
            OperationResult with field ID string on success, error message on failure

        INVARIANT - SELF-ENTITY LOOKUP:
            LOOKUP fields may only reference foreign entities.
            A LOOKUP field cannot reference its own entity (self-referential lookups
            are architecturally invalid and rejected at this layer).
        """
        # =====================================================================
        # SELF-ENTITY LOOKUP INVARIANT: LOOKUP fields cannot reference their own entity
        # =====================================================================
        if field_type.upper() == "LOOKUP" and lookup_entity_id:
            if lookup_entity_id.strip() == entity_id.strip():
                return OperationResult.fail(
                    "A LOOKUP field cannot reference its own entity."
                )

        # =====================================================================
        # LOOKUP DISPLAY FIELD INVARIANT: Must reference valid field in lookup entity
        # =====================================================================
        if field_type.upper() == "LOOKUP" and lookup_entity_id and lookup_display_field:
            validation_result = self._validate_lookup_display_field(
                lookup_entity_id=lookup_entity_id,
                lookup_display_field=lookup_display_field,
            )
            if not validation_result.success:
                return validation_result

        result = self._add_field_command.execute(
            entity_id=entity_id,
            field_id=field_id,
            field_type=field_type,
            label_key=label_key,
            help_text_key=help_text_key,
            required=required,
            default_value=default_value,
            lookup_entity_id=lookup_entity_id,
            lookup_display_field=lookup_display_field,
        )

        if result.is_success():
            # Unwrap domain ID to string HERE (not in Presentation)
            return OperationResult.ok(result.value.value)
        else:
            return OperationResult.fail(result.error)

    def update_field(
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
    ) -> OperationResult:
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
            OperationResult with field ID string on success, error message on failure.
            Note: Field type is immutable and cannot be changed.

        INVARIANT - SELF-ENTITY LOOKUP:
            LOOKUP fields may only reference foreign entities.
            A LOOKUP field cannot reference its own entity (self-referential lookups
            are architecturally invalid and rejected at this layer).

        INVARIANT - FORMULA DESIGN-TIME SEMANTICS:
            Formula is stored as an OPAQUE STRING. This method performs:
            - NO formula parsing
            - NO formula validation (syntax or field references)
            - NO formula execution
            Formula validation and evaluation are runtime/export responsibilities.
            Schema Designer stores formulas as opaque strings.
        """
        # =====================================================================
        # CALCULATED FIELD INVARIANT: Block required=True for CALCULATED fields
        # =====================================================================
        if required is True:
            from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
            entity_id_obj = EntityDefinitionId(entity_id.strip())
            load_result = self._schema_repository.get_by_id(entity_id_obj)
            if load_result.is_success():
                entity = load_result.value
                field_id_obj = FieldDefinitionId(field_id.strip())
                if field_id_obj in entity.fields:
                    field = entity.fields[field_id_obj]
                    if field.field_type.value.lower() == "calculated":
                        return OperationResult.fail(
                            "CALCULATED fields cannot be required. "
                            "They derive their values from formulas, not user input."
                        )

        # =====================================================================
        # SELF-ENTITY LOOKUP INVARIANT: LOOKUP fields cannot reference their own entity
        # =====================================================================
        if lookup_entity_id:
            if lookup_entity_id.strip() == entity_id.strip():
                return OperationResult.fail(
                    "A LOOKUP field cannot reference its own entity."
                )

        # =====================================================================
        # LOOKUP DISPLAY FIELD INVARIANT: Must reference valid field in lookup entity
        # =====================================================================
        if lookup_display_field is not None:
            # Need to determine the lookup_entity_id to validate against
            # Use the new value if provided, otherwise load from existing field
            target_lookup_entity_id = lookup_entity_id
            if target_lookup_entity_id is None:
                # Load existing field to get current lookup_entity_id
                from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
                entity_id_obj = EntityDefinitionId(entity_id.strip())
                load_result = self._schema_repository.get_by_id(entity_id_obj)
                if load_result.is_success():
                    entity = load_result.value
                    field_id_obj = FieldDefinitionId(field_id.strip())
                    if field_id_obj in entity.fields:
                        field = entity.fields[field_id_obj]
                        target_lookup_entity_id = field.lookup_entity_id

            # Validate if we have a lookup entity to validate against
            if target_lookup_entity_id and lookup_display_field.strip():
                validation_result = self._validate_lookup_display_field(
                    lookup_entity_id=target_lookup_entity_id,
                    lookup_display_field=lookup_display_field,
                )
                if not validation_result.success:
                    return validation_result

        result = self._update_field_command.execute(
            entity_id=entity_id,
            field_id=field_id,
            label_key=label_key,
            help_text_key=help_text_key,
            required=required,
            default_value=default_value,
            formula=formula,
            lookup_entity_id=lookup_entity_id,
            lookup_display_field=lookup_display_field,
            child_entity_id=child_entity_id,
        )

        if result.is_success():
            # Unwrap domain ID to string HERE (not in Presentation)
            return OperationResult.ok(result.value.value)
        else:
            return OperationResult.fail(result.error)

    def delete_field(self, entity_id: str, field_id: str) -> OperationResult:
        """Delete a field from an entity.

        Args:
            entity_id: Parent entity ID
            field_id: Field ID to delete

        Returns:
            OperationResult with None on success, error message on failure.
            Failure includes dependency details if field is referenced by:
            - Formulas in other fields
            - Control rules (as source or target)
            - LOOKUP fields (as lookup_display_field)
        """
        result = self._delete_field_command.execute(
            entity_id=entity_id,
            field_id=field_id,
        )

        if result.is_success():
            return OperationResult.ok(None)
        else:
            return OperationResult.fail(result.error)

    def create_relationship(
        self,
        relationship_id: str,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        name_key: str,
        description_key: Optional[str] = None,
        inverse_name_key: Optional[str] = None,
    ) -> OperationResult:
        """Create a new relationship.

        Args:
            relationship_id: Unique relationship identifier
            source_entity_id: Source entity ID
            target_entity_id: Target entity ID
            relationship_type: Type (CONTAINS, REFERENCES, ASSOCIATES)
            name_key: Translation key for relationship name
            description_key: Translation key for description (optional)
            inverse_name_key: Translation key for inverse name (optional)

        Returns:
            OperationResult with relationship ID string on success, error message on failure
        """
        if not self._create_relationship_command:
            return OperationResult.fail("Relationship creation not configured")

        result = self._create_relationship_command.execute(
            relationship_id=relationship_id,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relationship_type=relationship_type,
            name_key=name_key,
            description_key=description_key,
            inverse_name_key=inverse_name_key,
        )

        if result.is_success():
            # Unwrap domain ID to string HERE (not in Presentation)
            return OperationResult.ok(result.value.value)
        else:
            return OperationResult.fail(result.error)

    def update_relationship(
        self,
        relationship_id: str,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        name_key: str,
        description_key: Optional[str] = None,
        inverse_name_key: Optional[str] = None,
    ) -> OperationResult:
        """Update relationship metadata (DESIGN-TIME ONLY).

        INVARIANT: Relationships are design-time constructs.
        - Editing does NOT imply runtime behavior
        - Source and target entity cannot be changed
        - Only metadata fields can be updated
        - No cascade effects on fields or entities
        - Runtime semantics are deferred to later phases

        Args:
            relationship_id: ID of relationship to update (must exist)
            source_entity_id: Source entity (must match existing - cannot change)
            target_entity_id: Target entity (must match existing - cannot change)
            relationship_type: Type (CONTAINS, REFERENCES, ASSOCIATES)
            name_key: Updated translation key for relationship name
            description_key: Updated translation key for description (optional)
            inverse_name_key: Updated translation key for inverse name (optional)

        Returns:
            OperationResult with None on success, error message on failure
        """
        if not self._update_relationship_command:
            return OperationResult.fail("Relationship update not configured")

        result = self._update_relationship_command.execute(
            relationship_id=relationship_id,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relationship_type=relationship_type,
            name_key=name_key,
            description_key=description_key,
            inverse_name_key=inverse_name_key,
        )

        if result.is_success():
            return OperationResult.ok(None)
        else:
            return OperationResult.fail(result.error)

    def delete_relationship(
        self,
        relationship_id: str,
    ) -> OperationResult:
        """Delete relationship (DESIGN-TIME ONLY).

        INVARIANT: Relationships are design-time constructs.
        - Deletion does NOT cascade to fields
        - Deletion does NOT cascade to entities
        - Deletion does NOT modify other relationships
        - Runtime semantics are deferred to later phases

        Args:
            relationship_id: ID of relationship to delete

        Returns:
            OperationResult with None on success, error message on failure
        """
        if not self._delete_relationship_command:
            return OperationResult.fail("Relationship deletion not configured")

        result = self._delete_relationship_command.execute(
            relationship_id=relationship_id,
        )

        if result.is_success():
            return OperationResult.ok(None)
        else:
            return OperationResult.fail(result.error)

    def export_schema(
        self,
        schema_id: str,
        file_path: Path,
        version: Optional[str] = None,
    ) -> tuple[bool, Optional[ExportResult], Optional[str]]:
        """Export schema to JSON file.

        Args:
            schema_id: Identifier for the schema
            file_path: Path to write export file
            version: Optional semantic version string

        Returns:
            Tuple of (success, export_result, error_message):
            - success: True if export succeeded
            - export_result: ExportResult with data and warnings (on success)
            - error_message: Error message (on failure)
        """
        result = self._export_command.execute(
            schema_id=schema_id,
            file_path=file_path,
            version=version,
        )

        if result.is_success():
            return (True, result.value, None)
        else:
            return (False, None, result.error)

    def import_schema(
        self,
        file_path: Path,
        enforcement_policy: EnforcementPolicy = EnforcementPolicy.STRICT,
        identical_action: IdenticalSchemaAction = IdenticalSchemaAction.SKIP,
        force: bool = False,
    ) -> ImportResult:
        """Import schema from JSON file.

        Args:
            file_path: Path to JSON import file
            enforcement_policy: How to handle compatibility issues
                - STRICT: Block incompatible schemas (default)
                - WARN: Allow with warnings
                - NONE: No compatibility checking
            identical_action: What to do when schema is identical
                - SKIP: Do nothing (default)
                - REPLACE: Replace anyway
            force: Force import even if incompatible (overrides enforcement_policy)

        Returns:
            ImportResult with:
            - success: True if import succeeded
            - entity_count, field_count, relationship_count: Imported counts
            - warnings: Tuple of ImportWarning
            - validation_errors: Tuple of ImportValidationError (on failure)
            - compatibility_result: CompatibilityResult (if checked)
            - was_identical: True if schema was identical
            - was_skipped: True if import was skipped
            - error: Error message (on failure)
        """
        return self._import_command.execute(
            file_path=file_path,
            enforcement_policy=enforcement_policy,
            identical_action=identical_action,
            force=force,
        )

    def add_constraint(
        self,
        entity_id: str,
        field_id: str,
        constraint_type: str,
        value: Optional[float] = None,
        severity: str = "ERROR",
        # Phase SD-6: Additional parameters for advanced constraints
        pattern: Optional[str] = None,
        pattern_description: Optional[str] = None,
        allowed_values: Optional[tuple] = None,
        allowed_extensions: Optional[tuple] = None,
        max_size_bytes: Optional[int] = None,
    ) -> OperationResult:
        """Add a validation constraint to a field.

        Args:
            entity_id: Entity containing the field
            field_id: Field to add constraint to
            constraint_type: Type of constraint:
                - "REQUIRED": Field value must not be empty
                - "MIN_VALUE": Field value must be >= value
                - "MAX_VALUE": Field value must be <= value
                - "MIN_LENGTH": Field value must have >= value characters
                - "MAX_LENGTH": Field value must have <= value characters
                - "PATTERN": Field value must match regex pattern
                - "ALLOWED_VALUES": Field value must be one of allowed values
                - "FILE_EXTENSION": File must have one of allowed extensions
                - "MAX_FILE_SIZE": File size must not exceed max_size_bytes
            value: Numeric value (for MIN/MAX types)
            severity: Severity level ("ERROR", "WARNING", "INFO"), defaults to "ERROR"
            pattern: Regex pattern string (for PATTERN constraint)
            pattern_description: Human-readable description of pattern (for PATTERN)
            allowed_values: Tuple of allowed values (for ALLOWED_VALUES constraint)
            allowed_extensions: Tuple of allowed file extensions (for FILE_EXTENSION)
            max_size_bytes: Maximum file size in bytes (for MAX_FILE_SIZE)

        Returns:
            OperationResult with field ID string on success, error message on failure
        """
        # Parse severity
        try:
            severity_enum = Severity(severity.upper())
        except ValueError:
            return OperationResult.fail(
                f"Invalid severity: {severity}. Must be ERROR, WARNING, or INFO."
            )

        # Construct the appropriate constraint (domain construction happens HERE)
        constraint_type_upper = constraint_type.upper()
        try:
            if constraint_type_upper == "REQUIRED":
                constraint = RequiredConstraint(severity=severity_enum)

            elif constraint_type_upper == "MIN_VALUE":
                if value is None:
                    return OperationResult.fail("value is required for MIN_VALUE constraint")
                constraint = MinValueConstraint(min_value=float(value), severity=severity_enum)

            elif constraint_type_upper == "MAX_VALUE":
                if value is None:
                    return OperationResult.fail("value is required for MAX_VALUE constraint")
                constraint = MaxValueConstraint(max_value=float(value), severity=severity_enum)

            elif constraint_type_upper == "MIN_LENGTH":
                if value is None:
                    return OperationResult.fail("value is required for MIN_LENGTH constraint")
                constraint = MinLengthConstraint(min_length=int(value), severity=severity_enum)

            elif constraint_type_upper == "MAX_LENGTH":
                if value is None:
                    return OperationResult.fail("value is required for MAX_LENGTH constraint")
                constraint = MaxLengthConstraint(max_length=int(value), severity=severity_enum)

            # Phase SD-6: Advanced constraints
            elif constraint_type_upper == "PATTERN":
                if not pattern:
                    return OperationResult.fail("pattern is required for PATTERN constraint")
                constraint = PatternConstraint(
                    pattern=pattern,
                    description=pattern_description,
                    severity=severity_enum,
                )

            elif constraint_type_upper == "ALLOWED_VALUES":
                if not allowed_values:
                    return OperationResult.fail(
                        "allowed_values is required for ALLOWED_VALUES constraint"
                    )
                if not isinstance(allowed_values, tuple):
                    return OperationResult.fail("allowed_values must be a tuple")
                constraint = AllowedValuesConstraint(
                    allowed_values=allowed_values,
                    severity=severity_enum,
                )

            elif constraint_type_upper == "FILE_EXTENSION":
                if not allowed_extensions:
                    return OperationResult.fail(
                        "allowed_extensions is required for FILE_EXTENSION constraint"
                    )
                if not isinstance(allowed_extensions, tuple):
                    return OperationResult.fail("allowed_extensions must be a tuple")
                constraint = FileExtensionConstraint(
                    allowed_extensions=allowed_extensions,
                    severity=severity_enum,
                )

            elif constraint_type_upper == "MAX_FILE_SIZE":
                if max_size_bytes is None:
                    return OperationResult.fail(
                        "max_size_bytes is required for MAX_FILE_SIZE constraint"
                    )
                constraint = MaxFileSizeConstraint(
                    max_size_bytes=int(max_size_bytes),
                    severity=severity_enum,
                )

            else:
                return OperationResult.fail(
                    f"Unknown constraint type: {constraint_type}. "
                    "Supported types: REQUIRED, MIN_VALUE, MAX_VALUE, MIN_LENGTH, MAX_LENGTH, "
                    "PATTERN, ALLOWED_VALUES, FILE_EXTENSION, MAX_FILE_SIZE"
                )
        except ValueError as e:
            return OperationResult.fail(f"Invalid constraint value: {e}")

        # =====================================================================
        # SINGLE ENTITY LOAD: All validation derives from ONE entity snapshot
        # Invariant: One usecase execution = one entity snapshot
        # =====================================================================
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        entity_id_obj = EntityDefinitionId(entity_id.strip())
        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return OperationResult.fail(f"Entity '{entity_id}' not found")

        entity = load_result.value
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return OperationResult.fail(f"Field '{field_id}' not found in entity '{entity_id}'")

        field = entity.fields[field_id_obj]
        field_type_str = field.field_type.value.lower()

        # =====================================================================
        # CALCULATED FIELD INVARIANT: CALCULATED fields cannot have any constraints
        # This is a semantic invariant - calculated fields derive their values
        # from formulas and should not have validation constraints.
        # =====================================================================
        if field_type_str == "calculated":
            return OperationResult.fail(
                "CALCULATED fields cannot have validation constraints. "
                "Calculated values are derived from formulas and are not user-editable."
            )

        # DOMAIN SOURCE OF TRUTH: Use field.constraints for all validation
        # DTOs are presentation-only and forbidden as validation sources
        domain_constraints = field.constraints

        # =====================================================================
        # UNIQUENESS INVARIANT: Each constraint type may exist at most once per field.
        # Check BEFORE executing the command to prevent duplicates.
        # =====================================================================
        constraint_class_name = type(constraint).__name__
        for existing in domain_constraints:
            if type(existing).__name__ == constraint_class_name:
                return OperationResult.fail(
                    f"A {constraint_type_upper} constraint already exists for this field. "
                    "Each constraint type may only appear once per field. "
                    "Delete the existing constraint first if you want to change its value."
                )

        # =====================================================================
        # FIELD TYPE COMPATIBILITY: Constraint must be valid for field type
        # =====================================================================
        if constraint_type_upper in ("MIN_VALUE", "MAX_VALUE"):
            # Numeric constraints only allowed on NUMBER or DATE fields.
            # Note: DATE is treated as numeric for MIN_VALUE/MAX_VALUE constraints
            # (dates are compared as ordinal values).
            if field_type_str not in ("number", "date"):
                return OperationResult.fail(
                    f"{constraint_type_upper} constraint is only valid for NUMBER or DATE fields, "
                    f"not {field_type_str.upper()} fields."
                )

        if constraint_type_upper in ("MIN_LENGTH", "MAX_LENGTH"):
            # Text length constraints only allowed on TEXT or TEXTAREA fields
            if field_type_str not in ("text", "textarea"):
                return OperationResult.fail(
                    f"{constraint_type_upper} constraint is only valid for TEXT or TEXTAREA fields, "
                    f"not {field_type_str.upper()} fields."
                )

        # =====================================================================
        # SEMANTIC CROSS-CONSTRAINT VALIDATION: min <= max invariants
        # Uses DOMAIN constraints directly (not DTOs)
        # =====================================================================
        if constraint_type_upper == "MIN_VALUE":
            # Check if MAX_VALUE exists and validate min_value <= max_value
            for existing in domain_constraints:
                if isinstance(existing, MaxValueConstraint):
                    existing_max = existing.max_value
                    if value is not None and value > existing_max:
                        return OperationResult.fail(
                            f"MIN_VALUE ({value}) must be less than or equal to MAX_VALUE ({existing_max})."
                        )

        if constraint_type_upper == "MAX_VALUE":
            # Check if MIN_VALUE exists and validate min_value <= max_value
            for existing in domain_constraints:
                if isinstance(existing, MinValueConstraint):
                    existing_min = existing.min_value
                    if value is not None and existing_min > value:
                        return OperationResult.fail(
                            f"MIN_VALUE ({existing_min}) must be less than or equal to MAX_VALUE ({value})."
                        )

        if constraint_type_upper == "MIN_LENGTH":
            # Check if MAX_LENGTH exists and validate min_length <= max_length
            for existing in domain_constraints:
                if isinstance(existing, MaxLengthConstraint):
                    existing_max = existing.max_length
                    if value is not None and value > existing_max:
                        return OperationResult.fail(
                            f"MIN_LENGTH ({int(value)}) must be less than or equal to MAX_LENGTH ({existing_max})."
                        )

        if constraint_type_upper == "MAX_LENGTH":
            # Check if MIN_LENGTH exists and validate min_length <= max_length
            for existing in domain_constraints:
                if isinstance(existing, MinLengthConstraint):
                    existing_min = existing.min_length
                    if value is not None and existing_min > value:
                        return OperationResult.fail(
                            f"MIN_LENGTH ({existing_min}) must be less than or equal to MAX_LENGTH ({int(value)})."
                        )

        # Execute command
        result = self._add_constraint_command.execute(
            entity_id=entity_id,
            field_id=field_id,
            constraint=constraint,
        )

        if result.is_success():
            return OperationResult.ok(result.value.value)
        else:
            return OperationResult.fail(result.error)

    def get_entity_list_for_selection(self) -> tuple[tuple[str, str], ...]:
        """Get list of entities for dropdown/selection UI.

        Returns:
            Tuple of (entity_id, entity_name) pairs
        """
        entities = self.get_all_entities()
        return tuple((entity.id, entity.name) for entity in entities)

    # =========================================================================
    # Constraint Query Operations (Phase R-2)
    # =========================================================================

    def list_constraints_for_field(
        self,
        entity_id: str,
        field_id: str,
    ) -> tuple[ConstraintExportDTO, ...]:
        """List all constraints for a field (Phase R-2).

        Args:
            entity_id: Entity containing the field
            field_id: Field to list constraints for

        Returns:
            Tuple of ConstraintExportDTO for the field.
            Empty tuple if entity/field not found or has no constraints.
            Severity is included in parameters dict.

        Phase R-2 Compliance:
            - Read-only query
            - Returns DTOs only
            - Severity included in parameters
        """
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        # Get entity
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return ()

        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return ()

        entity = load_result.value

        # Get field
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return ()

        field = entity.fields[field_id_obj]

        # Convert domain constraints to ConstraintExportDTOs with severity
        constraint_dtos = []
        for constraint in field.constraints:
            # Get constraint type name
            constraint_type = type(constraint).__name__
            parameters: dict = {}

            # Extract constraint-specific parameters
            if isinstance(constraint, RequiredConstraint):
                # No additional parameters for required constraint
                pass
            elif isinstance(constraint, MinLengthConstraint):
                parameters["min_length"] = constraint.min_length
            elif isinstance(constraint, MaxLengthConstraint):
                parameters["max_length"] = constraint.max_length
            elif isinstance(constraint, MinValueConstraint):
                parameters["min_value"] = constraint.min_value
            elif isinstance(constraint, MaxValueConstraint):
                parameters["max_value"] = constraint.max_value
            elif isinstance(constraint, PatternConstraint):
                parameters["pattern"] = constraint.pattern
                if constraint.description:
                    parameters["description"] = constraint.description
            elif isinstance(constraint, AllowedValuesConstraint):
                parameters["allowed_values"] = list(constraint.allowed_values)
            elif isinstance(constraint, FileExtensionConstraint):
                parameters["allowed_extensions"] = list(constraint.allowed_extensions)
            elif isinstance(constraint, MaxFileSizeConstraint):
                parameters["max_size_bytes"] = constraint.max_size_bytes

            # Always include severity (Phase R-2 requirement)
            parameters["severity"] = constraint.severity.value

            constraint_dtos.append(
                ConstraintExportDTO(
                    constraint_type=constraint_type,
                    parameters=parameters,
                )
            )

        return tuple(constraint_dtos)

    # =========================================================================
    # Control Rule Operations (Phase F-10)
    # =========================================================================

    def add_control_rule(
        self,
        entity_id: str,
        field_id: str,
        rule_type: str,
        formula_text: str,
    ) -> OperationResult:
        """Add a control rule to a field (Phase F-10).

        Validates the control rule using Formula Governance (F-6) and
        Boolean enforcement (F-8) before adding.

        Args:
            entity_id: Entity containing the field
            field_id: Field to add control rule to (this is the target field)
            rule_type: Type of control rule (VISIBILITY, ENABLED, REQUIRED)
            formula_text: Boolean formula expression

        Returns:
            OperationResult with field ID on success, error message on failure.
            Failure reasons:
            - Entity or field not found
            - Invalid rule type
            - Formula governance failed (F-6)
            - Formula is not BOOLEAN type (F-8)

        Phase F-10 Compliance:
            - Design-time only (NO runtime execution)
            - NO observers, listeners, signals
            - NO field mutation
            - Schema persistence via repository
        """
        from dataclasses import replace
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        # Validate rule_type
        try:
            control_rule_type = ControlRuleType(rule_type.upper())
        except ValueError:
            return OperationResult.fail(
                f"Invalid rule type: {rule_type}. "
                "Must be VISIBILITY, ENABLED, or REQUIRED."
            )

        # Get entity
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return OperationResult.fail(f"Entity not found: {entity_id}")

        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return OperationResult.fail(f"Failed to load entity: {load_result.error}")

        entity = load_result.value

        # Get field
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return OperationResult.fail(
                f"Field not found: {field_id} in entity {entity_id}"
            )

        field = entity.fields[field_id_obj]

        # Build schema fields for validation
        schema_fields = self._build_schema_fields_for_entity(entity)

        # Validate control rule using ControlRuleUseCases (F-6, F-8)
        validation_result = self._control_rule_usecases.validate_control_rule(
            rule_type=control_rule_type,
            target_field_id=field_id,
            formula_text=formula_text,
            schema_fields=schema_fields,
        )

        # Check validation result
        if validation_result.status == ControlRuleStatus.BLOCKED:
            return OperationResult.fail(
                f"Control rule blocked: {validation_result.block_reason}"
            )

        if validation_result.status == ControlRuleStatus.CLEARED:
            return OperationResult.fail(
                "Cannot add control rule with empty formula"
            )

        # Check for duplicate rule type on field
        for existing_rule in field.control_rules:
            if isinstance(existing_rule, ControlRuleExportDTO):
                if existing_rule.rule_type == rule_type.upper():
                    return OperationResult.fail(
                        f"Field already has a {rule_type} control rule. "
                        "Use update_control_rule() to modify it."
                    )

        # Create control rule DTO
        control_rule_dto = ControlRuleExportDTO(
            rule_type=rule_type.upper(),
            target_field_id=field_id,
            formula_text=formula_text,
        )

        # Update field with new control rule
        new_control_rules = field.control_rules + (control_rule_dto,)
        updated_field = replace(field, control_rules=new_control_rules)

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return OperationResult.fail(f"Failed to add control rule: {save_result.error}")

        return OperationResult.ok(field_id)

    def update_control_rule(
        self,
        entity_id: str,
        field_id: str,
        rule_type: str,
        formula_text: str,
    ) -> OperationResult:
        """Update an existing control rule (Phase F-10).

        Re-validates the control rule using Formula Governance (F-6) and
        Boolean enforcement (F-8) before updating.

        Args:
            entity_id: Entity containing the field
            field_id: Field with the control rule
            rule_type: Type of control rule to update (VISIBILITY, ENABLED, REQUIRED)
            formula_text: New boolean formula expression

        Returns:
            OperationResult with field ID on success, error message on failure.
            Failure reasons:
            - Entity or field not found
            - Control rule of specified type not found
            - Formula governance failed (F-6)
            - Formula is not BOOLEAN type (F-8)

        Phase F-10 Compliance:
            - Design-time only (NO runtime execution)
            - NO observers, listeners, signals
            - NO field mutation
            - Schema persistence via repository
        """
        from dataclasses import replace
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        # Validate rule_type
        try:
            control_rule_type = ControlRuleType(rule_type.upper())
        except ValueError:
            return OperationResult.fail(
                f"Invalid rule type: {rule_type}. "
                "Must be VISIBILITY, ENABLED, or REQUIRED."
            )

        # Get entity
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return OperationResult.fail(f"Entity not found: {entity_id}")

        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return OperationResult.fail(f"Failed to load entity: {load_result.error}")

        entity = load_result.value

        # Get field
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return OperationResult.fail(
                f"Field not found: {field_id} in entity {entity_id}"
            )

        field = entity.fields[field_id_obj]

        # Find existing rule to update
        rule_found = False
        rule_index = -1
        for i, existing_rule in enumerate(field.control_rules):
            if isinstance(existing_rule, ControlRuleExportDTO):
                if existing_rule.rule_type == rule_type.upper():
                    rule_found = True
                    rule_index = i
                    break

        if not rule_found:
            return OperationResult.fail(
                f"No {rule_type} control rule found on field {field_id}. "
                "Use add_control_rule() to create one."
            )

        # Build schema fields for validation
        schema_fields = self._build_schema_fields_for_entity(entity)

        # Validate updated control rule using ControlRuleUseCases (F-6, F-8)
        validation_result = self._control_rule_usecases.validate_control_rule(
            rule_type=control_rule_type,
            target_field_id=field_id,
            formula_text=formula_text,
            schema_fields=schema_fields,
        )

        # Check validation result
        if validation_result.status == ControlRuleStatus.BLOCKED:
            return OperationResult.fail(
                f"Control rule blocked: {validation_result.block_reason}"
            )

        if validation_result.status == ControlRuleStatus.CLEARED:
            # Empty formula means delete the rule
            return self.delete_control_rule(entity_id, field_id, rule_type)

        # Create updated control rule DTO
        updated_rule_dto = ControlRuleExportDTO(
            rule_type=rule_type.upper(),
            target_field_id=field_id,
            formula_text=formula_text,
        )

        # Replace the rule in the tuple
        rules_list = list(field.control_rules)
        rules_list[rule_index] = updated_rule_dto
        new_control_rules = tuple(rules_list)

        # Update field with modified control rules
        updated_field = replace(field, control_rules=new_control_rules)

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return OperationResult.fail(f"Failed to update control rule: {save_result.error}")

        return OperationResult.ok(field_id)

    def delete_control_rule(
        self,
        entity_id: str,
        field_id: str,
        rule_type: str,
    ) -> OperationResult:
        """Delete a control rule from a field (Phase F-10).

        Args:
            entity_id: Entity containing the field
            field_id: Field with the control rule
            rule_type: Type of control rule to delete (VISIBILITY, ENABLED, REQUIRED)

        Returns:
            OperationResult with field ID on success, error message on failure.
            Failure reasons:
            - Entity or field not found
            - Control rule of specified type not found

        Phase F-10 Compliance:
            - Design-time only (NO runtime execution)
            - NO observers, listeners, signals
            - NO field mutation
            - Schema persistence via repository
        """
        from dataclasses import replace
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        # Validate rule_type
        try:
            ControlRuleType(rule_type.upper())
        except ValueError:
            return OperationResult.fail(
                f"Invalid rule type: {rule_type}. "
                "Must be VISIBILITY, ENABLED, or REQUIRED."
            )

        # Get entity
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return OperationResult.fail(f"Entity not found: {entity_id}")

        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return OperationResult.fail(f"Failed to load entity: {load_result.error}")

        entity = load_result.value

        # Get field
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return OperationResult.fail(
                f"Field not found: {field_id} in entity {entity_id}"
            )

        field = entity.fields[field_id_obj]

        # Find and remove the rule
        rule_found = False
        new_rules = []
        for existing_rule in field.control_rules:
            if isinstance(existing_rule, ControlRuleExportDTO):
                if existing_rule.rule_type == rule_type.upper():
                    rule_found = True
                    continue  # Skip this rule (delete it)
            new_rules.append(existing_rule)

        if not rule_found:
            return OperationResult.fail(
                f"No {rule_type} control rule found on field {field_id}"
            )

        # Update field with modified control rules
        updated_field = replace(field, control_rules=tuple(new_rules))

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return OperationResult.fail(f"Failed to delete control rule: {save_result.error}")

        return OperationResult.ok(field_id)

    def list_control_rules_for_field(
        self,
        entity_id: str,
        field_id: str,
    ) -> tuple[ControlRuleExportDTO, ...]:
        """List all control rules for a field (Phase F-10).

        Args:
            entity_id: Entity containing the field
            field_id: Field to list control rules for

        Returns:
            Tuple of ControlRuleExportDTO for the field.
            Empty tuple if entity/field not found or has no rules.

        Phase F-10 Compliance:
            - Read-only query
            - Returns DTOs only
            - No execution
        """
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        # Get entity
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return ()

        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return ()

        entity = load_result.value

        # Get field
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return ()

        field = entity.fields[field_id_obj]

        # Filter to ControlRuleExportDTO only
        rules = []
        for rule in field.control_rules:
            if isinstance(rule, ControlRuleExportDTO):
                rules.append(rule)

        return tuple(rules)

    # =========================================================================
    # Output Mapping Methods (Phase F-12.5)
    # =========================================================================

    def add_output_mapping(
        self,
        entity_id: str,
        field_id: str,
        target: str,
        formula_text: str,
    ) -> OperationResult:
        """Add an output mapping to a field (Phase F-12.5).

        Args:
            entity_id: Entity containing the field
            field_id: Field to add output mapping to
            target: Output target type (TEXT, NUMBER, BOOLEAN)
            formula_text: Formula expression for output transformation

        Returns:
            OperationResult with field ID on success, error message on failure.
            Failure reasons:
            - Entity or field not found
            - Empty target or formula
            - Duplicate target type already exists

        Phase F-12.5 Compliance:
            - Design-time only (NO runtime execution)
            - NO validation logic (validation in import/export layer)
            - NO observers, listeners, signals
            - Schema persistence via repository
        """
        from dataclasses import replace
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        # Validate target and formula are not empty
        if not target or not target.strip():
            return OperationResult.fail("Output mapping target cannot be empty")

        if not formula_text or not formula_text.strip():
            return OperationResult.fail("Output mapping formula_text cannot be empty")

        target = target.strip().upper()

        # Get entity
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return OperationResult.fail(f"Entity not found: {entity_id}")

        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return OperationResult.fail(f"Failed to load entity: {load_result.error}")

        entity = load_result.value

        # Get field
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return OperationResult.fail(
                f"Field not found: {field_id} in entity {entity_id}"
            )

        field = entity.fields[field_id_obj]

        # Check for duplicate target type on field
        for existing_mapping in field.output_mappings:
            if isinstance(existing_mapping, OutputMappingExportDTO):
                if existing_mapping.target == target:
                    return OperationResult.fail(
                        f"Field already has an output mapping for target {target}. "
                        "Use update_output_mapping() to modify it."
                    )

        # Create output mapping DTO
        output_mapping_dto = OutputMappingExportDTO(
            target=target,
            formula_text=formula_text.strip(),
        )

        # Update field with new output mapping
        new_output_mappings = field.output_mappings + (output_mapping_dto,)
        updated_field = replace(field, output_mappings=new_output_mappings)

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return OperationResult.fail(f"Failed to add output mapping: {save_result.error}")

        return OperationResult.ok(field_id)

    def update_output_mapping(
        self,
        entity_id: str,
        field_id: str,
        target: str,
        formula_text: str,
    ) -> OperationResult:
        """Update an existing output mapping (Phase F-12.5).

        Args:
            entity_id: Entity containing the field
            field_id: Field with the output mapping
            target: Output target type to update (TEXT, NUMBER, BOOLEAN)
            formula_text: New formula expression for output transformation

        Returns:
            OperationResult with field ID on success, error message on failure.
            Failure reasons:
            - Entity or field not found
            - Output mapping of specified target not found
            - Empty formula (use delete_output_mapping instead)

        Phase F-12.5 Compliance:
            - Design-time only (NO runtime execution)
            - NO validation logic (validation in import/export layer)
            - NO observers, listeners, signals
            - Schema persistence via repository
        """
        from dataclasses import replace
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        # Validate target and formula are not empty
        if not target or not target.strip():
            return OperationResult.fail("Output mapping target cannot be empty")

        if not formula_text or not formula_text.strip():
            return OperationResult.fail(
                "Output mapping formula_text cannot be empty. "
                "Use delete_output_mapping() to remove the mapping."
            )

        target = target.strip().upper()

        # Get entity
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return OperationResult.fail(f"Entity not found: {entity_id}")

        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return OperationResult.fail(f"Failed to load entity: {load_result.error}")

        entity = load_result.value

        # Get field
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return OperationResult.fail(
                f"Field not found: {field_id} in entity {entity_id}"
            )

        field = entity.fields[field_id_obj]

        # Find existing mapping to update
        mapping_found = False
        mapping_index = -1
        for i, existing_mapping in enumerate(field.output_mappings):
            if isinstance(existing_mapping, OutputMappingExportDTO):
                if existing_mapping.target == target:
                    mapping_found = True
                    mapping_index = i
                    break

        if not mapping_found:
            return OperationResult.fail(
                f"No output mapping for target {target} found on field {field_id}. "
                "Use add_output_mapping() to create one."
            )

        # Create updated output mapping DTO
        updated_mapping_dto = OutputMappingExportDTO(
            target=target,
            formula_text=formula_text.strip(),
        )

        # Replace the mapping in the tuple
        mappings_list = list(field.output_mappings)
        mappings_list[mapping_index] = updated_mapping_dto
        new_output_mappings = tuple(mappings_list)

        # Update field with modified output mappings
        updated_field = replace(field, output_mappings=new_output_mappings)

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return OperationResult.fail(f"Failed to update output mapping: {save_result.error}")

        return OperationResult.ok(field_id)

    def delete_output_mapping(
        self,
        entity_id: str,
        field_id: str,
        target: str,
    ) -> OperationResult:
        """Delete an output mapping from a field (Phase F-12.5).

        Args:
            entity_id: Entity containing the field
            field_id: Field with the output mapping
            target: Output target type to delete (TEXT, NUMBER, BOOLEAN)

        Returns:
            OperationResult with field ID on success, error message on failure.
            Failure reasons:
            - Entity or field not found
            - Output mapping of specified target not found

        Phase F-12.5 Compliance:
            - Design-time only (NO runtime execution)
            - NO observers, listeners, signals
            - Schema persistence via repository
        """
        from dataclasses import replace
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        # Validate target is not empty
        if not target or not target.strip():
            return OperationResult.fail("Output mapping target cannot be empty")

        target = target.strip().upper()

        # Get entity
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return OperationResult.fail(f"Entity not found: {entity_id}")

        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return OperationResult.fail(f"Failed to load entity: {load_result.error}")

        entity = load_result.value

        # Get field
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return OperationResult.fail(
                f"Field not found: {field_id} in entity {entity_id}"
            )

        field = entity.fields[field_id_obj]

        # Find and remove the mapping
        mapping_found = False
        new_mappings = []
        for existing_mapping in field.output_mappings:
            if isinstance(existing_mapping, OutputMappingExportDTO):
                if existing_mapping.target == target:
                    mapping_found = True
                    continue  # Skip this mapping (delete it)
            new_mappings.append(existing_mapping)

        if not mapping_found:
            return OperationResult.fail(
                f"No output mapping for target {target} found on field {field_id}"
            )

        # Update field with modified output mappings
        updated_field = replace(field, output_mappings=tuple(new_mappings))

        # Update entity's field via aggregate method
        entity.update_field(field_id_obj, updated_field)

        # Save updated entity
        save_result = self._schema_repository.save(entity)
        if save_result.is_failure():
            return OperationResult.fail(f"Failed to delete output mapping: {save_result.error}")

        return OperationResult.ok(field_id)

    def list_output_mappings_for_field(
        self,
        entity_id: str,
        field_id: str,
    ) -> tuple[OutputMappingExportDTO, ...]:
        """List all output mappings for a field (Phase F-12.5).

        Args:
            entity_id: Entity containing the field
            field_id: Field to list output mappings for

        Returns:
            Tuple of OutputMappingExportDTO for the field.
            Empty tuple if entity/field not found or has no mappings.

        Phase F-12.5 Compliance:
            - Read-only query
            - Returns DTOs only
            - No execution
        """
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        # Get entity
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return ()

        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return ()

        entity = load_result.value

        # Get field
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return ()

        field = entity.fields[field_id_obj]

        # Filter to OutputMappingExportDTO only
        mappings = []
        for mapping in field.output_mappings:
            if isinstance(mapping, OutputMappingExportDTO):
                mappings.append(mapping)

        return tuple(mappings)

    def _build_schema_fields_for_entity(
        self,
        entity,
    ) -> tuple[SchemaFieldInfoDTO, ...]:
        """Build SchemaFieldInfoDTO tuple for validation.

        Args:
            entity: EntityDefinition to extract fields from

        Returns:
            Tuple of SchemaFieldInfoDTO for all fields in the entity
        """
        schema_fields = []
        for field_def in entity.fields.values():
            # Translate label key to get display label
            label = self._translation_service.translate(field_def.label_key.key)
            field_info = SchemaFieldInfoDTO(
                field_id=field_def.id.value,
                field_type=field_def.field_type.value,
                entity_id=entity.id.value,
                label=label,
            )
            schema_fields.append(field_info)
        return tuple(schema_fields)

    # =========================================================================
    # Field Option Methods (Phase F-14) - DROPDOWN/RADIO only
    # =========================================================================

    def add_field_option(
        self,
        entity_id: str,
        field_id: str,
        option_value: str,
        option_label_key: str,
    ) -> OperationResult:
        """Add an option to a choice field (Phase F-14).

        Args:
            entity_id: Entity containing the field
            field_id: Field to add option to (must be DROPDOWN or RADIO)
            option_value: Option value (unique identifier within field)
            option_label_key: Translation key for option label

        Returns:
            OperationResult with field ID on success, error message on failure.
            Failure reasons:
            - Entity or field not found
            - Field is not a choice type (DROPDOWN, RADIO)
            - Option value already exists in field

        Phase F-14 Compliance:
            - Design-time only (NO runtime execution)
            - NO observers, listeners, signals
            - Schema persistence via repository
        """
        result = self._add_field_option_command.execute(
            entity_id=entity_id,
            field_id=field_id,
            option_value=option_value,
            option_label_key=option_label_key,
        )

        if result.is_success():
            return OperationResult.ok(result.value.value)
        else:
            return OperationResult.fail(result.error)

    def update_field_option(
        self,
        entity_id: str,
        field_id: str,
        option_value: str,
        new_label_key: str,
    ) -> OperationResult:
        """Update an option's label key in a choice field (Phase F-14).

        Args:
            entity_id: Entity containing the field
            field_id: Field containing the option
            option_value: Option value to update (identifier, immutable)
            new_label_key: New translation key for option label

        Returns:
            OperationResult with field ID on success, error message on failure.
            Failure reasons:
            - Entity or field not found
            - Field is not a choice type (DROPDOWN, RADIO)
            - Option value not found in field

        Phase F-14 Compliance:
            - Design-time only (NO runtime execution)
            - NO observers, listeners, signals
            - Option values are immutable (only label_key can change)
            - Schema persistence via repository
        """
        result = self._update_field_option_command.execute(
            entity_id=entity_id,
            field_id=field_id,
            option_value=option_value,
            new_label_key=new_label_key,
        )

        if result.is_success():
            return OperationResult.ok(result.value.value)
        else:
            return OperationResult.fail(result.error)

    def delete_field_option(
        self,
        entity_id: str,
        field_id: str,
        option_value: str,
    ) -> OperationResult:
        """Delete an option from a choice field (Phase F-14).

        Args:
            entity_id: Entity containing the field
            field_id: Field to delete option from
            option_value: Option value to delete

        Returns:
            OperationResult with field ID on success, error message on failure.
            Failure reasons:
            - Entity or field not found
            - Field is not a choice type (DROPDOWN, RADIO)
            - Option value not found in field

        Phase F-14 Compliance:
            - Design-time only (NO runtime execution)
            - NO observers, listeners, signals
            - Schema persistence via repository
        """
        result = self._delete_field_option_command.execute(
            entity_id=entity_id,
            field_id=field_id,
            option_value=option_value,
        )

        if result.is_success():
            return OperationResult.ok(result.value.value)
        else:
            return OperationResult.fail(result.error)

    def reorder_field_options(
        self,
        entity_id: str,
        field_id: str,
        new_option_order: list[str],
    ) -> OperationResult:
        """Reorder options in a choice field (Phase F-14).

        Args:
            entity_id: Entity containing the field
            field_id: Field to reorder options in
            new_option_order: List of option values in desired order.
                Must contain exactly the same option values as the field
                (no duplicates, no missing, no extra).

        Returns:
            OperationResult with field ID on success, error message on failure.
            Failure reasons:
            - Entity or field not found
            - Field is not a choice type (DROPDOWN, RADIO)
            - new_option_order contains duplicates
            - new_option_order is missing existing options
            - new_option_order contains unknown options

        Phase F-14 Compliance:
            - Design-time only (NO runtime execution)
            - NO observers, listeners, signals
            - Option values and labels are preserved, only order changes
            - Schema persistence via repository
        """
        result = self._reorder_field_options_command.execute(
            entity_id=entity_id,
            field_id=field_id,
            new_option_order=new_option_order,
        )

        if result.is_success():
            return OperationResult.ok(result.value.value)
        else:
            return OperationResult.fail(result.error)

    def list_field_options(
        self,
        entity_id: str,
        field_id: str,
    ) -> tuple[FieldOptionExportDTO, ...]:
        """List all options for a choice field (Phase F-14).

        Args:
            entity_id: Entity containing the field
            field_id: Field to list options for

        Returns:
            Tuple of FieldOptionExportDTO for the field.
            Empty tuple if entity/field not found or field has no options.
            Note: Returns empty tuple for non-choice fields (TEXT, NUMBER, etc.).

        Phase F-14 Compliance:
            - Read-only query
            - Returns DTOs only (label_key, not translated)
            - Design-time data structure
        """
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        # Get entity
        entity_id_obj = EntityDefinitionId(entity_id.strip())
        if not self._schema_repository.exists(entity_id_obj):
            return ()

        load_result = self._schema_repository.get_by_id(entity_id_obj)
        if load_result.is_failure():
            return ()

        entity = load_result.value

        # Get field
        field_id_obj = FieldDefinitionId(field_id.strip())
        if field_id_obj not in entity.fields:
            return ()

        field = entity.fields[field_id_obj]

        # Convert domain options to DTOs
        option_dtos = []
        for value, label_key in field.options:
            # label_key is a TranslationKey, convert to string
            label_key_str = label_key.key if hasattr(label_key, 'key') else str(label_key)
            option_dtos.append(
                FieldOptionExportDTO(
                    value=value,
                    label_key=label_key_str,
                )
            )

        return tuple(option_dtos)

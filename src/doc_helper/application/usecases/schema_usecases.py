"""Schema Use Cases (Architecture Enforcement Phase, updated Phase F-10, Phase F-12.5).

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
"""

from pathlib import Path
from typing import Optional

from doc_helper.application.commands.schema.add_field_command import AddFieldCommand
from doc_helper.application.commands.schema.add_field_constraint_command import (
    AddFieldConstraintCommand,
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
        if relationship_repository:
            self._create_relationship_command = CreateRelationshipCommand(
                schema_repository, relationship_repository
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

        # Phase F-10: Control Rule UseCases for validation
        self._control_rule_usecases = ControlRuleUseCases()

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

        Returns:
            OperationResult with field ID string on success, error message on failure
        """
        result = self._add_field_command.execute(
            entity_id=entity_id,
            field_id=field_id,
            field_type=field_type,
            label_key=label_key,
            help_text_key=help_text_key,
            required=required,
            default_value=default_value,
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
        """
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
            field_info = SchemaFieldInfoDTO(
                field_id=field_def.id.value,
                field_type=field_def.field_type.value,
                is_required=field_def.required,
            )
            schema_fields.append(field_info)
        return tuple(schema_fields)

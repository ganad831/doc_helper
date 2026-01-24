"""Schema Use Cases (Architecture Enforcement Phase).

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
- AddFieldConstraintCommand (add constraint to field)
- CreateRelationshipCommand (create relationship)
- ExportSchemaCommand (export schema)
- ImportSchemaCommand (import schema)
"""

from pathlib import Path
from typing import Optional

from doc_helper.application.commands.schema.add_field_command import AddFieldCommand
from doc_helper.application.commands.schema.add_field_constraint_command import (
    AddFieldConstraintCommand,
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
from doc_helper.application.dto.export_dto import ExportResult
from doc_helper.application.dto.import_dto import (
    EnforcementPolicy,
    IdenticalSchemaAction,
    ImportResult,
)
from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.dto.relationship_dto import RelationshipDTO
from doc_helper.application.dto.schema_dto import EntityDefinitionDTO
from doc_helper.application.queries.schema.get_relationships_query import (
    GetRelationshipsQuery,
)
from doc_helper.application.queries.schema.get_schema_entities_query import (
    GetSchemaEntitiesQuery,
)
from doc_helper.domain.schema.relationship_repository import IRelationshipRepository
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.validation.constraints import (
    MaxLengthConstraint,
    MaxValueConstraint,
    MinLengthConstraint,
    MinValueConstraint,
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
            value: Constraint value (required for MIN/MAX types, ignored for REQUIRED)
            severity: Severity level ("ERROR", "WARNING", "INFO"), defaults to "ERROR"

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
            else:
                return OperationResult.fail(
                    f"Unknown constraint type: {constraint_type}. "
                    "Supported types: REQUIRED, MIN_VALUE, MAX_VALUE, MIN_LENGTH, MAX_LENGTH"
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

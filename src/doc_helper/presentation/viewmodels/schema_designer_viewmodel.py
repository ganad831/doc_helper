"""Schema Designer ViewModel (Phase 2 + Phase 6B + Phase 7).

Manages presentation state for Schema Designer UI.
Loads entities, fields, validation rules, and relationships from application queries.

Phase 2 Step 1 Scope (COMPLETE):
- READ-ONLY view of schema
- Entity list display
- Field list display for selected entity
- Validation rules display for selected field
- Selection navigation between panels

Phase 2 Step 2 Scope (COMPLETE):
- CREATE new entities
- ADD fields to existing entities

Phase 6B Scope (ADR-022):
- View relationships (READ-ONLY)
- Add relationships (ADD-ONLY)
- Display relationship metadata
- Validation error display

Phase 7 Scope:
- Export schema to JSON file
- Display export warnings

NOT in scope:
- No edit/delete operations
- No import functionality
- No formulas/controls/output mappings display
- No validation rule creation

ARCHITECTURAL FIX (Clean Architecture Compliance):
- ViewModel depends ONLY on Application layer (queries, DTOs, OperationResult)
- NO domain imports (ISchemaRepository, Result, domain IDs, constraints)
- All domain access goes through GetSchemaEntitiesQuery
"""

from pathlib import Path
from typing import Callable, Optional

from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.dto.export_dto import ExportResult, ExportWarning
from doc_helper.application.dto.schema_dto import EntityDefinitionDTO, FieldDefinitionDTO
from doc_helper.application.queries.schema.get_relationships_query import (
    GetRelationshipsQuery,
    RelationshipDTO,
)
from doc_helper.application.queries.schema.get_schema_entities_query import (
    GetSchemaEntitiesQuery,
)
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


# Type alias for relationship creator function (application layer dependency)
# Signature: (relationship_id, source_entity_id, target_entity_id, relationship_type,
#             name_key, description_key, inverse_name_key) -> OperationResult
CreateRelationshipFn = Callable[
    [str, str, str, str, str, Optional[str], Optional[str]],
    OperationResult,
]


class SchemaDesignerViewModel(BaseViewModel):
    """ViewModel for Schema Designer (READ-ONLY).

    Responsibilities:
    - Load all entities from application query
    - Track selected entity and field
    - Provide entity list for UI
    - Provide field list for selected entity
    - Provide validation rules for selected field

    Usage:
        vm = SchemaDesignerViewModel(schema_query, translation_service)
        vm.load_entities()
        entities = vm.entities  # List of EntityDefinitionDTO
        vm.select_entity(entity_id)
        fields = vm.fields  # List of FieldDefinitionDTO for selected entity
        vm.select_field(field_id)
        rules = vm.validation_rules  # List of constraint descriptions

    Clean Architecture Note:
        ViewModel depends ONLY on Application layer components (queries, DTOs).
        Domain layer types (Result, ISchemaRepository, IDs, constraints) are NOT imported.
    """

    def __init__(
        self,
        schema_query: GetSchemaEntitiesQuery,
        translation_service,  # ITranslationService
        relationship_query: Optional[GetRelationshipsQuery] = None,
        create_relationship_fn: Optional[CreateRelationshipFn] = None,
    ) -> None:
        """Initialize Schema Designer ViewModel.

        Args:
            schema_query: Query for loading schema entities (application layer)
            translation_service: Service for translating labels/descriptions
            relationship_query: Query for loading relationships (application layer)
            create_relationship_fn: Function to create relationships (application layer)

        Clean Architecture Note:
            ViewModel depends only on application-layer components (queries, DTOs).
            Domain-layer repositories are NOT injected directly.
        """
        super().__init__()
        self._schema_query = schema_query
        self._translation_service = translation_service
        self._relationship_query = relationship_query
        self._create_relationship_fn = create_relationship_fn

        # State
        self._entities: tuple[EntityDefinitionDTO, ...] = ()
        self._selected_entity_id: Optional[str] = None
        self._selected_field_id: Optional[str] = None
        self._error_message: Optional[str] = None

        # Phase 6B: Relationship state
        self._relationships: tuple[RelationshipDTO, ...] = ()

    # -------------------------------------------------------------------------
    # Properties (Observable)
    # -------------------------------------------------------------------------

    @property
    def entities(self) -> tuple[EntityDefinitionDTO, ...]:
        """Get all loaded entities."""
        return self._entities

    @property
    def selected_entity_id(self) -> Optional[str]:
        """Get currently selected entity ID."""
        return self._selected_entity_id

    @property
    def selected_field_id(self) -> Optional[str]:
        """Get currently selected field ID."""
        return self._selected_field_id

    @property
    def fields(self) -> tuple[FieldDefinitionDTO, ...]:
        """Get fields for currently selected entity.

        Returns:
            Tuple of field DTOs, empty if no entity selected
        """
        if not self._selected_entity_id:
            return ()

        # Find selected entity
        for entity in self._entities:
            if entity.id == self._selected_entity_id:
                return entity.fields

        return ()

    @property
    def validation_rules(self) -> tuple[str, ...]:
        """Get validation rules for currently selected field.

        Returns:
            Tuple of human-readable constraint descriptions
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return ()

        # Delegate to application layer query (no domain access here)
        return self._schema_query.get_field_validation_rules(
            self._selected_entity_id,
            self._selected_field_id,
        )

    @property
    def error_message(self) -> Optional[str]:
        """Get error message if loading failed."""
        return self._error_message

    @property
    def relationships(self) -> tuple[RelationshipDTO, ...]:
        """Get all relationships (Phase 6B).

        Returns:
            Tuple of relationship DTOs
        """
        return self._relationships

    @property
    def entity_relationships(self) -> tuple[RelationshipDTO, ...]:
        """Get relationships involving currently selected entity (Phase 6B).

        Returns:
            Tuple of relationship DTOs where selected entity is source or target
        """
        if not self._selected_entity_id:
            return ()

        return tuple(
            rel for rel in self._relationships
            if (rel.source_entity_id == self._selected_entity_id or
                rel.target_entity_id == self._selected_entity_id)
        )

    # -------------------------------------------------------------------------
    # Commands (User Actions)
    # -------------------------------------------------------------------------

    def load_entities(self) -> bool:
        """Load all entities from application query.

        Returns:
            True if load succeeded, False otherwise
        """
        result = self._schema_query.execute()
        if result.is_failure():
            self._error_message = result.error
            self.notify_change("error_message")
            return False

        self._entities = result.value
        self._error_message = None

        self.notify_change("entities")
        self.notify_change("error_message")

        # Phase 6B: Also load relationships
        self.load_relationships()

        return True

    def load_relationships(self) -> bool:
        """Load all relationships using query (Phase 6B).

        Returns:
            True if load succeeded, False otherwise
        """
        if not self._relationship_query:
            # No query provided, relationships feature disabled
            self._relationships = ()
            return True

        result = self._relationship_query.execute()

        if result.is_failure():
            # Don't fail entirely - just set empty relationships
            self._relationships = ()
            return False

        self._relationships = result.value
        self.notify_change("relationships")
        self.notify_change("entity_relationships")
        return True

    def select_entity(self, entity_id: str) -> None:
        """Select an entity.

        Args:
            entity_id: ID of entity to select
        """
        if self._selected_entity_id != entity_id:
            self._selected_entity_id = entity_id
            self._selected_field_id = None  # Clear field selection

            self.notify_change("selected_entity_id")
            self.notify_change("selected_field_id")
            self.notify_change("fields")
            self.notify_change("validation_rules")
            # Phase 6B: Also notify about relationships
            self.notify_change("entity_relationships")

    def select_field(self, field_id: str) -> None:
        """Select a field.

        Args:
            field_id: ID of field to select
        """
        if self._selected_field_id != field_id:
            self._selected_field_id = field_id

            self.notify_change("selected_field_id")
            self.notify_change("validation_rules")

    def clear_selection(self) -> None:
        """Clear entity and field selection."""
        self._selected_entity_id = None
        self._selected_field_id = None

        self.notify_change("selected_entity_id")
        self.notify_change("selected_field_id")
        self.notify_change("fields")
        self.notify_change("validation_rules")

    # -------------------------------------------------------------------------
    # Phase 2 Step 2: Creation Commands
    # -------------------------------------------------------------------------

    def create_entity(
        self,
        entity_id: str,
        name_key: str,
        description_key: Optional[str] = None,
        is_root_entity: bool = False,
    ) -> OperationResult:
        """Create a new entity (Phase 2 Step 2).

        Args:
            entity_id: Unique entity identifier
            name_key: Translation key for entity name
            description_key: Translation key for description (optional)
            is_root_entity: Whether this is a root entity

        Returns:
            OperationResult with created entity ID or error message
        """
        from doc_helper.application.commands.schema.create_entity_command import (
            CreateEntityCommand,
        )

        # CreateEntityCommand needs repository - get it from schema_query
        command = CreateEntityCommand(self._schema_query._schema_repository)
        result = command.execute(
            entity_id=entity_id,
            name_key=name_key,
            description_key=description_key,
            is_root_entity=is_root_entity,
            parent_entity_id=None,  # Simplified for Phase 2 Step 2
        )

        if result.is_success():
            # Reload entities to show new entity
            self.load_entities()
            return OperationResult.ok(result.value.value)  # Return entity ID string
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
        """Add a field to an existing entity (Phase 2 Step 2).

        Args:
            entity_id: Entity to add field to
            field_id: Unique field identifier
            field_type: Field type (TEXT, NUMBER, etc.)
            label_key: Translation key for field label
            help_text_key: Translation key for help text (optional)
            required: Whether field is required
            default_value: Default value (optional)

        Returns:
            OperationResult with created field ID or error message
        """
        from doc_helper.application.commands.schema.add_field_command import (
            AddFieldCommand,
        )

        # AddFieldCommand needs repository - get it from schema_query
        command = AddFieldCommand(self._schema_query._schema_repository)
        result = command.execute(
            entity_id=entity_id,
            field_id=field_id,
            field_type=field_type,
            label_key=label_key,
            help_text_key=help_text_key,
            required=required,
            default_value=default_value,
        )

        if result.is_success():
            # Reload entities to show new field
            self.load_entities()
            # Re-select the entity to update field list
            if self._selected_entity_id == entity_id:
                self.select_entity(entity_id)
            return OperationResult.ok(result.value.value)  # Return field ID string
        else:
            return OperationResult.fail(result.error)

    # -------------------------------------------------------------------------
    # Phase 6B: Relationship Operations (ADD-ONLY per ADR-022)
    # -------------------------------------------------------------------------

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
        """Create a new relationship (Phase 6B - ADD-ONLY).

        Relationships are immutable once created per ADR-022.
        No update or delete operations are provided.

        Args:
            relationship_id: Unique relationship identifier
            source_entity_id: Source entity ID
            target_entity_id: Target entity ID
            relationship_type: Type (CONTAINS, REFERENCES, ASSOCIATES)
            name_key: Translation key for relationship name
            description_key: Translation key for description (optional)
            inverse_name_key: Translation key for inverse name (optional)

        Returns:
            OperationResult with created relationship ID or error message
        """
        if not self._create_relationship_fn:
            return OperationResult.fail("Relationship creation not configured")

        result = self._create_relationship_fn(
            relationship_id,
            source_entity_id,
            target_entity_id,
            relationship_type,
            name_key,
            description_key,
            inverse_name_key,
        )

        if result.success:
            # Reload relationships to show new relationship
            self.load_relationships()

        return result

    def get_entity_list_for_relationship(self) -> tuple[tuple[str, str], ...]:
        """Get list of entities for relationship source/target selection.

        Returns:
            Tuple of (entity_id, entity_name) pairs
        """
        return tuple(
            (entity.id, entity.name) for entity in self._entities
        )

    # -------------------------------------------------------------------------
    # Phase 7: Export Operations
    # -------------------------------------------------------------------------

    def export_schema(
        self,
        schema_id: str,
        file_path: Path,
        version: Optional[str] = None,
    ) -> tuple[bool, Optional[ExportResult], Optional[str]]:
        """Export schema to JSON file (Phase 7).

        Calls existing ExportSchemaCommand to export entities, fields,
        constraints, and relationships to a JSON file.

        Args:
            schema_id: Identifier for the schema (included in export)
            file_path: Path to write export file
            version: Optional semantic version string

        Returns:
            Tuple of (success, export_result, error_message):
            - success: True if export succeeded
            - export_result: ExportResult with data and warnings (on success)
            - error_message: Error message (on failure)
        """
        from doc_helper.application.commands.schema.export_schema_command import (
            ExportSchemaCommand,
        )

        # Get relationship repository if available
        relationship_repository = None
        if self._relationship_query:
            relationship_repository = self._relationship_query._relationship_repository

        # Create and execute command
        command = ExportSchemaCommand(
            self._schema_query._schema_repository,
            relationship_repository,
        )

        result = command.execute(
            schema_id=schema_id,
            file_path=file_path,
            version=version,
        )

        if result.is_success():
            export_result = result.value
            return (True, export_result, None)
        else:
            return (False, None, result.error)

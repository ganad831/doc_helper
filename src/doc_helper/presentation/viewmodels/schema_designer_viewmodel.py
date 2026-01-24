"""Schema Designer ViewModel (Phase 2 + Phase 6B + Phase 7).

Manages presentation state for Schema Designer UI.
Loads entities, fields, validation rules, and relationships from application use-cases.

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

Phase SD-1 Scope:
- Import schema from JSON file
- Handle enforcement policy options
- Handle identical schema actions
- Reload entities after successful import

NOT in scope:
- No edit/delete operations
- No formulas/controls/output mappings display
- No validation rule creation

ARCHITECTURE ENFORCEMENT (Rule 0 Compliance):
- ViewModel depends ONLY on SchemaUseCases (Application layer use-case)
- NO command imports
- NO query imports
- NO repository access (direct or reach-through)
- NO domain ID unwrapping
- All orchestration delegated to SchemaUseCases
"""

from pathlib import Path
from typing import Optional

from doc_helper.application.dto.export_dto import ExportResult
from doc_helper.application.dto.import_dto import (
    EnforcementPolicy,
    IdenticalSchemaAction,
    ImportResult,
)
from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.dto.relationship_dto import RelationshipDTO
from doc_helper.application.dto.schema_dto import EntityDefinitionDTO, FieldDefinitionDTO
from doc_helper.application.usecases.schema_usecases import SchemaUseCases
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


class SchemaDesignerViewModel(BaseViewModel):
    """ViewModel for Schema Designer.

    Responsibilities:
    - Load all entities via use-case
    - Track selected entity and field
    - Provide entity list for UI
    - Provide field list for selected entity
    - Provide validation rules for selected field

    Usage:
        vm = SchemaDesignerViewModel(schema_usecases)
        vm.load_entities()
        entities = vm.entities  # List of EntityDefinitionDTO
        vm.select_entity(entity_id)
        fields = vm.fields  # List of FieldDefinitionDTO for selected entity
        vm.select_field(field_id)
        rules = vm.validation_rules  # List of constraint descriptions

    Architecture Compliance (Rule 0):
        ViewModel depends ONLY on SchemaUseCases (Application layer).
        NO commands, queries, or repositories are imported or accessed.
    """

    def __init__(
        self,
        schema_usecases: SchemaUseCases,
    ) -> None:
        """Initialize Schema Designer ViewModel.

        Args:
            schema_usecases: Use-case class for all schema operations

        Architecture Compliance (Rule 0):
            ViewModel receives ONLY use-case class via DI.
            NO commands, queries, or repositories are injected.
        """
        super().__init__()
        self._schema_usecases = schema_usecases

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

        # Delegate to use-case (no domain access here)
        return self._schema_usecases.get_field_validation_rules(
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
        """Load all entities from use-case.

        Returns:
            True if load succeeded, False otherwise
        """
        self._entities = self._schema_usecases.get_all_entities()

        if not self._entities:
            # Could be empty or error - use-case returns empty tuple on error
            self._error_message = None  # Don't set error for empty schema
        else:
            self._error_message = None

        self.notify_change("entities")
        self.notify_change("error_message")

        # Phase 6B: Also load relationships
        self.load_relationships()

        return True

    def load_relationships(self) -> bool:
        """Load all relationships from use-case (Phase 6B).

        Returns:
            True if load succeeded, False otherwise
        """
        self._relationships = self._schema_usecases.get_all_relationships()
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
        result = self._schema_usecases.create_entity(
            entity_id=entity_id,
            name_key=name_key,
            description_key=description_key,
            is_root_entity=is_root_entity,
        )

        if result.success:
            # Reload entities to show new entity
            self.load_entities()

        return result

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
        result = self._schema_usecases.add_field(
            entity_id=entity_id,
            field_id=field_id,
            field_type=field_type,
            label_key=label_key,
            help_text_key=help_text_key,
            required=required,
            default_value=default_value,
        )

        if result.success:
            # Reload entities to show new field
            self.load_entities()
            # Re-select the entity to update field list
            if self._selected_entity_id == entity_id:
                self.select_entity(entity_id)

        return result

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
        result = self._schema_usecases.create_relationship(
            relationship_id=relationship_id,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relationship_type=relationship_type,
            name_key=name_key,
            description_key=description_key,
            inverse_name_key=inverse_name_key,
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
        return self._schema_usecases.get_entity_list_for_selection()

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

        Delegates to SchemaUseCases which handles command execution.

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
        return self._schema_usecases.export_schema(
            schema_id=schema_id,
            file_path=file_path,
            version=version,
        )

    # -------------------------------------------------------------------------
    # Phase SD-1: Import Operations
    # -------------------------------------------------------------------------

    def import_schema(
        self,
        file_path: Path,
        enforcement_policy: EnforcementPolicy = EnforcementPolicy.STRICT,
        identical_action: IdenticalSchemaAction = IdenticalSchemaAction.SKIP,
        force: bool = False,
    ) -> ImportResult:
        """Import schema from JSON file (Phase SD-1).

        Delegates to SchemaUseCases which handles command execution.

        Args:
            file_path: Path to JSON import file
            enforcement_policy: How to handle compatibility issues
            identical_action: What to do when schema is identical
            force: Force import even if incompatible

        Returns:
            ImportResult with success status, counts, warnings, and errors
        """
        result = self._schema_usecases.import_schema(
            file_path=file_path,
            enforcement_policy=enforcement_policy,
            identical_action=identical_action,
            force=force,
        )

        if result.success and not result.was_skipped:
            # Reload entities to show imported schema
            self.load_entities()

        return result

    def dispose(self) -> None:
        """Clean up resources."""
        super().dispose()
        self._entities = ()
        self._relationships = ()
        self._selected_entity_id = None
        self._selected_field_id = None

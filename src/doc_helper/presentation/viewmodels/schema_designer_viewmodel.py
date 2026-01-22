"""Schema Designer ViewModel (Phase 2, Step 2: CREATE operations).

Manages presentation state for Schema Designer UI.
Loads entities, fields, and validation rules from schema repository.

Phase 2 Step 1 Scope (COMPLETE):
- READ-ONLY view of schema
- Entity list display
- Field list display for selected entity
- Validation rules display for selected field
- Selection navigation between panels

Phase 2 Step 2 Scope (CURRENT):
- CREATE new entities
- ADD fields to existing entities

NOT in Step 2:
- No edit/delete operations
- No export functionality
- No relationships UI
- No formulas/controls/output mappings display
- No validation rule creation
"""

from typing import Optional

from doc_helper.application.dto.schema_dto import EntityDefinitionDTO, FieldDefinitionDTO
from doc_helper.domain.common.result import Result
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.validation.constraints import (
    FieldConstraint,
    RequiredConstraint,
    MinLengthConstraint,
    MaxLengthConstraint,
    MinValueConstraint,
    MaxValueConstraint,
    PatternConstraint,
    AllowedValuesConstraint,
    FileExtensionConstraint,
    MaxFileSizeConstraint,
)
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


class SchemaDesignerViewModel(BaseViewModel):
    """ViewModel for Schema Designer (READ-ONLY).

    Responsibilities:
    - Load all entities from schema repository
    - Track selected entity and field
    - Provide entity list for UI
    - Provide field list for selected entity
    - Provide validation rules for selected field

    Usage:
        vm = SchemaDesignerViewModel(schema_repository, translation_service)
        vm.load_entities()
        entities = vm.entities  # List of EntityDefinitionDTO
        vm.select_entity(entity_id)
        fields = vm.fields  # List of FieldDefinitionDTO for selected entity
        vm.select_field(field_id)
        rules = vm.validation_rules  # List of constraint descriptions
    """

    def __init__(
        self,
        schema_repository: ISchemaRepository,
        translation_service,  # ITranslationService
    ) -> None:
        """Initialize Schema Designer ViewModel.

        Args:
            schema_repository: Repository for loading schema definitions
            translation_service: Service for translating labels/descriptions
        """
        super().__init__()
        self._schema_repository = schema_repository
        self._translation_service = translation_service

        # State
        self._entities: tuple[EntityDefinitionDTO, ...] = ()
        self._selected_entity_id: Optional[str] = None
        self._selected_field_id: Optional[str] = None
        self._error_message: Optional[str] = None

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

        # Find selected field
        for entity in self._entities:
            if entity.id == self._selected_entity_id:
                for field_dto in entity.fields:
                    if field_dto.id == self._selected_field_id:
                        # Get field definition from repository to access constraints
                        entity_result = self._schema_repository.get_by_id(
                            EntityDefinitionId(self._selected_entity_id)
                        )
                        if entity_result.is_failure():
                            return ()

                        entity_def = entity_result.value
                        field_def = entity_def.get_field(
                            FieldDefinitionId(self._selected_field_id)
                        )
                        if not field_def:
                            return ()

                        # Convert constraints to human-readable descriptions
                        return tuple(
                            self._format_constraint(c) for c in field_def.constraints
                        )

        return ()

    @property
    def error_message(self) -> Optional[str]:
        """Get error message if loading failed."""
        return self._error_message

    # -------------------------------------------------------------------------
    # Commands (User Actions)
    # -------------------------------------------------------------------------

    def load_entities(self) -> bool:
        """Load all entities from schema repository.

        Returns:
            True if load succeeded, False otherwise
        """
        result = self._schema_repository.get_all()
        if result.is_failure():
            self._error_message = result.error
            self.notify_change("error_message")
            return False

        # Convert domain entities to DTOs
        entity_definitions = result.value
        self._entities = tuple(
            self._entity_to_dto(entity) for entity in entity_definitions
        )
        self._error_message = None

        self.notify_change("entities")
        self.notify_change("error_message")
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
    # Private Helpers
    # -------------------------------------------------------------------------

    def _entity_to_dto(self, entity_definition) -> EntityDefinitionDTO:
        """Convert EntityDefinition to DTO.

        Args:
            entity_definition: Domain entity definition

        Returns:
            EntityDefinitionDTO for UI consumption
        """
        # Translate entity name
        entity_name = self._translation_service.get(entity_definition.name_key)

        # Translate description if present
        entity_description = None
        if entity_definition.description_key:
            entity_description = self._translation_service.get(
                entity_definition.description_key
            )

        # Convert fields to DTOs
        field_dtos = tuple(
            self._field_to_dto(field) for field in entity_definition.get_all_fields()
        )

        return EntityDefinitionDTO(
            id=str(entity_definition.id.value),
            name=entity_name,
            description=entity_description,
            field_count=entity_definition.field_count,
            is_root_entity=entity_definition.is_root_entity,
            parent_entity_id=(
                str(entity_definition.parent_entity_id.value)
                if entity_definition.parent_entity_id
                else None
            ),
            fields=field_dtos,
        )

    def _field_to_dto(self, field_definition) -> FieldDefinitionDTO:
        """Convert FieldDefinition to DTO.

        Args:
            field_definition: Domain field definition

        Returns:
            FieldDefinitionDTO for UI consumption
        """
        from doc_helper.application.dto.schema_dto import FieldOptionDTO

        # Translate field label
        field_label = self._translation_service.get(field_definition.label_key)

        # Translate help text if present
        help_text = None
        if field_definition.help_text_key:
            help_text = self._translation_service.get(field_definition.help_text_key)

        # Convert options to DTOs (for choice fields)
        option_dtos = ()
        if field_definition.options:
            option_dtos = tuple(
                FieldOptionDTO(
                    value=opt[0],
                    label=self._translation_service.get(opt[1]),
                )
                for opt in field_definition.options
            )

        return FieldDefinitionDTO(
            id=str(field_definition.id.value),
            field_type=field_definition.field_type.value,
            label=field_label,
            help_text=help_text,
            required=field_definition.required,
            default_value=(
                str(field_definition.default_value)
                if field_definition.default_value is not None
                else None
            ),
            options=option_dtos,
            formula=field_definition.formula,
            is_calculated=field_definition.is_calculated,
            is_choice_field=field_definition.is_choice_field,
            is_collection_field=field_definition.is_collection_field,
            lookup_entity_id=field_definition.lookup_entity_id,
            child_entity_id=field_definition.child_entity_id,
        )

    def _format_constraint(self, constraint: FieldConstraint) -> str:
        """Format a constraint as human-readable text.

        Args:
            constraint: Field constraint to format

        Returns:
            Human-readable constraint description
        """
        if isinstance(constraint, RequiredConstraint):
            return "Required field"

        elif isinstance(constraint, MinLengthConstraint):
            return f"Minimum length: {constraint.min_length} characters"

        elif isinstance(constraint, MaxLengthConstraint):
            return f"Maximum length: {constraint.max_length} characters"

        elif isinstance(constraint, MinValueConstraint):
            return f"Minimum value: {constraint.min_value}"

        elif isinstance(constraint, MaxValueConstraint):
            return f"Maximum value: {constraint.max_value}"

        elif isinstance(constraint, PatternConstraint):
            desc = f"Pattern: {constraint.pattern}"
            if constraint.description:
                desc += f" ({constraint.description})"
            return desc

        elif isinstance(constraint, AllowedValuesConstraint):
            values = ", ".join(str(v) for v in constraint.allowed_values)
            return f"Allowed values: {values}"

        elif isinstance(constraint, FileExtensionConstraint):
            exts = ", ".join(constraint.allowed_extensions)
            return f"Allowed extensions: {exts}"

        elif isinstance(constraint, MaxFileSizeConstraint):
            size_mb = constraint.max_size_bytes / (1024 * 1024)
            return f"Maximum file size: {size_mb:.2f} MB"

        else:
            return f"Unknown constraint: {type(constraint).__name__}"

    # -------------------------------------------------------------------------
    # Phase 2 Step 2: Creation Commands
    # -------------------------------------------------------------------------

    def create_entity(
        self,
        entity_id: str,
        name_key: str,
        description_key: Optional[str] = None,
        is_root_entity: bool = False,
    ) -> Result[str, str]:
        """Create a new entity (Phase 2 Step 2).

        Args:
            entity_id: Unique entity identifier
            name_key: Translation key for entity name
            description_key: Translation key for description (optional)
            is_root_entity: Whether this is a root entity

        Returns:
            Result with created entity ID or error message
        """
        from doc_helper.application.commands.schema.create_entity_command import (
            CreateEntityCommand,
        )

        command = CreateEntityCommand(self._schema_repository)
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
            return Success(result.value.value)  # Return entity ID string
        else:
            return Failure(result.error)

    def add_field(
        self,
        entity_id: str,
        field_id: str,
        field_type: str,
        label_key: str,
        help_text_key: Optional[str] = None,
        required: bool = False,
        default_value: Optional[str] = None,
    ) -> Result[str, str]:
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
            Result with created field ID or error message
        """
        from doc_helper.application.commands.schema.add_field_command import (
            AddFieldCommand,
        )

        command = AddFieldCommand(self._schema_repository)
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
            return Success(result.value.value)  # Return field ID string
        else:
            return Failure(result.error)

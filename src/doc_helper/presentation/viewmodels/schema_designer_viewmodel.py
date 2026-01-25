"""Schema Designer ViewModel (Phase 2 + Phase 6B + Phase 7 + Phase F-1 + Phase F-9 + Phase F-13 + Phase F-14).

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

Phase SD-2 Scope:
- Add validation constraints to fields
- Support: Required, MinValue, MaxValue, MinLength, MaxLength
- Refresh validation rules after adding

Phase SD-3 Scope:
- Update entity metadata
- Delete entity (with dependency check)

Phase SD-4 Scope:
- Update field metadata
- Delete field (with dependency check)

Phase F-1 Scope (Formula Editor - Read-Only, Design-Time):
- Formula Editor panel for CALCULATED fields
- Live validation of formula syntax
- Field reference validation against schema
- Type inference display
- NO formula execution
- NO schema mutation from formula editor

Phase F-9 Scope (Control Rules Preview - UI-Only):
- Toggle preview mode ON/OFF
- Set temporary field values for preview
- Define control rules (VISIBILITY, ENABLED, REQUIRED)
- Evaluate rules via use-cases
- Apply rule effects to UI only (no persistence)
- Display blocked rules with reasons
- NO schema mutation
- NO persistence

Phase F-13 Scope (Output Mapping Formula UI - Design-Time Only):
- View persisted output mappings for selected field
- Add new output mapping (target type + formula)
- Update existing output mapping formula
- Delete output mapping by target type
- Design-time only, NO runtime execution
- NO preview or formula evaluation

Phase F-14 Scope (Field Option Management - Design-Time Only):
- Add options to choice fields (DROPDOWN, RADIO)
- Update option label keys
- Delete options from choice fields
- Reorder options in choice fields
- List all options for a field
- Design-time only, NO runtime execution

ARCHITECTURE ENFORCEMENT (Rule 0 Compliance):
- ViewModel depends ONLY on SchemaUseCases (Application layer use-case)
- NO command imports
- NO query imports
- NO repository access (direct or reach-through)
- NO domain ID unwrapping
- All orchestration delegated to SchemaUseCases
"""

from pathlib import Path
from typing import Any, Optional

from doc_helper.application.dto.control_rule_dto import ControlRuleStatus, ControlRuleType
from doc_helper.application.dto.control_rule_preview_dto import (
    ControlRulePreviewInputDTO,
    ControlRulePreviewResultDTO,
    FieldPreviewStateDTO,
    PreviewModeStateDTO,
)
from doc_helper.application.dto.export_dto import (
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
from doc_helper.application.dto.schema_dto import EntityDefinitionDTO, FieldDefinitionDTO
from doc_helper.application.usecases.control_rule_usecases import ControlRuleUseCases
from doc_helper.application.usecases.formula_usecases import FormulaUseCases
from doc_helper.application.usecases.schema_usecases import SchemaUseCases
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel
from doc_helper.presentation.viewmodels.formula_editor_viewmodel import (
    FormulaEditorViewModel,
)


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
        formula_usecases: Optional[FormulaUseCases] = None,
        control_rule_usecases: Optional[ControlRuleUseCases] = None,
    ) -> None:
        """Initialize Schema Designer ViewModel.

        Args:
            schema_usecases: Use-case class for all schema operations
            formula_usecases: Use-case class for formula validation (Phase F-1)
                             Optional for backward compatibility
            control_rule_usecases: Use-case class for control rule preview (Phase F-9)
                                   Optional for backward compatibility

        Architecture Compliance (Rule 0):
            ViewModel receives ONLY use-case classes via DI.
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

        # Phase F-1: Formula Editor ViewModel
        self._formula_usecases = formula_usecases
        self._formula_editor_viewmodel: Optional[FormulaEditorViewModel] = None
        if formula_usecases is not None:
            self._formula_editor_viewmodel = FormulaEditorViewModel(formula_usecases)

        # Phase F-9: Control Rules Preview state (UI-only, in-memory)
        self._control_rule_usecases = control_rule_usecases
        self._preview_mode_enabled: bool = False
        self._preview_field_values: dict[str, Any] = {}
        self._preview_control_rules: list[ControlRulePreviewInputDTO] = []
        self._preview_results: list[ControlRulePreviewResultDTO] = []
        self._field_preview_states: dict[str, FieldPreviewStateDTO] = {}

        # Phase F-11: Persisted control rules for selected field (design-time only)
        self._control_rules: tuple[ControlRuleExportDTO, ...] = ()

        # Phase F-13: Persisted output mappings for selected field (design-time only)
        self._output_mappings: tuple[OutputMappingExportDTO, ...] = ()

        # Phase F-14: Field options for selected field (design-time only)
        self._field_options: tuple[FieldOptionExportDTO, ...] = ()

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

    @property
    def formula_editor_viewmodel(self) -> Optional[FormulaEditorViewModel]:
        """Get the Formula Editor ViewModel (Phase F-1).

        Returns:
            FormulaEditorViewModel instance, or None if formula_usecases not provided
        """
        return self._formula_editor_viewmodel

    @property
    def selected_field_type(self) -> Optional[str]:
        """Get the field type of the currently selected field.

        Returns:
            Field type string (e.g., 'TEXT', 'CALCULATED'), or None if no field selected
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return None

        for entity in self._entities:
            if entity.id == self._selected_entity_id:
                for field in entity.fields:
                    if field.id == self._selected_field_id:
                        return field.field_type
        return None

    @property
    def selected_field_formula(self) -> Optional[str]:
        """Get the formula of the currently selected field.

        Returns:
            Formula string, or None if no field selected or field has no formula
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return None

        for entity in self._entities:
            if entity.id == self._selected_entity_id:
                for field in entity.fields:
                    if field.id == self._selected_field_id:
                        return field.formula
        return None

    # -------------------------------------------------------------------------
    # Phase F-9: Preview Mode Properties
    # -------------------------------------------------------------------------

    @property
    def is_preview_mode_enabled(self) -> bool:
        """Check if preview mode is enabled (Phase F-9).

        Returns:
            True if preview mode is active
        """
        return self._preview_mode_enabled

    @property
    def preview_field_values(self) -> dict[str, Any]:
        """Get current preview field values (Phase F-9).

        Returns:
            Dict mapping field_id -> preview value (in-memory only)
        """
        return self._preview_field_values.copy()

    @property
    def preview_control_rules(self) -> tuple[ControlRulePreviewInputDTO, ...]:
        """Get current preview control rules (Phase F-9).

        Returns:
            Tuple of control rule input DTOs
        """
        return tuple(self._preview_control_rules)

    @property
    def preview_results(self) -> tuple[ControlRulePreviewResultDTO, ...]:
        """Get preview rule evaluation results (Phase F-9).

        Returns:
            Tuple of preview result DTOs with validation/execution status
        """
        return tuple(self._preview_results)

    @property
    def preview_mode_state(self) -> PreviewModeStateDTO:
        """Get complete preview mode state as DTO (Phase F-9).

        Returns:
            PreviewModeStateDTO with all preview state
        """
        return PreviewModeStateDTO(
            is_enabled=self._preview_mode_enabled,
            entity_id=self._selected_entity_id,
            field_values=tuple(self._preview_field_values.items()),
            control_rules=tuple(self._preview_control_rules),
            field_states=tuple(self._field_preview_states.values()),
        )

    def get_field_preview_state(self, field_id: str) -> FieldPreviewStateDTO:
        """Get preview state for a specific field (Phase F-9).

        Args:
            field_id: ID of field to get state for

        Returns:
            FieldPreviewStateDTO with visibility, enabled, required states
        """
        if field_id in self._field_preview_states:
            return self._field_preview_states[field_id]

        # Return default state if not set
        return FieldPreviewStateDTO(field_id=field_id)

    # -------------------------------------------------------------------------
    # Phase F-11: Persisted Control Rules Properties
    # -------------------------------------------------------------------------

    @property
    def control_rules(self) -> tuple[ControlRuleExportDTO, ...]:
        """Get persisted control rules for currently selected field (Phase F-11).

        Returns:
            Tuple of ControlRuleExportDTO for selected field, empty if no field selected

        Phase F-11 Compliance:
            - Design-time only, no runtime enforcement
            - Loaded from schema via SchemaUseCases
            - Updated via add/update/delete methods
        """
        return self._control_rules

    @property
    def has_control_rules(self) -> bool:
        """Check if selected field has persisted control rules (Phase F-11).

        Returns:
            True if selected field has control rules, False otherwise
        """
        return len(self._control_rules) > 0

    # -------------------------------------------------------------------------
    # Phase F-13: Persisted Output Mappings Properties
    # -------------------------------------------------------------------------

    @property
    def output_mappings(self) -> tuple[OutputMappingExportDTO, ...]:
        """Get persisted output mappings for currently selected field (Phase F-13).

        Returns:
            Tuple of OutputMappingExportDTO for selected field, empty if no field selected

        Phase F-13 Compliance:
            - Design-time only, no runtime execution
            - Loaded from schema via SchemaUseCases
            - Updated via add/update/delete methods
        """
        return self._output_mappings

    @property
    def has_output_mappings(self) -> bool:
        """Check if selected field has persisted output mappings (Phase F-13).

        Returns:
            True if selected field has output mappings, False otherwise
        """
        return len(self._output_mappings) > 0

    # -------------------------------------------------------------------------
    # Phase F-14: Field Options Properties
    # -------------------------------------------------------------------------

    @property
    def field_options(self) -> tuple[FieldOptionExportDTO, ...]:
        """Get field options for currently selected field (Phase F-14).

        Returns:
            Tuple of FieldOptionExportDTO for selected field, empty if no field selected
            or field is not a choice type (DROPDOWN, RADIO).

        Phase F-14 Compliance:
            - Design-time only, returns label_key not translated label
            - Loaded from schema via SchemaUseCases
            - Updated via add/update/delete/reorder methods
        """
        return self._field_options

    @property
    def has_field_options(self) -> bool:
        """Check if selected field has options (Phase F-14).

        Returns:
            True if selected field has options, False otherwise
        """
        return len(self._field_options) > 0

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

            # Phase F-1: Update formula editor context
            self._update_formula_editor_context()

            # Phase F-11: Load control rules for selected field
            self.load_control_rules()

            # Phase F-13: Load output mappings for selected field
            self.load_output_mappings()

            # Phase F-14: Load field options for selected field
            self.load_field_options()

    def clear_selection(self) -> None:
        """Clear entity and field selection."""
        self._selected_entity_id = None
        self._selected_field_id = None

        self.notify_change("selected_entity_id")
        self.notify_change("selected_field_id")
        self.notify_change("fields")
        self.notify_change("validation_rules")

        # Phase F-1: Clear formula editor
        if self._formula_editor_viewmodel:
            self._formula_editor_viewmodel.clear_formula()

    def _update_formula_editor_context(self) -> None:
        """Update formula editor with current schema context (Phase F-1).

        Called when field selection changes. Sets up the formula editor
        with available fields from the current entity for validation.
        """
        if not self._formula_editor_viewmodel:
            return

        # Build schema field info from current entity's fields
        schema_fields: list[SchemaFieldInfoDTO] = []

        if self._selected_entity_id:
            for entity in self._entities:
                if entity.id == self._selected_entity_id:
                    for field in entity.fields:
                        # Don't include the currently selected field (can't reference itself)
                        if field.id != self._selected_field_id:
                            schema_fields.append(
                                SchemaFieldInfoDTO(
                                    field_id=field.id,
                                    field_type=field.field_type,
                                    label=field.label,
                                )
                            )
                    break

        # Set schema context on formula editor viewmodel
        self._formula_editor_viewmodel.set_schema_context(tuple(schema_fields))

        # If selected field is CALCULATED and has a formula, load it
        if self._selected_field_id:
            formula = self.selected_field_formula
            if formula:
                self._formula_editor_viewmodel.set_formula(formula)
            else:
                self._formula_editor_viewmodel.clear_formula()

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

    def update_entity(
        self,
        entity_id: str,
        name_key: Optional[str] = None,
        description_key: Optional[str] = None,
        is_root_entity: Optional[bool] = None,
    ) -> OperationResult:
        """Update entity metadata (Phase SD-3).

        Args:
            entity_id: Entity ID to update (immutable)
            name_key: New name translation key (optional)
            description_key: New description translation key (optional)
            is_root_entity: New root entity status (optional)

        Returns:
            OperationResult with entity ID on success, error message on failure
        """
        result = self._schema_usecases.update_entity(
            entity_id=entity_id,
            name_key=name_key,
            description_key=description_key,
            is_root_entity=is_root_entity,
        )

        if result.success:
            # Reload entities to show updated entity
            self.load_entities()

        return result

    def delete_entity(self, entity_id: str) -> OperationResult:
        """Delete an entity (Phase SD-3).

        Args:
            entity_id: Entity ID to delete

        Returns:
            OperationResult with None on success, error message on failure.
            Failure includes dependency details if entity is referenced.
        """
        result = self._schema_usecases.delete_entity(entity_id=entity_id)

        if result.success:
            # Clear selection if deleted entity was selected
            if self._selected_entity_id == entity_id:
                self.clear_selection()
            # Reload entities to reflect deletion
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
        """Update field metadata (Phase SD-4).

        Args:
            entity_id: Parent entity ID
            field_id: Field ID to update (immutable)
            label_key: New label translation key (optional)
            help_text_key: New help text translation key (optional)
            required: New required flag (optional)
            default_value: New default value (optional)
            formula: New formula expression (CALCULATED fields only)
            lookup_entity_id: New lookup entity ID (LOOKUP fields only)
            lookup_display_field: New lookup display field (LOOKUP fields only)
            child_entity_id: New child entity ID (TABLE fields only)

        Returns:
            OperationResult with field ID on success, error message on failure.
            Note: Field type is immutable and cannot be changed.
        """
        result = self._schema_usecases.update_field(
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

        if result.success:
            # Reload entities to show updated field
            self.load_entities()
            # Re-select the entity to update field list
            if self._selected_entity_id == entity_id:
                self.select_entity(entity_id)

        return result

    def delete_field(self, entity_id: str, field_id: str) -> OperationResult:
        """Delete a field from an entity (Phase SD-4).

        Args:
            entity_id: Parent entity ID
            field_id: Field ID to delete

        Returns:
            OperationResult with None on success, error message on failure.
            Failure includes dependency details if field is referenced.
        """
        result = self._schema_usecases.delete_field(
            entity_id=entity_id,
            field_id=field_id,
        )

        if result.success:
            # Clear field selection if deleted field was selected
            if self._selected_field_id == field_id:
                self._selected_field_id = None
                self.notify_change("selected_field_id")
                self.notify_change("validation_rules")
            # Reload entities to reflect deletion
            self.load_entities()

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

    # -------------------------------------------------------------------------
    # Phase SD-2: Constraint Operations
    # Phase SD-6: Extended with advanced constraint parameters
    # -------------------------------------------------------------------------

    def add_constraint(
        self,
        entity_id: str,
        field_id: str,
        constraint_type: str,
        value: Optional[float] = None,
        severity: str = "ERROR",
        # Phase SD-6: Advanced constraint parameters
        pattern: Optional[str] = None,
        pattern_description: Optional[str] = None,
        allowed_values: Optional[tuple] = None,
        allowed_extensions: Optional[tuple] = None,
        max_size_bytes: Optional[int] = None,
    ) -> OperationResult:
        """Add a validation constraint to a field (Phase SD-2, SD-6).

        Delegates to SchemaUseCases which handles domain object construction
        and command execution.

        Args:
            entity_id: Entity containing the field
            field_id: Field to add constraint to
            constraint_type: Type of constraint (REQUIRED, MIN_VALUE, etc.)
            value: Constraint value (required for MIN/MAX types)
            severity: Severity level (ERROR, WARNING, INFO)

            Phase SD-6 additional parameters:
            pattern: Regex pattern (for PATTERN constraint)
            pattern_description: Human-readable pattern description
            allowed_values: Tuple of allowed values (for ALLOWED_VALUES)
            allowed_extensions: Tuple of file extensions (for FILE_EXTENSION)
            max_size_bytes: Maximum file size in bytes (for MAX_FILE_SIZE)

        Returns:
            OperationResult with field ID on success, error message on failure
        """
        result = self._schema_usecases.add_constraint(
            entity_id=entity_id,
            field_id=field_id,
            constraint_type=constraint_type,
            value=value,
            severity=severity,
            # Phase SD-6: Pass advanced constraint parameters
            pattern=pattern,
            pattern_description=pattern_description,
            allowed_values=allowed_values,
            allowed_extensions=allowed_extensions,
            max_size_bytes=max_size_bytes,
        )

        if result.success:
            # Reload entities to refresh constraint data
            self.load_entities()
            # Notify about validation rules change
            self.notify_change("validation_rules")

        return result

    # -------------------------------------------------------------------------
    # Phase F-9: Preview Mode Commands
    # -------------------------------------------------------------------------

    def enable_preview_mode(self) -> None:
        """Enable preview mode (Phase F-9)."""
        if not self._preview_mode_enabled:
            self._preview_mode_enabled = True
            self.notify_change("is_preview_mode_enabled")
            self.notify_change("preview_mode_state")

    def disable_preview_mode(self) -> None:
        """Disable preview mode and clear state (Phase F-9)."""
        if self._preview_mode_enabled:
            self._preview_mode_enabled = False
            self._clear_preview_state()
            self.notify_change("is_preview_mode_enabled")
            self.notify_change("preview_mode_state")

    def set_preview_field_value(self, field_id: str, value: Any) -> None:
        """Set a preview field value (Phase F-9).

        Args:
            field_id: ID of field to set value for
            value: Preview value (in-memory only)

        Phase F-9 Compliance:
            - In-memory only, no persistence
            - Used for formula execution during preview
        """
        self._preview_field_values[field_id] = value
        self.notify_change("preview_field_values")
        self.notify_change("preview_mode_state")

        # Re-evaluate rules with new values
        if self._preview_mode_enabled:
            self._evaluate_preview_rules()

    def clear_preview_field_value(self, field_id: str) -> None:
        """Clear a preview field value (Phase F-9).

        Args:
            field_id: ID of field to clear value for
        """
        if field_id in self._preview_field_values:
            del self._preview_field_values[field_id]
            self.notify_change("preview_field_values")
            self.notify_change("preview_mode_state")

            # Re-evaluate rules
            if self._preview_mode_enabled:
                self._evaluate_preview_rules()

    def add_preview_control_rule(
        self,
        rule_type: ControlRuleType,
        target_field_id: str,
        formula_text: str,
    ) -> int:
        """Add a preview control rule (Phase F-9).

        Args:
            rule_type: Type of control rule (VISIBILITY, ENABLED, REQUIRED)
            target_field_id: ID of field this rule applies to
            formula_text: Boolean formula expression

        Returns:
            Index of added rule

        Phase F-9 Compliance:
            - In-memory only, no persistence
            - Rule is validated and evaluated immediately
        """
        rule_input = ControlRulePreviewInputDTO(
            rule_type=rule_type,
            target_field_id=target_field_id,
            formula_text=formula_text,
        )
        self._preview_control_rules.append(rule_input)
        index = len(self._preview_control_rules) - 1

        self.notify_change("preview_control_rules")
        self.notify_change("preview_mode_state")

        # Evaluate the new rule
        if self._preview_mode_enabled:
            self._evaluate_preview_rules()

        return index

    def remove_preview_control_rule(self, index: int) -> bool:
        """Remove a preview control rule by index (Phase F-9).

        Args:
            index: Index of rule to remove

        Returns:
            True if rule was removed, False if index invalid
        """
        if 0 <= index < len(self._preview_control_rules):
            del self._preview_control_rules[index]
            # Also remove corresponding result if it exists
            if index < len(self._preview_results):
                del self._preview_results[index]

            self.notify_change("preview_control_rules")
            self.notify_change("preview_results")
            self.notify_change("preview_mode_state")

            # Re-compute field states
            if self._preview_mode_enabled:
                self._compute_field_preview_states()

            return True
        return False

    def update_preview_control_rule(
        self,
        index: int,
        rule_type: Optional[ControlRuleType] = None,
        target_field_id: Optional[str] = None,
        formula_text: Optional[str] = None,
    ) -> bool:
        """Update a preview control rule (Phase F-9).

        Args:
            index: Index of rule to update
            rule_type: New rule type (optional)
            target_field_id: New target field ID (optional)
            formula_text: New formula text (optional)

        Returns:
            True if rule was updated, False if index invalid
        """
        if 0 <= index < len(self._preview_control_rules):
            old_rule = self._preview_control_rules[index]
            new_rule = ControlRulePreviewInputDTO(
                rule_type=rule_type if rule_type is not None else old_rule.rule_type,
                target_field_id=(
                    target_field_id
                    if target_field_id is not None
                    else old_rule.target_field_id
                ),
                formula_text=(
                    formula_text if formula_text is not None else old_rule.formula_text
                ),
            )
            self._preview_control_rules[index] = new_rule

            self.notify_change("preview_control_rules")
            self.notify_change("preview_mode_state")

            # Re-evaluate rules
            if self._preview_mode_enabled:
                self._evaluate_preview_rules()

            return True
        return False

    def evaluate_preview_rules(self) -> tuple[ControlRulePreviewResultDTO, ...]:
        """Manually trigger evaluation of all preview rules (Phase F-9).

        Returns:
            Tuple of preview result DTOs

        Phase F-9 Compliance:
            - Uses ControlRuleUseCases.preview_control_rule()
            - No persistence
            - Deterministic execution
        """
        self._evaluate_preview_rules()
        return tuple(self._preview_results)

    def _evaluate_preview_rules(self) -> None:
        """Internal: Evaluate all preview rules via use-cases.

        Updates _preview_results and _field_preview_states.
        """
        if self._control_rule_usecases is None:
            # No use-cases available, clear results
            self._preview_results = []
            self._field_preview_states = {}
            return

        # Build schema fields from current entity
        schema_fields = self._build_schema_fields_for_preview()

        # Evaluate each rule
        self._preview_results = []
        for rule_input in self._preview_control_rules:
            result = self._control_rule_usecases.preview_control_rule(
                rule_input=rule_input,
                schema_fields=schema_fields,
                field_values=self._preview_field_values,
            )
            self._preview_results.append(result)

        # Compute field preview states from results
        self._compute_field_preview_states()

        self.notify_change("preview_results")

    def _build_schema_fields_for_preview(self) -> tuple[SchemaFieldInfoDTO, ...]:
        """Build schema field info for preview validation.

        Returns:
            Tuple of SchemaFieldInfoDTO for current entity's fields
        """
        if not self._selected_entity_id:
            return ()

        schema_fields: list[SchemaFieldInfoDTO] = []
        for entity in self._entities:
            if entity.id == self._selected_entity_id:
                for field in entity.fields:
                    schema_fields.append(
                        SchemaFieldInfoDTO(
                            field_id=field.id,
                            field_type=field.field_type,
                            label=field.label,
                        )
                    )
                break

        return tuple(schema_fields)

    def _compute_field_preview_states(self) -> None:
        """Compute field preview states from rule results.

        Applies rule effects to field states:
        - VISIBILITY: affects is_visible
        - ENABLED: affects is_enabled
        - REQUIRED: affects show_required_indicator
        """
        # Reset all field states
        self._field_preview_states = {}

        # Get all field IDs for current entity
        field_ids: list[str] = []
        if self._selected_entity_id:
            for entity in self._entities:
                if entity.id == self._selected_entity_id:
                    field_ids = [f.id for f in entity.fields]
                    break

        # Initialize default states for all fields
        for field_id in field_ids:
            self._field_preview_states[field_id] = FieldPreviewStateDTO(
                field_id=field_id,
                is_visible=True,
                is_enabled=True,
                show_required_indicator=False,
                applied_rules=(),
                blocked_rules=(),
            )

        # Apply rule results
        for result in self._preview_results:
            target_id = result.rule_input.target_field_id
            if target_id not in self._field_preview_states:
                continue

            current_state = self._field_preview_states[target_id]
            applied_rules = list(current_state.applied_rules)
            blocked_rules = list(current_state.blocked_rules)

            if result.is_blocked:
                # Rule is blocked, record it but don't apply
                blocked_rules.append(
                    (result.rule_input.rule_type, result.block_reason or "Unknown")
                )
            elif result.is_allowed and result.execution_result is not None:
                # Rule is allowed and executed, apply effect
                applied_rules.append(result.rule_input.rule_type)

                # Get current state values
                is_visible = current_state.is_visible
                is_enabled = current_state.is_enabled
                show_required = current_state.show_required_indicator

                # Apply effect based on rule type
                if result.rule_input.rule_type == ControlRuleType.VISIBILITY:
                    is_visible = result.execution_result
                elif result.rule_input.rule_type == ControlRuleType.ENABLED:
                    is_enabled = result.execution_result
                elif result.rule_input.rule_type == ControlRuleType.REQUIRED:
                    show_required = result.execution_result

                # Update state
                self._field_preview_states[target_id] = FieldPreviewStateDTO(
                    field_id=target_id,
                    is_visible=is_visible,
                    is_enabled=is_enabled,
                    show_required_indicator=show_required,
                    applied_rules=tuple(applied_rules),
                    blocked_rules=tuple(blocked_rules),
                )
            else:
                # Rule allowed but execution had error or no result
                # Just update blocked_rules if there was an error
                if result.execution_error:
                    blocked_rules.append(
                        (
                            result.rule_input.rule_type,
                            f"Execution error: {result.execution_error}",
                        )
                    )
                    self._field_preview_states[target_id] = FieldPreviewStateDTO(
                        field_id=target_id,
                        is_visible=current_state.is_visible,
                        is_enabled=current_state.is_enabled,
                        show_required_indicator=current_state.show_required_indicator,
                        applied_rules=tuple(applied_rules),
                        blocked_rules=tuple(blocked_rules),
                    )

        self.notify_change("preview_mode_state")

    def _clear_preview_state(self) -> None:
        """Clear all preview state (internal)."""
        self._preview_field_values.clear()
        self._preview_control_rules.clear()
        self._preview_results.clear()
        self._field_preview_states.clear()

        self.notify_change("preview_field_values")
        self.notify_change("preview_control_rules")
        self.notify_change("preview_results")
        self.notify_change("preview_mode_state")

    # -------------------------------------------------------------------------
    # Phase F-11: Persisted Control Rules Commands (DESIGN-TIME ONLY)
    # -------------------------------------------------------------------------

    def load_control_rules(self) -> None:
        """Load persisted control rules for currently selected field (Phase F-11).

        Phase F-11 Compliance:
            - Calls SchemaUseCases.list_control_rules_for_field()
            - Design-time only, no runtime enforcement
            - Updates _control_rules and notifies UI
        """
        if not self._selected_entity_id or not self._selected_field_id:
            self._control_rules = ()
            self.notify_change("control_rules")
            self.notify_change("has_control_rules")
            return

        # Load control rules from SchemaUseCases
        self._control_rules = self._schema_usecases.list_control_rules_for_field(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
        )

        self.notify_change("control_rules")
        self.notify_change("has_control_rules")

    def add_control_rule(
        self,
        rule_type: str,
        target_field_id: str,
        formula_text: str,
    ) -> OperationResult:
        """Add a persisted control rule to selected field (Phase F-11).

        Args:
            rule_type: Control rule type (VISIBILITY, ENABLED, REQUIRED)
            target_field_id: ID of field this rule applies to
            formula_text: Boolean formula expression

        Returns:
            OperationResult with success status and message

        Phase F-11 Compliance:
            - Delegates to SchemaUseCases.add_control_rule()
            - Enforces formula governance and boolean validation
            - Reloads control rules on success
            - Design-time only, no runtime enforcement
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return OperationResult(
                success=False,
                error="No field selected",
            )

        result = self._schema_usecases.add_control_rule(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
            rule_type=rule_type,
            formula_text=formula_text,
        )

        if result.success:
            # Reload control rules to show new rule
            self.load_control_rules()
            # Reload entities to update field metadata
            self.load_entities()

        return result

    def update_control_rule(
        self,
        rule_type: str,
        formula_text: str,
    ) -> OperationResult:
        """Update an existing persisted control rule (Phase F-11).

        Args:
            rule_type: Control rule type to update (VISIBILITY, ENABLED, REQUIRED)
            formula_text: New boolean formula expression

        Returns:
            OperationResult with success status and message

        Phase F-11 Compliance:
            - Delegates to SchemaUseCases.update_control_rule()
            - Re-validates formula with governance and boolean check
            - Reloads control rules on success
            - Design-time only, no runtime enforcement
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return OperationResult(
                success=False,
                error="No field selected",
            )

        result = self._schema_usecases.update_control_rule(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
            rule_type=rule_type,
            formula_text=formula_text,
        )

        if result.success:
            # Reload control rules to show updated rule
            self.load_control_rules()
            # Reload entities to update field metadata
            self.load_entities()

        return result

    def delete_control_rule(
        self,
        rule_type: str,
    ) -> OperationResult:
        """Delete a persisted control rule from selected field (Phase F-11).

        Args:
            rule_type: Control rule type to delete (VISIBILITY, ENABLED, REQUIRED)

        Returns:
            OperationResult with success status and message

        Phase F-11 Compliance:
            - Delegates to SchemaUseCases.delete_control_rule()
            - Reloads control rules on success
            - Design-time only, no runtime enforcement
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return OperationResult(
                success=False,
                error="No field selected",
            )

        result = self._schema_usecases.delete_control_rule(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
            rule_type=rule_type,
        )

        if result.success:
            # Reload control rules to reflect deletion
            self.load_control_rules()
            # Reload entities to update field metadata
            self.load_entities()

        return result

    # -------------------------------------------------------------------------
    # Phase F-13: Persisted Output Mappings Commands (DESIGN-TIME ONLY)
    # -------------------------------------------------------------------------

    def load_output_mappings(self) -> None:
        """Load persisted output mappings for currently selected field (Phase F-13).

        Phase F-13 Compliance:
            - Calls SchemaUseCases.list_output_mappings_for_field()
            - Design-time only, no runtime execution
            - Updates _output_mappings and notifies UI
        """
        if not self._selected_entity_id or not self._selected_field_id:
            self._output_mappings = ()
            self.notify_change("output_mappings")
            self.notify_change("has_output_mappings")
            return

        # Load output mappings from SchemaUseCases
        self._output_mappings = self._schema_usecases.list_output_mappings_for_field(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
        )

        self.notify_change("output_mappings")
        self.notify_change("has_output_mappings")

    def add_output_mapping(
        self,
        target: str,
        formula_text: str,
    ) -> OperationResult:
        """Add a persisted output mapping to selected field (Phase F-13).

        Args:
            target: Output target type (TEXT, NUMBER, BOOLEAN)
            formula_text: Formula expression for output transformation

        Returns:
            OperationResult with success status and message

        Phase F-13 Compliance:
            - Delegates to SchemaUseCases.add_output_mapping()
            - Reloads output mappings on success
            - Design-time only, no runtime execution
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return OperationResult(
                success=False,
                error="No field selected",
            )

        result = self._schema_usecases.add_output_mapping(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
            target=target,
            formula_text=formula_text,
        )

        if result.success:
            # Reload output mappings to show new mapping
            self.load_output_mappings()
            # Reload entities to update field metadata
            self.load_entities()

        return result

    def update_output_mapping(
        self,
        target: str,
        formula_text: str,
    ) -> OperationResult:
        """Update an existing persisted output mapping (Phase F-13).

        Args:
            target: Output target type to update (TEXT, NUMBER, BOOLEAN)
            formula_text: New formula expression

        Returns:
            OperationResult with success status and message

        Phase F-13 Compliance:
            - Delegates to SchemaUseCases.update_output_mapping()
            - Reloads output mappings on success
            - Design-time only, no runtime execution
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return OperationResult(
                success=False,
                error="No field selected",
            )

        result = self._schema_usecases.update_output_mapping(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
            target=target,
            formula_text=formula_text,
        )

        if result.success:
            # Reload output mappings to show updated mapping
            self.load_output_mappings()
            # Reload entities to update field metadata
            self.load_entities()

        return result

    def delete_output_mapping(
        self,
        target: str,
    ) -> OperationResult:
        """Delete a persisted output mapping from selected field (Phase F-13).

        Args:
            target: Output target type to delete (TEXT, NUMBER, BOOLEAN)

        Returns:
            OperationResult with success status and message

        Phase F-13 Compliance:
            - Delegates to SchemaUseCases.delete_output_mapping()
            - Reloads output mappings on success
            - Design-time only, no runtime execution
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return OperationResult(
                success=False,
                error="No field selected",
            )

        result = self._schema_usecases.delete_output_mapping(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
            target=target,
        )

        if result.success:
            # Reload output mappings to reflect deletion
            self.load_output_mappings()
            # Reload entities to update field metadata
            self.load_entities()

        return result

    # -------------------------------------------------------------------------
    # Phase F-14: Field Option Commands (DESIGN-TIME ONLY)
    # -------------------------------------------------------------------------

    def load_field_options(self) -> None:
        """Load field options for currently selected field (Phase F-14).

        Phase F-14 Compliance:
            - Calls SchemaUseCases.list_field_options()
            - Design-time only, returns label_key not translated label
            - Updates _field_options and notifies UI
        """
        if not self._selected_entity_id or not self._selected_field_id:
            self._field_options = ()
            self.notify_change("field_options")
            self.notify_change("has_field_options")
            return

        # Load field options from SchemaUseCases
        self._field_options = self._schema_usecases.list_field_options(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
        )

        self.notify_change("field_options")
        self.notify_change("has_field_options")

    def add_field_option(
        self,
        option_value: str,
        option_label_key: str,
    ) -> OperationResult:
        """Add an option to selected field (Phase F-14).

        Args:
            option_value: Option value (unique identifier within field)
            option_label_key: Translation key for option label

        Returns:
            OperationResult with success status and message

        Phase F-14 Compliance:
            - Delegates to SchemaUseCases.add_field_option()
            - Reloads field options on success
            - Design-time only, NO runtime execution
            - Only valid for DROPDOWN/RADIO fields
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return OperationResult(
                success=False,
                error="No field selected",
            )

        result = self._schema_usecases.add_field_option(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
            option_value=option_value,
            option_label_key=option_label_key,
        )

        if result.success:
            # Reload field options to show new option
            self.load_field_options()
            # Reload entities to update field metadata
            self.load_entities()

        return result

    def update_field_option(
        self,
        option_value: str,
        new_label_key: str,
    ) -> OperationResult:
        """Update an option's label key in selected field (Phase F-14).

        Args:
            option_value: Option value to update (identifier, immutable)
            new_label_key: New translation key for option label

        Returns:
            OperationResult with success status and message

        Phase F-14 Compliance:
            - Delegates to SchemaUseCases.update_field_option()
            - Reloads field options on success
            - Design-time only, NO runtime execution
            - Option values are immutable (only label_key can change)
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return OperationResult(
                success=False,
                error="No field selected",
            )

        result = self._schema_usecases.update_field_option(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
            option_value=option_value,
            new_label_key=new_label_key,
        )

        if result.success:
            # Reload field options to show updated option
            self.load_field_options()
            # Reload entities to update field metadata
            self.load_entities()

        return result

    def delete_field_option(
        self,
        option_value: str,
    ) -> OperationResult:
        """Delete an option from selected field (Phase F-14).

        Args:
            option_value: Option value to delete

        Returns:
            OperationResult with success status and message

        Phase F-14 Compliance:
            - Delegates to SchemaUseCases.delete_field_option()
            - Reloads field options on success
            - Design-time only, NO runtime execution
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return OperationResult(
                success=False,
                error="No field selected",
            )

        result = self._schema_usecases.delete_field_option(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
            option_value=option_value,
        )

        if result.success:
            # Reload field options to reflect deletion
            self.load_field_options()
            # Reload entities to update field metadata
            self.load_entities()

        return result

    def reorder_field_options(
        self,
        new_option_order: list[str],
    ) -> OperationResult:
        """Reorder options in selected field (Phase F-14).

        Args:
            new_option_order: List of option values in desired order.
                Must contain exactly the same option values as the field.

        Returns:
            OperationResult with success status and message

        Phase F-14 Compliance:
            - Delegates to SchemaUseCases.reorder_field_options()
            - Reloads field options on success
            - Design-time only, NO runtime execution
            - Option values and labels are preserved, only order changes
        """
        if not self._selected_entity_id or not self._selected_field_id:
            return OperationResult(
                success=False,
                error="No field selected",
            )

        result = self._schema_usecases.reorder_field_options(
            entity_id=self._selected_entity_id,
            field_id=self._selected_field_id,
            new_option_order=new_option_order,
        )

        if result.success:
            # Reload field options to reflect new order
            self.load_field_options()
            # Reload entities to update field metadata
            self.load_entities()

        return result

    def dispose(self) -> None:
        """Clean up resources."""
        # Phase F-1: Dispose formula editor viewmodel
        if self._formula_editor_viewmodel:
            self._formula_editor_viewmodel.dispose()
            self._formula_editor_viewmodel = None

        # Phase F-9: Clear preview state
        self._clear_preview_state()
        self._preview_mode_enabled = False

        # Phase F-11: Clear control rules
        self._control_rules = ()

        # Phase F-13: Clear output mappings
        self._output_mappings = ()

        # Phase F-14: Clear field options
        self._field_options = ()

        super().dispose()
        self._entities = ()
        self._relationships = ()
        self._selected_entity_id = None
        self._selected_field_id = None

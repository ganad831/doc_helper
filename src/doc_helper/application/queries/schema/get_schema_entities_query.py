"""Query for loading schema entities with validation rules.

This query encapsulates all domain access for schema entities,
including constraint formatting, so Presentation layer never
touches domain types.

ARCHITECTURAL FIX:
- Replaces direct ISchemaRepository access in ViewModel
- Moves constraint formatting from Presentation to Application
- Keeps all domain imports inside Application layer
"""

from typing import Optional

from doc_helper.application.dto.schema_dto import (
    EntityDefinitionDTO,
    FieldDefinitionDTO,
    FieldOptionDTO,
)
from doc_helper.domain.common.result import Result, Success, Failure
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


class GetSchemaEntitiesQuery:
    """Query for retrieving all schema entities with full field details.

    This query:
    - Loads all entities from schema repository
    - Converts domain entities to DTOs
    - Translates labels and descriptions
    - Formats validation constraints as human-readable strings

    All domain types stay within this query - only DTOs are returned.
    """

    def __init__(
        self,
        schema_repository: ISchemaRepository,
        translation_service,  # ITranslationService
    ) -> None:
        """Initialize query.

        Args:
            schema_repository: Repository for loading schema definitions
            translation_service: Service for translating labels/descriptions
        """
        self._schema_repository = schema_repository
        self._translation_service = translation_service

    def execute(self) -> Result[tuple[EntityDefinitionDTO, ...], str]:
        """Execute query to load all entities.

        Returns:
            Result containing tuple of EntityDefinitionDTOs or error message
        """
        result = self._schema_repository.get_all()
        if result.is_failure():
            return Failure(result.error)

        entity_definitions = result.value
        dtos = tuple(
            self._entity_to_dto(entity) for entity in entity_definitions
        )
        return Success(dtos)

    def get_field_validation_rules(
        self,
        entity_id: str,
        field_id: str,
    ) -> tuple[str, ...]:
        """Get formatted validation rules for a specific field.

        Args:
            entity_id: Entity ID (string)
            field_id: Field ID (string)

        Returns:
            Tuple of human-readable constraint descriptions
        """
        # Convert string IDs to domain IDs (inside application layer)
        entity_result = self._schema_repository.get_by_id(
            EntityDefinitionId(entity_id)
        )
        if entity_result.is_failure():
            return ()

        entity_def = entity_result.value
        field_def = entity_def.get_field(FieldDefinitionId(field_id))
        if not field_def:
            return ()

        # Format constraints as strings (domain logic stays here)
        return tuple(
            self._format_constraint(c) for c in field_def.constraints
        )

    def _entity_to_dto(self, entity_definition) -> EntityDefinitionDTO:
        """Convert EntityDefinition to DTO.

        Args:
            entity_definition: Domain entity definition

        Returns:
            EntityDefinitionDTO for UI consumption
        """
        current_lang = self._translation_service.get_current_language()
        entity_name = self._translation_service.get(
            entity_definition.name_key, current_lang
        )

        entity_description = None
        if entity_definition.description_key:
            entity_description = self._translation_service.get(
                entity_definition.description_key, current_lang
            )

        field_dtos = tuple(
            self._field_to_dto(field) for field in entity_definition.get_all_fields()
        )

        return EntityDefinitionDTO(
            id=str(entity_definition.id.value),
            name=entity_name,
            description=entity_description,
            name_key=entity_definition.name_key.key,
            description_key=(
                entity_definition.description_key.key
                if entity_definition.description_key
                else None
            ),
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
        current_lang = self._translation_service.get_current_language()
        field_label = self._translation_service.get(
            field_definition.label_key, current_lang
        )

        help_text = None
        if field_definition.help_text_key:
            help_text = self._translation_service.get(
                field_definition.help_text_key, current_lang
            )

        option_dtos = ()
        if field_definition.options:
            option_dtos = tuple(
                FieldOptionDTO(
                    value=opt[0],
                    label=self._translation_service.get(opt[1], current_lang),
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

        This method was moved from Presentation layer to Application layer
        to avoid domain constraint imports in ViewModel.

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

"""Schema mappers - Domain → DTO conversion.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- ONE-WAY mapping: Domain → DTO only
- NO to_domain() or from_dto() methods
"""

from typing import Optional

from doc_helper.application.dto import (
    EntityDefinitionDTO,
    FieldDefinitionDTO,
    FieldOptionDTO,
)
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.translation import ITranslationService
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.validation.constraints import RequiredConstraint


class FieldDefinitionMapper:
    """Maps FieldDefinition domain value object to FieldDefinitionDTO.

    This mapper is ONE-WAY: Domain → DTO only.
    Requires ITranslationService to translate label/help text keys.
    """

    def __init__(self, translation_service: ITranslationService) -> None:
        """Initialize mapper with translation service.

        Args:
            translation_service: Service for translating i18n keys
        """
        self._translation_service = translation_service

    def _translate(self, key: str) -> str:
        """Translate a key using the current language.

        Args:
            key: Translation key string

        Returns:
            Translated string
        """
        translation_key = TranslationKey(key)
        current_language = self._translation_service.get_current_language()
        return self._translation_service.get(translation_key, current_language)

    def to_dto(self, field_def: FieldDefinition) -> FieldDefinitionDTO:
        """Convert FieldDefinition to FieldDefinitionDTO.

        Args:
            field_def: FieldDefinition domain value object

        Returns:
            FieldDefinitionDTO for UI display
        """
        # Translate options
        options = tuple(
            FieldOptionDTO(
                value=str(opt_value),
                label=self._translate(opt_label_key),
            )
            for opt_value, opt_label_key in field_def.options
        )

        # Translate help text if present
        help_text: Optional[str] = None
        if field_def.help_text_key is not None:
            help_text = self._translate(field_def.help_text_key)

        # =====================================================================
        # CALCULATED FIELD INVARIANT: CALCULATED fields are NEVER required.
        # Both `required` and `is_required` must be False. No OR logic.
        # =====================================================================
        if field_def.is_calculated:
            required = False
            is_required = False
        else:
            required = field_def.required
            has_required_constraint = any(
                isinstance(c, RequiredConstraint) for c in field_def.constraints
            )
            is_required = required or has_required_constraint

        return FieldDefinitionDTO(
            id=str(field_def.id.value),
            field_type=field_def.field_type.value,
            label=self._translate(field_def.label_key),
            help_text=help_text,
            required=required,
            is_required=is_required,
            default_value=str(field_def.default_value) if field_def.default_value is not None else None,
            options=options,
            formula=field_def.formula,
            is_calculated=field_def.is_calculated,
            is_choice_field=field_def.is_choice_field,
            is_collection_field=field_def.is_collection_field,
            lookup_entity_id=field_def.lookup_entity_id,
            lookup_display_field=field_def.lookup_display_field,
            child_entity_id=field_def.child_entity_id,
        )

    # ❌ FORBIDDEN: No to_domain() or from_dto() methods


class EntityDefinitionMapper:
    """Maps EntityDefinition domain aggregate to EntityDefinitionDTO.

    This mapper is ONE-WAY: Domain → DTO only.
    Requires ITranslationService to translate name/description keys.
    """

    def __init__(self, translation_service: ITranslationService) -> None:
        """Initialize mapper with translation service.

        Args:
            translation_service: Service for translating i18n keys
        """
        self._translation_service = translation_service
        self._field_mapper = FieldDefinitionMapper(translation_service)

    def _translate(self, key: str) -> str:
        """Translate a key using the current language.

        Args:
            key: Translation key string

        Returns:
            Translated string
        """
        translation_key = TranslationKey(key)
        current_language = self._translation_service.get_current_language()
        return self._translation_service.get(translation_key, current_language)

    def to_dto(self, entity_def: EntityDefinition) -> EntityDefinitionDTO:
        """Convert EntityDefinition to EntityDefinitionDTO.

        Args:
            entity_def: EntityDefinition domain aggregate

        Returns:
            EntityDefinitionDTO for UI display
        """
        # Translate description if present
        description: Optional[str] = None
        if entity_def.description_key is not None:
            description = self._translate(entity_def.description_key)

        # Map all fields
        fields = tuple(
            self._field_mapper.to_dto(field_def)
            for field_def in entity_def.get_all_fields()
        )

        return EntityDefinitionDTO(
            id=str(entity_def.id.value),
            name=self._translate(entity_def.name_key.key),
            description=description,
            name_key=entity_def.name_key.key,
            description_key=entity_def.description_key.key if entity_def.description_key else None,
            field_count=entity_def.field_count,
            is_root_entity=entity_def.is_root_entity,
            parent_entity_id=str(entity_def.parent_entity_id.value) if entity_def.parent_entity_id else None,
            fields=fields,
        )

    # ❌ FORBIDDEN: No to_domain() or from_dto() methods

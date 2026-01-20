"""Field value mapper - Domain → DTO conversion.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- ONE-WAY mapping: Domain → DTO only
- NO to_domain() or from_dto() methods
"""

from typing import Any, Optional

from doc_helper.application.dto import FieldValueDTO, FieldStateDTO
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.common.translation import ITranslationService


def _format_display_value(value: Any) -> str:
    """Format any value for display.

    Args:
        value: Raw value

    Returns:
        String representation for display
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


class FieldValueMapper:
    """Maps FieldValue domain value object to FieldValueDTO.

    This mapper is ONE-WAY: Domain → DTO only.
    """

    @staticmethod
    def to_dto(field_value: FieldValue) -> FieldValueDTO:
        """Convert FieldValue to FieldValueDTO.

        Args:
            field_value: FieldValue domain value object

        Returns:
            FieldValueDTO for UI display
        """
        return FieldValueDTO(
            field_id=str(field_value.field_id.value),
            value=field_value.value,
            display_value=_format_display_value(field_value.value),
            is_computed=field_value.is_computed,
            is_override=field_value.is_override,
            computed_from=field_value.computed_from,
            has_original_value=field_value.original_computed_value is not None,
        )

    @staticmethod
    def to_state_dto(
        field_def: FieldDefinition,
        field_value: Optional[FieldValue],
        translation_service: ITranslationService,
        is_valid: bool = True,
        validation_errors: tuple[str, ...] = (),
        is_visible: bool = True,
        is_enabled: bool = True,
    ) -> FieldStateDTO:
        """Create FieldStateDTO combining definition, value, and state.

        Args:
            field_def: Field definition
            field_value: Field value (if any)
            translation_service: Service for translating i18n keys
            is_valid: Whether field passes validation
            validation_errors: Tuple of error messages
            is_visible: Whether field is visible
            is_enabled: Whether field is enabled

        Returns:
            FieldStateDTO combining all field state
        """
        # Get help text
        help_text: Optional[str] = None
        if field_def.help_text_key is not None:
            help_text = translation_service.translate(field_def.help_text_key)

        # Get value info
        has_value = field_value is not None
        value = field_value.value if field_value else None
        display_value = _format_display_value(value)
        is_computed = field_value.is_computed if field_value else False
        is_override = field_value.is_override if field_value else False

        return FieldStateDTO(
            field_id=str(field_def.id.value),
            field_type=field_def.field_type.value,
            label=translation_service.translate(field_def.label_key),
            help_text=help_text,
            required=field_def.required,
            is_calculated=field_def.is_calculated,
            is_choice_field=field_def.is_choice_field,
            has_value=has_value,
            value=value,
            display_value=display_value,
            is_computed=is_computed,
            is_override=is_override,
            is_valid=is_valid,
            validation_errors=validation_errors,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

    # ❌ FORBIDDEN: No to_domain() or from_dto() methods

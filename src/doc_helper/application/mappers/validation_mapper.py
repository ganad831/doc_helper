"""Validation mapper - Domain → DTO conversion.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- ONE-WAY mapping: Domain → DTO only
- NO to_domain() or from_dto() methods
- ADR-025: Map severity enum to string for DTOs
"""

from doc_helper.application.dto import ValidationResultDTO, ValidationErrorDTO
from doc_helper.domain.common.translation import ITranslationService
from doc_helper.domain.validation.validation_result import (
    ValidationResult,
    ValidationError,
)


class ValidationMapper:
    """Maps ValidationResult domain value object to ValidationResultDTO.

    This mapper is ONE-WAY: Domain → DTO only.
    Requires ITranslationService to translate error message keys.
    ADR-025: Converts severity enum to string for DTOs.
    """

    def __init__(self, translation_service: ITranslationService) -> None:
        """Initialize mapper with translation service.

        Args:
            translation_service: Service for translating i18n keys
        """
        self._translation_service = translation_service

    def error_to_dto(self, error: ValidationError) -> ValidationErrorDTO:
        """Convert ValidationError to ValidationErrorDTO.

        Args:
            error: ValidationError domain value object

        Returns:
            ValidationErrorDTO for UI display
        """
        # Translate error message with parameters
        # error.message_key is already a TranslationKey
        current_language = self._translation_service.get_current_language()
        message = self._translation_service.get(
            error.message_key,
            current_language,
            error.constraint_params,
        )

        return ValidationErrorDTO(
            field_id=error.field_path,
            message=message,
            constraint_type=error.constraint_type,
            severity=error.severity.value,  # Convert enum to string (ADR-025)
        )

    def to_dto(
        self,
        result: ValidationResult,
        field_id: str | None = None,
    ) -> ValidationResultDTO:
        """Convert ValidationResult to ValidationResultDTO.

        Args:
            result: ValidationResult domain value object
            field_id: Optional field ID (for single-field validation)

        Returns:
            ValidationResultDTO for UI display
        """
        errors = tuple(
            self.error_to_dto(error)
            for error in result.errors
        )

        return ValidationResultDTO(
            is_valid=result.is_valid(),
            errors=errors,
            field_id=field_id,
        )

    # ❌ FORBIDDEN: No to_domain() or from_dto() methods

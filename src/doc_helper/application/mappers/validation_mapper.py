"""Validation mapper - Domain → DTO conversion.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- ONE-WAY mapping: Domain → DTO only
- NO to_domain() or from_dto() methods
- ADR-025: Map severity enum to string for DTOs
- Phase H-3: This mapper is the SINGLE construction authority for ValidationResultDTO
"""

from doc_helper.application.dto import ValidationResultDTO, ValidationErrorDTO
from doc_helper.domain.common.translation import ITranslationService
from doc_helper.domain.validation.validation_result import (
    ValidationResult,
    ValidationError,
)


def create_valid_validation_result(
    field_id: str | None = None,
) -> ValidationResultDTO:
    """Create a valid (no errors) ValidationResultDTO.

    Phase H-3: Factory function for creating valid DTOs.
    This is an authorized construction path for tests and services.

    Args:
        field_id: Optional field ID for field-level validation

    Returns:
        ValidationResultDTO with no errors
    """
    return ValidationResultDTO(
        is_valid=True,
        errors=(),
        _error_count=0,
        _error_messages=(),
        _has_blocking_errors=False,
        _has_warnings=False,
        _has_info=False,
        field_id=field_id,
    )


def create_error_validation_result(
    message: str,
    field_id: str | None = None,
    constraint_type: str = "SYSTEM_ERROR",
    severity: str = "ERROR",
) -> ValidationResultDTO:
    """Create a ValidationResultDTO for synthetic error cases.

    Phase H-3: Factory function for creating error DTOs without domain objects.
    This is an authorized construction path for ViewModels and services that need
    to create error results without going through full domain validation.

    Args:
        message: Error message to display
        field_id: Optional field ID associated with the error
        constraint_type: Type of constraint (default: SYSTEM_ERROR)
        severity: Error severity (default: ERROR)

    Returns:
        ValidationResultDTO with the error
    """
    error = ValidationErrorDTO(
        field_id=field_id if field_id else "",
        message=message,
        constraint_type=constraint_type,
        severity=severity,
    )
    errors = (error,)
    return ValidationResultDTO(
        is_valid=False,
        errors=errors,
        _error_count=1,
        _error_messages=(message,),
        _has_blocking_errors=(severity == "ERROR"),
        _has_warnings=(severity == "WARNING"),
        _has_info=(severity == "INFO"),
        field_id=field_id,
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

        # Pre-compute derived values (Phase H-2: DTO Purity)
        error_count = len(errors)
        error_messages = tuple(error.message for error in errors)
        has_blocking_errors = any(error.severity == "ERROR" for error in errors)
        has_warnings = any(error.severity == "WARNING" for error in errors)
        has_info = any(error.severity == "INFO" for error in errors)

        return ValidationResultDTO(
            is_valid=result.is_valid(),
            errors=errors,
            field_id=field_id,
            _error_count=error_count,
            _error_messages=error_messages,
            _has_blocking_errors=has_blocking_errors,
            _has_warnings=has_warnings,
            _has_info=has_info,
        )

    # ❌ FORBIDDEN: No to_domain() or from_dto() methods

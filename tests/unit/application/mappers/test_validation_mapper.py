"""Unit tests for ValidationMapper."""

from typing import Any, Dict, Optional

import pytest

from doc_helper.application.dto import ValidationResultDTO, ValidationErrorDTO
from doc_helper.application.mappers import ValidationMapper
from doc_helper.domain.common.i18n import Language, TranslationKey
from doc_helper.domain.common.translation import ITranslationService
from doc_helper.domain.validation.validation_result import (
    ValidationResult,
    ValidationError,
)


class MockTranslationService(ITranslationService):
    """Mock translation service for testing."""

    def get(
        self,
        key: TranslationKey,
        language: Language,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get translated string for key and language."""
        result = f"[{key.key}]"
        if params:
            param_str = ", ".join(f"{k}={v}" for k, v in params.items())
            result = f"[{key.key}: {param_str}]"
        return result

    def get_current_language(self) -> Language:
        """Get the currently selected language."""
        return Language.ENGLISH

    def set_language(self, language: Language) -> None:
        """Set the current language."""
        pass

    def has_key(self, key: TranslationKey, language: Language) -> bool:
        """Check if translation exists for key and language."""
        return True


class TestValidationMapper:
    """Tests for ValidationMapper."""

    @pytest.fixture
    def translation_service(self) -> MockTranslationService:
        """Create mock translation service."""
        return MockTranslationService()

    @pytest.fixture
    def mapper(
        self, translation_service: MockTranslationService
    ) -> ValidationMapper:
        """Create ValidationMapper."""
        return ValidationMapper(translation_service)

    def test_error_to_dto(self, mapper: ValidationMapper) -> None:
        """error_to_dto should convert ValidationError to DTO."""
        error = ValidationError(
            field_path="field_1",
            message_key=TranslationKey("validation.required"),
            constraint_type="required",
            current_value=None,
            constraint_params={"field_name": "Field 1"},
        )

        dto = mapper.error_to_dto(error)

        assert isinstance(dto, ValidationErrorDTO)
        assert dto.field_id == "field_1"
        assert dto.constraint_type == "required"
        # Message should be translated with params
        assert "validation.required" in dto.message
        assert "field_name" in dto.message

    def test_error_to_dto_no_params(self, mapper: ValidationMapper) -> None:
        """error_to_dto should handle errors without params."""
        error = ValidationError(
            field_path="field_2",
            message_key=TranslationKey("validation.invalid"),
            constraint_type="invalid",
            current_value="bad value",
            constraint_params=None,
        )

        dto = mapper.error_to_dto(error)

        assert dto.field_id == "field_2"
        assert "[validation.invalid]" in dto.message

    def test_to_dto_valid_result(self, mapper: ValidationMapper) -> None:
        """to_dto should convert valid ValidationResult to DTO."""
        result = ValidationResult.success()

        dto = mapper.to_dto(result)

        assert isinstance(dto, ValidationResultDTO)
        assert dto.is_valid is True
        assert len(dto.errors) == 0

    def test_to_dto_invalid_result(self, mapper: ValidationMapper) -> None:
        """to_dto should convert invalid ValidationResult to DTO."""
        errors = (
            ValidationError(
                field_path="field_1",
                message_key=TranslationKey("validation.required"),
                constraint_type="required",
                current_value=None,
            ),
            ValidationError(
                field_path="field_2",
                message_key=TranslationKey("validation.min-length"),
                constraint_type="min_length",
                current_value="ab",
                constraint_params={"min": 5},
            ),
        )
        result = ValidationResult.failure(errors)

        dto = mapper.to_dto(result)

        assert dto.is_valid is False
        assert len(dto.errors) == 2
        assert dto.errors[0].field_id == "field_1"
        assert dto.errors[1].field_id == "field_2"

    def test_to_dto_with_field_id(self, mapper: ValidationMapper) -> None:
        """to_dto should include field_id if provided."""
        result = ValidationResult.success()

        dto = mapper.to_dto(result, field_id="specific_field")

        assert dto.field_id == "specific_field"

    def test_to_dto_is_immutable(self, mapper: ValidationMapper) -> None:
        """ValidationResultDTO should be immutable (frozen)."""
        result = ValidationResult.success()
        dto = mapper.to_dto(result)

        with pytest.raises(Exception):  # frozen dataclass raises
            dto.is_valid = False  # type: ignore

    def test_no_reverse_mapping(self) -> None:
        """ValidationMapper should NOT have reverse mapping methods."""
        assert not hasattr(ValidationMapper, "to_domain")
        assert not hasattr(ValidationMapper, "from_dto")

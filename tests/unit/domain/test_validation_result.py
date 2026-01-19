"""Tests for ValidationResult and ValidationError."""

import pytest

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.validation.validation_result import (
    ValidationError,
    ValidationResult,
)


class TestValidationError:
    """Tests for ValidationError."""

    def test_create_validation_error(self) -> None:
        """ValidationError should be created with all fields."""
        error = ValidationError(
            field_path="project.site_location",
            message_key=TranslationKey("validation.required"),
            constraint_type="RequiredConstraint",
            current_value=None,
        )
        assert error.field_path == "project.site_location"
        assert error.message_key.key == "validation.required"
        assert error.constraint_type == "RequiredConstraint"
        assert error.current_value is None
        assert error.constraint_params is None

    def test_validation_error_with_params(self) -> None:
        """ValidationError should accept constraint_params."""
        error = ValidationError(
            field_path="name",
            message_key=TranslationKey("validation.min_length"),
            constraint_type="MinLengthConstraint",
            current_value="Hi",
            constraint_params={"min": 5},
        )
        assert error.constraint_params == {"min": 5}

    def test_empty_field_path_raises(self) -> None:
        """ValidationError should reject empty field_path."""
        with pytest.raises(ValueError, match="field_path cannot be empty"):
            ValidationError(
                field_path="",
                message_key=TranslationKey("validation.required"),
                constraint_type="RequiredConstraint",
                current_value=None,
            )

    def test_empty_constraint_type_raises(self) -> None:
        """ValidationError should reject empty constraint_type."""
        with pytest.raises(ValueError, match="constraint_type cannot be empty"):
            ValidationError(
                field_path="field",
                message_key=TranslationKey("validation.required"),
                constraint_type="",
                current_value=None,
            )

    def test_validation_error_immutable(self) -> None:
        """ValidationError should be immutable."""
        error = ValidationError(
            field_path="field",
            message_key=TranslationKey("validation.required"),
            constraint_type="RequiredConstraint",
            current_value=None,
        )
        with pytest.raises(AttributeError):
            error.field_path = "new_field"  # type: ignore

    def test_validation_error_equality(self) -> None:
        """ValidationError should compare by value."""
        error1 = ValidationError(
            field_path="field",
            message_key=TranslationKey("validation.required"),
            constraint_type="RequiredConstraint",
            current_value=None,
        )
        error2 = ValidationError(
            field_path="field",
            message_key=TranslationKey("validation.required"),
            constraint_type="RequiredConstraint",
            current_value=None,
        )
        assert error1 == error2


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_create_success_result(self) -> None:
        """ValidationResult.success() should create valid result."""
        result = ValidationResult.success()
        assert result.is_valid()
        assert not result.is_invalid()
        assert result.error_count == 0
        assert len(result.errors) == 0

    def test_create_failure_result(self) -> None:
        """ValidationResult.failure() should create invalid result."""
        errors = (
            ValidationError(
                field_path="field1",
                message_key=TranslationKey("validation.required"),
                constraint_type="RequiredConstraint",
                current_value=None,
            ),
            ValidationError(
                field_path="field2",
                message_key=TranslationKey("validation.min_length"),
                constraint_type="MinLengthConstraint",
                current_value="Hi",
                constraint_params={"min": 5},
            ),
        )
        result = ValidationResult.failure(errors)
        assert not result.is_valid()
        assert result.is_invalid()
        assert result.error_count == 2
        assert len(result.errors) == 2

    def test_errors_must_be_tuple(self) -> None:
        """ValidationResult should reject non-tuple errors."""
        with pytest.raises(ValueError, match="errors must be a tuple"):
            ValidationResult(errors=[])  # type: ignore

    def test_errors_must_be_validation_error(self) -> None:
        """ValidationResult should reject non-ValidationError items."""
        with pytest.raises(ValueError, match="All errors must be ValidationError"):
            ValidationResult(errors=("not an error",))  # type: ignore

    def test_validation_result_immutable(self) -> None:
        """ValidationResult should be immutable."""
        result = ValidationResult.success()
        with pytest.raises(AttributeError):
            result.errors = ()  # type: ignore

    def test_get_errors_for_field(self) -> None:
        """ValidationResult should filter errors by field."""
        errors = (
            ValidationError(
                field_path="field1",
                message_key=TranslationKey("validation.required"),
                constraint_type="RequiredConstraint",
                current_value=None,
            ),
            ValidationError(
                field_path="field2",
                message_key=TranslationKey("validation.required"),
                constraint_type="RequiredConstraint",
                current_value=None,
            ),
            ValidationError(
                field_path="field1",
                message_key=TranslationKey("validation.min_length"),
                constraint_type="MinLengthConstraint",
                current_value="Hi",
            ),
        )
        result = ValidationResult.failure(errors)

        field1_errors = result.get_errors_for_field("field1")
        assert len(field1_errors) == 2
        assert all(e.field_path == "field1" for e in field1_errors)

        field2_errors = result.get_errors_for_field("field2")
        assert len(field2_errors) == 1
        assert field2_errors[0].field_path == "field2"

    def test_has_errors_for_field(self) -> None:
        """ValidationResult should check if field has errors."""
        errors = (
            ValidationError(
                field_path="field1",
                message_key=TranslationKey("validation.required"),
                constraint_type="RequiredConstraint",
                current_value=None,
            ),
        )
        result = ValidationResult.failure(errors)

        assert result.has_errors_for_field("field1")
        assert not result.has_errors_for_field("field2")

    def test_merge_validation_results(self) -> None:
        """ValidationResult should merge with another result."""
        result1 = ValidationResult.failure((
            ValidationError(
                field_path="field1",
                message_key=TranslationKey("validation.required"),
                constraint_type="RequiredConstraint",
                current_value=None,
            ),
        ))
        result2 = ValidationResult.failure((
            ValidationError(
                field_path="field2",
                message_key=TranslationKey("validation.required"),
                constraint_type="RequiredConstraint",
                current_value=None,
            ),
        ))

        merged = result1.merge(result2)
        assert merged.error_count == 2
        assert merged.has_errors_for_field("field1")
        assert merged.has_errors_for_field("field2")

    def test_merge_with_success(self) -> None:
        """ValidationResult should merge success results."""
        result1 = ValidationResult.success()
        result2 = ValidationResult.success()

        merged = result1.merge(result2)
        assert merged.is_valid()
        assert merged.error_count == 0

    def test_merge_success_with_failure(self) -> None:
        """ValidationResult should merge success with failure."""
        result1 = ValidationResult.success()
        result2 = ValidationResult.failure((
            ValidationError(
                field_path="field1",
                message_key=TranslationKey("validation.required"),
                constraint_type="RequiredConstraint",
                current_value=None,
            ),
        ))

        merged = result1.merge(result2)
        assert not merged.is_valid()
        assert merged.error_count == 1

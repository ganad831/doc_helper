"""Unit tests for LOOKUP display field validation (Pure Domain Logic).

Tests for the validation functions in lookup_display_field.py.
Ensures invariants are properly enforced:
- lookup_display_field must reference an existing field
- Must NOT reference CALCULATED, TABLE, FILE, IMAGE field types
- NULL is explicitly allowed
"""

import pytest

from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.validation.lookup_display_field import (
    INVALID_DISPLAY_FIELD_TYPES,
    VALID_DISPLAY_FIELD_TYPES,
    LookupDisplayFieldValidationResult,
    validate_lookup_display_field,
    is_valid_display_field_type,
    get_valid_display_fields,
)


class TestValidateLookupDisplayField:
    """Tests for validate_lookup_display_field function."""

    @pytest.fixture
    def available_fields(self) -> dict[str, FieldType]:
        """Create sample available fields for testing."""
        return {
            "name": FieldType.TEXT,
            "description": FieldType.TEXTAREA,
            "count": FieldType.NUMBER,
            "created_date": FieldType.DATE,
            "status": FieldType.DROPDOWN,
            "is_active": FieldType.CHECKBOX,
            "priority": FieldType.RADIO,
            "parent_ref": FieldType.LOOKUP,
            "total": FieldType.CALCULATED,
            "children": FieldType.TABLE,
            "document": FieldType.FILE,
            "photo": FieldType.IMAGE,
        }

    def test_none_is_valid(self, available_fields):
        """NULL lookup_display_field is explicitly allowed."""
        result = validate_lookup_display_field(
            lookup_display_field=None,
            available_fields=available_fields,
        )
        assert result.is_valid
        assert result.error_code is None
        assert result.error_message is None

    def test_empty_string_is_valid(self, available_fields):
        """Empty string is treated as None (valid)."""
        result = validate_lookup_display_field(
            lookup_display_field="",
            available_fields=available_fields,
        )
        assert result.is_valid

    def test_whitespace_only_is_valid(self, available_fields):
        """Whitespace-only string is treated as None (valid)."""
        result = validate_lookup_display_field(
            lookup_display_field="   ",
            available_fields=available_fields,
        )
        assert result.is_valid

    def test_valid_text_field(self, available_fields):
        """TEXT field is valid for display."""
        result = validate_lookup_display_field(
            lookup_display_field="name",
            available_fields=available_fields,
        )
        assert result.is_valid

    def test_valid_textarea_field(self, available_fields):
        """TEXTAREA field is valid for display."""
        result = validate_lookup_display_field(
            lookup_display_field="description",
            available_fields=available_fields,
        )
        assert result.is_valid

    def test_valid_number_field(self, available_fields):
        """NUMBER field is valid for display."""
        result = validate_lookup_display_field(
            lookup_display_field="count",
            available_fields=available_fields,
        )
        assert result.is_valid

    def test_valid_date_field(self, available_fields):
        """DATE field is valid for display."""
        result = validate_lookup_display_field(
            lookup_display_field="created_date",
            available_fields=available_fields,
        )
        assert result.is_valid

    def test_valid_dropdown_field(self, available_fields):
        """DROPDOWN field is valid for display."""
        result = validate_lookup_display_field(
            lookup_display_field="status",
            available_fields=available_fields,
        )
        assert result.is_valid

    def test_valid_checkbox_field(self, available_fields):
        """CHECKBOX field is valid for display."""
        result = validate_lookup_display_field(
            lookup_display_field="is_active",
            available_fields=available_fields,
        )
        assert result.is_valid

    def test_valid_radio_field(self, available_fields):
        """RADIO field is valid for display."""
        result = validate_lookup_display_field(
            lookup_display_field="priority",
            available_fields=available_fields,
        )
        assert result.is_valid

    def test_valid_lookup_field(self, available_fields):
        """LOOKUP field can reference another LOOKUP's display value."""
        result = validate_lookup_display_field(
            lookup_display_field="parent_ref",
            available_fields=available_fields,
        )
        assert result.is_valid

    def test_invalid_calculated_field(self, available_fields):
        """CALCULATED field cannot be used as display field."""
        result = validate_lookup_display_field(
            lookup_display_field="total",
            available_fields=available_fields,
        )
        assert not result.is_valid
        assert result.error_code == "INVALID_FIELD_TYPE"
        assert "calculated" in result.error_message

    def test_invalid_table_field(self, available_fields):
        """TABLE field cannot be used as display field."""
        result = validate_lookup_display_field(
            lookup_display_field="children",
            available_fields=available_fields,
        )
        assert not result.is_valid
        assert result.error_code == "INVALID_FIELD_TYPE"
        assert "table" in result.error_message

    def test_invalid_file_field(self, available_fields):
        """FILE field cannot be used as display field."""
        result = validate_lookup_display_field(
            lookup_display_field="document",
            available_fields=available_fields,
        )
        assert not result.is_valid
        assert result.error_code == "INVALID_FIELD_TYPE"
        assert "file" in result.error_message

    def test_invalid_image_field(self, available_fields):
        """IMAGE field cannot be used as display field."""
        result = validate_lookup_display_field(
            lookup_display_field="photo",
            available_fields=available_fields,
        )
        assert not result.is_valid
        assert result.error_code == "INVALID_FIELD_TYPE"
        assert "image" in result.error_message

    def test_nonexistent_field(self, available_fields):
        """Non-existent field is invalid."""
        result = validate_lookup_display_field(
            lookup_display_field="nonexistent",
            available_fields=available_fields,
        )
        assert not result.is_valid
        assert result.error_code == "FIELD_NOT_FOUND"
        assert "nonexistent" in result.error_message


class TestIsValidDisplayFieldType:
    """Tests for is_valid_display_field_type utility function."""

    @pytest.mark.parametrize("field_type", [
        FieldType.TEXT,
        FieldType.TEXTAREA,
        FieldType.NUMBER,
        FieldType.DATE,
        FieldType.DROPDOWN,
        FieldType.CHECKBOX,
        FieldType.RADIO,
        FieldType.LOOKUP,
    ])
    def test_valid_types(self, field_type):
        """All valid display field types should return True."""
        assert is_valid_display_field_type(field_type) is True

    @pytest.mark.parametrize("field_type", [
        FieldType.CALCULATED,
        FieldType.TABLE,
        FieldType.FILE,
        FieldType.IMAGE,
    ])
    def test_invalid_types(self, field_type):
        """All invalid display field types should return False."""
        assert is_valid_display_field_type(field_type) is False


class TestGetValidDisplayFields:
    """Tests for get_valid_display_fields utility function."""

    def test_filters_out_invalid_types(self):
        """Should filter out CALCULATED, TABLE, FILE, IMAGE types."""
        available_fields = {
            "name": FieldType.TEXT,
            "total": FieldType.CALCULATED,
            "children": FieldType.TABLE,
            "doc": FieldType.FILE,
            "photo": FieldType.IMAGE,
            "count": FieldType.NUMBER,
        }

        result = get_valid_display_fields(available_fields)

        assert "name" in result
        assert "count" in result
        assert "total" not in result
        assert "children" not in result
        assert "doc" not in result
        assert "photo" not in result
        assert len(result) == 2

    def test_returns_new_dict(self):
        """Should return a new dict, not mutate input."""
        original = {"name": FieldType.TEXT, "total": FieldType.CALCULATED}
        result = get_valid_display_fields(original)

        assert result is not original
        assert "total" in original  # Original unchanged
        assert "total" not in result


class TestConstants:
    """Tests for module-level constants."""

    def test_invalid_types_are_correct(self):
        """INVALID_DISPLAY_FIELD_TYPES contains exactly the right types."""
        assert FieldType.CALCULATED in INVALID_DISPLAY_FIELD_TYPES
        assert FieldType.TABLE in INVALID_DISPLAY_FIELD_TYPES
        assert FieldType.FILE in INVALID_DISPLAY_FIELD_TYPES
        assert FieldType.IMAGE in INVALID_DISPLAY_FIELD_TYPES
        assert len(INVALID_DISPLAY_FIELD_TYPES) == 4

    def test_valid_types_are_correct(self):
        """VALID_DISPLAY_FIELD_TYPES contains all valid types."""
        assert FieldType.TEXT in VALID_DISPLAY_FIELD_TYPES
        assert FieldType.TEXTAREA in VALID_DISPLAY_FIELD_TYPES
        assert FieldType.NUMBER in VALID_DISPLAY_FIELD_TYPES
        assert FieldType.DATE in VALID_DISPLAY_FIELD_TYPES
        assert FieldType.DROPDOWN in VALID_DISPLAY_FIELD_TYPES
        assert FieldType.CHECKBOX in VALID_DISPLAY_FIELD_TYPES
        assert FieldType.RADIO in VALID_DISPLAY_FIELD_TYPES
        assert FieldType.LOOKUP in VALID_DISPLAY_FIELD_TYPES
        assert len(VALID_DISPLAY_FIELD_TYPES) == 8

    def test_valid_and_invalid_are_disjoint(self):
        """Valid and invalid sets should have no overlap."""
        overlap = VALID_DISPLAY_FIELD_TYPES & INVALID_DISPLAY_FIELD_TYPES
        assert len(overlap) == 0

    def test_valid_and_invalid_cover_all_except_none(self):
        """Valid + invalid should cover all field types."""
        all_types = set(FieldType)
        covered = VALID_DISPLAY_FIELD_TYPES | INVALID_DISPLAY_FIELD_TYPES
        assert covered == all_types

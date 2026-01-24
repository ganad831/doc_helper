"""Tests for Constraint Availability Engine (Phase SD-6).

Tests the central mapping of FieldType -> AllowedConstraints.
"""

import pytest

from doc_helper.presentation.utils.constraint_availability import (
    CONSTRAINT_TYPES,
    get_allowed_constraints,
    is_constraint_allowed,
    has_constraints_available,
)


class TestConstraintTypes:
    """Tests for CONSTRAINT_TYPES constant."""

    def test_constraint_types_contains_basic_constraints(self) -> None:
        """Should contain all basic constraint types."""
        assert "REQUIRED" in CONSTRAINT_TYPES
        assert "MIN_VALUE" in CONSTRAINT_TYPES
        assert "MAX_VALUE" in CONSTRAINT_TYPES
        assert "MIN_LENGTH" in CONSTRAINT_TYPES
        assert "MAX_LENGTH" in CONSTRAINT_TYPES

    def test_constraint_types_contains_advanced_constraints(self) -> None:
        """Should contain all Phase SD-6 advanced constraint types."""
        assert "PATTERN" in CONSTRAINT_TYPES
        assert "ALLOWED_VALUES" in CONSTRAINT_TYPES
        assert "FILE_EXTENSION" in CONSTRAINT_TYPES
        assert "MAX_FILE_SIZE" in CONSTRAINT_TYPES


class TestGetAllowedConstraints:
    """Tests for get_allowed_constraints function."""

    def test_text_field_constraints(self) -> None:
        """TEXT fields should support text-related constraints."""
        allowed = get_allowed_constraints("text")
        assert "REQUIRED" in allowed
        assert "MIN_LENGTH" in allowed
        assert "MAX_LENGTH" in allowed
        assert "PATTERN" in allowed
        assert "ALLOWED_VALUES" in allowed
        # Should NOT include numeric/file constraints
        assert "MIN_VALUE" not in allowed
        assert "MAX_VALUE" not in allowed
        assert "FILE_EXTENSION" not in allowed
        assert "MAX_FILE_SIZE" not in allowed

    def test_textarea_field_constraints(self) -> None:
        """TEXTAREA fields should support same constraints as TEXT."""
        allowed = get_allowed_constraints("textarea")
        assert "REQUIRED" in allowed
        assert "MIN_LENGTH" in allowed
        assert "MAX_LENGTH" in allowed
        assert "PATTERN" in allowed
        assert "ALLOWED_VALUES" in allowed

    def test_number_field_constraints(self) -> None:
        """NUMBER fields should support numeric constraints."""
        allowed = get_allowed_constraints("number")
        assert "REQUIRED" in allowed
        assert "MIN_VALUE" in allowed
        assert "MAX_VALUE" in allowed
        assert "ALLOWED_VALUES" in allowed
        # Should NOT include text/file constraints
        assert "MIN_LENGTH" not in allowed
        assert "MAX_LENGTH" not in allowed
        assert "PATTERN" not in allowed
        assert "FILE_EXTENSION" not in allowed

    def test_date_field_constraints(self) -> None:
        """DATE fields should support min/max date constraints."""
        allowed = get_allowed_constraints("date")
        assert "REQUIRED" in allowed
        assert "MIN_VALUE" in allowed
        assert "MAX_VALUE" in allowed
        # Should NOT include other constraints
        assert "PATTERN" not in allowed
        assert "ALLOWED_VALUES" not in allowed

    def test_checkbox_field_no_constraints(self) -> None:
        """CHECKBOX (boolean) fields should have NO constraints."""
        allowed = get_allowed_constraints("checkbox")
        assert len(allowed) == 0

    def test_dropdown_field_constraints(self) -> None:
        """DROPDOWN fields should support required and allowed values."""
        allowed = get_allowed_constraints("dropdown")
        assert "REQUIRED" in allowed
        assert "ALLOWED_VALUES" in allowed
        assert len(allowed) == 2

    def test_radio_field_constraints(self) -> None:
        """RADIO fields should support required and allowed values."""
        allowed = get_allowed_constraints("radio")
        assert "REQUIRED" in allowed
        assert "ALLOWED_VALUES" in allowed
        assert len(allowed) == 2

    def test_calculated_field_no_constraints(self) -> None:
        """CALCULATED fields should have NO constraints (read-only)."""
        allowed = get_allowed_constraints("calculated")
        assert len(allowed) == 0

    def test_lookup_field_constraints(self) -> None:
        """LOOKUP fields should support only required."""
        allowed = get_allowed_constraints("lookup")
        assert "REQUIRED" in allowed
        assert len(allowed) == 1

    def test_file_field_constraints(self) -> None:
        """FILE fields should support file-related constraints."""
        allowed = get_allowed_constraints("file")
        assert "REQUIRED" in allowed
        assert "FILE_EXTENSION" in allowed
        assert "MAX_FILE_SIZE" in allowed
        # Should NOT include text/numeric constraints
        assert "PATTERN" not in allowed
        assert "MIN_VALUE" not in allowed

    def test_image_field_constraints(self) -> None:
        """IMAGE fields should support file-related constraints."""
        allowed = get_allowed_constraints("image")
        assert "REQUIRED" in allowed
        assert "FILE_EXTENSION" in allowed
        assert "MAX_FILE_SIZE" in allowed

    def test_table_field_constraints(self) -> None:
        """TABLE fields should support only required."""
        allowed = get_allowed_constraints("table")
        assert "REQUIRED" in allowed
        assert len(allowed) == 1

    def test_unknown_field_type_returns_empty(self) -> None:
        """Unknown field types should return empty set."""
        allowed = get_allowed_constraints("unknown_type")
        assert len(allowed) == 0

    def test_case_insensitive(self) -> None:
        """Should be case-insensitive."""
        assert get_allowed_constraints("TEXT") == get_allowed_constraints("text")
        assert get_allowed_constraints("Text") == get_allowed_constraints("text")
        assert get_allowed_constraints("NUMBER") == get_allowed_constraints("number")


class TestIsConstraintAllowed:
    """Tests for is_constraint_allowed function."""

    def test_allowed_constraint_returns_true(self) -> None:
        """Should return True for allowed constraint."""
        assert is_constraint_allowed("text", "REQUIRED") is True
        assert is_constraint_allowed("text", "PATTERN") is True
        assert is_constraint_allowed("number", "MIN_VALUE") is True
        assert is_constraint_allowed("file", "FILE_EXTENSION") is True

    def test_disallowed_constraint_returns_false(self) -> None:
        """Should return False for disallowed constraint."""
        assert is_constraint_allowed("text", "MIN_VALUE") is False
        assert is_constraint_allowed("number", "PATTERN") is False
        assert is_constraint_allowed("checkbox", "REQUIRED") is False
        assert is_constraint_allowed("date", "ALLOWED_VALUES") is False

    def test_case_insensitive_constraint_type(self) -> None:
        """Constraint type should be case-insensitive."""
        assert is_constraint_allowed("text", "required") is True
        assert is_constraint_allowed("text", "Required") is True
        assert is_constraint_allowed("text", "REQUIRED") is True


class TestHasConstraintsAvailable:
    """Tests for has_constraints_available function."""

    def test_fields_with_constraints(self) -> None:
        """Should return True for fields with available constraints."""
        assert has_constraints_available("text") is True
        assert has_constraints_available("number") is True
        assert has_constraints_available("file") is True
        assert has_constraints_available("dropdown") is True

    def test_fields_without_constraints(self) -> None:
        """Should return False for fields without constraints."""
        assert has_constraints_available("checkbox") is False
        assert has_constraints_available("calculated") is False
        assert has_constraints_available("unknown") is False

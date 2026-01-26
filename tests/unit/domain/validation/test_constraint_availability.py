"""Tests for Domain Constraint Availability Matrix (Authoritative).

These tests verify the constraint availability matrix which is the
SINGLE SOURCE OF TRUTH for which constraints are allowed per field type.
"""

import pytest

from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.validation.constraint_availability import (
    get_allowed_constraint_types,
    is_constraint_allowed_for_field_type,
    is_constraint_class_allowed_for_field_type,
    has_any_constraints_available,
    get_field_types_without_constraints,
    get_constraint_class_from_type_string,
    is_constraint_type_allowed_for_field_type,
    CONSTRAINT_TYPE_MAP,
)
from doc_helper.domain.validation.constraints import (
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


class TestConstraintTypeMap:
    """Tests for CONSTRAINT_TYPE_MAP constant."""

    def test_constraint_type_map_contains_all_constraints(self) -> None:
        """Map should contain all constraint types."""
        assert "REQUIRED" in CONSTRAINT_TYPE_MAP
        assert "MIN_LENGTH" in CONSTRAINT_TYPE_MAP
        assert "MAX_LENGTH" in CONSTRAINT_TYPE_MAP
        assert "MIN_VALUE" in CONSTRAINT_TYPE_MAP
        assert "MAX_VALUE" in CONSTRAINT_TYPE_MAP
        assert "PATTERN" in CONSTRAINT_TYPE_MAP
        assert "ALLOWED_VALUES" in CONSTRAINT_TYPE_MAP
        assert "FILE_EXTENSION" in CONSTRAINT_TYPE_MAP
        assert "MAX_FILE_SIZE" in CONSTRAINT_TYPE_MAP

    def test_constraint_type_map_maps_to_correct_classes(self) -> None:
        """Map should map strings to correct constraint classes."""
        assert CONSTRAINT_TYPE_MAP["REQUIRED"] is RequiredConstraint
        assert CONSTRAINT_TYPE_MAP["MIN_LENGTH"] is MinLengthConstraint
        assert CONSTRAINT_TYPE_MAP["MAX_LENGTH"] is MaxLengthConstraint
        assert CONSTRAINT_TYPE_MAP["MIN_VALUE"] is MinValueConstraint
        assert CONSTRAINT_TYPE_MAP["MAX_VALUE"] is MaxValueConstraint
        assert CONSTRAINT_TYPE_MAP["PATTERN"] is PatternConstraint
        assert CONSTRAINT_TYPE_MAP["ALLOWED_VALUES"] is AllowedValuesConstraint
        assert CONSTRAINT_TYPE_MAP["FILE_EXTENSION"] is FileExtensionConstraint
        assert CONSTRAINT_TYPE_MAP["MAX_FILE_SIZE"] is MaxFileSizeConstraint


class TestGetAllowedConstraintTypes:
    """Tests for get_allowed_constraint_types function."""

    def test_text_field_allowed_constraints(self) -> None:
        """TEXT fields should allow text-related constraints."""
        allowed = get_allowed_constraint_types(FieldType.TEXT)
        assert RequiredConstraint in allowed
        assert MinLengthConstraint in allowed
        assert MaxLengthConstraint in allowed
        assert PatternConstraint in allowed
        assert AllowedValuesConstraint in allowed
        # Should NOT include numeric/file constraints
        assert MinValueConstraint not in allowed
        assert MaxValueConstraint not in allowed
        assert FileExtensionConstraint not in allowed
        assert MaxFileSizeConstraint not in allowed

    def test_textarea_field_allowed_constraints(self) -> None:
        """TEXTAREA fields should allow same constraints as TEXT."""
        allowed = get_allowed_constraint_types(FieldType.TEXTAREA)
        assert RequiredConstraint in allowed
        assert MinLengthConstraint in allowed
        assert MaxLengthConstraint in allowed
        assert PatternConstraint in allowed
        assert AllowedValuesConstraint in allowed

    def test_number_field_allowed_constraints(self) -> None:
        """NUMBER fields should allow numeric constraints."""
        allowed = get_allowed_constraint_types(FieldType.NUMBER)
        assert RequiredConstraint in allowed
        assert MinValueConstraint in allowed
        assert MaxValueConstraint in allowed
        assert AllowedValuesConstraint in allowed
        # Should NOT include text/file constraints
        assert MinLengthConstraint not in allowed
        assert MaxLengthConstraint not in allowed
        assert PatternConstraint not in allowed
        assert FileExtensionConstraint not in allowed

    def test_date_field_allowed_constraints(self) -> None:
        """DATE fields should allow min/max value constraints."""
        allowed = get_allowed_constraint_types(FieldType.DATE)
        assert RequiredConstraint in allowed
        assert MinValueConstraint in allowed
        assert MaxValueConstraint in allowed
        # Should NOT include other constraints
        assert PatternConstraint not in allowed
        assert AllowedValuesConstraint not in allowed
        assert MinLengthConstraint not in allowed

    def test_dropdown_field_allowed_constraints(self) -> None:
        """DROPDOWN fields should allow required and allowed values."""
        allowed = get_allowed_constraint_types(FieldType.DROPDOWN)
        assert RequiredConstraint in allowed
        assert AllowedValuesConstraint in allowed
        assert len(allowed) == 2

    def test_radio_field_allowed_constraints(self) -> None:
        """RADIO fields should allow required and allowed values."""
        allowed = get_allowed_constraint_types(FieldType.RADIO)
        assert RequiredConstraint in allowed
        assert AllowedValuesConstraint in allowed
        assert len(allowed) == 2

    def test_lookup_field_allowed_constraints(self) -> None:
        """LOOKUP fields should allow only required."""
        allowed = get_allowed_constraint_types(FieldType.LOOKUP)
        assert RequiredConstraint in allowed
        assert len(allowed) == 1

    def test_file_field_allowed_constraints(self) -> None:
        """FILE fields should allow file-related constraints."""
        allowed = get_allowed_constraint_types(FieldType.FILE)
        assert RequiredConstraint in allowed
        assert FileExtensionConstraint in allowed
        assert MaxFileSizeConstraint in allowed
        # Should NOT include text/numeric constraints
        assert PatternConstraint not in allowed
        assert MinValueConstraint not in allowed
        assert MinLengthConstraint not in allowed

    def test_image_field_allowed_constraints(self) -> None:
        """IMAGE fields should allow same constraints as FILE."""
        allowed = get_allowed_constraint_types(FieldType.IMAGE)
        assert RequiredConstraint in allowed
        assert FileExtensionConstraint in allowed
        assert MaxFileSizeConstraint in allowed


class TestFieldTypesWithNoConstraints:
    """Tests for field types that NEVER have constraints.

    INVARIANTS:
    - CALCULATED: Values computed by formulas, not user-typed
    - TABLE: Holds child records, not user-typed values
    - CHECKBOX: Boolean true/false is always valid
    """

    def test_calculated_field_no_constraints_invariant(self) -> None:
        """INVARIANT: CALCULATED fields have NO constraints."""
        allowed = get_allowed_constraint_types(FieldType.CALCULATED)
        assert len(allowed) == 0, "CALCULATED fields must have NO constraints"

    def test_table_field_no_constraints_invariant(self) -> None:
        """INVARIANT: TABLE fields have NO constraints."""
        allowed = get_allowed_constraint_types(FieldType.TABLE)
        assert len(allowed) == 0, "TABLE fields must have NO constraints"

    def test_checkbox_field_no_constraints_invariant(self) -> None:
        """INVARIANT: CHECKBOX fields have NO constraints."""
        allowed = get_allowed_constraint_types(FieldType.CHECKBOX)
        assert len(allowed) == 0, "CHECKBOX fields must have NO constraints"

    def test_get_field_types_without_constraints(self) -> None:
        """Should return all field types that cannot have constraints."""
        no_constraint_types = get_field_types_without_constraints()
        assert FieldType.CALCULATED in no_constraint_types
        assert FieldType.TABLE in no_constraint_types
        assert FieldType.CHECKBOX in no_constraint_types
        assert len(no_constraint_types) == 3


class TestIsConstraintAllowedForFieldType:
    """Tests for is_constraint_allowed_for_field_type function."""

    def test_allowed_constraint_returns_true(self) -> None:
        """Should return True for allowed constraint instances."""
        assert is_constraint_allowed_for_field_type(
            FieldType.TEXT, RequiredConstraint()
        )
        assert is_constraint_allowed_for_field_type(
            FieldType.TEXT, MinLengthConstraint(min_length=5)
        )
        assert is_constraint_allowed_for_field_type(
            FieldType.NUMBER, MinValueConstraint(min_value=0)
        )
        assert is_constraint_allowed_for_field_type(
            FieldType.FILE, FileExtensionConstraint(allowed_extensions=(".pdf",))
        )

    def test_disallowed_constraint_returns_false(self) -> None:
        """Should return False for disallowed constraint instances."""
        # Text constraints not allowed on NUMBER
        assert not is_constraint_allowed_for_field_type(
            FieldType.NUMBER, MinLengthConstraint(min_length=5)
        )
        # Numeric constraints not allowed on TEXT
        assert not is_constraint_allowed_for_field_type(
            FieldType.TEXT, MinValueConstraint(min_value=0)
        )
        # File constraints not allowed on TEXT
        assert not is_constraint_allowed_for_field_type(
            FieldType.TEXT, FileExtensionConstraint(allowed_extensions=(".pdf",))
        )

    def test_no_constraints_for_calculated_field(self) -> None:
        """INVARIANT: No constraints allowed for CALCULATED fields."""
        assert not is_constraint_allowed_for_field_type(
            FieldType.CALCULATED, RequiredConstraint()
        )
        assert not is_constraint_allowed_for_field_type(
            FieldType.CALCULATED, MinValueConstraint(min_value=0)
        )

    def test_no_constraints_for_table_field(self) -> None:
        """INVARIANT: No constraints allowed for TABLE fields."""
        assert not is_constraint_allowed_for_field_type(
            FieldType.TABLE, RequiredConstraint()
        )

    def test_no_constraints_for_checkbox_field(self) -> None:
        """INVARIANT: No constraints allowed for CHECKBOX fields."""
        assert not is_constraint_allowed_for_field_type(
            FieldType.CHECKBOX, RequiredConstraint()
        )


class TestIsConstraintClassAllowedForFieldType:
    """Tests for is_constraint_class_allowed_for_field_type function."""

    def test_allowed_class_returns_true(self) -> None:
        """Should return True for allowed constraint classes."""
        assert is_constraint_class_allowed_for_field_type(
            FieldType.TEXT, RequiredConstraint
        )
        assert is_constraint_class_allowed_for_field_type(
            FieldType.NUMBER, MinValueConstraint
        )
        assert is_constraint_class_allowed_for_field_type(
            FieldType.FILE, FileExtensionConstraint
        )

    def test_disallowed_class_returns_false(self) -> None:
        """Should return False for disallowed constraint classes."""
        assert not is_constraint_class_allowed_for_field_type(
            FieldType.NUMBER, MinLengthConstraint
        )
        assert not is_constraint_class_allowed_for_field_type(
            FieldType.TEXT, MinValueConstraint
        )


class TestHasAnyConstraintsAvailable:
    """Tests for has_any_constraints_available function."""

    def test_returns_true_for_fields_with_constraints(self) -> None:
        """Should return True for fields that have available constraints."""
        assert has_any_constraints_available(FieldType.TEXT)
        assert has_any_constraints_available(FieldType.NUMBER)
        assert has_any_constraints_available(FieldType.DATE)
        assert has_any_constraints_available(FieldType.DROPDOWN)
        assert has_any_constraints_available(FieldType.RADIO)
        assert has_any_constraints_available(FieldType.LOOKUP)
        assert has_any_constraints_available(FieldType.FILE)
        assert has_any_constraints_available(FieldType.IMAGE)

    def test_returns_false_for_fields_without_constraints(self) -> None:
        """Should return False for fields that have NO constraints."""
        assert not has_any_constraints_available(FieldType.CALCULATED)
        assert not has_any_constraints_available(FieldType.TABLE)
        assert not has_any_constraints_available(FieldType.CHECKBOX)


class TestGetConstraintClassFromTypeString:
    """Tests for get_constraint_class_from_type_string function."""

    def test_returns_correct_class_for_valid_string(self) -> None:
        """Should return correct class for valid type strings."""
        assert get_constraint_class_from_type_string("REQUIRED") is RequiredConstraint
        assert get_constraint_class_from_type_string("MIN_VALUE") is MinValueConstraint
        assert get_constraint_class_from_type_string("MAX_LENGTH") is MaxLengthConstraint

    def test_case_insensitive(self) -> None:
        """Should be case-insensitive."""
        assert get_constraint_class_from_type_string("required") is RequiredConstraint
        assert get_constraint_class_from_type_string("Required") is RequiredConstraint
        assert get_constraint_class_from_type_string("REQUIRED") is RequiredConstraint

    def test_returns_none_for_unknown_string(self) -> None:
        """Should return None for unknown type strings."""
        assert get_constraint_class_from_type_string("UNKNOWN") is None
        assert get_constraint_class_from_type_string("") is None


class TestIsConstraintTypeAllowedForFieldType:
    """Tests for is_constraint_type_allowed_for_field_type function."""

    def test_allowed_type_string_returns_true(self) -> None:
        """Should return True for allowed constraint type strings."""
        assert is_constraint_type_allowed_for_field_type(FieldType.TEXT, "REQUIRED")
        assert is_constraint_type_allowed_for_field_type(FieldType.TEXT, "MIN_LENGTH")
        assert is_constraint_type_allowed_for_field_type(FieldType.NUMBER, "MIN_VALUE")
        assert is_constraint_type_allowed_for_field_type(FieldType.FILE, "FILE_EXTENSION")

    def test_disallowed_type_string_returns_false(self) -> None:
        """Should return False for disallowed constraint type strings."""
        assert not is_constraint_type_allowed_for_field_type(FieldType.NUMBER, "MIN_LENGTH")
        assert not is_constraint_type_allowed_for_field_type(FieldType.TEXT, "MIN_VALUE")

    def test_unknown_type_string_returns_false(self) -> None:
        """Should return False for unknown type strings."""
        assert not is_constraint_type_allowed_for_field_type(FieldType.TEXT, "UNKNOWN")

    def test_case_insensitive(self) -> None:
        """Should be case-insensitive for type strings."""
        assert is_constraint_type_allowed_for_field_type(FieldType.TEXT, "required")
        assert is_constraint_type_allowed_for_field_type(FieldType.TEXT, "Required")
        assert is_constraint_type_allowed_for_field_type(FieldType.TEXT, "REQUIRED")


class TestArchitecturalRule:
    """Tests for the architectural rule:

    'If a field's value is not directly typed by the user, it must NOT
    accept scalar validation constraints.'
    """

    def test_calculated_fields_reject_all_constraints(self) -> None:
        """CALCULATED fields derive values from formulas - no constraints allowed."""
        for constraint_class in CONSTRAINT_TYPE_MAP.values():
            assert not is_constraint_class_allowed_for_field_type(
                FieldType.CALCULATED, constraint_class
            ), f"CALCULATED should reject {constraint_class.__name__}"

    def test_table_fields_reject_all_constraints(self) -> None:
        """TABLE fields hold child records - no constraints allowed."""
        for constraint_class in CONSTRAINT_TYPE_MAP.values():
            assert not is_constraint_class_allowed_for_field_type(
                FieldType.TABLE, constraint_class
            ), f"TABLE should reject {constraint_class.__name__}"

    def test_checkbox_fields_reject_all_constraints(self) -> None:
        """CHECKBOX (boolean) fields are always valid - no constraints allowed."""
        for constraint_class in CONSTRAINT_TYPE_MAP.values():
            assert not is_constraint_class_allowed_for_field_type(
                FieldType.CHECKBOX, constraint_class
            ), f"CHECKBOX should reject {constraint_class.__name__}"

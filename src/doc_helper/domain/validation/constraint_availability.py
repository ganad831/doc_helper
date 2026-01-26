"""Constraint Availability Matrix (Authoritative).

DOMAIN LAYER - Single Source of Truth.

This module defines which validation constraints are allowed for each field type.
This is the AUTHORITATIVE source - all other layers (Application, Presentation)
MUST derive their constraint availability from this matrix.

SYNCHRONIZATION ENFORCEMENT:
    The Presentation layer has a string-based copy of this matrix
    (presentation/utils/constraint_availability.py) to avoid domain imports.

    SYNCHRONIZATION IS ENFORCED BY TEST:
        tests/unit/test_constraint_availability_sync.py

    If you modify this file, you MUST update the Presentation layer copy.
    The test will FAIL if they diverge.

ARCHITECTURAL RULE (Non-Negotiable):
    If a field's value is not directly typed by the user, it must NOT
    accept scalar validation constraints.

    - CALCULATED fields: Derived from formulas → NO constraints
    - TABLE fields: Hold child records → NO constraints
    - CHECKBOX fields: Boolean true/false → NO constraints (true/false is always valid)
    - LOOKUP fields: Reference another entity → REQUIRED only (presence check)

See: FIELD-TYPE INVARIANT AUDIT for rationale.
"""

from typing import FrozenSet, Type

from doc_helper.domain.schema.field_type import FieldType
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


# =============================================================================
# CONSTRAINT AVAILABILITY MATRIX (AUTHORITATIVE)
# =============================================================================
# Maps FieldType -> Set of allowed constraint classes.
# This is the single source of truth for constraint enforcement.
#
# Rules:
# 1. TEXT/TEXTAREA: Text-based constraints (length, pattern) + required
# 2. NUMBER: Numeric constraints (min/max value) + required
# 3. DATE: Date range constraints (treated as min/max value) + required
# 4. DROPDOWN/RADIO: Selection constraints (allowed values) + required
# 5. CHECKBOX: NO constraints (boolean is always valid)
# 6. CALCULATED: NO constraints (values derived from formulas)
# 7. LOOKUP: REQUIRED only (reference presence check)
# 8. FILE/IMAGE: File constraints (extension, size) + required
# 9. TABLE: NO constraints (holds child records, not user-typed values)
# =============================================================================

_CONSTRAINT_AVAILABILITY: dict[FieldType, FrozenSet[Type[FieldConstraint]]] = {
    FieldType.TEXT: frozenset({
        RequiredConstraint,
        MinLengthConstraint,
        MaxLengthConstraint,
        PatternConstraint,
        AllowedValuesConstraint,
    }),

    FieldType.TEXTAREA: frozenset({
        RequiredConstraint,
        MinLengthConstraint,
        MaxLengthConstraint,
        PatternConstraint,
        AllowedValuesConstraint,
    }),

    FieldType.NUMBER: frozenset({
        RequiredConstraint,
        MinValueConstraint,
        MaxValueConstraint,
        AllowedValuesConstraint,
    }),

    FieldType.DATE: frozenset({
        RequiredConstraint,
        MinValueConstraint,
        MaxValueConstraint,
    }),

    FieldType.DROPDOWN: frozenset({
        RequiredConstraint,
        AllowedValuesConstraint,
    }),

    # CHECKBOX (boolean): NO constraints
    # Rationale: A boolean is always valid (true or false). There's no
    # meaningful validation constraint for a checkbox.
    FieldType.CHECKBOX: frozenset(),

    FieldType.RADIO: frozenset({
        RequiredConstraint,
        AllowedValuesConstraint,
    }),

    # CALCULATED: NO constraints (INVARIANT)
    # Rationale: Calculated fields derive their values from formulas.
    # User does not type values directly. Validation of input is meaningless.
    FieldType.CALCULATED: frozenset(),

    # LOOKUP: REQUIRED only
    # Rationale: Lookup fields reference another entity. The only meaningful
    # constraint is whether a reference is required (presence check).
    FieldType.LOOKUP: frozenset({
        RequiredConstraint,
    }),

    # FILE: File-specific constraints + required
    FieldType.FILE: frozenset({
        RequiredConstraint,
        FileExtensionConstraint,
        MaxFileSizeConstraint,
    }),

    # IMAGE: File-specific constraints + required (same as FILE)
    FieldType.IMAGE: frozenset({
        RequiredConstraint,
        FileExtensionConstraint,
        MaxFileSizeConstraint,
    }),

    # TABLE: NO constraints (INVARIANT)
    # Rationale: TABLE fields hold child records (embedded tables).
    # User does not type a "value" directly. Structural constraints like
    # MIN_ROWS/MAX_ROWS would be different from scalar validation constraints.
    # For v1, TABLE has NO constraints.
    FieldType.TABLE: frozenset(),
}


def get_allowed_constraint_types(field_type: FieldType) -> FrozenSet[Type[FieldConstraint]]:
    """Get the set of allowed constraint classes for a field type.

    Args:
        field_type: FieldType enum value

    Returns:
        FrozenSet of allowed constraint class types.
        Empty set if field type has no constraints.

    Example:
        allowed = get_allowed_constraint_types(FieldType.TEXT)
        # Returns {RequiredConstraint, MinLengthConstraint, MaxLengthConstraint, PatternConstraint, AllowedValuesConstraint}
    """
    return _CONSTRAINT_AVAILABILITY.get(field_type, frozenset())


def is_constraint_allowed_for_field_type(
    field_type: FieldType,
    constraint: FieldConstraint
) -> bool:
    """Check if a constraint instance is allowed for a field type.

    Args:
        field_type: FieldType enum value
        constraint: FieldConstraint instance to check

    Returns:
        True if the constraint type is allowed for this field type.

    Example:
        is_allowed = is_constraint_allowed_for_field_type(
            FieldType.TEXT,
            MinLengthConstraint(min_length=5)
        )
        # Returns True
    """
    allowed = get_allowed_constraint_types(field_type)
    return type(constraint) in allowed


def is_constraint_class_allowed_for_field_type(
    field_type: FieldType,
    constraint_class: Type[FieldConstraint]
) -> bool:
    """Check if a constraint class is allowed for a field type.

    Args:
        field_type: FieldType enum value
        constraint_class: FieldConstraint class to check

    Returns:
        True if the constraint class is allowed for this field type.

    Example:
        is_allowed = is_constraint_class_allowed_for_field_type(
            FieldType.TEXT,
            MinLengthConstraint
        )
        # Returns True
    """
    allowed = get_allowed_constraint_types(field_type)
    return constraint_class in allowed


def has_any_constraints_available(field_type: FieldType) -> bool:
    """Check if a field type has any constraints available.

    Args:
        field_type: FieldType enum value

    Returns:
        True if at least one constraint is available.
        False for CHECKBOX, CALCULATED, TABLE, or unknown types.

    Example:
        has_any_constraints_available(FieldType.TEXT)  # True
        has_any_constraints_available(FieldType.CALCULATED)  # False
    """
    return len(get_allowed_constraint_types(field_type)) > 0


def get_field_types_without_constraints() -> FrozenSet[FieldType]:
    """Get field types that cannot have any constraints.

    Returns:
        FrozenSet of FieldType values that have no allowed constraints.
        Includes: CHECKBOX, CALCULATED, TABLE

    Use this for validation checks that need to reject constraints entirely.
    """
    return frozenset(
        field_type
        for field_type, allowed in _CONSTRAINT_AVAILABILITY.items()
        if len(allowed) == 0
    )


# =============================================================================
# CONSTRAINT TYPE STRING MAPPING
# =============================================================================
# Maps constraint type strings (used by UI/API) to constraint classes.
# This allows translation between string identifiers and domain types.

CONSTRAINT_TYPE_MAP: dict[str, Type[FieldConstraint]] = {
    "REQUIRED": RequiredConstraint,
    "MIN_LENGTH": MinLengthConstraint,
    "MAX_LENGTH": MaxLengthConstraint,
    "MIN_VALUE": MinValueConstraint,
    "MAX_VALUE": MaxValueConstraint,
    "PATTERN": PatternConstraint,
    "ALLOWED_VALUES": AllowedValuesConstraint,
    "FILE_EXTENSION": FileExtensionConstraint,
    "MAX_FILE_SIZE": MaxFileSizeConstraint,
}


def get_constraint_class_from_type_string(type_string: str) -> Type[FieldConstraint] | None:
    """Get constraint class from type string identifier.

    Args:
        type_string: Constraint type string (e.g., "REQUIRED", "MIN_VALUE")

    Returns:
        Constraint class, or None if type string not recognized.
    """
    return CONSTRAINT_TYPE_MAP.get(type_string.upper())


def is_constraint_type_allowed_for_field_type(
    field_type: FieldType,
    constraint_type_string: str
) -> bool:
    """Check if a constraint type string is allowed for a field type.

    This is a convenience function combining string lookup with validation.

    Args:
        field_type: FieldType enum value
        constraint_type_string: Constraint type string (e.g., "REQUIRED", "MIN_VALUE")

    Returns:
        True if the constraint type is allowed for this field type.
        False if constraint type is unknown or not allowed.
    """
    constraint_class = get_constraint_class_from_type_string(constraint_type_string)
    if constraint_class is None:
        return False
    return is_constraint_class_allowed_for_field_type(field_type, constraint_class)

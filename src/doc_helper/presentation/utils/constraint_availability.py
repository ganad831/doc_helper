"""Constraint Availability Engine (Phase SD-6).

Presentation layer utility for constraint availability in UI.

ARCHITECTURAL SYNCHRONIZATION REQUIREMENT:
    This module MUST remain synchronized with the authoritative Domain layer:
    domain/validation/constraint_availability.py

    The Domain layer uses FieldType enums and FieldConstraint classes.
    This Presentation layer uses strings (to avoid domain imports).

    SYNCHRONIZATION IS ENFORCED BY TEST:
        tests/unit/test_constraint_availability_sync.py

    If you modify this file, you MUST verify the test still passes.
    If you modify the Domain constraint matrix, you MUST update this file.

NOTE: This is a Presentation layer utility.
- Uses string-based field types and constraint types
- NO domain imports (architectural boundary)
- Used by AddConstraintDialog to filter available constraints
"""

from typing import FrozenSet


# Constraint types supported by SchemaUseCases.add_constraint()
# These are the string identifiers passed to the use-case
CONSTRAINT_TYPES = frozenset({
    "REQUIRED",
    "MIN_VALUE",
    "MAX_VALUE",
    "MIN_LENGTH",
    "MAX_LENGTH",
    "PATTERN",
    "ALLOWED_VALUES",
    "FILE_EXTENSION",
    "MAX_FILE_SIZE",
})

# Field type -> allowed constraint types mapping
# Based on Phase SD-6 requirements
_CONSTRAINT_AVAILABILITY: dict[str, FrozenSet[str]] = {
    # TEXT fields: Required, MinLength, MaxLength, Pattern, AllowedValues
    "text": frozenset({
        "REQUIRED",
        "MIN_LENGTH",
        "MAX_LENGTH",
        "PATTERN",
        "ALLOWED_VALUES",
    }),

    # TEXTAREA fields: Same as TEXT
    "textarea": frozenset({
        "REQUIRED",
        "MIN_LENGTH",
        "MAX_LENGTH",
        "PATTERN",
        "ALLOWED_VALUES",
    }),

    # NUMBER fields: Required, MinValue, MaxValue, AllowedValues
    "number": frozenset({
        "REQUIRED",
        "MIN_VALUE",
        "MAX_VALUE",
        "ALLOWED_VALUES",
    }),

    # DATE fields: Required, MinValue (date), MaxValue (date)
    "date": frozenset({
        "REQUIRED",
        "MIN_VALUE",
        "MAX_VALUE",
    }),

    # DROPDOWN fields: Required, AllowedValues
    "dropdown": frozenset({
        "REQUIRED",
        "ALLOWED_VALUES",
    }),

    # CHECKBOX (BOOLEAN) fields: NO constraints allowed
    "checkbox": frozenset(),

    # RADIO fields: Required, AllowedValues
    "radio": frozenset({
        "REQUIRED",
        "ALLOWED_VALUES",
    }),

    # CALCULATED fields: Read-only computed values - no constraints
    "calculated": frozenset(),

    # LOOKUP fields: Required only
    "lookup": frozenset({
        "REQUIRED",
    }),

    # FILE fields: Required, FileExtension, MaxFileSize
    "file": frozenset({
        "REQUIRED",
        "FILE_EXTENSION",
        "MAX_FILE_SIZE",
    }),

    # IMAGE fields: Required, FileExtension, MaxFileSize
    "image": frozenset({
        "REQUIRED",
        "FILE_EXTENSION",
        "MAX_FILE_SIZE",
    }),

    # TABLE fields: NO constraints (holds child records, not user-typed values)
    # Synced with Domain: domain/validation/constraint_availability.py
    "table": frozenset(),
}


def get_allowed_constraints(field_type: str) -> FrozenSet[str]:
    """Get the set of allowed constraint types for a field type.

    Args:
        field_type: Field type string (e.g., "text", "number", "file")

    Returns:
        FrozenSet of allowed constraint type strings.
        Empty set if field type not recognized or has no constraints.
    """
    return _CONSTRAINT_AVAILABILITY.get(field_type.lower(), frozenset())


def is_constraint_allowed(field_type: str, constraint_type: str) -> bool:
    """Check if a constraint type is allowed for a field type.

    Args:
        field_type: Field type string (e.g., "text", "number", "file")
        constraint_type: Constraint type string (e.g., "REQUIRED", "PATTERN")

    Returns:
        True if the constraint is allowed for this field type.
    """
    allowed = get_allowed_constraints(field_type)
    return constraint_type.upper() in allowed


def has_constraints_available(field_type: str) -> bool:
    """Check if a field type has any constraints available.

    Args:
        field_type: Field type string

    Returns:
        True if at least one constraint is available.
        False for CHECKBOX, CALCULATED, or unknown types.
    """
    return len(get_allowed_constraints(field_type)) > 0

"""LOOKUP display field validation (Pure Domain Logic).

This module provides pure validation functions for LOOKUP field display fields.
No repositories, DTOs, persistence, or UI dependencies.

AUTHORITATIVE INVARIANTS (Non-negotiable):
1. lookup_display_field must reference an existing field in lookup_entity_id
2. Must NOT reference: CALCULATED, TABLE, FILE, IMAGE field types
3. Must be a user-readable scalar field
4. NULL is explicitly allowed (means "no display field")

See: STRICT MODE CORRECTIVE PATCH - LOOKUP Display Field Validity
"""

from dataclasses import dataclass
from typing import Mapping, Optional

from doc_helper.domain.schema.field_type import FieldType


# Field types that CANNOT be used as lookup display fields
# These are either computed, non-scalar, or not user-readable in a dropdown context
INVALID_DISPLAY_FIELD_TYPES: frozenset[FieldType] = frozenset({
    FieldType.CALCULATED,  # Computed values, not stable for display
    FieldType.TABLE,       # Nested collection, not a scalar
    FieldType.FILE,        # Binary data, not displayable as text
    FieldType.IMAGE,       # Binary data, not displayable as text
})

# Field types that CAN be used as lookup display fields
# These are user-readable scalar values suitable for dropdown display
VALID_DISPLAY_FIELD_TYPES: frozenset[FieldType] = frozenset({
    FieldType.TEXT,
    FieldType.TEXTAREA,
    FieldType.NUMBER,
    FieldType.DATE,
    FieldType.DROPDOWN,
    FieldType.CHECKBOX,
    FieldType.RADIO,
    FieldType.LOOKUP,  # Can reference another lookup's display value
})


@dataclass(frozen=True)
class LookupDisplayFieldValidationResult:
    """Result of lookup display field validation.

    Immutable value object following domain patterns.
    """
    is_valid: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    @classmethod
    def valid(cls) -> "LookupDisplayFieldValidationResult":
        """Create a valid result."""
        return cls(is_valid=True)

    @classmethod
    def invalid(cls, error_code: str, error_message: str) -> "LookupDisplayFieldValidationResult":
        """Create an invalid result with error details."""
        return cls(is_valid=False, error_code=error_code, error_message=error_message)


def validate_lookup_display_field(
    lookup_display_field: Optional[str],
    available_fields: Mapping[str, FieldType],
) -> LookupDisplayFieldValidationResult:
    """Validate that a lookup_display_field is valid for a LOOKUP field.

    PURE FUNCTION - No side effects, no external dependencies.

    Args:
        lookup_display_field: The field ID to validate (None is allowed)
        available_fields: Mapping of field_id -> FieldType for the lookup entity

    Returns:
        LookupDisplayFieldValidationResult indicating validity

    Invariants:
        - NULL is explicitly allowed (no display field selected)
        - Field must exist in available_fields
        - Field type must NOT be in INVALID_DISPLAY_FIELD_TYPES
    """
    # INVARIANT: NULL is explicitly allowed
    if lookup_display_field is None:
        return LookupDisplayFieldValidationResult.valid()

    # Empty string treated as None (valid)
    if lookup_display_field.strip() == "":
        return LookupDisplayFieldValidationResult.valid()

    # INVARIANT: Field must exist in the lookup entity
    if lookup_display_field not in available_fields:
        return LookupDisplayFieldValidationResult.invalid(
            error_code="FIELD_NOT_FOUND",
            error_message=f"lookup_display_field '{lookup_display_field}' does not exist in the lookup entity"
        )

    # Get the field type
    field_type = available_fields[lookup_display_field]

    # INVARIANT: Field type must NOT be CALCULATED, TABLE, FILE, or IMAGE
    if field_type in INVALID_DISPLAY_FIELD_TYPES:
        return LookupDisplayFieldValidationResult.invalid(
            error_code="INVALID_FIELD_TYPE",
            error_message=(
                f"lookup_display_field '{lookup_display_field}' has type {field_type.value} "
                f"which cannot be used as a display field. "
                f"Valid types: TEXT, TEXTAREA, NUMBER, DATE, DROPDOWN, RADIO, CHECKBOX, LOOKUP"
            )
        )

    # All checks passed
    return LookupDisplayFieldValidationResult.valid()


def is_valid_display_field_type(field_type: FieldType) -> bool:
    """Check if a field type can be used as a lookup display field.

    PURE FUNCTION - Simple type check utility.

    Args:
        field_type: The FieldType to check

    Returns:
        True if the field type is valid for display, False otherwise
    """
    return field_type not in INVALID_DISPLAY_FIELD_TYPES


def get_valid_display_fields(
    available_fields: Mapping[str, FieldType]
) -> dict[str, FieldType]:
    """Filter a mapping to only include fields valid for lookup display.

    PURE FUNCTION - Returns new dict, no mutation.

    Args:
        available_fields: Mapping of field_id -> FieldType

    Returns:
        New dict containing only fields with valid display types
    """
    return {
        field_id: field_type
        for field_id, field_type in available_fields.items()
        if is_valid_display_field_type(field_type)
    }

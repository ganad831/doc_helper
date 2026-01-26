"""Field type utilities for presentation layer.

PC-1: Normalize field type helper.
"""

from doc_helper.domain.schema.field_type import FieldType


def normalize_field_type(field_type: str) -> str:
    """Normalize field type string to canonical form (lowercase).

    Uses FieldType enum to ensure valid field type values.
    Returns the FieldType.value (lowercase) for consistent comparison.

    Args:
        field_type: Field type string (any case)

    Returns:
        Normalized field type string (lowercase)

    Raises:
        ValueError: If field_type is not a valid FieldType

    Example:
        >>> normalize_field_type("LOOKUP")
        'lookup'
        >>> normalize_field_type("Calculated")
        'calculated'
    """
    return FieldType.from_string(field_type).value

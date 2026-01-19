"""Field types for schema definition.

FieldType enum defines the 12 supported field types (FROZEN for v1).
"""

from enum import Enum


class FieldType(str, Enum):
    """Supported field types (v1: FROZEN list of 12 types).

    v1 Scope (FROZEN):
    1. TEXT - Single-line text input
    2. TEXTAREA - Multi-line text input
    3. NUMBER - Numeric input with optional decimals
    4. DATE - Date picker
    5. DROPDOWN - Single selection from options
    6. CHECKBOX - Boolean true/false
    7. RADIO - Single selection (radio buttons)
    8. CALCULATED - Formula-driven read-only value
    9. LOOKUP - Value from another entity/record
    10. FILE - File attachment reference
    11. IMAGE - Image attachment with preview
    12. TABLE - Nested tabular data (child records)

    v2+ may add more types, but these 12 are FROZEN for v1.

    RULES (IMPLEMENTATION_RULES.md Section 3):
    - Field types are immutable
    - NO new types in v1 (list is frozen)
    - Each type maps to a specific validator and widget
    """

    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    DATE = "date"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    CALCULATED = "calculated"
    LOOKUP = "lookup"
    FILE = "file"
    IMAGE = "image"
    TABLE = "table"

    @property
    def display_name(self) -> str:
        """Get human-readable display name for this field type.

        Returns:
            Display name (e.g., "Text", "Text Area", "Number")
        """
        return {
            FieldType.TEXT: "Text",
            FieldType.TEXTAREA: "Text Area",
            FieldType.NUMBER: "Number",
            FieldType.DATE: "Date",
            FieldType.DROPDOWN: "Dropdown",
            FieldType.CHECKBOX: "Checkbox",
            FieldType.RADIO: "Radio Button",
            FieldType.CALCULATED: "Calculated",
            FieldType.LOOKUP: "Lookup",
            FieldType.FILE: "File",
            FieldType.IMAGE: "Image",
            FieldType.TABLE: "Table",
        }[self]

    @property
    def supports_constraints(self) -> bool:
        """Check if this field type supports validation constraints.

        Returns:
            True if constraints can be applied to this type
        """
        # Calculated fields are read-only and don't need constraints
        return self != FieldType.CALCULATED

    @property
    def is_numeric(self) -> bool:
        """Check if this field type stores numeric values.

        Returns:
            True if field stores numbers
        """
        return self == FieldType.NUMBER

    @property
    def is_text(self) -> bool:
        """Check if this field type stores text values.

        Returns:
            True if field stores text
        """
        return self in (FieldType.TEXT, FieldType.TEXTAREA)

    @property
    def is_date(self) -> bool:
        """Check if this field type stores date values.

        Returns:
            True if field stores dates
        """
        return self == FieldType.DATE

    @property
    def is_choice(self) -> bool:
        """Check if this field type requires predefined options.

        Returns:
            True if field requires options (dropdown, radio)
        """
        return self in (FieldType.DROPDOWN, FieldType.RADIO)

    @property
    def is_file(self) -> bool:
        """Check if this field type stores file references.

        Returns:
            True if field stores files
        """
        return self in (FieldType.FILE, FieldType.IMAGE)

    @property
    def is_collection(self) -> bool:
        """Check if this field type stores multiple values.

        Returns:
            True if field stores collections (table)
        """
        return self == FieldType.TABLE

    @staticmethod
    def from_string(value: str) -> "FieldType":
        """Get FieldType from string value.

        Args:
            value: String value (e.g., "text", "number")

        Returns:
            FieldType enum value

        Raises:
            ValueError: If value is not a valid field type
        """
        try:
            return FieldType(value.lower())
        except ValueError:
            valid_types = [ft.value for ft in FieldType]
            raise ValueError(
                f"Invalid field type: {value}. "
                f"Valid types: {valid_types}"
            )

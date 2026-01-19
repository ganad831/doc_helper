"""Field value for storing field data in projects."""

from dataclasses import dataclass
from typing import Any, Optional

from doc_helper.domain.common.value_object import ValueObject
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


@dataclass(frozen=True)
class FieldValue(ValueObject):
    """Value object representing a field's value in a project.

    FieldValue stores the actual data for a field, along with metadata
    about whether the value is computed (from formula) or user-provided.

    RULES:
    - FieldValue is immutable (frozen dataclass)
    - Supports both computed and user-provided values
    - Can track if value is overridden (user value replaces computed)
    - Value can be any type (string, number, bool, None, etc.)

    Example:
        # User-provided value
        value1 = FieldValue(
            field_id=FieldDefinitionId("site_location"),
            value="123 Main Street",
            is_computed=False
        )

        # Computed value from formula
        value2 = FieldValue(
            field_id=FieldDefinitionId("total_cost"),
            value=15000.50,
            is_computed=True,
            computed_from="labor_cost + material_cost"
        )

        # Overridden value (user replaced computed value)
        value3 = FieldValue(
            field_id=FieldDefinitionId("adjusted_total"),
            value=16000.00,
            is_computed=False,
            is_override=True,
            original_computed_value=15800.00
        )
    """

    field_id: FieldDefinitionId
    value: Any  # Field value (can be any type)
    is_computed: bool = False  # True if value came from formula evaluation
    computed_from: Optional[str] = None  # Formula that computed this value (if computed)
    is_override: bool = False  # True if user overrode a computed value
    original_computed_value: Any = None  # Original computed value before override

    def __post_init__(self) -> None:
        """Validate field value."""
        if not isinstance(self.field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")
        if not isinstance(self.is_computed, bool):
            raise TypeError("is_computed must be a bool")
        if not isinstance(self.is_override, bool):
            raise TypeError("is_override must be a bool")

        # Validation: computed_from should be set if is_computed is True
        if self.is_computed and self.computed_from is not None:
            if not isinstance(self.computed_from, str):
                raise TypeError("computed_from must be a string or None")

        # Validation: original_computed_value should be set if is_override is True
        if self.is_override and not self.is_computed:
            # Override only makes sense for computed values
            if self.original_computed_value is None:
                raise ValueError(
                    "original_computed_value must be set when is_override is True"
                )

    @property
    def is_user_provided(self) -> bool:
        """Check if value was provided by user (not computed).

        Returns:
            True if value is user-provided
        """
        return not self.is_computed

    @property
    def has_override(self) -> bool:
        """Check if this value overrides a computed value.

        Returns:
            True if this is an override
        """
        return self.is_override

    def with_value(self, new_value: Any) -> "FieldValue":
        """Create new FieldValue with updated value.

        If this was a computed value, the new value becomes an override.

        Args:
            new_value: New value to set

        Returns:
            New FieldValue with updated value
        """
        if self.is_computed:
            # User is overriding a computed value
            return FieldValue(
                field_id=self.field_id,
                value=new_value,
                is_computed=False,
                computed_from=None,
                is_override=True,
                original_computed_value=self.value,
            )
        else:
            # Simple value update
            return FieldValue(
                field_id=self.field_id,
                value=new_value,
                is_computed=False,
                computed_from=None,
                is_override=self.is_override,
                original_computed_value=self.original_computed_value,
            )

    def with_computed_value(self, computed_value: Any, formula: str) -> "FieldValue":
        """Create new FieldValue with computed value.

        If there's an existing override, it's preserved.

        Args:
            computed_value: Computed value from formula
            formula: Formula that computed the value

        Returns:
            New FieldValue with computed value
        """
        if self.is_override:
            # Preserve the override, but update original computed value
            return FieldValue(
                field_id=self.field_id,
                value=self.value,  # Keep overridden value
                is_computed=False,
                computed_from=None,
                is_override=True,
                original_computed_value=computed_value,
            )
        else:
            # Replace with computed value
            return FieldValue(
                field_id=self.field_id,
                value=computed_value,
                is_computed=True,
                computed_from=formula,
                is_override=False,
                original_computed_value=None,
            )

    def clear_override(self) -> "FieldValue":
        """Create new FieldValue with override cleared.

        Restores the original computed value if there was one.

        Returns:
            New FieldValue without override

        Raises:
            ValueError: If this is not an override
        """
        if not self.is_override:
            raise ValueError("Cannot clear override - this value is not an override")

        # Restore original computed value
        return FieldValue(
            field_id=self.field_id,
            value=self.original_computed_value,
            is_computed=True,
            computed_from=None,  # Formula info lost
            is_override=False,
            original_computed_value=None,
        )

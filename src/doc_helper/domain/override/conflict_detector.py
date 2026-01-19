"""Conflict detection for overrides.

Detects conflicts between user overrides and computed/controlled values.
"""

from dataclasses import dataclass
from typing import Any, Optional

from doc_helper.domain.schema.schema_ids import FieldDefinitionId


@dataclass(frozen=True)
class ConflictInfo:
    """Information about a detected conflict.

    A conflict occurs when:
    - User override differs from computed formula value
    - User override differs from control-set value
    - Both formula and control try to set the same field
    """

    field_id: FieldDefinitionId
    conflict_type: str  # "formula", "control", "formula_control"
    override_value: Any
    computed_value: Optional[Any] = None  # For formula conflicts
    control_value: Optional[Any] = None  # For control conflicts
    description: Optional[str] = None  # Human-readable conflict description

    def __post_init__(self) -> None:
        """Validate conflict info."""
        if not isinstance(self.field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")
        if not isinstance(self.conflict_type, str):
            raise TypeError("conflict_type must be a string")
        if not self.conflict_type:
            raise ValueError("conflict_type cannot be empty")
        if self.description is not None and not isinstance(self.description, str):
            raise TypeError("description must be a string or None")

    @property
    def is_formula_conflict(self) -> bool:
        """Check if this is a formula conflict.

        Returns:
            True if conflict involves formula computation
        """
        return self.conflict_type in ("formula", "formula_control")

    @property
    def is_control_conflict(self) -> bool:
        """Check if this is a control conflict.

        Returns:
            True if conflict involves control rule
        """
        return self.conflict_type in ("control", "formula_control")

    @property
    def is_dual_conflict(self) -> bool:
        """Check if this is a dual conflict (formula and control).

        Returns:
            True if both formula and control try to set the field
        """
        return self.conflict_type == "formula_control"


class ConflictDetector:
    """Detects conflicts between overrides and computed/controlled values.

    The ConflictDetector identifies situations where:
    1. User override differs from formula-computed value
    2. User override differs from control-set value
    3. Both formula and control try to set the same field

    Example:
        detector = ConflictDetector()

        # Detect formula conflict
        conflict = detector.detect_formula_conflict(
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            computed_value=1500
        )
        if conflict:
            print(f"Formula conflict: {conflict.description}")

        # Detect control conflict
        conflict = detector.detect_control_conflict(
            field_id=FieldDefinitionId("status"),
            override_value="active",
            control_value="disabled"
        )

        # Detect dual conflict
        conflict = detector.detect_dual_conflict(
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            computed_value=1500,
            control_value=1550
        )
    """

    def detect_formula_conflict(
        self,
        field_id: FieldDefinitionId,
        override_value: Any,
        computed_value: Any,
    ) -> Optional[ConflictInfo]:
        """Detect conflict between override and formula-computed value.

        Args:
            field_id: Field ID
            override_value: User override value
            computed_value: Formula-computed value

        Returns:
            ConflictInfo if conflict detected, None otherwise
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")

        # Conflict if values differ (type-aware comparison)
        if not self.check_values_match(override_value, computed_value):
            return ConflictInfo(
                field_id=field_id,
                conflict_type="formula",
                override_value=override_value,
                computed_value=computed_value,
                description=f"Override value {override_value} differs from "
                f"formula-computed value {computed_value}",
            )
        return None

    def detect_control_conflict(
        self,
        field_id: FieldDefinitionId,
        override_value: Any,
        control_value: Any,
    ) -> Optional[ConflictInfo]:
        """Detect conflict between override and control-set value.

        Args:
            field_id: Field ID
            override_value: User override value
            control_value: Control-set value

        Returns:
            ConflictInfo if conflict detected, None otherwise
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")

        # Conflict if values differ (type-aware comparison)
        if not self.check_values_match(override_value, control_value):
            return ConflictInfo(
                field_id=field_id,
                conflict_type="control",
                override_value=override_value,
                control_value=control_value,
                description=f"Override value {override_value} differs from "
                f"control-set value {control_value}",
            )
        return None

    def detect_dual_conflict(
        self,
        field_id: FieldDefinitionId,
        override_value: Any,
        computed_value: Any,
        control_value: Any,
    ) -> Optional[ConflictInfo]:
        """Detect conflict when both formula and control try to set field.

        This is a special case where:
        1. Formula computes a value
        2. Control rule sets a value
        3. User overrides with a third value

        Args:
            field_id: Field ID
            override_value: User override value
            computed_value: Formula-computed value
            control_value: Control-set value

        Returns:
            ConflictInfo if conflict detected, None otherwise
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")

        # Dual conflict if override differs from both (type-aware comparison)
        if (
            not self.check_values_match(override_value, computed_value)
            and not self.check_values_match(override_value, control_value)
        ):
            return ConflictInfo(
                field_id=field_id,
                conflict_type="formula_control",
                override_value=override_value,
                computed_value=computed_value,
                control_value=control_value,
                description=f"Override value {override_value} differs from both "
                f"formula-computed value {computed_value} and "
                f"control-set value {control_value}",
            )
        return None

    def check_values_match(self, value1: Any, value2: Any) -> bool:
        """Check if two values match (strict type-aware comparison).

        Uses both value and type comparison to avoid Python's type coercion
        (e.g., 0 == False, 1 == True, "1" == 1).

        Args:
            value1: First value
            value2: Second value

        Returns:
            True if values match with same type
        """
        # Check both value and type to avoid coercion
        return value1 == value2 and type(value1) == type(value2)

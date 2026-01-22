"""Schema Compatibility types (Phase 3).

Types for representing compatibility between schema versions.

APPROVED DECISIONS:
- Decision 6: Three-level compatibility (IDENTICAL / COMPATIBLE / INCOMPATIBLE)
- Compatibility is informational only (does not block operations)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from doc_helper.domain.common.value_object import ValueObject
from doc_helper.domain.schema.schema_change import SchemaChange
from doc_helper.domain.schema.schema_version import SchemaVersion


class CompatibilityLevel(str, Enum):
    """Compatibility level between two schema versions.

    Three-level classification (Decision 6):
    - IDENTICAL: No changes detected
    - COMPATIBLE: Non-breaking changes only
    - INCOMPATIBLE: At least one breaking change

    IMPORTANT: This is informational only and MUST NOT block operations.
    """

    IDENTICAL = "identical"
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"

    @property
    def display_name(self) -> str:
        """Get human-readable display name.

        Returns:
            Display name for UI
        """
        return {
            CompatibilityLevel.IDENTICAL: "Identical",
            CompatibilityLevel.COMPATIBLE: "Compatible",
            CompatibilityLevel.INCOMPATIBLE: "Incompatible",
        }[self]

    @property
    def description(self) -> str:
        """Get description of what this level means.

        Returns:
            Description string
        """
        return {
            CompatibilityLevel.IDENTICAL: "No changes detected between versions",
            CompatibilityLevel.COMPATIBLE: "Non-breaking changes only; existing data remains valid",
            CompatibilityLevel.INCOMPATIBLE: "Breaking changes detected; existing data may be affected",
        }[self]


@dataclass(frozen=True)
class CompatibilityResult(ValueObject):
    """Result of comparing two schema versions for compatibility.

    Contains:
    - Compatibility level classification
    - List of all detected changes
    - Summary statistics

    IMPORTANT: This is informational only and MUST NOT block operations.

    Examples:
        # Identical schemas
        result = CompatibilityResult(
            level=CompatibilityLevel.IDENTICAL,
            changes=(),
        )

        # Compatible with changes
        result = CompatibilityResult(
            level=CompatibilityLevel.COMPATIBLE,
            changes=(
                SchemaChange(ChangeType.FIELD_ADDED, "project", "new_field"),
            ),
        )
    """

    level: CompatibilityLevel
    changes: tuple  # Tuple of SchemaChange
    source_version: Optional[SchemaVersion] = None
    target_version: Optional[SchemaVersion] = None

    @property
    def is_identical(self) -> bool:
        """Check if schemas are identical.

        Returns:
            True if no changes detected
        """
        return self.level == CompatibilityLevel.IDENTICAL

    @property
    def is_compatible(self) -> bool:
        """Check if schemas are compatible (identical or non-breaking changes only).

        Returns:
            True if compatible or identical
        """
        return self.level in (CompatibilityLevel.IDENTICAL, CompatibilityLevel.COMPATIBLE)

    @property
    def is_incompatible(self) -> bool:
        """Check if schemas are incompatible (has breaking changes).

        Returns:
            True if has breaking changes
        """
        return self.level == CompatibilityLevel.INCOMPATIBLE

    @property
    def total_changes(self) -> int:
        """Get total number of changes.

        Returns:
            Count of all changes
        """
        return len(self.changes)

    @property
    def breaking_changes(self) -> tuple:
        """Get only the breaking changes.

        Returns:
            Tuple of breaking SchemaChange instances
        """
        return tuple(c for c in self.changes if c.is_breaking)

    @property
    def breaking_change_count(self) -> int:
        """Get count of breaking changes.

        Returns:
            Number of breaking changes
        """
        return len(self.breaking_changes)

    @property
    def non_breaking_changes(self) -> tuple:
        """Get only the non-breaking changes.

        Returns:
            Tuple of non-breaking SchemaChange instances
        """
        return tuple(c for c in self.changes if not c.is_breaking)

    @property
    def non_breaking_change_count(self) -> int:
        """Get count of non-breaking changes.

        Returns:
            Number of non-breaking changes
        """
        return len(self.non_breaking_changes)

    @property
    def summary(self) -> str:
        """Get human-readable summary of the comparison.

        Returns:
            Summary string
        """
        if self.is_identical:
            return "Schemas are identical"

        parts = []
        if self.breaking_change_count > 0:
            parts.append(f"{self.breaking_change_count} breaking change(s)")
        if self.non_breaking_change_count > 0:
            parts.append(f"{self.non_breaking_change_count} non-breaking change(s)")

        changes_str = ", ".join(parts)
        return f"{self.level.display_name}: {changes_str}"

    def get_changes_by_entity(self) -> dict:
        """Group changes by entity ID.

        Returns:
            Dict mapping entity_id to list of changes
        """
        result: dict = {}
        for change in self.changes:
            if change.entity_id not in result:
                result[change.entity_id] = []
            result[change.entity_id].append(change)
        return result

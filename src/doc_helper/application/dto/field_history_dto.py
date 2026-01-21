"""Field History DTOs for UI display.

ADR-027: Field History Storage
RULES (AGENT_RULES.md Section 3-4, ADR-020):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class FieldHistoryEntryDTO:
    """UI-facing field history entry for display.

    ADR-027: Field History Storage
    - Represents a single field value change for UI consumption
    - Contains only display-relevant data with primitive types
    - Timestamp as ISO string for easy parsing in UI

    FORBIDDEN in this DTO:
    - Domain entities (FieldHistoryEntry, Project)
    - Domain value objects (UUID, ChangeSource enum)
    - Domain types of any kind
    """

    history_id: str  # UUID as string
    project_id: str  # Project ID as string
    field_id: str  # Field ID as string
    previous_value: Any  # Value before change (primitive type)
    new_value: Any  # Value after change (primitive type)
    change_source: str  # "USER_EDIT", "FORMULA_RECOMPUTATION", etc.
    user_id: Optional[str]  # User ID as string (if applicable)
    timestamp: str  # ISO timestamp string (e.g., "2024-01-15T10:30:00")

    def is_user_initiated(self) -> bool:
        """Check if change was initiated by user.

        Returns:
            True if change source is USER_EDIT, UNDO_OPERATION, or REDO_OPERATION
        """
        return self.change_source in (
            "USER_EDIT",
            "UNDO_OPERATION",
            "REDO_OPERATION",
        )

    def is_system_initiated(self) -> bool:
        """Check if change was initiated by system.

        Returns:
            True if change source is formula, override, or control
        """
        return self.change_source in (
            "FORMULA_RECOMPUTATION",
            "OVERRIDE_ACCEPTANCE",
            "CONTROL_EFFECT",
        )


@dataclass(frozen=True)
class FieldHistoryResultDTO:
    """Result of a field history query with pagination metadata.

    ADR-027: Field History Storage
    - Includes pagination metadata for large result sets
    - Total count helps UI display "Showing X of Y" messages
    """

    entries: tuple[FieldHistoryEntryDTO, ...]  # History entries
    total_count: int  # Total number of entries (before pagination)
    offset: int  # Number of entries skipped
    limit: Optional[int]  # Maximum entries returned (None = all)

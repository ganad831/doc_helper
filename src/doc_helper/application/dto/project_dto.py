"""Project DTOs for UI display.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProjectDTO:
    """UI-facing project data for display.

    This DTO represents a project for UI consumption. It contains
    only display-relevant data with primitive types.

    FORBIDDEN in this DTO:
    - Domain entities (Project, FieldValue)
    - Domain value objects (ProjectId, EntityDefinitionId)
    - Previous values for undo
    - Internal state for restoration
    """

    id: str  # Project ID as string (from ProjectId.value)
    name: str  # Project name (user-visible)
    description: Optional[str]  # Optional project description
    file_path: Optional[str]  # File path where project is saved
    entity_definition_id: str  # Schema definition ID as string
    field_count: int  # Number of field values
    is_saved: bool  # Whether project has been saved


@dataclass(frozen=True)
class ProjectSummaryDTO:
    """Minimal project data for lists and recent projects.

    Used in welcome screen, recent projects list, etc.
    Contains only essential display information.
    """

    id: str  # Project ID as string
    name: str  # Project name
    file_path: Optional[str]  # File path (for display)
    is_saved: bool  # Whether project has been saved

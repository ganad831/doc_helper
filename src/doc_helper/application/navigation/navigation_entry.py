"""Navigation entry value object.

Represents a single location in the application navigation hierarchy.
Immutable value object for navigation history tracking.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NavigationEntry:
    """A single entry in the navigation history.

    Represents a specific location in the app (entity/tab, group, field).

    Attributes:
        entity_id: Entity/tab identifier (required)
        group_id: Group identifier within entity (optional)
        field_id: Field identifier within group (optional)

    Example:
        # Navigate to entity
        entry = NavigationEntry(entity_id="project_info")

        # Navigate to group within entity
        entry = NavigationEntry(entity_id="borehole", group_id="location")

        # Navigate to specific field
        entry = NavigationEntry(
            entity_id="borehole",
            group_id="location",
            field_id="depth"
        )
    """

    entity_id: str
    group_id: Optional[str] = None
    field_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate navigation entry."""
        if not self.entity_id:
            raise ValueError("entity_id cannot be empty")

    def is_same_entity(self, other: "NavigationEntry") -> bool:
        """Check if this entry is in the same entity as another."""
        return self.entity_id == other.entity_id

    def is_same_group(self, other: "NavigationEntry") -> bool:
        """Check if this entry is in the same group as another."""
        return (
            self.entity_id == other.entity_id
            and self.group_id == other.group_id
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary for persistence.

        Returns:
            Dictionary with entity_id, group_id, field_id
        """
        return {
            "entity_id": self.entity_id,
            "group_id": self.group_id,
            "field_id": self.field_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NavigationEntry":
        """Deserialize from dictionary.

        Args:
            data: Dictionary with entity_id, group_id, field_id

        Returns:
            NavigationEntry instance
        """
        return cls(
            entity_id=data["entity_id"],
            group_id=data.get("group_id"),
            field_id=data.get("field_id"),
        )

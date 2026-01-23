"""Schema Change detection types (Phase 3).

Types for representing changes between schema versions.

APPROVED DECISIONS:
- Decision 2: No rename detection (rename = delete + add)
- Decision 3: Moderate breaking-change policy
- Decision 7: Structural comparison only
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from doc_helper.domain.common.value_object import ValueObject


class ChangeType(str, Enum):
    """Type of change detected between schema versions.

    Categories:
    - ADDED: New element introduced
    - REMOVED: Existing element deleted
    - MODIFIED: Element properties changed
    """

    # Entity-level changes
    ENTITY_ADDED = "entity_added"
    ENTITY_REMOVED = "entity_removed"

    # Field-level changes
    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_TYPE_CHANGED = "field_type_changed"
    FIELD_REQUIRED_CHANGED = "field_required_changed"

    # Constraint changes
    CONSTRAINT_ADDED = "constraint_added"
    CONSTRAINT_REMOVED = "constraint_removed"
    CONSTRAINT_MODIFIED = "constraint_modified"

    # Option changes (for choice fields)
    OPTION_ADDED = "option_added"
    OPTION_REMOVED = "option_removed"

    # Relationship changes (Phase 6A)
    RELATIONSHIP_ADDED = "relationship_added"
    RELATIONSHIP_REMOVED = "relationship_removed"

    @property
    def is_breaking(self) -> bool:
        """Check if this change type is breaking (Decision 3: Moderate policy).

        Breaking changes (data-losing):
        - Entity removed
        - Field removed
        - Field type changed
        - Option removed from choice field

        Returns:
            True if this is a breaking change
        """
        return self in (
            ChangeType.ENTITY_REMOVED,
            ChangeType.FIELD_REMOVED,
            ChangeType.FIELD_TYPE_CHANGED,
            ChangeType.OPTION_REMOVED,
        )

    @property
    def is_structural(self) -> bool:
        """Check if this is a structural change (affects schema shape).

        Returns:
            True if this affects schema structure
        """
        return self in (
            ChangeType.ENTITY_ADDED,
            ChangeType.ENTITY_REMOVED,
            ChangeType.FIELD_ADDED,
            ChangeType.FIELD_REMOVED,
            ChangeType.FIELD_TYPE_CHANGED,
            ChangeType.RELATIONSHIP_ADDED,
            ChangeType.RELATIONSHIP_REMOVED,
        )


@dataclass(frozen=True)
class SchemaChange(ValueObject):
    """Represents a single change between schema versions.

    Captures what changed, where it changed, and relevant details.

    Examples:
        # Entity added
        change = SchemaChange(
            change_type=ChangeType.ENTITY_ADDED,
            entity_id="new_entity",
        )

        # Field removed
        change = SchemaChange(
            change_type=ChangeType.FIELD_REMOVED,
            entity_id="project",
            field_id="old_field",
        )

        # Field type changed
        change = SchemaChange(
            change_type=ChangeType.FIELD_TYPE_CHANGED,
            entity_id="project",
            field_id="status",
            old_value="TEXT",
            new_value="DROPDOWN",
        )
    """

    change_type: ChangeType
    entity_id: Optional[str] = None  # Optional for relationship changes
    field_id: Optional[str] = None
    constraint_type: Optional[str] = None
    option_value: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    relationship_id: Optional[str] = None  # Phase 6A: For relationship changes

    @property
    def is_breaking(self) -> bool:
        """Check if this change is breaking.

        Returns:
            True if this is a breaking change
        """
        return self.change_type.is_breaking

    @property
    def location(self) -> str:
        """Get human-readable location of the change.

        Returns:
            Location string (e.g., "entity.field" or "relationship_id")
        """
        # Relationship changes use relationship_id
        if self.relationship_id:
            return f"relationship:{self.relationship_id}"

        if self.field_id:
            if self.constraint_type:
                return f"{self.entity_id}.{self.field_id}[{self.constraint_type}]"
            if self.option_value:
                return f"{self.entity_id}.{self.field_id}[option:{self.option_value}]"
            return f"{self.entity_id}.{self.field_id}"
        return self.entity_id or ""

    @property
    def description(self) -> str:
        """Get human-readable description of the change.

        Returns:
            Description string
        """
        type_descriptions = {
            ChangeType.ENTITY_ADDED: f"Entity '{self.entity_id}' added",
            ChangeType.ENTITY_REMOVED: f"Entity '{self.entity_id}' removed",
            ChangeType.FIELD_ADDED: f"Field '{self.location}' added",
            ChangeType.FIELD_REMOVED: f"Field '{self.location}' removed",
            ChangeType.FIELD_TYPE_CHANGED: f"Field '{self.location}' type changed from {self.old_value} to {self.new_value}",
            ChangeType.FIELD_REQUIRED_CHANGED: f"Field '{self.location}' required changed from {self.old_value} to {self.new_value}",
            ChangeType.CONSTRAINT_ADDED: f"Constraint '{self.constraint_type}' added to '{self.location}'",
            ChangeType.CONSTRAINT_REMOVED: f"Constraint '{self.constraint_type}' removed from '{self.location}'",
            ChangeType.CONSTRAINT_MODIFIED: f"Constraint '{self.constraint_type}' modified on '{self.location}'",
            ChangeType.OPTION_ADDED: f"Option '{self.option_value}' added to '{self.location}'",
            ChangeType.OPTION_REMOVED: f"Option '{self.option_value}' removed from '{self.location}'",
            ChangeType.RELATIONSHIP_ADDED: f"Relationship '{self.relationship_id}' added",
            ChangeType.RELATIONSHIP_REMOVED: f"Relationship '{self.relationship_id}' removed",
        }
        return type_descriptions.get(self.change_type, f"Unknown change at {self.location}")

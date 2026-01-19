"""Base entity and aggregate root classes.

Domain-Driven Design tactical patterns (ADR-002).
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, List, TypeVar
from uuid import UUID, uuid4


TId = TypeVar("TId")  # Strongly typed ID


@dataclass
class Entity(ABC, Generic[TId]):
    """Base class for all entities.

    Entities have:
    - Identity (strongly typed ID)
    - Mutable state
    - Behavior methods

    RULES (IMPLEMENTATION_RULES.md Section 3):
    - Entities are NOT anemic - they have behavior
    - Identity is strongly typed (not raw strings/ints)
    - Equality based on ID only
    - No persistence code (infrastructure concern)
    """

    id: TId
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)

    def __eq__(self, other: Any) -> bool:
        """Entities are equal if they have the same ID and type."""
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets/dicts."""
        return hash(self.id)

    def _touch(self) -> None:
        """Update modified_at timestamp on state changes."""
        self.modified_at = datetime.now()


@dataclass
class AggregateRoot(Entity[TId], Generic[TId]):
    """Base class for aggregate roots.

    Aggregate roots:
    - Control access to child entities
    - Enforce consistency boundaries
    - Collect domain events
    - Are the only entry point for modifications

    RULES (IMPLEMENTATION_RULES.md Section 3):
    - Only aggregate roots can be fetched from repositories
    - Child entities accessed only through aggregate root
    - Domain events emitted for state changes
    - No direct modification of children from outside

    Usage:
        class Project(AggregateRoot[ProjectId]):
            def add_field_value(self, field_value: FieldValue) -> None:
                self.field_values.append(field_value)
                self._add_domain_event(FieldValueAdded(field_value))
    """

    _domain_events: List["DomainEvent"] = field(default_factory=list, init=False, repr=False)

    def _add_domain_event(self, event: "DomainEvent") -> None:
        """Add a domain event to be published after persistence."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List["DomainEvent"]:
        """Get all domain events for this aggregate."""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Clear domain events after they've been published."""
        self._domain_events.clear()


# Stub for DomainEvent to avoid circular imports
# Full implementation in events.py
class DomainEvent:
    """Placeholder for DomainEvent. See events.py for full implementation."""

    pass

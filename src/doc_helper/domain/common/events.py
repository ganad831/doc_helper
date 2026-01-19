"""Domain events for cross-cutting concerns.

Framework-independent event bus pattern (ADR-006).
"""

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from doc_helper.domain.common.value_object import ValueObject


@dataclass(frozen=True)
class DomainEvent(ValueObject, ABC):
    """Base class for all domain events.

    Domain events:
    - Are immutable value objects
    - Represent something that happened in the domain
    - Are emitted by aggregate roots
    - Published AFTER successful persistence
    - Framework-independent (NO PyQt6!)

    RULES (IMPLEMENTATION_RULES.md Section 2.2):
    - Domain events must NOT use PyQt6 signals
    - Events are plain immutable objects
    - Event bus in infrastructure layer handles pub/sub
    - Events emitted after persistence (eventual consistency)

    Example:
        @dataclass(frozen=True)
        class FieldValueChanged(DomainEvent):
            project_id: ProjectId
            field_id: FieldId
            old_value: Any
            new_value: Any

        # In aggregate root:
        def update_field_value(self, field_id, new_value):
            old_value = self._get_field_value(field_id)
            self._set_field_value(field_id, new_value)
            self._add_domain_event(
                FieldValueChanged(
                    project_id=self.id,
                    field_id=field_id,
                    old_value=old_value,
                    new_value=new_value
                )
            )
    """

    event_id: UUID = UUID(int=0)  # Will be set in __post_init__
    occurred_at: datetime = datetime.min  # Will be set in __post_init__

    def __post_init__(self) -> None:
        """Initialize event ID and timestamp.

        Note: We use object.__setattr__ because dataclass is frozen.
        """
        if self.event_id == UUID(int=0):
            object.__setattr__(self, "event_id", uuid4())
        if self.occurred_at == datetime.min:
            object.__setattr__(self, "occurred_at", datetime.now())

"""Domain events for project aggregate.

ADR-027: Field History Storage
- FieldValueChanged event emitted when field values change
- Event captures: old value, new value, change source (USER_EDIT, FORMULA, etc.)
- Application layer subscribes to this event to create history entries
"""

from dataclasses import dataclass
from typing import Any, Optional

from doc_helper.domain.common.events import DomainEvent
from doc_helper.domain.project.field_history import ChangeSource
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


@dataclass(frozen=True, kw_only=True)
class FieldValueChanged(DomainEvent):
    """Domain event emitted when a field value changes.

    ADR-027: This event is the authoritative source for field history.
    The application layer subscribes to this event and persists history entries.

    Attributes:
        project_id: Project where the change occurred
        field_id: Field that was changed
        previous_value: Value before the change (None if field was unset)
        new_value: Value after the change
        change_source: Source of the change (USER_EDIT, FORMULA_RECOMPUTATION, etc.)
        user_id: User who made the change (if applicable)

    Note: kw_only=True allows required fields after parent's default fields (Python 3.10+)

    Example:
        # Emitted by Project aggregate when set_field_value() is called
        event = FieldValueChanged(
            project_id=ProjectId("abc-123"),
            field_id=FieldDefinitionId("site_location"),
            previous_value="123 Main St",
            new_value="456 Oak Ave",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-123"
        )
    """

    project_id: ProjectId
    field_id: FieldDefinitionId
    previous_value: Any  # Primitive type (str, int, float, etc.) or None
    new_value: Any  # Primitive type (str, int, float, etc.)
    change_source: ChangeSource
    user_id: Optional[str] = None  # None for system-initiated changes

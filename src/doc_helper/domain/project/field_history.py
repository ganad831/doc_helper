"""Field history value objects for audit trail.

ADR-027: Field History Storage
- Persistent, append-only record of field value changes
- Architecturally distinct from undo system
- Project-scoped, survives indefinitely
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from doc_helper.domain.common.value_object import ValueObject


class ChangeSource(Enum):
    """Source of a field value change.

    ADR-027: Track where changes originated for audit purposes.
    """

    USER_EDIT = "USER_EDIT"  # Direct user edit
    FORMULA_RECOMPUTATION = "FORMULA_RECOMPUTATION"  # Formula recalculation
    OVERRIDE_ACCEPTANCE = "OVERRIDE_ACCEPTANCE"  # Override accepted
    CONTROL_EFFECT = "CONTROL_EFFECT"  # Control rule VALUE_SET
    UNDO_OPERATION = "UNDO_OPERATION"  # Undo command executed
    REDO_OPERATION = "REDO_OPERATION"  # Redo command executed


@dataclass(frozen=True)
class FieldHistoryEntry(ValueObject):
    """Immutable record of a single field value change.

    ADR-027: Field History Storage
    - One entry per field value transition
    - Append-only (never modified after creation)
    - Records what changed, when, and why
    - No business logic (pure data)

    Example:
        entry = FieldHistoryEntry.create(
            project_id="proj-123",
            field_id="F1",
            previous_value="100",
            new_value="150",
            change_source=ChangeSource.USER_EDIT,
            user_id="user-456"
        )
    """

    history_id: UUID
    project_id: str  # Project containing the field
    field_id: str  # Field that changed
    previous_value: Any  # Value before change
    new_value: Any  # Value after change
    change_source: ChangeSource  # Where the change came from
    user_id: str | None  # User who made the change (if applicable)
    timestamp: datetime  # When the change occurred

    @classmethod
    def create(
        cls,
        project_id: str,
        field_id: str,
        previous_value: Any,
        new_value: Any,
        change_source: ChangeSource,
        user_id: str | None = None,
    ) -> "FieldHistoryEntry":
        """Create a new field history entry.

        Args:
            project_id: ID of project containing the field
            field_id: ID of field that changed
            previous_value: Value before change (raw, not formatted)
            new_value: Value after change (raw, not formatted)
            change_source: Source of the change
            user_id: ID of user who made the change (optional)

        Returns:
            New FieldHistoryEntry with generated ID and timestamp
        """
        return cls(
            history_id=uuid4(),
            project_id=project_id,
            field_id=field_id,
            previous_value=previous_value,
            new_value=new_value,
            change_source=change_source,
            user_id=user_id,
            timestamp=datetime.utcnow(),
        )

    def is_user_initiated(self) -> bool:
        """Check if change was initiated by user.

        Returns:
            True if change source is USER_EDIT, UNDO_OPERATION, or REDO_OPERATION
        """
        return self.change_source in (
            ChangeSource.USER_EDIT,
            ChangeSource.UNDO_OPERATION,
            ChangeSource.REDO_OPERATION,
        )

    def is_system_initiated(self) -> bool:
        """Check if change was initiated by system.

        Returns:
            True if change source is formula, override, or control
        """
        return self.change_source in (
            ChangeSource.FORMULA_RECOMPUTATION,
            ChangeSource.OVERRIDE_ACCEPTANCE,
            ChangeSource.CONTROL_EFFECT,
        )

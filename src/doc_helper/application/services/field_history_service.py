"""Field history service for tracking field value changes.

ADR-027: Field History Storage
- Subscribes to FieldValueChanged domain events
- Creates FieldHistoryEntry records from events
- Persists history entries via IFieldHistoryRepository
"""

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.field_history import FieldHistoryEntry
from doc_helper.domain.project.field_history_repository import IFieldHistoryRepository
from doc_helper.domain.project.project_events import FieldValueChanged


class FieldHistoryService:
    """Service for recording field value changes as history entries.

    ADR-027: This service handles the application-level orchestration of field history:
    - Receives FieldValueChanged domain events
    - Converts events to FieldHistoryEntry value objects
    - Persists entries via IFieldHistoryRepository

    The service acts as a bridge between domain events (what happened) and
    persistent history (audit trail).

    Dependencies:
        - IFieldHistoryRepository: For persisting history entries

    Example:
        history_repo = SqliteFieldHistoryRepository(db_path)
        history_service = FieldHistoryService(history_repo)

        # Handle event from Project aggregate
        event = FieldValueChanged(...)
        result = history_service.handle_field_value_changed(event)
        if isinstance(result, Success):
            print("History entry recorded")
    """

    def __init__(self, field_history_repository: IFieldHistoryRepository) -> None:
        """Initialize FieldHistoryService.

        Args:
            field_history_repository: Repository for history persistence
        """
        if not isinstance(field_history_repository, IFieldHistoryRepository):
            raise TypeError(
                "field_history_repository must implement IFieldHistoryRepository"
            )
        self._field_history_repository = field_history_repository

    def handle_field_value_changed(
        self, event: FieldValueChanged
    ) -> Result[None, str]:
        """Handle FieldValueChanged event by creating and persisting history entry.

        ADR-027: This method is called after domain events are published
        (typically after successful project save).

        Args:
            event: FieldValueChanged domain event

        Returns:
            Success(None) if history entry persisted successfully
            Failure(error) if persistence failed
        """
        if not isinstance(event, FieldValueChanged):
            return Failure("event must be a FieldValueChanged instance")

        # Convert domain event to history entry
        # Note: Event fields use domain types (ProjectId, FieldDefinitionId)
        # but FieldHistoryEntry uses string IDs for storage
        history_entry = FieldHistoryEntry.create(
            project_id=str(event.project_id.value),  # Convert ProjectId to string
            field_id=str(
                event.field_id.value
            ),  # Convert FieldDefinitionId to string
            previous_value=event.previous_value,
            new_value=event.new_value,
            change_source=event.change_source,
            user_id=event.user_id,
        )

        # Persist history entry
        result = self._field_history_repository.add_entry(history_entry)
        if isinstance(result, Failure):
            return Failure(f"Failed to persist history entry: {result.error}")

        return Success(None)

    def handle_domain_events(
        self, events: list[FieldValueChanged]
    ) -> Result[int, str]:
        """Handle multiple FieldValueChanged events in batch.

        Convenience method for processing multiple events from an aggregate.

        Args:
            events: List of FieldValueChanged domain events

        Returns:
            Success(count) with number of entries persisted
            Failure(error) if any persistence failed
        """
        if not isinstance(events, list):
            return Failure("events must be a list")

        persisted_count = 0
        for event in events:
            # Only handle FieldValueChanged events (ignore other event types)
            if isinstance(event, FieldValueChanged):
                result = self.handle_field_value_changed(event)
                if isinstance(result, Failure):
                    # Return first error encountered
                    return Failure(
                        f"Failed after {persisted_count} entries: {result.error}"
                    )
                persisted_count += 1

        return Success(persisted_count)

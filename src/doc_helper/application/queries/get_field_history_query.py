"""Query for retrieving field history.

ADR-027: Field History Storage
RULES (AGENT_RULES.md Section 3-4):
- Queries return DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary
- Use mappers to convert Domain → DTO
"""

from typing import Optional

from doc_helper.application.dto import FieldHistoryResultDTO
from doc_helper.application.mappers.field_history_mapper import FieldHistoryMapper
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.field_history_repository import IFieldHistoryRepository


class GetFieldHistoryQuery:
    """Query to retrieve field history entries.

    ADR-027: Returns paginated field history for a specific field or project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return DTOs, not domain objects
    - CQRS pattern: separate reads from writes

    Example:
        query = GetFieldHistoryQuery(field_history_repository=repo)
        result = query.execute_for_field(
            project_id="proj-123",
            field_id="field-456",
            limit=10,
            offset=0
        )
        if isinstance(result, Success):
            history_result = result.value  # FieldHistoryResultDTO
            for entry_dto in history_result.entries:
                print(f"{entry_dto.timestamp}: {entry_dto.previous_value} → {entry_dto.new_value}")
    """

    def __init__(
        self, field_history_repository: IFieldHistoryRepository
    ) -> None:
        """Initialize query.

        Args:
            field_history_repository: Repository for loading field history
        """
        if not isinstance(field_history_repository, IFieldHistoryRepository):
            raise TypeError(
                "field_history_repository must implement IFieldHistoryRepository"
            )
        self._field_history_repository = field_history_repository

    def execute_for_field(
        self,
        project_id: str,
        field_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Result[FieldHistoryResultDTO, str]:
        """Execute query to get history for a specific field.

        ADR-027: Returns entries ordered by timestamp DESC (newest first).

        Args:
            project_id: Project ID to filter by
            field_id: Field ID to filter by
            limit: Maximum number of entries to return (None = all)
            offset: Number of entries to skip (for pagination)

        Returns:
            Success(FieldHistoryResultDTO) with entries and pagination metadata
            Failure(error) on error

        Example:
            # Get first page (10 entries)
            result = query.execute_for_field("proj-123", "field-456", limit=10, offset=0)

            # Get second page
            result = query.execute_for_field("proj-123", "field-456", limit=10, offset=10)
        """
        if not isinstance(project_id, str) or not project_id:
            return Failure("project_id must be a non-empty string")
        if not isinstance(field_id, str) or not field_id:
            return Failure("field_id must be a non-empty string")
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            return Failure("limit must be a positive integer or None")
        if not isinstance(offset, int) or offset < 0:
            return Failure("offset must be a non-negative integer")

        # Get entries from repository
        entries_result = self._field_history_repository.get_by_field(
            project_id, field_id, limit, offset
        )
        if isinstance(entries_result, Failure):
            return Failure(f"Failed to load field history: {entries_result.error}")

        entries = entries_result.value

        # Get total count for pagination metadata
        count_result = self._field_history_repository.count_by_field(
            project_id, field_id
        )
        if isinstance(count_result, Failure):
            return Failure(f"Failed to count field history: {count_result.error}")

        total_count = count_result.value

        # Map to DTO result before returning
        result_dto = FieldHistoryMapper.to_result_dto(
            entries, total_count, offset, limit
        )
        return Success(result_dto)

    def execute_for_project(
        self,
        project_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Result[FieldHistoryResultDTO, str]:
        """Execute query to get history for all fields in a project.

        ADR-027: Returns entries ordered by timestamp DESC (newest first).

        Args:
            project_id: Project ID to filter by
            limit: Maximum number of entries to return (None = all)
            offset: Number of entries to skip (for pagination)

        Returns:
            Success(FieldHistoryResultDTO) with entries and pagination metadata
            Failure(error) on error

        Example:
            # Get all history for project (first 50 entries)
            result = query.execute_for_project("proj-123", limit=50, offset=0)
        """
        if not isinstance(project_id, str) or not project_id:
            return Failure("project_id must be a non-empty string")
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            return Failure("limit must be a positive integer or None")
        if not isinstance(offset, int) or offset < 0:
            return Failure("offset must be a non-negative integer")

        # Get entries from repository
        entries_result = self._field_history_repository.get_by_project(
            project_id, limit, offset
        )
        if isinstance(entries_result, Failure):
            return Failure(f"Failed to load project history: {entries_result.error}")

        entries = entries_result.value

        # Get total count for pagination metadata
        count_result = self._field_history_repository.count_by_project(project_id)
        if isinstance(count_result, Failure):
            return Failure(f"Failed to count project history: {count_result.error}")

        total_count = count_result.value

        # Map to DTO result before returning
        result_dto = FieldHistoryMapper.to_result_dto(
            entries, total_count, offset, limit
        )
        return Success(result_dto)

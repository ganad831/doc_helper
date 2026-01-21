"""Field history mapper - Domain → DTO conversion.

ADR-027: Field History Storage
RULES (AGENT_RULES.md Section 3-4):
- ONE-WAY mapping: Domain → DTO only
- NO to_domain() or from_dto() methods
- DTOs use primitive types (str, not UUID/enum)
"""

from doc_helper.application.dto import FieldHistoryEntryDTO, FieldHistoryResultDTO
from doc_helper.domain.project.field_history import FieldHistoryEntry


class FieldHistoryMapper:
    """Maps FieldHistoryEntry domain value object to FieldHistoryEntryDTO for UI display.

    ADR-027: This mapper is ONE-WAY: Domain → DTO only.
    There is NO reverse mapping (to_domain, from_dto).

    Example:
        entry = FieldHistoryEntry(...)
        dto = FieldHistoryMapper.to_dto(entry)
        # dto is now safe for presentation layer consumption
    """

    @staticmethod
    def to_dto(entry: FieldHistoryEntry) -> FieldHistoryEntryDTO:
        """Convert FieldHistoryEntry to FieldHistoryEntryDTO.

        Args:
            entry: FieldHistoryEntry domain value object

        Returns:
            FieldHistoryEntryDTO for presentation layer

        Example:
            dto = FieldHistoryMapper.to_dto(history_entry)
            assert isinstance(dto.history_id, str)  # UUID converted to string
            assert isinstance(dto.change_source, str)  # Enum converted to string
        """
        return FieldHistoryEntryDTO(
            history_id=str(entry.history_id),  # UUID → string
            project_id=entry.project_id,  # Already string in domain
            field_id=entry.field_id,  # Already string in domain
            previous_value=entry.previous_value,  # Primitive type (str, int, float, etc.)
            new_value=entry.new_value,  # Primitive type
            change_source=entry.change_source.value,  # Enum → string ("USER_EDIT", etc.)
            user_id=entry.user_id,  # Already string or None
            timestamp=entry.timestamp.isoformat(),  # datetime → ISO string
        )

    @staticmethod
    def to_result_dto(
        entries: list[FieldHistoryEntry], total_count: int, offset: int, limit: int | None
    ) -> FieldHistoryResultDTO:
        """Convert list of FieldHistoryEntry to FieldHistoryResultDTO with pagination.

        ADR-027: Used by GetFieldHistoryQuery to return paginated results.

        Args:
            entries: List of FieldHistoryEntry domain value objects
            total_count: Total count of entries (for pagination metadata)
            offset: Offset used in query
            limit: Limit used in query (None if unlimited)

        Returns:
            FieldHistoryResultDTO with entries tuple and pagination metadata

        Example:
            entries = [entry1, entry2, entry3]
            result_dto = FieldHistoryMapper.to_result_dto(entries, total_count=100, offset=0, limit=10)
            assert len(result_dto.entries) == 3
            assert result_dto.total_count == 100
        """
        # Convert all entries to DTOs
        entry_dtos = tuple(FieldHistoryMapper.to_dto(entry) for entry in entries)

        return FieldHistoryResultDTO(
            entries=entry_dtos, total_count=total_count, offset=offset, limit=limit
        )

    # ❌ FORBIDDEN: No to_domain() method
    # ❌ FORBIDDEN: No from_dto() method
    # ❌ FORBIDDEN: No reverse mapping
    # Reason: Mappers are one-way only (unified_upgrade_plan.md H3)
    # Field history is append-only, no need for reverse mapping

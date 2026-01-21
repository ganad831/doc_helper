"""Repository interface for field history.

ADR-027: Field History Storage
- Append-only persistence (no updates or deletes)
- Project-scoped queries
- Pagination support for large result sets
"""

from abc import ABC, abstractmethod
from typing import Optional

from doc_helper.domain.common.result import Result
from doc_helper.domain.project.field_history import FieldHistoryEntry


class IFieldHistoryRepository(ABC):
    """Repository interface for field history operations.

    ADR-027: Field History Storage
    - Append-only semantics (only add_entry method, no update/delete)
    - Project-scoped queries
    - Pagination for large histories

    Example:
        repo = SqliteFieldHistoryRepository(db_path="project.db")
        result = repo.add_entry(history_entry)
        if isinstance(result, Success):
            print("History entry saved")
    """

    @abstractmethod
    def add_entry(self, entry: FieldHistoryEntry) -> Result[None, str]:
        """Add a new history entry (append-only).

        Args:
            entry: History entry to append

        Returns:
            Success(None) if added, Failure(error) otherwise
        """
        pass

    @abstractmethod
    def get_by_field(
        self,
        project_id: str,
        field_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Result[list[FieldHistoryEntry], str]:
        """Get history entries for a specific field.

        Args:
            project_id: Project ID to filter by
            field_id: Field ID to filter by
            limit: Maximum number of entries to return (None = all)
            offset: Number of entries to skip (for pagination)

        Returns:
            Success(entries) ordered newest first, or Failure(error)
        """
        pass

    @abstractmethod
    def get_by_project(
        self,
        project_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Result[list[FieldHistoryEntry], str]:
        """Get all history entries for a project.

        Args:
            project_id: Project ID to filter by
            limit: Maximum number of entries to return (None = all)
            offset: Number of entries to skip (for pagination)

        Returns:
            Success(entries) ordered newest first, or Failure(error)
        """
        pass

    @abstractmethod
    def count_by_field(
        self,
        project_id: str,
        field_id: str,
    ) -> Result[int, str]:
        """Count history entries for a specific field.

        Args:
            project_id: Project ID to filter by
            field_id: Field ID to filter by

        Returns:
            Success(count) or Failure(error)
        """
        pass

    @abstractmethod
    def count_by_project(self, project_id: str) -> Result[int, str]:
        """Count all history entries for a project.

        Args:
            project_id: Project ID to filter by

        Returns:
            Success(count) or Failure(error)
        """
        pass

    @abstractmethod
    def delete_by_project(self, project_id: str) -> Result[None, str]:
        """Delete all history entries for a project.

        ADR-027: Only used when project is deleted entirely.
        Individual history entries are never deleted.

        Args:
            project_id: Project ID whose history to delete

        Returns:
            Success(None) if deleted, Failure(error) otherwise
        """
        pass

"""SQLite implementation of field history repository.

ADR-027: Field History Storage
- Append-only persistence (only add_entry, no update/delete of individual entries)
- Project-scoped queries
- Pagination support for large result sets
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.field_history import (
    ChangeSource,
    FieldHistoryEntry,
)
from doc_helper.domain.project.field_history_repository import IFieldHistoryRepository
from doc_helper.infrastructure.persistence.sqlite_base import SqliteConnection


class SqliteFieldHistoryRepository(IFieldHistoryRepository):
    """SQLite implementation of field history repository.

    ADR-027: Field History Storage
    - Stores history entries in field_history table
    - Append-only semantics (no updates to existing entries)
    - Supports pagination for large histories

    Database schema:
    - field_history table: All field value change records

    Example:
        repo = SqliteFieldHistoryRepository(db_path="project.db")
        entry = FieldHistoryEntry.create(...)
        result = repo.add_entry(entry)
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize repository.

        Args:
            db_path: Path to SQLite database (typically project.db)
        """
        if not isinstance(db_path, (str, Path)):
            raise TypeError("db_path must be a string or Path")

        self.db_path = Path(db_path)
        self._connection = SqliteConnection(self.db_path)

        # Create table if database is new
        self._ensure_schema()

    def add_entry(self, entry: FieldHistoryEntry) -> Result[None, str]:
        """Add a new history entry (append-only).

        Args:
            entry: History entry to append

        Returns:
            Success(None) if added, Failure(error) otherwise
        """
        if not isinstance(entry, FieldHistoryEntry):
            return Failure("entry must be a FieldHistoryEntry instance")

        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Insert history entry
                cursor.execute(
                    """
                    INSERT INTO field_history
                    (history_id, project_id, field_id, previous_value, new_value,
                     change_source, user_id, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(entry.history_id),
                        entry.project_id,
                        entry.field_id,
                        self._serialize_value(entry.previous_value),
                        self._serialize_value(entry.new_value),
                        entry.change_source.value,
                        entry.user_id,
                        entry.timestamp.isoformat(),
                    ),
                )

                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error adding history entry: {str(e)}")

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
        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Build query with optional limit
                query = """
                    SELECT * FROM field_history
                    WHERE project_id = ? AND field_id = ?
                    ORDER BY timestamp DESC
                """
                params: list[Any] = [project_id, field_id]

                if limit is not None:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Convert rows to FieldHistoryEntry objects
                entries = [self._row_to_entry(row) for row in rows]

                return Success(entries)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error retrieving field history: {str(e)}")

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
        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Build query with optional limit
                query = """
                    SELECT * FROM field_history
                    WHERE project_id = ?
                    ORDER BY timestamp DESC
                """
                params: list[Any] = [project_id]

                if limit is not None:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Convert rows to FieldHistoryEntry objects
                entries = [self._row_to_entry(row) for row in rows]

                return Success(entries)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error retrieving project history: {str(e)}")

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
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(*) as count FROM field_history
                    WHERE project_id = ? AND field_id = ?
                    """,
                    (project_id, field_id),
                )
                row = cursor.fetchone()
                count = row["count"] if row else 0
                return Success(count)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error counting field history: {str(e)}")

    def count_by_project(self, project_id: str) -> Result[int, str]:
        """Count all history entries for a project.

        Args:
            project_id: Project ID to filter by

        Returns:
            Success(count) or Failure(error)
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(*) as count FROM field_history
                    WHERE project_id = ?
                    """,
                    (project_id,),
                )
                row = cursor.fetchone()
                count = row["count"] if row else 0
                return Success(count)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error counting project history: {str(e)}")

    def delete_by_project(self, project_id: str) -> Result[None, str]:
        """Delete all history entries for a project.

        ADR-027: Only used when project is deleted entirely.
        Individual history entries are never deleted.

        Args:
            project_id: Project ID whose history to delete

        Returns:
            Success(None) if deleted, Failure(error) otherwise
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM field_history WHERE project_id = ?",
                    (project_id,),
                )
                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error deleting project history: {str(e)}")

    def _ensure_schema(self) -> None:
        """Ensure database schema exists.

        Creates field_history table if it doesn't exist.
        """
        # Create database file if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.touch(exist_ok=True)

        with self._connection as conn:
            cursor = conn.cursor()

            # Create field_history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS field_history (
                    history_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    field_id TEXT NOT NULL,
                    previous_value TEXT,
                    new_value TEXT,
                    change_source TEXT NOT NULL,
                    user_id TEXT,
                    timestamp TEXT NOT NULL
                )
                """
            )

            # Create indexes for efficient queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_field_history_project
                ON field_history(project_id)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_field_history_field
                ON field_history(project_id, field_id)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_field_history_timestamp
                ON field_history(timestamp DESC)
                """
            )

    @staticmethod
    def _serialize_value(value: Any) -> str:
        """Serialize a value to JSON string for storage.

        Args:
            value: Value to serialize

        Returns:
            JSON string representation
        """
        return json.dumps(value)

    @staticmethod
    def _deserialize_value(value_str: str) -> Any:
        """Deserialize a JSON string to value.

        Args:
            value_str: JSON string to deserialize

        Returns:
            Deserialized value
        """
        if value_str is None:
            return None
        return json.loads(value_str)

    def _row_to_entry(self, row: sqlite3.Row) -> FieldHistoryEntry:
        """Convert database row to FieldHistoryEntry.

        Args:
            row: SQLite row

        Returns:
            FieldHistoryEntry instance
        """
        return FieldHistoryEntry(
            history_id=UUID(row["history_id"]),
            project_id=row["project_id"],
            field_id=row["field_id"],
            previous_value=self._deserialize_value(row["previous_value"]),
            new_value=self._deserialize_value(row["new_value"]),
            change_source=ChangeSource(row["change_source"]),
            user_id=row["user_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )

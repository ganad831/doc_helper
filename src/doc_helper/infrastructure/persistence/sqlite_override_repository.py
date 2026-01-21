"""SQLite implementation of override repository.

Provides persistent storage for Override entities using SQLite database.

RULES (ADR-020, ADR-024):
- Repository works directly with domain entities
- Returns Result[T, E] for explicit error handling
- No business logic, only persistence operations
- Interface defined in domain, implementation in infrastructure
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.override.override_entity import Override
from doc_helper.domain.override.override_ids import OverrideId
from doc_helper.domain.override.override_state import OverrideState
from doc_helper.domain.override.repositories import IOverrideRepository
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId
from doc_helper.infrastructure.persistence.sqlite_base import SqliteConnection


class SqliteOverrideRepository(IOverrideRepository):
    """SQLite implementation of override repository.

    Stores overrides in a SQLite database with persistent storage.

    Database schema:
    - overrides table: Override entities with all fields
    - Indexes: project_id, (project_id, field_id), state

    Example:
        repo = SqliteOverrideRepository(db_path="projects.db")
        result = repo.save(override)
        if result.is_success:
            print("Override saved successfully")
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize repository.

        Args:
            db_path: Path to SQLite database

        Raises:
            TypeError: If db_path is not string or Path
        """
        if not isinstance(db_path, (str, Path)):
            raise TypeError("db_path must be a string or Path")

        self.db_path = Path(db_path)
        self._connection = SqliteConnection(self.db_path)

        # Create schema if database is new
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create overrides table and indexes if they don't exist.

        This method is idempotent - safe to call multiple times.
        """
        # Create parent directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connection as conn:
            cursor = conn.cursor()

            # Create overrides table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS overrides (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    field_id TEXT NOT NULL,
                    override_value TEXT NOT NULL,
                    original_value TEXT NOT NULL,
                    state TEXT NOT NULL,
                    reason TEXT,
                    conflict_type TEXT,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                        ON DELETE CASCADE
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_overrides_project
                ON overrides(project_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_overrides_project_field
                ON overrides(project_id, field_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_overrides_state
                ON overrides(state)
            """)

    @staticmethod
    def _row_to_override(row: sqlite3.Row) -> Override:
        """Convert database row to Override entity.

        Args:
            row: SQLite row with override data

        Returns:
            Override entity reconstructed from row

        Raises:
            ValueError: If row data is invalid
        """
        return Override(
            id=OverrideId(UUID(row["id"])),
            project_id=ProjectId(UUID(row["project_id"])),
            field_id=FieldDefinitionId(row["field_id"]),
            override_value=json.loads(row["override_value"]),
            original_value=json.loads(row["original_value"]),
            state=OverrideState(row["state"]),
            reason=row["reason"],
            conflict_type=row["conflict_type"],
        )

    def get_by_id(self, override_id: OverrideId) -> Result[Override, str]:
        """Get override by ID.

        Args:
            override_id: Override identifier

        Returns:
            Success(override) if found
            Failure(error) if not found or error occurred
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM overrides WHERE id = ?",
                    (str(override_id.value),)
                )
                row = cursor.fetchone()

                if row is None:
                    return Failure(f"Override {override_id.value} not found")

                return Success(self._row_to_override(row))

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error getting override: {str(e)}")

    def get_by_project_and_field(
        self, project_id: ProjectId, field_id: FieldDefinitionId
    ) -> Result[Optional[Override], str]:
        """Get override for a specific field in a project.

        Args:
            project_id: Project identifier
            field_id: Field identifier

        Returns:
            Success(override) if found
            Success(None) if no override exists for this field
            Failure(error) if error occurred
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM overrides WHERE project_id = ? AND field_id = ?",
                    (str(project_id.value), field_id.value)
                )
                row = cursor.fetchone()

                if row is None:
                    return Success(None)

                return Success(self._row_to_override(row))

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error getting override: {str(e)}")

    def list_by_project(self, project_id: ProjectId) -> Result[tuple[Override, ...], str]:
        """Get all overrides for a project.

        Args:
            project_id: Project identifier

        Returns:
            Success(tuple of overrides) if found (may be empty tuple)
            Failure(error) if error occurred
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM overrides WHERE project_id = ?",
                    (str(project_id.value),)
                )
                rows = cursor.fetchall()

                overrides = tuple(self._row_to_override(row) for row in rows)
                return Success(overrides)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error listing overrides: {str(e)}")

    def save(self, override: Override) -> Result[None, str]:
        """Save override (create or update).

        Args:
            override: Override to save

        Returns:
            Success(None) if saved successfully
            Failure(error) if save failed
        """
        if not isinstance(override, Override):
            return Failure("override must be an Override instance")

        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO overrides
                    (id, project_id, field_id, override_value, original_value,
                     state, reason, conflict_type, created_at, modified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(override.id.value),
                        str(override.project_id.value),
                        override.field_id.value,
                        json.dumps(override.override_value),
                        json.dumps(override.original_value),
                        override.state.value,
                        override.reason,
                        override.conflict_type,
                        override.created_at.isoformat(),
                        override.modified_at.isoformat(),
                    )
                )
                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error saving override: {str(e)}")

    def delete(self, override_id: OverrideId) -> Result[None, str]:
        """Delete override by ID.

        Args:
            override_id: Override identifier

        Returns:
            Success(None) if deleted successfully
            Failure(error) if delete failed or override not found
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM overrides WHERE id = ?",
                    (str(override_id.value),)
                )

                if cursor.rowcount == 0:
                    return Failure(f"Override {override_id.value} not found")

                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error deleting override: {str(e)}")

    def delete_by_project_and_field(
        self, project_id: ProjectId, field_id: FieldDefinitionId
    ) -> Result[None, str]:
        """Delete override for a specific field in a project.

        Args:
            project_id: Project identifier
            field_id: Field identifier

        Returns:
            Success(None) if deleted successfully (or no override existed)
            Failure(error) if error occurred
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM overrides WHERE project_id = ? AND field_id = ?",
                    (str(project_id.value), field_id.value)
                )

                # Success even if no rows deleted (idempotent operation)
                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error deleting override: {str(e)}")

    def exists(self, override_id: OverrideId) -> Result[bool, str]:
        """Check if override exists.

        Args:
            override_id: Override identifier

        Returns:
            Success(True) if exists
            Success(False) if does not exist
            Failure(error) if error occurred
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM overrides WHERE id = ? LIMIT 1",
                    (str(override_id.value),)
                )

                exists = cursor.fetchone() is not None
                return Success(exists)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error checking override existence: {str(e)}")

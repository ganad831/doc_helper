"""SQLite implementation of undo history repository.

ADR-031: Undo History Persistence
- Project-scoped persistence of undo stacks
- JSON serialization for command storage
- Best-effort restoration (corrupted data returns None, not error)
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from doc_helper.application.undo.undo_history_repository import IUndoHistoryRepository
from doc_helper.application.undo.undo_persistence_dto import (
    UndoCommandPersistenceDTO,
    UndoHistoryPersistenceDTO,
)
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.infrastructure.persistence.sqlite_base import SqliteConnection


class SqliteUndoHistoryRepository(IUndoHistoryRepository):
    """SQLite implementation of undo history repository.

    ADR-031: Project-scoped undo history persistence.

    Database schema:
    - undo_history table: project_id (PK), undo_stack_json, redo_stack_json,
      max_stack_depth, last_modified

    Storage strategy:
    - Each project has at most one undo_history row
    - Undo/redo stacks serialized as JSON arrays
    - Commands stored as JSON objects with type and state_data

    Example:
        repo = SqliteUndoHistoryRepository(db_path="project.db")

        # Save undo history
        history = UndoHistoryPersistenceDTO(...)
        result = repo.save(history)

        # Load undo history
        load_result = repo.load(project_id="proj-123")
        if load_result.is_success:
            history = load_result.value  # May be None
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

    def save(self, history: UndoHistoryPersistenceDTO) -> Result[None, str]:
        """Save undo history for a project.

        ADR-031: Overwrites existing undo history. Called on project save.

        Args:
            history: UndoHistoryPersistenceDTO to persist

        Returns:
            Success(None) if saved, Failure(error) otherwise
        """
        if not isinstance(history, UndoHistoryPersistenceDTO):
            return Failure("history must be an UndoHistoryPersistenceDTO instance")

        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Serialize stacks to JSON
                undo_stack_json = self._serialize_stack(history.undo_stack)
                redo_stack_json = self._serialize_stack(history.redo_stack)

                # Upsert (INSERT OR REPLACE) to handle both insert and update
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO undo_history
                    (project_id, undo_stack_json, redo_stack_json, max_stack_depth, last_modified)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        history.project_id,
                        undo_stack_json,
                        redo_stack_json,
                        history.max_stack_depth,
                        history.last_modified,
                    ),
                )

                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error saving undo history: {str(e)}")

    def load(
        self, project_id: str
    ) -> Result[Optional[UndoHistoryPersistenceDTO], str]:
        """Load undo history for a project.

        ADR-031: Best-effort restoration - corrupted data returns None, not error.

        Args:
            project_id: Project ID to load history for

        Returns:
            Success(UndoHistoryPersistenceDTO) if found and valid
            Success(None) if not found or corrupted
            Failure(error) only on severe database errors
        """
        if not isinstance(project_id, str) or not project_id:
            return Failure("project_id must be a non-empty string")

        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT project_id, undo_stack_json, redo_stack_json,
                           max_stack_depth, last_modified
                    FROM undo_history
                    WHERE project_id = ?
                    """,
                    (project_id,),
                )
                row = cursor.fetchone()

                if row is None:
                    # No undo history exists for this project
                    return Success(None)

                # Deserialize stacks from JSON
                try:
                    undo_stack = self._deserialize_stack(row["undo_stack_json"])
                    redo_stack = self._deserialize_stack(row["redo_stack_json"])

                    history = UndoHistoryPersistenceDTO(
                        project_id=row["project_id"],
                        undo_stack=undo_stack,
                        redo_stack=redo_stack,
                        max_stack_depth=row["max_stack_depth"],
                        last_modified=row["last_modified"],
                    )

                    return Success(history)

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # ADR-031: Best-effort restoration - corrupted data returns None
                    # Log error but don't prevent project open
                    print(
                        f"Warning: Failed to deserialize undo history for project {project_id}: {e}"
                    )
                    return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error loading undo history: {str(e)}")

    def delete(self, project_id: str) -> Result[None, str]:
        """Delete undo history for a project.

        ADR-031: Called on explicit project close (session boundary).

        Args:
            project_id: Project ID whose undo history to delete

        Returns:
            Success(None) if deleted, Failure(error) otherwise
        """
        if not isinstance(project_id, str) or not project_id:
            return Failure("project_id must be a non-empty string")

        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM undo_history WHERE project_id = ?",
                    (project_id,),
                )
                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error deleting undo history: {str(e)}")

    def exists(self, project_id: str) -> Result[bool, str]:
        """Check if undo history exists for a project.

        Args:
            project_id: Project ID to check

        Returns:
            Success(True) if exists, Success(False) if not, Failure(error) on error
        """
        if not isinstance(project_id, str) or not project_id:
            return Failure("project_id must be a non-empty string")

        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) as count FROM undo_history WHERE project_id = ?",
                    (project_id,),
                )
                row = cursor.fetchone()
                exists = row["count"] > 0
                return Success(exists)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error checking undo history existence: {str(e)}")

    def _ensure_schema(self) -> None:
        """Ensure database schema exists.

        Creates undo_history table if it doesn't exist.
        """
        # Create database file if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.touch(exist_ok=True)

        with self._connection as conn:
            cursor = conn.cursor()

            # Create undo_history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS undo_history (
                    project_id TEXT PRIMARY KEY,
                    undo_stack_json TEXT NOT NULL,
                    redo_stack_json TEXT NOT NULL,
                    max_stack_depth INTEGER NOT NULL,
                    last_modified TEXT NOT NULL
                )
                """
            )

            # Create index on project_id (redundant with PRIMARY KEY, but explicit)
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_undo_history_project
                ON undo_history(project_id)
                """
            )

    @staticmethod
    def _serialize_stack(
        stack: tuple[UndoCommandPersistenceDTO, ...]
    ) -> str:
        """Serialize undo/redo stack to JSON string.

        Args:
            stack: Tuple of UndoCommandPersistenceDTO

        Returns:
            JSON string representation
        """
        # Convert tuple of DTOs to list of dicts for JSON serialization
        commands_list = [
            {
                "command_type": cmd.command_type,
                "state_data": cmd.state_data,
                "timestamp": cmd.timestamp,
            }
            for cmd in stack
        ]
        return json.dumps(commands_list)

    @staticmethod
    def _deserialize_stack(
        json_str: str,
    ) -> tuple[UndoCommandPersistenceDTO, ...]:
        """Deserialize JSON string to undo/redo stack.

        Args:
            json_str: JSON string representation

        Returns:
            Tuple of UndoCommandPersistenceDTO

        Raises:
            json.JSONDecodeError: If JSON is invalid
            KeyError: If required keys missing from JSON
        """
        commands_list = json.loads(json_str)

        # Convert list of dicts back to tuple of DTOs
        commands = tuple(
            UndoCommandPersistenceDTO(
                command_type=cmd["command_type"],
                state_data=cmd["state_data"],
                timestamp=cmd["timestamp"],
            )
            for cmd in commands_list
        )
        return commands

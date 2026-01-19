"""SQLite implementation of project repository."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.infrastructure.persistence.sqlite_base import SqliteConnection


class SqliteProjectRepository(IProjectRepository):
    """SQLite implementation of project repository.

    Stores projects in a SQLite database separate from config.db.

    Database schema:
    - projects table: Project metadata
    - field_values table: Field values for each project

    Example:
        repo = SqliteProjectRepository(db_path="projects.db")
        result = repo.save(project)
        if isinstance(result, Success):
            print("Project saved")
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize repository.

        Args:
            db_path: Path to projects SQLite database
        """
        if not isinstance(db_path, (str, Path)):
            raise TypeError("db_path must be a string or Path")

        self.db_path = Path(db_path)
        self._connection = SqliteConnection(self.db_path)

        # Create tables if database is new
        self._ensure_schema()

    def save(self, project: Project) -> Result[None, str]:
        """Save or update a project.

        Args:
            project: Project to save

        Returns:
            Success(None) if saved, Failure(error) otherwise
        """
        if not isinstance(project, Project):
            return Failure("project must be a Project instance")

        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Check if project exists
                cursor.execute(
                    "SELECT 1 FROM projects WHERE project_id = ?",
                    (str(project.id.value),),
                )
                exists = cursor.fetchone() is not None

                if exists:
                    # Update existing project
                    cursor.execute(
                        """
                        UPDATE projects
                        SET name = ?, entity_definition_id = ?, description = ?,
                            file_path = ?, modified_at = ?
                        WHERE project_id = ?
                        """,
                        (
                            project.name,
                            project.entity_definition_id.value,
                            project.description,
                            project.file_path,
                            project.modified_at.isoformat(),
                            str(project.id.value),
                        ),
                    )

                    # Delete existing field values
                    cursor.execute(
                        "DELETE FROM field_values WHERE project_id = ?",
                        (str(project.id.value),),
                    )
                else:
                    # Insert new project
                    cursor.execute(
                        """
                        INSERT INTO projects
                        (project_id, name, entity_definition_id, description,
                         file_path, created_at, modified_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(project.id.value),
                            project.name,
                            project.entity_definition_id.value,
                            project.description,
                            project.file_path,
                            project.created_at.isoformat(),
                            project.modified_at.isoformat(),
                        ),
                    )

                # Insert field values
                for field_id, field_value in project.field_values.items():
                    cursor.execute(
                        """
                        INSERT INTO field_values
                        (project_id, field_id, value, is_computed, computed_from,
                         is_override, original_computed_value)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(project.id.value),
                            field_id.value,
                            json.dumps(field_value.value),
                            field_value.is_computed,
                            field_value.computed_from,
                            field_value.is_override,
                            json.dumps(field_value.original_computed_value)
                            if field_value.original_computed_value is not None
                            else None,
                        ),
                    )

                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error saving project: {str(e)}")

    def get_by_id(self, project_id: ProjectId) -> Result[Optional[Project], str]:
        """Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Success(Project) if found, Success(None) if not found, Failure(error) on error
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Load project metadata
                cursor.execute(
                    "SELECT * FROM projects WHERE project_id = ?",
                    (str(project_id.value),),
                )
                project_row = cursor.fetchone()

                if project_row is None:
                    return Success(None)

                # Load field values
                cursor.execute(
                    "SELECT * FROM field_values WHERE project_id = ?",
                    (str(project_id.value),),
                )
                value_rows = cursor.fetchall()

                # Build field_values dict
                field_values = {}
                for row in value_rows:
                    field_id = FieldDefinitionId(row["field_id"])
                    value = json.loads(row["value"])
                    original_computed_value = (
                        json.loads(row["original_computed_value"])
                        if row["original_computed_value"]
                        else None
                    )

                    field_value = FieldValue(
                        field_id=field_id,
                        value=value,
                        is_computed=bool(row["is_computed"]),
                        computed_from=row["computed_from"],
                        is_override=bool(row["is_override"]),
                        original_computed_value=original_computed_value,
                    )
                    field_values[field_id] = field_value

                # Build Project
                project = Project(
                    id=project_id,
                    name=project_row["name"],
                    entity_definition_id=EntityDefinitionId(
                        project_row["entity_definition_id"]
                    ),
                    field_values=field_values,
                    description=project_row["description"],
                    file_path=project_row["file_path"],
                    created_at=datetime.fromisoformat(project_row["created_at"]),
                    modified_at=datetime.fromisoformat(project_row["modified_at"]),
                )

                return Success(project)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error loading project: {str(e)}")

    def get_all(self) -> Result[list, str]:
        """Get all projects.

        Returns:
            Success(list of Projects) if successful, Failure(error) otherwise
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT project_id FROM projects ORDER BY modified_at DESC"
                )
                project_ids = [
                    ProjectId(self._parse_uuid(row["project_id"]))
                    for row in cursor.fetchall()
                ]

                # Load each project
                projects = []
                for project_id in project_ids:
                    result = self.get_by_id(project_id)
                    if isinstance(result, Success) and result.value is not None:
                        projects.append(result.value)

                return Success(projects)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error loading projects: {str(e)}")

    def delete(self, project_id: ProjectId) -> Result[None, str]:
        """Delete a project.

        Args:
            project_id: Project ID

        Returns:
            Success(None) if deleted, Failure(error) otherwise
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Delete field values first (foreign key)
                cursor.execute(
                    "DELETE FROM field_values WHERE project_id = ?",
                    (str(project_id.value),),
                )

                # Delete project
                cursor.execute(
                    "DELETE FROM projects WHERE project_id = ?",
                    (str(project_id.value),),
                )

                if cursor.rowcount == 0:
                    return Failure(f"Project '{project_id.value}' not found")

                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error deleting project: {str(e)}")

    def exists(self, project_id: ProjectId) -> Result[bool, str]:
        """Check if project exists.

        Args:
            project_id: Project ID

        Returns:
            Success(True) if exists, Success(False) if not, Failure(error) on error
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM projects WHERE project_id = ? LIMIT 1",
                    (str(project_id.value),),
                )
                exists = cursor.fetchone() is not None
                return Success(exists)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error checking project existence: {str(e)}")

    def get_recent(self, limit: int = 10) -> Result[list, str]:
        """Get recent projects ordered by modification date.

        Args:
            limit: Maximum number of projects to return (default 10)

        Returns:
            Success(list of Projects) if successful, Failure(error) otherwise
        """
        if not isinstance(limit, int) or limit <= 0:
            return Failure("limit must be a positive integer")

        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT project_id FROM projects
                    ORDER BY modified_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                project_ids = [
                    ProjectId(self._parse_uuid(row["project_id"]))
                    for row in cursor.fetchall()
                ]

                # Load each project
                projects = []
                for project_id in project_ids:
                    result = self.get_by_id(project_id)
                    if isinstance(result, Success) and result.value is not None:
                        projects.append(result.value)

                return Success(projects)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error loading recent projects: {str(e)}")

    def _ensure_schema(self) -> None:
        """Ensure database schema exists.

        Creates tables if they don't exist.
        """
        # Create database file if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.touch(exist_ok=True)

        with self._connection as conn:
            cursor = conn.cursor()

            # Create projects table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    entity_definition_id TEXT NOT NULL,
                    description TEXT,
                    file_path TEXT,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL
                )
                """
            )

            # Create field_values table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS field_values (
                    project_id TEXT NOT NULL,
                    field_id TEXT NOT NULL,
                    value TEXT NOT NULL,
                    is_computed INTEGER NOT NULL DEFAULT 0,
                    computed_from TEXT,
                    is_override INTEGER NOT NULL DEFAULT 0,
                    original_computed_value TEXT,
                    PRIMARY KEY (project_id, field_id),
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                        ON DELETE CASCADE
                )
                """
            )

            # Create index for faster queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_projects_modified
                ON projects(modified_at DESC)
                """
            )

    @staticmethod
    def _parse_uuid(uuid_str: str) -> Any:
        """Parse UUID string to UUID object.

        Args:
            uuid_str: UUID as string

        Returns:
            UUID object
        """
        from uuid import UUID

        return UUID(uuid_str)

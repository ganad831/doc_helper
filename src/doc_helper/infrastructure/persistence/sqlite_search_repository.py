"""SQLite implementation of search repository.

ADR-026: Search Architecture
- Read-only search operations
- Joins schema database (config.db) with project database (project.db)
- Case-insensitive partial matching on field labels, IDs, and values
"""

import json
import sqlite3
from pathlib import Path
from typing import Any

from doc_helper.application.search import ISearchRepository
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.infrastructure.persistence.sqlite_base import SqliteConnection


class SqliteSearchRepository(ISearchRepository):
    """SQLite implementation of search repository.

    ADR-026: Search Architecture
    - Searches across schema database (field definitions) and project database (field values)
    - Uses ATTACH DATABASE to join both databases in a single query
    - Returns raw dict data for application layer to map to DTOs

    Database schema:
    - Schema DB (config.db): entities, fields tables
    - Project DB (project.db): field_values table

    Example:
        repo = SqliteSearchRepository(
            project_db_path="projects/my_project/project.db",
            schema_db_path="app_types/soil_investigation/config.db"
        )
        result = repo.search_fields(
            project_id="proj-123",
            search_term="location",
            limit=50
        )
        if isinstance(result, Success):
            for row in result.value:
                print(f"{row['field_label']}: {row['current_value']}")
    """

    def __init__(self, project_db_path: str | Path, schema_db_path: str | Path) -> None:
        """Initialize search repository.

        Args:
            project_db_path: Path to project database (project.db)
            schema_db_path: Path to schema database (config.db)

        Raises:
            TypeError: If paths are not strings or Path objects
            FileNotFoundError: If databases don't exist
        """
        if not isinstance(project_db_path, (str, Path)):
            raise TypeError("project_db_path must be a string or Path")
        if not isinstance(schema_db_path, (str, Path)):
            raise TypeError("schema_db_path must be a string or Path")

        self.project_db_path = Path(project_db_path)
        self.schema_db_path = Path(schema_db_path)

        # Verify databases exist
        if not self.project_db_path.exists():
            raise FileNotFoundError(f"Project database not found: {project_db_path}")
        if not self.schema_db_path.exists():
            raise FileNotFoundError(f"Schema database not found: {schema_db_path}")

        self._connection = SqliteConnection(self.project_db_path)

    def search_fields(
        self,
        project_id: str,
        search_term: str,
        limit: int = 100,
    ) -> Result[list[dict], str]:
        """Search for fields matching the search term within a project.

        ADR-026: Searches field labels, field IDs, and field values.
        Returns results ordered by match type (label matches first, then value matches).

        Implementation:
        1. Attach schema database to access field definitions
        2. Join entities, fields, and field_values tables
        3. Filter by project_id and search term (case-insensitive partial match)
        4. Order by match relevance: label matches, then field_id matches, then value matches
        5. Limit results to prevent performance issues

        Args:
            project_id: Project ID to search within
            search_term: Search term (case-insensitive partial match)
            limit: Maximum number of results to return

        Returns:
            Success(list[dict]) containing matching fields with keys:
                - field_id: str
                - field_label: str
                - entity_id: str
                - entity_name: str
                - current_value: Any | None
                - field_path: str (entity_id.field_id)
                - match_type: str ("label", "value", "field_id")
            Failure(error) if search failed

        Example:
            result = repo.search_fields(
                project_id="proj-123",
                search_term="location"
            )
        """
        if not isinstance(project_id, str) or not project_id:
            return Failure("project_id must be a non-empty string")
        if not isinstance(search_term, str) or not search_term:
            return Failure("search_term must be a non-empty string")
        if not isinstance(limit, int) or limit <= 0:
            return Failure("limit must be a positive integer")

        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Attach schema database for joins
                cursor.execute(
                    "ATTACH DATABASE ? AS schema_db",
                    (str(self.schema_db_path),)
                )

                # Build search query
                # Match priority: label > field_id > value
                search_pattern = f"%{search_term}%"

                query = """
                    WITH search_results AS (
                        SELECT
                            f.id AS field_id,
                            f.label AS field_label,
                            f.entity_id AS entity_id,
                            e.name AS entity_name,
                            fv.value AS current_value,
                            e.name || '.' || f.id AS field_path,
                            CASE
                                WHEN f.label LIKE ? COLLATE NOCASE THEN 'label'
                                WHEN f.id LIKE ? COLLATE NOCASE THEN 'field_id'
                                WHEN fv.value LIKE ? COLLATE NOCASE THEN 'value'
                                ELSE 'none'
                            END AS match_type
                        FROM schema_db.fields f
                        INNER JOIN schema_db.entities e ON f.entity_id = e.id
                        LEFT JOIN field_values fv ON f.id = fv.field_id AND fv.project_id = ?
                        WHERE
                            f.label LIKE ? COLLATE NOCASE
                            OR f.id LIKE ? COLLATE NOCASE
                            OR fv.value LIKE ? COLLATE NOCASE
                    )
                    SELECT * FROM search_results
                    WHERE match_type != 'none'
                    ORDER BY
                        CASE match_type
                            WHEN 'label' THEN 1
                            WHEN 'field_id' THEN 2
                            WHEN 'value' THEN 3
                        END,
                        field_label
                    LIMIT ?
                """

                cursor.execute(
                    query,
                    (
                        search_pattern,  # label match check
                        search_pattern,  # field_id match check
                        search_pattern,  # value match check
                        project_id,      # project filter
                        search_pattern,  # label WHERE clause
                        search_pattern,  # field_id WHERE clause
                        search_pattern,  # value WHERE clause
                        limit,           # result limit
                    ),
                )

                rows = cursor.fetchall()

                # Detach schema database
                cursor.execute("DETACH DATABASE schema_db")

                # Convert rows to list of dicts
                results = []
                for row in rows:
                    # Deserialize value if it's JSON
                    current_value = self._deserialize_value(row["current_value"])

                    results.append({
                        "field_id": row["field_id"],
                        "field_label": row["field_label"],
                        "entity_id": row["entity_id"],
                        "entity_name": row["entity_name"],
                        "current_value": current_value,
                        "field_path": row["field_path"],
                        "match_type": row["match_type"],
                    })

                return Success(results)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error searching fields: {str(e)}")

    @staticmethod
    def _deserialize_value(value_str: str | None) -> Any:
        """Deserialize a JSON string to value.

        Args:
            value_str: JSON string to deserialize (or None)

        Returns:
            Deserialized value, or None if value_str is None
        """
        if value_str is None:
            return None

        try:
            return json.loads(value_str)
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, return as-is (plain string)
            return value_str

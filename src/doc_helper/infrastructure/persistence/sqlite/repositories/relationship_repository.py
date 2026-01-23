"""SQLite implementation of relationship repository (Phase 6A - ADR-022).

Provides persistence for RelationshipDefinition entities.
ADD-ONLY semantics: relationships can be created but not updated or deleted.
"""

from pathlib import Path
import sqlite3

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.relationship_repository import IRelationshipRepository
from doc_helper.domain.schema.relationship_type import RelationshipType
from doc_helper.domain.schema.schema_ids import (
    EntityDefinitionId,
    RelationshipDefinitionId,
)
from doc_helper.infrastructure.persistence.sqlite_base import SqliteConnection


class SqliteRelationshipRepository(IRelationshipRepository):
    """SQLite implementation of relationship repository.

    ADR-022 Compliance:
    - ADD-ONLY semantics (save only, no update/delete)
    - Validates entity references exist before save
    - Returns Result[T, E] for error handling

    Database Schema (relationships table):
        - id TEXT PRIMARY KEY
        - source_entity_id TEXT NOT NULL (FK to entities.id)
        - target_entity_id TEXT NOT NULL (FK to entities.id)
        - relationship_type TEXT NOT NULL (CONTAINS, REFERENCES, ASSOCIATES)
        - name_key TEXT NOT NULL
        - description_key TEXT
        - inverse_name_key TEXT
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize repository.

        Args:
            db_path: Path to SQLite database file

        Raises:
            TypeError: If db_path is not string or Path
            FileNotFoundError: If database file does not exist
        """
        if not isinstance(db_path, (str, Path)):
            raise TypeError("db_path must be a string or Path")

        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

        self._connection = SqliteConnection(self.db_path)

        # Ensure relationships table exists
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Ensure relationships table exists in database.

        Creates the table if it doesn't exist, allowing safe initialization
        for existing databases that predate Phase 6A.
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS relationships (
                        id TEXT PRIMARY KEY,
                        source_entity_id TEXT NOT NULL,
                        target_entity_id TEXT NOT NULL,
                        relationship_type TEXT NOT NULL,
                        name_key TEXT NOT NULL,
                        description_key TEXT,
                        inverse_name_key TEXT,
                        FOREIGN KEY (source_entity_id) REFERENCES entities(id) ON DELETE RESTRICT,
                        FOREIGN KEY (target_entity_id) REFERENCES entities(id) ON DELETE RESTRICT,
                        CHECK (relationship_type IN ('CONTAINS', 'REFERENCES', 'ASSOCIATES')),
                        CHECK (source_entity_id != target_entity_id)
                    )
                """)

                # Create indexes if they don't exist
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_relationships_source
                    ON relationships(source_entity_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_relationships_target
                    ON relationships(target_entity_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_relationships_type
                    ON relationships(relationship_type)
                """)
        except sqlite3.Error:
            # Table creation failed - will be caught on first operation
            pass

    # -------------------------------------------------------------------------
    # Read Operations
    # -------------------------------------------------------------------------

    def get_by_id(
        self, relationship_id: RelationshipDefinitionId
    ) -> Result[RelationshipDefinition, str]:
        """Get relationship definition by ID."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, source_entity_id, target_entity_id, relationship_type,
                           name_key, description_key, inverse_name_key
                    FROM relationships
                    WHERE id = ?
                    """,
                    (str(relationship_id.value),),
                )
                row = cursor.fetchone()

                if not row:
                    return Failure(f"Relationship '{relationship_id.value}' not found")

                relationship = self._row_to_relationship(row)
                return Success(relationship)

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    def get_all(self) -> Result[tuple[RelationshipDefinition, ...], str]:
        """Get all relationship definitions."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, source_entity_id, target_entity_id, relationship_type,
                           name_key, description_key, inverse_name_key
                    FROM relationships
                    ORDER BY id
                    """
                )
                rows = cursor.fetchall()

                relationships = tuple(
                    self._row_to_relationship(row) for row in rows
                )
                return Success(relationships)

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    def get_by_source_entity(
        self, entity_id: EntityDefinitionId
    ) -> Result[tuple[RelationshipDefinition, ...], str]:
        """Get relationships where the given entity is the source."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, source_entity_id, target_entity_id, relationship_type,
                           name_key, description_key, inverse_name_key
                    FROM relationships
                    WHERE source_entity_id = ?
                    ORDER BY id
                    """,
                    (str(entity_id.value),),
                )
                rows = cursor.fetchall()

                relationships = tuple(
                    self._row_to_relationship(row) for row in rows
                )
                return Success(relationships)

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    def get_by_target_entity(
        self, entity_id: EntityDefinitionId
    ) -> Result[tuple[RelationshipDefinition, ...], str]:
        """Get relationships where the given entity is the target."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, source_entity_id, target_entity_id, relationship_type,
                           name_key, description_key, inverse_name_key
                    FROM relationships
                    WHERE target_entity_id = ?
                    ORDER BY id
                    """,
                    (str(entity_id.value),),
                )
                rows = cursor.fetchall()

                relationships = tuple(
                    self._row_to_relationship(row) for row in rows
                )
                return Success(relationships)

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    def get_by_entity(
        self, entity_id: EntityDefinitionId
    ) -> Result[tuple[RelationshipDefinition, ...], str]:
        """Get all relationships involving the given entity (source or target)."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, source_entity_id, target_entity_id, relationship_type,
                           name_key, description_key, inverse_name_key
                    FROM relationships
                    WHERE source_entity_id = ? OR target_entity_id = ?
                    ORDER BY id
                    """,
                    (str(entity_id.value), str(entity_id.value)),
                )
                rows = cursor.fetchall()

                relationships = tuple(
                    self._row_to_relationship(row) for row in rows
                )
                return Success(relationships)

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    def exists(self, relationship_id: RelationshipDefinitionId) -> bool:
        """Check if relationship definition exists."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM relationships WHERE id = ?",
                    (str(relationship_id.value),),
                )
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    # -------------------------------------------------------------------------
    # Write Operations (ADD-ONLY)
    # -------------------------------------------------------------------------

    def save(self, relationship: RelationshipDefinition) -> Result[None, str]:
        """Save new relationship definition (ADD-ONLY).

        Validates:
            - Relationship ID must be unique
            - Source entity must exist
            - Target entity must exist
        """
        try:
            # Check if relationship already exists
            if self.exists(relationship.id):
                return Failure(
                    f"Relationship '{relationship.id.value}' already exists. "
                    "Relationships are ADD-ONLY and cannot be updated."
                )

            with self._connection as conn:
                cursor = conn.cursor()

                # Validate source entity exists
                cursor.execute(
                    "SELECT 1 FROM entities WHERE id = ?",
                    (str(relationship.source_entity_id.value),),
                )
                if not cursor.fetchone():
                    return Failure(
                        f"Source entity '{relationship.source_entity_id.value}' does not exist"
                    )

                # Validate target entity exists
                cursor.execute(
                    "SELECT 1 FROM entities WHERE id = ?",
                    (str(relationship.target_entity_id.value),),
                )
                if not cursor.fetchone():
                    return Failure(
                        f"Target entity '{relationship.target_entity_id.value}' does not exist"
                    )

                # Insert relationship
                cursor.execute(
                    """
                    INSERT INTO relationships (
                        id, source_entity_id, target_entity_id, relationship_type,
                        name_key, description_key, inverse_name_key
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(relationship.id.value),
                        str(relationship.source_entity_id.value),
                        str(relationship.target_entity_id.value),
                        relationship.relationship_type.value,
                        relationship.name_key.key,
                        relationship.description_key.key if relationship.description_key else None,
                        relationship.inverse_name_key.key if relationship.inverse_name_key else None,
                    ),
                )

                return Success(None)

        except sqlite3.IntegrityError as e:
            return Failure(f"Integrity error: {e}")
        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    # NOTE: No update() method - ADD-ONLY semantics (ADR-022)
    # NOTE: No delete() method - ADD-ONLY semantics (ADR-022)

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    def _row_to_relationship(self, row: sqlite3.Row) -> RelationshipDefinition:
        """Convert database row to RelationshipDefinition.

        Args:
            row: SQLite Row object

        Returns:
            RelationshipDefinition domain object
        """
        return RelationshipDefinition(
            id=RelationshipDefinitionId(row["id"]),
            source_entity_id=EntityDefinitionId(row["source_entity_id"]),
            target_entity_id=EntityDefinitionId(row["target_entity_id"]),
            relationship_type=RelationshipType(row["relationship_type"]),
            name_key=TranslationKey(row["name_key"]),
            description_key=(
                TranslationKey(row["description_key"])
                if row["description_key"]
                else None
            ),
            inverse_name_key=(
                TranslationKey(row["inverse_name_key"])
                if row["inverse_name_key"]
                else None
            ),
        )

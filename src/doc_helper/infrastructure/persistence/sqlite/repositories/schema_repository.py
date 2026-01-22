"""SQLite implementation of schema repository (Phase 2 Step 2).

Provides persistence for EntityDefinition and FieldDefinition.
Phase 2 Step 2 scope: CREATE operations only.
"""

from typing import Optional
from pathlib import Path
import sqlite3

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.infrastructure.persistence.sqlite_base import SqliteConnection


class SqliteSchemaRepository(ISchemaRepository):
    """SQLite implementation of schema repository.

    Phase 2 Step 2 Scope:
    - Read operations (get_all, get_by_id, exists, etc.)
    - CREATE operations (save new entities)

    NOT in Step 2:
    - UPDATE operations (modify existing entities)
    - DELETE operations (remove entities)

    Database Schema (config.db):
        entities:
            - id TEXT PRIMARY KEY
            - name_key TEXT NOT NULL
            - description_key TEXT
            - is_root_entity INTEGER (0 or 1)
            - parent_entity_id TEXT
            - display_order INTEGER

        fields:
            - id TEXT PRIMARY KEY
            - entity_id TEXT NOT NULL (FK to entities.id)
            - field_type TEXT NOT NULL
            - label_key TEXT NOT NULL
            - help_text_key TEXT
            - required INTEGER (0 or 1)
            - default_value TEXT
            - display_order INTEGER
            - formula TEXT
            - lookup_entity_id TEXT
            - lookup_display_field TEXT
            - child_entity_id TEXT
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

    # -------------------------------------------------------------------------
    # Read Operations (Phase 1 + Phase 2 Step 1)
    # -------------------------------------------------------------------------

    def get_by_id(self, entity_id: EntityDefinitionId) -> Result[EntityDefinition, str]:
        """Get entity definition by ID."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, name_key, description_key, is_root_entity, parent_entity_id
                    FROM entities
                    WHERE id = ?
                    """,
                    (str(entity_id.value),),
                )
                row = cursor.fetchone()

                if not row:
                    return Failure(f"Entity '{entity_id.value}' not found")

                # Load fields for this entity
                fields_result = self._load_fields_for_entity(cursor, entity_id)
                if fields_result.is_failure():
                    return Failure(f"Failed to load fields: {fields_result.error}")

                # Construct EntityDefinition
                entity = EntityDefinition(
                    id=entity_id,
                    name_key=TranslationKey(row[1]),
                    description_key=TranslationKey(row[2]) if row[2] else None,
                    fields=fields_result.value,
                    is_root_entity=bool(row[3]),
                    parent_entity_id=(
                        EntityDefinitionId(row[4]) if row[4] else None
                    ),
                )

                return Success(entity)

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    def get_all(self) -> Result[tuple, str]:
        """Get all entity definitions."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id
                    FROM entities
                    ORDER BY display_order, id
                    """
                )
                rows = cursor.fetchall()

                entities = []
                for row in rows:
                    entity_id = EntityDefinitionId(row[0])
                    entity_result = self.get_by_id(entity_id)
                    if entity_result.is_success():
                        entities.append(entity_result.value)

                return Success(tuple(entities))

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    def get_root_entity(self) -> Result[EntityDefinition, str]:
        """Get the root entity definition."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id
                    FROM entities
                    WHERE is_root_entity = 1
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()

                if not row:
                    return Failure("No root entity found")

                return self.get_by_id(EntityDefinitionId(row[0]))

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    def exists(self, entity_id: EntityDefinitionId) -> bool:
        """Check if entity definition exists."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM entities WHERE id = ?",
                    (str(entity_id.value),),
                )
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def get_child_entities(
        self, parent_entity_id: EntityDefinitionId
    ) -> Result[tuple, str]:
        """Get all child entities of a parent entity."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id
                    FROM entities
                    WHERE parent_entity_id = ?
                    ORDER BY display_order, id
                    """,
                    (str(parent_entity_id.value),),
                )
                rows = cursor.fetchall()

                children = []
                for row in rows:
                    child_id = EntityDefinitionId(row[0])
                    child_result = self.get_by_id(child_id)
                    if child_result.is_success():
                        children.append(child_result.value)

                return Success(tuple(children))

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    # -------------------------------------------------------------------------
    # Write Operations (Phase 2 Step 2: CREATE only)
    # -------------------------------------------------------------------------

    def save(self, entity: EntityDefinition) -> Result[None, str]:
        """Save entity definition (create new or add fields to existing).

        Phase 2 Step 2 Behavior:
        - If entity does NOT exist: CREATE new entity with all fields
        - If entity EXISTS: ADD only new fields (does not modify existing fields)

        Phase 2 Step 3: Will add full UPDATE support (modify existing fields/entity metadata)

        Args:
            entity: Entity definition to save

        Returns:
            Result with None on success or error message

        Validation:
            - New entities: Entity ID must not exist
            - Existing entities: Can only add NEW fields (no field overwrites)
            - All fields must have valid field types
        """
        try:
            entity_exists = self.exists(entity.id)

            with self._connection as conn:
                cursor = conn.cursor()

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                try:
                    if not entity_exists:
                        # CREATE: Insert new entity + all fields
                        cursor.execute(
                            """
                            INSERT INTO entities (id, name_key, description_key, is_root_entity, parent_entity_id, display_order)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                str(entity.id.value),
                                entity.name_key.key,
                                entity.description_key.key if entity.description_key else None,
                                1 if entity.is_root_entity else 0,
                                str(entity.parent_entity_id.value) if entity.parent_entity_id else None,
                                0,  # Default display order
                            ),
                        )

                        # Insert all fields
                        for field_def in entity.get_all_fields():
                            self._insert_field(cursor, entity.id, field_def)

                    else:
                        # UPDATE (Phase 2 Step 2): Add NEW fields only
                        # Load existing field IDs
                        cursor.execute(
                            "SELECT id FROM fields WHERE entity_id = ?",
                            (str(entity.id.value),),
                        )
                        existing_field_ids = {row[0] for row in cursor.fetchall()}

                        # Insert only NEW fields (not already in database)
                        new_fields = [
                            field_def
                            for field_def in entity.get_all_fields()
                            if str(field_def.id.value) not in existing_field_ids
                        ]

                        if not new_fields:
                            cursor.execute("ROLLBACK")
                            return Failure(
                                f"No new fields to add. Entity '{entity.id.value}' already has all specified fields."
                            )

                        for field_def in new_fields:
                            self._insert_field(cursor, entity.id, field_def)

                    # Commit transaction
                    cursor.execute("COMMIT")

                    return Success(None)

                except sqlite3.Error as e:
                    cursor.execute("ROLLBACK")
                    return Failure(f"Failed to save entity: {e}")

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    def _load_fields_for_entity(
        self, cursor: sqlite3.Cursor, entity_id: EntityDefinitionId
    ) -> Result[dict, str]:
        """Load all fields for an entity.

        Args:
            cursor: Database cursor (from active connection)
            entity_id: Entity definition ID

        Returns:
            Result containing dict[FieldDefinitionId, FieldDefinition] or error
        """
        try:
            cursor.execute(
                """
                SELECT id, field_type, label_key, help_text_key, required, default_value,
                       formula, lookup_entity_id, lookup_display_field, child_entity_id
                FROM fields
                WHERE entity_id = ?
                ORDER BY display_order, id
                """,
                (str(entity_id.value),),
            )
            rows = cursor.fetchall()

            fields = {}
            for row in rows:
                field_id = FieldDefinitionId(row[0])
                field_type = FieldType(row[1])

                # Create FieldDefinition
                field_def = FieldDefinition(
                    id=field_id,
                    field_type=field_type,
                    label_key=TranslationKey(row[2]),
                    help_text_key=TranslationKey(row[3]) if row[3] else None,
                    required=bool(row[4]),
                    default_value=row[5],
                    formula=row[6],
                    lookup_entity_id=row[7],
                    lookup_display_field=row[8],
                    child_entity_id=row[9],
                    constraints=(),  # Load constraints separately if needed
                    options=(),  # Load options separately if needed
                    control_rules=(),  # Not loaded in Phase 2 Step 2
                )

                fields[field_id] = field_def

            return Success(fields)

        except sqlite3.Error as e:
            return Failure(f"Failed to load fields: {e}")

    def _insert_field(
        self,
        cursor: sqlite3.Cursor,
        entity_id: EntityDefinitionId,
        field_def: FieldDefinition,
    ) -> None:
        """Insert a field into the database.

        Args:
            cursor: Database cursor
            entity_id: Entity ID this field belongs to
            field_def: Field definition to insert

        Raises:
            sqlite3.Error: If insert fails
        """
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, help_text_key, required,
                                default_value, display_order, formula, lookup_entity_id,
                                lookup_display_field, child_entity_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(field_def.id.value),
                str(entity_id.value),
                field_def.field_type.value,
                field_def.label_key.key,
                field_def.help_text_key.key if field_def.help_text_key else None,
                1 if field_def.required else 0,
                field_def.default_value,
                0,  # Default display order
                field_def.formula,
                field_def.lookup_entity_id,
                field_def.lookup_display_field,
                field_def.child_entity_id,
            ),
        )

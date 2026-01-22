"""SQLite implementation of schema repository."""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.validation.constraints import (
    MaxLengthConstraint,
    MaxValueConstraint,
    MinLengthConstraint,
    MinValueConstraint,
    PatternConstraint,
    RequiredConstraint,
)
from doc_helper.infrastructure.persistence.sqlite_base import SqliteConnection


class SqliteSchemaRepository(ISchemaRepository):
    """SQLite implementation of schema repository.

    Loads schema from config.db SQLite database.

    Schema structure:
    - entities table: entity definitions
    - fields table: field definitions
    - validation_rules table: field constraints
    - field_options table: dropdown/radio options
    - formulas table: calculated field formulas

    Example:
        repo = SqliteSchemaRepository(db_path="app_types/soil_investigation/config.db")
        result = repo.get_by_id(EntityDefinitionId("project"))
        if isinstance(result, Success):
            entity = result.value
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize repository.

        Args:
            db_path: Path to config.db SQLite database
        """
        if not isinstance(db_path, (str, Path)):
            raise TypeError("db_path must be a string or Path")

        self.db_path = Path(db_path)
        self._connection = SqliteConnection(self.db_path)

        # Ensure database exists
        try:
            self._connection.ensure_exists()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Schema database not found: {db_path}") from e

    def get_by_id(
        self, entity_id: EntityDefinitionId
    ) -> Result[EntityDefinition, str]:
        """Get entity definition by ID.

        Args:
            entity_id: Entity definition ID

        Returns:
            Success(EntityDefinition) if found, Failure(error) otherwise
        """
        if not isinstance(entity_id, EntityDefinitionId):
            return Failure("entity_id must be an EntityDefinitionId")

        try:
            with self._connection as conn:
                # Load entity
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM entities WHERE id = ?", (entity_id.value,)
                )
                entity_row = cursor.fetchone()

                if entity_row is None:
                    return Failure(f"Entity '{entity_id.value}' not found")

                # Load fields
                fields = self._load_fields_for_entity(conn, entity_id)

                # Build EntityDefinition
                entity = EntityDefinition(
                    id=entity_id,
                    name_key=TranslationKey(entity_row["name"]),
                    description_key=TranslationKey(f"entity.{entity_row['name']}.description") if "description" in entity_row.keys() and entity_row["description"] else None,
                    fields={field.id: field for field in fields},
                )

                return Success(entity)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error loading entity: {str(e)}")

    def get_all(self) -> Result[tuple, str]:
        """Get all entity definitions.

        Returns:
            Success(tuple of EntityDefinition) if successful, Failure(error) otherwise
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM entities ORDER BY sort_order")
                entity_ids = [
                    EntityDefinitionId(row["id"].lower()) for row in cursor.fetchall()
                ]

                # Load each entity within same connection
                entities = []
                for entity_id in entity_ids:
                    # Load entity data directly (don't call get_by_id to avoid nested connections)
                    cursor.execute(
                        "SELECT * FROM entities WHERE id = ?", (entity_id.value,)
                    )
                    entity_row = cursor.fetchone()

                    if entity_row is not None:
                        fields = self._load_fields_for_entity(conn, entity_id)
                        entity = EntityDefinition(
                            id=entity_id,
                            name_key=TranslationKey(entity_row["name"]),
                            description_key=TranslationKey(f"entity.{entity_row['name']}.description") if "description" in entity_row.keys() and entity_row["description"] else None,
                            fields={field.id: field for field in fields},
                        )
                        entities.append(entity)

                return Success(tuple(entities))

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error loading entities: {str(e)}")

    def get_root_entity(self) -> Result[EntityDefinition, str]:
        """Get the root entity definition.

        The root entity is identified by entity_type = 'root' or the first entity
        in sort order.

        Returns:
            Success(EntityDefinition) if found, Failure(error) otherwise
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Try to find root entity by type
                cursor.execute(
                    "SELECT id FROM entities WHERE entity_type = 'root' LIMIT 1"
                )
                row = cursor.fetchone()

                if row is None:
                    # Fallback: get first entity by sort order
                    cursor.execute(
                        "SELECT id FROM entities ORDER BY sort_order LIMIT 1"
                    )
                    row = cursor.fetchone()

                if row is None:
                    return Failure("No entities found in schema")

                entity_id = EntityDefinitionId(row["id"].lower())

                # Load entity data directly (avoid nested connection)
                cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id.value,))
                entity_row = cursor.fetchone()

                if entity_row is None:
                    return Failure(f"Entity '{entity_id.value}' not found")

                # Load fields
                fields = self._load_fields_for_entity(conn, entity_id)

                # Build EntityDefinition
                entity = EntityDefinition(
                    id=entity_id,
                    name_key=TranslationKey(entity_row["name"]),
                    description_key=TranslationKey(f"entity.{entity_row['name']}.description") if "description" in entity_row.keys() and entity_row["description"] else None,
                    fields={field.id: field for field in fields},
                )

                return Success(entity)

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error loading root entity: {str(e)}")

    def exists(self, entity_id: EntityDefinitionId) -> bool:
        """Check if entity definition exists.

        Args:
            entity_id: Entity definition ID

        Returns:
            True if entity exists
        """
        if not isinstance(entity_id, EntityDefinitionId):
            return False

        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM entities WHERE id = ? LIMIT 1", (entity_id.value,)
                )
                return cursor.fetchone() is not None

        except (sqlite3.Error, Exception):
            return False

    def get_child_entities(
        self, parent_entity_id: EntityDefinitionId
    ) -> Result[tuple, str]:
        """Get all child entities of a parent entity.

        Child entities are entities referenced in TABLE fields.

        Args:
            parent_entity_id: Parent entity definition ID

        Returns:
            Success(tuple of EntityDefinition) if successful, Failure(error) otherwise
        """
        if not isinstance(parent_entity_id, EntityDefinitionId):
            return Failure("parent_entity_id must be an EntityDefinitionId")

        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Find TABLE fields in parent entity
                cursor.execute(
                    """
                    SELECT DISTINCT f.id, f.name, vo.table_entity_id
                    FROM fields f
                    LEFT JOIN validation_rules vr ON f.id = vr.field_id
                    LEFT JOIN (
                        SELECT field_id, json_extract(inline_options, '$.table_entity_id') as table_entity_id
                        FROM field_options
                    ) vo ON f.id = vo.field_id
                    WHERE f.entity_id = ? AND f.field_type = 'TABLE'
                    """,
                    (parent_entity_id.value,),
                )
                table_fields = cursor.fetchall()

                # Collect unique child entity IDs
                child_entity_ids = set()
                for row in table_fields:
                    table_entity_id = row["table_entity_id"]
                    if table_entity_id:
                        child_entity_ids.add(EntityDefinitionId(table_entity_id.lower()))

                # Load child entities within same connection
                children = []
                for entity_id in child_entity_ids:
                    cursor.execute(
                        "SELECT * FROM entities WHERE id = ?", (entity_id.value,)
                    )
                    entity_row = cursor.fetchone()

                    if entity_row is not None:
                        fields = self._load_fields_for_entity(conn, entity_id)
                        entity = EntityDefinition(
                            id=entity_id,
                            name_key=TranslationKey(entity_row["name"]),
                            description_key=TranslationKey(f"entity.{entity_row['name']}.description") if "description" in entity_row.keys() and entity_row["description"] else None,
                            fields={field.id: field for field in fields},
                        )
                        children.append(entity)

                return Success(tuple(children))

        except sqlite3.Error as e:
            return Failure(f"Database error: {str(e)}")
        except Exception as e:
            return Failure(f"Error loading child entities: {str(e)}")

    def _load_fields_for_entity(
        self, conn: sqlite3.Connection, entity_id: EntityDefinitionId
    ) -> tuple[FieldDefinition, ...]:
        """Load all field definitions for an entity.

        Args:
            conn: Active database connection
            entity_id: Entity ID to load fields for

        Returns:
            Tuple of FieldDefinition objects
        """
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM fields
            WHERE entity_id = ?
            ORDER BY sort_order
            """,
            (entity_id.value,),
        )
        field_rows = cursor.fetchall()

        fields = []
        for row in field_rows:
            # Normalize field ID to lowercase
            field_id = FieldDefinitionId(row["id"].lower())

            # Parse field type
            try:
                field_type = FieldType(row["field_type"])
            except ValueError:
                # Skip unknown field types
                continue

            # Load constraints
            constraints = self._load_constraints_for_field(conn, field_id)

            # Load formula if CALCULATED field
            formula = None
            if field_type == FieldType.CALCULATED:
                formula = self._load_formula_for_field(conn, field_id)

            # Load options if DROPDOWN/RADIO field
            options = None
            if field_type in (FieldType.DROPDOWN, FieldType.RADIO):
                options = self._load_options_for_field(conn, field_id)

            # Build FieldDefinition
            field = FieldDefinition(
                id=field_id,
                field_type=field_type,
                label_key=TranslationKey(f"field.{row['name']}"),
                constraints=constraints,
                formula=formula,
                options=options if options else (),
            )
            fields.append(field)

        return tuple(fields)

    def _load_constraints_for_field(
        self, conn: sqlite3.Connection, field_id: FieldDefinitionId
    ) -> tuple:
        """Load constraints for a field.

        Args:
            conn: Active database connection
            field_id: Field ID to load constraints for

        Returns:
            Tuple of constraint objects
        """
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM validation_rules WHERE field_id = ?", (field_id.value,)
        )
        rule_row = cursor.fetchone()

        if rule_row is None:
            return ()

        constraints = []

        # Required constraint
        if "required" in rule_row.keys() and rule_row["required"]:
            constraints.append(RequiredConstraint())

        # Min/Max value constraints
        if "min_value" in rule_row.keys():
            min_value = rule_row["min_value"]
            if min_value is not None:
                constraints.append(MinValueConstraint(min_value=min_value))

        if "max_value" in rule_row.keys():
            max_value = rule_row["max_value"]
            if max_value is not None:
                constraints.append(MaxValueConstraint(max_value=max_value))

        # Min/Max length constraints
        if "min_length" in rule_row.keys():
            min_length = rule_row["min_length"]
            if min_length is not None:
                constraints.append(MinLengthConstraint(min_length=min_length))

        if "max_length" in rule_row.keys():
            max_length = rule_row["max_length"]
            if max_length is not None:
                constraints.append(MaxLengthConstraint(max_length=max_length))

        # Pattern constraint
        if "pattern" in rule_row.keys():
            pattern = rule_row["pattern"]
            if pattern:
                constraints.append(PatternConstraint(pattern=pattern))

        return tuple(constraints)

    def _load_formula_for_field(
        self, conn: sqlite3.Connection, field_id: FieldDefinitionId
    ) -> Optional[str]:
        """Load formula expression for a field.

        Args:
            conn: Active database connection
            field_id: Field ID to load formula for

        Returns:
            Formula expression string or None
        """
        cursor = conn.cursor()
        cursor.execute(
            "SELECT expression FROM formulas WHERE field_id = ?", (field_id.value,)
        )
        row = cursor.fetchone()
        return row["expression"] if row else None

    def _load_options_for_field(
        self, conn: sqlite3.Connection, field_id: FieldDefinitionId
    ) -> Optional[tuple]:
        """Load options for dropdown/radio field.

        Args:
            conn: Active database connection
            field_id: Field ID to load options for

        Returns:
            Tuple of option strings or None
        """
        cursor = conn.cursor()
        cursor.execute(
            "SELECT inline_options, dropdown_id FROM field_options WHERE field_id = ?",
            (field_id.value,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        # Try inline options first
        inline_options = row["inline_options"]
        if inline_options:
            try:
                options_data = json.loads(inline_options)
                if isinstance(options_data, list):
                    return tuple(options_data)
            except json.JSONDecodeError:
                pass

        # Try dropdown_id reference
        dropdown_id = row["dropdown_id"]
        if dropdown_id:
            cursor.execute(
                "SELECT value FROM dropdown_options WHERE dropdown_id = ? ORDER BY sort_order",
                (dropdown_id,),
            )
            options = [opt_row["value"] for opt_row in cursor.fetchall()]
            if options:
                return tuple(options)

        return None

    # -------------------------------------------------------------------------
    # Write Operations (Schema Designer - Phase 2 Step 3)
    # -------------------------------------------------------------------------

    def save(self, entity: EntityDefinition) -> Result[None, str]:
        """Save entity definition (create new or update existing).

        Args:
            entity: Entity definition to save

        Returns:
            Result with None on success or error message
        """
        try:
            entity_exists = self.exists(entity.id)

            with self._connection as conn:
                cursor = conn.cursor()

                if not entity_exists:
                    # CREATE: Insert new entity
                    cursor.execute(
                        """
                        INSERT INTO entities (id, name, entity_type, sort_order)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            entity.id.value,
                            entity.name_key.key.replace("entity.", "").replace(".name", ""),
                            "collection",  # Default type
                            0,  # Default sort order
                        ),
                    )

                    # Insert all fields
                    for field_def in entity.get_all_fields():
                        self._insert_field(cursor, entity.id, field_def)

                else:
                    # UPDATE: Update entity metadata and fields
                    cursor.execute(
                        """
                        UPDATE entities
                        SET name = ?
                        WHERE id = ?
                        """,
                        (
                            entity.name_key.key.replace("entity.", "").replace(".name", ""),
                            entity.id.value,
                        ),
                    )

                    # Get existing field IDs
                    cursor.execute(
                        "SELECT id FROM fields WHERE entity_id = ?",
                        (entity.id.value,),
                    )
                    existing_field_ids = {row["id"] for row in cursor.fetchall()}

                    # Insert new fields, update existing
                    for field_def in entity.get_all_fields():
                        if field_def.id.value in existing_field_ids:
                            self._update_field(cursor, entity.id, field_def)
                        else:
                            self._insert_field(cursor, entity.id, field_def)

                conn.commit()
                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Failed to save entity: {e}")
        except Exception as e:
            return Failure(f"Error saving entity: {str(e)}")

    def update(self, entity: EntityDefinition) -> Result[None, str]:
        """Update entity definition metadata.

        Args:
            entity: Entity definition with updated metadata

        Returns:
            Result with None on success or error message
        """
        if not self.exists(entity.id):
            return Failure(f"Entity '{entity.id.value}' does not exist")

        try:
            with self._connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE entities
                    SET name = ?
                    WHERE id = ?
                    """,
                    (
                        entity.name_key.key.replace("entity.", "").replace(".name", ""),
                        entity.id.value,
                    ),
                )
                conn.commit()
                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Failed to update entity: {e}")
        except Exception as e:
            return Failure(f"Error updating entity: {str(e)}")

    def delete(self, entity_id: EntityDefinitionId) -> Result[None, str]:
        """Delete entity definition from schema.

        Args:
            entity_id: Entity definition ID to delete

        Returns:
            Result with None on success or error message
        """
        if not self.exists(entity_id):
            return Failure(f"Entity '{entity_id.value}' does not exist")

        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Delete validation rules for this entity's fields
                try:
                    cursor.execute(
                        """
                        DELETE FROM validation_rules
                        WHERE field_id IN (SELECT id FROM fields WHERE entity_id = ?)
                        """,
                        (entity_id.value,),
                    )
                except sqlite3.OperationalError:
                    pass  # Table might not exist

                # Delete field options
                try:
                    cursor.execute(
                        """
                        DELETE FROM field_options
                        WHERE field_id IN (SELECT id FROM fields WHERE entity_id = ?)
                        """,
                        (entity_id.value,),
                    )
                except sqlite3.OperationalError:
                    pass

                # Delete formulas
                try:
                    cursor.execute(
                        """
                        DELETE FROM formulas
                        WHERE field_id IN (SELECT id FROM fields WHERE entity_id = ?)
                        """,
                        (entity_id.value,),
                    )
                except sqlite3.OperationalError:
                    pass

                # Delete fields
                cursor.execute(
                    "DELETE FROM fields WHERE entity_id = ?",
                    (entity_id.value,),
                )

                # Delete entity
                cursor.execute(
                    "DELETE FROM entities WHERE id = ?",
                    (entity_id.value,),
                )

                conn.commit()
                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Failed to delete entity: {e}")
        except Exception as e:
            return Failure(f"Error deleting entity: {str(e)}")

    def get_entity_dependencies(
        self, entity_id: EntityDefinitionId
    ) -> Result[dict, str]:
        """Get all dependencies on an entity.

        Args:
            entity_id: Entity definition ID to check

        Returns:
            Result containing dependency info dict or error message
        """
        if not self.exists(entity_id):
            return Failure(f"Entity '{entity_id.value}' does not exist")

        try:
            with self._connection as conn:
                cursor = conn.cursor()

                dependencies = {
                    "referenced_by_table_fields": [],
                    "referenced_by_lookup_fields": [],
                    "child_entities": [],
                }

                # Find TABLE fields referencing this entity
                try:
                    cursor.execute(
                        """
                        SELECT f.entity_id, f.id
                        FROM fields f
                        JOIN field_options fo ON f.id = fo.field_id
                        WHERE f.field_type = 'TABLE'
                        AND json_extract(fo.inline_options, '$.table_entity_id') = ?
                        """,
                        (entity_id.value,),
                    )
                    for row in cursor.fetchall():
                        dependencies["referenced_by_table_fields"].append(
                            (row["entity_id"], row["id"])
                        )
                except sqlite3.OperationalError:
                    pass

                # Find LOOKUP fields referencing this entity
                try:
                    cursor.execute(
                        """
                        SELECT f.entity_id, f.id
                        FROM fields f
                        JOIN field_options fo ON f.id = fo.field_id
                        WHERE f.field_type = 'LOOKUP'
                        AND json_extract(fo.inline_options, '$.lookup_entity_id') = ?
                        """,
                        (entity_id.value,),
                    )
                    for row in cursor.fetchall():
                        dependencies["referenced_by_lookup_fields"].append(
                            (row["entity_id"], row["id"])
                        )
                except sqlite3.OperationalError:
                    pass

                return Success(dependencies)

        except sqlite3.Error as e:
            return Failure(f"Failed to get entity dependencies: {e}")
        except Exception as e:
            return Failure(f"Error getting entity dependencies: {str(e)}")

    def get_field_dependencies(
        self, entity_id: EntityDefinitionId, field_id: FieldDefinitionId
    ) -> Result[dict, str]:
        """Get all dependencies on a field.

        Args:
            entity_id: Parent entity definition ID
            field_id: Field definition ID to check

        Returns:
            Result containing dependency info dict or error message
        """
        if not self.exists(entity_id):
            return Failure(f"Entity '{entity_id.value}' does not exist")

        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Check field exists
                cursor.execute(
                    "SELECT 1 FROM fields WHERE id = ? AND entity_id = ?",
                    (field_id.value, entity_id.value),
                )
                if not cursor.fetchone():
                    return Failure(
                        f"Field '{field_id.value}' not found in entity '{entity_id.value}'"
                    )

                dependencies = {
                    "referenced_by_formulas": [],
                    "referenced_by_controls_source": [],
                    "referenced_by_controls_target": [],
                    "referenced_by_lookup_display": [],
                }

                # Find formulas referencing this field
                pattern = f"%{{{{{field_id.value}}}}}%"
                try:
                    cursor.execute(
                        """
                        SELECT f.entity_id, f.id
                        FROM fields f
                        JOIN formulas fo ON f.id = fo.field_id
                        WHERE fo.expression LIKE ?
                        """,
                        (pattern,),
                    )
                    for row in cursor.fetchall():
                        dependencies["referenced_by_formulas"].append(
                            (row["entity_id"], row["id"])
                        )
                except sqlite3.OperationalError:
                    pass

                return Success(dependencies)

        except sqlite3.Error as e:
            return Failure(f"Failed to get field dependencies: {e}")
        except Exception as e:
            return Failure(f"Error getting field dependencies: {str(e)}")

    # -------------------------------------------------------------------------
    # Private Write Helpers
    # -------------------------------------------------------------------------

    def _insert_field(
        self,
        cursor: sqlite3.Cursor,
        entity_id: EntityDefinitionId,
        field_def: FieldDefinition,
    ) -> None:
        """Insert a field into the database."""
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, name, field_type, sort_order)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                field_def.id.value,
                entity_id.value,
                field_def.label_key.key.replace("field.", ""),
                field_def.field_type.value,
                0,
            ),
        )

    def _update_field(
        self,
        cursor: sqlite3.Cursor,
        entity_id: EntityDefinitionId,
        field_def: FieldDefinition,
    ) -> None:
        """Update an existing field in the database."""
        cursor.execute(
            """
            UPDATE fields
            SET name = ?, field_type = ?
            WHERE id = ? AND entity_id = ?
            """,
            (
                field_def.label_key.key.replace("field.", ""),
                field_def.field_type.value,
                field_def.id.value,
                entity_id.value,
            ),
        )

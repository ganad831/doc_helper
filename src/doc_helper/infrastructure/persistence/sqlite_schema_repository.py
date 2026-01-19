"""SQLite implementation of schema repository."""

import json
import sqlite3
from pathlib import Path
from typing import Optional

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
                    entity_id=entity_id,
                    name_key=entity_row["name"],
                    display_name=entity_row["label"],
                    field_definitions=fields,
                    description=entity_row["description"] if "description" in entity_row.keys() else None,
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
                            entity_id=entity_id,
                            name_key=entity_row["name"],
                            display_name=entity_row["label"],
                            field_definitions=fields,
                            description=entity_row["description"] if "description" in entity_row.keys() else None,
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
                    entity_id=entity_id,
                    name_key=entity_row["name"],
                    display_name=entity_row["label"],
                    field_definitions=fields,
                    description=entity_row["description"] if "description" in entity_row.keys() else None,
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
                            entity_id=entity_id,
                            name_key=entity_row["name"],
                            display_name=entity_row["label"],
                            field_definitions=fields,
                            description=entity_row["description"] if "description" in entity_row.keys() else None,
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
            from doc_helper.domain.common.i18n import TranslationKey

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
        if rule_row.get("required"):
            constraints.append(RequiredConstraint())

        # Min/Max value constraints
        min_value = rule_row.get("min_value")
        if min_value is not None:
            constraints.append(MinValueConstraint(min_value=min_value))

        max_value = rule_row.get("max_value")
        if max_value is not None:
            constraints.append(MaxValueConstraint(max_value=max_value))

        # Min/Max length constraints
        min_length = rule_row.get("min_length")
        if min_length is not None:
            constraints.append(MinLengthConstraint(min_length=min_length))

        max_length = rule_row.get("max_length")
        if max_length is not None:
            constraints.append(MaxLengthConstraint(max_length=max_length))

        # Pattern constraint
        pattern = rule_row.get("pattern")
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

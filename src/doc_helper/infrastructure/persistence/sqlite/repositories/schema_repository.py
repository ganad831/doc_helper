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
from doc_helper.domain.validation.constraint_factory import ConstraintFactory
from doc_helper.infrastructure.persistence.sqlite_base import SqliteConnection
from doc_helper.application.dto.export_dto import ControlRuleExportDTO


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
        self._constraint_factory = ConstraintFactory()

    # -------------------------------------------------------------------------
    # Read Operations (Phase 1 + Phase 2 Step 1)
    # -------------------------------------------------------------------------

    def _load_entity_with_cursor(
        self, cursor: sqlite3.Cursor, entity_id: EntityDefinitionId
    ) -> Result[EntityDefinition, str]:
        """Load entity using an existing cursor (avoids nested connections).

        Args:
            cursor: Open database cursor (caller manages connection)
            entity_id: Entity ID to load

        Returns:
            Success with EntityDefinition or Failure with error message
        """
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

    def get_by_id(self, entity_id: EntityDefinitionId) -> Result[EntityDefinition, str]:
        """Get entity definition by ID."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                return self._load_entity_with_cursor(cursor, entity_id)

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
                    entity_result = self._load_entity_with_cursor(cursor, entity_id)
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

                return self._load_entity_with_cursor(cursor, EntityDefinitionId(row[0]))

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    def exists(self, entity_id: EntityDefinitionId) -> bool:
        """Check if entity definition exists."""
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                return self._exists_with_cursor(cursor, entity_id)
        except sqlite3.Error:
            return False

    def _exists_with_cursor(
        self, cursor: sqlite3.Cursor, entity_id: EntityDefinitionId
    ) -> bool:
        """Check if entity exists using an existing cursor (avoids nested connections).

        Args:
            cursor: Open database cursor (caller manages connection)
            entity_id: Entity ID to check

        Returns:
            True if entity exists, False otherwise
        """
        cursor.execute(
            "SELECT 1 FROM entities WHERE id = ?",
            (str(entity_id.value),),
        )
        return cursor.fetchone() is not None

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
                    child_result = self._load_entity_with_cursor(cursor, child_id)
                    if child_result.is_success():
                        children.append(child_result.value)

                return Success(tuple(children))

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    # -------------------------------------------------------------------------
    # Write Operations (Phase 2 Step 2: CREATE only)
    # -------------------------------------------------------------------------

    def save(self, entity: EntityDefinition) -> Result[None, str]:
        """Save entity definition (create new or add/update fields).

        Phase 2 Step 3 Behavior:
        - If entity does NOT exist: CREATE new entity with all fields
        - If entity EXISTS: ADD new fields OR UPDATE existing fields

        Args:
            entity: Entity definition to save

        Returns:
            Result with None on success or error message

        Validation:
            - All fields must have valid field types
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()
                entity_exists = self._exists_with_cursor(cursor, entity.id)

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
                        # UPDATE (Phase 2 Step 3): Add/update/delete fields
                        # Load existing field IDs from database
                        cursor.execute(
                            "SELECT id FROM fields WHERE entity_id = ?",
                            (str(entity.id.value),),
                        )
                        existing_field_ids = {row[0] for row in cursor.fetchall()}

                        # Get current field IDs from aggregate
                        current_field_ids = {
                            str(field_def.id.value)
                            for field_def in entity.get_all_fields()
                        }

                        # DELETE fields that were removed from aggregate
                        # NOTE: validation_rules cleanup is handled by ON DELETE CASCADE
                        # (see schema_bootstrap.py VALIDATION_RULES_TABLE_DDL)
                        removed_field_ids = existing_field_ids - current_field_ids
                        for removed_id in removed_field_ids:
                            cursor.execute(
                                "DELETE FROM fields WHERE id = ? AND entity_id = ?",
                                (removed_id, str(entity.id.value)),
                            )

                        # Process all current fields: insert new, update existing
                        for field_def in entity.get_all_fields():
                            if str(field_def.id.value) in existing_field_ids:
                                # Field exists - UPDATE it
                                self._update_field(cursor, entity.id, field_def)
                            else:
                                # Field is new - INSERT it
                                self._insert_field(cursor, entity.id, field_def)

                    # Commit transaction
                    cursor.execute("COMMIT")

                    return Success(None)

                except sqlite3.Error as e:
                    cursor.execute("ROLLBACK")
                    return Failure(f"Failed to save entity: {e}")

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")

    def update(self, entity: EntityDefinition) -> Result[None, str]:
        """Update entity definition metadata (Phase 2 Step 3).

        Updates entity metadata: name_key, description_key, is_root_entity, parent_entity_id.
        Does NOT modify fields (use save() for adding fields).

        Args:
            entity: Entity definition with updated metadata

        Returns:
            Result with None on success or error message
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Check if entity exists
                if not self._exists_with_cursor(cursor, entity.id):
                    return Failure(f"Entity '{entity.id.value}' does not exist. Use save() to create new entities.")

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                try:
                    # Update entity metadata
                    cursor.execute(
                        """
                        UPDATE entities
                        SET name_key = ?,
                            description_key = ?,
                            is_root_entity = ?,
                            parent_entity_id = ?
                        WHERE id = ?
                        """,
                        (
                            entity.name_key.key,
                            entity.description_key.key if entity.description_key else None,
                            1 if entity.is_root_entity else 0,
                            str(entity.parent_entity_id.value) if entity.parent_entity_id else None,
                            str(entity.id.value),
                        ),
                    )

                    # Commit transaction
                    cursor.execute("COMMIT")

                    return Success(None)

                except sqlite3.Error as e:
                    cursor.execute("ROLLBACK")
                    return Failure(f"Failed to update entity: {e}")

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

                # Load constraints from validation_rules table
                constraints = self._load_constraints(cursor, field_id)

                # =====================================================================
                # CALCULATED FIELD INVARIANT (READ-PATH SAFETY NET):
                # CALCULATED fields NEVER have constraints. If db is dirty, force
                # constraints=() and required=False. This is a defensive measure.
                # =====================================================================
                if field_type == FieldType.CALCULATED:
                    constraints = ()
                    required_flag = False
                else:
                    required_flag = bool(row[4])

                # =====================================================================
                # SELF-ENTITY LOOKUP INVARIANT (READ-PATH SAFETY NET):
                # LOOKUP fields cannot reference their own entity. If db has corrupted
                # data where lookup_entity_id == entity_id, DROP THE FIELD entirely.
                # NO database mutation here - just skip loading the corrupted field.
                # This is Option A (Preferred) from A1.2-3 spec.
                # =====================================================================
                lookup_entity_id_value = row[7]
                if field_type == FieldType.LOOKUP and lookup_entity_id_value:
                    if lookup_entity_id_value.strip() == str(entity_id.value).strip():
                        # Skip this corrupted field - do not add to loaded fields dict
                        continue

                # =====================================================================
                # LOOKUP DISPLAY FIELD INVARIANT (READ-PATH SANITIZATION):
                # If lookup_display_field references a non-existent field or a field
                # with an invalid type (CALCULATED, TABLE, FILE, IMAGE), sanitize to
                # NULL. Do NOT fail the load - just correct the value.
                # =====================================================================
                lookup_display_field_value = row[8]
                if field_type == FieldType.LOOKUP and lookup_display_field_value and lookup_entity_id_value:
                    lookup_display_field_value = self._sanitize_lookup_display_field(
                        cursor, lookup_entity_id_value, lookup_display_field_value
                    )

                # Load control rules for this field (Phase A5.4)
                control_rules = self._load_control_rules(cursor, field_id)

                # Create FieldDefinition
                field_def = FieldDefinition(
                    id=field_id,
                    field_type=field_type,
                    label_key=TranslationKey(row[2]),
                    help_text_key=TranslationKey(row[3]) if row[3] else None,
                    required=required_flag,
                    default_value=row[5],
                    formula=row[6],
                    lookup_entity_id=lookup_entity_id_value,
                    lookup_display_field=lookup_display_field_value,
                    child_entity_id=row[9],
                    constraints=constraints,
                    options=(),  # Load options separately if needed
                    control_rules=control_rules,  # Phase A5.4: Load control rules
                )

                fields[field_id] = field_def

            return Success(fields)

        except sqlite3.Error as e:
            return Failure(f"Failed to load fields: {e}")

    # =========================================================================
    # INVARIANT (Phase A2.1-1):
    # If a LOOKUP display field becomes invalid (field deleted, field renamed,
    # or field type changed to an incompatible type like CALCULATED/TABLE/FILE/IMAGE),
    # lookup_display_field is automatically sanitized to NULL on load.
    #
    # This is INTENTIONAL and NOT an error. It prevents dangling cross-entity
    # references from causing runtime failures. Schema Designer enforces
    # structural validity only; corrupted references are silently healed.
    #
    # The database is NOT modified - sanitization is read-path only.
    # =========================================================================
    def _sanitize_lookup_display_field(
        self,
        cursor: sqlite3.Cursor,
        lookup_entity_id: str,
        lookup_display_field: str,
    ) -> str | None:
        """Sanitize lookup_display_field to ensure it references a valid field.

        READ-PATH SANITIZATION: If lookup_display_field references a non-existent
        field or a field with an invalid type (CALCULATED, TABLE, FILE, IMAGE),
        return None to sanitize the value. Does NOT modify the database.

        Args:
            cursor: Database cursor
            lookup_entity_id: The entity that lookup_display_field should reference
            lookup_display_field: The field ID to validate

        Returns:
            lookup_display_field if valid, None if invalid (sanitized)
        """
        from doc_helper.domain.validation.lookup_display_field import (
            INVALID_DISPLAY_FIELD_TYPES,
        )

        try:
            # Query for the field in the lookup entity
            cursor.execute(
                """
                SELECT field_type FROM fields
                WHERE entity_id = ? AND id = ?
                """,
                (lookup_entity_id.strip(), lookup_display_field.strip()),
            )
            row = cursor.fetchone()

            if not row:
                # Field doesn't exist in the lookup entity - sanitize to None
                return None

            field_type_value = row[0]
            try:
                field_type = FieldType(field_type_value)
            except ValueError:
                # Invalid field type in database - sanitize to None
                return None

            # Check if the field type is invalid for display
            if field_type in INVALID_DISPLAY_FIELD_TYPES:
                # Invalid type (CALCULATED, TABLE, FILE, IMAGE) - sanitize to None
                return None

            # Field is valid
            return lookup_display_field

        except sqlite3.Error:
            # Database error - be defensive, sanitize to None
            return None

    def _load_control_rules(
        self,
        cursor: sqlite3.Cursor,
        field_id: FieldDefinitionId,
    ) -> tuple:
        """Load control rules for a field from control_rules table (Phase A5.4).

        DESIGN-TIME ONLY: Loads control rule metadata. NO runtime execution.

        DEFENSIVE READ BEHAVIOR:
        - Unknown rule_type: Skip the row (do NOT crash)
        - NULL or empty formula_text: Skip the row (do NOT crash)
        - Database doesn't have control_rules table: Return empty tuple

        Args:
            cursor: Database cursor
            field_id: Field ID to load control rules for

        Returns:
            Tuple of ControlRuleExportDTO objects (empty if none found or table missing)
        """
        # Valid rule types that we recognize
        valid_rule_types = frozenset({"VISIBILITY", "ENABLED", "REQUIRED"})

        try:
            cursor.execute(
                """
                SELECT rule_type, formula_text
                FROM control_rules
                WHERE field_id = ?
                """,
                (str(field_id.value),),
            )
            rows = cursor.fetchall()

            control_rules = []
            for row in rows:
                rule_type = row[0]
                formula_text = row[1]

                # Defensive: skip unknown rule types
                if not rule_type or rule_type.strip().upper() not in valid_rule_types:
                    continue

                # Defensive: skip NULL or empty formula_text
                if not formula_text or not formula_text.strip():
                    continue

                # Create ControlRuleExportDTO
                control_rule = ControlRuleExportDTO(
                    rule_type=rule_type.strip().upper(),
                    target_field_id=str(field_id.value),
                    formula_text=formula_text.strip(),
                )
                control_rules.append(control_rule)

            return tuple(control_rules)

        except sqlite3.OperationalError:
            # Table doesn't exist - that's okay, return empty tuple
            return ()
        except sqlite3.Error:
            # Other database error - be defensive, return empty tuple
            return ()

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

        # Insert constraints into validation_rules table
        if field_def.constraints:
            self._insert_constraints(cursor, field_def.id, field_def.constraints)

        # Insert control rules into control_rules table (Phase A5.4)
        if field_def.control_rules:
            self._insert_control_rules(cursor, field_def.id, field_def.control_rules)

    def _update_field(
        self,
        cursor: sqlite3.Cursor,
        entity_id: EntityDefinitionId,
        field_def: FieldDefinition,
    ) -> None:
        """Update an existing field in the database.

        Args:
            cursor: Database cursor
            entity_id: Entity ID this field belongs to
            field_def: Field definition to update

        Raises:
            sqlite3.Error: If update fails
        """
        cursor.execute(
            """
            UPDATE fields
            SET field_type = ?,
                label_key = ?,
                help_text_key = ?,
                required = ?,
                default_value = ?,
                formula = ?,
                lookup_entity_id = ?,
                lookup_display_field = ?,
                child_entity_id = ?
            WHERE id = ? AND entity_id = ?
            """,
            (
                field_def.field_type.value,
                field_def.label_key.key,
                field_def.help_text_key.key if field_def.help_text_key else None,
                1 if field_def.required else 0,
                field_def.default_value,
                field_def.formula,
                field_def.lookup_entity_id,
                field_def.lookup_display_field,
                field_def.child_entity_id,
                str(field_def.id.value),
                str(entity_id.value),
            ),
        )

        # Sync constraints: delete old, insert new
        self._delete_constraints(cursor, field_def.id)
        if field_def.constraints:
            self._insert_constraints(cursor, field_def.id, field_def.constraints)

        # Sync control rules: delete old, insert new (Phase A5.4)
        self._delete_control_rules(cursor, field_def.id)
        if field_def.control_rules:
            self._insert_control_rules(cursor, field_def.id, field_def.control_rules)

    # -------------------------------------------------------------------------
    # Constraint Persistence Helpers
    # -------------------------------------------------------------------------

    def _insert_constraints(
        self,
        cursor: sqlite3.Cursor,
        field_id: FieldDefinitionId,
        constraints: tuple,
    ) -> None:
        """Insert constraints for a field into validation_rules table.

        Args:
            cursor: Database cursor
            field_id: Field ID these constraints belong to
            constraints: Tuple of FieldConstraint objects
        """
        import uuid

        for constraint in constraints:
            rule_type, rule_value = self._constraint_to_db_row(constraint)
            cursor.execute(
                """
                INSERT INTO validation_rules (id, field_id, rule_type, rule_value, error_message_key)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),  # Generate unique ID
                    str(field_id.value),
                    rule_type,
                    rule_value,
                    None,  # error_message_key not used yet
                ),
            )

    def _delete_constraints(
        self,
        cursor: sqlite3.Cursor,
        field_id: FieldDefinitionId,
    ) -> None:
        """Delete all constraints for a field from validation_rules table.

        Args:
            cursor: Database cursor
            field_id: Field ID to delete constraints for
        """
        cursor.execute(
            "DELETE FROM validation_rules WHERE field_id = ?",
            (str(field_id.value),),
        )

    def _load_constraints(
        self,
        cursor: sqlite3.Cursor,
        field_id: FieldDefinitionId,
    ) -> tuple:
        """Load constraints for a field from validation_rules table.

        Args:
            cursor: Database cursor
            field_id: Field ID to load constraints for

        Returns:
            Tuple of FieldConstraint objects
        """
        cursor.execute(
            """
            SELECT rule_type, rule_value
            FROM validation_rules
            WHERE field_id = ?
            """,
            (str(field_id.value),),
        )
        rows = cursor.fetchall()

        constraints = []
        for row in rows:
            constraint = self._db_row_to_constraint(row[0], row[1])
            if constraint:
                constraints.append(constraint)

        return tuple(constraints)

    def _constraint_to_db_row(self, constraint) -> tuple:
        """Convert a FieldConstraint to database row format.

        Uses ConstraintFactory to serialize domain objects to raw data.
        This keeps domain object knowledge in the Domain layer.

        Args:
            constraint: FieldConstraint to convert

        Returns:
            Tuple of (rule_type, rule_value)
        """
        return self._constraint_factory.serialize_to_raw(constraint)

    def _db_row_to_constraint(self, rule_type: str, rule_value: str):
        """Convert database row to a FieldConstraint.

        Uses ConstraintFactory to hydrate domain objects from raw data.
        This keeps domain object instantiation in the Domain layer.

        Args:
            rule_type: Rule type from database
            rule_value: Rule value from database

        Returns:
            FieldConstraint or None if unknown type
        """
        return self._constraint_factory.create_from_raw(rule_type, rule_value)

    # -------------------------------------------------------------------------
    # Control Rules Persistence Helpers (Phase A5.4)
    # -------------------------------------------------------------------------

    def _insert_control_rules(
        self,
        cursor: sqlite3.Cursor,
        field_id: FieldDefinitionId,
        control_rules: tuple,
    ) -> None:
        """Insert control rules for a field into control_rules table (Phase A5.4).

        DESIGN-TIME ONLY: Stores control rule metadata. NO runtime execution.

        Uses INSERT OR REPLACE to handle the UNIQUE constraint on (field_id, rule_type).

        Args:
            cursor: Database cursor
            field_id: Field ID these control rules belong to
            control_rules: Tuple of ControlRuleExportDTO objects
        """
        for control_rule in control_rules:
            # Only insert if it's a ControlRuleExportDTO
            if isinstance(control_rule, ControlRuleExportDTO):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO control_rules (field_id, rule_type, formula_text)
                    VALUES (?, ?, ?)
                    """,
                    (
                        str(field_id.value),
                        control_rule.rule_type.strip().upper(),
                        control_rule.formula_text.strip(),
                    ),
                )

    def _delete_control_rules(
        self,
        cursor: sqlite3.Cursor,
        field_id: FieldDefinitionId,
    ) -> None:
        """Delete all control rules for a field from control_rules table (Phase A5.4).

        Args:
            cursor: Database cursor
            field_id: Field ID to delete control rules for
        """
        try:
            cursor.execute(
                "DELETE FROM control_rules WHERE field_id = ?",
                (str(field_id.value),),
            )
        except sqlite3.OperationalError:
            # Table doesn't exist - that's okay, nothing to delete
            pass

    def get_entity_dependencies(self, entity_id: EntityDefinitionId) -> Result[dict, str]:
        """Get all dependencies on an entity (Phase 2 Step 3 - Decision 4).

        See ISchemaRepository.get_entity_dependencies for documentation.
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()

                entity_id_str = str(entity_id.value)

                # Check if entity exists
                cursor.execute("SELECT id FROM entities WHERE id = ?", (entity_id_str,))
                if not cursor.fetchone():
                    return Failure(f"Entity '{entity_id.value}' does not exist")

                dependencies = {
                    "referenced_by_table_fields": [],
                    "referenced_by_lookup_fields": [],
                    "child_entities": [],
                }

                # Find TABLE fields referencing this entity (child_entity_id)
                cursor.execute(
                    """
                    SELECT entity_id, id
                    FROM fields
                    WHERE child_entity_id = ? AND field_type = 'TABLE'
                    """,
                    (entity_id_str,),
                )
                for row in cursor.fetchall():
                    dependencies["referenced_by_table_fields"].append((row[0], row[1]))

                # Find LOOKUP fields referencing this entity (lookup_entity_id)
                cursor.execute(
                    """
                    SELECT entity_id, id
                    FROM fields
                    WHERE lookup_entity_id = ? AND field_type = 'LOOKUP'
                    """,
                    (entity_id_str,),
                )
                for row in cursor.fetchall():
                    dependencies["referenced_by_lookup_fields"].append((row[0], row[1]))

                # Find child entities (entities with parent_entity_id = this entity)
                cursor.execute(
                    """
                    SELECT id
                    FROM entities
                    WHERE parent_entity_id = ?
                    """,
                    (entity_id_str,),
                )
                for row in cursor.fetchall():
                    dependencies["child_entities"].append(row[0])

                return Success(dependencies)

        except sqlite3.Error as e:
            return Failure(f"Failed to check entity dependencies: {e}")

    def get_field_dependencies(
        self, entity_id: EntityDefinitionId, field_id: FieldDefinitionId
    ) -> Result[dict, str]:
        """Get all dependencies on a field (Phase 2 Step 3 - Decision 4).

        See ISchemaRepository.get_field_dependencies for documentation.
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()

                entity_id_str = str(entity_id.value)
                field_id_str = str(field_id.value)

                # Check if entity exists
                cursor.execute("SELECT id FROM entities WHERE id = ?", (entity_id_str,))
                if not cursor.fetchone():
                    return Failure(f"Entity '{entity_id.value}' does not exist")

                # Check if field exists
                cursor.execute(
                    "SELECT id FROM fields WHERE id = ? AND entity_id = ?",
                    (field_id_str, entity_id_str),
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

                # Find formulas referencing this field ({{field_id}})
                # Formula syntax uses {{field_id}} to reference fields
                pattern = f"%{{{{{field_id_str}}}}}%"
                cursor.execute(
                    """
                    SELECT entity_id, id
                    FROM fields
                    WHERE formula IS NOT NULL AND formula LIKE ?
                    """,
                    (pattern,),
                )
                for row in cursor.fetchall():
                    dependencies["referenced_by_formulas"].append((row[0], row[1]))

                # Find control rules where this field is source
                # Note: control_relations table structure varies by implementation
                # This assumes a control_relations table with source_field_id and target_field_id
                # If this table doesn't exist or has different structure, this query will fail gracefully
                try:
                    # Build full field identifier for controls
                    full_field_id = f"{entity_id_str}.{field_id_str}"

                    cursor.execute(
                        """
                        SELECT target_entity_id, target_field_id
                        FROM control_relations
                        WHERE source_entity_id = ? AND source_field_id = ?
                        """,
                        (entity_id_str, field_id_str),
                    )
                    for row in cursor.fetchall():
                        dependencies["referenced_by_controls_source"].append((row[0], row[1]))

                    # Find control rules where this field is target
                    cursor.execute(
                        """
                        SELECT source_entity_id, source_field_id
                        FROM control_relations
                        WHERE target_entity_id = ? AND target_field_id = ?
                        """,
                        (entity_id_str, field_id_str),
                    )
                    for row in cursor.fetchall():
                        dependencies["referenced_by_controls_target"].append((row[0], row[1]))

                except sqlite3.OperationalError:
                    # control_relations table might not exist - that's okay, skip it
                    pass

                # Find LOOKUP fields using this field as lookup_display_field
                cursor.execute(
                    """
                    SELECT entity_id, id
                    FROM fields
                    WHERE lookup_display_field = ? AND field_type = 'LOOKUP'
                    """,
                    (field_id_str,),
                )
                for row in cursor.fetchall():
                    dependencies["referenced_by_lookup_display"].append((row[0], row[1]))

                return Success(dependencies)

        except sqlite3.Error as e:
            return Failure(f"Failed to check field dependencies: {e}")

    # -------------------------------------------------------------------------
    # Delete Operations (Phase 2 Step 3)
    # -------------------------------------------------------------------------

    def delete(self, entity_id: EntityDefinitionId) -> Result[None, str]:
        """Delete entity definition from schema (Phase 2 Step 3).

        IMPORTANT: Caller MUST check dependencies using get_entity_dependencies()
        before calling delete(). This method does NOT check dependencies.

        Cascade Behavior:
            - Deletes entity definition from entities table
            - Deletes all field definitions belonging to this entity
            - Deletes all control relations where entity is source or target
            - Deletes all validation rules for this entity's fields (if table exists)

        Args:
            entity_id: Entity definition ID to delete

        Returns:
            Result with None on success or error message
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()

                entity_id_str = str(entity_id.value)

                # Check if entity exists
                cursor.execute("SELECT id FROM entities WHERE id = ?", (entity_id_str,))
                if not cursor.fetchone():
                    return Failure(f"Entity '{entity_id.value}' does not exist")

                # Begin cascade delete (transaction will auto-rollback on error)

                # 1. Delete all validation rules for this entity's fields (if table exists)
                try:
                    cursor.execute(
                        """
                        DELETE FROM validation_rules
                        WHERE field_id IN (SELECT id FROM fields WHERE entity_id = ?)
                        """,
                        (entity_id_str,),
                    )
                except sqlite3.OperationalError:
                    # validation_rules table might not exist - that's okay
                    pass

                # 2. Delete all control relations where this entity is source or target
                try:
                    cursor.execute(
                        """
                        DELETE FROM control_relations
                        WHERE source_entity_id = ? OR target_entity_id = ?
                        """,
                        (entity_id_str, entity_id_str),
                    )
                except sqlite3.OperationalError:
                    # control_relations table might not exist - that's okay
                    pass

                # 3. Delete all field definitions belonging to this entity
                # NOTE: validation_rules cleanup is handled by ON DELETE CASCADE
                # (see schema_bootstrap.py VALIDATION_RULES_TABLE_DDL)
                cursor.execute(
                    "DELETE FROM fields WHERE entity_id = ?",
                    (entity_id_str,),
                )

                # 4. Delete the entity definition itself
                cursor.execute(
                    "DELETE FROM entities WHERE id = ?",
                    (entity_id_str,),
                )

                # Commit transaction (context manager handles this)
                conn.commit()

                return Success(None)

        except sqlite3.Error as e:
            return Failure(f"Failed to delete entity '{entity_id.value}': {e}")

    # -------------------------------------------------------------------------
    # CALCULATED Field Constraint Cleanup (Invariant Enforcement)
    # -------------------------------------------------------------------------

    def purge_calculated_field_constraints(self) -> Result[int, str]:
        """Purge all validation constraints from CALCULATED fields.

        CALCULATED FIELD INVARIANT: CALCULATED fields NEVER have constraints.
        This method cleans up any corrupted data in the validation_rules table.

        This is a one-time cleanup function that should be called:
        - On schema database bootstrap/initialization
        - During migration from older versions

        It is idempotent - safe to run multiple times.

        Returns:
            Result containing count of deleted constraints or error message.
        """
        try:
            with self._connection as conn:
                cursor = conn.cursor()

                # Find all CALCULATED fields
                cursor.execute(
                    """
                    SELECT id FROM fields WHERE field_type = 'CALCULATED'
                    """
                )
                calculated_field_ids = [row[0] for row in cursor.fetchall()]

                if not calculated_field_ids:
                    return Success(0)

                # Delete all validation_rules for CALCULATED fields
                placeholders = ",".join("?" * len(calculated_field_ids))
                cursor.execute(
                    f"""
                    DELETE FROM validation_rules
                    WHERE field_id IN ({placeholders})
                    """,
                    calculated_field_ids,
                )

                deleted_count = cursor.rowcount
                conn.commit()

                return Success(deleted_count)

        except sqlite3.Error as e:
            return Failure(f"Failed to purge CALCULATED field constraints: {e}")

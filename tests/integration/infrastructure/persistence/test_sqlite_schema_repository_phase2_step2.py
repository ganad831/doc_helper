"""Integration tests for SqliteSchemaRepository Phase 2 Step 2 (CREATE operations)."""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
    SqliteSchemaRepository,
)


class TestSqliteSchemaRepositoryPhase2Step2:
    """Integration tests for SqliteSchemaRepository Phase 2 Step 2 operations."""

    @pytest.fixture
    def temp_db_path(self) -> Path:
        """Create temporary database with schema."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_path = Path(temp_file.name)
        temp_file.close()

        # Create tables
        conn = sqlite3.connect(str(temp_path))
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            CREATE TABLE entities (
                id TEXT PRIMARY KEY,
                name_key TEXT NOT NULL,
                description_key TEXT,
                is_root_entity INTEGER NOT NULL DEFAULT 0,
                parent_entity_id TEXT,
                display_order INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (parent_entity_id) REFERENCES entities(id) ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE fields (
                id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                field_type TEXT NOT NULL,
                label_key TEXT NOT NULL,
                help_text_key TEXT,
                required INTEGER NOT NULL DEFAULT 0,
                default_value TEXT,
                display_order INTEGER NOT NULL DEFAULT 0,
                formula TEXT,
                lookup_entity_id TEXT,
                lookup_display_field TEXT,
                child_entity_id TEXT,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                CHECK (field_type IN ('text', 'textarea', 'number', 'date', 'dropdown', 'checkbox', 'radio', 'calculated', 'lookup', 'file', 'image', 'table'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_rules (
                id TEXT PRIMARY KEY,
                field_id TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                rule_value TEXT,
                error_message_key TEXT,
                FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

        yield temp_path

        # Cleanup
        temp_path.unlink(missing_ok=True)

    @pytest.fixture
    def repository(self, temp_db_path: Path) -> SqliteSchemaRepository:
        """Create repository instance with temp database."""
        return SqliteSchemaRepository(temp_db_path)

    # =========================================================================
    # CREATE Entity Tests
    # =========================================================================

    def test_save_new_entity_success(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should successfully save new entity with fields."""
        # Create entity
        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test_entity"),
            description_key=TranslationKey("entity.test_entity.description"),
            fields={
                FieldDefinitionId("field1"): FieldDefinition(
                    id=FieldDefinitionId("field1"),
                    field_type=FieldType.TEXT,
                    label_key=TranslationKey("field.field1"),
                    help_text_key=None,
                    required=True,
                    default_value=None,
                    constraints=(),
                    options=(),
                    formula=None,
                    lookup_entity_id=None,
                    lookup_display_field=None,
                    child_entity_id=None,
                    control_rules=(),
                ),
                FieldDefinitionId("field2"): FieldDefinition(
                    id=FieldDefinitionId("field2"),
                    field_type=FieldType.NUMBER,
                    label_key=TranslationKey("field.field2"),
                    help_text_key=None,
                    required=False,
                    default_value="0",
                    constraints=(),
                    options=(),
                    formula=None,
                    lookup_entity_id=None,
                    lookup_display_field=None,
                    child_entity_id=None,
                    control_rules=(),
                ),
            },
            is_root_entity=True,
            parent_entity_id=None,
        )

        # Save entity
        result = repository.save(entity)
        assert result.is_success()

        # Verify entity saved correctly
        assert repository.exists(EntityDefinitionId("test_entity"))

        # Load entity
        load_result = repository.get_by_id(EntityDefinitionId("test_entity"))
        assert load_result.is_success()

        loaded_entity = load_result.value
        assert loaded_entity.id == EntityDefinitionId("test_entity")
        assert loaded_entity.name_key == TranslationKey("entity.test_entity")
        assert loaded_entity.is_root_entity is True
        assert len(loaded_entity.fields) == 2
        assert FieldDefinitionId("field1") in loaded_entity.fields
        assert FieldDefinitionId("field2") in loaded_entity.fields

    def test_save_new_entity_without_fields(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should successfully save new entity with no fields."""
        entity = EntityDefinition(
            id=EntityDefinitionId("empty_entity"),
            name_key=TranslationKey("entity.empty_entity"),
            description_key=None,
            fields={},
            is_root_entity=False,
            parent_entity_id=None,
        )

        result = repository.save(entity)
        assert result.is_success()

        # Verify entity saved
        load_result = repository.get_by_id(EntityDefinitionId("empty_entity"))
        assert load_result.is_success()
        assert len(load_result.value.fields) == 0

    # =========================================================================
    # ADD Fields to Existing Entity Tests
    # =========================================================================

    def test_save_existing_entity_add_new_fields(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should add new fields to existing entity."""
        # Create and save initial entity
        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test_entity"),
            description_key=None,
            fields={
                FieldDefinitionId("field1"): FieldDefinition(
                    id=FieldDefinitionId("field1"),
                    field_type=FieldType.TEXT,
                    label_key=TranslationKey("field.field1"),
                    help_text_key=None,
                    required=True,
                    default_value=None,
                    constraints=(),
                    options=(),
                    formula=None,
                    lookup_entity_id=None,
                    lookup_display_field=None,
                    child_entity_id=None,
                    control_rules=(),
                ),
            },
            is_root_entity=False,
            parent_entity_id=None,
        )
        repository.save(entity)

        # Load entity and add new field
        load_result = repository.get_by_id(EntityDefinitionId("test_entity"))
        assert load_result.is_success()
        entity = load_result.value

        # Add new field
        new_field = FieldDefinition(
            id=FieldDefinitionId("field2"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.field2"),
            help_text_key=None,
            required=False,
            default_value=None,
            constraints=(),
            options=(),
            formula=None,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
            control_rules=(),
        )
        entity.fields[FieldDefinitionId("field2")] = new_field

        # Save updated entity
        result = repository.save(entity)
        assert result.is_success()

        # Verify both fields exist
        load_result = repository.get_by_id(EntityDefinitionId("test_entity"))
        assert load_result.is_success()
        loaded_entity = load_result.value
        assert len(loaded_entity.fields) == 2
        assert FieldDefinitionId("field1") in loaded_entity.fields
        assert FieldDefinitionId("field2") in loaded_entity.fields

    def test_save_existing_entity_no_new_fields_updates_existing(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should succeed when saving existing entity with same fields (UPDATE behavior).

        Phase 2 Step 3: save() now supports UPDATE of existing fields.
        When all fields already exist, they are updated (not rejected).
        """
        # Create and save initial entity
        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test_entity"),
            description_key=None,
            fields={
                FieldDefinitionId("field1"): FieldDefinition(
                    id=FieldDefinitionId("field1"),
                    field_type=FieldType.TEXT,
                    label_key=TranslationKey("field.field1"),
                    help_text_key=None,
                    required=True,
                    default_value=None,
                    constraints=(),
                    options=(),
                    formula=None,
                    lookup_entity_id=None,
                    lookup_display_field=None,
                    child_entity_id=None,
                    control_rules=(),
                ),
            },
            is_root_entity=False,
            parent_entity_id=None,
        )
        repository.save(entity)

        # Save again with same fields - should UPDATE (succeed), not reject
        result = repository.save(entity)
        assert result.is_success()  # Phase 2 Step 3: UPDATE existing fields is valid

    def test_save_existing_entity_with_duplicate_field_ignored(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should only insert NEW fields, ignoring existing ones."""
        # Create and save initial entity with field1
        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test_entity"),
            description_key=None,
            fields={
                FieldDefinitionId("field1"): FieldDefinition(
                    id=FieldDefinitionId("field1"),
                    field_type=FieldType.TEXT,
                    label_key=TranslationKey("field.field1"),
                    help_text_key=None,
                    required=True,
                    default_value=None,
                    constraints=(),
                    options=(),
                    formula=None,
                    lookup_entity_id=None,
                    lookup_display_field=None,
                    child_entity_id=None,
                    control_rules=(),
                ),
            },
            is_root_entity=False,
            parent_entity_id=None,
        )
        repository.save(entity)

        # Load and add field2 (field1 still in fields dict)
        load_result = repository.get_by_id(EntityDefinitionId("test_entity"))
        entity = load_result.value
        entity.fields[FieldDefinitionId("field2")] = FieldDefinition(
            id=FieldDefinitionId("field2"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.field2"),
            help_text_key=None,
            required=False,
            default_value=None,
            constraints=(),
            options=(),
            formula=None,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
            control_rules=(),
        )

        # Save (should only insert field2, not field1)
        result = repository.save(entity)
        assert result.is_success()

        # Verify both fields exist (no duplicate insertion error)
        load_result = repository.get_by_id(EntityDefinitionId("test_entity"))
        assert len(load_result.value.fields) == 2

    # =========================================================================
    # Rollback Tests
    # =========================================================================

    def test_save_rollback_on_constraint_violation(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should rollback transaction on database constraint violation."""
        # Create entity with invalid foreign key (parent doesn't exist)
        entity = EntityDefinition(
            id=EntityDefinitionId("child_entity"),
            name_key=TranslationKey("entity.child_entity"),
            description_key=None,
            fields={},
            is_root_entity=False,
            parent_entity_id=EntityDefinitionId("nonexistent_parent"),
        )

        # Save should fail (foreign key constraint)
        result = repository.save(entity)
        assert result.is_failure()
        assert "failed to save entity" in result.error.lower()

        # Verify entity was NOT saved (rollback successful)
        assert repository.exists(EntityDefinitionId("child_entity")) is False

    def test_save_rollback_on_invalid_field_type(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should rollback transaction on invalid field type in CHECK constraint."""
        # Directly attempt to insert invalid field type via repository
        # This tests the CHECK constraint on field_type column

        # Create entity with field
        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test_entity"),
            description_key=None,
            fields={},
            is_root_entity=False,
            parent_entity_id=None,
        )
        repository.save(entity)

        # Manually try to insert invalid field type (bypassing FieldType enum)
        # Use direct connection to test database constraint
        conn = sqlite3.connect(str(repository.db_path))
        cursor = conn.cursor()
        try:
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    """INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    ("invalid_field", "test_entity", "INVALID_TYPE", "field.invalid", 0, 0),
                )
        finally:
            conn.close()

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_save_entity_with_all_field_types(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should save entity with all testable field types.

        Note: Phase 2 Step 2 can only create 7 of 12 field types:
        - TEXT, TEXTAREA, NUMBER, DATE, CHECKBOX, FILE, IMAGE can be created
        - DROPDOWN, RADIO need options
        - CALCULATED needs formula
        - LOOKUP needs lookup_entity_id
        - TABLE needs child_entity_id

        These will be testable in Phase 2 Step 3 when editing is implemented.
        """
        field_types = [
            FieldType.TEXT,
            FieldType.TEXTAREA,
            FieldType.NUMBER,
            FieldType.DATE,
            FieldType.CHECKBOX,
            FieldType.FILE,
            FieldType.IMAGE,
        ]

        fields = {}
        for i, field_type in enumerate(field_types):
            field_id = FieldDefinitionId(f"field_{field_type.value.lower()}")
            fields[field_id] = FieldDefinition(
                id=field_id,
                field_type=field_type,
                label_key=TranslationKey(f"field.{field_type.value.lower()}"),
                help_text_key=None,
                required=False,
                default_value=None,
                constraints=(),
                options=(),
                formula=None,
                lookup_entity_id=None,
                lookup_display_field=None,
                child_entity_id=None,
                control_rules=(),
            )

        entity = EntityDefinition(
            id=EntityDefinitionId("all_types_entity"),
            name_key=TranslationKey("entity.all_types"),
            description_key=None,
            fields=fields,
            is_root_entity=False,
            parent_entity_id=None,
        )

        result = repository.save(entity)
        assert result.is_success()

        # Verify all fields saved
        load_result = repository.get_by_id(EntityDefinitionId("all_types_entity"))
        assert load_result.is_success()
        assert len(load_result.value.fields) == 7  # Only 7 field types testable in Phase 2 Step 2

    # =========================================================================
    # INVARIANT TEST (Phase A2.1-2):
    # Proves that invalid lookup_display_field is sanitized to NULL on load.
    # =========================================================================

    def test_lookup_display_field_sanitized_when_invalid(
        self, temp_db_path: Path
    ) -> None:
        """INVARIANT: Invalid lookup_display_field is sanitized to NULL on load.

        Phase A2.1-2: This test proves the read-path sanitization behavior.
        When a LOOKUP field references a non-existent display field, the
        repository silently sanitizes it to None rather than failing.
        """
        # Directly insert data with an INVALID lookup_display_field
        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()

        # Create target entity with a valid field
        cursor.execute(
            """INSERT INTO entities (id, name_key, is_root_entity, display_order)
               VALUES ('target_entity', 'entity.target', 0, 0)"""
        )
        cursor.execute(
            """INSERT INTO fields (id, entity_id, field_type, label_key, display_order)
               VALUES ('valid_field', 'target_entity', 'text', 'field.valid', 0)"""
        )

        # Create source entity with LOOKUP field pointing to NON-EXISTENT display field
        cursor.execute(
            """INSERT INTO entities (id, name_key, is_root_entity, display_order)
               VALUES ('source_entity', 'entity.source', 0, 1)"""
        )
        cursor.execute(
            """INSERT INTO fields (id, entity_id, field_type, label_key, display_order,
                                   lookup_entity_id, lookup_display_field)
               VALUES ('lookup_field', 'source_entity', 'lookup', 'field.lookup', 0,
                       'target_entity', 'NONEXISTENT_FIELD')"""
        )

        conn.commit()
        conn.close()

        # Load via repository - sanitization should occur
        repository = SqliteSchemaRepository(temp_db_path)
        result = repository.get_by_id(EntityDefinitionId("source_entity"))

        # ASSERT: Load succeeds and lookup_display_field is sanitized to None
        assert result.is_success(), f"Load should succeed, got: {result.error}"
        lookup_field = result.value.fields[FieldDefinitionId("lookup_field")]
        assert lookup_field.lookup_entity_id == "target_entity"
        assert lookup_field.lookup_display_field is None, (
            "INVARIANT VIOLATION: Invalid lookup_display_field should be sanitized to None"
        )

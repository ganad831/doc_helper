"""Integration tests for schema repository delete operations (Phase 2 Step 3)."""

import sqlite3
import pytest
from pathlib import Path

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
    SqliteSchemaRepository,
)


class TestSchemaRepositoryDelete:
    """Integration tests for delete() method."""

    @pytest.fixture
    def test_db_path(self, tmp_path: Path) -> Path:
        """Create temporary test database with schema."""
        db_path = tmp_path / "test_delete.db"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create entities table
        cursor.execute(
            """
            CREATE TABLE entities (
                id TEXT PRIMARY KEY,
                name_key TEXT NOT NULL,
                description_key TEXT,
                is_root_entity INTEGER NOT NULL,
                parent_entity_id TEXT,
                display_order INTEGER DEFAULT 0,
                FOREIGN KEY (parent_entity_id) REFERENCES entities(id)
            )
            """
        )

        # Create fields table
        cursor.execute(
            """
            CREATE TABLE fields (
                id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                field_type TEXT NOT NULL,
                label_key TEXT NOT NULL,
                help_text_key TEXT,
                required INTEGER NOT NULL,
                default_value TEXT,
                display_order INTEGER NOT NULL,
                formula TEXT,
                lookup_entity_id TEXT,
                lookup_display_field TEXT,
                child_entity_id TEXT,
                FOREIGN KEY (entity_id) REFERENCES entities(id)
            )
            """
        )

        # Create control_relations table
        cursor.execute(
            """
            CREATE TABLE control_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity_id TEXT NOT NULL,
                source_field_id TEXT NOT NULL,
                target_entity_id TEXT NOT NULL,
                target_field_id TEXT NOT NULL,
                effect_type TEXT NOT NULL,
                FOREIGN KEY (source_entity_id) REFERENCES entities(id),
                FOREIGN KEY (target_entity_id) REFERENCES entities(id)
            )
            """
        )

        # Create validation_rules table
        cursor.execute(
            """
            CREATE TABLE validation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                rule_value TEXT,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
            """
        )

        conn.commit()
        conn.close()
        return db_path

    @pytest.fixture
    def repository(self, test_db_path: Path) -> SqliteSchemaRepository:
        """Create repository with test database."""
        return SqliteSchemaRepository(test_db_path)

    @pytest.fixture
    def connection(self, test_db_path: Path) -> sqlite3.Connection:
        """Get connection to test database for setup."""
        return sqlite3.connect(test_db_path)

    # =========================================================================
    # Delete Tests
    # =========================================================================

    def test_delete_entity_with_no_fields_success(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should successfully delete entity with no fields."""
        cursor = connection.cursor()

        # Create standalone entity
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("standalone_entity", "entity.standalone", 0),
        )
        connection.commit()

        # Verify entity exists
        assert repository.exists(EntityDefinitionId("standalone_entity"))

        # Execute delete
        result = repository.delete(EntityDefinitionId("standalone_entity"))

        # Assert
        assert result.is_success()

        # Verify entity deleted from database
        cursor.execute("SELECT id FROM entities WHERE id = ?", ("standalone_entity",))
        assert cursor.fetchone() is None

        # Verify exists() now returns False
        assert not repository.exists(EntityDefinitionId("standalone_entity"))

    def test_delete_entity_with_fields_cascades(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should cascade delete all fields when deleting entity."""
        cursor = connection.cursor()

        # Create entity
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("test_entity", "entity.test", 0),
        )

        # Create fields for this entity
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("field1", "test_entity", "TEXT", "field.one", 0, 0),
        )
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("field2", "test_entity", "NUMBER", "field.two", 0, 1),
        )

        connection.commit()

        # Verify fields exist
        cursor.execute("SELECT COUNT(*) FROM fields WHERE entity_id = ?", ("test_entity",))
        assert cursor.fetchone()[0] == 2

        # Execute delete
        result = repository.delete(EntityDefinitionId("test_entity"))

        # Assert
        assert result.is_success()

        # Verify fields were cascade deleted
        cursor.execute("SELECT COUNT(*) FROM fields WHERE entity_id = ?", ("test_entity",))
        assert cursor.fetchone()[0] == 0

        # Verify entity deleted
        cursor.execute("SELECT id FROM entities WHERE id = ?", ("test_entity",))
        assert cursor.fetchone() is None

    def test_delete_entity_with_control_relations_cascades(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should cascade delete all control relations when deleting entity."""
        cursor = connection.cursor()

        # Create entities
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("entity1", "entity.one", 0),
        )
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("entity2", "entity.two", 0),
        )

        # Create fields
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("field1", "entity1", "DROPDOWN", "field.one", 0, 0),
        )
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("field2", "entity2", "TEXT", "field.two", 0, 0),
        )

        # Create control relation from entity1.field1 to entity2.field2
        cursor.execute(
            """
            INSERT INTO control_relations (source_entity_id, source_field_id, target_entity_id, target_field_id, effect_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("entity1", "field1", "entity2", "field2", "VISIBILITY"),
        )

        connection.commit()

        # Verify control relation exists
        cursor.execute(
            "SELECT COUNT(*) FROM control_relations WHERE source_entity_id = ? OR target_entity_id = ?",
            ("entity1", "entity1"),
        )
        assert cursor.fetchone()[0] == 1

        # Execute delete of entity1
        result = repository.delete(EntityDefinitionId("entity1"))

        # Assert
        assert result.is_success()

        # Verify control relations were cascade deleted
        cursor.execute(
            "SELECT COUNT(*) FROM control_relations WHERE source_entity_id = ? OR target_entity_id = ?",
            ("entity1", "entity1"),
        )
        assert cursor.fetchone()[0] == 0

        # Verify entity1 deleted but entity2 still exists
        cursor.execute("SELECT id FROM entities WHERE id = ?", ("entity1",))
        assert cursor.fetchone() is None

        cursor.execute("SELECT id FROM entities WHERE id = ?", ("entity2",))
        assert cursor.fetchone() is not None

    def test_delete_entity_with_validation_rules_cascades(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should cascade delete all validation rules when deleting entity."""
        cursor = connection.cursor()

        # Create entity
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("test_entity", "entity.test", 0),
        )

        # Create field
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("text_field", "test_entity", "TEXT", "field.text", 0, 0),
        )

        # Create validation rules for this field
        cursor.execute(
            """
            INSERT INTO validation_rules (field_id, rule_type, rule_value)
            VALUES (?, ?, ?)
            """,
            ("text_field", "min_length", "5"),
        )
        cursor.execute(
            """
            INSERT INTO validation_rules (field_id, rule_type, rule_value)
            VALUES (?, ?, ?)
            """,
            ("text_field", "max_length", "100"),
        )

        connection.commit()

        # Verify validation rules exist
        cursor.execute("SELECT COUNT(*) FROM validation_rules WHERE field_id = ?", ("text_field",))
        assert cursor.fetchone()[0] == 2

        # Execute delete
        result = repository.delete(EntityDefinitionId("test_entity"))

        # Assert
        assert result.is_success()

        # Verify validation rules were cascade deleted
        cursor.execute("SELECT COUNT(*) FROM validation_rules WHERE field_id = ?", ("text_field",))
        assert cursor.fetchone()[0] == 0

    def test_delete_nonexistent_entity_fails(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should fail when attempting to delete non-existent entity."""
        result = repository.delete(EntityDefinitionId("nonexistent_entity"))

        assert result.is_failure()
        assert "does not exist" in result.error.lower()

    def test_delete_multiple_entities_independently(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should delete entities independently without affecting each other."""
        cursor = connection.cursor()

        # Create three entities
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("entity1", "entity.one", 0),
        )
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("entity2", "entity.two", 0),
        )
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("entity3", "entity.three", 0),
        )

        connection.commit()

        # Delete entity2
        result = repository.delete(EntityDefinitionId("entity2"))
        assert result.is_success()

        # Verify entity1 and entity3 still exist
        cursor.execute("SELECT id FROM entities WHERE id = ?", ("entity1",))
        assert cursor.fetchone() is not None

        cursor.execute("SELECT id FROM entities WHERE id = ?", ("entity3",))
        assert cursor.fetchone() is not None

        # Verify entity2 deleted
        cursor.execute("SELECT id FROM entities WHERE id = ?", ("entity2",))
        assert cursor.fetchone() is None

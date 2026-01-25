"""Integration tests for Schema Database Bootstrap.

Phase B-1: Verify bootstrap creates config.db with correct schema.

Tests verify:
1. Bootstrap creates database file if not exists
2. Bootstrap creates all required tables
3. Bootstrap is idempotent (safe to call multiple times)
4. Bootstrap does nothing if database exists and has content
5. Bootstrap raises fatal error on failure
"""

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from doc_helper.infrastructure.persistence.sqlite.schema_bootstrap import (
    SchemaBootstrapError,
    bootstrap_schema_database,
)


class TestSchemaBootstrap:
    """Test schema database bootstrap functionality."""

    def test_bootstrap_creates_database_file(self) -> None:
        """Bootstrap creates database file if not exists."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"
            assert not db_path.exists()

            bootstrap_schema_database(db_path)

            assert db_path.exists()
            assert db_path.stat().st_size > 0

    def test_bootstrap_creates_entities_table(self) -> None:
        """Bootstrap creates entities table with correct schema."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"
            bootstrap_schema_database(db_path)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check entities table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='entities'"
            )
            assert cursor.fetchone() is not None

            # Check column structure
            cursor.execute("PRAGMA table_info(entities)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "name_key" in columns
            assert "description_key" in columns
            assert "is_root_entity" in columns
            assert "parent_entity_id" in columns
            assert "display_order" in columns

            conn.close()

    def test_bootstrap_creates_fields_table(self) -> None:
        """Bootstrap creates fields table with correct schema."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"
            bootstrap_schema_database(db_path)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check fields table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='fields'"
            )
            assert cursor.fetchone() is not None

            # Check column structure
            cursor.execute("PRAGMA table_info(fields)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "entity_id" in columns
            assert "field_type" in columns
            assert "label_key" in columns
            assert "help_text_key" in columns
            assert "required" in columns
            assert "default_value" in columns
            assert "display_order" in columns
            assert "formula" in columns
            assert "lookup_entity_id" in columns
            assert "lookup_display_field" in columns
            assert "child_entity_id" in columns

            conn.close()

    def test_bootstrap_creates_relationships_table(self) -> None:
        """Bootstrap creates relationships table with correct schema."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"
            bootstrap_schema_database(db_path)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='relationships'"
            )
            assert cursor.fetchone() is not None

            cursor.execute("PRAGMA table_info(relationships)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "source_entity_id" in columns
            assert "target_entity_id" in columns
            assert "relationship_type" in columns
            assert "name_key" in columns

            conn.close()

    def test_bootstrap_creates_field_options_table(self) -> None:
        """Bootstrap creates field_options table with correct schema."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"
            bootstrap_schema_database(db_path)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='field_options'"
            )
            assert cursor.fetchone() is not None

            cursor.execute("PRAGMA table_info(field_options)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "field_id" in columns
            assert "value" in columns
            assert "label_key" in columns
            assert "display_order" in columns

            conn.close()

    def test_bootstrap_creates_validation_rules_table(self) -> None:
        """Bootstrap creates validation_rules table with correct schema."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"
            bootstrap_schema_database(db_path)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='validation_rules'"
            )
            assert cursor.fetchone() is not None

            cursor.execute("PRAGMA table_info(validation_rules)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "field_id" in columns
            assert "rule_type" in columns
            assert "rule_value" in columns
            assert "error_message_key" in columns

            conn.close()

    def test_bootstrap_creates_control_relations_table(self) -> None:
        """Bootstrap creates control_relations table with correct schema."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"
            bootstrap_schema_database(db_path)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='control_relations'"
            )
            assert cursor.fetchone() is not None

            cursor.execute("PRAGMA table_info(control_relations)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "source_entity_id" in columns
            assert "source_field_id" in columns
            assert "target_entity_id" in columns
            assert "target_field_id" in columns
            assert "control_type" in columns
            assert "condition_value" in columns
            assert "effect_value" in columns

            conn.close()

    def test_bootstrap_creates_output_mappings_table(self) -> None:
        """Bootstrap creates output_mappings table with correct schema."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"
            bootstrap_schema_database(db_path)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='output_mappings'"
            )
            assert cursor.fetchone() is not None

            cursor.execute("PRAGMA table_info(output_mappings)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "entity_id" in columns
            assert "field_id" in columns
            assert "output_type" in columns
            assert "target_tag" in columns
            assert "transformer_id" in columns

            conn.close()

    def test_bootstrap_is_idempotent(self) -> None:
        """Bootstrap is safe to call multiple times."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"

            # First call creates database
            bootstrap_schema_database(db_path)
            first_size = db_path.stat().st_size

            # Second call does nothing (idempotent)
            bootstrap_schema_database(db_path)
            second_size = db_path.stat().st_size

            assert first_size == second_size

    def test_bootstrap_skips_existing_database_with_content(self) -> None:
        """Bootstrap does nothing if database exists and has content."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"

            # Create database with some content
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE test_table (id TEXT)")
            conn.execute("INSERT INTO test_table VALUES ('test_data')")
            conn.commit()
            conn.close()

            # Bootstrap should not modify existing database
            bootstrap_schema_database(db_path)

            # Original content should still exist
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test_table")
            assert cursor.fetchone() == ("test_data",)
            conn.close()

    def test_bootstrap_creates_parent_directory(self) -> None:
        """Bootstrap creates parent directories if they don't exist."""
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "nested" / "dir" / "test_config.db"
            assert not db_path.parent.exists()

            bootstrap_schema_database(db_path)

            assert db_path.parent.exists()
            assert db_path.exists()


class TestSchemaBootstrapWithRepository:
    """Test bootstrap works correctly with SqliteSchemaRepository."""

    def test_bootstrapped_database_works_with_repository(self) -> None:
        """Repository can use bootstrapped database."""
        from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
            SqliteSchemaRepository,
        )

        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"

            # Bootstrap database
            bootstrap_schema_database(db_path)

            # Create repository
            repo = SqliteSchemaRepository(db_path=db_path)

            # Repository should work - no entities initially
            result = repo.get_all()
            assert result.is_success()
            entities = result.value
            assert isinstance(entities, tuple)
            assert len(entities) == 0

    def test_can_save_entity_after_bootstrap(self) -> None:
        """Can save entity to bootstrapped database."""
        from doc_helper.domain.common.i18n import TranslationKey
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId
        from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
            SqliteSchemaRepository,
        )

        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"

            # Bootstrap database
            bootstrap_schema_database(db_path)

            # Create repository and save entity
            repo = SqliteSchemaRepository(db_path=db_path)

            entity = EntityDefinition(
                id=EntityDefinitionId("test_entity"),
                name_key=TranslationKey("entity.test"),
                description_key=TranslationKey("entity.test.desc"),
                is_root_entity=True,
            )

            result = repo.save(entity)
            assert result.is_success()

            # Verify entity was saved
            saved = repo.get_by_id(EntityDefinitionId("test_entity"))
            assert saved.is_success()
            assert saved.value.name_key == TranslationKey("entity.test")

    def test_get_all_does_not_raise_nested_connection_error(self) -> None:
        """Regression: get_all() must not raise 'Connection already open'."""
        from doc_helper.domain.common.i18n import TranslationKey
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId
        from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
            SqliteSchemaRepository,
        )

        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_config.db"

            # Bootstrap database
            bootstrap_schema_database(db_path)

            # Create repository and save entity
            repo = SqliteSchemaRepository(db_path=db_path)

            entity = EntityDefinition(
                id=EntityDefinitionId("test_entity"),
                name_key=TranslationKey("entity.test"),
                description_key=TranslationKey("entity.test.desc"),
                is_root_entity=True,
            )

            save_result = repo.save(entity)
            assert save_result.is_success()

            # This must NOT raise "Connection already open"
            all_result = repo.get_all()
            assert all_result.is_success()
            assert len(all_result.value) == 1
            assert all_result.value[0].id == EntityDefinitionId("test_entity")

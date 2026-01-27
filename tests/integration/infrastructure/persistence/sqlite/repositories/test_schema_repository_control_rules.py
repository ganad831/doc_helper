"""Integration tests for control rules persistence (Phase A5.4).

Tests that control rules are correctly persisted to and loaded from
the control_rules table in SQLite.

PHASE A5.4 SCOPE:
- Persistence only (no runtime execution)
- Design-time metadata storage
- Roundtrip verification (save + reload)
- Defensive read behavior for corrupted data
"""

import pytest
import sqlite3
from pathlib import Path
from dataclasses import replace

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.application.dto.export_dto import ControlRuleExportDTO
from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
    SqliteSchemaRepository,
)


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Create temporary test database with control_rules table."""
    db_path = tmp_path / "test_control_rules.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create entities table
    cursor.execute(
        """
        CREATE TABLE entities (
            id TEXT PRIMARY KEY,
            name_key TEXT NOT NULL,
            description_key TEXT,
            is_root_entity INTEGER NOT NULL DEFAULT 0,
            parent_entity_id TEXT,
            display_order INTEGER DEFAULT 0
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
            required INTEGER NOT NULL DEFAULT 0,
            default_value TEXT,
            display_order INTEGER DEFAULT 0,
            formula TEXT,
            lookup_entity_id TEXT,
            lookup_display_field TEXT,
            child_entity_id TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities(id)
        )
        """
    )

    # Create validation_rules table (required for schema repository)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS validation_rules (
            id TEXT PRIMARY KEY,
            field_id TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            rule_value TEXT,
            error_message_key TEXT,
            FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
        )
        """
    )

    # Create control_rules table (Phase A5.4)
    cursor.execute(
        """
        CREATE TABLE control_rules (
            field_id TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            formula_text TEXT NOT NULL,
            UNIQUE (field_id, rule_type),
            FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_control_rules_field ON control_rules(field_id)
        """
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def repository(test_db_path: Path) -> SqliteSchemaRepository:
    """Create repository instance."""
    return SqliteSchemaRepository(test_db_path)


class TestControlRulesPersistenceRoundtrip:
    """Infrastructure roundtrip tests for control rules persistence (Phase A5.4)."""

    def test_control_rule_roundtrip_single_rule(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should persist and reload a single control rule correctly.

        This is the MANDATORY roundtrip test specified in Phase A5.4:
        1. Create entity + field
        2. Add control rule
        3. Save schema
        4. Reload schema
        5. Assert: exactly one rule exists, rule_type matches, formula_text matches
        """
        # Create control rule DTO
        visibility_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="optional_field",
            formula_text="is_advanced_mode == true",
        )

        # Create field with control rule
        field_with_rule = FieldDefinition(
            id=FieldDefinitionId("optional_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.optional"),
            required=False,
            control_rules=(visibility_rule,),
        )

        # Create entity with field
        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            fields={field_with_rule.id: field_with_rule},
            is_root_entity=True,
        )

        # Save entity
        save_result = repository.save(entity)
        assert save_result.is_success(), f"Save failed: {save_result.error}"

        # Reload entity (fresh load from database)
        load_result = repository.get_by_id(entity.id)
        assert load_result.is_success(), f"Load failed: {load_result.error}"

        # Get loaded field
        loaded_entity = load_result.value
        loaded_field = loaded_entity.fields[FieldDefinitionId("optional_field")]

        # Assert: exactly one rule exists
        assert len(loaded_field.control_rules) == 1, (
            f"Expected exactly 1 control rule, got {len(loaded_field.control_rules)}"
        )

        # Assert: rule_type matches
        loaded_rule = loaded_field.control_rules[0]
        assert loaded_rule.rule_type == "VISIBILITY", (
            f"Expected rule_type 'VISIBILITY', got '{loaded_rule.rule_type}'"
        )

        # Assert: formula_text matches
        assert loaded_rule.formula_text == "is_advanced_mode == true", (
            f"Expected formula_text 'is_advanced_mode == true', got '{loaded_rule.formula_text}'"
        )

    def test_control_rule_roundtrip_multiple_rules(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should persist and reload multiple control rules on same field."""
        # Create control rules for different types
        visibility_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="multi_rule_field",
            formula_text="show_advanced == true",
        )
        enabled_rule = ControlRuleExportDTO(
            rule_type="ENABLED",
            target_field_id="multi_rule_field",
            formula_text="is_editable == true",
        )
        required_rule = ControlRuleExportDTO(
            rule_type="REQUIRED",
            target_field_id="multi_rule_field",
            formula_text="mandatory_mode == true",
        )

        # Create field with multiple control rules
        field_with_rules = FieldDefinition(
            id=FieldDefinitionId("multi_rule_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.multi_rule"),
            required=False,
            control_rules=(visibility_rule, enabled_rule, required_rule),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("multi_rule_entity"),
            name_key=TranslationKey("entity.multi_rule"),
            fields={field_with_rules.id: field_with_rules},
            is_root_entity=True,
        )

        # Save and reload
        save_result = repository.save(entity)
        assert save_result.is_success()

        load_result = repository.get_by_id(entity.id)
        assert load_result.is_success()

        loaded_field = load_result.value.fields[FieldDefinitionId("multi_rule_field")]

        # Assert: all 3 rules exist
        assert len(loaded_field.control_rules) == 3

        # Check each rule type and formula
        rule_map = {r.rule_type: r.formula_text for r in loaded_field.control_rules}
        assert rule_map.get("VISIBILITY") == "show_advanced == true"
        assert rule_map.get("ENABLED") == "is_editable == true"
        assert rule_map.get("REQUIRED") == "mandatory_mode == true"

    def test_control_rule_update_replaces_existing(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should replace existing control rule when saving updated field."""
        # Initial control rule
        initial_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="update_field",
            formula_text="initial_formula == true",
        )

        field = FieldDefinition(
            id=FieldDefinitionId("update_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.update"),
            required=False,
            control_rules=(initial_rule,),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("update_entity"),
            name_key=TranslationKey("entity.update"),
            fields={field.id: field},
            is_root_entity=True,
        )

        # Save initial
        repository.save(entity)

        # Update control rule formula
        updated_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="update_field",
            formula_text="updated_formula == false",
        )

        updated_field = replace(field, control_rules=(updated_rule,))
        updated_entity = replace(entity, fields={updated_field.id: updated_field})

        # Save updated
        save_result = repository.save(updated_entity)
        assert save_result.is_success()

        # Reload and verify
        load_result = repository.get_by_id(entity.id)
        loaded_field = load_result.value.fields[FieldDefinitionId("update_field")]

        # Should have exactly one rule with updated formula
        assert len(loaded_field.control_rules) == 1
        assert loaded_field.control_rules[0].formula_text == "updated_formula == false"


class TestControlRulesDefensiveRead:
    """Defensive read behavior tests for control rules (Phase A5.4)."""

    def test_ignores_unknown_rule_type(
        self, test_db_path: Path, repository: SqliteSchemaRepository
    ) -> None:
        """Should ignore rows with unknown rule_type (not crash)."""
        # Create field without control rules
        field = FieldDefinition(
            id=FieldDefinitionId("defensive_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.defensive"),
            required=False,
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("defensive_entity"),
            name_key=TranslationKey("entity.defensive"),
            fields={field.id: field},
            is_root_entity=True,
        )

        # Save entity (creates field but no control rules)
        repository.save(entity)

        # Manually insert corrupted data with unknown rule_type
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO control_rules (field_id, rule_type, formula_text)
            VALUES (?, ?, ?)
            """,
            ("defensive_field", "UNKNOWN_TYPE", "some_formula == true"),
        )
        conn.commit()
        conn.close()

        # Reload - should NOT crash, should return empty control_rules
        load_result = repository.get_by_id(entity.id)
        assert load_result.is_success()

        loaded_field = load_result.value.fields[FieldDefinitionId("defensive_field")]
        assert len(loaded_field.control_rules) == 0

    def test_ignores_empty_formula_text(
        self, test_db_path: Path, repository: SqliteSchemaRepository
    ) -> None:
        """Should ignore rows with NULL or empty formula_text (not crash)."""
        # Create field
        field = FieldDefinition(
            id=FieldDefinitionId("empty_formula_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.empty_formula"),
            required=False,
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("empty_formula_entity"),
            name_key=TranslationKey("entity.empty_formula"),
            fields={field.id: field},
            is_root_entity=True,
        )

        repository.save(entity)

        # Manually insert corrupted data with empty formula_text
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO control_rules (field_id, rule_type, formula_text)
            VALUES (?, ?, ?)
            """,
            ("empty_formula_field", "VISIBILITY", ""),
        )
        cursor.execute(
            """
            INSERT INTO control_rules (field_id, rule_type, formula_text)
            VALUES (?, ?, ?)
            """,
            ("empty_formula_field", "ENABLED", "   "),  # whitespace only
        )
        conn.commit()
        conn.close()

        # Reload - should NOT crash, should return empty control_rules
        load_result = repository.get_by_id(entity.id)
        assert load_result.is_success()

        loaded_field = load_result.value.fields[FieldDefinitionId("empty_formula_field")]
        assert len(loaded_field.control_rules) == 0

    def test_ignores_valid_and_invalid_mixed(
        self, test_db_path: Path, repository: SqliteSchemaRepository
    ) -> None:
        """Should load valid rules and skip invalid ones."""
        # Create field with a valid rule
        valid_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="mixed_field",
            formula_text="valid_formula == true",
        )

        field = FieldDefinition(
            id=FieldDefinitionId("mixed_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.mixed"),
            required=False,
            control_rules=(valid_rule,),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("mixed_entity"),
            name_key=TranslationKey("entity.mixed"),
            fields={field.id: field},
            is_root_entity=True,
        )

        repository.save(entity)

        # Manually insert invalid rows
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        # Unknown type - should be skipped
        cursor.execute(
            """
            INSERT OR REPLACE INTO control_rules (field_id, rule_type, formula_text)
            VALUES (?, ?, ?)
            """,
            ("mixed_field", "INVALID_TYPE", "bad_formula"),
        )
        conn.commit()
        conn.close()

        # Reload - should have only the valid VISIBILITY rule
        load_result = repository.get_by_id(entity.id)
        assert load_result.is_success()

        loaded_field = load_result.value.fields[FieldDefinitionId("mixed_field")]
        assert len(loaded_field.control_rules) == 1
        assert loaded_field.control_rules[0].rule_type == "VISIBILITY"
        assert loaded_field.control_rules[0].formula_text == "valid_formula == true"


class TestControlRulesTableMigration:
    """Test that control_rules table is created in existing databases."""

    def test_migration_creates_table_in_existing_db(self, tmp_path: Path) -> None:
        """Should create control_rules table when bootstrapping existing database."""
        from doc_helper.infrastructure.persistence.sqlite.schema_bootstrap import (
            bootstrap_schema_database,
        )

        db_path = tmp_path / "existing_db.db"

        # Create database WITHOUT control_rules table (simulates old database)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE entities (
                id TEXT PRIMARY KEY,
                name_key TEXT NOT NULL,
                description_key TEXT,
                is_root_entity INTEGER NOT NULL DEFAULT 0,
                parent_entity_id TEXT,
                display_order INTEGER DEFAULT 0
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE fields (
                id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                field_type TEXT NOT NULL,
                label_key TEXT NOT NULL,
                help_text_key TEXT,
                required INTEGER NOT NULL DEFAULT 0,
                default_value TEXT,
                display_order INTEGER DEFAULT 0,
                formula TEXT,
                lookup_entity_id TEXT,
                lookup_display_field TEXT,
                child_entity_id TEXT,
                FOREIGN KEY (entity_id) REFERENCES entities(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS validation_rules (
                id TEXT PRIMARY KEY,
                field_id TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                rule_value TEXT,
                error_message_key TEXT,
                FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()
        conn.close()

        # Verify control_rules table does NOT exist yet
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='control_rules'"
        )
        assert cursor.fetchone() is None, "control_rules table should not exist yet"
        conn.close()

        # Run bootstrap on existing database - should create control_rules table
        bootstrap_schema_database(db_path)

        # Verify control_rules table NOW exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='control_rules'"
        )
        result = cursor.fetchone()
        assert result is not None, "control_rules table should exist after migration"
        assert result[0] == "control_rules"
        conn.close()

        # Verify we can use the repository with this database
        repository = SqliteSchemaRepository(db_path)

        # Create field with control rule - should work now
        control_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="test == true",
        )

        field = FieldDefinition(
            id=FieldDefinitionId("test_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.test"),
            required=False,
            control_rules=(control_rule,),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            fields={field.id: field},
            is_root_entity=True,
        )

        # This should succeed (not raise "no such table: control_rules")
        save_result = repository.save(entity)
        assert save_result.is_success(), f"Save should succeed: {save_result.error}"


class TestControlRulesCascadeDelete:
    """Test that control rules are deleted when parent field is deleted."""

    def test_control_rules_deleted_with_field(
        self, test_db_path: Path, repository: SqliteSchemaRepository
    ) -> None:
        """Should delete control rules when field is removed from entity."""
        # Create field with control rule
        rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="cascade_field",
            formula_text="test == true",
        )

        field = FieldDefinition(
            id=FieldDefinitionId("cascade_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.cascade"),
            required=False,
            control_rules=(rule,),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("cascade_entity"),
            name_key=TranslationKey("entity.cascade"),
            fields={field.id: field},
            is_root_entity=True,
        )

        # Save entity with field and control rule
        repository.save(entity)

        # Verify control rule exists in database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM control_rules WHERE field_id = ?", ("cascade_field",))
        count_before = cursor.fetchone()[0]
        assert count_before == 1
        conn.close()

        # Remove field from entity and save
        empty_entity = replace(entity, fields={})
        repository.save(empty_entity)

        # Verify control rule was deleted (via ON DELETE CASCADE)
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM control_rules WHERE field_id = ?", ("cascade_field",))
        count_after = cursor.fetchone()[0]
        assert count_after == 0
        conn.close()

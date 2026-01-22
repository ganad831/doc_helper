"""Integration tests for schema repository dependency queries (Phase 2 Step 3)."""

import sqlite3
import pytest
from pathlib import Path

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
    SqliteSchemaRepository,
)


class TestSchemaRepositoryDependencies:
    """Integration tests for dependency query methods."""

    @pytest.fixture
    def test_db_path(self, tmp_path: Path) -> Path:
        """Create temporary test database with schema."""
        db_path = tmp_path / "test_dependencies.db"

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

        # Create control_relations table (optional - for control dependency tests)
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
    # Entity Dependencies Tests
    # =========================================================================

    def test_get_entity_dependencies_no_dependencies(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should return empty dependencies for entity with no references."""
        # Create entity with no dependencies
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("standalone_entity", "entity.standalone", 0),
        )
        connection.commit()

        # Execute
        result = repository.get_entity_dependencies(EntityDefinitionId("standalone_entity"))

        # Assert
        assert result.is_success()
        deps = result.value
        assert deps["referenced_by_table_fields"] == []
        assert deps["referenced_by_lookup_fields"] == []
        assert deps["child_entities"] == []

    def test_get_entity_dependencies_referenced_by_table_field(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should find TABLE fields referencing entity."""
        cursor = connection.cursor()

        # Create target entity (will be referenced)
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("borehole", "entity.borehole", 0),
        )

        # Create source entity (has TABLE field)
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("project", "entity.project", 1),
        )

        # Create TABLE field referencing borehole
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order, child_entity_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("boreholes_table", "project", "TABLE", "field.boreholes", 0, 0, "borehole"),
        )

        connection.commit()

        # Execute
        result = repository.get_entity_dependencies(EntityDefinitionId("borehole"))

        # Assert
        assert result.is_success()
        deps = result.value
        assert ("project", "boreholes_table") in deps["referenced_by_table_fields"]
        assert deps["referenced_by_lookup_fields"] == []
        assert deps["child_entities"] == []

    def test_get_entity_dependencies_referenced_by_lookup_field(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should find LOOKUP fields referencing entity."""
        cursor = connection.cursor()

        # Create target entity (will be referenced)
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("contractor", "entity.contractor", 0),
        )

        # Create source entity (has LOOKUP field)
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("project", "entity.project", 1),
        )

        # Create LOOKUP field referencing contractor
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order, lookup_entity_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("contractor_lookup", "project", "LOOKUP", "field.contractor", 0, 0, "contractor"),
        )

        connection.commit()

        # Execute
        result = repository.get_entity_dependencies(EntityDefinitionId("contractor"))

        # Assert
        assert result.is_success()
        deps = result.value
        assert deps["referenced_by_table_fields"] == []
        assert ("project", "contractor_lookup") in deps["referenced_by_lookup_fields"]
        assert deps["child_entities"] == []

    def test_get_entity_dependencies_has_child_entities(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should find child entities with parent_entity_id."""
        cursor = connection.cursor()

        # Create parent entity
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("project", "entity.project", 1),
        )

        # Create child entities
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity, parent_entity_id) VALUES (?, ?, ?, ?)",
            ("borehole", "entity.borehole", 0, "project"),
        )
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity, parent_entity_id) VALUES (?, ?, ?, ?)",
            ("lab_test", "entity.lab_test", 0, "project"),
        )

        connection.commit()

        # Execute
        result = repository.get_entity_dependencies(EntityDefinitionId("project"))

        # Assert
        assert result.is_success()
        deps = result.value
        assert deps["referenced_by_table_fields"] == []
        assert deps["referenced_by_lookup_fields"] == []
        assert "borehole" in deps["child_entities"]
        assert "lab_test" in deps["child_entities"]

    def test_get_entity_dependencies_nonexistent_entity(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should return failure for non-existent entity."""
        result = repository.get_entity_dependencies(EntityDefinitionId("nonexistent"))

        assert result.is_failure()
        assert "does not exist" in result.error.lower()

    # =========================================================================
    # Field Dependencies Tests
    # =========================================================================

    def test_get_field_dependencies_no_dependencies(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should return empty dependencies for field with no references."""
        cursor = connection.cursor()

        # Create entity with standalone field
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("project", "entity.project", 1),
        )
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("site_name", "project", "TEXT", "field.site_name", 0, 0),
        )
        connection.commit()

        # Execute
        result = repository.get_field_dependencies(
            EntityDefinitionId("project"), FieldDefinitionId("site_name")
        )

        # Assert
        assert result.is_success()
        deps = result.value
        assert deps["referenced_by_formulas"] == []
        assert deps["referenced_by_controls_source"] == []
        assert deps["referenced_by_controls_target"] == []
        assert deps["referenced_by_lookup_display"] == []

    def test_get_field_dependencies_referenced_by_formula(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should find formulas referencing field."""
        cursor = connection.cursor()

        # Create entity
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("project", "entity.project", 1),
        )

        # Create source field (will be referenced in formula)
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("depth_from", "project", "NUMBER", "field.depth_from", 0, 0),
        )

        # Create calculated field with formula referencing depth_from
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order, formula)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "depth_total",
                "project",
                "CALCULATED",
                "field.depth_total",
                0,
                1,
                "{{depth_from}} + {{depth_to}}",
            ),
        )

        connection.commit()

        # Execute
        result = repository.get_field_dependencies(
            EntityDefinitionId("project"), FieldDefinitionId("depth_from")
        )

        # Assert
        assert result.is_success()
        deps = result.value
        assert ("project", "depth_total") in deps["referenced_by_formulas"]

    def test_get_field_dependencies_referenced_by_control_source(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should find control rules where field is source."""
        cursor = connection.cursor()

        # Create entity
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("project", "entity.project", 1),
        )

        # Create source field
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("soil_type", "project", "DROPDOWN", "field.soil_type", 0, 0),
        )

        # Create target field
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("sand_density", "project", "NUMBER", "field.sand_density", 0, 1),
        )

        # Create control relation (source -> target)
        cursor.execute(
            """
            INSERT INTO control_relations (source_entity_id, source_field_id, target_entity_id, target_field_id, effect_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("project", "soil_type", "project", "sand_density", "VISIBILITY"),
        )

        connection.commit()

        # Execute
        result = repository.get_field_dependencies(
            EntityDefinitionId("project"), FieldDefinitionId("soil_type")
        )

        # Assert
        assert result.is_success()
        deps = result.value
        assert ("project", "sand_density") in deps["referenced_by_controls_source"]

    def test_get_field_dependencies_referenced_by_lookup_display(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should find LOOKUP fields using field as lookup_display_field."""
        cursor = connection.cursor()

        # Create entities
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("contractor", "entity.contractor", 0),
        )
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("project", "entity.project", 1),
        )

        # Create field in contractor entity (will be used as lookup_display_field)
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("contractor_name", "contractor", "TEXT", "field.contractor_name", 1, 0),
        )

        # Create LOOKUP field using contractor_name as display field
        cursor.execute(
            """
            INSERT INTO fields (id, entity_id, field_type, label_key, required, display_order, lookup_entity_id, lookup_display_field)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "contractor_lookup",
                "project",
                "LOOKUP",
                "field.contractor",
                0,
                0,
                "contractor",
                "contractor_name",
            ),
        )

        connection.commit()

        # Execute
        result = repository.get_field_dependencies(
            EntityDefinitionId("contractor"), FieldDefinitionId("contractor_name")
        )

        # Assert
        assert result.is_success()
        deps = result.value
        assert ("project", "contractor_lookup") in deps["referenced_by_lookup_display"]

    def test_get_field_dependencies_nonexistent_entity(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should return failure for non-existent entity."""
        result = repository.get_field_dependencies(
            EntityDefinitionId("nonexistent"), FieldDefinitionId("field")
        )

        assert result.is_failure()
        assert "does not exist" in result.error.lower()

    def test_get_field_dependencies_nonexistent_field(
        self, repository: SqliteSchemaRepository, connection: sqlite3.Connection
    ) -> None:
        """Should return failure for non-existent field."""
        cursor = connection.cursor()

        # Create entity
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("project", "entity.project", 1),
        )
        connection.commit()

        # Execute with non-existent field
        result = repository.get_field_dependencies(
            EntityDefinitionId("project"), FieldDefinitionId("nonexistent_field")
        )

        assert result.is_failure()
        assert "not found" in result.error.lower()

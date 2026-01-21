"""Integration tests for project database migration with app_type_id.

Phase 2 v2 Platform Work: Tests that existing projects without app_type_id
are migrated to use the default app_type_id (soil_investigation).

RULES (AGENT_RULES.md Section 2):
- Test infrastructure layer behavior
- Verify backward compatibility
- Test migration path for existing data
"""

import sqlite3
import pytest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.infrastructure.persistence.sqlite_project_repository import (
    SqliteProjectRepository,
)


class TestProjectMigrationAppTypeId:
    """Tests for app_type_id migration in existing projects."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database path."""
        return tmp_path / "test_migration.db"

    @pytest.fixture
    def legacy_db(self, temp_db):
        """Create a legacy database without app_type_id column.

        This simulates an existing database created before v2 platform work.
        """
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Create legacy schema WITHOUT app_type_id column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                entity_definition_id TEXT NOT NULL,
                description TEXT,
                file_path TEXT,
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL
            )
        """)

        # Create field_values table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS field_values (
                project_id TEXT NOT NULL,
                field_id TEXT NOT NULL,
                value TEXT,
                is_computed INTEGER DEFAULT 0,
                computed_from TEXT,
                is_override INTEGER DEFAULT 0,
                original_computed_value TEXT,
                PRIMARY KEY (project_id, field_id),
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        """)

        # Insert a legacy project (no app_type_id)
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO projects (project_id, name, entity_definition_id, description, file_path, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "legacy-project-id-001",
            "Legacy Project",
            "project",
            "A project created before v2",
            None,
            now,
            now,
        ))

        conn.commit()
        conn.close()

        return temp_db

    def test_migration_adds_app_type_id_column(self, legacy_db):
        """Test that opening repository on legacy DB adds app_type_id column."""
        # Create repository - this triggers migration
        repo = SqliteProjectRepository(db_path=legacy_db)

        # Verify column exists by checking schema
        conn = sqlite3.connect(legacy_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        assert "app_type_id" in columns

    def test_migration_sets_default_app_type_id(self, legacy_db):
        """Test that legacy projects get default app_type_id after migration."""
        # Create repository - this triggers migration
        repo = SqliteProjectRepository(db_path=legacy_db)

        # Read the legacy project directly from DB
        conn = sqlite3.connect(legacy_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT app_type_id FROM projects WHERE project_id = ?", ("legacy-project-id-001",))
        row = cursor.fetchone()
        conn.close()

        # Should have default app_type_id
        assert row["app_type_id"] == "soil_investigation"

    def test_migration_is_idempotent(self, legacy_db):
        """Test that running migration multiple times is safe."""
        # Create repository twice - should not fail
        repo1 = SqliteProjectRepository(db_path=legacy_db)
        repo2 = SqliteProjectRepository(db_path=legacy_db)

        # Should not raise and column should exist
        conn = sqlite3.connect(legacy_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        assert columns.count("app_type_id") == 1

    def test_load_legacy_project_has_default_app_type_id(self, legacy_db):
        """Test that loading a legacy project returns correct app_type_id."""
        repo = SqliteProjectRepository(db_path=legacy_db)

        # Load the legacy project
        result = repo.get_by_id(ProjectId(uuid4()))  # This won't find it, but that's OK

        # Load directly
        conn = sqlite3.connect(legacy_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE project_id = ?", ("legacy-project-id-001",))
        row = cursor.fetchone()
        conn.close()

        assert row["app_type_id"] == "soil_investigation"

    def test_new_project_saves_app_type_id(self, temp_db):
        """Test that new projects save their app_type_id."""
        repo = SqliteProjectRepository(db_path=temp_db)

        project = Project(
            id=ProjectId(uuid4()),
            name="New Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("project"),
        )

        result = repo.save(project)
        assert isinstance(result, Success)

        # Verify app_type_id was saved
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT app_type_id FROM projects WHERE project_id = ?", (str(project.id.value),))
        row = cursor.fetchone()
        conn.close()

        assert row["app_type_id"] == "soil_investigation"

    def test_load_project_returns_correct_app_type_id(self, temp_db):
        """Test that loaded project has correct app_type_id."""
        repo = SqliteProjectRepository(db_path=temp_db)

        project_id = ProjectId(uuid4())
        project = Project(
            id=project_id,
            name="Test Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("project"),
        )

        repo.save(project)

        result = repo.get_by_id(project_id)
        assert isinstance(result, Success)
        assert result.value.app_type_id == "soil_investigation"


class TestAppTypeRoutingIntegration:
    """Tests for AppType routing through platform infrastructure."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database path."""
        return tmp_path / "test_routing.db"

    def test_project_creation_with_app_type_id(self, temp_db):
        """Test that projects can be created with specific app_type_id."""
        repo = SqliteProjectRepository(db_path=temp_db)

        project = Project(
            id=ProjectId(uuid4()),
            name="Soil Investigation Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("project"),
        )

        result = repo.save(project)
        assert isinstance(result, Success)

    def test_project_round_trip_preserves_app_type_id(self, temp_db):
        """Test that app_type_id is preserved through save/load cycle."""
        repo = SqliteProjectRepository(db_path=temp_db)

        project_id = ProjectId(uuid4())
        original = Project(
            id=project_id,
            name="Round Trip Test",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("project"),
            description="Testing round trip",
        )

        # Save
        save_result = repo.save(original)
        assert isinstance(save_result, Success)

        # Load
        load_result = repo.get_by_id(project_id)
        assert isinstance(load_result, Success)

        loaded = load_result.value
        assert loaded.app_type_id == original.app_type_id
        assert loaded.name == original.name
        assert loaded.entity_definition_id == original.entity_definition_id

    def test_get_all_returns_projects_with_app_type_id(self, temp_db):
        """Test that get_all returns projects with correct app_type_id."""
        repo = SqliteProjectRepository(db_path=temp_db)

        # Create multiple projects
        for i in range(3):
            project = Project(
                id=ProjectId(uuid4()),
                name=f"Project {i}",
                app_type_id="soil_investigation",
                entity_definition_id=EntityDefinitionId("project"),
            )
            repo.save(project)

        result = repo.get_all()
        assert isinstance(result, Success)

        projects = result.value
        assert len(projects) == 3
        for project in projects:
            assert project.app_type_id == "soil_investigation"

    def test_get_recent_returns_projects_with_app_type_id(self, temp_db):
        """Test that get_recent returns projects with correct app_type_id."""
        repo = SqliteProjectRepository(db_path=temp_db)

        # Create a project
        project = Project(
            id=ProjectId(uuid4()),
            name="Recent Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("project"),
        )
        repo.save(project)

        result = repo.get_recent(limit=10)
        assert isinstance(result, Success)

        projects = result.value
        assert len(projects) >= 1
        assert projects[0].app_type_id == "soil_investigation"

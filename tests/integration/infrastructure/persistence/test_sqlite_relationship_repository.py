"""Integration tests for SqliteRelationshipRepository (Phase 6A - ADR-022).

Tests the repository implementation against a real SQLite database.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.relationship_type import RelationshipType
from doc_helper.domain.schema.schema_ids import (
    EntityDefinitionId,
    RelationshipDefinitionId,
)
from doc_helper.infrastructure.persistence.sqlite.repositories.relationship_repository import (
    SqliteRelationshipRepository,
)


class TestSqliteRelationshipRepository:
    """Tests for SqliteRelationshipRepository."""

    @pytest.fixture
    def temp_db(self) -> Path:
        """Create temporary database with required tables."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        # Create tables
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create entities table (required for FK relationships)
        cursor.execute("""
            CREATE TABLE entities (
                id TEXT PRIMARY KEY,
                name_key TEXT NOT NULL,
                description_key TEXT,
                is_root_entity INTEGER DEFAULT 0,
                parent_entity_id TEXT
            )
        """)

        # Insert test entities
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("project", "entity.project", 1),
        )
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("borehole", "entity.borehole", 0),
        )
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("sample", "entity.sample", 0),
        )
        cursor.execute(
            "INSERT INTO entities (id, name_key, is_root_entity) VALUES (?, ?, ?)",
            ("lab_test", "entity.lab_test", 0),
        )

        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        if db_path.exists():
            db_path.unlink()

    @pytest.fixture
    def repository(self, temp_db: Path) -> SqliteRelationshipRepository:
        """Create repository instance with temp database."""
        return SqliteRelationshipRepository(temp_db)

    @pytest.fixture
    def sample_relationship(self) -> RelationshipDefinition:
        """Create sample relationship for testing."""
        return RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.project_boreholes"),
            description_key=TranslationKey("relationship.project_boreholes.desc"),
            inverse_name_key=TranslationKey("relationship.borehole_project"),
        )

    # -------------------------------------------------------------------------
    # Repository Creation Tests
    # -------------------------------------------------------------------------

    def test_create_repository(self, temp_db: Path) -> None:
        """Repository should be created with valid database path."""
        repo = SqliteRelationshipRepository(temp_db)
        assert repo.db_path == temp_db

    def test_create_repository_with_invalid_path(self) -> None:
        """Repository should raise error for non-existent database."""
        with pytest.raises(FileNotFoundError):
            SqliteRelationshipRepository("nonexistent/path/to/db.db")

    def test_create_repository_requires_path(self) -> None:
        """Repository should require database path."""
        with pytest.raises(TypeError):
            SqliteRelationshipRepository(None)  # type: ignore

    def test_repository_creates_table_if_missing(self, temp_db: Path) -> None:
        """Repository should create relationships table if it doesn't exist."""
        # Verify table was created automatically by constructor
        repo = SqliteRelationshipRepository(temp_db)

        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='relationships'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "relationships"

    # -------------------------------------------------------------------------
    # Save Tests (ADD-ONLY)
    # -------------------------------------------------------------------------

    def test_save_new_relationship(
        self,
        repository: SqliteRelationshipRepository,
        sample_relationship: RelationshipDefinition,
    ) -> None:
        """save should successfully save new relationship."""
        result = repository.save(sample_relationship)

        assert isinstance(result, Success)
        assert result.value is None

        # Verify saved
        assert repository.exists(sample_relationship.id) is True

    def test_save_relationship_with_minimal_fields(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """save should work with only required fields."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("minimal_rel"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.REFERENCES,
            name_key=TranslationKey("relationship.minimal"),
        )

        result = repository.save(relationship)
        assert isinstance(result, Success)

        # Verify saved
        get_result = repository.get_by_id(relationship.id)
        assert isinstance(get_result, Success)
        assert get_result.value.description_key is None
        assert get_result.value.inverse_name_key is None

    def test_save_duplicate_fails_add_only(
        self,
        repository: SqliteRelationshipRepository,
        sample_relationship: RelationshipDefinition,
    ) -> None:
        """save should fail for existing relationship (ADD-ONLY semantics)."""
        # Save first time
        result1 = repository.save(sample_relationship)
        assert isinstance(result1, Success)

        # Attempt to save again should fail
        result2 = repository.save(sample_relationship)
        assert isinstance(result2, Failure)
        assert "already exists" in result2.error.lower()
        assert "ADD-ONLY" in result2.error

    def test_save_validates_source_entity_exists(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """save should fail if source entity doesn't exist."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("invalid_source"),
            source_entity_id=EntityDefinitionId("nonexistent"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )

        result = repository.save(relationship)
        assert isinstance(result, Failure)
        assert "source entity" in result.error.lower()
        assert "nonexistent" in result.error

    def test_save_validates_target_entity_exists(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """save should fail if target entity doesn't exist."""
        relationship = RelationshipDefinition(
            id=RelationshipDefinitionId("invalid_target"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("nonexistent"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test"),
        )

        result = repository.save(relationship)
        assert isinstance(result, Failure)
        assert "target entity" in result.error.lower()
        assert "nonexistent" in result.error

    # -------------------------------------------------------------------------
    # Get By ID Tests
    # -------------------------------------------------------------------------

    def test_get_by_id_existing(
        self,
        repository: SqliteRelationshipRepository,
        sample_relationship: RelationshipDefinition,
    ) -> None:
        """get_by_id should return relationship if exists."""
        repository.save(sample_relationship)

        result = repository.get_by_id(sample_relationship.id)

        assert isinstance(result, Success)
        rel = result.value
        assert rel.id == sample_relationship.id
        assert rel.source_entity_id == sample_relationship.source_entity_id
        assert rel.target_entity_id == sample_relationship.target_entity_id
        assert rel.relationship_type == sample_relationship.relationship_type
        assert rel.name_key == sample_relationship.name_key
        assert rel.description_key == sample_relationship.description_key
        assert rel.inverse_name_key == sample_relationship.inverse_name_key

    def test_get_by_id_nonexistent(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """get_by_id should return Failure for non-existent relationship."""
        result = repository.get_by_id(
            RelationshipDefinitionId("nonexistent")
        )

        assert isinstance(result, Failure)
        assert "not found" in result.error.lower()

    # -------------------------------------------------------------------------
    # Exists Tests
    # -------------------------------------------------------------------------

    def test_exists_for_existing(
        self,
        repository: SqliteRelationshipRepository,
        sample_relationship: RelationshipDefinition,
    ) -> None:
        """exists should return True for existing relationship."""
        repository.save(sample_relationship)
        assert repository.exists(sample_relationship.id) is True

    def test_exists_for_nonexistent(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """exists should return False for non-existent relationship."""
        assert repository.exists(
            RelationshipDefinitionId("nonexistent")
        ) is False

    # -------------------------------------------------------------------------
    # Get All Tests
    # -------------------------------------------------------------------------

    def test_get_all_empty(self, repository: SqliteRelationshipRepository) -> None:
        """get_all should return empty tuple when no relationships."""
        result = repository.get_all()

        assert isinstance(result, Success)
        assert result.value == ()

    def test_get_all_with_relationships(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """get_all should return all saved relationships."""
        rel1 = RelationshipDefinition(
            id=RelationshipDefinitionId("rel1"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.rel1"),
        )
        rel2 = RelationshipDefinition(
            id=RelationshipDefinitionId("rel2"),
            source_entity_id=EntityDefinitionId("borehole"),
            target_entity_id=EntityDefinitionId("sample"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.rel2"),
        )

        repository.save(rel1)
        repository.save(rel2)

        result = repository.get_all()

        assert isinstance(result, Success)
        assert len(result.value) == 2
        ids = {r.id.value for r in result.value}
        assert ids == {"rel1", "rel2"}

    # -------------------------------------------------------------------------
    # Get By Source Entity Tests
    # -------------------------------------------------------------------------

    def test_get_by_source_entity(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """get_by_source_entity should return relationships from source."""
        rel1 = RelationshipDefinition(
            id=RelationshipDefinitionId("project_to_borehole"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test1"),
        )
        rel2 = RelationshipDefinition(
            id=RelationshipDefinitionId("project_to_sample"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("sample"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test2"),
        )
        rel3 = RelationshipDefinition(
            id=RelationshipDefinitionId("borehole_to_sample"),
            source_entity_id=EntityDefinitionId("borehole"),
            target_entity_id=EntityDefinitionId("sample"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test3"),
        )

        repository.save(rel1)
        repository.save(rel2)
        repository.save(rel3)

        result = repository.get_by_source_entity(EntityDefinitionId("project"))

        assert isinstance(result, Success)
        assert len(result.value) == 2
        ids = {r.id.value for r in result.value}
        assert ids == {"project_to_borehole", "project_to_sample"}

    def test_get_by_source_entity_empty(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """get_by_source_entity should return empty for no matches."""
        result = repository.get_by_source_entity(EntityDefinitionId("project"))

        assert isinstance(result, Success)
        assert result.value == ()

    # -------------------------------------------------------------------------
    # Get By Target Entity Tests
    # -------------------------------------------------------------------------

    def test_get_by_target_entity(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """get_by_target_entity should return relationships to target."""
        rel1 = RelationshipDefinition(
            id=RelationshipDefinitionId("project_to_sample"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("sample"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test1"),
        )
        rel2 = RelationshipDefinition(
            id=RelationshipDefinitionId("borehole_to_sample"),
            source_entity_id=EntityDefinitionId("borehole"),
            target_entity_id=EntityDefinitionId("sample"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test2"),
        )

        repository.save(rel1)
        repository.save(rel2)

        result = repository.get_by_target_entity(EntityDefinitionId("sample"))

        assert isinstance(result, Success)
        assert len(result.value) == 2

    # -------------------------------------------------------------------------
    # Get By Entity (Both Directions) Tests
    # -------------------------------------------------------------------------

    def test_get_by_entity(self, repository: SqliteRelationshipRepository) -> None:
        """get_by_entity should return relationships in both directions."""
        rel1 = RelationshipDefinition(
            id=RelationshipDefinitionId("project_to_borehole"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test1"),
        )
        rel2 = RelationshipDefinition(
            id=RelationshipDefinitionId("borehole_to_sample"),
            source_entity_id=EntityDefinitionId("borehole"),
            target_entity_id=EntityDefinitionId("sample"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.test2"),
        )
        rel3 = RelationshipDefinition(
            id=RelationshipDefinitionId("lab_to_borehole"),
            source_entity_id=EntityDefinitionId("lab_test"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.REFERENCES,
            name_key=TranslationKey("relationship.test3"),
        )

        repository.save(rel1)
        repository.save(rel2)
        repository.save(rel3)

        # Borehole is involved in all 3 relationships:
        # - target of project_to_borehole
        # - source of borehole_to_sample
        # - target of lab_to_borehole
        result = repository.get_by_entity(EntityDefinitionId("borehole"))

        assert isinstance(result, Success)
        assert len(result.value) == 3

    # -------------------------------------------------------------------------
    # No Update/Delete Tests (ADD-ONLY Semantics)
    # -------------------------------------------------------------------------

    def test_no_update_method(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """Repository should NOT have update method (ADD-ONLY per ADR-022)."""
        assert not hasattr(repository, "update")

    def test_no_delete_method(
        self, repository: SqliteRelationshipRepository
    ) -> None:
        """Repository should NOT have delete method (ADD-ONLY per ADR-022)."""
        assert not hasattr(repository, "delete")

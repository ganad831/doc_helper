"""Integration tests for SqliteSchemaRepository."""

import pytest
from pathlib import Path

from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.infrastructure.persistence.sqlite_schema_repository import (
    SqliteSchemaRepository,
)


# Path to test database (using legacy app's config.db)
TEST_DB_PATH = Path("legacy_app/app_types/soil_report/config.db")


class TestSqliteSchemaRepository:
    """Tests for SqliteSchemaRepository."""

    @pytest.fixture
    def repository(self) -> SqliteSchemaRepository:
        """Create repository instance."""
        if not TEST_DB_PATH.exists():
            pytest.skip(f"Test database not found: {TEST_DB_PATH}")
        return SqliteSchemaRepository(TEST_DB_PATH)

    def test_create_repository(self) -> None:
        """Repository should be created with valid database path."""
        if not TEST_DB_PATH.exists():
            pytest.skip(f"Test database not found: {TEST_DB_PATH}")
        repo = SqliteSchemaRepository(TEST_DB_PATH)
        assert repo.db_path == TEST_DB_PATH

    def test_create_repository_with_invalid_path(self) -> None:
        """Repository should raise error for non-existent database."""
        with pytest.raises(FileNotFoundError):
            SqliteSchemaRepository("nonexistent/path/to/db.db")

    def test_create_repository_requires_path(self) -> None:
        """Repository should require database path."""
        with pytest.raises(TypeError):
            SqliteSchemaRepository(None)  # type: ignore

    def test_get_root_entity(self, repository: SqliteSchemaRepository) -> None:
        """get_root_entity should return root entity."""
        result = repository.get_root_entity()
        assert isinstance(result, Success)
        entity = result.value
        assert entity is not None
        assert entity.entity_id.value == "project"
        assert entity.name_key == "project"
        assert len(entity.field_definitions) > 0

    def test_get_by_id_existing_entity(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """get_by_id should return entity if exists."""
        result = repository.get_by_id(EntityDefinitionId("project"))
        assert isinstance(result, Success)
        entity = result.value
        assert entity.entity_id == EntityDefinitionId("project")
        assert entity.name_key == "project"
        assert len(entity.field_definitions) > 0

    def test_get_by_id_nonexistent_entity(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """get_by_id should return Failure for non-existent entity."""
        result = repository.get_by_id(EntityDefinitionId("nonexistent"))
        assert isinstance(result, Failure)
        assert "not found" in result.error.lower()

    def test_get_by_id_requires_entity_definition_id(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """get_by_id should require EntityDefinitionId."""
        result = repository.get_by_id("project")  # type: ignore
        assert isinstance(result, Failure)
        assert "EntityDefinitionId" in result.error

    def test_exists_for_existing_entity(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """exists should return True for existing entity."""
        assert repository.exists(EntityDefinitionId("project")) is True

    def test_exists_for_nonexistent_entity(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """exists should return False for non-existent entity."""
        assert repository.exists(EntityDefinitionId("nonexistent")) is False

    def test_exists_requires_entity_definition_id(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """exists should require EntityDefinitionId."""
        assert repository.exists("project") is False  # type: ignore

    def test_get_all(self, repository: SqliteSchemaRepository) -> None:
        """get_all should return all entities."""
        result = repository.get_all()
        assert isinstance(result, Success)
        entities = result.value
        assert len(entities) > 0
        # Should include at least the project entity
        entity_ids = [e.entity_id.value for e in entities]
        assert "project" in entity_ids

    def test_get_child_entities(self, repository: SqliteSchemaRepository) -> None:
        """get_child_entities should return child entities for parent."""
        # This test depends on the actual schema structure
        # If project has TABLE fields, their entities should be returned
        result = repository.get_child_entities(EntityDefinitionId("project"))
        assert isinstance(result, Success)
        # Result may be empty tuple if no TABLE fields exist

    def test_get_child_entities_requires_entity_definition_id(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """get_child_entities should require EntityDefinitionId."""
        result = repository.get_child_entities("project")  # type: ignore
        assert isinstance(result, Failure)
        assert "EntityDefinitionId" in result.error

    def test_loaded_entity_has_fields(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Loaded entity should have field definitions."""
        result = repository.get_by_id(EntityDefinitionId("project"))
        assert isinstance(result, Success)
        entity = result.value
        assert len(entity.field_definitions) > 0

        # Check at least one field
        first_field = entity.field_definitions[0]
        assert first_field.field_id.value
        assert first_field.name_key
        assert first_field.field_type is not None

    def test_loaded_fields_have_constraints(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Loaded fields should include constraints from validation_rules."""
        result = repository.get_by_id(EntityDefinitionId("project"))
        assert isinstance(result, Success)
        entity = result.value

        # Check if any field has constraints
        # (depends on actual schema, but at least verify structure)
        for field in entity.field_definitions:
            # Constraints should be a tuple (may be empty)
            assert isinstance(field.constraints, tuple)

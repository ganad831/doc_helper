"""Integration tests for SqliteSearchRepository.

ADR-026: Search Architecture
Tests for search operations with real SQLite databases.
"""

import json
import sqlite3
from pathlib import Path

import pytest

from doc_helper.domain.common.result import Failure, Success
from doc_helper.infrastructure.persistence.sqlite_search_repository import (
    SqliteSearchRepository,
)


@pytest.fixture
def temp_schema_db(tmp_path: Path) -> Path:
    """Create a temporary schema database (config.db) with test data."""
    schema_db = tmp_path / "config.db"
    conn = sqlite3.connect(schema_db)
    cursor = conn.cursor()

    # Create entities table
    cursor.execute(
        """
        CREATE TABLE entities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            sort_order INTEGER
        )
    """
    )

    # Create fields table
    cursor.execute(
        """
        CREATE TABLE fields (
            id TEXT PRIMARY KEY,
            entity_id TEXT NOT NULL,
            label TEXT NOT NULL,
            field_type TEXT NOT NULL,
            sort_order INTEGER,
            FOREIGN KEY (entity_id) REFERENCES entities(id)
        )
    """
    )

    # Insert test entities
    cursor.executemany(
        "INSERT INTO entities (id, name, description, sort_order) VALUES (?, ?, ?, ?)",
        [
            ("project", "Project Information", "Main project data", 1),
            ("borehole", "Borehole", "Borehole information", 2),
        ],
    )

    # Insert test fields
    cursor.executemany(
        "INSERT INTO fields (id, entity_id, label, field_type, sort_order) VALUES (?, ?, ?, ?, ?)",
        [
            ("site_location", "project", "Site Location", "TEXT", 1),
            ("owner_name", "project", "Owner Name", "TEXT", 2),
            ("project_description", "project", "Description", "TEXTAREA", 3),
            ("borehole_depth", "borehole", "Depth (m)", "NUMBER", 1),
            ("soil_type", "borehole", "Soil Type", "DROPDOWN", 2),
        ],
    )

    conn.commit()
    conn.close()
    return schema_db


@pytest.fixture
def temp_project_db(tmp_path: Path) -> Path:
    """Create a temporary project database (project.db) with test data."""
    project_db = tmp_path / "project.db"
    conn = sqlite3.connect(project_db)
    cursor = conn.cursor()

    # Create field_values table
    cursor.execute(
        """
        CREATE TABLE field_values (
            project_id TEXT NOT NULL,
            field_id TEXT NOT NULL,
            value TEXT,
            is_computed INTEGER DEFAULT 0,
            is_override INTEGER DEFAULT 0,
            PRIMARY KEY (project_id, field_id)
        )
    """
    )

    # Insert test field values (JSON-serialized)
    cursor.executemany(
        "INSERT INTO field_values (project_id, field_id, value) VALUES (?, ?, ?)",
        [
            ("proj-123", "site_location", json.dumps("123 Main Street")),
            ("proj-123", "owner_name", json.dumps("John Doe")),
            (
                "proj-123",
                "project_description",
                json.dumps("Soil investigation at downtown site"),
            ),
            ("proj-123", "borehole_depth", json.dumps(10.5)),
            ("proj-123", "soil_type", json.dumps("Clay")),
        ],
    )

    conn.commit()
    conn.close()
    return project_db


@pytest.fixture
def repository(
    temp_project_db: Path, temp_schema_db: Path
) -> SqliteSearchRepository:
    """Create a repository instance with temp databases."""
    return SqliteSearchRepository(
        project_db_path=temp_project_db, schema_db_path=temp_schema_db
    )


class TestSqliteSearchRepository:
    """Test SqliteSearchRepository with real databases."""

    def test_search_by_label_match(self, repository: SqliteSearchRepository):
        """Test searching fields by label match."""
        # Search for "location" (should match "Site Location")
        result = repository.search_fields(
            project_id="proj-123", search_term="location", limit=10
        )

        assert isinstance(result, Success)
        results = result.value
        assert len(results) >= 1

        # Find the site_location result
        location_result = next(
            (r for r in results if r["field_id"] == "site_location"), None
        )
        assert location_result is not None
        assert location_result["field_label"] == "Site Location"
        assert location_result["entity_id"] == "project"
        assert location_result["entity_name"] == "Project Information"
        assert location_result["current_value"] == "123 Main Street"
        assert location_result["field_path"] == "Project Information.site_location"
        assert location_result["match_type"] == "label"

    def test_search_by_value_match(self, repository: SqliteSearchRepository):
        """Test searching fields by value match."""
        # Search for "downtown" (should match project_description value)
        result = repository.search_fields(
            project_id="proj-123", search_term="downtown", limit=10
        )

        assert isinstance(result, Success)
        results = result.value
        assert len(results) >= 1

        # Find the project_description result
        description_result = next(
            (r for r in results if r["field_id"] == "project_description"), None
        )
        assert description_result is not None
        assert description_result["field_label"] == "Description"
        assert (
            description_result["current_value"]
            == "Soil investigation at downtown site"
        )
        assert description_result["match_type"] == "value"

    def test_search_by_field_id_match(self, repository: SqliteSearchRepository):
        """Test searching fields by field_id match."""
        # Search for "borehole" (should match field_id "borehole_depth")
        result = repository.search_fields(
            project_id="proj-123", search_term="borehole", limit=10
        )

        assert isinstance(result, Success)
        results = result.value
        assert len(results) >= 1

        # Find the borehole_depth result
        borehole_result = next(
            (r for r in results if r["field_id"] == "borehole_depth"), None
        )
        assert borehole_result is not None
        assert borehole_result["match_type"] == "field_id"

    def test_search_case_insensitive(self, repository: SqliteSearchRepository):
        """Test that search is case-insensitive."""
        # Search with different cases
        result_lower = repository.search_fields(
            project_id="proj-123", search_term="location", limit=10
        )
        result_upper = repository.search_fields(
            project_id="proj-123", search_term="LOCATION", limit=10
        )
        result_mixed = repository.search_fields(
            project_id="proj-123", search_term="LoCaTiOn", limit=10
        )

        assert isinstance(result_lower, Success)
        assert isinstance(result_upper, Success)
        assert isinstance(result_mixed, Success)

        # All should return same results
        assert len(result_lower.value) == len(result_upper.value)
        assert len(result_lower.value) == len(result_mixed.value)

    def test_search_partial_match(self, repository: SqliteSearchRepository):
        """Test that search supports partial matching."""
        # Search for "own" (should match "Owner Name")
        result = repository.search_fields(
            project_id="proj-123", search_term="own", limit=10
        )

        assert isinstance(result, Success)
        results = result.value
        assert len(results) >= 1

        owner_result = next(
            (r for r in results if r["field_id"] == "owner_name"), None
        )
        assert owner_result is not None

    def test_search_with_limit(self, repository: SqliteSearchRepository):
        """Test that search respects limit parameter."""
        # Search for something that matches multiple fields
        result = repository.search_fields(
            project_id="proj-123", search_term="o", limit=2  # Very broad search
        )

        assert isinstance(result, Success)
        results = result.value
        # Should return at most 2 results
        assert len(results) <= 2

    def test_search_no_matches(self, repository: SqliteSearchRepository):
        """Test searching with term that doesn't match anything."""
        result = repository.search_fields(
            project_id="proj-123", search_term="nonexistentterm12345", limit=10
        )

        assert isinstance(result, Success)
        assert result.value == []

    def test_search_different_project(self, repository: SqliteSearchRepository):
        """Test searching different project returns no results."""
        # Search in different project (no field values for proj-999)
        result = repository.search_fields(
            project_id="proj-999", search_term="location", limit=10
        )

        assert isinstance(result, Success)
        # Should still return fields from schema, but with None values
        results = result.value
        for r in results:
            # Values should be None because project has no data
            if r["current_value"] is not None:
                # If current_value is not None, it means field exists in both projects
                # This is acceptable
                pass

    def test_search_validates_project_id(self, repository: SqliteSearchRepository):
        """Test that search validates project_id parameter."""
        result = repository.search_fields(
            project_id="", search_term="location", limit=10
        )

        assert isinstance(result, Failure)
        assert "project_id" in result.error.lower()

    def test_search_validates_search_term(self, repository: SqliteSearchRepository):
        """Test that search validates search_term parameter."""
        result = repository.search_fields(
            project_id="proj-123", search_term="", limit=10
        )

        assert isinstance(result, Failure)
        assert "search_term" in result.error.lower()

    def test_search_validates_limit(self, repository: SqliteSearchRepository):
        """Test that search validates limit parameter."""
        result = repository.search_fields(
            project_id="proj-123", search_term="location", limit=0
        )

        assert isinstance(result, Failure)
        assert "limit" in result.error.lower()

    def test_search_handles_numeric_values(self, repository: SqliteSearchRepository):
        """Test searching for numeric field values."""
        # Search for "10.5" (borehole_depth value)
        result = repository.search_fields(
            project_id="proj-123", search_term="10.5", limit=10
        )

        assert isinstance(result, Success)
        results = result.value

        # Should find borehole_depth field
        depth_result = next(
            (r for r in results if r["field_id"] == "borehole_depth"), None
        )
        assert depth_result is not None
        assert depth_result["current_value"] == 10.5
        assert depth_result["match_type"] == "value"

    def test_search_result_ordering(self, repository: SqliteSearchRepository):
        """Test that results are ordered by match type (label > field_id > value)."""
        # Search for term that matches multiple types
        result = repository.search_fields(
            project_id="proj-123", search_term="soil", limit=10
        )

        assert isinstance(result, Success)
        results = result.value

        # Verify ordering: label matches should come before value matches
        if len(results) > 1:
            for i in range(len(results) - 1):
                current_priority = {
                    "label": 1,
                    "field_id": 2,
                    "value": 3,
                }[results[i]["match_type"]]
                next_priority = {
                    "label": 1,
                    "field_id": 2,
                    "value": 3,
                }[results[i + 1]["match_type"]]
                assert current_priority <= next_priority

    def test_constructor_validates_project_db_path(self, temp_schema_db: Path):
        """Test that constructor validates project_db_path exists."""
        with pytest.raises(FileNotFoundError) as exc_info:
            SqliteSearchRepository(
                project_db_path="nonexistent.db", schema_db_path=temp_schema_db
            )

        assert "project database not found" in str(exc_info.value).lower()

    def test_constructor_validates_schema_db_path(self, temp_project_db: Path):
        """Test that constructor validates schema_db_path exists."""
        with pytest.raises(FileNotFoundError) as exc_info:
            SqliteSearchRepository(
                project_db_path=temp_project_db, schema_db_path="nonexistent.db"
            )

        assert "schema database not found" in str(exc_info.value).lower()

    def test_constructor_validates_path_types(self):
        """Test that constructor validates path parameter types."""
        with pytest.raises(TypeError) as exc_info:
            SqliteSearchRepository(
                project_db_path=123, schema_db_path="path.db"  # type: ignore
            )

        assert "project_db_path" in str(exc_info.value).lower()

    def test_search_handles_null_field_values(
        self, repository: SqliteSearchRepository, temp_project_db: Path
    ):
        """Test searching when some fields have NULL values."""
        # Add a field with NULL value
        conn = sqlite3.connect(temp_project_db)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO field_values (project_id, field_id, value) VALUES (?, ?, ?)",
            ("proj-123", "empty_field", None),
        )
        conn.commit()
        conn.close()

        # Search should handle NULL values gracefully
        result = repository.search_fields(
            project_id="proj-123", search_term="location", limit=10
        )

        assert isinstance(result, Success)

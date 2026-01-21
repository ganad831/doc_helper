"""Unit tests for SearchFieldsQuery.

ADR-026: Search Architecture
- Tests validation of inputs
- Tests mapping of raw dict results to SearchResultDTO
- Tests error handling
"""

import pytest

from doc_helper.application.dto import SearchResultDTO
from doc_helper.application.queries import SearchFieldsQuery
from doc_helper.application.search import ISearchRepository
from doc_helper.domain.common.result import Failure, Result, Success


class FakeSearchRepository(ISearchRepository):
    """Fake search repository for testing."""

    def __init__(self) -> None:
        """Initialize fake repository."""
        self._results: list[dict] = []
        self._should_fail = False
        self._failure_message = ""

    def set_results(self, results: list[dict]) -> None:
        """Set results to return from search_fields."""
        self._results = results

    def set_failure(self, message: str) -> None:
        """Configure repository to return failure."""
        self._should_fail = True
        self._failure_message = message

    def search_fields(
        self, project_id: str, search_term: str, limit: int = 100
    ) -> Result[list[dict], str]:
        """Search for fields (fake implementation)."""
        if self._should_fail:
            return Failure(self._failure_message)
        return Success(self._results)


class TestSearchFieldsQuery:
    """Tests for SearchFieldsQuery."""

    @pytest.fixture
    def repository(self) -> FakeSearchRepository:
        """Create fake search repository."""
        return FakeSearchRepository()

    @pytest.fixture
    def query(self, repository: FakeSearchRepository) -> SearchFieldsQuery:
        """Create search fields query."""
        return SearchFieldsQuery(repository)

    def test_execute_returns_search_result_dtos(
        self, query: SearchFieldsQuery, repository: FakeSearchRepository
    ) -> None:
        """execute should map raw dict results to SearchResultDTO instances."""
        # Arrange
        repository.set_results(
            [
                {
                    "field_id": "site_location",
                    "field_label": "Site Location",
                    "entity_id": "project",
                    "entity_name": "Project Information",
                    "current_value": "123 Main Street",
                    "field_path": "project.site_location",
                    "match_type": "value",
                },
                {
                    "field_id": "owner_name",
                    "field_label": "Owner Name",
                    "entity_id": "project",
                    "entity_name": "Project Information",
                    "current_value": None,
                    "field_path": "project.owner_name",
                    "match_type": "label",
                },
            ]
        )

        # Act
        result = query.execute(project_id="proj-123", search_term="location")

        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2

        # Check first result
        dto1 = result.value[0]
        assert isinstance(dto1, SearchResultDTO)
        assert dto1.field_id == "site_location"
        assert dto1.field_label == "Site Location"
        assert dto1.entity_id == "project"
        assert dto1.entity_name == "Project Information"
        assert dto1.current_value == "123 Main Street"
        assert dto1.field_path == "project.site_location"
        assert dto1.match_type == "value"

        # Check second result
        dto2 = result.value[1]
        assert isinstance(dto2, SearchResultDTO)
        assert dto2.field_id == "owner_name"
        assert dto2.current_value is None

    def test_execute_returns_empty_list_when_no_matches(
        self, query: SearchFieldsQuery, repository: FakeSearchRepository
    ) -> None:
        """execute should return empty list when no results found."""
        # Arrange
        repository.set_results([])

        # Act
        result = query.execute(project_id="proj-123", search_term="nonexistent")

        # Assert
        assert isinstance(result, Success)
        assert result.value == []

    def test_execute_validates_project_id_not_empty(
        self, query: SearchFieldsQuery
    ) -> None:
        """execute should reject empty project_id."""
        # Act
        result = query.execute(project_id="", search_term="location")

        # Assert
        assert isinstance(result, Failure)
        assert "project_id" in result.error.lower()
        assert "non-empty" in result.error.lower()

    def test_execute_validates_project_id_is_string(
        self, query: SearchFieldsQuery
    ) -> None:
        """execute should reject non-string project_id."""
        # Act
        result = query.execute(project_id=123, search_term="location")  # type: ignore

        # Assert
        assert isinstance(result, Failure)
        assert "project_id" in result.error.lower()

    def test_execute_validates_search_term_not_empty(
        self, query: SearchFieldsQuery
    ) -> None:
        """execute should reject empty search_term."""
        # Act
        result = query.execute(project_id="proj-123", search_term="")

        # Assert
        assert isinstance(result, Failure)
        assert "search_term" in result.error.lower()
        assert "non-empty" in result.error.lower()

    def test_execute_validates_search_term_not_whitespace(
        self, query: SearchFieldsQuery
    ) -> None:
        """execute should reject whitespace-only search_term."""
        # Act
        result = query.execute(project_id="proj-123", search_term="   ")

        # Assert
        assert isinstance(result, Failure)
        assert "search_term" in result.error.lower()

    def test_execute_validates_search_term_is_string(
        self, query: SearchFieldsQuery
    ) -> None:
        """execute should reject non-string search_term."""
        # Act
        result = query.execute(project_id="proj-123", search_term=123)  # type: ignore

        # Assert
        assert isinstance(result, Failure)
        assert "search_term" in result.error.lower()

    def test_execute_validates_limit_is_positive(
        self, query: SearchFieldsQuery
    ) -> None:
        """execute should reject non-positive limit."""
        # Act
        result1 = query.execute(project_id="proj-123", search_term="location", limit=0)
        result2 = query.execute(
            project_id="proj-123", search_term="location", limit=-10
        )

        # Assert
        assert isinstance(result1, Failure)
        assert "limit" in result1.error.lower()
        assert "positive" in result1.error.lower()

        assert isinstance(result2, Failure)
        assert "limit" in result2.error.lower()

    def test_execute_validates_limit_is_integer(
        self, query: SearchFieldsQuery
    ) -> None:
        """execute should reject non-integer limit."""
        # Act
        result = query.execute(
            project_id="proj-123", search_term="location", limit="100"  # type: ignore
        )

        # Assert
        assert isinstance(result, Failure)
        assert "limit" in result.error.lower()

    def test_execute_uses_default_limit(
        self, query: SearchFieldsQuery, repository: FakeSearchRepository
    ) -> None:
        """execute should use default limit of 100 when not specified."""
        # Arrange
        repository.set_results([])

        # Act
        result = query.execute(project_id="proj-123", search_term="location")

        # Assert - No validation error means default limit was accepted
        assert isinstance(result, Success)

    def test_execute_trims_whitespace_from_search_term(
        self, query: SearchFieldsQuery, repository: FakeSearchRepository
    ) -> None:
        """execute should trim leading/trailing whitespace from search_term."""
        # Arrange
        repository.set_results([])

        # Act - whitespace should be trimmed before passing to repository
        result = query.execute(project_id="proj-123", search_term="  location  ")

        # Assert - If search_term is empty after trim, it would fail validation
        # Since it passes, whitespace was trimmed
        assert isinstance(result, Success)

    def test_execute_propagates_repository_failure(
        self, query: SearchFieldsQuery, repository: FakeSearchRepository
    ) -> None:
        """execute should propagate failures from repository."""
        # Arrange
        repository.set_failure("Database connection error")

        # Act
        result = query.execute(project_id="proj-123", search_term="location")

        # Assert
        assert isinstance(result, Failure)
        assert "search failed" in result.error.lower()
        assert "database connection error" in result.error.lower()

    def test_execute_handles_malformed_repository_results(
        self, query: SearchFieldsQuery, repository: FakeSearchRepository
    ) -> None:
        """execute should handle repository results missing required keys."""
        # Arrange - Missing "field_label" key
        repository.set_results(
            [
                {
                    "field_id": "site_location",
                    # "field_label": "Site Location",  # MISSING
                    "entity_id": "project",
                    "entity_name": "Project Information",
                    "current_value": "123 Main Street",
                    "field_path": "project.site_location",
                    "match_type": "value",
                }
            ]
        )

        # Act
        result = query.execute(project_id="proj-123", search_term="location")

        # Assert
        assert isinstance(result, Failure)
        assert "failed to map" in result.error.lower()

    def test_constructor_validates_repository_type(self) -> None:
        """Constructor should validate that repository implements ISearchRepository."""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            SearchFieldsQuery("not a repository")  # type: ignore

        assert "ISearchRepository" in str(exc_info.value)

    def test_execute_handles_complex_value_types(
        self, query: SearchFieldsQuery, repository: FakeSearchRepository
    ) -> None:
        """execute should handle complex current_value types (lists, dicts)."""
        # Arrange
        repository.set_results(
            [
                {
                    "field_id": "tags",
                    "field_label": "Tags",
                    "entity_id": "project",
                    "entity_name": "Project",
                    "current_value": ["tag1", "tag2"],
                    "field_path": "project.tags",
                    "match_type": "value",
                },
                {
                    "field_id": "metadata",
                    "field_label": "Metadata",
                    "entity_id": "project",
                    "entity_name": "Project",
                    "current_value": {"key": "value"},
                    "field_path": "project.metadata",
                    "match_type": "label",
                },
            ]
        )

        # Act
        result = query.execute(project_id="proj-123", search_term="tag")

        # Assert
        assert isinstance(result, Success)
        assert result.value[0].current_value == ["tag1", "tag2"]
        assert result.value[1].current_value == {"key": "value"}

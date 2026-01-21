"""Query for searching fields within a project.

ADR-026: Search Architecture
RULES (AGENT_RULES.md Section 3-4):
- Queries return DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary
- CQRS pattern: read-only operations
"""

from doc_helper.application.dto import SearchResultDTO
from doc_helper.application.search import ISearchRepository
from doc_helper.domain.common.result import Failure, Result, Success


class SearchFieldsQuery:
    """Query to search for fields within a project.

    ADR-026: Search Architecture
    - Read-only query operation (CQRS)
    - Searches field labels, field IDs, and field values
    - Returns SearchResultDTO instances for presentation layer
    - Project-scoped search only

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Query handlers are stateless (dependencies injected)
    - Queries return DTOs, not domain objects
    - CQRS pattern: separate reads from writes

    Example:
        query = SearchFieldsQuery(search_repository=repo)
        result = query.execute(
            project_id="proj-123",
            search_term="location",
            limit=50
        )
        if isinstance(result, Success):
            for search_result in result.value:
                print(f"{search_result.field_label}: {search_result.current_value}")
    """

    def __init__(self, search_repository: ISearchRepository) -> None:
        """Initialize query.

        Args:
            search_repository: Repository for searching fields

        Raises:
            TypeError: If search_repository doesn't implement ISearchRepository
        """
        if not isinstance(search_repository, ISearchRepository):
            raise TypeError("search_repository must implement ISearchRepository")
        self._search_repository = search_repository

    def execute(
        self,
        project_id: str,
        search_term: str,
        limit: int = 100,
    ) -> Result[list[SearchResultDTO], str]:
        """Execute search query for fields within a project.

        ADR-026: Searches field labels, field IDs, and field values.
        Returns results ordered by relevance (label matches first, then value matches).

        Args:
            project_id: Project ID to search within
            search_term: Search term (case-insensitive partial match)
            limit: Maximum number of results to return (default: 100)

        Returns:
            Success(list[SearchResultDTO]) containing matching fields
            Failure(error) on validation or search error

        Validation Rules:
            - project_id must be non-empty string
            - search_term must be non-empty string
            - limit must be positive integer

        Example:
            # Search for fields matching "site"
            result = query.execute("proj-123", "site", limit=20)

            if isinstance(result, Success):
                for match in result.value:
                    print(f"Found: {match.field_label} in {match.entity_name}")
                    if match.has_value():
                        print(f"  Current value: {match.current_value}")
        """
        # Validate inputs
        if not isinstance(project_id, str) or not project_id:
            return Failure("project_id must be a non-empty string")

        if not isinstance(search_term, str) or not search_term.strip():
            return Failure("search_term must be a non-empty string")

        if not isinstance(limit, int) or limit <= 0:
            return Failure("limit must be a positive integer")

        # Execute search via repository
        search_result = self._search_repository.search_fields(
            project_id=project_id,
            search_term=search_term.strip(),
            limit=limit,
        )

        if isinstance(search_result, Failure):
            return Failure(f"Search failed: {search_result.error}")

        raw_results = search_result.value

        # Map raw dict results to SearchResultDTO instances
        dtos = []
        for raw_result in raw_results:
            try:
                dto = SearchResultDTO(
                    field_id=raw_result["field_id"],
                    field_label=raw_result["field_label"],
                    entity_id=raw_result["entity_id"],
                    entity_name=raw_result["entity_name"],
                    current_value=raw_result["current_value"],
                    field_path=raw_result["field_path"],
                    match_type=raw_result["match_type"],
                )
                dtos.append(dto)
            except (KeyError, TypeError) as e:
                return Failure(f"Failed to map search result to DTO: {str(e)}")

        return Success(dtos)

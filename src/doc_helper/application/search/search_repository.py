"""Repository interface for search operations.

ADR-026: Search Architecture
- Interface defined in Application layer (search is application-level concern)
- Implementation in Infrastructure layer
- Read-only operations (no mutations, no side effects)
- Project-scoped search only
"""

from abc import ABC, abstractmethod

from doc_helper.domain.common.result import Result


class ISearchRepository(ABC):
    """Repository interface for searching fields within a project.

    ADR-026: Search Architecture
    - Read-only query operation (CQRS)
    - Search field definitions and field values
    - Returns raw search data (field_id, label, value, entity info)
    - Application layer maps results to DTOs

    Lifecycle:
    - search_fields(): Search by term within project scope
    - Results include field metadata and current values
    - Respects project boundaries (no cross-project search)

    Example:
        repo = SqliteSearchRepository(project_db="project.db", schema_db="config.db")

        # Search for fields matching term
        result = repo.search_fields(
            project_id="proj-123",
            search_term="location"
        )

        if result.is_success:
            raw_results = result.value
            for row in raw_results:
                print(f"Field: {row['field_label']}, Value: {row['current_value']}")
    """

    @abstractmethod
    def search_fields(
        self,
        project_id: str,
        search_term: str,
        limit: int = 100,
    ) -> Result[list[dict], str]:
        """Search for fields matching the search term within a project.

        ADR-026: Searches field labels, field IDs, and field values.
        Returns raw data (dict format) for application layer to map to DTOs.

        Args:
            project_id: Project ID to search within
            search_term: Search term (case-insensitive partial match)
            limit: Maximum number of results to return

        Returns:
            Success(list[dict]) containing matching fields with keys:
                - field_id: str
                - field_label: str
                - entity_id: str
                - entity_name: str
                - current_value: Any | None
                - field_path: str (entity_id.field_id)
                - match_type: str ("label", "value", "field_id")
            Failure(error) if search failed

        Example:
            result = repo.search_fields(
                project_id="proj-123",
                search_term="site"
            )

            if result.is_success:
                for row in result.value:
                    print(f"{row['field_label']}: {row['current_value']}")
        """
        pass

"""Search module for field search operations.

ADR-026: Search Architecture
- Read-only query operations
- Project-scoped search
- CQRS query-side only
"""

from doc_helper.application.search.search_repository import ISearchRepository

__all__ = [
    "ISearchRepository",
]

"""Query handlers for read operations.

ADR-004: CQRS Pattern
- Queries are read-only operations
- Queries return DTOs, never domain objects
- Queries are stateless (dependencies injected)
"""

from doc_helper.application.queries.get_entity_fields_query import GetEntityFieldsQuery
from doc_helper.application.queries.get_field_history_query import GetFieldHistoryQuery
from doc_helper.application.queries.get_project_query import (
    GetAllProjectsQuery,
    GetProjectQuery,
    GetRecentProjectsQuery,
)
from doc_helper.application.queries.get_validation_result_query import (
    GetValidationResultQuery,
)

__all__ = [
    "GetProjectQuery",
    "GetAllProjectsQuery",
    "GetRecentProjectsQuery",
    "GetEntityFieldsQuery",
    "GetValidationResultQuery",
    "GetFieldHistoryQuery",
]

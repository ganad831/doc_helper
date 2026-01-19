"""Project domain.

The Project domain manages document generation projects with field values and metadata.

Key components:
- Project: Aggregate root representing a document generation project
- FieldValue: Value object storing field data with override support
- ProjectId: Strongly-typed project identifier
"""

from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository

__all__ = [
    "FieldValue",
    "Project",
    "ProjectId",
    "IProjectRepository",
]

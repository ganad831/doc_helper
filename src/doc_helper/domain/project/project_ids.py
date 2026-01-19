"""Project domain strongly-typed IDs."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ProjectId:
    """Strongly-typed ID for Project aggregate.

    ProjectId uses UUID for globally unique identification.

    Example:
        from uuid import uuid4

        project_id = ProjectId(uuid4())
        print(project_id.value)  # UUID object
    """

    value: UUID

    def __post_init__(self) -> None:
        """Validate project ID."""
        if not isinstance(self.value, UUID):
            raise TypeError("ProjectId value must be a UUID")

    def __str__(self) -> str:
        """String representation (UUID string)."""
        return str(self.value)

    def __repr__(self) -> str:
        """Debug representation."""
        return f"ProjectId({self.value!r})"

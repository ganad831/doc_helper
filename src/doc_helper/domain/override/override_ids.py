"""Override domain strongly-typed IDs."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class OverrideId:
    """Strongly-typed ID for Override entity.

    OverrideId uses UUID for globally unique identification.

    Example:
        from uuid import uuid4

        override_id = OverrideId(uuid4())
        print(override_id.value)  # UUID object
    """

    value: UUID

    def __post_init__(self) -> None:
        """Validate override ID."""
        if not isinstance(self.value, UUID):
            raise TypeError("OverrideId value must be a UUID")

    def __str__(self) -> str:
        """String representation (UUID string)."""
        return str(self.value)

    def __repr__(self) -> str:
        """Debug representation."""
        return f"OverrideId({self.value!r})"

"""Strongly-typed IDs for file domain."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AttachmentId:
    """Strongly-typed ID for Attachment entity.

    AttachmentId uses UUID for globally unique identification.

    Example:
        from uuid import uuid4

        attachment_id = AttachmentId(uuid4())
        print(attachment_id.value)  # UUID object
    """

    value: UUID

    def __post_init__(self) -> None:
        """Validate attachment ID.

        Raises:
            TypeError: If value is not UUID
        """
        if not isinstance(self.value, UUID):
            raise TypeError(f"AttachmentId value must be a UUID, got {type(self.value)}")

    def __str__(self) -> str:
        """String representation (UUID string)."""
        return str(self.value)

    def __repr__(self) -> str:
        """Debug representation."""
        return f"AttachmentId({self.value!r})"

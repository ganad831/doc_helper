"""Attachment aggregate root for file management."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from doc_helper.domain.common.entity import Entity
from doc_helper.domain.file.file_ids import AttachmentId
from doc_helper.domain.file.value_objects.index_type import IndexType
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


@dataclass(kw_only=True)
class Attachment(Entity):
    """Aggregate root for file attachment.

    Represents a single file attached to a FILE or IMAGE field.
    Tracks file metadata and figure numbering configuration.

    RULES:
    - Attachment is an Entity (has identity via AttachmentId)
    - file_path is relative to project directory
    - Figure number is NOT stored here (calculated by NumberingService)
    - index_type determines which numbering sequence (Figure 1, Image 1, etc.)
    - exclude_from_index removes from figure numbering
    - caption is optional descriptive text

    Example:
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("site_photos"),
            file_path="attachments/photo1.jpg",
            index_type=IndexType.FIGURE,
            exclude_from_index=False,
            caption="Site overview from north"
        )
    """

    id: AttachmentId
    project_id: ProjectId
    field_id: FieldDefinitionId
    file_path: str  # Relative path from project root
    index_type: IndexType = IndexType.FIGURE
    exclude_from_index: bool = False
    caption: str = ""
    position: int = 0  # Position within field (for ordering)

    def __post_init__(self) -> None:
        """Validate attachment.

        Raises:
            TypeError: If types are invalid
            ValueError: If values are invalid
        """
        if not isinstance(self.id, AttachmentId):
            raise TypeError(f"id must be AttachmentId, got {type(self.id)}")
        if not isinstance(self.project_id, ProjectId):
            raise TypeError(f"project_id must be ProjectId, got {type(self.project_id)}")
        if not isinstance(self.field_id, FieldDefinitionId):
            raise TypeError(f"field_id must be FieldDefinitionId, got {type(self.field_id)}")
        if not isinstance(self.file_path, str):
            raise TypeError(f"file_path must be str, got {type(self.file_path)}")
        if not isinstance(self.index_type, IndexType):
            raise TypeError(f"index_type must be IndexType, got {type(self.index_type)}")
        if not isinstance(self.exclude_from_index, bool):
            raise TypeError(f"exclude_from_index must be bool, got {type(self.exclude_from_index)}")
        if not isinstance(self.caption, str):
            raise TypeError(f"caption must be str, got {type(self.caption)}")
        if not isinstance(self.position, int):
            raise TypeError(f"position must be int, got {type(self.position)}")
        if self.file_path == "":
            raise ValueError("file_path cannot be empty")
        if self.position < 0:
            raise ValueError(f"position must be >= 0, got {self.position}")

    @property
    def file_name(self) -> str:
        """Get file name from path.

        Returns:
            File name without directory
        """
        return Path(self.file_path).name

    @property
    def file_extension(self) -> str:
        """Get file extension.

        Returns:
            File extension with dot (e.g., ".jpg", ".pdf")
        """
        return Path(self.file_path).suffix

    @property
    def is_image(self) -> bool:
        """Check if attachment is an image file.

        Returns:
            True if file extension is image format
        """
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
        return self.file_extension.lower() in image_extensions

    @property
    def is_pdf(self) -> bool:
        """Check if attachment is a PDF file.

        Returns:
            True if file extension is .pdf
        """
        return self.file_extension.lower() == ".pdf"

    @property
    def should_have_figure_number(self) -> bool:
        """Check if this attachment should receive a figure number.

        Returns:
            True if not excluded from index
        """
        return not self.exclude_from_index

    def set_caption(self, caption: str) -> "Attachment":
        """Create new Attachment with updated caption.

        Args:
            caption: New caption text

        Returns:
            New Attachment with updated caption

        Raises:
            TypeError: If caption is not string
        """
        if not isinstance(caption, str):
            raise TypeError(f"caption must be str, got {type(caption)}")

        return Attachment(
            id=self.id,
            project_id=self.project_id,
            field_id=self.field_id,
            file_path=self.file_path,
            index_type=self.index_type,
            exclude_from_index=self.exclude_from_index,
            caption=caption,
            position=self.position,
        )

    def set_index_type(self, index_type: IndexType) -> "Attachment":
        """Create new Attachment with updated index type.

        Args:
            index_type: New index type

        Returns:
            New Attachment with updated index type

        Raises:
            TypeError: If index_type is not IndexType
        """
        if not isinstance(index_type, IndexType):
            raise TypeError(f"index_type must be IndexType, got {type(index_type)}")

        return Attachment(
            id=self.id,
            project_id=self.project_id,
            field_id=self.field_id,
            file_path=self.file_path,
            index_type=index_type,
            exclude_from_index=self.exclude_from_index,
            caption=self.caption,
            position=self.position,
        )

    def exclude_from_numbering(self) -> "Attachment":
        """Create new Attachment excluded from figure numbering.

        Returns:
            New Attachment with exclude_from_index=True
        """
        return Attachment(
            id=self.id,
            project_id=self.project_id,
            field_id=self.field_id,
            file_path=self.file_path,
            index_type=self.index_type,
            exclude_from_index=True,
            caption=self.caption,
            position=self.position,
        )

    def include_in_numbering(self) -> "Attachment":
        """Create new Attachment included in figure numbering.

        Returns:
            New Attachment with exclude_from_index=False
        """
        return Attachment(
            id=self.id,
            project_id=self.project_id,
            field_id=self.field_id,
            file_path=self.file_path,
            index_type=self.index_type,
            exclude_from_index=False,
            caption=self.caption,
            position=self.position,
        )

    def set_position(self, position: int) -> "Attachment":
        """Create new Attachment with updated position.

        Args:
            position: New position (0-based)

        Returns:
            New Attachment with updated position

        Raises:
            TypeError: If position is not int
            ValueError: If position is negative
        """
        if not isinstance(position, int):
            raise TypeError(f"position must be int, got {type(position)}")
        if position < 0:
            raise ValueError(f"position must be >= 0, got {position}")

        return Attachment(
            id=self.id,
            project_id=self.project_id,
            field_id=self.field_id,
            file_path=self.file_path,
            index_type=self.index_type,
            exclude_from_index=self.exclude_from_index,
            caption=self.caption,
            position=position,
        )

    def __str__(self) -> str:
        """String representation."""
        status = "excluded" if self.exclude_from_index else str(self.index_type)
        return f"Attachment({self.file_name}, {status})"

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"Attachment("
            f"id={self.id!r}, "
            f"file_path={self.file_path!r}, "
            f"index_type={self.index_type!r}, "
            f"exclude={self.exclude_from_index})"
        )

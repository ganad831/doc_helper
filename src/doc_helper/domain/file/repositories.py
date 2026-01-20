"""Repository interfaces for file domain context.

Following the Repository pattern, these interfaces are defined in the domain layer
but implemented in the infrastructure layer. This decouples the domain from
persistence concerns.
"""

from abc import ABC, abstractmethod
from typing import List

from doc_helper.domain.common.result import Result
from doc_helper.domain.file.entities.attachment import Attachment
from doc_helper.domain.file.file_ids import AttachmentId
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class IAttachmentRepository(ABC):
    """Repository interface for Attachment aggregate.

    RULES:
    - Attachments are scoped to a project
    - Each attachment has a unique AttachmentId
    - File paths are relative to project directory
    - Position determines ordering for figure numbering
    """

    @abstractmethod
    def get_by_id(self, attachment_id: AttachmentId) -> Result[Attachment, str]:
        """Retrieve attachment by ID.

        Args:
            attachment_id: Unique identifier

        Returns:
            Result containing:
            - Success: Attachment entity
            - Failure: Error message if not found
        """
        pass

    @abstractmethod
    def list_by_project(self, project_id: ProjectId) -> Result[List[Attachment], str]:
        """Retrieve all attachments for a project.

        Args:
            project_id: Project identifier

        Returns:
            Result containing:
            - Success: List of attachments (empty list if none)
            - Failure: Error message if query fails
        """
        pass

    @abstractmethod
    def list_by_field(
        self,
        project_id: ProjectId,
        field_id: FieldDefinitionId
    ) -> Result[List[Attachment], str]:
        """Retrieve all attachments for a specific field.

        Args:
            project_id: Project identifier
            field_id: Field identifier

        Returns:
            Result containing:
            - Success: List of attachments for this field (empty list if none)
            - Failure: Error message if query fails

        Notes:
            - Attachments returned in position order (ascending)
        """
        pass

    @abstractmethod
    def save(self, attachment: Attachment) -> Result[None, str]:
        """Save attachment (insert or update).

        Args:
            attachment: Attachment entity to persist

        Returns:
            Result containing:
            - Success: None
            - Failure: Error message if save fails

        Notes:
            - If attachment.id exists, performs UPDATE
            - If attachment.id is new, performs INSERT
        """
        pass

    @abstractmethod
    def delete(self, attachment_id: AttachmentId) -> Result[None, str]:
        """Delete attachment by ID.

        Args:
            attachment_id: Unique identifier

        Returns:
            Result containing:
            - Success: None (deletion succeeded or ID didn't exist)
            - Failure: Error message if deletion fails

        Notes:
            - Deletion is idempotent (deleting non-existent ID is not an error)
            - Physical file is NOT deleted by repository (application service responsibility)
        """
        pass

    @abstractmethod
    def exists(self, attachment_id: AttachmentId) -> Result[bool, str]:
        """Check if attachment exists.

        Args:
            attachment_id: Unique identifier

        Returns:
            Result containing:
            - Success: True if exists, False otherwise
            - Failure: Error message if query fails
        """
        pass

    @abstractmethod
    def delete_by_project(self, project_id: ProjectId) -> Result[int, str]:
        """Delete all attachments for a project.

        Args:
            project_id: Project identifier

        Returns:
            Result containing:
            - Success: Number of attachments deleted
            - Failure: Error message if deletion fails

        Notes:
            - Used when deleting entire project
            - Physical files are NOT deleted (application service responsibility)
        """
        pass

    @abstractmethod
    def delete_by_field(
        self,
        project_id: ProjectId,
        field_id: FieldDefinitionId
    ) -> Result[int, str]:
        """Delete all attachments for a specific field.

        Args:
            project_id: Project identifier
            field_id: Field identifier

        Returns:
            Result containing:
            - Success: Number of attachments deleted
            - Failure: Error message if deletion fails

        Notes:
            - Used when clearing FILE/IMAGE field
            - Physical files are NOT deleted (application service responsibility)
        """
        pass

    @abstractmethod
    def update_positions(
        self,
        attachments: List[Attachment]
    ) -> Result[None, str]:
        """Batch update attachment positions.

        Args:
            attachments: List of attachments with updated position values

        Returns:
            Result containing:
            - Success: None
            - Failure: Error message if update fails

        Notes:
            - Used after drag-and-drop reordering
            - Only updates position field, not other attributes
            - All attachments must exist in repository
        """
        pass

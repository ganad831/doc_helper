"""SQLite implementation of IAttachmentRepository."""

import sqlite3
from typing import List
from uuid import UUID

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.file.entities.attachment import Attachment
from doc_helper.domain.file.file_ids import AttachmentId
from doc_helper.domain.file.repositories import IAttachmentRepository
from doc_helper.domain.file.value_objects.index_type import IndexType
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class SqliteAttachmentRepository(IAttachmentRepository):
    """SQLite implementation of attachment repository.

    Schema:
        CREATE TABLE attachments (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            field_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            index_type TEXT NOT NULL,
            exclude_from_index INTEGER NOT NULL DEFAULT 0,
            caption TEXT NOT NULL DEFAULT '',
            position INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX idx_attachments_project ON attachments(project_id);
        CREATE INDEX idx_attachments_field ON attachments(project_id, field_id);
        CREATE INDEX idx_attachments_position ON attachments(project_id, field_id, position);
    """

    def __init__(self, connection: sqlite3.Connection):
        """Initialize repository with database connection.

        Args:
            connection: SQLite connection (must be open)
        """
        self._conn = connection
        self._conn.row_factory = sqlite3.Row

    def get_by_id(self, attachment_id: AttachmentId) -> Result[Attachment, str]:
        """Retrieve attachment by ID."""
        if not isinstance(attachment_id, AttachmentId):
            return Failure(f"attachment_id must be AttachmentId, got {type(attachment_id)}")

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT id, project_id, field_id, file_path, index_type,
                       exclude_from_index, caption, position
                FROM attachments
                WHERE id = ?
                """,
                (str(attachment_id.value),)
            )

            row = cursor.fetchone()

            if row is None:
                return Failure(f"Attachment {attachment_id.value} not found")

            attachment = self._row_to_entity(row)
            return Success(attachment)

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")
        except Exception as e:
            return Failure(f"Unexpected error: {e}")

    def list_by_project(self, project_id: ProjectId) -> Result[List[Attachment], str]:
        """Retrieve all attachments for a project."""
        if not isinstance(project_id, ProjectId):
            return Failure(f"project_id must be ProjectId, got {type(project_id)}")

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT id, project_id, field_id, file_path, index_type,
                       exclude_from_index, caption, position
                FROM attachments
                WHERE project_id = ?
                ORDER BY position ASC
                """,
                (str(project_id.value),)
            )

            rows = cursor.fetchall()
            attachments = [self._row_to_entity(row) for row in rows]
            return Success(attachments)

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")
        except Exception as e:
            return Failure(f"Unexpected error: {e}")

    def list_by_field(
        self,
        project_id: ProjectId,
        field_id: FieldDefinitionId
    ) -> Result[List[Attachment], str]:
        """Retrieve all attachments for a specific field."""
        if not isinstance(project_id, ProjectId):
            return Failure(f"project_id must be ProjectId, got {type(project_id)}")

        if not isinstance(field_id, FieldDefinitionId):
            return Failure(f"field_id must be FieldDefinitionId, got {type(field_id)}")

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT id, project_id, field_id, file_path, index_type,
                       exclude_from_index, caption, position
                FROM attachments
                WHERE project_id = ? AND field_id = ?
                ORDER BY position ASC
                """,
                (str(project_id.value), field_id.value)
            )

            rows = cursor.fetchall()
            attachments = [self._row_to_entity(row) for row in rows]
            return Success(attachments)

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")
        except Exception as e:
            return Failure(f"Unexpected error: {e}")

    def save(self, attachment: Attachment) -> Result[None, str]:
        """Save attachment (insert or update)."""
        if not isinstance(attachment, Attachment):
            return Failure(f"attachment must be Attachment, got {type(attachment)}")

        try:
            cursor = self._conn.cursor()

            # Check if attachment exists
            exists_result = self.exists(attachment.id)
            if not exists_result.is_success:
                return Failure(f"Failed to check existence: {exists_result.error}")

            if exists_result.value:
                # UPDATE
                cursor.execute(
                    """
                    UPDATE attachments
                    SET project_id = ?, field_id = ?, file_path = ?,
                        index_type = ?, exclude_from_index = ?,
                        caption = ?, position = ?,
                        modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        str(attachment.project_id.value),
                        attachment.field_id.value,
                        attachment.file_path,
                        attachment.index_type.value,
                        1 if attachment.exclude_from_index else 0,
                        attachment.caption,
                        attachment.position,
                        str(attachment.id.value),
                    )
                )
            else:
                # INSERT
                cursor.execute(
                    """
                    INSERT INTO attachments (
                        id, project_id, field_id, file_path,
                        index_type, exclude_from_index, caption, position
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(attachment.id.value),
                        str(attachment.project_id.value),
                        attachment.field_id.value,
                        attachment.file_path,
                        attachment.index_type.value,
                        1 if attachment.exclude_from_index else 0,
                        attachment.caption,
                        attachment.position,
                    )
                )

            self._conn.commit()
            return Success(None)

        except sqlite3.Error as e:
            self._conn.rollback()
            return Failure(f"Database error: {e}")
        except Exception as e:
            self._conn.rollback()
            return Failure(f"Unexpected error: {e}")

    def delete(self, attachment_id: AttachmentId) -> Result[None, str]:
        """Delete attachment by ID."""
        if not isinstance(attachment_id, AttachmentId):
            return Failure(f"attachment_id must be AttachmentId, got {type(attachment_id)}")

        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM attachments WHERE id = ?", (str(attachment_id.value),))
            self._conn.commit()
            return Success(None)

        except sqlite3.Error as e:
            self._conn.rollback()
            return Failure(f"Database error: {e}")
        except Exception as e:
            self._conn.rollback()
            return Failure(f"Unexpected error: {e}")

    def exists(self, attachment_id: AttachmentId) -> Result[bool, str]:
        """Check if attachment exists."""
        if not isinstance(attachment_id, AttachmentId):
            return Failure(f"attachment_id must be AttachmentId, got {type(attachment_id)}")

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT 1 FROM attachments WHERE id = ? LIMIT 1",
                (str(attachment_id.value),)
            )
            return Success(cursor.fetchone() is not None)

        except sqlite3.Error as e:
            return Failure(f"Database error: {e}")
        except Exception as e:
            return Failure(f"Unexpected error: {e}")

    def delete_by_project(self, project_id: ProjectId) -> Result[int, str]:
        """Delete all attachments for a project."""
        if not isinstance(project_id, ProjectId):
            return Failure(f"project_id must be ProjectId, got {type(project_id)}")

        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM attachments WHERE project_id = ?", (str(project_id.value),))
            deleted_count = cursor.rowcount
            self._conn.commit()
            return Success(deleted_count)

        except sqlite3.Error as e:
            self._conn.rollback()
            return Failure(f"Database error: {e}")
        except Exception as e:
            self._conn.rollback()
            return Failure(f"Unexpected error: {e}")

    def delete_by_field(
        self,
        project_id: ProjectId,
        field_id: FieldDefinitionId
    ) -> Result[int, str]:
        """Delete all attachments for a specific field."""
        if not isinstance(project_id, ProjectId):
            return Failure(f"project_id must be ProjectId, got {type(project_id)}")

        if not isinstance(field_id, FieldDefinitionId):
            return Failure(f"field_id must be FieldDefinitionId, got {type(field_id)}")

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "DELETE FROM attachments WHERE project_id = ? AND field_id = ?",
                (str(project_id.value), field_id.value)
            )
            deleted_count = cursor.rowcount
            self._conn.commit()
            return Success(deleted_count)

        except sqlite3.Error as e:
            self._conn.rollback()
            return Failure(f"Database error: {e}")
        except Exception as e:
            self._conn.rollback()
            return Failure(f"Unexpected error: {e}")

    def update_positions(
        self,
        attachments: List[Attachment]
    ) -> Result[None, str]:
        """Batch update attachment positions."""
        if not isinstance(attachments, list):
            return Failure("attachments must be a list")

        if not all(isinstance(a, Attachment) for a in attachments):
            return Failure("All items must be Attachment instances")

        try:
            cursor = self._conn.cursor()

            for attachment in attachments:
                cursor.execute(
                    """
                    UPDATE attachments
                    SET position = ?, modified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (attachment.position, str(attachment.id.value))
                )

            self._conn.commit()
            return Success(None)

        except sqlite3.Error as e:
            self._conn.rollback()
            return Failure(f"Database error: {e}")
        except Exception as e:
            self._conn.rollback()
            return Failure(f"Unexpected error: {e}")

    def _row_to_entity(self, row: sqlite3.Row) -> Attachment:
        """Convert database row to Attachment entity.

        Args:
            row: sqlite3.Row from query

        Returns:
            Attachment entity
        """
        return Attachment(
            id=AttachmentId(UUID(row["id"])),
            project_id=ProjectId(UUID(row["project_id"])),
            field_id=FieldDefinitionId(row["field_id"]),
            file_path=row["file_path"],
            index_type=IndexType(row["index_type"]),
            exclude_from_index=bool(row["exclude_from_index"]),
            caption=row["caption"],
            position=row["position"],
        )

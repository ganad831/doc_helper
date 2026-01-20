"""Integration tests for SqliteAttachmentRepository."""

import sqlite3
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.file.entities.attachment import Attachment
from doc_helper.domain.file.file_ids import AttachmentId
from doc_helper.domain.file.value_objects.index_type import IndexType
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId
from doc_helper.infrastructure.persistence.sqlite.repositories.attachment_repository import (
    SqliteAttachmentRepository,
)


class TestSqliteAttachmentRepository:
    """Integration tests for SqliteAttachmentRepository."""

    @pytest.fixture
    def temp_db(self) -> Path:
        """Create temporary database file with schema."""
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        # Create schema
        conn = sqlite3.connect(str(temp_path))
        conn.execute(
            """
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
            )
            """
        )
        conn.execute("CREATE INDEX idx_attachments_project ON attachments(project_id)")
        conn.execute("CREATE INDEX idx_attachments_field ON attachments(project_id, field_id)")
        conn.execute("CREATE INDEX idx_attachments_position ON attachments(project_id, field_id, position)")
        conn.commit()
        conn.close()

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def connection(self, temp_db: Path) -> sqlite3.Connection:
        """Create database connection."""
        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row
        yield conn
        conn.close()

    @pytest.fixture
    def repository(self, connection: sqlite3.Connection) -> SqliteAttachmentRepository:
        """Create repository instance."""
        return SqliteAttachmentRepository(connection)

    @pytest.fixture
    def sample_attachment(self) -> Attachment:
        """Create sample attachment for testing."""
        return Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("site_photos"),
            file_path="attachments/photo1.jpg",
            index_type=IndexType.FIGURE,
            exclude_from_index=False,
            caption="Site overview from north",
            position=0,
        )

    def test_save_new_attachment(self, repository: SqliteAttachmentRepository, sample_attachment: Attachment):
        """Test saving a new attachment."""
        result = repository.save(sample_attachment)

        assert isinstance(result, Success)

        # Verify saved
        get_result = repository.get_by_id(sample_attachment.id)
        assert isinstance(get_result, Success)
        loaded = get_result.value
        assert loaded.id == sample_attachment.id
        assert loaded.project_id == sample_attachment.project_id
        assert loaded.field_id == sample_attachment.field_id
        assert loaded.file_path == sample_attachment.file_path
        assert loaded.index_type == sample_attachment.index_type
        assert loaded.exclude_from_index == sample_attachment.exclude_from_index
        assert loaded.caption == sample_attachment.caption
        assert loaded.position == sample_attachment.position

    def test_save_update_existing_attachment(
        self, repository: SqliteAttachmentRepository, sample_attachment: Attachment
    ):
        """Test updating an existing attachment."""
        # Save initial
        repository.save(sample_attachment)

        # Update
        updated = sample_attachment.set_caption("Updated caption")
        result = repository.save(updated)

        assert isinstance(result, Success)

        # Verify updated
        get_result = repository.get_by_id(sample_attachment.id)
        assert isinstance(get_result, Success)
        loaded = get_result.value
        assert loaded.caption == "Updated caption"

    def test_save_requires_attachment_instance(self, repository: SqliteAttachmentRepository):
        """Test save requires Attachment instance."""
        result = repository.save("not an attachment")  # type: ignore

        assert isinstance(result, Failure)
        assert "Attachment" in result.error

    def test_get_by_id_not_found(self, repository: SqliteAttachmentRepository):
        """Test get_by_id returns Failure when attachment not found."""
        non_existent_id = AttachmentId(uuid4())
        result = repository.get_by_id(non_existent_id)

        assert isinstance(result, Failure)
        assert "not found" in result.error

    def test_get_by_id_requires_attachment_id(self, repository: SqliteAttachmentRepository):
        """Test get_by_id requires AttachmentId."""
        result = repository.get_by_id("not an id")  # type: ignore

        assert isinstance(result, Failure)
        assert "AttachmentId" in result.error

    def test_list_by_project(self, repository: SqliteAttachmentRepository):
        """Test listing all attachments for a project."""
        project_id = ProjectId(uuid4())

        # Create 3 attachments for same project
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=project_id,
                field_id=FieldDefinitionId("photos"),
                file_path=f"photo{i}.jpg",
                index_type=IndexType.FIGURE,
                position=i,
            )
            for i in range(3)
        ]

        for attachment in attachments:
            repository.save(attachment)

        # List by project
        result = repository.list_by_project(project_id)

        assert isinstance(result, Success)
        assert len(result.value) == 3

        # Verify sorted by position
        for i, attachment in enumerate(result.value):
            assert attachment.position == i

    def test_list_by_project_empty(self, repository: SqliteAttachmentRepository):
        """Test listing attachments for project with no attachments."""
        project_id = ProjectId(uuid4())
        result = repository.list_by_project(project_id)

        assert isinstance(result, Success)
        assert len(result.value) == 0

    def test_list_by_project_requires_project_id(self, repository: SqliteAttachmentRepository):
        """Test list_by_project requires ProjectId."""
        result = repository.list_by_project("not an id")  # type: ignore

        assert isinstance(result, Failure)
        assert "ProjectId" in result.error

    def test_list_by_field(self, repository: SqliteAttachmentRepository):
        """Test listing attachments for a specific field."""
        project_id = ProjectId(uuid4())
        field_id = FieldDefinitionId("site_photos")

        # Create attachments for different fields
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=project_id,
                field_id=field_id,
                file_path=f"photo{i}.jpg",
                index_type=IndexType.FIGURE,
                position=i,
            )
            for i in range(2)
        ]

        # Different field
        other_attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("other_field"),
            file_path="other.jpg",
            index_type=IndexType.IMAGE,
            position=0,
        )

        for attachment in attachments:
            repository.save(attachment)
        repository.save(other_attachment)

        # List by field
        result = repository.list_by_field(project_id, field_id)

        assert isinstance(result, Success)
        assert len(result.value) == 2  # Only attachments for this field

        # Verify sorted by position
        for i, attachment in enumerate(result.value):
            assert attachment.field_id == field_id
            assert attachment.position == i

    def test_list_by_field_requires_types(self, repository: SqliteAttachmentRepository):
        """Test list_by_field requires correct types."""
        project_id = ProjectId(uuid4())

        # Invalid project_id
        result = repository.list_by_field("not an id", FieldDefinitionId("field"))  # type: ignore
        assert isinstance(result, Failure)
        assert "ProjectId" in result.error

        # Invalid field_id
        result = repository.list_by_field(project_id, "not an id")  # type: ignore
        assert isinstance(result, Failure)
        assert "FieldDefinitionId" in result.error

    def test_delete(self, repository: SqliteAttachmentRepository, sample_attachment: Attachment):
        """Test deleting an attachment."""
        # Save
        repository.save(sample_attachment)

        # Delete
        result = repository.delete(sample_attachment.id)

        assert isinstance(result, Success)

        # Verify deleted
        get_result = repository.get_by_id(sample_attachment.id)
        assert isinstance(get_result, Failure)

    def test_delete_idempotent(self, repository: SqliteAttachmentRepository):
        """Test deleting non-existent attachment is not an error."""
        non_existent_id = AttachmentId(uuid4())
        result = repository.delete(non_existent_id)

        assert isinstance(result, Success)

    def test_delete_requires_attachment_id(self, repository: SqliteAttachmentRepository):
        """Test delete requires AttachmentId."""
        result = repository.delete("not an id")  # type: ignore

        assert isinstance(result, Failure)
        assert "AttachmentId" in result.error

    def test_exists(self, repository: SqliteAttachmentRepository, sample_attachment: Attachment):
        """Test checking attachment existence."""
        # Not exists initially
        result = repository.exists(sample_attachment.id)
        assert isinstance(result, Success)
        assert result.value is False

        # Save
        repository.save(sample_attachment)

        # Exists now
        result = repository.exists(sample_attachment.id)
        assert isinstance(result, Success)
        assert result.value is True

        # Delete
        repository.delete(sample_attachment.id)

        # Not exists after delete
        result = repository.exists(sample_attachment.id)
        assert isinstance(result, Success)
        assert result.value is False

    def test_exists_requires_attachment_id(self, repository: SqliteAttachmentRepository):
        """Test exists requires AttachmentId."""
        result = repository.exists("not an id")  # type: ignore

        assert isinstance(result, Failure)
        assert "AttachmentId" in result.error

    def test_delete_by_project(self, repository: SqliteAttachmentRepository):
        """Test deleting all attachments for a project."""
        project_id = ProjectId(uuid4())
        other_project_id = ProjectId(uuid4())

        # Create attachments for project
        for i in range(3):
            attachment = Attachment(
                id=AttachmentId(uuid4()),
                project_id=project_id,
                field_id=FieldDefinitionId("photos"),
                file_path=f"photo{i}.jpg",
                index_type=IndexType.FIGURE,
                position=i,
            )
            repository.save(attachment)

        # Create attachment for other project
        other_attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=other_project_id,
            field_id=FieldDefinitionId("photos"),
            file_path="other.jpg",
            index_type=IndexType.FIGURE,
            position=0,
        )
        repository.save(other_attachment)

        # Delete by project
        result = repository.delete_by_project(project_id)

        assert isinstance(result, Success)
        assert result.value == 3  # 3 attachments deleted

        # Verify project attachments deleted
        list_result = repository.list_by_project(project_id)
        assert isinstance(list_result, Success)
        assert len(list_result.value) == 0

        # Verify other project attachments still exist
        other_list_result = repository.list_by_project(other_project_id)
        assert isinstance(other_list_result, Success)
        assert len(other_list_result.value) == 1

    def test_delete_by_project_requires_project_id(self, repository: SqliteAttachmentRepository):
        """Test delete_by_project requires ProjectId."""
        result = repository.delete_by_project("not an id")  # type: ignore

        assert isinstance(result, Failure)
        assert "ProjectId" in result.error

    def test_delete_by_field(self, repository: SqliteAttachmentRepository):
        """Test deleting all attachments for a field."""
        project_id = ProjectId(uuid4())
        field_id = FieldDefinitionId("site_photos")
        other_field_id = FieldDefinitionId("other_photos")

        # Create attachments for field
        for i in range(2):
            attachment = Attachment(
                id=AttachmentId(uuid4()),
                project_id=project_id,
                field_id=field_id,
                file_path=f"photo{i}.jpg",
                index_type=IndexType.FIGURE,
                position=i,
            )
            repository.save(attachment)

        # Create attachment for other field
        other_attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=project_id,
            field_id=other_field_id,
            file_path="other.jpg",
            index_type=IndexType.IMAGE,
            position=0,
        )
        repository.save(other_attachment)

        # Delete by field
        result = repository.delete_by_field(project_id, field_id)

        assert isinstance(result, Success)
        assert result.value == 2  # 2 attachments deleted

        # Verify field attachments deleted
        list_result = repository.list_by_field(project_id, field_id)
        assert isinstance(list_result, Success)
        assert len(list_result.value) == 0

        # Verify other field attachments still exist
        other_list_result = repository.list_by_field(project_id, other_field_id)
        assert isinstance(other_list_result, Success)
        assert len(other_list_result.value) == 1

    def test_delete_by_field_requires_types(self, repository: SqliteAttachmentRepository):
        """Test delete_by_field requires correct types."""
        project_id = ProjectId(uuid4())

        # Invalid project_id
        result = repository.delete_by_field("not an id", FieldDefinitionId("field"))  # type: ignore
        assert isinstance(result, Failure)
        assert "ProjectId" in result.error

        # Invalid field_id
        result = repository.delete_by_field(project_id, "not an id")  # type: ignore
        assert isinstance(result, Failure)
        assert "FieldDefinitionId" in result.error

    def test_update_positions(self, repository: SqliteAttachmentRepository):
        """Test batch updating attachment positions."""
        project_id = ProjectId(uuid4())
        field_id = FieldDefinitionId("photos")

        # Create attachments
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=project_id,
                field_id=field_id,
                file_path=f"photo{i}.jpg",
                index_type=IndexType.FIGURE,
                position=i,
            )
            for i in range(3)
        ]

        for attachment in attachments:
            repository.save(attachment)

        # Reverse positions (drag-and-drop reorder)
        updated_attachments = [
            attachments[0].set_position(2),
            attachments[1].set_position(1),
            attachments[2].set_position(0),
        ]

        # Update positions
        result = repository.update_positions(updated_attachments)

        assert isinstance(result, Success)

        # Verify positions updated
        list_result = repository.list_by_field(project_id, field_id)
        assert isinstance(list_result, Success)
        loaded = list_result.value

        # Should be sorted by new positions
        assert loaded[0].id == attachments[2].id  # Position 0
        assert loaded[1].id == attachments[1].id  # Position 1
        assert loaded[2].id == attachments[0].id  # Position 2

    def test_update_positions_requires_list(self, repository: SqliteAttachmentRepository):
        """Test update_positions requires list."""
        result = repository.update_positions("not a list")  # type: ignore

        assert isinstance(result, Failure)
        assert "must be a list" in result.error

    def test_update_positions_requires_attachment_instances(self, repository: SqliteAttachmentRepository):
        """Test update_positions requires Attachment instances."""
        result = repository.update_positions(["not an attachment"])  # type: ignore

        assert isinstance(result, Failure)
        assert "Attachment instances" in result.error

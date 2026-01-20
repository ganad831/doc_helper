"""Unit tests for Attachment entity."""

from uuid import uuid4

import pytest

from doc_helper.domain.file.entities.attachment import Attachment
from doc_helper.domain.file.file_ids import AttachmentId
from doc_helper.domain.file.value_objects.index_type import IndexType
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class TestAttachmentCreation:
    """Test Attachment creation."""

    def test_create_valid_attachment(self):
        """Test creating a valid attachment."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("site_photos"),
            file_path="attachments/photo1.jpg",
            index_type=IndexType.FIGURE,
            exclude_from_index=False,
            caption="Site overview",
            position=0,
        )

        assert isinstance(attachment.id, AttachmentId)
        assert isinstance(attachment.project_id, ProjectId)
        assert attachment.file_path == "attachments/photo1.jpg"
        assert attachment.index_type == IndexType.FIGURE
        assert attachment.exclude_from_index is False
        assert attachment.caption == "Site overview"
        assert attachment.position == 0

    def test_create_with_defaults(self):
        """Test creating with default values."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="files/test.pdf",
        )

        assert attachment.index_type == IndexType.FIGURE  # Default
        assert attachment.exclude_from_index is False  # Default
        assert attachment.caption == ""  # Default
        assert attachment.position == 0  # Default

    def test_create_excluded_attachment(self):
        """Test creating an excluded attachment."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("docs"),
            file_path="docs/report.pdf",
            exclude_from_index=True,
        )

        assert attachment.exclude_from_index is True


class TestAttachmentValidation:
    """Test Attachment validation."""

    def test_rejects_invalid_id_type(self):
        """Test that invalid ID type is rejected."""
        with pytest.raises(TypeError, match="id must be AttachmentId"):
            Attachment(
                id="not_an_id",  # type: ignore
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo.jpg",
            )

    def test_rejects_invalid_project_id_type(self):
        """Test that invalid project_id type is rejected."""
        with pytest.raises(TypeError, match="project_id must be ProjectId"):
            Attachment(
                id=AttachmentId(uuid4()),
                project_id="not_a_project_id",  # type: ignore
                field_id=FieldDefinitionId("photos"),
                file_path="photo.jpg",
            )

    def test_rejects_empty_file_path(self):
        """Test that empty file_path is rejected."""
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="",
            )

    def test_rejects_negative_position(self):
        """Test that negative position is rejected."""
        with pytest.raises(ValueError, match="position must be >= 0"):
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo.jpg",
                position=-1,
            )


class TestAttachmentProperties:
    """Test Attachment properties."""

    def test_file_name_property(self):
        """Test file_name property extracts name."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="attachments/subfolder/photo1.jpg",
        )

        assert attachment.file_name == "photo1.jpg"

    def test_file_extension_property(self):
        """Test file_extension property."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
        )

        assert attachment.file_extension == ".jpg"

    def test_is_image_property_true(self):
        """Test is_image property returns True for images."""
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]

        for ext in image_extensions:
            attachment = Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path=f"photo{ext}",
            )
            assert attachment.is_image is True, f"Expected {ext} to be recognized as image"

    def test_is_image_property_false(self):
        """Test is_image property returns False for non-images."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("docs"),
            file_path="document.pdf",
        )

        assert attachment.is_image is False

    def test_is_pdf_property_true(self):
        """Test is_pdf property returns True for PDFs."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("docs"),
            file_path="document.pdf",
        )

        assert attachment.is_pdf is True

    def test_is_pdf_property_false(self):
        """Test is_pdf property returns False for non-PDFs."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
        )

        assert attachment.is_pdf is False

    def test_should_have_figure_number(self):
        """Test should_have_figure_number property."""
        # Included in numbering
        attachment1 = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            exclude_from_index=False,
        )
        assert attachment1.should_have_figure_number is True

        # Excluded from numbering
        attachment2 = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            exclude_from_index=True,
        )
        assert attachment2.should_have_figure_number is False


class TestAttachmentMethods:
    """Test Attachment methods."""

    def test_set_caption(self):
        """Test set_caption method."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            caption="Old caption",
        )

        new_attachment = attachment.set_caption("New caption")

        assert new_attachment.caption == "New caption"
        assert attachment.caption == "Old caption"  # Original unchanged

    def test_set_index_type(self):
        """Test set_index_type method."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            index_type=IndexType.FIGURE,
        )

        new_attachment = attachment.set_index_type(IndexType.IMAGE)

        assert new_attachment.index_type == IndexType.IMAGE
        assert attachment.index_type == IndexType.FIGURE  # Original unchanged

    def test_exclude_from_numbering(self):
        """Test exclude_from_numbering method."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            exclude_from_index=False,
        )

        new_attachment = attachment.exclude_from_numbering()

        assert new_attachment.exclude_from_index is True
        assert attachment.exclude_from_index is False  # Original unchanged

    def test_include_in_numbering(self):
        """Test include_in_numbering method."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            exclude_from_index=True,
        )

        new_attachment = attachment.include_in_numbering()

        assert new_attachment.exclude_from_index is False
        assert attachment.exclude_from_index is True  # Original unchanged

    def test_set_position(self):
        """Test set_position method."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            position=0,
        )

        new_attachment = attachment.set_position(5)

        assert new_attachment.position == 5
        assert attachment.position == 0  # Original unchanged

    def test_set_position_rejects_negative(self):
        """Test set_position rejects negative values."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
        )

        with pytest.raises(ValueError, match="position must be >= 0"):
            attachment.set_position(-1)


class TestAttachmentStringRepresentation:
    """Test string representations."""

    def test_str_representation(self):
        """Test __str__ method."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="attachments/photo1.jpg",
            index_type=IndexType.FIGURE,
        )

        str_repr = str(attachment)
        assert "photo1.jpg" in str_repr
        assert "figure" in str_repr.lower()

    def test_str_representation_excluded(self):
        """Test __str__ for excluded attachment."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            exclude_from_index=True,
        )

        str_repr = str(attachment)
        assert "excluded" in str_repr.lower()

    def test_repr_representation(self):
        """Test __repr__ method."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            index_type=IndexType.IMAGE,
            exclude_from_index=True,
        )

        repr_str = repr(attachment)
        assert "Attachment" in repr_str
        assert "photo.jpg" in repr_str
        assert "IMAGE" in repr_str
        assert "exclude=True" in repr_str

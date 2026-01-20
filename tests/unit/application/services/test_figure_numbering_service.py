"""Unit tests for FigureNumberingService."""

from uuid import uuid4

import pytest

from doc_helper.application.services.figure_numbering_service import FigureNumberingService
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.file.entities.attachment import Attachment
from doc_helper.domain.file.file_ids import AttachmentId
from doc_helper.domain.file.value_objects.figure_number import FigureNumber
from doc_helper.domain.file.value_objects.index_type import IndexType
from doc_helper.domain.file.value_objects.numbering_format import NumberingFormat
from doc_helper.domain.file.value_objects.numbering_style import NumberingStyle
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class TestCalculateNumbers:
    """Test calculate_numbers method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return FigureNumberingService()

    def test_empty_list_returns_empty_dict(self, service):
        """Test that empty list returns empty result dict."""
        result = service.calculate_numbers([])

        assert isinstance(result, Success)
        assert result.value == {}

    def test_single_attachment_gets_number_1(self, service):
        """Test single attachment receives sequence 1."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            index_type=IndexType.FIGURE,
            position=0,
        )

        result = service.calculate_numbers([attachment])

        assert isinstance(result, Success)
        assert len(result.value) == 1
        figure_number = result.value[str(attachment.id.value)]
        assert figure_number.index_type == IndexType.FIGURE
        assert figure_number.sequence == 1

    def test_multiple_attachments_same_type_get_sequential_numbers(self, service):
        """Test multiple attachments of same type get sequential numbers."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path=f"photo{i}.jpg",
                index_type=IndexType.FIGURE,
                position=i,
            )
            for i in range(3)
        ]

        result = service.calculate_numbers(attachments)

        assert isinstance(result, Success)
        assert len(result.value) == 3

        # Check sequential numbering
        for i, attachment in enumerate(attachments):
            figure_number = result.value[str(attachment.id.value)]
            assert figure_number.sequence == i + 1

    def test_excluded_attachments_not_numbered(self, service):
        """Test attachments with exclude_from_index=True are not numbered."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo1.jpg",
                index_type=IndexType.FIGURE,
                position=0,
                exclude_from_index=False,
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo2.jpg",
                index_type=IndexType.FIGURE,
                position=1,
                exclude_from_index=True,  # Excluded
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo3.jpg",
                index_type=IndexType.FIGURE,
                position=2,
                exclude_from_index=False,
            ),
        ]

        result = service.calculate_numbers(attachments)

        assert isinstance(result, Success)
        assert len(result.value) == 2  # Only 2 numbered

        # Check first attachment is Figure 1
        assert result.value[str(attachments[0].id.value)].sequence == 1

        # Check second attachment is NOT in result
        assert str(attachments[1].id.value) not in result.value

        # Check third attachment is Figure 2 (not 3, because 2 was excluded)
        assert result.value[str(attachments[2].id.value)].sequence == 2

    def test_different_index_types_have_independent_numbering(self, service):
        """Test different index types maintain independent counters."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="figure1.jpg",
                index_type=IndexType.FIGURE,
                position=0,
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("images"),
                file_path="image1.jpg",
                index_type=IndexType.IMAGE,
                position=0,
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="figure2.jpg",
                index_type=IndexType.FIGURE,
                position=1,
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("images"),
                file_path="image2.jpg",
                index_type=IndexType.IMAGE,
                position=1,
            ),
        ]

        result = service.calculate_numbers(attachments)

        assert isinstance(result, Success)
        assert len(result.value) == 4

        # Check FIGURE attachments: Figure 1, Figure 2
        assert result.value[str(attachments[0].id.value)].sequence == 1
        assert result.value[str(attachments[0].id.value)].index_type == IndexType.FIGURE
        assert result.value[str(attachments[2].id.value)].sequence == 2
        assert result.value[str(attachments[2].id.value)].index_type == IndexType.FIGURE

        # Check IMAGE attachments: Image 1, Image 2
        assert result.value[str(attachments[1].id.value)].sequence == 1
        assert result.value[str(attachments[1].id.value)].index_type == IndexType.IMAGE
        assert result.value[str(attachments[3].id.value)].sequence == 2
        assert result.value[str(attachments[3].id.value)].index_type == IndexType.IMAGE

    def test_position_determines_numbering_order(self, service):
        """Test attachments are numbered according to position, not insertion order."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo_c.jpg",
                index_type=IndexType.FIGURE,
                position=2,  # Third position
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo_a.jpg",
                index_type=IndexType.FIGURE,
                position=0,  # First position
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo_b.jpg",
                index_type=IndexType.FIGURE,
                position=1,  # Second position
            ),
        ]

        result = service.calculate_numbers(attachments)

        assert isinstance(result, Success)

        # Check numbering follows position, not insertion order
        assert result.value[str(attachments[0].id.value)].sequence == 3  # position 2 → Figure 3
        assert result.value[str(attachments[1].id.value)].sequence == 1  # position 0 → Figure 1
        assert result.value[str(attachments[2].id.value)].sequence == 2  # position 1 → Figure 2

    def test_invalid_input_type_returns_failure(self, service):
        """Test invalid input type returns Failure."""
        result = service.calculate_numbers("not a list")

        assert isinstance(result, Failure)
        assert "must be a list" in result.error

    def test_invalid_attachment_type_returns_failure(self, service):
        """Test list containing non-Attachment returns Failure."""
        result = service.calculate_numbers([Attachment, "not an attachment"])

        assert isinstance(result, Failure)
        assert "Attachment instances" in result.error


class TestFormatNumber:
    """Test format_number method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return FigureNumberingService()

    def test_format_number_with_arabic_style(self, service):
        """Test formatting with Arabic numerals."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=5)
        format_spec = NumberingFormat(style=NumberingStyle.ARABIC, prefix="Fig. ", suffix=".")

        result = service.format_number(figure_number, format_spec)

        assert isinstance(result, Success)
        assert result.value == "Fig. 5."

    def test_format_number_with_roman_upper_style(self, service):
        """Test formatting with Roman numerals (uppercase)."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=7)
        format_spec = NumberingFormat(style=NumberingStyle.ROMAN_UPPER, prefix="(", suffix=")")

        result = service.format_number(figure_number, format_spec)

        assert isinstance(result, Success)
        assert result.value == "(VII)"

    def test_format_number_with_alpha_upper_style(self, service):
        """Test formatting with alphabetic uppercase."""
        figure_number = FigureNumber(index_type=IndexType.APPENDIX, sequence=3)
        format_spec = NumberingFormat(style=NumberingStyle.ALPHA_UPPER, prefix="Appendix ", suffix="")

        result = service.format_number(figure_number, format_spec)

        assert isinstance(result, Success)
        assert result.value == "Appendix C"

    def test_format_number_with_no_prefix_suffix(self, service):
        """Test formatting with no prefix or suffix."""
        figure_number = FigureNumber(index_type=IndexType.IMAGE, sequence=10)
        format_spec = NumberingFormat(style=NumberingStyle.ARABIC)

        result = service.format_number(figure_number, format_spec)

        assert isinstance(result, Success)
        assert result.value == "10"

    def test_invalid_figure_number_type_returns_failure(self, service):
        """Test invalid figure_number type returns Failure."""
        format_spec = NumberingFormat()

        result = service.format_number("not a figure number", format_spec)

        assert isinstance(result, Failure)
        assert "FigureNumber" in result.error

    def test_invalid_format_spec_type_returns_failure(self, service):
        """Test invalid format_spec type returns Failure."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)

        result = service.format_number(figure_number, "not a format spec")

        assert isinstance(result, Failure)
        assert "NumberingFormat" in result.error


class TestCalculateAndFormat:
    """Test calculate_and_format method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return FigureNumberingService()

    def test_calculate_and_format_with_single_type(self, service):
        """Test end-to-end calculation and formatting for single index type."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path=f"photo{i}.jpg",
                index_type=IndexType.FIGURE,
                position=i,
            )
            for i in range(3)
        ]

        format_specs = {
            IndexType.FIGURE: NumberingFormat(prefix="Fig. ", suffix=".")
        }

        result = service.calculate_and_format(attachments, format_specs)

        assert isinstance(result, Success)
        assert len(result.value) == 3

        # Check formatted strings
        assert result.value[str(attachments[0].id.value)] == "Fig. 1."
        assert result.value[str(attachments[1].id.value)] == "Fig. 2."
        assert result.value[str(attachments[2].id.value)] == "Fig. 3."

    def test_calculate_and_format_with_multiple_types(self, service):
        """Test formatting with different specs per index type."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="figure.jpg",
                index_type=IndexType.FIGURE,
                position=0,
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("images"),
                file_path="image.jpg",
                index_type=IndexType.IMAGE,
                position=0,
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("tables"),
                file_path="table.jpg",
                index_type=IndexType.TABLE,
                position=0,
            ),
        ]

        format_specs = {
            IndexType.FIGURE: NumberingFormat(
                style=NumberingStyle.ARABIC,
                prefix="Figure ",
                suffix=""
            ),
            IndexType.IMAGE: NumberingFormat(
                style=NumberingStyle.ROMAN_UPPER,
                prefix="Image ",
                suffix=""
            ),
            IndexType.TABLE: NumberingFormat(
                style=NumberingStyle.ALPHA_UPPER,
                prefix="Table ",
                suffix=""
            ),
        }

        result = service.calculate_and_format(attachments, format_specs)

        assert isinstance(result, Success)
        assert len(result.value) == 3

        # Check each type formatted correctly
        assert result.value[str(attachments[0].id.value)] == "Figure 1"
        assert result.value[str(attachments[1].id.value)] == "Image I"
        assert result.value[str(attachments[2].id.value)] == "Table A"

    def test_calculate_and_format_uses_default_if_spec_missing(self, service):
        """Test default format used if spec not provided for index type."""
        attachment = Attachment(
            id=AttachmentId(uuid4()),
            project_id=ProjectId(uuid4()),
            field_id=FieldDefinitionId("photos"),
            file_path="photo.jpg",
            index_type=IndexType.FIGURE,
            position=0,
        )

        format_specs = {}  # No spec for FIGURE

        result = service.calculate_and_format([attachment], format_specs)

        assert isinstance(result, Success)
        assert len(result.value) == 1

        # Should use default format (ARABIC, no prefix/suffix)
        assert result.value[str(attachment.id.value)] == "1"

    def test_invalid_format_specs_type_returns_failure(self, service):
        """Test invalid format_specs type returns Failure."""
        attachments = []

        result = service.calculate_and_format(attachments, "not a dict")

        assert isinstance(result, Failure)
        assert "must be a dict" in result.error


class TestGetNextPosition:
    """Test get_next_position method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return FigureNumberingService()

    def test_next_position_with_no_attachments(self, service):
        """Test next position is 0 when no attachments exist."""
        result = service.get_next_position([], IndexType.FIGURE)

        assert isinstance(result, Success)
        assert result.value == 0

    def test_next_position_with_no_attachments_of_type(self, service):
        """Test next position is 0 when no attachments of requested type exist."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("images"),
                file_path="image.jpg",
                index_type=IndexType.IMAGE,  # Different type
                position=0,
            )
        ]

        result = service.get_next_position(attachments, IndexType.FIGURE)

        assert isinstance(result, Success)
        assert result.value == 0

    def test_next_position_with_one_attachment(self, service):
        """Test next position is max + 1 with one attachment."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo.jpg",
                index_type=IndexType.FIGURE,
                position=0,
            )
        ]

        result = service.get_next_position(attachments, IndexType.FIGURE)

        assert isinstance(result, Success)
        assert result.value == 1

    def test_next_position_with_multiple_attachments(self, service):
        """Test next position is max + 1 with multiple attachments."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path=f"photo{i}.jpg",
                index_type=IndexType.FIGURE,
                position=i,
            )
            for i in range(5)
        ]

        result = service.get_next_position(attachments, IndexType.FIGURE)

        assert isinstance(result, Success)
        assert result.value == 5  # Max position is 4, so next is 5

    def test_next_position_with_gaps_in_positions(self, service):
        """Test next position uses max, even with gaps."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo1.jpg",
                index_type=IndexType.FIGURE,
                position=0,
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="photo2.jpg",
                index_type=IndexType.FIGURE,
                position=5,  # Gap: positions 1-4 missing
            ),
        ]

        result = service.get_next_position(attachments, IndexType.FIGURE)

        assert isinstance(result, Success)
        assert result.value == 6  # Max is 5, so next is 6

    def test_next_position_only_considers_requested_type(self, service):
        """Test next position only considers attachments of requested type."""
        attachments = [
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("photos"),
                file_path="figure.jpg",
                index_type=IndexType.FIGURE,
                position=0,
            ),
            Attachment(
                id=AttachmentId(uuid4()),
                project_id=ProjectId(uuid4()),
                field_id=FieldDefinitionId("images"),
                file_path="image.jpg",
                index_type=IndexType.IMAGE,
                position=10,  # Higher position, but different type
            ),
        ]

        result = service.get_next_position(attachments, IndexType.FIGURE)

        assert isinstance(result, Success)
        assert result.value == 1  # Only FIGURE attachment at position 0

    def test_invalid_attachments_type_returns_failure(self, service):
        """Test invalid attachments type returns Failure."""
        result = service.get_next_position("not a list", IndexType.FIGURE)

        assert isinstance(result, Failure)
        assert "must be a list" in result.error

    def test_invalid_index_type_returns_failure(self, service):
        """Test invalid index_type returns Failure."""
        result = service.get_next_position([], "not an index type")

        assert isinstance(result, Failure)
        assert "IndexType" in result.error

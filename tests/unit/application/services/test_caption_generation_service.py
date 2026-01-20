"""Tests for CaptionGenerationService."""

import pytest

from doc_helper.application.services.caption_generation_service import (
    CaptionGenerationService,
)
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.file.value_objects.figure_number import FigureNumber
from doc_helper.domain.file.value_objects.index_type import IndexType
from doc_helper.domain.file.value_objects.numbering_format import NumberingFormat
from doc_helper.domain.file.value_objects.numbering_style import NumberingStyle


class TestCaptionGenerationService:
    """Tests for caption generation service."""

    @pytest.fixture
    def service(self) -> CaptionGenerationService:
        """Create service instance."""
        return CaptionGenerationService()

    def test_generate_simple_caption_no_text(self, service: CaptionGenerationService):
        """Test generating caption without user text."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat()

        result = service.generate_caption(figure_number, "", numbering_format)

        assert isinstance(result, Success)
        assert result.value == "Figure 1"

    def test_generate_caption_with_text(self, service: CaptionGenerationService):
        """Test generating caption with user text."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat()

        result = service.generate_caption(figure_number, "Site overview", numbering_format)

        assert isinstance(result, Success)
        assert result.value == "Figure 1: Site overview"

    def test_generate_caption_with_placeholders(self, service: CaptionGenerationService):
        """Test caption with placeholder resolution."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat()
        user_caption = "{label} {number}: {caption}"

        result = service.generate_caption(figure_number, user_caption, numbering_format)

        assert isinstance(result, Success)
        # Placeholder {caption} resolves to the whole user_caption string
        assert result.value == "Figure 1: {label} {number}: {caption}"

    def test_generate_caption_with_placeholder_template(self, service: CaptionGenerationService):
        """Test caption with meaningful placeholder usage."""
        figure_number = FigureNumber(index_type=IndexType.IMAGE, sequence=5)
        numbering_format = NumberingFormat()
        user_caption = "{label} {number} shows site location"

        result = service.generate_caption(figure_number, user_caption, numbering_format)

        assert isinstance(result, Success)
        assert result.value == "Image 5 shows site location"

    def test_generate_caption_roman_numerals(self, service: CaptionGenerationService):
        """Test caption with Roman numeral formatting."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=3)
        numbering_format = NumberingFormat(style=NumberingStyle.ROMAN_UPPER)

        result = service.generate_caption(figure_number, "Cross-section", numbering_format)

        assert isinstance(result, Success)
        assert result.value == "Figure III: Cross-section"

    def test_generate_caption_alpha_upper(self, service: CaptionGenerationService):
        """Test caption with alphabetic formatting."""
        figure_number = FigureNumber(index_type=IndexType.PLAN, sequence=2)
        numbering_format = NumberingFormat(style=NumberingStyle.ALPHA_UPPER)

        result = service.generate_caption(figure_number, "Floor plan", numbering_format)

        assert isinstance(result, Success)
        assert result.value == "Plan B: Floor plan"

    def test_generate_caption_with_prefix_suffix(self, service: CaptionGenerationService):
        """Test caption with numbering prefix/suffix."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat(prefix="(", suffix=")")

        result = service.generate_caption(figure_number, "Overview", numbering_format)

        assert isinstance(result, Success)
        assert result.value == "Figure (1): Overview"

    def test_generate_caption_with_format_prefix_suffix(self, service: CaptionGenerationService):
        """Test generate_caption_with_format with caption prefix/suffix."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat()

        result = service.generate_caption_with_format(
            figure_number,
            "Site overview",
            numbering_format,
            caption_prefix="(",
            caption_suffix=")"
        )

        assert isinstance(result, Success)
        assert result.value == "(Figure 1) Site overview"

    def test_generate_caption_with_format_both_prefix_suffix(self, service: CaptionGenerationService):
        """Test with both numbering and caption prefix/suffix."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat(prefix="[", suffix="]")

        result = service.generate_caption_with_format(
            figure_number,
            "Overview",
            numbering_format,
            caption_prefix="(",
            caption_suffix=")"
        )

        assert isinstance(result, Success)
        assert result.value == "(Figure [1]) Overview"

    def test_generate_caption_with_format_no_user_text(self, service: CaptionGenerationService):
        """Test format with no user caption text."""
        figure_number = FigureNumber(index_type=IndexType.IMAGE, sequence=2)
        numbering_format = NumberingFormat()

        result = service.generate_caption_with_format(
            figure_number,
            "",
            numbering_format,
            caption_prefix="<",
            caption_suffix=">"
        )

        assert isinstance(result, Success)
        assert result.value == "<Image 2>"

    def test_generate_simple_caption_convenience(self, service: CaptionGenerationService):
        """Test simple_caption convenience method."""
        result = service.generate_simple_caption(
            IndexType.FIGURE,
            1,
            "Site overview"
        )

        assert isinstance(result, Success)
        assert result.value == "Figure 1: Site overview"

    def test_generate_simple_caption_no_text(self, service: CaptionGenerationService):
        """Test simple_caption without user text."""
        result = service.generate_simple_caption(IndexType.TABLE, 3)

        assert isinstance(result, Success)
        assert result.value == "Table 3"

    def test_generate_caption_different_index_types(self, service: CaptionGenerationService):
        """Test captions for different index types."""
        numbering_format = NumberingFormat()

        for index_type in IndexType:
            figure_number = FigureNumber(index_type=index_type, sequence=1)
            result = service.generate_caption(figure_number, "Test", numbering_format)

            assert isinstance(result, Success)
            assert result.value.startswith(index_type.display_name)

    def test_generate_caption_invalid_figure_number_type(self, service: CaptionGenerationService):
        """Test with invalid figure_number type."""
        result = service.generate_caption(
            "not a figure number",  # type: ignore
            "Caption",
            NumberingFormat()
        )

        assert isinstance(result, Failure)
        assert "FigureNumber" in result.error

    def test_generate_caption_invalid_format_type(self, service: CaptionGenerationService):
        """Test with invalid numbering_format type."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)

        result = service.generate_caption(
            figure_number,
            "Caption",
            "not a format"  # type: ignore
        )

        assert isinstance(result, Failure)
        assert "NumberingFormat" in result.error

    def test_generate_simple_caption_invalid_index_type(self, service: CaptionGenerationService):
        """Test simple_caption with invalid index_type."""
        result = service.generate_simple_caption(
            "not an index type",  # type: ignore
            1,
            "Caption"
        )

        assert isinstance(result, Failure)
        assert "IndexType" in result.error

    def test_generate_simple_caption_invalid_sequence(self, service: CaptionGenerationService):
        """Test simple_caption with invalid sequence."""
        result = service.generate_simple_caption(IndexType.FIGURE, 0, "Caption")

        assert isinstance(result, Failure)
        assert "sequence must be >= 1" in result.error

    def test_placeholder_resolution_label(self, service: CaptionGenerationService):
        """Test {label} placeholder resolution."""
        figure_number = FigureNumber(index_type=IndexType.APPENDIX, sequence=1)
        numbering_format = NumberingFormat()

        result = service.generate_caption(
            figure_number,
            "See {label} for details",
            numbering_format
        )

        assert isinstance(result, Success)
        assert result.value == "See Appendix for details"

    def test_placeholder_resolution_number(self, service: CaptionGenerationService):
        """Test {number} placeholder resolution."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=42)
        numbering_format = NumberingFormat()

        result = service.generate_caption(
            figure_number,
            "Item {number} of series",
            numbering_format
        )

        assert isinstance(result, Success)
        assert result.value == "Item 42 of series"

    def test_placeholder_resolution_multiple(self, service: CaptionGenerationService):
        """Test multiple placeholders in one caption."""
        figure_number = FigureNumber(index_type=IndexType.CHART, sequence=7)
        numbering_format = NumberingFormat(style=NumberingStyle.ROMAN_LOWER)

        result = service.generate_caption(
            figure_number,
            "{label} {number} ({label} number {number})",
            numbering_format
        )

        assert isinstance(result, Success)
        assert result.value == "Chart vii (Chart number vii)"

    def test_caption_with_colon_in_user_text(self, service: CaptionGenerationService):
        """Test caption where user text contains colon."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat()

        result = service.generate_caption(
            figure_number,
            "Site: North view",
            numbering_format
        )

        assert isinstance(result, Success)
        assert result.value == "Figure 1: Site: North view"

    def test_caption_with_empty_placeholder(self, service: CaptionGenerationService):
        """Test caption with placeholder but empty caption value."""
        figure_number = FigureNumber(index_type=IndexType.IMAGE, sequence=3)
        numbering_format = NumberingFormat()

        result = service.generate_caption(
            figure_number,
            "{label} {number}",
            numbering_format
        )

        assert isinstance(result, Success)
        assert result.value == "Image 3"

    def test_generate_caption_with_format_placeholder_caption(
        self, service: CaptionGenerationService
    ):
        """Test caption_with_format when user caption has placeholders."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat()

        result = service.generate_caption_with_format(
            figure_number,
            "{label} {number} shows overview",
            numbering_format,
            caption_prefix="[",
            caption_suffix="]"
        )

        assert isinstance(result, Success)
        # When placeholders present, just wrap entire caption
        assert result.value == "[Figure 1 shows overview]"

    def test_caption_with_unicode(self, service: CaptionGenerationService):
        """Test caption with Unicode characters (Arabic example)."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat()

        result = service.generate_caption(
            figure_number,
            "منظر عام للموقع",  # "Site overview" in Arabic
            numbering_format
        )

        assert isinstance(result, Success)
        assert result.value == "Figure 1: منظر عام للموقع"

    def test_caption_very_long_text(self, service: CaptionGenerationService):
        """Test caption with very long user text."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat()
        long_text = "A" * 1000

        result = service.generate_caption(figure_number, long_text, numbering_format)

        assert isinstance(result, Success)
        assert result.value.startswith("Figure 1: A")
        assert len(result.value) == 1000 + len("Figure 1: ")

    def test_caption_with_special_characters(self, service: CaptionGenerationService):
        """Test caption with special characters."""
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        numbering_format = NumberingFormat()

        result = service.generate_caption(
            figure_number,
            "Site #1 @ 50% scale (2024)",
            numbering_format
        )

        assert isinstance(result, Success)
        assert result.value == "Figure 1: Site #1 @ 50% scale (2024)"

    def test_generate_caption_sequence_edge_cases(self, service: CaptionGenerationService):
        """Test caption generation with edge case sequence numbers."""
        numbering_format = NumberingFormat(style=NumberingStyle.ROMAN_UPPER)

        # Large sequence number
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=3999)
        result = service.generate_caption(figure_number, "Test", numbering_format)
        assert isinstance(result, Success)
        assert "MMMCMXCIX" in result.value

        # Sequence 1 (minimum)
        figure_number = FigureNumber(index_type=IndexType.FIGURE, sequence=1)
        result = service.generate_caption(figure_number, "Test", numbering_format)
        assert isinstance(result, Success)
        assert "Figure I" in result.value

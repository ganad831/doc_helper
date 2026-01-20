"""Unit tests for IndexType enum."""

from doc_helper.domain.file.value_objects.index_type import IndexType


class TestIndexType:
    """Test IndexType enum."""

    def test_all_index_types_exist(self):
        """Test all expected index types are defined."""
        assert IndexType.FIGURE == "figure"
        assert IndexType.IMAGE == "image"
        assert IndexType.PLAN == "plan"
        assert IndexType.TABLE == "table"
        assert IndexType.APPENDIX == "appendix"
        assert IndexType.SECTION == "section"
        assert IndexType.CHART == "chart"

    def test_display_names(self):
        """Test display names are capitalized."""
        assert IndexType.FIGURE.display_name == "Figure"
        assert IndexType.IMAGE.display_name == "Image"
        assert IndexType.PLAN.display_name == "Plan"
        assert IndexType.TABLE.display_name == "Table"
        assert IndexType.APPENDIX.display_name == "Appendix"

    def test_is_figure_property(self):
        """Test is_figure property."""
        assert IndexType.FIGURE.is_figure is True
        assert IndexType.IMAGE.is_figure is False
        assert IndexType.PLAN.is_figure is False

    def test_is_image_property(self):
        """Test is_image property."""
        assert IndexType.IMAGE.is_image is True
        assert IndexType.FIGURE.is_image is False
        assert IndexType.PLAN.is_image is False

    def test_string_representation(self):
        """Test __str__ returns value."""
        assert str(IndexType.FIGURE) == "figure"
        assert str(IndexType.IMAGE) == "image"

    def test_repr_representation(self):
        """Test __repr__ returns debug string."""
        assert repr(IndexType.FIGURE) == "IndexType.FIGURE"
        assert repr(IndexType.IMAGE) == "IndexType.IMAGE"

    def test_equality(self):
        """Test enum equality."""
        assert IndexType.FIGURE == "figure"
        assert IndexType.FIGURE == IndexType.FIGURE
        assert IndexType.FIGURE != IndexType.IMAGE

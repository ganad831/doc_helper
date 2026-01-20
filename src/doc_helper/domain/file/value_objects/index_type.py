"""Index type value object for figure numbering."""

from enum import Enum


class IndexType(str, Enum):
    """Index type for figure numbering.

    Each index type maintains its own independent counter:
    - FIGURE 1, FIGURE 2, FIGURE 3
    - IMAGE 1, IMAGE 2, IMAGE 3
    - PLAN 1, PLAN 2, PLAN 3
    - Etc.

    Example:
        index_type = IndexType.FIGURE
        assert index_type == "figure"
        assert index_type.display_name == "Figure"
    """

    FIGURE = "figure"
    IMAGE = "image"
    PLAN = "plan"
    TABLE = "table"
    APPENDIX = "appendix"
    SECTION = "section"
    CHART = "chart"

    @property
    def display_name(self) -> str:
        """Get display name for this index type.

        Returns:
            Capitalized name (e.g., "Figure", "Image")
        """
        return self.value.capitalize()

    @property
    def is_figure(self) -> bool:
        """Check if this is a figure index type."""
        return self == IndexType.FIGURE

    @property
    def is_image(self) -> bool:
        """Check if this is an image index type."""
        return self == IndexType.IMAGE

    def __str__(self) -> str:
        """String representation (value)."""
        return self.value

    def __repr__(self) -> str:
        """Debug representation."""
        return f"IndexType.{self.name}"

"""Figure number value object."""

from dataclasses import dataclass

from doc_helper.domain.file.value_objects.index_type import IndexType


@dataclass(frozen=True)
class FigureNumber:
    """Auto-assigned sequential number for a figure/image/etc.

    Immutable value object representing a number assigned to a file attachment.
    Each index type maintains its own sequence (Figure 1, Figure 2 vs Image 1, Image 2).

    Example:
        number = FigureNumber(
            index_type=IndexType.FIGURE,
            sequence=5
        )
        assert number.display_value == "5"
        assert str(number) == "Figure 5"
    """

    index_type: IndexType
    sequence: int  # 1-based sequential number within index type

    def __post_init__(self) -> None:
        """Validate figure number.

        Raises:
            TypeError: If index_type is not IndexType
            ValueError: If sequence is less than 1
        """
        if not isinstance(self.index_type, IndexType):
            raise TypeError(f"index_type must be IndexType, got {type(self.index_type)}")
        if not isinstance(self.sequence, int):
            raise TypeError(f"sequence must be int, got {type(self.sequence)}")
        if self.sequence < 1:
            raise ValueError(f"sequence must be >= 1, got {self.sequence}")

    @property
    def display_value(self) -> str:
        """Get display value (just the number).

        Returns:
            String representation of sequence number
        """
        return str(self.sequence)

    def __str__(self) -> str:
        """String representation with index type.

        Returns:
            "Figure 5", "Image 3", etc.
        """
        return f"{self.index_type.display_name} {self.sequence}"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"FigureNumber(index_type={self.index_type!r}, sequence={self.sequence})"

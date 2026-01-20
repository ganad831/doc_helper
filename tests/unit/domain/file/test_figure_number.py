"""Unit tests for FigureNumber value object."""

import pytest

from doc_helper.domain.file.value_objects.figure_number import FigureNumber
from doc_helper.domain.file.value_objects.index_type import IndexType


class TestFigureNumberCreation:
    """Test FigureNumber creation."""

    def test_create_valid_figure_number(self):
        """Test creating a valid figure number."""
        number = FigureNumber(
            index_type=IndexType.FIGURE,
            sequence=5
        )

        assert number.index_type == IndexType.FIGURE
        assert number.sequence == 5

    def test_create_image_number(self):
        """Test creating an image number."""
        number = FigureNumber(
            index_type=IndexType.IMAGE,
            sequence=3
        )

        assert number.index_type == IndexType.IMAGE
        assert number.sequence == 3

    def test_create_sequence_one(self):
        """Test creating sequence number 1."""
        number = FigureNumber(
            index_type=IndexType.PLAN,
            sequence=1
        )

        assert number.sequence == 1


class TestFigureNumberValidation:
    """Test FigureNumber validation."""

    def test_rejects_invalid_index_type(self):
        """Test that invalid index_type is rejected."""
        with pytest.raises(TypeError, match="index_type must be IndexType"):
            FigureNumber(
                index_type="figure",  # type: ignore
                sequence=1
            )

    def test_rejects_invalid_sequence_type(self):
        """Test that non-int sequence is rejected."""
        with pytest.raises(TypeError, match="sequence must be int"):
            FigureNumber(
                index_type=IndexType.FIGURE,
                sequence="5"  # type: ignore
            )

    def test_rejects_zero_sequence(self):
        """Test that sequence must be >= 1."""
        with pytest.raises(ValueError, match="sequence must be >= 1"):
            FigureNumber(
                index_type=IndexType.FIGURE,
                sequence=0
            )

    def test_rejects_negative_sequence(self):
        """Test that negative sequence is rejected."""
        with pytest.raises(ValueError, match="sequence must be >= 1"):
            FigureNumber(
                index_type=IndexType.FIGURE,
                sequence=-1
            )


class TestFigureNumberProperties:
    """Test FigureNumber properties."""

    def test_display_value(self):
        """Test display_value property."""
        number = FigureNumber(
            index_type=IndexType.FIGURE,
            sequence=5
        )

        assert number.display_value == "5"

    def test_display_value_large_number(self):
        """Test display_value with large sequence."""
        number = FigureNumber(
            index_type=IndexType.TABLE,
            sequence=123
        )

        assert number.display_value == "123"


class TestFigureNumberStringRepresentation:
    """Test string representations."""

    def test_str_representation(self):
        """Test __str__ includes index type."""
        number = FigureNumber(
            index_type=IndexType.FIGURE,
            sequence=5
        )

        assert str(number) == "Figure 5"

    def test_str_representation_image(self):
        """Test __str__ for image type."""
        number = FigureNumber(
            index_type=IndexType.IMAGE,
            sequence=3
        )

        assert str(number) == "Image 3"

    def test_repr_representation(self):
        """Test __repr__ is debuggable."""
        number = FigureNumber(
            index_type=IndexType.PLAN,
            sequence=7
        )

        repr_str = repr(number)
        assert "FigureNumber" in repr_str
        assert "IndexType.PLAN" in repr_str
        assert "7" in repr_str


class TestFigureNumberImmutability:
    """Test FigureNumber immutability."""

    def test_is_immutable(self):
        """Test that FigureNumber is frozen."""
        number = FigureNumber(
            index_type=IndexType.FIGURE,
            sequence=5
        )

        with pytest.raises(AttributeError):
            number.sequence = 10  # type: ignore

    def test_equality(self):
        """Test equality comparison."""
        number1 = FigureNumber(IndexType.FIGURE, 5)
        number2 = FigureNumber(IndexType.FIGURE, 5)
        number3 = FigureNumber(IndexType.FIGURE, 6)
        number4 = FigureNumber(IndexType.IMAGE, 5)

        assert number1 == number2
        assert number1 != number3
        assert number1 != number4

    def test_hashable(self):
        """Test that FigureNumber is hashable."""
        number1 = FigureNumber(IndexType.FIGURE, 5)
        number2 = FigureNumber(IndexType.FIGURE, 5)

        # Can be used in sets
        number_set = {number1, number2}
        assert len(number_set) == 1  # Same value, one item

        # Can be used as dict keys
        number_dict = {number1: "value"}
        assert number_dict[number2] == "value"

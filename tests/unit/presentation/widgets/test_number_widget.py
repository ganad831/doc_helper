"""Tests for number field widget."""

import pytest

from doc_helper.presentation.widgets.number_widget import NumberFieldWidget


class TestNumberFieldWidget:
    """Tests for NumberFieldWidget."""

    @pytest.fixture
    def widget(self) -> NumberFieldWidget:
        """Create NumberFieldWidget instance."""
        return NumberFieldWidget()

    def test_set_value_with_integer(self, widget: NumberFieldWidget) -> None:
        """Test setting value with integer."""
        # Act
        widget.set_value(42)

        # Assert
        assert widget.get_value() == 42

    def test_set_value_with_float(self, widget: NumberFieldWidget) -> None:
        """Test setting value with float."""
        # Act
        widget.set_value(3.14)

        # Assert
        assert widget.get_value() == 3.14

    def test_set_value_with_none(self, widget: NumberFieldWidget) -> None:
        """Test setting value with None."""
        # Act
        widget.set_value(None)

        # Assert
        assert widget.get_value() is None

    def test_set_value_with_string_integer(self, widget: NumberFieldWidget) -> None:
        """Test setting value with string representation of integer."""
        # Act
        widget.set_value("42")

        # Assert
        assert widget.get_value() == 42

    def test_set_value_with_string_float(self, widget: NumberFieldWidget) -> None:
        """Test setting value with string representation of float."""
        # Act
        widget.set_value("3.14")

        # Assert
        assert widget.get_value() == 3.14

    def test_set_value_with_invalid_string(self, widget: NumberFieldWidget) -> None:
        """Test setting value with invalid string."""
        # Act
        widget.set_value("not a number")

        # Assert
        assert widget.get_value() is None

    def test_set_value_with_negative_number(self, widget: NumberFieldWidget) -> None:
        """Test setting value with negative number."""
        # Act
        widget.set_value(-42)

        # Assert
        assert widget.get_value() == -42

    def test_set_value_with_zero(self, widget: NumberFieldWidget) -> None:
        """Test setting value with zero."""
        # Act
        widget.set_value(0)

        # Assert
        assert widget.get_value() == 0

    def test_get_value_initial_state(self, widget: NumberFieldWidget) -> None:
        """Test getting value in initial state."""
        # Assert
        assert widget.get_value() is None

"""Tests for checkbox field widget."""

import pytest

from doc_helper.presentation.widgets.checkbox_widget import CheckboxFieldWidget


class TestCheckboxFieldWidget:
    """Tests for CheckboxFieldWidget."""

    @pytest.fixture
    def widget(self) -> CheckboxFieldWidget:
        """Create CheckboxFieldWidget instance."""
        return CheckboxFieldWidget()

    def test_set_value_with_true(self, widget: CheckboxFieldWidget) -> None:
        """Test setting value with True."""
        # Act
        widget.set_value(True)

        # Assert
        assert widget.get_value() is True

    def test_set_value_with_false(self, widget: CheckboxFieldWidget) -> None:
        """Test setting value with False."""
        # Act
        widget.set_value(False)

        # Assert
        assert widget.get_value() is False

    def test_set_value_with_none(self, widget: CheckboxFieldWidget) -> None:
        """Test setting value with None converts to False."""
        # Act
        widget.set_value(None)

        # Assert
        assert widget.get_value() is False

    def test_set_value_with_truthy_value(self, widget: CheckboxFieldWidget) -> None:
        """Test setting value with truthy value."""
        # Act
        widget.set_value(1)

        # Assert
        assert widget.get_value() is True

    def test_set_value_with_falsy_value(self, widget: CheckboxFieldWidget) -> None:
        """Test setting value with falsy value."""
        # Act
        widget.set_value(0)

        # Assert
        assert widget.get_value() is False

    def test_set_value_with_string_true(self, widget: CheckboxFieldWidget) -> None:
        """Test setting value with non-empty string."""
        # Act
        widget.set_value("true")

        # Assert
        assert widget.get_value() is True

    def test_set_value_with_empty_string(self, widget: CheckboxFieldWidget) -> None:
        """Test setting value with empty string."""
        # Act
        widget.set_value("")

        # Assert
        assert widget.get_value() is False

    def test_get_value_initial_state(self, widget: CheckboxFieldWidget) -> None:
        """Test getting value in initial state."""
        # Assert - initial state should be None or False
        value = widget.get_value()
        assert value is None or value is False

"""Tests for text field widgets."""

import pytest

from doc_helper.presentation.widgets.text_widget import (
    TextAreaFieldWidget,
    TextFieldWidget,
)


class TestTextFieldWidget:
    """Tests for TextFieldWidget."""

    @pytest.fixture
    def widget(self) -> TextFieldWidget:
        """Create TextFieldWidget instance."""
        return TextFieldWidget()

    def test_set_value_with_string(self, widget: TextFieldWidget) -> None:
        """Test setting value with string."""
        # Act
        widget.set_value("Hello World")

        # Assert
        assert widget.get_value() == "Hello World"

    def test_set_value_with_none(self, widget: TextFieldWidget) -> None:
        """Test setting value with None."""
        # Act
        widget.set_value(None)

        # Assert
        assert widget.get_value() is None

    def test_set_value_with_empty_string(self, widget: TextFieldWidget) -> None:
        """Test setting value with empty string."""
        # Act
        widget.set_value("")

        # Assert
        assert widget.get_value() is None

    def test_set_value_with_number(self, widget: TextFieldWidget) -> None:
        """Test setting value with number (converts to string)."""
        # Act
        widget.set_value(42)

        # Assert
        assert widget.get_value() == "42"

    def test_get_value_initial_state(self, widget: TextFieldWidget) -> None:
        """Test getting value in initial state."""
        # Assert
        assert widget.get_value() is None

    def test_set_enabled(self, widget: TextFieldWidget) -> None:
        """Test setting enabled state."""
        # Act & Assert - should not raise exception
        widget.set_enabled(True)
        widget.set_enabled(False)

    def test_set_visible(self, widget: TextFieldWidget) -> None:
        """Test setting visibility."""
        # Act & Assert - should not raise exception
        widget.set_visible(True)
        widget.set_visible(False)

    def test_set_validation_errors(self, widget: TextFieldWidget) -> None:
        """Test setting validation errors."""
        # Arrange
        from doc_helper.domain.common.i18n import TranslationKey
        from doc_helper.domain.validation.validation_result import ValidationError

        error = ValidationError(
            field_path="test.field",
            message_key=TranslationKey("validation.required"),
            constraint_type="RequiredConstraint",
            current_value=None,
        )
        errors = [error]

        # Act & Assert - should not raise exception
        widget.set_validation_errors(errors)

    def test_value_changed_callback(self, widget: TextFieldWidget) -> None:
        """Test value changed callback is called."""
        # Arrange
        callback_called = False
        callback_value = None

        def callback(value):
            nonlocal callback_called, callback_value
            callback_called = True
            callback_value = value

        widget.on_value_changed(callback)

        # Act
        widget.set_value("Test")
        widget._notify_value_changed()

        # Assert
        assert callback_called
        assert callback_value == "Test"


class TestTextAreaFieldWidget:
    """Tests for TextAreaFieldWidget."""

    @pytest.fixture
    def widget(self) -> TextAreaFieldWidget:
        """Create TextAreaFieldWidget instance."""
        return TextAreaFieldWidget()

    def test_set_value_with_string(self, widget: TextAreaFieldWidget) -> None:
        """Test setting value with string."""
        # Act
        widget.set_value("Line 1\nLine 2\nLine 3")

        # Assert
        assert widget.get_value() == "Line 1\nLine 2\nLine 3"

    def test_set_value_with_none(self, widget: TextAreaFieldWidget) -> None:
        """Test setting value with None."""
        # Act
        widget.set_value(None)

        # Assert
        assert widget.get_value() is None

    def test_set_value_with_empty_string(self, widget: TextAreaFieldWidget) -> None:
        """Test setting value with empty string."""
        # Act
        widget.set_value("")

        # Assert
        assert widget.get_value() is None

    def test_multiline_text(self, widget: TextAreaFieldWidget) -> None:
        """Test handling multiline text."""
        # Arrange
        multiline = "First line\nSecond line\nThird line"

        # Act
        widget.set_value(multiline)

        # Assert
        assert widget.get_value() == multiline
        assert "\n" in widget.get_value()

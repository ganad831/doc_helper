"""Text field widget."""

from typing import Any, Optional

from doc_helper.presentation.widgets.field_widget import IFieldWidget


class TextFieldWidget(IFieldWidget):
    """Widget for TEXT field type.

    Displays a single-line text input.

    v1 Implementation:
    - Single-line text entry
    - Character limit based on MaxLengthConstraint
    - Validation error display

    tkinter Implementation Notes (for future):
    - Use ttk.Entry for input
    - Use ttk.Label for validation errors
    - Bind <KeyRelease> to validate as user types
    """

    def set_value(self, value: Any) -> None:
        """Set field value.

        Args:
            value: String value
        """
        if value is None:
            self._value = ""
        else:
            self._value = str(value)
        # In tkinter implementation: update Entry widget

    def get_value(self) -> Optional[str]:
        """Get field value.

        Returns:
            Current string value or None
        """
        if self._value == "":
            return None
        return self._value

    def _update_enabled_state(self) -> None:
        """Update UI to reflect enabled/disabled state."""
        # In tkinter implementation: widget.config(state='normal' or 'disabled')
        pass

    def _update_visibility(self) -> None:
        """Update UI to reflect visibility."""
        # In tkinter implementation: widget.grid() or widget.grid_remove()
        pass

    def _update_validation_display(self) -> None:
        """Update UI to display validation errors."""
        # In tkinter implementation: show/hide error label, update border color
        pass


class TextAreaFieldWidget(IFieldWidget):
    """Widget for TEXTAREA field type.

    Displays a multi-line text input.

    v1 Implementation:
    - Multi-line text entry
    - Scrollbar for long content
    - Character limit based on MaxLengthConstraint

    tkinter Implementation Notes:
    - Use tkinter.Text widget with scrollbar
    - Configure height based on field definition
    """

    def set_value(self, value: Any) -> None:
        """Set field value."""
        if value is None:
            self._value = ""
        else:
            self._value = str(value)

    def get_value(self) -> Optional[str]:
        """Get field value."""
        if self._value == "":
            return None
        return self._value

    def _update_enabled_state(self) -> None:
        """Update enabled state."""
        pass

    def _update_visibility(self) -> None:
        """Update visibility."""
        pass

    def _update_validation_display(self) -> None:
        """Update validation display."""
        pass

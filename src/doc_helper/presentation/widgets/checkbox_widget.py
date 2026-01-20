"""Checkbox field widget."""

from typing import Any, Optional

from doc_helper.presentation.widgets.field_widget import IFieldWidget


class CheckboxFieldWidget(IFieldWidget):
    """Widget for CHECKBOX field type.

    Displays a checkbox for boolean true/false values.

    v1 Implementation:
    - Simple checked/unchecked state
    - Boolean value (True/False)
    - Optional label text

    tkinter Implementation Notes (for future):
    - Use ttk.Checkbutton
    - Bind to BooleanVar for state management
    - Handle command callback for value changes
    """

    def set_value(self, value: Any) -> None:
        """Set field value.

        Args:
            value: Boolean value
        """
        if value is None:
            self._value = False
        elif isinstance(value, bool):
            self._value = value
        else:
            # Convert to boolean
            self._value = bool(value)
        # In tkinter implementation: update BooleanVar

    def get_value(self) -> Optional[bool]:
        """Get field value.

        Returns:
            Current boolean value
        """
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
        # In tkinter implementation: show/hide error label
        pass

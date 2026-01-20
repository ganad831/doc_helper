"""Number field widget."""

from typing import Any, Optional

from doc_helper.presentation.widgets.field_widget import IFieldWidget


class NumberFieldWidget(IFieldWidget):
    """Widget for NUMBER field type.

    Displays a numeric input for integers or decimals.

    v1 Implementation:
    - Integer and decimal support
    - Min/Max value constraints
    - Validation error display

    tkinter Implementation Notes (for future):
    - Use ttk.Entry with number validation
    - Use ttk.Spinbox for integer fields with step controls
    - Bind <KeyRelease> to validate as user types
    - Only allow numeric characters, minus sign, and decimal point
    """

    def set_value(self, value: Any) -> None:
        """Set field value.

        Args:
            value: Numeric value (int or float)
        """
        if value is None:
            self._value = None
        elif isinstance(value, (int, float)):
            self._value = value
        else:
            # Try to convert to number
            try:
                # Try int first
                if "." not in str(value):
                    self._value = int(value)
                else:
                    self._value = float(value)
            except (ValueError, TypeError):
                self._value = None
        # In tkinter implementation: update Entry widget

    def get_value(self) -> Optional[float | int]:
        """Get field value.

        Returns:
            Current numeric value or None
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
        # In tkinter implementation: show/hide error label, update border color
        pass

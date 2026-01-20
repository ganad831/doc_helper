"""Date field widget."""

from datetime import date
from typing import Any, Optional

from doc_helper.presentation.widgets.field_widget import IFieldWidget


class DateFieldWidget(IFieldWidget):
    """Widget for DATE field type.

    Displays a date picker control.

    v1 Implementation:
    - Date selection via calendar picker
    - Date range constraints (min/max date)
    - ISO format display (YYYY-MM-DD)

    tkinter Implementation Notes (for future):
    - Use tkcalenendar.DateEntry for date picking
    - Display format: locale-aware
    - Store format: ISO (YYYY-MM-DD)
    - Min/Max date validation
    """

    def set_value(self, value: Any) -> None:
        """Set field value.

        Args:
            value: Date value (date object or ISO string)
        """
        if value is None:
            self._value = None
        elif isinstance(value, date):
            self._value = value
        elif isinstance(value, str):
            # Parse ISO format YYYY-MM-DD
            try:
                self._value = date.fromisoformat(value)
            except (ValueError, TypeError):
                self._value = None
        else:
            self._value = None
        # In tkinter implementation: update DateEntry widget

    def get_value(self) -> Optional[date]:
        """Get field value.

        Returns:
            Current date value or None
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

"""Calculated field widget."""

from typing import Any, Optional

from doc_helper.presentation.widgets.field_widget import IFieldWidget


class CalculatedFieldWidget(IFieldWidget):
    """Widget for CALCULATED field type.

    Displays a read-only calculated value from formula evaluation.

    v1 Implementation:
    - Read-only display
    - Shows computed value from formula
    - Visual indicator that field is calculated

    tkinter Implementation Notes (for future):
    - Use ttk.Label or ttk.Entry with state='readonly'
    - Different background color to indicate calculated nature
    - May show formula on hover/tooltip
    """

    def set_value(self, value: Any) -> None:
        """Set field value.

        Args:
            value: Calculated value (any type)
        """
        self._value = value
        # In tkinter implementation: update display widget

    def get_value(self) -> Optional[Any]:
        """Get field value.

        Returns:
            Current calculated value or None
        """
        return self._value

    def _update_enabled_state(self) -> None:
        """Update UI to reflect enabled/disabled state.

        Note: Calculated fields are always read-only.
        """
        # Calculated fields are always read-only
        # In tkinter implementation: widget.config(state='readonly')
        pass

    def _update_visibility(self) -> None:
        """Update UI to reflect visibility."""
        # In tkinter implementation: widget.grid() or widget.grid_remove()
        pass

    def _update_validation_display(self) -> None:
        """Update UI to display validation errors."""
        # In tkinter implementation: show/hide error label
        pass

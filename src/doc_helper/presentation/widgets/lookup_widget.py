"""Lookup field widget."""

from typing import Any, Optional

from doc_helper.presentation.widgets.field_widget import IFieldWidget


class LookupFieldWidget(IFieldWidget):
    """Widget for LOOKUP field type.

    Displays a value looked up from another entity/record.

    v1 Implementation:
    - Dropdown showing available lookup values
    - Displays related entity records
    - Reference to another entity's field

    tkinter Implementation Notes (for future):
    - Use ttk.Combobox with state='readonly'
    - Populate from related entity records
    - Show display field (e.g., name) but store ID
    - May include "Add New" button to create related record
    """

    def __init__(self, lookup_options: Optional[list[tuple[Any, str]]] = None) -> None:
        """Initialize lookup widget.

        Args:
            lookup_options: List of (value, display_text) tuples
        """
        super().__init__()
        self._lookup_options = lookup_options or []

    def set_lookup_options(self, options: list[tuple[Any, str]]) -> None:
        """Set available lookup options.

        Args:
            options: List of (value, display_text) tuples
        """
        self._lookup_options = options
        # In tkinter implementation: update Combobox values

    def set_value(self, value: Any) -> None:
        """Set field value.

        Args:
            value: Lookup value (typically an ID)
        """
        # Check if value exists in lookup options
        valid_values = [v for v, _ in self._lookup_options]
        if value is None or value in valid_values:
            self._value = value
        else:
            self._value = None
        # In tkinter implementation: update Combobox selection

    def get_value(self) -> Optional[Any]:
        """Get field value.

        Returns:
            Current lookup value or None
        """
        return self._value

    def _update_enabled_state(self) -> None:
        """Update UI to reflect enabled/disabled state."""
        # In tkinter implementation: widget.config(state='readonly' or 'disabled')
        pass

    def _update_visibility(self) -> None:
        """Update UI to reflect visibility."""
        # In tkinter implementation: widget.grid() or widget.grid_remove()
        pass

    def _update_validation_display(self) -> None:
        """Update UI to display validation errors."""
        # In tkinter implementation: show/hide error label
        pass

"""Radio button field widget."""

from typing import Any, Optional

from doc_helper.presentation.widgets.field_widget import IFieldWidget


class RadioFieldWidget(IFieldWidget):
    """Widget for RADIO field type.

    Displays radio buttons for single selection from options.

    v1 Implementation:
    - Single selection from predefined options
    - Options from AllowedValuesConstraint
    - Radio button group

    tkinter Implementation Notes (for future):
    - Use multiple ttk.Radiobutton widgets
    - Bind all to same StringVar
    - Create one Radiobutton per option
    - Handle command callback for selection changes
    """

    def __init__(self, options: Optional[list[str]] = None) -> None:
        """Initialize radio widget.

        Args:
            options: List of allowed values
        """
        super().__init__()
        self._options = options or []

    def set_options(self, options: list[str]) -> None:
        """Set available options.

        Args:
            options: List of allowed values
        """
        self._options = options
        # In tkinter implementation: recreate Radiobutton widgets

    def set_value(self, value: Any) -> None:
        """Set field value.

        Args:
            value: Selected option value
        """
        if value is None:
            self._value = None
        elif str(value) in self._options:
            self._value = str(value)
        else:
            # Value not in options
            self._value = None
        # In tkinter implementation: update StringVar

    def get_value(self) -> Optional[str]:
        """Get field value.

        Returns:
            Currently selected option or None
        """
        return self._value

    def _update_enabled_state(self) -> None:
        """Update UI to reflect enabled/disabled state."""
        # In tkinter implementation: all Radiobutton.config(state='normal' or 'disabled')
        pass

    def _update_visibility(self) -> None:
        """Update UI to reflect visibility."""
        # In tkinter implementation: all Radiobutton.grid() or grid_remove()
        pass

    def _update_validation_display(self) -> None:
        """Update UI to display validation errors."""
        # In tkinter implementation: show/hide error label
        pass

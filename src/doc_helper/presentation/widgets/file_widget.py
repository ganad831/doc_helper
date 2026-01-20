"""File attachment field widget."""

from pathlib import Path
from typing import Any, Optional

from doc_helper.presentation.widgets.field_widget import IFieldWidget


class FileFieldWidget(IFieldWidget):
    """Widget for FILE field type.

    Displays file attachment reference with upload/remove capabilities.

    v1 Implementation:
    - File path reference
    - Upload button to select file
    - Display filename
    - Remove button
    - File type constraints (extensions)

    tkinter Implementation Notes (for future):
    - Use ttk.Frame containing:
      - ttk.Label for filename display
      - ttk.Button for "Browse..." (opens file dialog)
      - ttk.Button for "Remove" (clears selection)
    - Store absolute path or relative to project
    - Validate file extension against AllowedFileTypesConstraint
    """

    def set_value(self, value: Any) -> None:
        """Set field value.

        Args:
            value: File path (str or Path)
        """
        if value is None:
            self._value = None
        elif isinstance(value, Path):
            self._value = value
        elif isinstance(value, str):
            self._value = Path(value)
        else:
            self._value = None
        # In tkinter implementation: update filename label

    def get_value(self) -> Optional[Path]:
        """Get field value.

        Returns:
            Current file path or None
        """
        return self._value

    def _update_enabled_state(self) -> None:
        """Update UI to reflect enabled/disabled state."""
        # In tkinter implementation: Browse/Remove buttons.config(state='normal' or 'disabled')
        pass

    def _update_visibility(self) -> None:
        """Update UI to reflect visibility."""
        # In tkinter implementation: widget.grid() or widget.grid_remove()
        pass

    def _update_validation_display(self) -> None:
        """Update UI to display validation errors."""
        # In tkinter implementation: show/hide error label
        pass

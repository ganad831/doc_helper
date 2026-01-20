"""Table field widget."""

from typing import Any, Optional

from doc_helper.presentation.widgets.field_widget import IFieldWidget


class TableFieldWidget(IFieldWidget):
    """Widget for TABLE field type.

    Displays nested tabular data (child records) with add/edit/delete capabilities.

    v1 Implementation:
    - Grid/table display of child records
    - Add/Edit/Delete row buttons
    - Column headers from child entity definition
    - Inline editing or dialog-based editing

    tkinter Implementation Notes (for future):
    - Use ttk.Treeview in table mode for grid display
    - Columns from child entity field definitions
    - Toolbar with Add/Edit/Delete buttons
    - Double-click row to edit
    - Edit dialog shows full form for child entity
    - Store as list of child records (each record is dict of field values)

    Design Note:
    - Each row represents a child entity instance
    - Child entity has its own EntityDefinition
    - Validation applies to each child record
    - Formulas can reference child table fields (e.g., SUM, COUNT)
    """

    def __init__(self, child_entity_name: Optional[str] = None) -> None:
        """Initialize table widget.

        Args:
            child_entity_name: Name of child entity definition
        """
        super().__init__()
        self._child_entity_name = child_entity_name
        self._value: list[dict[str, Any]] = []

    def set_child_entity(self, child_entity_name: str) -> None:
        """Set child entity definition.

        Args:
            child_entity_name: Name of child entity
        """
        self._child_entity_name = child_entity_name
        # In tkinter implementation: update Treeview columns

    def set_value(self, value: Any) -> None:
        """Set field value.

        Args:
            value: List of child records (list of dicts)
        """
        if value is None:
            self._value = []
        elif isinstance(value, list):
            # Validate each record is a dict
            self._value = [
                record for record in value if isinstance(record, dict)
            ]
        else:
            self._value = []
        # In tkinter implementation: update Treeview rows

    def get_value(self) -> Optional[list[dict[str, Any]]]:
        """Get field value.

        Returns:
            List of child records or None if empty
        """
        if not self._value:
            return None
        return self._value

    def add_row(self, record: dict[str, Any]) -> None:
        """Add a new row to the table.

        Args:
            record: Child record data
        """
        self._value.append(record)
        # In tkinter implementation: insert into Treeview
        # Trigger value changed callback
        if self._value_changed_callback:
            self._value_changed_callback(self._value)

    def update_row(self, index: int, record: dict[str, Any]) -> None:
        """Update an existing row.

        Args:
            index: Row index
            record: Updated child record data
        """
        if 0 <= index < len(self._value):
            self._value[index] = record
            # In tkinter implementation: update Treeview row
            # Trigger value changed callback
            if self._value_changed_callback:
                self._value_changed_callback(self._value)

    def delete_row(self, index: int) -> None:
        """Delete a row from the table.

        Args:
            index: Row index
        """
        if 0 <= index < len(self._value):
            del self._value[index]
            # In tkinter implementation: delete from Treeview
            # Trigger value changed callback
            if self._value_changed_callback:
                self._value_changed_callback(self._value)

    def _update_enabled_state(self) -> None:
        """Update UI to reflect enabled/disabled state."""
        # In tkinter implementation: Treeview and toolbar buttons config(state=...)
        pass

    def _update_visibility(self) -> None:
        """Update UI to reflect visibility."""
        # In tkinter implementation: widget.grid() or widget.grid_remove()
        pass

    def _update_validation_display(self) -> None:
        """Update UI to display validation errors."""
        # In tkinter implementation: highlight invalid rows, show error summary
        pass

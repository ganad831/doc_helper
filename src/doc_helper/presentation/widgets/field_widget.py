"""Base field widget interface.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md):
- Presentation layer uses DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from doc_helper.application.dto import FieldDefinitionDTO


class IFieldWidget(ABC):
    """Interface for field widgets.

    Field widgets are responsible for:
    - Displaying field value
    - Capturing user input
    - Showing validation errors
    - Handling enabled/disabled state
    - Handling visibility

    Each field type (TEXT, NUMBER, DATE, etc.) has its own widget implementation.

    Example:
        widget = TextFieldWidget(field_dto)
        widget.set_value("Hello")
        widget.set_enabled(True)
        widget.on_value_changed(lambda v: print(f"New value: {v}"))
    """

    def __init__(self, field_definition: Optional[FieldDefinitionDTO] = None) -> None:
        """Initialize field widget.

        Args:
            field_definition: Field definition DTO (optional for v1)
        """
        self._field_definition = field_definition
        self._value: Optional[Any] = None
        self._validation_errors: list[str] = []  # List of error message strings
        self._is_enabled = True
        self._is_visible = True
        self._value_changed_callback: Optional[Callable[[Any], None]] = None

    @property
    def field_definition(self) -> Optional[FieldDefinitionDTO]:
        """Get field definition.

        Returns:
            FieldDefinitionDTO for this widget (optional for v1)
        """
        return self._field_definition

    @property
    def value(self) -> Optional[Any]:
        """Get current value.

        Returns:
            Current field value
        """
        return self._value

    @property
    def has_validation_errors(self) -> bool:
        """Check if field has validation errors.

        Returns:
            True if validation errors exist
        """
        return len(self._validation_errors) > 0

    @property
    def validation_errors(self) -> list[str]:
        """Get validation errors.

        Returns:
            List of validation error messages (strings, not domain objects)
        """
        return self._validation_errors

    @abstractmethod
    def set_value(self, value: Any) -> None:
        """Set field value.

        Args:
            value: Value to set
        """
        pass

    @abstractmethod
    def get_value(self) -> Optional[Any]:
        """Get field value.

        Returns:
            Current field value
        """
        pass

    def set_enabled(self, enabled: bool) -> None:
        """Set enabled state.

        Args:
            enabled: True to enable, False to disable
        """
        self._is_enabled = enabled
        self._update_enabled_state()

    def set_visible(self, visible: bool) -> None:
        """Set visibility.

        Args:
            visible: True to show, False to hide
        """
        self._is_visible = visible
        self._update_visibility()

    def set_validation_errors(self, errors: list[str]) -> None:
        """Set validation errors for this field.

        Args:
            errors: List of validation error messages (strings)
        """
        self._validation_errors = errors
        self._update_validation_display()

    def on_value_changed(self, callback: Callable[[Any], None]) -> None:
        """Register callback for value changes.

        Args:
            callback: Function to call when value changes
        """
        self._value_changed_callback = callback

    def _notify_value_changed(self) -> None:
        """Notify that value has changed."""
        if self._value_changed_callback:
            self._value_changed_callback(self._value)

    @abstractmethod
    def _update_enabled_state(self) -> None:
        """Update UI to reflect enabled/disabled state."""
        pass

    @abstractmethod
    def _update_visibility(self) -> None:
        """Update UI to reflect visibility."""
        pass

    @abstractmethod
    def _update_validation_display(self) -> None:
        """Update UI to display validation errors."""
        pass

    def dispose(self) -> None:
        """Clean up resources."""
        self._value_changed_callback = None
        self._validation_errors.clear()

"""Base field widget interface.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md):
- Presentation layer uses DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary

ADR-025: Validation Severity Levels
- Widgets display validation errors with severity-based visual differentiation
- ERROR (red): Critical issues
- WARNING (yellow): Non-critical issues
- INFO (blue): Informational messages
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from doc_helper.application.dto import FieldDefinitionDTO, ValidationErrorDTO


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
        self._validation_errors: list[str] = []  # List of error message strings (legacy)
        self._validation_error_dtos: list[ValidationErrorDTO] = []  # ADR-025: Full DTOs with severity
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
        """Check if field has validation errors (any severity).

        ADR-025: Checks for errors of any severity (ERROR, WARNING, INFO).

        Returns:
            True if validation errors exist
        """
        return len(self._validation_error_dtos) > 0 or len(self._validation_errors) > 0

    @property
    def validation_errors(self) -> list[str]:
        """Get validation error messages (legacy, no severity info).

        Returns:
            List of validation error messages (strings, not domain objects)
        """
        # If DTOs available, extract messages; otherwise use legacy list
        if self._validation_error_dtos:
            return [error.message for error in self._validation_error_dtos]
        return self._validation_errors

    @property
    def validation_error_dtos(self) -> list[ValidationErrorDTO]:
        """Get validation error DTOs with severity information.

        ADR-025: Returns full ValidationErrorDTO objects with severity field.

        Returns:
            List of ValidationErrorDTO objects
        """
        return self._validation_error_dtos

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
        """Set validation errors for this field (legacy method, no severity).

        Deprecated: Use set_validation_error_dtos() for severity support.

        Args:
            errors: List of validation error messages (strings)
        """
        self._validation_errors = errors
        self._validation_error_dtos = []  # Clear DTOs when using legacy method
        self._update_validation_display()

    def set_validation_error_dtos(self, error_dtos: list[ValidationErrorDTO]) -> None:
        """Set validation errors with severity information.

        ADR-025: Accepts ValidationErrorDTO objects with severity field for
        severity-aware display (ERROR/WARNING/INFO visual differentiation).

        Args:
            error_dtos: List of ValidationErrorDTO objects with severity
        """
        self._validation_error_dtos = error_dtos
        self._validation_errors = []  # Clear legacy list when using DTOs
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
        """Update UI to display validation errors.

        ADR-025: Implementations should check self._validation_error_dtos for
        severity-aware display:
        - ERROR severity: Red color/icon
        - WARNING severity: Yellow/orange color/icon
        - INFO severity: Blue color/icon

        If _validation_error_dtos is empty, fall back to _validation_errors (legacy).
        """
        pass

    def dispose(self) -> None:
        """Clean up resources."""
        self._value_changed_callback = None
        self._validation_errors.clear()
        self._validation_error_dtos.clear()

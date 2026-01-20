"""Field widget factory using registry pattern.

RULES (AGENT_RULES.md Section 3-4, ADR-012):
- Registry-based factory for extensibility
- Maps field types to widget classes
- Presentation layer uses DTOs, NOT domain objects
"""

from typing import Dict, Optional, Type

from doc_helper.application.dto import FieldDefinitionDTO
from doc_helper.presentation.widgets.calculated_widget import CalculatedFieldWidget
from doc_helper.presentation.widgets.checkbox_widget import CheckboxFieldWidget
from doc_helper.presentation.widgets.date_widget import DateFieldWidget
from doc_helper.presentation.widgets.dropdown_widget import DropdownFieldWidget
from doc_helper.presentation.widgets.field_widget import IFieldWidget
from doc_helper.presentation.widgets.file_widget import FileFieldWidget
from doc_helper.presentation.widgets.image_widget import ImageFieldWidget
from doc_helper.presentation.widgets.lookup_widget import LookupFieldWidget
from doc_helper.presentation.widgets.number_widget import NumberFieldWidget
from doc_helper.presentation.widgets.radio_widget import RadioFieldWidget
from doc_helper.presentation.widgets.table_widget import TableFieldWidget
from doc_helper.presentation.widgets.text_widget import TextAreaFieldWidget, TextFieldWidget


class FieldWidgetFactory:
    """Factory for creating field widgets based on field type.

    Uses registry pattern (ADR-012) for extensibility.

    v1 Implementation:
    - Maps all 12 field types to widget classes
    - Creates widget instances from FieldDefinitionDTO

    v2+ Extension:
    - Can register custom widget types
    - Plugin system for new field types

    Example:
        factory = FieldWidgetFactory()
        widget = factory.create_widget(field_definition_dto)
        widget.set_value(initial_value)
    """

    def __init__(self) -> None:
        """Initialize factory with default widget type registry."""
        # Registry mapping field type strings to widget classes
        self._registry: Dict[str, Type[IFieldWidget]] = {}

        # Register all 12 v1 field types (FROZEN list)
        self._register_default_widgets()

    def _register_default_widgets(self) -> None:
        """Register default widget types for all 12 v1 field types."""
        self._registry["text"] = TextFieldWidget
        self._registry["textarea"] = TextAreaFieldWidget
        self._registry["number"] = NumberFieldWidget
        self._registry["date"] = DateFieldWidget
        self._registry["dropdown"] = DropdownFieldWidget
        self._registry["checkbox"] = CheckboxFieldWidget
        self._registry["radio"] = RadioFieldWidget
        self._registry["calculated"] = CalculatedFieldWidget
        self._registry["lookup"] = LookupFieldWidget
        self._registry["file"] = FileFieldWidget
        self._registry["image"] = ImageFieldWidget
        self._registry["table"] = TableFieldWidget

    def register_widget_type(
        self, field_type: str, widget_class: Type[IFieldWidget]
    ) -> None:
        """Register a custom widget type.

        Args:
            field_type: Field type string (e.g., "text", "number")
            widget_class: Widget class to instantiate for this type

        Note:
            v2+ feature for custom field types. In v1, the 12 types are FROZEN.
        """
        self._registry[field_type.lower()] = widget_class

    def create_widget(
        self, field_definition: FieldDefinitionDTO
    ) -> Optional[IFieldWidget]:
        """Create a widget for the given field definition.

        Args:
            field_definition: Field definition DTO (NOT domain object)

        Returns:
            Widget instance or None if field type not recognized

        Example:
            widget = factory.create_widget(field_def_dto)
            if widget:
                widget.set_value(initial_value)
                widget.on_value_changed(callback)
        """
        field_type = field_definition.field_type.lower()

        if field_type not in self._registry:
            # Unknown field type - this should not happen in v1 with frozen types
            return None

        widget_class = self._registry[field_type]
        return widget_class(field_definition)

    def supports_field_type(self, field_type: str) -> bool:
        """Check if a field type is supported.

        Args:
            field_type: Field type string

        Returns:
            True if factory can create widget for this type
        """
        return field_type.lower() in self._registry

    def list_supported_types(self) -> list[str]:
        """Get list of supported field types.

        Returns:
            List of field type strings

        Example:
            types = factory.list_supported_types()
            # ['text', 'textarea', 'number', ...]
        """
        return list(self._registry.keys())

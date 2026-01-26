"""Unit tests for FieldWidgetFactory.

Tests the registry-based factory pattern for creating field widgets.
"""

import pytest

from doc_helper.application.dto import FieldDefinitionDTO, FieldOptionDTO
from doc_helper.presentation.factories import FieldWidgetFactory
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


class TestFieldWidgetFactory:
    """Test FieldWidgetFactory."""

    def test_factory_initialization(self):
        """Test factory initializes with all 12 v1 field types."""
        factory = FieldWidgetFactory()

        expected_types = [
            "text",
            "textarea",
            "number",
            "date",
            "dropdown",
            "checkbox",
            "radio",
            "calculated",
            "lookup",
            "file",
            "image",
            "table",
        ]

        supported = factory.list_supported_types()
        assert len(supported) == 12
        for field_type in expected_types:
            assert field_type in supported

    def test_create_text_widget(self):
        """Test creating TEXT widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_1",
            field_type="text",
            label="Name",
            help_text=None,
            required=True,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, TextFieldWidget)
        assert widget.field_definition == field_def

    def test_create_textarea_widget(self):
        """Test creating TEXTAREA widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_2",
            field_type="textarea",
            label="Description",
            help_text=None,
            required=False,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, TextAreaFieldWidget)

    def test_create_number_widget(self):
        """Test creating NUMBER widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_3",
            field_type="number",
            label="Age",
            help_text=None,
            required=True,
            default_value="0",
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, NumberFieldWidget)

    def test_create_date_widget(self):
        """Test creating DATE widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_4",
            field_type="date",
            label="Birth Date",
            help_text=None,
            required=True,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, DateFieldWidget)

    def test_create_dropdown_widget(self):
        """Test creating DROPDOWN widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_5",
            field_type="dropdown",
            label="Status",
            help_text=None,
            required=True,
            default_value=None,
            options=(
                FieldOptionDTO(value="active", label="Active"),
                FieldOptionDTO(value="inactive", label="Inactive"),
            ),
            formula=None,
            is_calculated=False,
            is_choice_field=True,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, DropdownFieldWidget)

    def test_create_checkbox_widget(self):
        """Test creating CHECKBOX widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_6",
            field_type="checkbox",
            label="Accept Terms",
            help_text=None,
            required=True,
            default_value="false",
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, CheckboxFieldWidget)

    def test_create_radio_widget(self):
        """Test creating RADIO widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_7",
            field_type="radio",
            label="Gender",
            help_text=None,
            required=True,
            default_value=None,
            options=(
                FieldOptionDTO(value="male", label="Male"),
                FieldOptionDTO(value="female", label="Female"),
            ),
            formula=None,
            is_calculated=False,
            is_choice_field=True,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, RadioFieldWidget)

    def test_create_calculated_widget(self):
        """Test creating CALCULATED widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_8",
            field_type="calculated",
            label="Total",
            help_text=None,
            required=False,
            default_value=None,
            options=(),
            formula="{{quantity}} * {{price}}",
            is_calculated=True,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, CalculatedFieldWidget)

    def test_create_lookup_widget(self):
        """Test creating LOOKUP widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_9",
            field_type="lookup",
            label="Related Entity",
            help_text=None,
            required=False,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id="entity_2",
            lookup_display_field="name",
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, LookupFieldWidget)

    def test_create_file_widget(self):
        """Test creating FILE widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_10",
            field_type="file",
            label="Attachment",
            help_text=None,
            required=False,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, FileFieldWidget)

    def test_create_image_widget(self):
        """Test creating IMAGE widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_11",
            field_type="image",
            label="Photo",
            help_text=None,
            required=False,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, ImageFieldWidget)

    def test_create_table_widget(self):
        """Test creating TABLE widget."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_12",
            field_type="table",
            label="Items",
            help_text=None,
            required=False,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=True,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id="entity_child",
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, TableFieldWidget)

    def test_create_widget_with_unknown_type(self):
        """Test creating widget with unknown field type returns None."""
        factory = FieldWidgetFactory()
        field_def = FieldDefinitionDTO(
            id="field_unknown",
            field_type="unknown",
            label="Unknown",
            help_text=None,
            required=False,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is None

    def test_supports_field_type(self):
        """Test supports_field_type method."""
        factory = FieldWidgetFactory()

        assert factory.supports_field_type("text")
        assert factory.supports_field_type("TEXT")  # Case insensitive
        assert factory.supports_field_type("number")
        assert not factory.supports_field_type("unknown")

    def test_register_custom_widget_type(self):
        """Test registering custom widget type (v2+ feature)."""
        factory = FieldWidgetFactory()

        # Create a custom widget class
        class CustomWidget(IFieldWidget):
            def set_value(self, value):
                self._value = value

            def get_value(self):
                return self._value

            def _update_enabled_state(self):
                pass

            def _update_visibility(self):
                pass

            def _update_validation_display(self):
                pass

        # Register custom type
        factory.register_widget_type("custom", CustomWidget)

        assert factory.supports_field_type("custom")
        assert "custom" in factory.list_supported_types()

        # Create widget with custom type
        field_def = FieldDefinitionDTO(
            id="field_custom",
            field_type="custom",
            label="Custom Field",
            help_text=None,
            required=False,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )

        widget = factory.create_widget(field_def)
        assert widget is not None
        assert isinstance(widget, CustomWidget)

"""Tests for FieldDefinition."""

import pytest

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import FieldDefinitionId
from doc_helper.domain.validation.constraints import (
    AllowedValuesConstraint,
    MaxLengthConstraint,
    MinLengthConstraint,
    RequiredConstraint,
)


class TestFieldDefinition:
    """Tests for FieldDefinition."""

    def test_create_simple_text_field(self) -> None:
        """FieldDefinition should create simple text field."""
        field = FieldDefinition(
            id=FieldDefinitionId("site_location"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.site_location"),
        )
        assert field.id.value == "site_location"
        assert field.field_type == FieldType.TEXT
        assert not field.is_required
        assert not field.is_calculated

    def test_create_required_field(self) -> None:
        """FieldDefinition should create required field."""
        field = FieldDefinition(
            id=FieldDefinitionId("project_name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.project_name"),
            required=True,
        )
        assert field.is_required

    def test_create_field_with_constraints(self) -> None:
        """FieldDefinition should accept constraints."""
        field = FieldDefinition(
            id=FieldDefinitionId("description"),
            field_type=FieldType.TEXTAREA,
            label_key=TranslationKey("field.description"),
            constraints=(
                RequiredConstraint(),
                MinLengthConstraint(min_length=10),
                MaxLengthConstraint(max_length=500),
            ),
        )
        assert len(field.constraints) == 3
        assert isinstance(field.constraints[0], RequiredConstraint)

    def test_create_field_with_help_text(self) -> None:
        """FieldDefinition should accept help text."""
        field = FieldDefinition(
            id=FieldDefinitionId("depth"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.depth"),
            help_text_key=TranslationKey("field.depth.help"),
        )
        assert field.help_text_key is not None
        assert field.help_text_key.key == "field.depth.help"

    def test_create_field_with_default_value(self) -> None:
        """FieldDefinition should accept default value."""
        field = FieldDefinition(
            id=FieldDefinitionId("units"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.units"),
            default_value="meters",
        )
        assert field.default_value == "meters"

    def test_create_dropdown_field_with_options(self) -> None:
        """FieldDefinition should create dropdown with options."""
        field = FieldDefinition(
            id=FieldDefinitionId("soil_type"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.soil_type"),
            options=(
                ("clay", TranslationKey("soil_type.clay")),
                ("sand", TranslationKey("soil_type.sand")),
                ("silt", TranslationKey("soil_type.silt")),
            ),
        )
        assert field.is_choice_field
        assert len(field.options) == 3
        assert field.get_option_values() == ("clay", "sand", "silt")

    def test_create_radio_field_with_options(self) -> None:
        """FieldDefinition should create radio field with options."""
        field = FieldDefinition(
            id=FieldDefinitionId("answer"),
            field_type=FieldType.RADIO,
            label_key=TranslationKey("field.answer"),
            options=(
                ("yes", TranslationKey("option.yes")),
                ("no", TranslationKey("option.no")),
            ),
        )
        assert field.is_choice_field
        assert field.get_option_values() == ("yes", "no")

    def test_get_option_label_key(self) -> None:
        """FieldDefinition should get label key for option."""
        field = FieldDefinition(
            id=FieldDefinitionId("size"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.size"),
            options=(
                ("small", TranslationKey("size.small")),
                ("large", TranslationKey("size.large")),
            ),
        )
        label = field.get_option_label_key("small")
        assert label is not None
        assert label.key == "size.small"

        none_label = field.get_option_label_key("medium")
        assert none_label is None

    def test_create_calculated_field_with_formula(self) -> None:
        """FieldDefinition should create calculated field with formula."""
        field = FieldDefinition(
            id=FieldDefinitionId("total_depth"),
            field_type=FieldType.CALCULATED,
            label_key=TranslationKey("field.total_depth"),
            formula="depth_from + depth_to",
        )
        assert field.is_calculated
        assert field.formula == "depth_from + depth_to"

    def test_create_lookup_field(self) -> None:
        """FieldDefinition should create lookup field."""
        field = FieldDefinition(
            id=FieldDefinitionId("category"),
            field_type=FieldType.LOOKUP,
            label_key=TranslationKey("field.category"),
            lookup_entity_id="category_entity",
            lookup_display_field="name",
        )
        assert field.lookup_entity_id == "category_entity"
        assert field.lookup_display_field == "name"

    def test_create_table_field(self) -> None:
        """FieldDefinition should create table field."""
        field = FieldDefinition(
            id=FieldDefinitionId("boreholes"),
            field_type=FieldType.TABLE,
            label_key=TranslationKey("field.boreholes"),
            child_entity_id="borehole",
        )
        assert field.is_collection_field
        assert field.child_entity_id == "borehole"

    def test_dropdown_with_empty_options_allowed(self) -> None:
        """FieldDefinition should allow dropdown with empty options at creation time.

        Options can be added later via the incremental configuration workflow.
        Validation for non-empty options happens at runtime/export time.
        """
        field = FieldDefinition(
            id=FieldDefinitionId("size"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.size"),
            options=(),
        )
        assert field.field_type == FieldType.DROPDOWN
        assert field.options == ()
        assert field.is_choice_field

    def test_radio_with_empty_options_allowed(self) -> None:
        """FieldDefinition should allow radio with empty options at creation time.

        Options can be added later via the incremental configuration workflow.
        Validation for non-empty options happens at runtime/export time.
        """
        field = FieldDefinition(
            id=FieldDefinitionId("choice"),
            field_type=FieldType.RADIO,
            label_key=TranslationKey("field.choice"),
        )
        assert field.field_type == FieldType.RADIO
        assert field.options == ()
        assert field.is_choice_field

    def test_calculated_without_formula_raises(self) -> None:
        """FieldDefinition should reject calculated without formula."""
        with pytest.raises(ValueError, match="must have a formula"):
            FieldDefinition(
                id=FieldDefinitionId("total"),
                field_type=FieldType.CALCULATED,
                label_key=TranslationKey("field.total"),
            )

    def test_lookup_without_entity_id_raises(self) -> None:
        """FieldDefinition should reject lookup without entity ID."""
        with pytest.raises(ValueError, match="must have lookup_entity_id"):
            FieldDefinition(
                id=FieldDefinitionId("category"),
                field_type=FieldType.LOOKUP,
                label_key=TranslationKey("field.category"),
            )

    def test_table_without_child_entity_id_raises(self) -> None:
        """FieldDefinition should reject table without child entity ID."""
        with pytest.raises(ValueError, match="must have child_entity_id"):
            FieldDefinition(
                id=FieldDefinitionId("items"),
                field_type=FieldType.TABLE,
                label_key=TranslationKey("field.items"),
            )

    def test_constraints_must_be_tuple(self) -> None:
        """FieldDefinition should reject non-tuple constraints."""
        with pytest.raises(ValueError, match="constraints must be a tuple"):
            FieldDefinition(
                id=FieldDefinitionId("field"),
                field_type=FieldType.TEXT,
                label_key=TranslationKey("field.name"),
                constraints=[RequiredConstraint()],  # type: ignore
            )

    def test_constraints_must_be_field_constraint(self) -> None:
        """FieldDefinition should reject non-FieldConstraint items."""
        with pytest.raises(ValueError, match="All constraints must be FieldConstraint"):
            FieldDefinition(
                id=FieldDefinitionId("field"),
                field_type=FieldType.TEXT,
                label_key=TranslationKey("field.name"),
                constraints=("not a constraint",),  # type: ignore
            )

    def test_options_must_be_tuple(self) -> None:
        """FieldDefinition should reject non-tuple options."""
        with pytest.raises(ValueError, match="options must be a tuple"):
            FieldDefinition(
                id=FieldDefinitionId("size"),
                field_type=FieldType.DROPDOWN,
                label_key=TranslationKey("field.size"),
                options=[("small", TranslationKey("size.small"))],  # type: ignore
            )

    def test_option_format_validation(self) -> None:
        """FieldDefinition should validate option format."""
        with pytest.raises(ValueError, match="must be a tuple of"):
            FieldDefinition(
                id=FieldDefinitionId("size"),
                field_type=FieldType.DROPDOWN,
                label_key=TranslationKey("field.size"),
                options=("small",),  # type: ignore - wrong format
            )

    def test_field_definition_immutable(self) -> None:
        """FieldDefinition should be immutable."""
        field = FieldDefinition(
            id=FieldDefinitionId("field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
        )
        with pytest.raises(AttributeError):
            field.required = True  # type: ignore

    def test_field_definition_equality(self) -> None:
        """FieldDefinition should compare by value."""
        field1 = FieldDefinition(
            id=FieldDefinitionId("field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
        )
        field2 = FieldDefinition(
            id=FieldDefinitionId("field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
        )
        assert field1 == field2

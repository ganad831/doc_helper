"""Tests for field value."""

import pytest

from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class TestFieldValue:
    """Tests for FieldValue value object."""

    def test_create_field_value(self) -> None:
        """FieldValue should be created with field_id and value."""
        field_value = FieldValue(
            field_id=FieldDefinitionId("site_location"), value="123 Main Street"
        )
        assert field_value.field_id == FieldDefinitionId("site_location")
        assert field_value.value == "123 Main Street"
        assert field_value.is_computed is False
        assert field_value.computed_from is None
        assert field_value.is_override is False

    def test_create_computed_field_value(self) -> None:
        """FieldValue should support computed values."""
        field_value = FieldValue(
            field_id=FieldDefinitionId("total"),
            value=1500,
            is_computed=True,
            computed_from="a + b",
        )
        assert field_value.value == 1500
        assert field_value.is_computed is True
        assert field_value.computed_from == "a + b"

    def test_create_override_field_value(self) -> None:
        """FieldValue should support override values."""
        field_value = FieldValue(
            field_id=FieldDefinitionId("adjusted_total"),
            value=1600,
            is_computed=False,
            is_override=True,
            original_computed_value=1500,
        )
        assert field_value.value == 1600
        assert field_value.is_override is True
        assert field_value.original_computed_value == 1500

    def test_field_value_is_immutable(self) -> None:
        """FieldValue should be immutable."""
        field_value = FieldValue(field_id=FieldDefinitionId("field1"), value=42)
        with pytest.raises(Exception):  # FrozenInstanceError
            field_value.value = 100  # type: ignore

    def test_field_value_requires_field_definition_id(self) -> None:
        """FieldValue should require FieldDefinitionId."""
        with pytest.raises(TypeError, match="field_id must be a FieldDefinitionId"):
            FieldValue(field_id="invalid", value=42)  # type: ignore

    def test_field_value_requires_bool_is_computed(self) -> None:
        """FieldValue should require bool for is_computed."""
        with pytest.raises(TypeError, match="is_computed must be a bool"):
            FieldValue(
                field_id=FieldDefinitionId("field1"), value=42, is_computed="yes"  # type: ignore
            )

    def test_field_value_requires_bool_is_override(self) -> None:
        """FieldValue should require bool for is_override."""
        with pytest.raises(TypeError, match="is_override must be a bool"):
            FieldValue(
                field_id=FieldDefinitionId("field1"), value=42, is_override="yes"  # type: ignore
            )

    def test_field_value_computed_from_requires_string(self) -> None:
        """FieldValue should require string for computed_from if provided."""
        with pytest.raises(TypeError, match="computed_from must be a string or None"):
            FieldValue(
                field_id=FieldDefinitionId("field1"),
                value=42,
                is_computed=True,
                computed_from=123,  # type: ignore
            )

    def test_field_value_override_requires_original_value(self) -> None:
        """FieldValue override should require original_computed_value."""
        with pytest.raises(
            ValueError, match="original_computed_value must be set when is_override is True"
        ):
            FieldValue(
                field_id=FieldDefinitionId("field1"),
                value=42,
                is_computed=False,
                is_override=True,
                original_computed_value=None,
            )

    def test_is_user_provided(self) -> None:
        """is_user_provided should return True for non-computed values."""
        field_value1 = FieldValue(field_id=FieldDefinitionId("field1"), value=42)
        assert field_value1.is_user_provided is True

        field_value2 = FieldValue(
            field_id=FieldDefinitionId("field2"),
            value=42,
            is_computed=True,
            computed_from="a + b",
        )
        assert field_value2.is_user_provided is False

    def test_has_override(self) -> None:
        """has_override should return True for overridden values."""
        field_value1 = FieldValue(field_id=FieldDefinitionId("field1"), value=42)
        assert field_value1.has_override is False

        field_value2 = FieldValue(
            field_id=FieldDefinitionId("field2"),
            value=100,
            is_override=True,
            original_computed_value=42,
        )
        assert field_value2.has_override is True

    def test_with_value_user_provided(self) -> None:
        """with_value should create new FieldValue with updated value."""
        original = FieldValue(field_id=FieldDefinitionId("field1"), value=42)
        updated = original.with_value(100)

        assert updated.value == 100
        assert updated.field_id == FieldDefinitionId("field1")
        assert updated.is_computed is False
        assert updated.is_override is False
        # Original unchanged (immutable)
        assert original.value == 42

    def test_with_value_computed_creates_override(self) -> None:
        """with_value on computed value should create override."""
        original = FieldValue(
            field_id=FieldDefinitionId("total"),
            value=1500,
            is_computed=True,
            computed_from="a + b",
        )
        updated = original.with_value(1600)

        assert updated.value == 1600
        assert updated.is_computed is False
        assert updated.is_override is True
        assert updated.original_computed_value == 1500
        # Original unchanged
        assert original.value == 1500
        assert original.is_computed is True

    def test_with_computed_value(self) -> None:
        """with_computed_value should create new FieldValue with computed value."""
        original = FieldValue(field_id=FieldDefinitionId("total"), value=0)
        updated = original.with_computed_value(1500, "a + b")

        assert updated.value == 1500
        assert updated.is_computed is True
        assert updated.computed_from == "a + b"
        assert updated.is_override is False
        # Original unchanged
        assert original.value == 0

    def test_with_computed_value_preserves_override(self) -> None:
        """with_computed_value should preserve existing override."""
        original = FieldValue(
            field_id=FieldDefinitionId("total"),
            value=1600,  # Overridden value
            is_override=True,
            original_computed_value=1500,
        )
        updated = original.with_computed_value(1550, "a + b")

        assert updated.value == 1600  # Override preserved
        assert updated.is_override is True
        assert updated.original_computed_value == 1550  # Updated
        assert updated.is_computed is False

    def test_clear_override(self) -> None:
        """clear_override should restore original computed value."""
        original = FieldValue(
            field_id=FieldDefinitionId("total"),
            value=1600,
            is_override=True,
            original_computed_value=1500,
        )
        cleared = original.clear_override()

        assert cleared.value == 1500  # Restored
        assert cleared.is_computed is True
        assert cleared.is_override is False
        assert cleared.original_computed_value is None

    def test_clear_override_on_non_override_raises(self) -> None:
        """clear_override should raise if not an override."""
        field_value = FieldValue(field_id=FieldDefinitionId("field1"), value=42)
        with pytest.raises(
            ValueError, match="Cannot clear override - this value is not an override"
        ):
            field_value.clear_override()

    def test_field_value_allows_any_value_type(self) -> None:
        """FieldValue should allow any value type."""
        # String
        fv1 = FieldValue(field_id=FieldDefinitionId("f1"), value="text")
        assert fv1.value == "text"

        # Number
        fv2 = FieldValue(field_id=FieldDefinitionId("f2"), value=123)
        assert fv2.value == 123

        # Float
        fv3 = FieldValue(field_id=FieldDefinitionId("f3"), value=45.67)
        assert fv3.value == 45.67

        # Boolean
        fv4 = FieldValue(field_id=FieldDefinitionId("f4"), value=True)
        assert fv4.value is True

        # None
        fv5 = FieldValue(field_id=FieldDefinitionId("f5"), value=None)
        assert fv5.value is None

        # List
        fv6 = FieldValue(field_id=FieldDefinitionId("f6"), value=[1, 2, 3])
        assert fv6.value == [1, 2, 3]

    def test_field_value_equality(self) -> None:
        """FieldValue should support equality comparison."""
        fv1 = FieldValue(field_id=FieldDefinitionId("field1"), value=42)
        fv2 = FieldValue(field_id=FieldDefinitionId("field1"), value=42)
        fv3 = FieldValue(field_id=FieldDefinitionId("field1"), value=100)
        fv4 = FieldValue(field_id=FieldDefinitionId("field2"), value=42)

        assert fv1 == fv2
        assert fv1 != fv3
        assert fv1 != fv4

"""Unit tests for OutputMapping value object (Phase F-12.5)."""

import pytest

from doc_helper.domain.schema.output_mapping import OutputMapping


class TestOutputMapping:
    """Unit tests for OutputMapping."""

    # =========================================================================
    # Creation Tests
    # =========================================================================

    def test_create_output_mapping_text(self) -> None:
        """Should create output mapping with TEXT target."""
        mapping = OutputMapping(
            target="TEXT",
            formula_text="{{depth_from}} - {{depth_to}}",
        )
        assert mapping.target == "TEXT"
        assert mapping.formula_text == "{{depth_from}} - {{depth_to}}"

    def test_create_output_mapping_number(self) -> None:
        """Should create output mapping with NUMBER target."""
        mapping = OutputMapping(
            target="NUMBER",
            formula_text="{{area}} * {{density}}",
        )
        assert mapping.target == "NUMBER"
        assert mapping.formula_text == "{{area}} * {{density}}"

    def test_create_output_mapping_boolean(self) -> None:
        """Should create output mapping with BOOLEAN target."""
        mapping = OutputMapping(
            target="BOOLEAN",
            formula_text="{{status}} == 'active'",
        )
        assert mapping.target == "BOOLEAN"
        assert mapping.formula_text == "{{status}} == 'active'"

    # =========================================================================
    # Validation Tests - Target
    # =========================================================================

    def test_reject_empty_target(self) -> None:
        """Should reject empty target."""
        with pytest.raises(ValueError, match="Output mapping target cannot be empty"):
            OutputMapping(
                target="",
                formula_text="{{field1}}",
            )

    def test_reject_whitespace_only_target(self) -> None:
        """Should reject whitespace-only target."""
        with pytest.raises(ValueError, match="Output mapping target cannot be empty"):
            OutputMapping(
                target="   ",
                formula_text="{{field1}}",
            )

    def test_reject_non_string_target(self) -> None:
        """Should reject non-string target."""
        with pytest.raises(ValueError, match="Output mapping target must be a string"):
            OutputMapping(
                target=123,  # type: ignore
                formula_text="{{field1}}",
            )

    def test_reject_none_target(self) -> None:
        """Should reject None target."""
        with pytest.raises(ValueError, match="Output mapping target must be a string"):
            OutputMapping(
                target=None,  # type: ignore
                formula_text="{{field1}}",
            )

    # =========================================================================
    # Validation Tests - Formula Text
    # =========================================================================

    def test_reject_empty_formula_text(self) -> None:
        """Should reject empty formula_text."""
        with pytest.raises(ValueError, match="Output mapping formula_text cannot be empty"):
            OutputMapping(
                target="TEXT",
                formula_text="",
            )

    def test_reject_whitespace_only_formula_text(self) -> None:
        """Should reject whitespace-only formula_text."""
        with pytest.raises(ValueError, match="Output mapping formula_text cannot be empty"):
            OutputMapping(
                target="TEXT",
                formula_text="   ",
            )

    def test_reject_non_string_formula_text(self) -> None:
        """Should reject non-string formula_text."""
        with pytest.raises(ValueError, match="Output mapping formula_text must be a string"):
            OutputMapping(
                target="TEXT",
                formula_text=123,  # type: ignore
            )

    def test_reject_none_formula_text(self) -> None:
        """Should reject None formula_text."""
        with pytest.raises(ValueError, match="Output mapping formula_text must be a string"):
            OutputMapping(
                target="TEXT",
                formula_text=None,  # type: ignore
            )

    # =========================================================================
    # Immutability Tests
    # =========================================================================

    def test_output_mapping_is_frozen(self) -> None:
        """Should be immutable (frozen dataclass)."""
        mapping = OutputMapping(
            target="TEXT",
            formula_text="{{field1}}",
        )
        with pytest.raises(AttributeError):
            mapping.target = "NUMBER"  # type: ignore

    def test_output_mapping_is_frozen_formula(self) -> None:
        """Should not allow modifying formula_text."""
        mapping = OutputMapping(
            target="TEXT",
            formula_text="{{field1}}",
        )
        with pytest.raises(AttributeError):
            mapping.formula_text = "{{field2}}"  # type: ignore

    # =========================================================================
    # Equality Tests
    # =========================================================================

    def test_equality_same_values(self) -> None:
        """Should be equal if target and formula_text match."""
        mapping1 = OutputMapping(
            target="TEXT",
            formula_text="{{field1}}",
        )
        mapping2 = OutputMapping(
            target="TEXT",
            formula_text="{{field1}}",
        )
        assert mapping1 == mapping2

    def test_inequality_different_target(self) -> None:
        """Should not be equal if target differs."""
        mapping1 = OutputMapping(
            target="TEXT",
            formula_text="{{field1}}",
        )
        mapping2 = OutputMapping(
            target="NUMBER",
            formula_text="{{field1}}",
        )
        assert mapping1 != mapping2

    def test_inequality_different_formula(self) -> None:
        """Should not be equal if formula_text differs."""
        mapping1 = OutputMapping(
            target="TEXT",
            formula_text="{{field1}}",
        )
        mapping2 = OutputMapping(
            target="TEXT",
            formula_text="{{field2}}",
        )
        assert mapping1 != mapping2

    def test_inequality_different_both(self) -> None:
        """Should not be equal if both fields differ."""
        mapping1 = OutputMapping(
            target="TEXT",
            formula_text="{{field1}}",
        )
        mapping2 = OutputMapping(
            target="NUMBER",
            formula_text="{{field2}}",
        )
        assert mapping1 != mapping2

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_target_case_preserved(self) -> None:
        """Should preserve target case (validation is case-sensitive in import layer)."""
        mapping = OutputMapping(
            target="text",  # lowercase
            formula_text="{{field1}}",
        )
        assert mapping.target == "text"

    def test_formula_text_with_special_chars(self) -> None:
        """Should accept formula_text with special characters."""
        mapping = OutputMapping(
            target="TEXT",
            formula_text="{{field1}} + {{field2}} * 100 / {{field3}}",
        )
        assert mapping.formula_text == "{{field1}} + {{field2}} * 100 / {{field3}}"

    def test_formula_text_with_string_literals(self) -> None:
        """Should accept formula_text with string literals."""
        mapping = OutputMapping(
            target="BOOLEAN",
            formula_text="{{status}} == 'completed' or {{status}} == 'done'",
        )
        assert mapping.formula_text == "{{status}} == 'completed' or {{status}} == 'done'"

    def test_formula_text_multiline(self) -> None:
        """Should accept multiline formula_text (though not recommended)."""
        formula = """{{field1}} +
        {{field2}}"""
        mapping = OutputMapping(
            target="NUMBER",
            formula_text=formula,
        )
        assert mapping.formula_text == formula

    # =========================================================================
    # Hashability Tests (for use in sets/dicts)
    # =========================================================================

    def test_output_mapping_hashable(self) -> None:
        """Should be hashable (can be used in sets)."""
        mapping1 = OutputMapping(
            target="TEXT",
            formula_text="{{field1}}",
        )
        mapping2 = OutputMapping(
            target="NUMBER",
            formula_text="{{field2}}",
        )
        mapping_set = {mapping1, mapping2, mapping1}
        assert len(mapping_set) == 2

    def test_output_mapping_dict_key(self) -> None:
        """Should work as dictionary key."""
        mapping = OutputMapping(
            target="TEXT",
            formula_text="{{field1}}",
        )
        data = {mapping: "test_value"}
        assert data[mapping] == "test_value"

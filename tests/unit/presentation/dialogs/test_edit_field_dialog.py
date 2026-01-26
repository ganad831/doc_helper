"""Unit tests for EditFieldDialog (Phase SD-4).

Tests the edit field dialog, specifically LOOKUP field configuration
which was fixed in hotfix A1.1-1.
"""

import pytest
from unittest.mock import Mock

from doc_helper.presentation.dialogs.edit_field_dialog import EditFieldDialog


class TestEditFieldDialogLookupSection:
    """Tests for LOOKUP field handling in EditFieldDialog.

    Regression tests for A1.1-1: EditFieldDialog must show LOOKUP configuration
    when field_type is "lookup" (case-insensitive).
    """

    @pytest.fixture
    def sample_entities(self):
        """Create sample available entities for testing."""
        return (
            ("entity_a", "Entity A"),
            ("entity_b", "Entity B"),
            ("entity_c", "Entity C"),
        )

    def test_lookup_section_shown_for_lookup_type_lowercase(
        self, qtbot, sample_entities
    ):
        """LOOKUP section should be shown when field_type is 'lookup' (lowercase).

        This is the regression test for A1.1-1 where the LOOKUP section was not
        shown because of case mismatch (dialog compared against uppercase 'LOOKUP'
        but received lowercase 'lookup' from FieldType enum).
        """
        dialog = EditFieldDialog(
            entity_id="test_entity",
            field_id="lookup_field",
            field_type="lookup",  # Lowercase - as received from FieldType enum
            current_label_key="field.lookup",
            current_help_text_key=None,
            current_required=False,
            current_default_value=None,
            current_lookup_entity_id="entity_b",
            current_lookup_display_field="name",
            available_entities=sample_entities,
            parent=None,
        )
        qtbot.addWidget(dialog)

        # LOOKUP section should be created
        assert dialog._lookup_entity_combo is not None
        assert dialog._lookup_display_field_combo is not None

    def test_lookup_section_shown_for_lookup_type_uppercase(
        self, qtbot, sample_entities
    ):
        """LOOKUP section should be shown when field_type is 'LOOKUP' (uppercase)."""
        dialog = EditFieldDialog(
            entity_id="test_entity",
            field_id="lookup_field",
            field_type="LOOKUP",  # Uppercase
            current_label_key="field.lookup",
            current_help_text_key=None,
            current_required=False,
            current_default_value=None,
            current_lookup_entity_id="entity_b",
            current_lookup_display_field="name",
            available_entities=sample_entities,
            parent=None,
        )
        qtbot.addWidget(dialog)

        # LOOKUP section should be created
        assert dialog._lookup_entity_combo is not None
        assert dialog._lookup_display_field_combo is not None

    def test_lookup_entity_combo_populated_with_available_entities(
        self, qtbot, sample_entities
    ):
        """Lookup entity combo should be populated with all available entities."""
        dialog = EditFieldDialog(
            entity_id="test_entity",
            field_id="lookup_field",
            field_type="lookup",
            current_label_key="field.lookup",
            current_help_text_key=None,
            current_required=False,
            current_default_value=None,
            available_entities=sample_entities,
            parent=None,
        )
        qtbot.addWidget(dialog)

        # Combo should have (None) + all entities
        assert dialog._lookup_entity_combo.count() == len(sample_entities) + 1

        # First item should be (None)
        assert dialog._lookup_entity_combo.itemText(0) == "(None)"
        assert dialog._lookup_entity_combo.itemData(0) == ""

        # Remaining items should be entities
        for i, (entity_id, entity_name) in enumerate(sample_entities):
            expected_text = f"{entity_name} ({entity_id})"
            assert dialog._lookup_entity_combo.itemText(i + 1) == expected_text
            assert dialog._lookup_entity_combo.itemData(i + 1) == entity_id

    def test_current_lookup_entity_preselected(self, qtbot, sample_entities):
        """Current lookup_entity_id should be pre-selected in combo box."""
        dialog = EditFieldDialog(
            entity_id="test_entity",
            field_id="lookup_field",
            field_type="lookup",
            current_label_key="field.lookup",
            current_help_text_key=None,
            current_required=False,
            current_default_value=None,
            current_lookup_entity_id="entity_b",  # Pre-select entity_b
            available_entities=sample_entities,
            parent=None,
        )
        qtbot.addWidget(dialog)

        # entity_b should be selected
        assert dialog._lookup_entity_combo.currentData() == "entity_b"

    def test_current_lookup_display_field_prefilled(self, qtbot, sample_entities):
        """Current lookup_display_field should be pre-filled when callback provides valid fields."""
        # Mock callback that returns valid display fields for entity_b
        def mock_get_valid_display_fields(entity_id: str):
            if entity_id == "entity_b":
                return (("display_name", "Display Name"), ("other_field", "Other Field"))
            return ()

        dialog = EditFieldDialog(
            entity_id="test_entity",
            field_id="lookup_field",
            field_type="lookup",
            current_label_key="field.lookup",
            current_help_text_key=None,
            current_required=False,
            current_default_value=None,
            current_lookup_entity_id="entity_b",
            current_lookup_display_field="display_name",  # Pre-fill display field
            available_entities=sample_entities,
            get_valid_display_fields=mock_get_valid_display_fields,
            parent=None,
        )
        qtbot.addWidget(dialog)

        # display_name should be selected in the combo
        assert dialog._lookup_display_field_combo.currentData() == "display_name"

    def test_no_lookup_section_for_text_field(self, qtbot, sample_entities):
        """LOOKUP section should NOT be created for TEXT fields."""
        dialog = EditFieldDialog(
            entity_id="test_entity",
            field_id="text_field",
            field_type="text",
            current_label_key="field.text",
            current_help_text_key=None,
            current_required=False,
            current_default_value=None,
            available_entities=sample_entities,
            parent=None,
        )
        qtbot.addWidget(dialog)

        # LOOKUP section should NOT be created
        assert dialog._lookup_entity_combo is None
        assert dialog._lookup_display_field_combo is None

    def test_no_lookup_section_for_calculated_field(self, qtbot, sample_entities):
        """LOOKUP section should NOT be created for CALCULATED fields."""
        dialog = EditFieldDialog(
            entity_id="test_entity",
            field_id="calc_field",
            field_type="calculated",
            current_label_key="field.calc",
            current_help_text_key=None,
            current_required=False,
            current_default_value=None,
            available_entities=sample_entities,
            parent=None,
        )
        qtbot.addWidget(dialog)

        # LOOKUP section should NOT be created
        assert dialog._lookup_entity_combo is None
        assert dialog._lookup_display_field_combo is None

        # But FORMULA section should be created
        assert dialog._formula_input is not None


class TestEditFieldDialogFieldTypeNormalization:
    """Tests for field type case normalization in EditFieldDialog.

    Verifies that field_type is normalized to lowercase internally
    (via normalize_field_type which uses FieldType.value).
    """

    def test_field_type_normalized_to_lowercase(self, qtbot):
        """Field type should be normalized to lowercase internally."""
        dialog = EditFieldDialog(
            entity_id="test_entity",
            field_id="test_field",
            field_type="TEXT",  # Uppercase input
            current_label_key="field.test",
            current_help_text_key=None,
            current_required=False,
            current_default_value=None,
            parent=None,
        )
        qtbot.addWidget(dialog)

        # Internal field_type should be lowercase (normalized via FieldType.value)
        assert dialog._field_type == "text"

    def test_field_type_mixed_case_normalized(self, qtbot):
        """Field type should be normalized even with mixed case."""
        dialog = EditFieldDialog(
            entity_id="test_entity",
            field_id="test_field",
            field_type="Lookup",  # Mixed case input
            current_label_key="field.test",
            current_help_text_key=None,
            current_required=False,
            current_default_value=None,
            parent=None,
        )
        qtbot.addWidget(dialog)

        # Internal field_type should be lowercase (normalized via FieldType.value)
        assert dialog._field_type == "lookup"

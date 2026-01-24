"""Tests for Control Rule Dialog (Phase F-12).

Tests the UI-only control rule add/edit dialog.
Verifies dialog modes, getter methods, and field selection.

PHASE F-12 COMPLIANCE:
- UI-only tests
- NO business logic validation
- NO formula execution
- NO schema mutation
"""

import pytest
from PyQt6.QtWidgets import QApplication

from doc_helper.application.dto.control_rule_dto import ControlRuleType
from doc_helper.application.dto.export_dto import ControlRuleExportDTO
from doc_helper.application.dto.schema_dto import FieldDefinitionDTO
from doc_helper.presentation.dialogs.control_rule_dialog import ControlRuleDialog


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def available_fields() -> tuple[FieldDefinitionDTO, ...]:
    """Create sample available fields for testing."""
    return (
        FieldDefinitionDTO(
            id="field1",
            label="Field 1",
            field_type="TEXT",
            required=False,
            default_value=None,
            help_text=None,
            options=(),
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            child_entity_id=None,
            formula=None,
        ),
        FieldDefinitionDTO(
            id="field2",
            label="Field 2",
            field_type="NUMBER",
            required=True,
            default_value=None,
            help_text=None,
            options=(),
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            child_entity_id=None,
            formula=None,
        ),
        FieldDefinitionDTO(
            id="status",
            label="Status",
            field_type="DROPDOWN",
            required=False,
            default_value=None,
            help_text=None,
            options=(),
            is_calculated=False,
            is_choice_field=True,
            is_collection_field=False,
            lookup_entity_id=None,
            child_entity_id=None,
            formula=None,
        ),
    )


class TestControlRuleDialogAddMode:
    """Tests for ControlRuleDialog in Add mode (Phase F-12)."""

    def test_add_mode_initialization(
        self, qapp, available_fields: tuple[FieldDefinitionDTO, ...]
    ) -> None:
        """Dialog should initialize in add mode when no existing_rule provided."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=None,
        )

        assert dialog.windowTitle() == "Add Control Rule"
        assert not dialog._is_edit_mode

    def test_add_mode_rule_type_editable(
        self, qapp, available_fields: tuple[FieldDefinitionDTO, ...]
    ) -> None:
        """Rule type combo should be editable in add mode."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=None,
        )

        assert dialog._rule_type_combo is not None
        assert dialog._rule_type_combo.isEnabled()

    def test_add_mode_target_field_selectable(
        self, qapp, available_fields: tuple[FieldDefinitionDTO, ...]
    ) -> None:
        """Target field combo should exist and be populated in add mode."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=None,
        )

        assert dialog._target_field_combo is not None
        assert dialog._target_field_combo.count() == len(available_fields)
        # Check first item
        assert dialog._target_field_combo.itemText(0) == "field1 (Field 1)"
        assert dialog._target_field_combo.itemData(0) == "field1"

    def test_add_mode_default_values(
        self, qapp, available_fields: tuple[FieldDefinitionDTO, ...]
    ) -> None:
        """Dialog should return default values in add mode."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=None,
        )

        # Default rule type should be VISIBILITY
        assert dialog.get_rule_type() == ControlRuleType.VISIBILITY.value

        # Default target field should be first field
        assert dialog.get_target_field_id() == "field1"

        # Default formula should be empty
        assert dialog.get_formula_text() == ""


class TestControlRuleDialogEditMode:
    """Tests for ControlRuleDialog in Edit mode (Phase F-12)."""

    @pytest.fixture
    def existing_rule(self) -> ControlRuleExportDTO:
        """Create sample existing rule for edit mode."""
        return ControlRuleExportDTO(
            rule_type="ENABLED",
            target_field_id="field2",
            formula_text="{{status}} == 'active'",
        )

    def test_edit_mode_initialization(
        self,
        qapp,
        available_fields: tuple[FieldDefinitionDTO, ...],
        existing_rule: ControlRuleExportDTO,
    ) -> None:
        """Dialog should initialize in edit mode when existing_rule provided."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=existing_rule,
        )

        assert dialog.windowTitle() == "Edit Control Rule"
        assert dialog._is_edit_mode

    def test_edit_mode_rule_type_locked(
        self,
        qapp,
        available_fields: tuple[FieldDefinitionDTO, ...],
        existing_rule: ControlRuleExportDTO,
    ) -> None:
        """Rule type combo should be disabled in edit mode."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=existing_rule,
        )

        assert dialog._rule_type_combo is not None
        assert not dialog._rule_type_combo.isEnabled()
        assert dialog.get_rule_type() == "ENABLED"

    def test_edit_mode_target_field_readonly(
        self,
        qapp,
        available_fields: tuple[FieldDefinitionDTO, ...],
        existing_rule: ControlRuleExportDTO,
    ) -> None:
        """Target field should be displayed as read-only label in edit mode."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=existing_rule,
        )

        # Target field combo should not exist in edit mode
        assert dialog._target_field_combo is None
        # Getter should return existing rule's target field
        assert dialog.get_target_field_id() == "field2"

    def test_edit_mode_formula_prefilled(
        self,
        qapp,
        available_fields: tuple[FieldDefinitionDTO, ...],
        existing_rule: ControlRuleExportDTO,
    ) -> None:
        """Formula text should be pre-filled with existing formula in edit mode."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=existing_rule,
        )

        assert dialog.get_formula_text() == "{{status}} == 'active'"


class TestControlRuleDialogGetters:
    """Tests for ControlRuleDialog getter methods (Phase F-12)."""

    def test_get_rule_type_returns_current_selection(
        self, qapp, available_fields: tuple[FieldDefinitionDTO, ...]
    ) -> None:
        """get_rule_type should return currently selected rule type."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=None,
        )

        # Change selection to REQUIRED
        dialog._rule_type_combo.setCurrentIndex(2)  # REQUIRED is index 2
        assert dialog.get_rule_type() == ControlRuleType.REQUIRED.value

    def test_get_target_field_id_returns_current_selection(
        self, qapp, available_fields: tuple[FieldDefinitionDTO, ...]
    ) -> None:
        """get_target_field_id should return currently selected field."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=None,
        )

        # Change selection to field2
        dialog._target_field_combo.setCurrentIndex(1)
        assert dialog.get_target_field_id() == "field2"

    def test_get_formula_text_returns_edited_text(
        self, qapp, available_fields: tuple[FieldDefinitionDTO, ...]
    ) -> None:
        """get_formula_text should return user-entered formula text."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=None,
        )

        # Enter formula text
        test_formula = "{{field1}} == 'test' AND {{field2}} > 0"
        dialog._formula_edit.setPlainText(test_formula)

        assert dialog.get_formula_text() == test_formula

    def test_get_formula_text_strips_whitespace(
        self, qapp, available_fields: tuple[FieldDefinitionDTO, ...]
    ) -> None:
        """get_formula_text should strip leading/trailing whitespace."""
        dialog = ControlRuleDialog(
            available_fields=available_fields,
            parent=None,
            existing_rule=None,
        )

        # Enter formula with whitespace
        dialog._formula_edit.setPlainText("  {{status}} == 'active'  \n")

        assert dialog.get_formula_text() == "{{status}} == 'active'"

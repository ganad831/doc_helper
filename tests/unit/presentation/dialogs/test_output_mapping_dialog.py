"""Tests for Output Mapping Dialog (Phase F-13).

Tests the UI-only output mapping add/edit dialog.
Verifies dialog modes, getter methods, and target type selection.

PHASE F-13 COMPLIANCE:
- UI-only tests
- NO business logic validation
- NO formula execution or preview
- NO schema mutation
"""

import pytest
from PyQt6.QtWidgets import QApplication

from doc_helper.application.dto.export_dto import OutputMappingExportDTO
from doc_helper.presentation.dialogs.output_mapping_dialog import OutputMappingDialog


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestOutputMappingDialogAddMode:
    """Tests for OutputMappingDialog in Add mode (Phase F-13)."""

    def test_add_mode_initialization(self, qapp) -> None:
        """Dialog should initialize in add mode when no existing_mapping provided."""
        dialog = OutputMappingDialog(parent=None, existing_mapping=None)

        assert dialog.windowTitle() == "Add Output Mapping"
        assert not dialog._is_edit_mode

    def test_add_mode_target_editable(self, qapp) -> None:
        """Target type combo should be editable in add mode."""
        dialog = OutputMappingDialog(parent=None, existing_mapping=None)

        assert dialog._target_combo is not None
        assert dialog._target_combo.isEnabled()

    def test_add_mode_target_types_available(self, qapp) -> None:
        """Target type combo should contain TEXT, NUMBER, BOOLEAN."""
        dialog = OutputMappingDialog(parent=None, existing_mapping=None)

        assert dialog._target_combo is not None
        assert dialog._target_combo.count() == 3
        assert dialog._target_combo.itemText(0) == "TEXT"
        assert dialog._target_combo.itemText(1) == "NUMBER"
        assert dialog._target_combo.itemText(2) == "BOOLEAN"

    def test_add_mode_default_values(self, qapp) -> None:
        """Dialog should return default values in add mode."""
        dialog = OutputMappingDialog(parent=None, existing_mapping=None)

        # Default target should be TEXT
        assert dialog.get_target() == "TEXT"

        # Default formula should be empty
        assert dialog.get_formula_text() == ""


class TestOutputMappingDialogEditMode:
    """Tests for OutputMappingDialog in Edit mode (Phase F-13)."""

    @pytest.fixture
    def existing_mapping(self) -> OutputMappingExportDTO:
        """Create sample existing mapping for edit mode."""
        return OutputMappingExportDTO(
            target="NUMBER",
            formula_text="{{depth_from}} - {{depth_to}}",
        )

    def test_edit_mode_initialization(
        self, qapp, existing_mapping: OutputMappingExportDTO
    ) -> None:
        """Dialog should initialize in edit mode when existing_mapping provided."""
        dialog = OutputMappingDialog(parent=None, existing_mapping=existing_mapping)

        assert dialog.windowTitle() == "Edit Output Mapping"
        assert dialog._is_edit_mode

    def test_edit_mode_target_readonly(
        self, qapp, existing_mapping: OutputMappingExportDTO
    ) -> None:
        """Target type should be displayed as read-only label in edit mode."""
        dialog = OutputMappingDialog(parent=None, existing_mapping=existing_mapping)

        # Target combo should not exist in edit mode
        # (target is shown as read-only label instead)
        # Getter should return existing mapping's target
        assert dialog.get_target() == "NUMBER"

    def test_edit_mode_formula_prefilled(
        self, qapp, existing_mapping: OutputMappingExportDTO
    ) -> None:
        """Formula text should be pre-filled with existing formula in edit mode."""
        dialog = OutputMappingDialog(parent=None, existing_mapping=existing_mapping)

        assert dialog.get_formula_text() == "{{depth_from}} - {{depth_to}}"


class TestOutputMappingDialogGetters:
    """Tests for OutputMappingDialog getter methods (Phase F-13)."""

    def test_get_target_returns_current_selection(self, qapp) -> None:
        """get_target should return currently selected target type."""
        dialog = OutputMappingDialog(parent=None, existing_mapping=None)

        # Change selection to BOOLEAN
        dialog._target_combo.setCurrentIndex(2)  # BOOLEAN is index 2
        assert dialog.get_target() == "BOOLEAN"

    def test_get_formula_text_returns_edited_text(self, qapp) -> None:
        """get_formula_text should return user-entered formula text."""
        dialog = OutputMappingDialog(parent=None, existing_mapping=None)

        # Enter formula text
        test_formula = "{{area}} * {{density}}"
        dialog._formula_edit.setPlainText(test_formula)

        assert dialog.get_formula_text() == test_formula

    def test_get_formula_text_strips_whitespace(self, qapp) -> None:
        """get_formula_text should strip leading/trailing whitespace."""
        dialog = OutputMappingDialog(parent=None, existing_mapping=None)

        # Enter formula with whitespace
        dialog._formula_edit.setPlainText("  {{depth_from}} - {{depth_to}}  \n")

        assert dialog.get_formula_text() == "{{depth_from}} - {{depth_to}}"

    def test_get_target_in_edit_mode(self, qapp) -> None:
        """get_target should return existing mapping's target in edit mode."""
        existing_mapping = OutputMappingExportDTO(
            target="BOOLEAN",
            formula_text="{{status}} == 'active'",
        )
        dialog = OutputMappingDialog(parent=None, existing_mapping=existing_mapping)

        # In edit mode, target comes from existing mapping
        assert dialog.get_target() == "BOOLEAN"

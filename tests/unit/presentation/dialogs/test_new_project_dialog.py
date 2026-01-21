"""Unit tests for NewProjectDialog (v2 Phase 4).

Tests AppType selection UI for project creation.
"""

import pytest
from unittest.mock import Mock
from PyQt6.QtWidgets import QDialog

from doc_helper.application.dto import AppTypeDTO
from doc_helper.presentation.dialogs.new_project_dialog import NewProjectDialog


@pytest.fixture
def sample_app_types():
    """Create sample AppType DTOs for testing."""
    return [
        AppTypeDTO(
            app_type_id="soil_investigation",
            name="Soil Investigation",
            version="1.0.0",
            description="Soil investigation reports and geotechnical analysis",
        ),
        AppTypeDTO(
            app_type_id="structural_report",
            name="Structural Report",
            version="1.0.0",
            description="Structural engineering reports and calculations",
        ),
        AppTypeDTO(
            app_type_id="environmental_assessment",
            name="Environmental Assessment",
            version="1.0.0",
            description="Environmental impact assessments and compliance reports",
        ),
    ]


class TestNewProjectDialog:
    """Test NewProjectDialog initialization and behavior."""

    def test_initialization(self, qtbot, sample_app_types):
        """Test: Dialog initializes with available AppTypes."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Create New Project"
        assert dialog._available_app_types == sample_app_types

    def test_app_type_combo_populated(self, qtbot, sample_app_types):
        """Test: AppType combo box is populated with all available AppTypes."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Verify combo box has correct number of items
        assert dialog._app_type_combo.count() == len(sample_app_types)

        # Verify each AppType is present (text includes version)
        for i, app_type in enumerate(sample_app_types):
            expected_text = f"{app_type.name} (v{app_type.version})"
            assert dialog._app_type_combo.itemText(i) == expected_text
            assert dialog._app_type_combo.itemData(i) == app_type.app_type_id

    def test_first_app_type_selected_by_default(self, qtbot, sample_app_types):
        """Test: First AppType is selected by default."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        assert dialog._app_type_combo.currentIndex() == 0
        assert dialog._app_type_combo.currentData() == sample_app_types[0].app_type_id

    def test_app_type_description_displayed(self, qtbot, sample_app_types):
        """Test: AppType description is displayed for selected AppType."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # First AppType should be selected by default
        assert (
            dialog._app_type_description_label.text()
            == sample_app_types[0].description
        )

    def test_app_type_selection_updates_description(self, qtbot, sample_app_types):
        """Test: Selecting different AppType updates description."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Change selection to second AppType
        dialog._app_type_combo.setCurrentIndex(1)

        # Verify description updated
        assert (
            dialog._app_type_description_label.text()
            == sample_app_types[1].description
        )

        # Change to third AppType
        dialog._app_type_combo.setCurrentIndex(2)

        # Verify description updated again
        assert (
            dialog._app_type_description_label.text()
            == sample_app_types[2].description
        )

    def test_get_project_name(self, qtbot, sample_app_types):
        """Test: get_project_name() returns entered name."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Set project name
        dialog._name_edit.setText("Test Project Name")

        # Verify getter returns correct value
        assert dialog.get_project_name() == "Test Project Name"

    def test_get_project_name_strips_whitespace(self, qtbot, sample_app_types):
        """Test: get_project_name() strips leading/trailing whitespace."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Set project name with whitespace
        dialog._name_edit.setText("  Test Project  ")

        # Verify whitespace is stripped
        assert dialog.get_project_name() == "Test Project"

    def test_get_selected_app_type_id(self, qtbot, sample_app_types):
        """Test: get_selected_app_type_id() returns selected AppType ID."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Default selection (first item)
        assert dialog.get_selected_app_type_id() == sample_app_types[0].app_type_id

        # Change selection
        dialog._app_type_combo.setCurrentIndex(1)
        assert dialog.get_selected_app_type_id() == sample_app_types[1].app_type_id

        dialog._app_type_combo.setCurrentIndex(2)
        assert dialog.get_selected_app_type_id() == sample_app_types[2].app_type_id

    def test_get_description(self, qtbot, sample_app_types):
        """Test: get_description() returns entered description."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Set description
        dialog._description_edit.setPlainText("This is a test project description.")

        # Verify getter returns correct value
        assert dialog.get_description() == "This is a test project description."

    def test_get_description_strips_whitespace(self, qtbot, sample_app_types):
        """Test: get_description() strips leading/trailing whitespace."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Set description with whitespace
        dialog._description_edit.setPlainText("  Test description  ")

        # Verify whitespace is stripped
        assert dialog.get_description() == "Test description"

    def test_get_description_returns_none_for_empty(self, qtbot, sample_app_types):
        """Test: get_description() returns None for empty description."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Leave description empty
        assert dialog.get_description() is None

        # Set to whitespace only
        dialog._description_edit.setPlainText("   ")
        assert dialog.get_description() is None

    def test_validation_requires_project_name(self, qtbot, sample_app_types):
        """Test: Validation requires project name to be entered."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Leave name empty, try to accept
        dialog._name_edit.setText("")
        dialog._validate_and_accept()

        # Dialog should still be open (not accepted)
        assert dialog.result() != QDialog.DialogCode.Accepted

    def test_validation_requires_app_type_selection(self, qtbot, sample_app_types):
        """Test: Validation requires AppType to be selected."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Set name but clear AppType selection
        dialog._name_edit.setText("Test Project")
        dialog._app_type_combo.setCurrentIndex(-1)

        dialog._validate_and_accept()

        # Dialog should still be open (not accepted)
        assert dialog.result() != QDialog.DialogCode.Accepted

    def test_validation_passes_with_required_fields(self, qtbot, sample_app_types):
        """Test: Validation passes when required fields are filled."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Set required fields
        dialog._name_edit.setText("Test Project")
        dialog._app_type_combo.setCurrentIndex(0)

        # Call validation method (simulates OK button click)
        dialog._validate_and_accept()

        # Dialog should be accepted
        assert dialog.result() == QDialog.DialogCode.Accepted

    def test_cancel_button_rejects_dialog(self, qtbot, sample_app_types):
        """Test: Cancel button rejects dialog."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Click cancel button
        dialog.reject()

        # Dialog should be rejected
        assert dialog.result() == QDialog.DialogCode.Rejected

    def test_empty_app_types_list(self, qtbot):
        """Test: Dialog handles empty AppTypes list gracefully."""
        dialog = NewProjectDialog(None, [])
        qtbot.addWidget(dialog)

        # Combo box should have placeholder item
        assert dialog._app_type_combo.count() == 1
        assert dialog._app_type_combo.itemText(0) == "No AppTypes available"
        assert dialog._app_type_combo.isEnabled() is False

        # get_selected_app_type_id should return None
        assert dialog.get_selected_app_type_id() is None

    def test_single_app_type(self, qtbot):
        """Test: Dialog works with single AppType."""
        single_app_type = [
            AppTypeDTO(
                app_type_id="soil_investigation",
                name="Soil Investigation",
                version="1.0.0",
                description="Soil investigation reports",
            )
        ]

        dialog = NewProjectDialog(None, single_app_type)
        qtbot.addWidget(dialog)

        assert dialog._app_type_combo.count() == 1
        assert dialog.get_selected_app_type_id() == "soil_investigation"
        assert (
            dialog._app_type_description_label.text()
            == "Soil investigation reports"
        )

    def test_dialog_does_not_modify_app_type_list(self, qtbot, sample_app_types):
        """Test: Dialog does not modify the input AppType list."""
        original_count = len(sample_app_types)
        original_first = sample_app_types[0]

        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Interact with dialog
        dialog._app_type_combo.setCurrentIndex(1)
        dialog._name_edit.setText("Test")

        # Verify original list unchanged
        assert len(sample_app_types) == original_count
        assert sample_app_types[0] == original_first

    def test_description_field_is_optional(self, qtbot, sample_app_types):
        """Test: Description field is optional for validation."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        # Set only required fields (name + app_type_id)
        dialog._name_edit.setText("Test Project")
        dialog._app_type_combo.setCurrentIndex(0)
        # Leave description empty

        dialog._validate_and_accept()

        # Should still accept
        assert dialog.result() == QDialog.DialogCode.Accepted
        assert dialog.get_description() is None

    def test_long_app_type_description(self, qtbot):
        """Test: Dialog handles long AppType descriptions."""
        long_description = "This is a very long description " * 20
        app_types = [
            AppTypeDTO(
                app_type_id="test",
                name="Test",
                version="1.0.0",
                description=long_description,
            )
        ]

        dialog = NewProjectDialog(None, app_types)
        qtbot.addWidget(dialog)

        # Should display full description without errors
        assert dialog._app_type_description_label.text() == long_description

    def test_special_characters_in_project_name(self, qtbot, sample_app_types):
        """Test: Dialog accepts special characters in project name."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        special_name = "Project #1 - Test (2024) & More!"
        dialog._name_edit.setText(special_name)
        dialog._app_type_combo.setCurrentIndex(0)

        dialog._validate_and_accept()

        assert dialog.result() == QDialog.DialogCode.Accepted
        assert dialog.get_project_name() == special_name

    def test_multiline_description(self, qtbot, sample_app_types):
        """Test: Dialog handles multiline descriptions."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        multiline_desc = "Line 1\nLine 2\nLine 3"
        dialog._description_edit.setPlainText(multiline_desc)

        assert dialog.get_description() == multiline_desc

    def test_app_type_order_preserved(self, qtbot, sample_app_types):
        """Test: AppTypes appear in combo box in same order as input list."""
        dialog = NewProjectDialog(None, sample_app_types)
        qtbot.addWidget(dialog)

        for i, app_type in enumerate(sample_app_types):
            expected_text = f"{app_type.name} (v{app_type.version})"
            assert dialog._app_type_combo.itemText(i) == expected_text
            assert dialog._app_type_combo.itemData(i) == app_type.app_type_id

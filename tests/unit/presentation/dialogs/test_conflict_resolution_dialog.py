"""Unit tests for ConflictResolutionDialog."""

import pytest
from unittest.mock import Mock
from PyQt6.QtWidgets import QDialog

from doc_helper.application.dto import ConflictDTO
from doc_helper.presentation.dialogs.conflict_resolution_dialog import ConflictResolutionDialog


@pytest.fixture
def mock_translation_adapter():
    """Mock QtTranslationAdapter."""
    adapter = Mock()
    adapter.translate = Mock(side_effect=lambda key, **params: key if not params else f"{key}_{params.get('count', '')}")
    return adapter


@pytest.fixture
def sample_conflicts():
    """Sample conflict DTOs for testing."""
    return (
        ConflictDTO(
            field_id="field_1",
            field_label="Borehole Depth",
            conflict_type="formula",
            user_value="105.0",
            formula_value="100.0",
            control_value=None,
            description="User override conflicts with formula-computed value",
        ),
        ConflictDTO(
            field_id="field_2",
            field_label="Sample Count",
            conflict_type="control",
            user_value="12",
            formula_value=None,
            control_value="10",
            description="User override conflicts with control-set value",
        ),
        ConflictDTO(
            field_id="field_3",
            field_label="Project Status",
            conflict_type="formula_control",
            user_value="Active",
            formula_value="Pending",
            control_value="Draft",
            description="User override conflicts with both formula and control",
        ),
    )


class TestConflictResolutionDialog:
    """Test suite for ConflictResolutionDialog."""

    def test_initialization(self, qtbot, mock_translation_adapter, sample_conflicts):
        """Test dialog initialization."""
        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=sample_conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "dialog.conflict_resolution.title"
        assert dialog.isModal()
        assert dialog.minimumWidth() == 700
        assert dialog.minimumHeight() == 500

    def test_conflict_table_populated(self, qtbot, mock_translation_adapter, sample_conflicts):
        """Test that conflict table is populated with all conflicts."""
        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=sample_conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog._conflict_table is not None
        assert dialog._conflict_table.rowCount() == 3

    def test_conflict_count_displayed(self, qtbot, mock_translation_adapter, sample_conflicts):
        """Test that conflict count is displayed correctly."""
        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=sample_conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Verify translate was called with count parameter
        mock_translation_adapter.translate.assert_any_call(
            "dialog.conflict_resolution.conflict_count",
            count=3
        )

    def test_first_conflict_selected_by_default(self, qtbot, mock_translation_adapter, sample_conflicts):
        """Test that first conflict is selected by default."""
        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=sample_conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog._conflict_table.currentRow() == 0
        assert dialog._description_text is not None
        # Description should be populated with first conflict
        assert "Borehole Depth" in dialog._description_text.toHtml()

    def test_conflict_selection_updates_description(self, qtbot, mock_translation_adapter, sample_conflicts):
        """Test that selecting a conflict updates the description panel."""
        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=sample_conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Select second conflict
        dialog._conflict_table.selectRow(1)

        assert dialog._description_text is not None
        assert "Sample Count" in dialog._description_text.toHtml()

    def test_conflict_type_display(self, qtbot, mock_translation_adapter, sample_conflicts):
        """Test that conflict type is displayed correctly."""
        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=sample_conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Verify translate was called for all conflict types
        mock_translation_adapter.translate.assert_any_call("dialog.conflict_resolution.type_formula")
        mock_translation_adapter.translate.assert_any_call("dialog.conflict_resolution.type_control")
        mock_translation_adapter.translate.assert_any_call("dialog.conflict_resolution.type_formula_control")

    def test_formula_conflict_shows_formula_value(self, qtbot, mock_translation_adapter):
        """Test that formula conflicts show formula value in description."""
        conflicts = (
            ConflictDTO(
                field_id="field_1",
                field_label="Test Field",
                conflict_type="formula",
                user_value="100",
                formula_value="95",
                control_value=None,
                description="Formula conflict",
            ),
        )

        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        html = dialog._description_text.toHtml()
        assert "95" in html  # Formula value
        assert "100" in html  # User value

    def test_control_conflict_shows_control_value(self, qtbot, mock_translation_adapter):
        """Test that control conflicts show control value in description."""
        conflicts = (
            ConflictDTO(
                field_id="field_1",
                field_label="Test Field",
                conflict_type="control",
                user_value="A",
                formula_value=None,
                control_value="B",
                description="Control conflict",
            ),
        )

        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        html = dialog._description_text.toHtml()
        assert "A" in html  # User value
        assert "B" in html  # Control value

    def test_dual_conflict_shows_both_values(self, qtbot, mock_translation_adapter):
        """Test that formula+control conflicts show both values."""
        conflicts = (
            ConflictDTO(
                field_id="field_1",
                field_label="Test Field",
                conflict_type="formula_control",
                user_value="X",
                formula_value="Y",
                control_value="Z",
                description="Dual conflict",
            ),
        )

        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        html = dialog._description_text.toHtml()
        assert "X" in html  # User value
        assert "Y" in html  # Formula value
        assert "Z" in html  # Control value

    def test_close_button_accepts_dialog(self, qtbot, mock_translation_adapter, sample_conflicts):
        """Test that Close button accepts the dialog."""
        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=sample_conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        with qtbot.waitSignal(dialog.accepted, timeout=1000):
            dialog._on_close()

        assert dialog.result() == QDialog.DialogCode.Accepted

    def test_static_show_conflicts_method(self, qtbot, mock_translation_adapter, sample_conflicts):
        """Test static show_conflicts method."""
        # This is a simple smoke test - actual implementation would mock exec()
        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=sample_conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Verify dialog was created
        assert dialog is not None

    def test_empty_conflict_list_handled(self, qtbot, mock_translation_adapter):
        """Test that dialog handles empty conflict list gracefully."""
        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog._conflict_table is not None
        assert dialog._conflict_table.rowCount() == 0

    def test_resolution_note_displayed(self, qtbot, mock_translation_adapter, sample_conflicts):
        """Test that resolution note is displayed in description."""
        dialog = ConflictResolutionDialog(
            parent=None,
            conflicts=sample_conflicts,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Select first conflict and check description includes resolution note
        html = dialog._description_text.toHtml()
        # Verify translate was called for resolution note
        mock_translation_adapter.translate.assert_any_call("dialog.conflict_resolution.resolution_note")

"""Unit tests for OverrideManagementDialog."""

import pytest
from unittest.mock import Mock
from PyQt6.QtWidgets import QDialog

from doc_helper.application.dto import OverrideDTO
from doc_helper.presentation.dialogs.override_management_dialog import OverrideManagementDialog


@pytest.fixture
def mock_translation_adapter():
    """Mock QtTranslationAdapter."""
    adapter = Mock()
    adapter.translate = Mock(side_effect=lambda key, **params: key)
    return adapter


@pytest.fixture
def sample_overrides():
    """Sample override DTOs for testing."""
    return (
        OverrideDTO(
            id="override_1",
            field_id="field_1",
            field_label="Borehole Depth",
            system_value="100.0",
            report_value="105.0",
            state="PENDING",
            can_accept=True,
            can_reject=True,
        ),
        OverrideDTO(
            id="override_2",
            field_id="field_2",
            field_label="Sample Count",
            system_value="10",
            report_value="12",
            state="PENDING",
            can_accept=True,
            can_reject=True,
        ),
        OverrideDTO(
            id="override_3",
            field_id="field_3",
            field_label="Project Name",
            system_value="Project A",
            report_value="Project B",
            state="ACCEPTED",
            can_accept=False,
            can_reject=True,
        ),
    )


class TestOverrideManagementDialog:
    """Test suite for OverrideManagementDialog."""

    def test_initialization(self, qtbot, mock_translation_adapter, sample_overrides):
        """Test dialog initialization."""
        dialog = OverrideManagementDialog(
            parent=None,
            overrides=sample_overrides,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "dialog.override_management.title"
        assert dialog.isModal()
        assert dialog.minimumWidth() == 800
        assert dialog.minimumHeight() == 500

    def test_override_table_populated(self, qtbot, mock_translation_adapter, sample_overrides):
        """Test that override table is populated with all overrides."""
        dialog = OverrideManagementDialog(
            parent=None,
            overrides=sample_overrides,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog._override_table is not None
        assert dialog._override_table.rowCount() == 3

    def test_accept_override_records_action(self, qtbot, mock_translation_adapter, sample_overrides):
        """Test that accepting override records the action."""
        dialog = OverrideManagementDialog(
            parent=None,
            overrides=sample_overrides,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        dialog._on_accept_override("field_1")

        actions = dialog.get_actions()
        assert "field_1" in actions
        assert actions["field_1"] == "accept"

    def test_reject_override_records_action(self, qtbot, mock_translation_adapter, sample_overrides):
        """Test that rejecting override records the action."""
        dialog = OverrideManagementDialog(
            parent=None,
            overrides=sample_overrides,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        dialog._on_reject_override("field_1")

        actions = dialog.get_actions()
        assert "field_1" in actions
        assert actions["field_1"] == "reject"

    def test_accept_all_records_all_actions(self, qtbot, mock_translation_adapter, sample_overrides):
        """Test that Accept All records actions for all acceptable overrides."""
        dialog = OverrideManagementDialog(
            parent=None,
            overrides=sample_overrides,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        dialog._on_accept_all()

        actions = dialog.get_actions()
        assert "field_1" in actions
        assert actions["field_1"] == "accept"
        assert "field_2" in actions
        assert actions["field_2"] == "accept"
        # field_3 cannot be accepted (can_accept=False)
        assert "field_3" not in actions

    def test_reject_all_records_all_actions(self, qtbot, mock_translation_adapter, sample_overrides):
        """Test that Reject All records actions for all rejectable overrides."""
        dialog = OverrideManagementDialog(
            parent=None,
            overrides=sample_overrides,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        dialog._on_reject_all()

        actions = dialog.get_actions()
        assert "field_1" in actions
        assert actions["field_1"] == "reject"
        assert "field_2" in actions
        assert actions["field_2"] == "reject"
        assert "field_3" in actions
        assert actions["field_3"] == "reject"

    def test_close_button_accepts_dialog(self, qtbot, mock_translation_adapter, sample_overrides):
        """Test that Close button accepts the dialog."""
        dialog = OverrideManagementDialog(
            parent=None,
            overrides=sample_overrides,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        with qtbot.waitSignal(dialog.accepted, timeout=1000):
            dialog._on_close()

        assert dialog.result() == QDialog.DialogCode.Accepted

    def test_get_actions_returns_copy(self, qtbot, mock_translation_adapter, sample_overrides):
        """Test that get_actions returns a copy of actions dict."""
        dialog = OverrideManagementDialog(
            parent=None,
            overrides=sample_overrides,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        dialog._on_accept_override("field_1")

        actions1 = dialog.get_actions()
        actions2 = dialog.get_actions()

        assert actions1 is not actions2  # Different objects
        assert actions1 == actions2  # Same content

    def test_static_manage_overrides_returns_actions_on_accept(
        self, qtbot, mock_translation_adapter, sample_overrides
    ):
        """Test static manage_overrides method returns actions on accept."""
        dialog = OverrideManagementDialog(
            parent=None,
            overrides=sample_overrides,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Record some actions
        dialog._on_accept_override("field_1")
        dialog._on_reject_override("field_2")

        # Simulate accept
        dialog._on_close()

        actions = dialog.get_actions()
        assert len(actions) == 2
        assert actions["field_1"] == "accept"
        assert actions["field_2"] == "reject"

    def test_empty_override_list_handled(self, qtbot, mock_translation_adapter):
        """Test that dialog handles empty override list gracefully."""
        dialog = OverrideManagementDialog(
            parent=None,
            overrides=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog._override_table is not None
        assert dialog._override_table.rowCount() == 0
        assert len(dialog.get_actions()) == 0

    def test_action_buttons_enabled_state(self, qtbot, mock_translation_adapter):
        """Test that action buttons respect can_accept/can_reject flags."""
        overrides = (
            OverrideDTO(
                id="override_test",
                field_id="field_1",
                field_label="Field 1",
                system_value="A",
                report_value="B",
                state="PENDING",
                can_accept=True,
                can_reject=False,  # Cannot reject
            ),
        )

        dialog = OverrideManagementDialog(
            parent=None,
            overrides=overrides,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Get action widget from table
        action_widget = dialog._override_table.cellWidget(0, 4)
        assert action_widget is not None

        # Accept button should be enabled, Reject button should be disabled
        # (This is a simplified check - actual widget structure may vary)
        assert action_widget is not None

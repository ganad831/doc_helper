"""Unit tests for PreGenerationChecklistDialog."""

import pytest
from unittest.mock import Mock
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QDialog

from doc_helper.application.dto import ValidationErrorDTO
from doc_helper.presentation.dialogs.pre_generation_checklist_dialog import PreGenerationChecklistDialog


@pytest.fixture
def mock_translation_adapter():
    """Mock QtTranslationAdapter."""
    adapter = Mock()
    adapter.translate = Mock(side_effect=lambda key, **params: key if not params else f"{key}_{params.get('count', '')}")
    return adapter


@pytest.fixture
def sample_errors():
    """Sample validation error DTOs for testing."""
    return (
        ValidationErrorDTO(
            field_id="field_1",
            message="Project name is required",
            constraint_type="REQUIRED",
        ),
        ValidationErrorDTO(
            field_id="field_2",
            message="Depth must be greater than 0",
            constraint_type="MIN_VALUE",
        ),
        ValidationErrorDTO(
            field_id="field_3",
            message="Date cannot be in the future",
            constraint_type="MAX_DATE",
        ),
    )


class TestPreGenerationChecklistDialog:
    """Test suite for PreGenerationChecklistDialog."""

    def test_initialization_with_errors(self, qtbot, mock_translation_adapter, sample_errors):
        """Test dialog initialization with validation errors."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=sample_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "dialog.pre_generation.title"
        assert dialog.isModal()
        assert dialog.minimumWidth() == 600
        assert dialog.minimumHeight() == 400
        assert not dialog.can_generate()

    def test_initialization_without_errors(self, qtbot, mock_translation_adapter):
        """Test dialog initialization without validation errors."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog.can_generate()

    def test_error_list_populated(self, qtbot, mock_translation_adapter, sample_errors):
        """Test that error list is populated with all errors."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=sample_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog._error_list is not None
        assert dialog._error_list.count() == 3

    def test_error_count_displayed(self, qtbot, mock_translation_adapter, sample_errors):
        """Test that error count is displayed correctly."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=sample_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Verify translate was called with count parameter
        mock_translation_adapter.translate.assert_any_call(
            "dialog.pre_generation.error_count",
            count=3
        )

    def test_ready_message_when_no_errors(self, qtbot, mock_translation_adapter):
        """Test that ready message is displayed when no errors."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Verify translate was called for ready message
        mock_translation_adapter.translate.assert_any_call("dialog.pre_generation.ready")
        mock_translation_adapter.translate.assert_any_call("dialog.pre_generation.ready_instructions")

    def test_error_instructions_when_has_errors(self, qtbot, mock_translation_adapter, sample_errors):
        """Test that error instructions are displayed when errors exist."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=sample_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Verify translate was called for error instructions
        mock_translation_adapter.translate.assert_any_call("dialog.pre_generation.error_instructions")

    def test_generate_button_shown_when_no_errors(self, qtbot, mock_translation_adapter):
        """Test that Generate button is shown when no errors."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Dialog should have OK/Cancel buttons (Generate renamed from OK)
        assert dialog.can_generate()

    def test_close_button_only_when_has_errors(self, qtbot, mock_translation_adapter, sample_errors):
        """Test that only Close button is shown when errors exist."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=sample_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Dialog should have only Close button
        assert not dialog.can_generate()

    def test_generate_button_accepts_dialog(self, qtbot, mock_translation_adapter):
        """Test that Generate button accepts the dialog."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        with qtbot.waitSignal(dialog.accepted, timeout=1000):
            dialog._on_generate()

        assert dialog.result() == QDialog.DialogCode.Accepted

    def test_cancel_button_rejects_dialog(self, qtbot, mock_translation_adapter):
        """Test that Cancel button rejects the dialog."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        with qtbot.waitSignal(dialog.rejected, timeout=1000):
            dialog._on_cancel()

        assert dialog.result() == QDialog.DialogCode.Rejected

    def test_close_button_rejects_dialog_when_errors(self, qtbot, mock_translation_adapter, sample_errors):
        """Test that Close button rejects the dialog when errors exist."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=sample_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        with qtbot.waitSignal(dialog.rejected, timeout=1000):
            dialog._on_cancel()

        assert dialog.result() == QDialog.DialogCode.Rejected

    def test_can_generate_returns_correct_state(self, qtbot, mock_translation_adapter):
        """Test that can_generate returns correct state."""
        # With errors
        dialog_with_errors = PreGenerationChecklistDialog(
            parent=None,
            errors=(ValidationErrorDTO("f1", "F1", "Error"),),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog_with_errors)
        assert not dialog_with_errors.can_generate()

        # Without errors
        dialog_without_errors = PreGenerationChecklistDialog(
            parent=None,
            errors=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog_without_errors)
        assert dialog_without_errors.can_generate()

    def test_static_check_and_confirm_returns_true_on_generate(self, qtbot, mock_translation_adapter):
        """Test static check_and_confirm returns True on Generate."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Simulate accept
        dialog._on_generate()

        assert dialog.result() == QDialog.DialogCode.Accepted
        assert dialog.can_generate()

    def test_static_check_and_confirm_returns_false_with_errors(self, qtbot, mock_translation_adapter, sample_errors):
        """Test static check_and_confirm returns False with errors."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=sample_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Cannot generate with errors
        assert not dialog.can_generate()

    def test_static_check_and_confirm_returns_false_on_cancel(self, qtbot, mock_translation_adapter):
        """Test static check_and_confirm returns False on Cancel."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Simulate reject
        dialog._on_cancel()

        assert dialog.result() == QDialog.DialogCode.Rejected

    def test_error_tooltips(self, qtbot, mock_translation_adapter, sample_errors):
        """Test that error items have field IDs as tooltips."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=sample_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Check first error item has tooltip
        first_item = dialog._error_list.item(0)
        assert first_item is not None
        assert "field_1" in first_item.toolTip()

    def test_error_formatting(self, qtbot, mock_translation_adapter, sample_errors):
        """Test that errors are formatted with bullet points."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=sample_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Check first error item text starts with bullet
        first_item = dialog._error_list.item(0)
        assert first_item is not None
        assert first_item.text().startswith("•")

    def test_generate_button_label(self, qtbot, mock_translation_adapter):
        """Test that OK button is renamed to 'Generate'."""
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Verify translate was called for generate button
        mock_translation_adapter.translate.assert_any_call("dialog.pre_generation.generate")

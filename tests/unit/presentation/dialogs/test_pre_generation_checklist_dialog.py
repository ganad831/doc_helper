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
    """Sample validation error DTOs for testing (legacy - no severity)."""
    return (
        ValidationErrorDTO(
            field_id="field_1",
            message="Project name is required",
            constraint_type="REQUIRED",
            severity="ERROR",  # Default severity
        ),
        ValidationErrorDTO(
            field_id="field_2",
            message="Depth must be greater than 0",
            constraint_type="MIN_VALUE",
            severity="ERROR",  # Default severity
        ),
        ValidationErrorDTO(
            field_id="field_3",
            message="Date cannot be in the future",
            constraint_type="MAX_DATE",
            severity="ERROR",  # Default severity
        ),
    )


@pytest.fixture
def error_severity_errors():
    """Sample ERROR-level validation errors (ADR-025)."""
    return (
        ValidationErrorDTO(
            field_id="field_1",
            message="Project name is required",
            constraint_type="REQUIRED",
            severity="ERROR",
        ),
        ValidationErrorDTO(
            field_id="field_2",
            message="Depth must be greater than 0",
            constraint_type="MIN_VALUE",
            severity="ERROR",
        ),
    )


@pytest.fixture
def warning_severity_errors():
    """Sample WARNING-level validation errors (ADR-025)."""
    return (
        ValidationErrorDTO(
            field_id="field_3",
            message="Description is too short (recommended 10+ chars)",
            constraint_type="MIN_LENGTH",
            severity="WARNING",
        ),
    )


@pytest.fixture
def info_severity_errors():
    """Sample INFO-level validation errors (ADR-025)."""
    return (
        ValidationErrorDTO(
            field_id="field_4",
            message="Consider adding more details",
            constraint_type="INFO_MESSAGE",
            severity="INFO",
        ),
    )


@pytest.fixture
def mixed_severity_errors():
    """Sample mixed-severity validation errors (ADR-025)."""
    return (
        ValidationErrorDTO(
            field_id="field_1",
            message="Project name is required",
            constraint_type="REQUIRED",
            severity="ERROR",
        ),
        ValidationErrorDTO(
            field_id="field_2",
            message="Description is too short",
            constraint_type="MIN_LENGTH",
            severity="WARNING",
        ),
        ValidationErrorDTO(
            field_id="field_3",
            message="Consider adding location details",
            constraint_type="INFO_MESSAGE",
            severity="INFO",
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
        assert dialog.minimumHeight() == 500  # ADR-025: Increased for severity sections
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


class TestPreGenerationChecklistDialogSeverity:
    """Test suite for PreGenerationChecklistDialog with ADR-025 severity support."""

    def test_error_severity_blocks_generation(self, qtbot, mock_translation_adapter, error_severity_errors):
        """ERROR-level failures should block generation.

        ADR-025: ERROR severity blocks generation unconditionally.
        """
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=error_severity_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # ERROR-level failures block generation
        assert not dialog.can_generate()
        assert dialog._has_blocking_errors

    def test_warning_severity_allows_generation_with_confirmation(
        self, qtbot, mock_translation_adapter, warning_severity_errors
    ):
        """WARNING-level failures should allow generation with confirmation.

        ADR-025: WARNING severity requires user confirmation but does not block.
        """
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=warning_severity_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # WARNING-level failures do not block
        assert dialog.can_generate()
        assert not dialog._has_blocking_errors

        # "Continue Anyway" button should be shown
        mock_translation_adapter.translate.assert_any_call("dialog.pre_generation.continue_anyway")

    def test_info_severity_allows_generation(self, qtbot, mock_translation_adapter, info_severity_errors):
        """INFO-level messages should allow generation without confirmation.

        ADR-025: INFO severity is informational only, never blocks.
        """
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=info_severity_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # INFO-level messages do not block
        assert dialog.can_generate()
        assert not dialog._has_blocking_errors

    def test_mixed_severity_blocks_on_error(self, qtbot, mock_translation_adapter, mixed_severity_errors):
        """Mixed severity failures should block if ANY ERROR exists.

        ADR-025: ERROR takes precedence over WARNING/INFO.
        """
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=mixed_severity_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # ERROR blocks even with WARNING/INFO present
        assert not dialog.can_generate()
        assert dialog._has_blocking_errors

    def test_severity_grouping(self, qtbot, mock_translation_adapter, mixed_severity_errors):
        """Errors should be grouped by severity level.

        ADR-025: Display ERROR, WARNING, INFO in separate sections.
        """
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=mixed_severity_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Check that errors are grouped correctly
        assert len(dialog._errors_by_severity["ERROR"]) == 1
        assert len(dialog._errors_by_severity["WARNING"]) == 1
        assert len(dialog._errors_by_severity["INFO"]) == 1

    def test_error_section_displayed_when_errors_exist(
        self, qtbot, mock_translation_adapter, mixed_severity_errors
    ):
        """ERROR section should be displayed when ERROR-level failures exist.

        ADR-025: Visual differentiation for ERROR (red).
        """
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=mixed_severity_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # ERROR section should exist
        assert dialog._error_list is not None
        assert dialog._error_list.count() == 1

        # Translation called for error section
        mock_translation_adapter.translate.assert_any_call(
            "dialog.pre_generation.errors_section",
            count=1
        )

    def test_warning_section_displayed_when_warnings_exist(
        self, qtbot, mock_translation_adapter, mixed_severity_errors
    ):
        """WARNING section should be displayed when WARNING-level failures exist.

        ADR-025: Visual differentiation for WARNING (yellow/orange).
        """
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=mixed_severity_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # WARNING section should exist
        assert dialog._warning_list is not None
        assert dialog._warning_list.count() == 1

        # Translation called for warning section
        mock_translation_adapter.translate.assert_any_call(
            "dialog.pre_generation.warnings_section",
            count=1
        )

    def test_info_section_displayed_when_info_exist(
        self, qtbot, mock_translation_adapter, mixed_severity_errors
    ):
        """INFO section should be displayed when INFO-level messages exist.

        ADR-025: Visual differentiation for INFO (blue).
        """
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=mixed_severity_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # INFO section should exist
        assert dialog._info_list is not None
        assert dialog._info_list.count() == 1

        # Translation called for info section
        mock_translation_adapter.translate.assert_any_call(
            "dialog.pre_generation.info_section",
            count=1
        )

    def test_continue_anyway_button_with_warnings_only(
        self, qtbot, mock_translation_adapter, warning_severity_errors
    ):
        """'Continue Anyway' button should be shown with WARNING-only failures.

        ADR-025: User confirmation required for WARNING severity.
        """
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=warning_severity_errors,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Can generate (warnings don't block)
        assert dialog.can_generate()

        # "Continue Anyway" button text
        mock_translation_adapter.translate.assert_any_call("dialog.pre_generation.continue_anyway")

    def test_generate_button_with_no_warnings(
        self, qtbot, mock_translation_adapter
    ):
        """'Generate' button should be shown when no warnings.

        ADR-025: Standard generate button when no validation issues.
        """
        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Can generate (no issues)
        assert dialog.can_generate()

        # "Generate" button text
        mock_translation_adapter.translate.assert_any_call("dialog.pre_generation.generate")

    def test_only_warnings_and_info_shows_correct_status(
        self, qtbot, mock_translation_adapter
    ):
        """Status message should reflect warnings/info when no errors.

        ADR-025: Different status message for non-blocking failures.
        """
        errors_with_warning_and_info = (
            ValidationErrorDTO(
                field_id="field_1",
                message="Description is short",
                constraint_type="MIN_LENGTH",
                severity="WARNING",
            ),
            ValidationErrorDTO(
                field_id="field_2",
                message="Consider adding details",
                constraint_type="INFO_MESSAGE",
                severity="INFO",
            ),
        )

        dialog = PreGenerationChecklistDialog(
            parent=None,
            errors=errors_with_warning_and_info,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Translation called with warning/info count
        mock_translation_adapter.translate.assert_any_call(
            "dialog.pre_generation.warnings_info_count",
            warning_count=1,
            info_count=1
        )

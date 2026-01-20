"""Unit tests for TemplateSelectionDialog."""

import pytest
from unittest.mock import Mock, MagicMock
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QDialog

from doc_helper.application.dto import TemplateDTO
from doc_helper.presentation.dialogs.template_selection_dialog import TemplateSelectionDialog


@pytest.fixture
def mock_translation_adapter():
    """Mock QtTranslationAdapter."""
    adapter = Mock()
    adapter.translate = Mock(side_effect=lambda key, **params: key)
    return adapter


@pytest.fixture
def sample_templates():
    """Sample template DTOs for testing."""
    return (
        TemplateDTO(
            id="template_1",
            name="Standard Report",
            description="Standard soil investigation report template",
            file_path="templates/standard_report.docx",
            format="docx",
            is_default=True,
        ),
        TemplateDTO(
            id="template_2",
            name="Detailed Report",
            description="Detailed template with additional sections",
            file_path="templates/detailed_report.docx",
            format="docx",
            is_default=False,
        ),
        TemplateDTO(
            id="template_3",
            name="Summary Report",
            description="Brief summary template",
            file_path="templates/summary_report.docx",
            format="docx",
            is_default=False,
        ),
    )


class TestTemplateSelectionDialog:
    """Test suite for TemplateSelectionDialog."""

    def test_initialization(self, qtbot, mock_translation_adapter, sample_templates):
        """Test dialog initialization."""
        dialog = TemplateSelectionDialog(
            parent=None,
            templates=sample_templates,
            translation_adapter=mock_translation_adapter,
            current_template_id="template_1",
        )
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "dialog.template_selection.title"
        assert dialog.isModal()
        assert dialog.minimumWidth() == 500
        assert dialog.minimumHeight() == 400

    def test_template_list_populated(self, qtbot, mock_translation_adapter, sample_templates):
        """Test that template list is populated with all templates."""
        dialog = TemplateSelectionDialog(
            parent=None,
            templates=sample_templates,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog._template_list is not None
        assert dialog._template_list.count() == 3

    def test_default_template_highlighted(self, qtbot, mock_translation_adapter, sample_templates):
        """Test that default template is highlighted with bold font."""
        dialog = TemplateSelectionDialog(
            parent=None,
            templates=sample_templates,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # First item (default template) should have bold font
        first_item = dialog._template_list.item(0)
        assert first_item is not None
        assert first_item.font().bold()

    def test_current_template_selected(self, qtbot, mock_translation_adapter, sample_templates):
        """Test that current template is pre-selected."""
        dialog = TemplateSelectionDialog(
            parent=None,
            templates=sample_templates,
            translation_adapter=mock_translation_adapter,
            current_template_id="template_2",
        )
        qtbot.addWidget(dialog)

        assert dialog._selected_template is not None
        assert dialog._selected_template.id == "template_2"

    def test_default_selected_if_no_current(self, qtbot, mock_translation_adapter, sample_templates):
        """Test that default template is selected if no current template."""
        dialog = TemplateSelectionDialog(
            parent=None,
            templates=sample_templates,
            translation_adapter=mock_translation_adapter,
            current_template_id=None,
        )
        qtbot.addWidget(dialog)

        assert dialog._selected_template is not None
        assert dialog._selected_template.is_default

    def test_template_selection_updates_details(self, qtbot, mock_translation_adapter, sample_templates):
        """Test that selecting a template updates the details panel."""
        dialog = TemplateSelectionDialog(
            parent=None,
            templates=sample_templates,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        # Select second template
        dialog._template_list.setCurrentRow(1)
        QCoreApplication.processEvents()

        assert dialog._selected_template is not None
        assert dialog._selected_template.id == "template_2"
        assert dialog._description_text is not None
        assert "Detailed Report" in dialog._description_text.toHtml()

    def test_ok_button_accepts_dialog(self, qtbot, mock_translation_adapter, sample_templates):
        """Test that OK button accepts the dialog."""
        dialog = TemplateSelectionDialog(
            parent=None,
            templates=sample_templates,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        with qtbot.waitSignal(dialog.accepted, timeout=1000):
            dialog._on_ok()

        assert dialog.result() == QDialog.DialogCode.Accepted

    def test_cancel_button_rejects_dialog(self, qtbot, mock_translation_adapter, sample_templates):
        """Test that Cancel button rejects the dialog."""
        dialog = TemplateSelectionDialog(
            parent=None,
            templates=sample_templates,
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        with qtbot.waitSignal(dialog.rejected, timeout=1000):
            dialog._on_cancel()

        assert dialog.result() == QDialog.DialogCode.Rejected
        assert dialog._selected_template is None

    def test_get_selected_template_returns_selection(self, qtbot, mock_translation_adapter, sample_templates):
        """Test that get_selected_template returns the selected template."""
        dialog = TemplateSelectionDialog(
            parent=None,
            templates=sample_templates,
            translation_adapter=mock_translation_adapter,
            current_template_id="template_2",
        )
        qtbot.addWidget(dialog)

        selected = dialog.get_selected_template()
        assert selected is not None
        assert selected.id == "template_2"

    def test_static_select_template_returns_template_on_accept(
        self, qtbot, mock_translation_adapter, sample_templates, monkeypatch
    ):
        """Test static select_template method returns template on accept."""
        # Mock exec() to simulate user accepting dialog
        def mock_exec(self):
            self._selected_template = sample_templates[1]
            return QDialog.DialogCode.Accepted

        monkeypatch.setattr(TemplateSelectionDialog, "exec", mock_exec)

        result = TemplateSelectionDialog.select_template(
            parent=None,
            templates=sample_templates,
            translation_adapter=mock_translation_adapter,
            current_template_id="template_1",
        )

        assert result is not None
        assert result.id == "template_2"

    def test_empty_template_list_handled(self, qtbot, mock_translation_adapter):
        """Test that dialog handles empty template list gracefully."""
        dialog = TemplateSelectionDialog(
            parent=None,
            templates=(),
            translation_adapter=mock_translation_adapter,
        )
        qtbot.addWidget(dialog)

        assert dialog._template_list is not None
        assert dialog._template_list.count() == 0
        assert dialog._selected_template is None

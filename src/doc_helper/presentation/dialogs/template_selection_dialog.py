"""Template selection dialog for document generation.

RULES (AGENT_RULES.md Section 3-4):
- Uses DTOs only (TemplateDTO, not domain types)
- No business logic (selection only)
- Translation adapter for i18n
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto import TemplateDTO
from doc_helper.presentation.adapters.qt_translation_adapter import QtTranslationAdapter


class TemplateSelectionDialog(QDialog):
    """Template selection dialog.

    v1 Implementation:
    - List of available templates
    - Template details display (name, description, format)
    - Default template highlighted
    - OK/Cancel buttons

    v2+ Features (deferred):
    - Template preview
    - Template filtering by format
    - Custom template upload

    RULES (AGENT_RULES.md Section 3-4):
    - Uses DTOs only (TemplateDTO)
    - No domain logic
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        templates: tuple[TemplateDTO, ...],
        translation_adapter: QtTranslationAdapter,
        current_template_id: Optional[str] = None,
    ) -> None:
        """Initialize template selection dialog.

        Args:
            parent: Parent widget
            templates: Tuple of available templates
            translation_adapter: Qt translation adapter for i18n
            current_template_id: Currently selected template ID (if any)
        """
        super().__init__(parent)
        self._templates = templates
        self._translation_adapter = translation_adapter
        self._current_template_id = current_template_id

        # UI components
        self._template_list: Optional[QListWidget] = None
        self._description_text: Optional[QTextEdit] = None
        self._selected_template: Optional[TemplateDTO] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        self.setWindowTitle(self._translation_adapter.translate("dialog.template_selection.title"))
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Instructions label
        instructions = QLabel(
            self._translation_adapter.translate("dialog.template_selection.instructions")
        )
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)

        # Template list
        list_label = QLabel(self._translation_adapter.translate("dialog.template_selection.available_templates"))
        main_layout.addWidget(list_label)

        self._template_list = QListWidget()
        self._template_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._template_list.currentItemChanged.connect(self._on_template_selected)
        main_layout.addWidget(self._template_list, 1)  # Stretch factor 1

        # Template details
        details_label = QLabel(self._translation_adapter.translate("dialog.template_selection.details"))
        main_layout.addWidget(details_label)

        self._description_text = QTextEdit()
        self._description_text.setReadOnly(True)
        self._description_text.setMaximumHeight(100)
        main_layout.addWidget(self._description_text)

        # Populate template list
        self._populate_templates()

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self._on_cancel)
        main_layout.addWidget(button_box)

    def _populate_templates(self) -> None:
        """Populate template list with available templates."""
        if not self._template_list:
            return

        for template in self._templates:
            # Template display text
            display_text = template.name
            if template.is_default:
                display_text += f" ({self._translation_adapter.translate('common.default')})"

            # Create list item
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, template.id)

            # Highlight default template with bold font
            if template.is_default:
                font = item.font()
                font.setBold(True)
                item.setFont(font)

            # Add item to list
            self._template_list.addItem(item)

            # Select current template or default
            if (self._current_template_id and template.id == self._current_template_id) or \
               (not self._current_template_id and template.is_default):
                self._template_list.setCurrentItem(item)
                self._selected_template = template

    def _on_template_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]) -> None:
        """Handle template selection change.

        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if not current or not self._description_text:
            return

        # Find selected template
        template_id = current.data(Qt.ItemDataRole.UserRole)
        selected_template = next((t for t in self._templates if t.id == template_id), None)

        if not selected_template:
            return

        self._selected_template = selected_template

        # Update description display
        description_parts = []

        # Template name
        description_parts.append(f"<b>{selected_template.name}</b>")

        # Description
        if selected_template.description:
            description_parts.append(f"<p>{selected_template.description}</p>")

        # Format
        format_label = self._translation_adapter.translate("dialog.template_selection.format")
        description_parts.append(f"<p><b>{format_label}:</b> {selected_template.format}</p>")

        # Default indicator
        if selected_template.is_default:
            description_parts.append(
                f"<p><i>{self._translation_adapter.translate('dialog.template_selection.default_template')}</i></p>"
            )

        self._description_text.setHtml("\n".join(description_parts))

    def _on_ok(self) -> None:
        """Handle OK button click."""
        # Validation: Ensure a template is selected
        if not self._selected_template:
            # No template selected - should not happen if we pre-select default
            return

        # Close dialog with acceptance
        self.accept()

    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        # Reset selection
        self._selected_template = None

        # Close dialog without saving
        self.reject()

    def get_selected_template(self) -> Optional[TemplateDTO]:
        """Get the selected template.

        Returns:
            Selected template DTO, or None if cancelled
        """
        return self._selected_template

    @staticmethod
    def select_template(
        parent: Optional[QWidget],
        templates: tuple[TemplateDTO, ...],
        translation_adapter: QtTranslationAdapter,
        current_template_id: Optional[str] = None,
    ) -> Optional[TemplateDTO]:
        """Show template selection dialog and return selected template.

        Args:
            parent: Parent widget
            templates: Tuple of available templates
            translation_adapter: Qt translation adapter
            current_template_id: Currently selected template ID (if any)

        Returns:
            Selected template DTO, or None if cancelled
        """
        dialog = TemplateSelectionDialog(
            parent, templates, translation_adapter, current_template_id
        )
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            return dialog.get_selected_template()

        return None

"""Settings dialog for application preferences."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from doc_helper.domain.common.i18n import Language
from doc_helper.domain.common.translation import ITranslationService


class SettingsDialog(QDialog):
    """Settings dialog for user preferences.

    v1 Implementation:
    - Language selection (English/Arabic)
    - Light theme only (dark mode is v2+)
    - OK/Cancel buttons

    v2+ Features (deferred):
    - Dark mode/theme switching
    - Auto-save settings
    - Font size settings
    - Additional language support

    RULES (AGENT_RULES.md Section 3-4):
    - Uses DTOs only (no domain objects)
    - Translation service for i18n
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        translation_service: ITranslationService,
    ) -> None:
        """Initialize settings dialog.

        Args:
            parent: Parent widget
            translation_service: Translation service for language switching
        """
        super().__init__(parent)
        self._translation_service = translation_service

        # UI components
        self._language_combo: Optional[QComboBox] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(400)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Settings form
        form_layout = QFormLayout()

        # Language selection
        language_label = QLabel("Language:")
        self._language_combo = QComboBox()

        # Populate language options
        for language in Language:
            self._language_combo.addItem(
                language.display_name,  # Display name (English, العربية)
                language,  # User data (Language enum)
            )

        # Set current language
        current_language = self._translation_service.get_current_language()
        current_index = list(Language).index(current_language)
        self._language_combo.setCurrentIndex(current_index)

        form_layout.addRow(language_label, self._language_combo)

        main_layout.addLayout(form_layout)

        # Spacer
        main_layout.addStretch()

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self._on_cancel)
        main_layout.addWidget(button_box)

    def _on_ok(self) -> None:
        """Handle OK button click."""
        # Get selected language
        if self._language_combo:
            selected_language = self._language_combo.currentData()

            # Set language via translation service
            if selected_language:
                self._translation_service.set_language(selected_language)

        # Close dialog
        self.accept()

    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        # Close dialog without saving
        self.reject()

    @staticmethod
    def show_settings(
        parent: Optional[QWidget],
        translation_service: ITranslationService,
    ) -> bool:
        """Show settings dialog and return whether user clicked OK.

        Args:
            parent: Parent widget
            translation_service: Translation service

        Returns:
            True if user clicked OK, False if cancelled
        """
        dialog = SettingsDialog(parent, translation_service)
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted

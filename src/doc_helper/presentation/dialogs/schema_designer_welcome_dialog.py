"""Schema Designer Welcome Dialog (Phase 5 Step 2).

First-launch welcome dialog for Schema Designer onboarding.

Phase 5: UX Polish & Onboarding
- Shown only on first launch of Schema Designer
- Explains TOOL AppType, meta-schema editing, manual workflow
- Dismissible permanently via QSettings
- Persistence ONLY for dismissal flag (no other data)
"""

from typing import Optional

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# Settings key for welcome dialog dismissal
# Stored in QSettings (platform-appropriate location)
_SETTINGS_KEY_WELCOME_DISMISSED = "schema_designer/welcome_dismissed"


class SchemaDesignerWelcomeDialog(QDialog):
    """First-launch welcome dialog for Schema Designer.

    Explains:
    - TOOL AppType
    - Meta-schema editing (not project data)
    - Manual export & deployment required

    Persistence:
    - Uses QSettings for "don't show again" flag
    - QSettings is Qt's standard cross-platform preferences storage
    - Does NOT involve schema or repository changes
    - UX preference only

    Phase 5 Scope:
    - Onboarding content only
    - Dismissal persistence allowed
    - No business logic
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize welcome dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._dont_show_again_checkbox: Optional[QCheckBox] = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        self.setWindowTitle("Welcome to Schema Designer")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setFixedHeight(420)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 20)

        # Welcome icon/header
        header = QLabel("Welcome to Schema Designer")
        header.setStyleSheet(
            "font-size: 18pt; "
            "font-weight: bold; "
            "color: #2d3748; "
            "padding-bottom: 8px;"
        )
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Main explanation
        explanation = QLabel(
            "Schema Designer is a <b>meta-schema editor</b>. "
            "It allows you to define:"
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("font-size: 10pt; color: #4a5568;")
        main_layout.addWidget(explanation)

        # Bullet points
        bullets = QLabel(
            "• <b>Entities</b> — e.g., 'Project Info', 'Boreholes', 'Samples'\n"
            "• <b>Fields</b> — e.g., 'Project Name', 'Depth', 'Sample Date'\n"
            "• <b>Validation rules</b> — constraints on field values"
        )
        bullets.setWordWrap(True)
        bullets.setStyleSheet(
            "font-size: 10pt; "
            "color: #4a5568; "
            "padding-left: 16px; "
            "line-height: 1.6;"
        )
        main_layout.addWidget(bullets)

        # Important notice box
        notice_box = QWidget()
        notice_box.setStyleSheet(
            "background-color: #fef3c7; "
            "border: 1px solid #f59e0b; "
            "border-radius: 6px; "
            "padding: 12px;"
        )
        notice_layout = QVBoxLayout(notice_box)
        notice_layout.setContentsMargins(12, 8, 12, 8)
        notice_layout.setSpacing(8)

        notice_title = QLabel("Important")
        notice_title.setStyleSheet(
            "font-weight: bold; "
            "color: #92400e; "
            "font-size: 10pt;"
        )
        notice_layout.addWidget(notice_title)

        notice_text = QLabel(
            "This tool does <b>NOT</b> edit project data. "
            "It defines the <i>structure</i> that project data will follow.\n\n"
            "After designing your schema, you must:\n"
            "1. Export your schema manually\n"
            "2. Deploy it to your target app type folder\n"
            "3. Restart the application"
        )
        notice_text.setWordWrap(True)
        notice_text.setStyleSheet("color: #92400e; font-size: 9pt;")
        notice_layout.addWidget(notice_text)

        main_layout.addWidget(notice_box)

        main_layout.addStretch()

        # Don't show again checkbox
        self._dont_show_again_checkbox = QCheckBox("Don't show this again")
        self._dont_show_again_checkbox.setStyleSheet("color: #718096;")
        main_layout.addWidget(self._dont_show_again_checkbox)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        got_it_button = QPushButton("Got it")
        got_it_button.setDefault(True)
        got_it_button.setMinimumWidth(100)
        got_it_button.setStyleSheet(
            "QPushButton { "
            "background-color: #4299e1; "
            "color: white; "
            "border: none; "
            "padding: 8px 24px; "
            "border-radius: 4px; "
            "font-weight: bold; "
            "} "
            "QPushButton:hover { "
            "background-color: #3182ce; "
            "}"
        )
        got_it_button.clicked.connect(self._on_got_it)
        button_layout.addWidget(got_it_button)

        main_layout.addLayout(button_layout)

    def _on_got_it(self) -> None:
        """Handle 'Got it' button click."""
        # Save preference if "Don't show again" is checked
        if self._dont_show_again_checkbox and self._dont_show_again_checkbox.isChecked():
            settings = QSettings()
            settings.setValue(_SETTINGS_KEY_WELCOME_DISMISSED, True)

        self.accept()

    @staticmethod
    def should_show() -> bool:
        """Check if the welcome dialog should be shown.

        Returns:
            True if welcome dialog has not been permanently dismissed
        """
        settings = QSettings()
        return not settings.value(_SETTINGS_KEY_WELCOME_DISMISSED, False, type=bool)

    @staticmethod
    def show_if_first_launch(parent: Optional[QWidget] = None) -> bool:
        """Show welcome dialog if this is the first launch.

        Args:
            parent: Parent widget

        Returns:
            True if dialog was shown, False if already dismissed
        """
        if SchemaDesignerWelcomeDialog.should_show():
            dialog = SchemaDesignerWelcomeDialog(parent)
            dialog.exec()
            return True
        return False

    @staticmethod
    def reset_welcome_flag() -> None:
        """Reset the welcome dismissed flag (for testing).

        This allows the welcome dialog to be shown again.
        """
        settings = QSettings()
        settings.remove(_SETTINGS_KEY_WELCOME_DISMISSED)

"""Schema Designer Help Dialog (Phase 5 Step 2).

Static help dialog explaining Schema Designer purpose and workflow.

Phase 5: UX Polish & Onboarding
- Static explanatory content
- No dynamic content or logic branching
- Accessible via "What is this?" link
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SchemaDesignerHelpDialog(QDialog):
    """Static help dialog for Schema Designer.

    Explains:
    - What Schema Designer is
    - What Schema Designer is NOT
    - Manual export & deployment responsibility
    - Why UI is intentionally minimal

    Phase 5 Scope:
    - Static content only
    - No dynamic content
    - No logic branching
    - UX explanation only
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize help dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        self.setWindowTitle("About Schema Designer")
        self.setModal(True)
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)

        main_layout = QVBoxLayout(self)

        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)

        # Title
        title = QLabel("Schema Designer")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2d3748;")
        content_layout.addWidget(title)

        # What it is
        self._add_section(
            content_layout,
            "What is Schema Designer?",
            "Schema Designer is a <b>TOOL AppType</b> for editing meta-schema "
            "definitions. It allows you to define:\n\n"
            "• <b>Entities</b> — Containers for related fields "
            "(e.g., 'Project Info', 'Boreholes', 'Samples')\n"
            "• <b>Fields</b> — Individual data elements within entities "
            "(e.g., 'Project Name', 'Depth', 'Sample Date')\n"
            "• <b>Validation Rules</b> — Constraints on field values "
            "(e.g., required, min/max, patterns)"
        )

        # What it is NOT
        self._add_section(
            content_layout,
            "What Schema Designer is NOT",
            "Schema Designer does <b>NOT</b>:\n\n"
            "• Edit project data — It only edits the <i>structure</i> "
            "(meta-schema) that projects will follow\n"
            "• Connect to existing projects — Projects are separate from schema\n"
            "• Auto-deploy changes — You must manually export and deploy\n"
            "• Generate documents — It's a schema editing tool, not a document generator"
        )

        # Manual workflow
        self._add_section(
            content_layout,
            "Manual Export & Deployment",
            "After designing your schema, you must:\n\n"
            "1. <b>Export</b> your schema to a file (JSON format)\n"
            "2. <b>Copy</b> the exported file to your target app type folder\n"
            "3. <b>Restart</b> Doc Helper to load the updated schema\n\n"
            "Schema Designer does not automatically deploy schemas. "
            "Import and deployment are manual processes outside this tool."
        )

        # Why minimal UI
        self._add_section(
            content_layout,
            "Why is the UI Minimal?",
            "Schema Designer is intentionally minimal because:\n\n"
            "• It focuses on core schema editing functionality\n"
            "• Advanced features (relationships, visual graphs) are planned for future releases\n"
            "• Simplicity reduces complexity and potential errors\n\n"
            "The current scope includes creating and viewing entities, fields, "
            "and basic validation rules. Additional capabilities will be added "
            "in future phases."
        )

        # Tip
        tip_label = QLabel(
            "<i>Tip: Think of Schema Designer as designing a form template, "
            "not filling out the form. The schema defines what fields exist — "
            "projects contain the actual data.</i>"
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(
            "color: #4a5568; "
            "background-color: #edf2f7; "
            "padding: 12px; "
            "border-radius: 4px; "
            "margin-top: 8px;"
        )
        content_layout.addWidget(tip_label)

        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        main_layout.addWidget(button_box)

    def _add_section(
        self,
        layout: QVBoxLayout,
        title: str,
        content: str,
    ) -> None:
        """Add a titled section to the layout.

        Args:
            layout: Parent layout
            title: Section title
            content: Section content (supports HTML)
        """
        # Section title
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 11pt; "
            "font-weight: bold; "
            "color: #4a5568; "
            "margin-top: 8px;"
        )
        layout.addWidget(title_label)

        # Section content
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.TextFormat.RichText)
        content_label.setStyleSheet(
            "color: #4a5568; "
            "line-height: 1.5; "
            "padding-left: 8px;"
        )
        layout.addWidget(content_label)

    @staticmethod
    def show_help(parent: Optional[QWidget] = None) -> None:
        """Show the help dialog.

        Args:
            parent: Parent widget
        """
        dialog = SchemaDesignerHelpDialog(parent)
        dialog.exec()

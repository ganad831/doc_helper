"""New Project Dialog.

v2 PHASE 4: Dialog for creating new projects with AppType selection.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto import AppTypeDTO


class NewProjectDialog(QDialog):
    """Dialog for creating a new project with AppType selection.

    v2 PHASE 4: User selects AppType before creating project.

    Usage:
        dialog = NewProjectDialog(parent, available_app_types)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_project_name()
            app_type_id = dialog.get_selected_app_type_id()
            description = dialog.get_description()
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        available_app_types: list[AppTypeDTO],
    ) -> None:
        """Initialize NewProjectDialog.

        Args:
            parent: Parent widget
            available_app_types: List of available AppTypes to choose from
        """
        super().__init__(parent)
        self._available_app_types = available_app_types

        # UI components
        self._name_edit: Optional[QLineEdit] = None
        self._app_type_combo: Optional[QComboBox] = None
        self._description_edit: Optional[QTextEdit] = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        self.setWindowTitle("Create New Project")
        self.setMinimumWidth(500)

        # Main layout
        layout = QVBoxLayout(self)

        # Form layout for inputs
        form_layout = QFormLayout()

        # Project name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter project name...")
        form_layout.addRow("Project Name:", self._name_edit)

        # AppType selection
        self._app_type_combo = QComboBox()

        # AppType description label (create BEFORE connecting signal)
        self._app_type_description_label = QLabel()
        self._app_type_description_label.setWordWrap(True)
        self._app_type_description_label.setStyleSheet("color: gray; font-size: 10pt;")

        # Populate AppType combo box
        if not self._available_app_types:
            self._app_type_combo.addItem("No AppTypes available", userData=None)
            self._app_type_combo.setEnabled(False)
        else:
            for app_type in self._available_app_types:
                self._app_type_combo.addItem(
                    f"{app_type.name} (v{app_type.version})",
                    userData=app_type.app_type_id,
                )

        # Connect signal AFTER creating label
        self._app_type_combo.currentIndexChanged.connect(self._on_app_type_changed)

        form_layout.addRow("AppType:", self._app_type_combo)
        form_layout.addRow("", self._app_type_description_label)

        # Update description for initial selection
        self._on_app_type_changed(0)

        # Project description (optional)
        self._description_edit = QTextEdit()
        self._description_edit.setPlaceholderText(
            "Enter project description (optional)..."
        )
        self._description_edit.setMaximumHeight(80)
        form_layout.addRow("Description:", self._description_edit)

        layout.addLayout(form_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_app_type_changed(self, index: int) -> None:
        """Handle AppType selection change.

        Args:
            index: Selected combo box index
        """
        if not self._app_type_combo or not self._app_type_description_label:
            return

        if index < 0 or index >= len(self._available_app_types):
            self._app_type_description_label.setText("")
            return

        app_type = self._available_app_types[index]
        self._app_type_description_label.setText(app_type.description)

    def _validate_and_accept(self) -> None:
        """Validate inputs before accepting dialog."""
        if not self._name_edit:
            return

        name = self._name_edit.text().strip()
        if not name:
            # TODO: Show error message
            return

        if not self._available_app_types:
            # TODO: Show error message
            return

        # Check if app type is actually selected
        if not self._app_type_combo or self._app_type_combo.currentIndex() < 0:
            # TODO: Show error message
            return

        self.accept()

    def get_project_name(self) -> str:
        """Get entered project name.

        Returns:
            Project name string
        """
        if not self._name_edit:
            return ""
        return self._name_edit.text().strip()

    def get_selected_app_type_id(self) -> Optional[str]:
        """Get selected AppType ID.

        Returns:
            AppType ID string, or None if no selection
        """
        if not self._app_type_combo:
            return None

        return self._app_type_combo.currentData()

    def get_description(self) -> Optional[str]:
        """Get entered description.

        Returns:
            Description string, or None if empty
        """
        if not self._description_edit:
            return None

        description = self._description_edit.toPlainText().strip()
        return description if description else None

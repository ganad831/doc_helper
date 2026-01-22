"""Add Entity Dialog (Phase 2 Step 2).

Dialog for creating new entity definitions.
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QLabel,
    QWidget,
)
from PyQt6.QtCore import Qt


class AddEntityDialog(QDialog):
    """Dialog for adding a new entity to the schema.

    Phase 2 Step 2 Scope:
    - Simple form with: entity ID, name key, description key, root flag
    - Basic validation (non-empty fields)
    - Returns entity data as dict

    NOT in Step 2:
    - Parent entity selection (simplified)
    - Display order customization
    - Relationship definitions

    Layout:
        Entity ID: [text input]
        Name Key: [text input]
        Description Key: [text input]
        Is Root Entity: [checkbox]

        [Cancel] [Create]
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Add Entity")
        self.setModal(True)
        self.resize(500, 300)

        # Result data (populated on accept)
        self.entity_data: Optional[dict] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            "Create a new entity in the schema. "
            "Entity ID should be lowercase with underscores (e.g., 'soil_sample')."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info)

        # Form layout
        form = QFormLayout()

        # Entity ID
        self._entity_id_input = QLineEdit()
        self._entity_id_input.setPlaceholderText("e.g., soil_sample")
        form.addRow("Entity ID*:", self._entity_id_input)

        # Name Key
        self._name_key_input = QLineEdit()
        self._name_key_input.setPlaceholderText("e.g., entity.soil_sample")
        form.addRow("Name Key*:", self._name_key_input)

        # Description Key
        self._description_key_input = QLineEdit()
        self._description_key_input.setPlaceholderText("e.g., entity.soil_sample.description")
        form.addRow("Description Key:", self._description_key_input)

        # Is Root Entity
        self._is_root_checkbox = QCheckBox("This is a root entity (top-level)")
        form.addRow("Root Entity:", self._is_root_checkbox)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        create_button = QPushButton("Create Entity")
        create_button.setDefault(True)
        create_button.clicked.connect(self._on_create_clicked)
        button_layout.addWidget(create_button)

        layout.addLayout(button_layout)

    def _on_create_clicked(self) -> None:
        """Handle create button click."""
        # Validate inputs
        entity_id = self._entity_id_input.text().strip()
        name_key = self._name_key_input.text().strip()
        description_key = self._description_key_input.text().strip()
        is_root = self._is_root_checkbox.isChecked()

        # Validation
        if not entity_id:
            QMessageBox.warning(self, "Validation Error", "Entity ID is required")
            self._entity_id_input.setFocus()
            return

        if not name_key:
            QMessageBox.warning(self, "Validation Error", "Name Key is required")
            self._name_key_input.setFocus()
            return

        # Validate entity_id format (lowercase, underscores, alphanumeric)
        if not entity_id.replace("_", "").isalnum():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Entity ID must contain only letters, numbers, and underscores",
            )
            self._entity_id_input.setFocus()
            return

        if entity_id[0].isdigit():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Entity ID cannot start with a number",
            )
            self._entity_id_input.setFocus()
            return

        # Store result
        self.entity_data = {
            "entity_id": entity_id,
            "name_key": name_key,
            "description_key": description_key if description_key else None,
            "is_root_entity": is_root,
            "parent_entity_id": None,  # Simplified for Phase 2 Step 2
        }

        self.accept()

    def get_entity_data(self) -> Optional[dict]:
        """Get entity data if dialog was accepted.

        Returns:
            Dict with entity data or None if cancelled
        """
        return self.entity_data

"""Edit Entity Dialog (Phase SD-3).

Dialog for editing existing entity definitions.

Phase SD-3 Scope:
- Edit entity metadata (name key, description key, root status)
- Entity ID is read-only (identity is immutable)
- Pre-populate with current values

NOT in scope:
- No domain layer changes
- No command changes
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QLabel,
    QWidget,
)


class EditEntityDialog(QDialog):
    """Dialog for editing an existing entity.

    Phase SD-3: Edit entity metadata.

    Layout:
        Entity ID: [read-only text]
        Name Key: [text input]
        Description Key: [text input]
        Is Root Entity: [checkbox]

        [Cancel] [Save Changes]
    """

    def __init__(
        self,
        entity_id: str,
        current_name_key: str,
        current_description_key: Optional[str],
        current_is_root: bool,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize dialog.

        Args:
            entity_id: Entity ID (read-only)
            current_name_key: Current name translation key
            current_description_key: Current description translation key
            current_is_root: Current root entity status
            parent: Parent widget
        """
        super().__init__(parent)
        self._entity_id = entity_id

        self.setWindowTitle(f"Edit Entity: {entity_id}")
        self.setModal(True)
        self.resize(500, 280)

        # Result data (populated on accept)
        self.entity_data: Optional[dict] = None

        # Build UI
        self._build_ui(
            current_name_key,
            current_description_key,
            current_is_root,
        )

    def _build_ui(
        self,
        current_name_key: str,
        current_description_key: Optional[str],
        current_is_root: bool,
    ) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            "Edit entity metadata. The entity ID cannot be changed."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info)

        # Form layout
        form = QFormLayout()

        # Entity ID (read-only)
        entity_id_display = QLineEdit(self._entity_id)
        entity_id_display.setReadOnly(True)
        entity_id_display.setStyleSheet(
            "background-color: #f0f0f0; color: #666;"
        )
        form.addRow("Entity ID:", entity_id_display)

        # Name Key
        self._name_key_input = QLineEdit()
        self._name_key_input.setText(current_name_key)
        self._name_key_input.setPlaceholderText("e.g., entity.soil_sample")
        form.addRow("Name Key*:", self._name_key_input)

        # Description Key
        self._description_key_input = QLineEdit()
        self._description_key_input.setText(current_description_key or "")
        self._description_key_input.setPlaceholderText(
            "e.g., entity.soil_sample.description"
        )
        form.addRow("Description Key:", self._description_key_input)

        # Is Root Entity
        self._is_root_checkbox = QCheckBox("This is a root entity (top-level)")
        self._is_root_checkbox.setChecked(current_is_root)
        form.addRow("Root Entity:", self._is_root_checkbox)

        layout.addLayout(form)

        # Stretch to push buttons to bottom
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save Changes")
        save_button.setDefault(True)
        save_button.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        # Validate inputs
        name_key = self._name_key_input.text().strip()
        description_key = self._description_key_input.text().strip()
        is_root = self._is_root_checkbox.isChecked()

        # Validation
        if not name_key:
            QMessageBox.warning(self, "Validation Error", "Name Key is required")
            self._name_key_input.setFocus()
            return

        # Store result
        self.entity_data = {
            "entity_id": self._entity_id,
            "name_key": name_key,
            "description_key": description_key if description_key else None,
            "is_root_entity": is_root,
        }

        self.accept()

    def get_entity_data(self) -> Optional[dict]:
        """Get entity data if dialog was accepted.

        Returns:
            Dict with entity data or None if cancelled
        """
        return self.entity_data

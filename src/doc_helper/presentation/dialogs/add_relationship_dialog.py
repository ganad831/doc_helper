"""Add Relationship Dialog (Phase 6B - ADR-022).

Dialog for creating new relationship definitions.
Relationships are ADD-ONLY and cannot be edited or deleted.
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt


class AddRelationshipDialog(QDialog):
    """Dialog for adding a new relationship to the schema.

    Phase 6B (ADR-022):
    - ADD-ONLY semantics - relationships cannot be updated or deleted
    - Source and target entity selection from existing entities
    - Relationship type selection (CONTAINS, REFERENCES, ASSOCIATES)
    - Translation keys for name, description, and inverse name

    Layout:
        Source Entity: [dropdown]
        Target Entity: [dropdown]
        Relationship Type: [dropdown]
        Relationship ID: [text input] (auto-generated suggestion)
        Name Key: [text input]
        Description Key: [text input] (optional)
        Inverse Name Key: [text input] (optional)

        [Warning: Relationships are immutable]
        [Cancel] [Create Relationship]
    """

    # Valid relationship types per ADR-022
    RELATIONSHIP_TYPES = [
        ("CONTAINS", "Contains - Parent-child relationship (cascading)"),
        ("REFERENCES", "References - Non-owning reference to another entity"),
        ("ASSOCIATES", "Associates - Bidirectional peer relationship"),
    ]

    def __init__(
        self,
        entities: tuple[tuple[str, str], ...],
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize dialog.

        Args:
            entities: Tuple of (entity_id, entity_name) pairs for dropdowns
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Add Relationship")
        self.setModal(True)
        self.resize(550, 450)

        # Input data
        self._entities = entities

        # Result data (populated on accept)
        self.relationship_data: Optional[dict] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            "Define a relationship between two entities. "
            "Relationships describe how entities are connected in your schema."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info)

        # Warning about immutability (Phase 6B - ADD-ONLY)
        warning = QLabel(
            "Note: Relationships are immutable once created. "
            "They cannot be edited or deleted after creation."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "color: #b45309; "
            "background-color: #fef3c7; "
            "border: 1px solid #fcd34d; "
            "border-radius: 4px; "
            "padding: 8px; "
            "margin: 5px 0;"
        )
        layout.addWidget(warning)

        # Form layout
        form = QFormLayout()

        # Source Entity dropdown
        self._source_combo = QComboBox()
        self._source_combo.addItem("-- Select Source Entity --", "")
        for entity_id, entity_name in self._entities:
            self._source_combo.addItem(f"{entity_name} ({entity_id})", entity_id)
        self._source_combo.currentIndexChanged.connect(self._on_entity_changed)
        form.addRow("Source Entity*:", self._source_combo)

        # Target Entity dropdown
        self._target_combo = QComboBox()
        self._target_combo.addItem("-- Select Target Entity --", "")
        for entity_id, entity_name in self._entities:
            self._target_combo.addItem(f"{entity_name} ({entity_id})", entity_id)
        self._target_combo.currentIndexChanged.connect(self._on_entity_changed)
        form.addRow("Target Entity*:", self._target_combo)

        # Relationship Type dropdown
        self._type_combo = QComboBox()
        type_tooltips = {
            "CONTAINS": "Parent-child ownership. Deleting parent deletes children.",
            "REFERENCES": "Non-owning link. Referenced entity exists independently.",
            "ASSOCIATES": "Peer connection. Both entities are equal partners.",
        }
        for type_value, type_desc in self.RELATIONSHIP_TYPES:
            self._type_combo.addItem(type_desc, type_value)
            index = self._type_combo.count() - 1
            self._type_combo.setItemData(
                index, type_tooltips.get(type_value, ""), Qt.ItemDataRole.ToolTipRole
            )
        self._type_combo.currentIndexChanged.connect(self._on_entity_changed)
        form.addRow("Relationship Type*:", self._type_combo)

        # Relationship ID (auto-generated suggestion)
        self._relationship_id_input = QLineEdit()
        self._relationship_id_input.setPlaceholderText("e.g., project_contains_boreholes")
        form.addRow("Relationship ID*:", self._relationship_id_input)

        # Name Key
        self._name_key_input = QLineEdit()
        self._name_key_input.setPlaceholderText("e.g., relationship.project_boreholes")
        form.addRow("Name Key*:", self._name_key_input)

        # Description Key (optional)
        self._description_key_input = QLineEdit()
        self._description_key_input.setPlaceholderText(
            "e.g., relationship.project_boreholes.description"
        )
        form.addRow("Description Key:", self._description_key_input)

        # Inverse Name Key (optional)
        self._inverse_name_key_input = QLineEdit()
        self._inverse_name_key_input.setPlaceholderText(
            "e.g., relationship.borehole_project"
        )
        form.addRow("Inverse Name Key:", self._inverse_name_key_input)

        layout.addLayout(form)

        # Relationship type explanations
        type_info = QLabel(
            "<b>Relationship Types:</b><br/>"
            "<b>CONTAINS</b> - Parent owns children (e.g., Project contains Boreholes)<br/>"
            "<b>REFERENCES</b> - Non-owning link (e.g., Sample references Lab)<br/>"
            "<b>ASSOCIATES</b> - Peer connection (e.g., Document associates Photos)"
        )
        type_info.setWordWrap(True)
        type_info.setStyleSheet(
            "color: #4a5568; "
            "background-color: #edf2f7; "
            "border-radius: 4px; "
            "padding: 8px; "
            "margin-top: 10px; "
            "font-size: 9pt;"
        )
        layout.addWidget(type_info)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        create_button = QPushButton("Create Relationship")
        create_button.setDefault(True)
        create_button.clicked.connect(self._on_create_clicked)
        button_layout.addWidget(create_button)

        layout.addLayout(button_layout)

    def _on_entity_changed(self) -> None:
        """Handle entity selection change - auto-generate ID suggestion."""
        source_id = self._source_combo.currentData()
        target_id = self._target_combo.currentData()
        rel_type = self._type_combo.currentData()

        if source_id and target_id and rel_type:
            # Auto-generate relationship ID suggestion
            type_verb = rel_type.lower()  # contains, references, associates
            suggested_id = f"{source_id}_{type_verb}_{target_id}"

            # Only update if user hasn't entered a custom ID
            if not self._relationship_id_input.text().strip():
                self._relationship_id_input.setText(suggested_id)

            # Also suggest name key
            if not self._name_key_input.text().strip():
                self._name_key_input.setText(f"relationship.{source_id}_{target_id}")

    def _on_create_clicked(self) -> None:
        """Handle create button click."""
        # Get values
        source_id = self._source_combo.currentData()
        target_id = self._target_combo.currentData()
        rel_type = self._type_combo.currentData()
        relationship_id = self._relationship_id_input.text().strip()
        name_key = self._name_key_input.text().strip()
        description_key = self._description_key_input.text().strip()
        inverse_name_key = self._inverse_name_key_input.text().strip()

        # Validation
        if not source_id:
            QMessageBox.warning(self, "Validation Error", "Please select a source entity")
            self._source_combo.setFocus()
            return

        if not target_id:
            QMessageBox.warning(self, "Validation Error", "Please select a target entity")
            self._target_combo.setFocus()
            return

        if source_id == target_id:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Source and target entity must be different.\n"
                "A relationship cannot point to the same entity.",
            )
            self._target_combo.setFocus()
            return

        if not relationship_id:
            QMessageBox.warning(self, "Validation Error", "Relationship ID is required")
            self._relationship_id_input.setFocus()
            return

        if not name_key:
            QMessageBox.warning(self, "Validation Error", "Name Key is required")
            self._name_key_input.setFocus()
            return

        # Validate relationship_id format (lowercase, underscores, hyphens, alphanumeric)
        import re
        if not re.match(r"^[a-z][a-z0-9_-]*$", relationship_id):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Relationship ID must:\n"
                "- Start with a lowercase letter\n"
                "- Contain only lowercase letters, numbers, underscores, or hyphens",
            )
            self._relationship_id_input.setFocus()
            return

        # Store result
        self.relationship_data = {
            "relationship_id": relationship_id,
            "source_entity_id": source_id,
            "target_entity_id": target_id,
            "relationship_type": rel_type,
            "name_key": name_key,
            "description_key": description_key if description_key else None,
            "inverse_name_key": inverse_name_key if inverse_name_key else None,
        }

        self.accept()

    def get_relationship_data(self) -> Optional[dict]:
        """Get relationship data if dialog was accepted.

        Returns:
            Dict with relationship data or None if cancelled
        """
        return self.relationship_data

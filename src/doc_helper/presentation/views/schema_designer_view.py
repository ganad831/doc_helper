"""Schema Designer View (Phase 2, Step 1: READ-ONLY).

UI component for viewing schema definitions.
Displays entities, fields, and validation rules in a three-panel layout.

Phase 2 Step 1 Scope:
- READ-ONLY display
- Entity list panel
- Field list panel for selected entity
- Validation rules panel for selected field
- Selection navigation between panels

NOT in Step 1:
- No create/edit/delete buttons
- No export functionality
- No relationships display
- No formulas/controls/output mappings display
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QWidget,
    QPushButton,
    QMessageBox,
)

from doc_helper.presentation.viewmodels.schema_designer_viewmodel import (
    SchemaDesignerViewModel,
)
from doc_helper.presentation.views.base_view import BaseView


class SchemaDesignerView(BaseView):
    """View for Schema Designer (READ-ONLY).

    Layout:
        ┌────────────────────────────────────────────────┐
        │  Schema Designer (Read-Only)                   │
        ├────────────────┬────────────────┬──────────────┤
        │ Entities       │ Fields         │ Validation   │
        │                │                │ Rules        │
        │ [Entity 1]     │ [Field 1]      │ [Rule 1]     │
        │ [Entity 2]     │ [Field 2]      │ [Rule 2]     │
        │ [Entity 3]     │ [Field 3]      │              │
        │                │                │              │
        └────────────────┴────────────────┴──────────────┘

    Interactions:
    - Click entity → display its fields in middle panel
    - Click field → display its validation rules in right panel

    Design:
    - Three-panel splitter layout (resizable)
    - No edit controls (read-only)
    - Clear visual selection feedback
    """

    def __init__(
        self,
        viewmodel: SchemaDesignerViewModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize Schema Designer View.

        Args:
            viewmodel: ViewModel managing presentation state
            parent: Parent widget (None for standalone dialog)
        """
        super().__init__(parent)
        self._viewmodel = viewmodel

        # UI Components (created in _build_ui)
        self._entity_list: Optional[QListWidget] = None
        self._field_list: Optional[QListWidget] = None
        self._validation_list: Optional[QListWidget] = None

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Create dialog
        dialog = QDialog(self._parent)
        dialog.setWindowTitle("Schema Designer (Read-Only)")
        dialog.resize(1200, 600)

        # Main layout
        main_layout = QVBoxLayout(dialog)

        # Title label
        title_label = QLabel("Schema Designer - View Schema Definitions")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title_label)

        # Info label
        info_label = QLabel(
            "Read-only view of schema. Select an entity to view its fields, "
            "then select a field to view its validation rules."
        )
        info_label.setStyleSheet("color: gray; padding: 5px;")
        main_layout.addWidget(info_label)

        # Create three-panel splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Entity list
        entity_panel = self._create_entity_panel()
        splitter.addWidget(entity_panel)

        # Middle panel: Field list
        field_panel = self._create_field_panel()
        splitter.addWidget(field_panel)

        # Right panel: Validation rules
        validation_panel = self._create_validation_panel()
        splitter.addWidget(validation_panel)

        # Set initial splitter sizes (equal distribution)
        splitter.setSizes([400, 400, 400])

        main_layout.addWidget(splitter)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        button_layout.addWidget(close_button)

        main_layout.addLayout(button_layout)

        self._root = dialog

        # Subscribe to ViewModel changes
        self._viewmodel.subscribe("entities", self._on_entities_changed)
        self._viewmodel.subscribe("fields", self._on_fields_changed)
        self._viewmodel.subscribe("validation_rules", self._on_validation_rules_changed)
        self._viewmodel.subscribe("error_message", self._on_error_changed)

        # Load entities
        self._load_entities()

    def _create_entity_panel(self) -> QWidget:
        """Create the entity list panel.

        Returns:
            Widget containing entity list
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Panel title
        title = QLabel("Entities")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        layout.addWidget(title)

        # Entity list
        self._entity_list = QListWidget()
        self._entity_list.currentItemChanged.connect(self._on_entity_selected)
        layout.addWidget(self._entity_list)

        return panel

    def _create_field_panel(self) -> QWidget:
        """Create the field list panel.

        Returns:
            Widget containing field list
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Panel title
        title = QLabel("Fields")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        layout.addWidget(title)

        # Info label (shows when no entity selected)
        info = QLabel("Select an entity to view its fields")
        info.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        # Field list
        self._field_list = QListWidget()
        self._field_list.currentItemChanged.connect(self._on_field_selected)
        self._field_list.setVisible(False)  # Hidden until entity selected
        layout.addWidget(self._field_list)

        return panel

    def _create_validation_panel(self) -> QWidget:
        """Create the validation rules panel.

        Returns:
            Widget containing validation rules list
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Panel title
        title = QLabel("Validation Rules")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        layout.addWidget(title)

        # Info label (shows when no field selected)
        info = QLabel("Select a field to view its validation rules")
        info.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        # Validation rules list
        self._validation_list = QListWidget()
        self._validation_list.setVisible(False)  # Hidden until field selected
        layout.addWidget(self._validation_list)

        return panel

    # -------------------------------------------------------------------------
    # Event Handlers (User Interactions)
    # -------------------------------------------------------------------------

    def _on_entity_selected(
        self,
        current: Optional[QListWidgetItem],
        previous: Optional[QListWidgetItem],
    ) -> None:
        """Handle entity selection.

        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if current:
            entity_id = current.data(Qt.ItemDataRole.UserRole)
            self._viewmodel.select_entity(entity_id)

    def _on_field_selected(
        self,
        current: Optional[QListWidgetItem],
        previous: Optional[QListWidgetItem],
    ) -> None:
        """Handle field selection.

        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if current:
            field_id = current.data(Qt.ItemDataRole.UserRole)
            self._viewmodel.select_field(field_id)

    # -------------------------------------------------------------------------
    # ViewModel Change Handlers
    # -------------------------------------------------------------------------

    def _on_entities_changed(self) -> None:
        """Handle entities list change."""
        self._entity_list.clear()

        for entity_dto in self._viewmodel.entities:
            # Create list item
            item = QListWidgetItem(entity_dto.name)
            item.setData(Qt.ItemDataRole.UserRole, entity_dto.id)

            # Add badge for root entity
            if entity_dto.is_root_entity:
                item.setText(f"{entity_dto.name} (Root)")

            # Add field count
            item.setToolTip(
                f"{entity_dto.name}\n"
                f"Fields: {entity_dto.field_count}\n"
                f"{'Root entity' if entity_dto.is_root_entity else 'Child entity'}"
            )

            self._entity_list.addItem(item)

    def _on_fields_changed(self) -> None:
        """Handle fields list change."""
        self._field_list.clear()

        fields = self._viewmodel.fields
        if not fields:
            self._field_list.setVisible(False)
            return

        self._field_list.setVisible(True)

        for field_dto in fields:
            # Create list item
            item_text = f"{field_dto.label} ({field_dto.field_type})"
            if field_dto.required:
                item_text += " *"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, field_dto.id)

            # Add tooltip with field details
            tooltip_parts = [
                f"Label: {field_dto.label}",
                f"Type: {field_dto.field_type}",
                f"Required: {'Yes' if field_dto.required else 'No'}",
            ]

            if field_dto.help_text:
                tooltip_parts.append(f"Help: {field_dto.help_text}")

            if field_dto.default_value:
                tooltip_parts.append(f"Default: {field_dto.default_value}")

            if field_dto.is_calculated:
                tooltip_parts.append("Calculated field")

            item.setToolTip("\n".join(tooltip_parts))

            self._field_list.addItem(item)

    def _on_validation_rules_changed(self) -> None:
        """Handle validation rules list change."""
        self._validation_list.clear()

        rules = self._viewmodel.validation_rules
        if not rules:
            self._validation_list.setVisible(False)
            return

        self._validation_list.setVisible(True)

        for rule_text in rules:
            item = QListWidgetItem(rule_text)
            self._validation_list.addItem(item)

        # Show message if no rules
        if not rules:
            item = QListWidgetItem("No validation rules defined")
            item.setForeground(Qt.GlobalColor.gray)
            self._validation_list.addItem(item)

    def _on_error_changed(self) -> None:
        """Handle error message change."""
        error = self._viewmodel.error_message
        if error:
            QMessageBox.critical(self._root, "Error Loading Schema", error)

    # -------------------------------------------------------------------------
    # Commands
    # -------------------------------------------------------------------------

    def _load_entities(self) -> None:
        """Load entities from repository."""
        success = self._viewmodel.load_entities()
        if not success:
            QMessageBox.critical(
                self._root,
                "Error",
                "Failed to load schema entities. Check error message.",
            )

    def dispose(self) -> None:
        """Clean up resources."""
        # Unsubscribe from ViewModel
        if self._viewmodel:
            self._viewmodel.dispose()

        super().dispose()

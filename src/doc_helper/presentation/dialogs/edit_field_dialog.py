"""Edit Field Dialog (Phase SD-4, Phase F-14).

Dialog for editing existing field definitions.

Phase SD-4 Scope:
- Edit field metadata (label key, help text key, required, default value)
- Edit type-specific properties (formula, lookup, child entity)
- Field ID and Field Type are read-only (immutable)
- Pre-populate with current values

Phase F-14 Scope:
- Option management for choice fields (DROPDOWN, RADIO)
- Add, Edit, Delete, Reorder options
- Options persist via ViewModel callbacks

NOT in scope:
- Field type changes (immutable per Decision 1)
- Constraint editing (separate dialog)
"""

from typing import Callable, Optional

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto.export_dto import FieldOptionExportDTO
from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.presentation.utils.field_type_utils import normalize_field_type


class EditFieldDialog(QDialog):
    """Dialog for editing an existing field.

    Phase SD-4: Edit field metadata.

    Layout:
        Entity ID: [read-only text]
        Field ID: [read-only text]
        Field Type: [read-only text]
        Label Key: [text input]
        Help Text Key: [text input]
        Required: [checkbox]
        Default Value: [text input]

        --- Type-specific (shown conditionally) ---
        Formula: [text input] (CALCULATED only)
        Lookup Entity: [dropdown] (LOOKUP only)
        Lookup Display Field: [text input] (LOOKUP only)
        Child Entity: [dropdown] (TABLE only)

        [Cancel] [Save Changes]
    """

    def __init__(
        self,
        entity_id: str,
        field_id: str,
        field_type: str,
        current_label_key: str,
        current_help_text_key: Optional[str],
        current_required: bool,
        current_default_value: Optional[str],
        current_formula: Optional[str] = None,
        current_lookup_entity_id: Optional[str] = None,
        current_lookup_display_field: Optional[str] = None,
        current_child_entity_id: Optional[str] = None,
        available_entities: Optional[tuple[tuple[str, str], ...]] = None,
        get_valid_display_fields: Optional[Callable[[str], tuple[tuple[str, str], ...]]] = None,
        current_options: Optional[tuple[FieldOptionExportDTO, ...]] = None,
        on_add_option: Optional[Callable[[str, str], OperationResult]] = None,
        on_update_option: Optional[Callable[[str, str], OperationResult]] = None,
        on_delete_option: Optional[Callable[[str], OperationResult]] = None,
        on_reorder_options: Optional[Callable[[list[str]], OperationResult]] = None,
        get_options: Optional[Callable[[], tuple[FieldOptionExportDTO, ...]]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize dialog.

        Args:
            entity_id: Parent entity ID (read-only)
            field_id: Field ID (read-only)
            field_type: Field type (read-only)
            current_label_key: Current label translation key
            current_help_text_key: Current help text translation key
            current_required: Current required flag
            current_default_value: Current default value
            current_formula: Current formula (CALCULATED fields)
            current_lookup_entity_id: Current lookup entity (LOOKUP fields)
            current_lookup_display_field: Current lookup display field (LOOKUP fields)
            current_child_entity_id: Current child entity (TABLE fields)
            available_entities: List of (entity_id, entity_name) for dropdowns
            get_valid_display_fields: Callback to get valid display fields for an entity.
                Takes entity_id, returns tuple of (field_id, field_label).
                Used to populate the lookup display field dropdown with only valid types.
            current_options: Current field options (DROPDOWN/RADIO fields)
            on_add_option: Callback to add option (value, label_key) -> Result
            on_update_option: Callback to update option (value, new_label_key) -> Result
            on_delete_option: Callback to delete option (value) -> Result
            on_reorder_options: Callback to reorder options (new_order) -> Result
            get_options: Callback to get current options from ViewModel
            parent: Parent widget
        """
        super().__init__(parent)
        self._entity_id = entity_id
        self._field_id = field_id
        self._field_type = normalize_field_type(field_type)  # Normalize to lowercase via FieldType
        self._available_entities = available_entities or ()
        self._get_valid_display_fields = get_valid_display_fields
        self._current_options = current_options or ()
        self._on_add_option = on_add_option
        self._on_update_option = on_update_option
        self._on_delete_option = on_delete_option
        self._on_reorder_options = on_reorder_options
        self._get_options = get_options

        self.setWindowTitle(f"Edit Field: {field_id}")
        self.setModal(True)
        self.resize(550, 500)

        # Result data (populated on accept)
        self.field_data: Optional[dict] = None

        # Build UI
        self._build_ui(
            current_label_key,
            current_help_text_key,
            current_required,
            current_default_value,
            current_formula,
            current_lookup_entity_id,
            current_lookup_display_field,
            current_child_entity_id,
        )

    def _build_ui(
        self,
        current_label_key: str,
        current_help_text_key: Optional[str],
        current_required: bool,
        current_default_value: Optional[str],
        current_formula: Optional[str],
        current_lookup_entity_id: Optional[str],
        current_lookup_display_field: Optional[str],
        current_child_entity_id: Optional[str],
    ) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            "Edit field metadata. Field ID and Type cannot be changed."
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

        # Field ID (read-only)
        field_id_display = QLineEdit(self._field_id)
        field_id_display.setReadOnly(True)
        field_id_display.setStyleSheet(
            "background-color: #f0f0f0; color: #666;"
        )
        form.addRow("Field ID:", field_id_display)

        # Field Type (read-only) - display uppercase for user-friendliness
        field_type_display = QLineEdit(self._field_type.upper())
        field_type_display.setReadOnly(True)
        field_type_display.setStyleSheet(
            "background-color: #f0f0f0; color: #666;"
        )
        form.addRow("Field Type:", field_type_display)

        # Label Key
        self._label_key_input = QLineEdit()
        self._label_key_input.setText(current_label_key)
        self._label_key_input.setPlaceholderText("e.g., field.sample_depth")
        form.addRow("Label Key*:", self._label_key_input)

        # Help Text Key
        self._help_text_key_input = QLineEdit()
        self._help_text_key_input.setText(current_help_text_key or "")
        self._help_text_key_input.setPlaceholderText(
            "e.g., field.sample_depth.help"
        )
        form.addRow("Help Text Key:", self._help_text_key_input)

        # Required
        # INVARIANT: CALCULATED fields cannot be required - disable checkbox
        self._required_checkbox = QCheckBox("Field is required")
        if self._field_type == "calculated":
            self._required_checkbox.setChecked(False)
            self._required_checkbox.setEnabled(False)
            self._required_checkbox.setToolTip(
                "CALCULATED fields cannot be required. "
                "They derive their values from formulas."
            )
        else:
            self._required_checkbox.setChecked(current_required)
        form.addRow("Required:", self._required_checkbox)

        # Default Value
        self._default_value_input = QLineEdit()
        self._default_value_input.setText(current_default_value or "")
        self._default_value_input.setPlaceholderText("Optional default value")
        form.addRow("Default Value:", self._default_value_input)

        layout.addLayout(form)

        # Type-specific section
        self._add_type_specific_fields(
            layout,
            current_formula,
            current_lookup_entity_id,
            current_lookup_display_field,
            current_child_entity_id,
        )

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

    def _add_type_specific_fields(
        self,
        layout: QVBoxLayout,
        current_formula: Optional[str],
        current_lookup_entity_id: Optional[str],
        current_lookup_display_field: Optional[str],
        current_child_entity_id: Optional[str],
    ) -> None:
        """Add type-specific fields based on field type."""
        # Initialize optional attributes
        self._formula_input: Optional[QLineEdit] = None
        self._lookup_entity_combo: Optional[QComboBox] = None
        self._lookup_display_field_combo: Optional[QComboBox] = None
        self._child_entity_combo: Optional[QComboBox] = None
        self._options_list: Optional[QListWidget] = None

        if self._field_type in ("dropdown", "radio"):
            # Options section for choice fields
            self._add_options_section(layout)

        elif self._field_type == "calculated":
            # Formula section
            formula_form = QFormLayout()
            formula_label = QLabel("--- CALCULATED Field Properties ---")
            formula_label.setStyleSheet("color: #4a5568; font-weight: bold; margin-top: 10px;")
            layout.addWidget(formula_label)

            self._formula_input = QLineEdit()
            self._formula_input.setText(current_formula or "")
            self._formula_input.setPlaceholderText("e.g., {{field1}} + {{field2}}")
            formula_form.addRow("Formula:", self._formula_input)
            layout.addLayout(formula_form)

        elif self._field_type == "lookup":
            # Lookup section
            lookup_form = QFormLayout()
            lookup_label = QLabel("--- LOOKUP Field Properties ---")
            lookup_label.setStyleSheet("color: #4a5568; font-weight: bold; margin-top: 10px;")
            layout.addWidget(lookup_label)

            self._lookup_entity_combo = QComboBox()
            self._lookup_entity_combo.addItem("(None)", "")
            for eid, ename in self._available_entities:
                # Filter out current entity - UX safety only (enforcement is at UseCases layer)
                if eid == self._entity_id:
                    continue
                self._lookup_entity_combo.addItem(f"{ename} ({eid})", eid)
            # Connect to update display field dropdown when entity changes
            self._lookup_entity_combo.currentIndexChanged.connect(
                self._on_lookup_entity_changed
            )
            # Set current selection
            if current_lookup_entity_id:
                index = self._lookup_entity_combo.findData(current_lookup_entity_id)
                if index >= 0:
                    self._lookup_entity_combo.setCurrentIndex(index)
            lookup_form.addRow("Lookup Entity:", self._lookup_entity_combo)

            self._lookup_display_field_combo = QComboBox()
            self._lookup_display_field_combo.addItem("(None)", "")
            self._lookup_display_field_combo.setToolTip(
                "Field from the lookup entity to display (optional).\n"
                "Only user-readable fields are shown (not CALCULATED, TABLE, FILE, IMAGE)."
            )
            # Populate display field dropdown based on current lookup entity
            self._populate_display_field_combo(current_lookup_entity_id)
            # Set current selection
            if current_lookup_display_field:
                index = self._lookup_display_field_combo.findData(current_lookup_display_field)
                if index >= 0:
                    self._lookup_display_field_combo.setCurrentIndex(index)
            lookup_form.addRow("Display Field:", self._lookup_display_field_combo)
            layout.addLayout(lookup_form)

        elif self._field_type == "table":
            # Table section
            table_form = QFormLayout()
            table_label = QLabel("--- TABLE Field Properties ---")
            table_label.setStyleSheet("color: #4a5568; font-weight: bold; margin-top: 10px;")
            layout.addWidget(table_label)

            self._child_entity_combo = QComboBox()
            self._child_entity_combo.addItem("(None)", "")
            for entity_id, entity_name in self._available_entities:
                self._child_entity_combo.addItem(f"{entity_name} ({entity_id})", entity_id)
            # Set current selection
            if current_child_entity_id:
                index = self._child_entity_combo.findData(current_child_entity_id)
                if index >= 0:
                    self._child_entity_combo.setCurrentIndex(index)
            table_form.addRow("Child Entity:", self._child_entity_combo)
            layout.addLayout(table_form)

    def _on_lookup_entity_changed(self, index: int) -> None:
        """Handle lookup entity selection change.

        Updates the display field dropdown with valid fields from the selected entity.
        Only fields with user-readable types are shown (not CALCULATED, TABLE, FILE, IMAGE).
        """
        if not self._lookup_display_field_combo:
            return

        # Get selected entity ID
        if not self._lookup_entity_combo:
            return

        selected_entity_id = self._lookup_entity_combo.currentData()
        self._populate_display_field_combo(selected_entity_id)

    def _populate_display_field_combo(self, entity_id: str | None) -> None:
        """Populate the display field combo with valid fields from an entity.

        Args:
            entity_id: The entity to get valid display fields from, or None to clear.
        """
        if not self._lookup_display_field_combo:
            return

        # Clear existing items (keep "(None)" option)
        self._lookup_display_field_combo.clear()
        self._lookup_display_field_combo.addItem("(None)", "")

        if not entity_id:
            return

        # Get valid display fields via callback
        if self._get_valid_display_fields:
            valid_fields = self._get_valid_display_fields(entity_id)
            for field_id, field_label in valid_fields:
                self._lookup_display_field_combo.addItem(
                    f"{field_label} ({field_id})", field_id
                )

    def _add_options_section(self, layout: QVBoxLayout) -> None:
        """Add options management section for choice fields (DROPDOWN, RADIO).

        Phase F-14: Option management UI.
        """
        # Section header - display uppercase for user-friendliness
        options_label = QLabel(f"--- {self._field_type.upper()} Field Options ---")
        options_label.setStyleSheet(
            "color: #4a5568; font-weight: bold; margin-top: 10px;"
        )
        layout.addWidget(options_label)

        # Horizontal layout for list and buttons
        options_layout = QHBoxLayout()

        # Options list widget
        self._options_list = QListWidget()
        self._options_list.setMinimumHeight(120)
        self._refresh_options_list()
        options_layout.addWidget(self._options_list, stretch=1)

        # Buttons layout (vertical)
        buttons_layout = QVBoxLayout()

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._on_add_option_clicked)
        buttons_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._on_edit_option_clicked)
        buttons_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._on_delete_option_clicked)
        buttons_layout.addWidget(delete_btn)

        buttons_layout.addSpacing(10)

        move_up_btn = QPushButton("Move Up")
        move_up_btn.clicked.connect(self._on_move_up_clicked)
        buttons_layout.addWidget(move_up_btn)

        move_down_btn = QPushButton("Move Down")
        move_down_btn.clicked.connect(self._on_move_down_clicked)
        buttons_layout.addWidget(move_down_btn)

        buttons_layout.addStretch()
        options_layout.addLayout(buttons_layout)

        layout.addLayout(options_layout)

    def _refresh_options_list(self) -> None:
        """Refresh the options list widget from current options."""
        if self._options_list is None:
            return

        self._options_list.clear()
        for option in self._current_options:
            item = QListWidgetItem(f"{option.value} - {option.label_key}")
            item.setData(256, option.value)  # Qt.ItemDataRole.UserRole = 256
            self._options_list.addItem(item)

    def _on_add_option_clicked(self) -> None:
        """Handle Add button click."""
        if self._on_add_option is None:
            QMessageBox.warning(
                self, "Not Available", "Option management is not available."
            )
            return

        # Get option value
        value, ok = QInputDialog.getText(
            self, "Add Option", "Option Value (identifier):"
        )
        if not ok or not value.strip():
            return

        # Get label key
        label_key, ok = QInputDialog.getText(
            self, "Add Option", "Label Key (translation key):"
        )
        if not ok or not label_key.strip():
            return

        result = self._on_add_option(value.strip(), label_key.strip())
        if result.success:
            # Reload options from ViewModel via refresh
            self._reload_options_from_callback()
        else:
            QMessageBox.warning(self, "Error", result.message or "Failed to add option")

    def _on_edit_option_clicked(self) -> None:
        """Handle Edit button click."""
        if self._options_list is None or self._on_update_option is None:
            return

        current_item = self._options_list.currentItem()
        if current_item is None:
            QMessageBox.information(self, "Select Option", "Please select an option to edit.")
            return

        option_value = current_item.data(256)  # Qt.ItemDataRole.UserRole

        # Find current label key
        current_label_key = ""
        for option in self._current_options:
            if option.value == option_value:
                current_label_key = option.label_key
                break

        # Get new label key
        new_label_key, ok = QInputDialog.getText(
            self,
            "Edit Option",
            f"New Label Key for '{option_value}':",
            text=current_label_key,
        )
        if not ok or not new_label_key.strip():
            return

        if new_label_key.strip() == current_label_key:
            return  # No change

        result = self._on_update_option(option_value, new_label_key.strip())
        if result.success:
            self._reload_options_from_callback()
        else:
            QMessageBox.warning(
                self, "Error", result.message or "Failed to update option"
            )

    def _on_delete_option_clicked(self) -> None:
        """Handle Delete button click."""
        if self._options_list is None or self._on_delete_option is None:
            return

        current_item = self._options_list.currentItem()
        if current_item is None:
            QMessageBox.information(
                self, "Select Option", "Please select an option to delete."
            )
            return

        option_value = current_item.data(256)  # Qt.ItemDataRole.UserRole

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete option '{option_value}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        result = self._on_delete_option(option_value)
        if result.success:
            self._reload_options_from_callback()
        else:
            QMessageBox.warning(
                self, "Error", result.message or "Failed to delete option"
            )

    def _on_move_up_clicked(self) -> None:
        """Handle Move Up button click."""
        if self._options_list is None or self._on_reorder_options is None:
            return

        current_row = self._options_list.currentRow()
        if current_row <= 0:
            return  # Already at top or nothing selected

        # Build new order
        new_order = [
            self._options_list.item(i).data(256)
            for i in range(self._options_list.count())
        ]
        # Swap with previous
        new_order[current_row], new_order[current_row - 1] = (
            new_order[current_row - 1],
            new_order[current_row],
        )

        result = self._on_reorder_options(new_order)
        if result.success:
            self._reload_options_from_callback()
            # Restore selection to moved item
            self._options_list.setCurrentRow(current_row - 1)
        else:
            QMessageBox.warning(
                self, "Error", result.message or "Failed to reorder options"
            )

    def _on_move_down_clicked(self) -> None:
        """Handle Move Down button click."""
        if self._options_list is None or self._on_reorder_options is None:
            return

        current_row = self._options_list.currentRow()
        if current_row < 0 or current_row >= self._options_list.count() - 1:
            return  # Already at bottom or nothing selected

        # Build new order
        new_order = [
            self._options_list.item(i).data(256)
            for i in range(self._options_list.count())
        ]
        # Swap with next
        new_order[current_row], new_order[current_row + 1] = (
            new_order[current_row + 1],
            new_order[current_row],
        )

        result = self._on_reorder_options(new_order)
        if result.success:
            self._reload_options_from_callback()
            # Restore selection to moved item
            self._options_list.setCurrentRow(current_row + 1)
        else:
            QMessageBox.warning(
                self, "Error", result.message or "Failed to reorder options"
            )

    def _reload_options_from_callback(self) -> None:
        """Reload options after a modification.

        Since callbacks persist changes to repository, we need to rebuild
        our local options list. Uses the get_options callback to fetch
        fresh data from the ViewModel.
        """
        if self._options_list is None:
            return

        # Fetch fresh options from ViewModel via callback
        if self._get_options is not None:
            self._current_options = self._get_options()
        self._refresh_options_list()

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        # Validate inputs
        label_key = self._label_key_input.text().strip()
        help_text_key = self._help_text_key_input.text().strip()
        required = self._required_checkbox.isChecked()
        default_value = self._default_value_input.text().strip()

        # Validation
        if not label_key:
            QMessageBox.warning(self, "Validation Error", "Label Key is required")
            self._label_key_input.setFocus()
            return

        # Store result
        self.field_data = {
            "entity_id": self._entity_id,
            "field_id": self._field_id,
            "label_key": label_key,
            "help_text_key": help_text_key if help_text_key else None,
            "required": required,
            "default_value": default_value if default_value else None,
        }

        # Add type-specific data
        if self._field_type == "calculated" and self._formula_input:
            formula = self._formula_input.text().strip()
            self.field_data["formula"] = formula if formula else None

        elif self._field_type == "lookup":
            # LOOKUP fields require lookup_entity_id
            if self._lookup_entity_combo:
                lookup_entity_id = self._lookup_entity_combo.currentData()
                if not lookup_entity_id:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "LOOKUP fields require a Lookup Entity.\n"
                        "Please select an entity to lookup values from.",
                    )
                    self._lookup_entity_combo.setFocus()
                    return  # Keep dialog open
                self.field_data["lookup_entity_id"] = lookup_entity_id
            if self._lookup_display_field_combo:
                lookup_display_field = self._lookup_display_field_combo.currentData()
                self.field_data["lookup_display_field"] = lookup_display_field if lookup_display_field else None

        elif self._field_type == "table" and self._child_entity_combo:
            child_entity_id = self._child_entity_combo.currentData()
            self.field_data["child_entity_id"] = child_entity_id if child_entity_id else None

        self.accept()

    def get_field_data(self) -> Optional[dict]:
        """Get field data if dialog was accepted.

        Returns:
            Dict with field data or None if cancelled
        """
        return self.field_data

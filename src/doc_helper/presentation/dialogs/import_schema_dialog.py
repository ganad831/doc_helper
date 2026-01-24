"""Import Schema Dialog (Phase SD-1).

Dialog for importing schema definitions from a JSON file.

Phase SD-1 Scope:
- File picker for import source
- Enforcement policy selection (STRICT, WARN, NONE)
- Identical action selection (SKIP, REPLACE)
- Force import checkbox
- Display compatibility analysis before import
- Display import warnings/errors after import

NOT in scope:
- No modification of ImportSchemaCommand
- No modification of SchemaComparisonService
- No modification of SchemaImportValidationService
- No domain layer changes
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto.import_dto import (
    EnforcementPolicy,
    IdenticalSchemaAction,
    ImportResult,
)


class ImportSchemaDialog(QDialog):
    """Dialog for importing schema from JSON file.

    Phase SD-1: Import UI for Schema Designer.
    Collects import parameters and displays results.

    Layout:
        Import from: [file path] [Browse...]
        Enforcement Policy: [dropdown]
        If Identical: [dropdown]
        [ ] Force import (ignore compatibility)

        [Compatibility Analysis - shown after file selected]

        [Import Result - shown after import]

        [Cancel] [Import]
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Import Schema")
        self.setModal(True)
        self.resize(650, 500)

        # Result data (populated on accept)
        self.import_params: Optional[dict] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            "Import a schema from a JSON file.\n"
            "This will replace all existing entities, fields, constraints, and relationships."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info)

        # Form layout
        form = QFormLayout()

        # File path with browse button
        file_layout = QHBoxLayout()
        self._file_path_input = QLineEdit()
        self._file_path_input.setPlaceholderText("Select JSON file to import...")
        self._file_path_input.setReadOnly(True)
        file_layout.addWidget(self._file_path_input)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._on_browse_clicked)
        file_layout.addWidget(browse_button)

        form.addRow("Import from*:", file_layout)

        # Enforcement Policy dropdown
        self._policy_combo = QComboBox()
        self._policy_combo.addItem("Strict - Block incompatible schemas", EnforcementPolicy.STRICT.value)
        self._policy_combo.addItem("Warn - Allow with warnings", EnforcementPolicy.WARN.value)
        self._policy_combo.addItem("None - No compatibility check", EnforcementPolicy.NONE.value)
        self._policy_combo.setToolTip(
            "STRICT: Import fails if schema is incompatible\n"
            "WARN: Import proceeds with warnings\n"
            "NONE: No compatibility checking"
        )
        form.addRow("Enforcement Policy:", self._policy_combo)

        # Identical Action dropdown
        self._identical_combo = QComboBox()
        self._identical_combo.addItem("Skip - Don't import if identical", IdenticalSchemaAction.SKIP.value)
        self._identical_combo.addItem("Replace - Import anyway", IdenticalSchemaAction.REPLACE.value)
        self._identical_combo.setToolTip(
            "SKIP: If schema is identical, do nothing\n"
            "REPLACE: Replace schema even if identical"
        )
        form.addRow("If Identical:", self._identical_combo)

        # Force checkbox
        self._force_checkbox = QCheckBox("Force import (ignore compatibility errors)")
        self._force_checkbox.setToolTip(
            "If checked, import will proceed even if schema is incompatible.\n"
            "WARNING: This may cause data loss or corruption."
        )
        form.addRow("", self._force_checkbox)

        layout.addLayout(form)

        # Warning about force import
        self._force_warning = QLabel(
            "Warning: Force import will replace the schema even if incompatible. "
            "Existing data may become invalid."
        )
        self._force_warning.setWordWrap(True)
        self._force_warning.setStyleSheet("color: #dc2626; padding: 5px; font-style: italic;")
        self._force_warning.setVisible(False)
        layout.addWidget(self._force_warning)

        # Connect force checkbox to show/hide warning
        self._force_checkbox.stateChanged.connect(self._on_force_changed)

        # Result display area (initially hidden)
        self._result_group = QGroupBox("Import Result")
        result_layout = QVBoxLayout(self._result_group)

        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMaximumHeight(180)
        result_layout.addWidget(self._result_text)

        self._result_group.setVisible(False)
        layout.addWidget(self._result_group)

        # Stretch to push buttons to bottom
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        self._import_button = QPushButton("Import Schema")
        self._import_button.setDefault(True)
        self._import_button.clicked.connect(self._on_import_clicked)
        button_layout.addWidget(self._import_button)

        layout.addLayout(button_layout)

    def _on_browse_clicked(self) -> None:
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Schema File",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            self._file_path_input.setText(file_path)

    def _on_force_changed(self, state: int) -> None:
        """Handle force checkbox state change."""
        self._force_warning.setVisible(state != 0)

    def _on_import_clicked(self) -> None:
        """Handle import button click."""
        # Validate file path
        file_path = self._file_path_input.text().strip()

        if not file_path:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select a JSON file to import",
            )
            return

        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            QMessageBox.warning(
                self,
                "Validation Error",
                f"File does not exist:\n{file_path}",
            )
            return

        if not path.is_file():
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Path is not a file:\n{file_path}",
            )
            return

        # Get selected options
        policy_value = self._policy_combo.currentData()
        identical_value = self._identical_combo.currentData()
        force = self._force_checkbox.isChecked()

        # Confirm force import if checked
        if force:
            confirm = QMessageBox.question(
                self,
                "Confirm Force Import",
                "You have selected 'Force import'. This will replace the schema "
                "even if it is incompatible with existing data.\n\n"
                "Are you sure you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        # Store import parameters
        self.import_params = {
            "file_path": path,
            "enforcement_policy": EnforcementPolicy(policy_value),
            "identical_action": IdenticalSchemaAction(identical_value),
            "force": force,
        }

        self.accept()

    def get_import_params(self) -> Optional[dict]:
        """Get import parameters if dialog was accepted.

        Returns:
            Dict with import parameters or None if cancelled
        """
        return self.import_params

    def show_import_result(self, result: ImportResult) -> None:
        """Display import result in the dialog.

        Called after import operation to show result details.

        Args:
            result: ImportResult from import operation
        """
        self._result_group.setVisible(True)

        if result.success:
            # Success message
            if result.was_skipped:
                message = "Import skipped - schema is identical to existing.\n"
                self._result_text.setStyleSheet("color: #2563eb;")  # Blue
            else:
                message = "Import completed successfully!\n\n"
                message += f"Entities: {result.entity_count}\n"
                message += f"Fields: {result.field_count}\n"
                message += f"Relationships: {result.relationship_count}\n"
                self._result_text.setStyleSheet("color: green;")

            # Include warnings if any
            if result.warnings:
                message += f"\nWarnings ({len(result.warnings)}):\n"
                for warning in result.warnings:
                    message += f"  - [{warning.category}] {warning.message}\n"
                self._result_text.setStyleSheet("color: #b45309;")  # Orange for warnings

            self._result_text.setPlainText(message)
        else:
            # Failure message
            message = "Import failed:\n\n"

            if result.error:
                message += f"{result.error}\n\n"

            if result.validation_errors:
                message += f"Validation Errors ({len(result.validation_errors)}):\n"
                for error in result.validation_errors:
                    location = f" at {error.location}" if error.location else ""
                    message += f"  - [{error.category}]{location}: {error.message}\n"

            self._result_text.setPlainText(message)
            self._result_text.setStyleSheet("color: red;")

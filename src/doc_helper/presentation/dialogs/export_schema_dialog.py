"""Export Schema Dialog (Phase 7).

Dialog for exporting schema definitions to a JSON file.

Phase 7 Scope:
- File picker for export destination
- Schema ID input (required)
- Version input (optional)
- Display export warnings after successful export
- Display error messages on failure

NOT in scope:
- No import functionality (Phase 8)
- No validation rule creation
- No edit/delete operations
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QLabel,
    QWidget,
    QFileDialog,
    QTextEdit,
    QGroupBox,
)
from PyQt6.QtCore import Qt


class ExportSchemaDialog(QDialog):
    """Dialog for exporting schema to JSON file.

    Phase 7: Export UI for Schema Designer.
    Calls existing ExportSchemaCommand through ViewModel.

    Layout:
        Schema ID: [text input]
        Version: [text input] (optional)
        Export to: [file path] [Browse...]

        [Export Warnings - shown after export]

        [Cancel] [Export]
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Export Schema")
        self.setModal(True)
        self.resize(600, 400)

        # Result data (populated on accept)
        self.export_data: Optional[dict] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            "Export the current schema to a JSON file.\n"
            "This exports entities, fields, constraints, and relationships."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info)

        # Form layout
        form = QFormLayout()

        # Schema ID
        self._schema_id_input = QLineEdit()
        self._schema_id_input.setPlaceholderText("e.g., soil_investigation")
        self._schema_id_input.setText("schema_export")  # Default value
        form.addRow("Schema ID*:", self._schema_id_input)

        # Version (optional)
        self._version_input = QLineEdit()
        self._version_input.setPlaceholderText("e.g., 1.0.0 (optional)")
        form.addRow("Version:", self._version_input)

        # File path with browse button
        file_layout = QHBoxLayout()
        self._file_path_input = QLineEdit()
        self._file_path_input.setPlaceholderText("Select export file location...")
        self._file_path_input.setReadOnly(True)
        file_layout.addWidget(self._file_path_input)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._on_browse_clicked)
        file_layout.addWidget(browse_button)

        form.addRow("Export to*:", file_layout)

        layout.addLayout(form)

        # Warning/result display area (initially hidden)
        self._result_group = QGroupBox("Export Result")
        result_layout = QVBoxLayout(self._result_group)

        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMaximumHeight(150)
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

        self._export_button = QPushButton("Export Schema")
        self._export_button.setDefault(True)
        self._export_button.clicked.connect(self._on_export_clicked)
        button_layout.addWidget(self._export_button)

        layout.addLayout(button_layout)

    def _on_browse_clicked(self) -> None:
        """Handle browse button click."""
        # Suggest default filename based on schema ID
        schema_id = self._schema_id_input.text().strip() or "schema_export"
        default_name = f"{schema_id}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Schema",
            default_name,
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            self._file_path_input.setText(file_path)

    def _on_export_clicked(self) -> None:
        """Handle export button click."""
        # Validate inputs
        schema_id = self._schema_id_input.text().strip()
        version = self._version_input.text().strip() or None
        file_path = self._file_path_input.text().strip()

        # Validation
        if not schema_id:
            QMessageBox.warning(self, "Validation Error", "Schema ID is required")
            self._schema_id_input.setFocus()
            return

        if not file_path:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select an export file location",
            )
            return

        # Validate schema_id format (lowercase, underscores, alphanumeric)
        if not schema_id.replace("_", "").isalnum():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Schema ID must contain only letters, numbers, and underscores",
            )
            self._schema_id_input.setFocus()
            return

        # Ensure .json extension
        if not file_path.lower().endswith(".json"):
            file_path += ".json"

        # Store result
        self.export_data = {
            "schema_id": schema_id,
            "version": version,
            "file_path": Path(file_path),
        }

        self.accept()

    def get_export_data(self) -> Optional[dict]:
        """Get export data if dialog was accepted.

        Returns:
            Dict with export parameters or None if cancelled
        """
        return self.export_data

    def show_export_result(
        self,
        success: bool,
        warnings: tuple = (),
        error: Optional[str] = None,
    ) -> None:
        """Display export result in the dialog.

        Called after export operation to show warnings or errors.

        Args:
            success: Whether export succeeded
            warnings: Tuple of warning messages
            error: Error message if failed
        """
        self._result_group.setVisible(True)

        if success:
            # Success with optional warnings
            if warnings:
                message = "Export completed with warnings:\n\n"
                for warning in warnings:
                    if hasattr(warning, "message"):
                        message += f"- {warning.message}\n"
                    else:
                        message += f"- {warning}\n"
                self._result_text.setPlainText(message)
                self._result_text.setStyleSheet("color: #b45309;")  # Orange for warnings
            else:
                self._result_text.setPlainText("Export completed successfully!")
                self._result_text.setStyleSheet("color: green;")
        else:
            # Failure
            self._result_text.setPlainText(f"Export failed:\n\n{error}")
            self._result_text.setStyleSheet("color: red;")

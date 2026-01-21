"""Import/Export dialog for project data interchange.

ADR-039: Import/Export Data Format
RULES (AGENT_RULES.md Section 3-4):
- Uses DTOs only (ImportResultDTO, ExportResultDTO)
- No domain objects in presentation
- File operations through commands
"""

from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from doc_helper.application.dto.import_export_dto import (
    ExportResultDTO,
    ImportResultDTO,
)


class ImportExportDialog(QDialog):
    """Import/Export dialog for project data interchange.

    ADR-039: Import/Export Data Format
    - Export: Serializes complete project to interchange format
    - Import: Creates new project from interchange format
    - Validation: Full validation before import
    - Human-readable format

    v1 Implementation:
    - Export to JSON format
    - Import from JSON format
    - Validation error display
    - Success/failure feedback
    - File picker for import/export

    v2+ Features (deferred):
    - Multiple format support (XML, CSV)
    - Export filtering (selective entities)
    - Incremental import
    - Template export (structure without data)
    - Cloud storage integration

    RULES (AGENT_RULES.md Section 3-4):
    - Uses ImportResultDTO and ExportResultDTO only (no domain objects)
    - Commands executed through callbacks
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        export_callback: Callable[[str], ExportResultDTO],
        import_callback: Callable[[str], ImportResultDTO],
        current_project_name: str,
    ) -> None:
        """Initialize import/export dialog.

        Args:
            parent: Parent widget
            export_callback: Callback to execute export (takes file_path, returns ExportResultDTO)
            import_callback: Callback to execute import (takes file_path, returns ImportResultDTO)
            current_project_name: Name of currently open project (for export default name)
        """
        super().__init__(parent)
        self._export_callback = export_callback
        self._import_callback = import_callback
        self._current_project_name = current_project_name

        # UI components
        self._export_path_input: Optional[QLineEdit] = None
        self._import_path_input: Optional[QLineEdit] = None
        self._result_text: Optional[QTextEdit] = None

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        self.setWindowTitle("Import/Export Project Data")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Export section
        export_group = self._build_export_section()
        main_layout.addWidget(export_group)

        main_layout.addSpacing(20)

        # Import section
        import_group = self._build_import_section()
        main_layout.addWidget(import_group)

        main_layout.addSpacing(20)

        # Result section
        result_group = self._build_result_section()
        main_layout.addWidget(result_group, 1)  # Stretch factor 1

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        main_layout.addWidget(button_box)

    def _build_export_section(self) -> QGroupBox:
        """Build export section UI.

        Returns:
            QGroupBox containing export controls
        """
        export_group = QGroupBox("Export Current Project")
        export_layout = QVBoxLayout()

        # Info label
        info_label = QLabel(
            "Export the current project to a human-readable JSON file.\n"
            "Includes all field values, entity instances, and metadata."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-style: italic;")
        export_layout.addWidget(info_label)

        # File path selection
        path_layout = QHBoxLayout()

        path_label = QLabel("Export to:")
        self._export_path_input = QLineEdit()
        self._export_path_input.setPlaceholderText("Select export file location...")
        self._export_path_input.setReadOnly(True)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._on_browse_export_path)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self._export_path_input, 1)  # Stretch factor 1
        path_layout.addWidget(browse_button)

        export_layout.addLayout(path_layout)

        # Export button
        export_button = QPushButton("Export Project")
        export_button.clicked.connect(self._on_export)
        export_layout.addWidget(export_button)

        export_group.setLayout(export_layout)
        return export_group

    def _build_import_section(self) -> QGroupBox:
        """Build import section UI.

        Returns:
            QGroupBox containing import controls
        """
        import_group = QGroupBox("Import Project")
        import_layout = QVBoxLayout()

        # Info label
        info_label = QLabel(
            "Import a project from a JSON file.\n"
            "Creates a new project (does not modify existing projects).\n"
            "All data is validated before import."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-style: italic;")
        import_layout.addWidget(info_label)

        # File path selection
        path_layout = QHBoxLayout()

        path_label = QLabel("Import from:")
        self._import_path_input = QLineEdit()
        self._import_path_input.setPlaceholderText("Select import file...")
        self._import_path_input.setReadOnly(True)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._on_browse_import_path)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self._import_path_input, 1)  # Stretch factor 1
        path_layout.addWidget(browse_button)

        import_layout.addLayout(path_layout)

        # Import button
        import_button = QPushButton("Import Project")
        import_button.clicked.connect(self._on_import)
        import_layout.addWidget(import_button)

        import_group.setLayout(import_layout)
        return import_group

    def _build_result_section(self) -> QGroupBox:
        """Build result section UI.

        Returns:
            QGroupBox containing result display
        """
        result_group = QGroupBox("Operation Result")
        result_layout = QVBoxLayout()

        # Result text area (read-only)
        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setPlaceholderText(
            "Import/Export results will be displayed here..."
        )
        result_layout.addWidget(self._result_text)

        result_group.setLayout(result_layout)
        return result_group

    def _on_browse_export_path(self) -> None:
        """Handle Export Browse button click."""
        # Suggest default filename based on current project name
        default_name = f"{self._current_project_name}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Project Data",
            default_name,
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path and self._export_path_input:
            self._export_path_input.setText(file_path)

    def _on_browse_import_path(self) -> None:
        """Handle Import Browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Project Data",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path and self._import_path_input:
            self._import_path_input.setText(file_path)

    def _on_export(self) -> None:
        """Handle Export button click."""
        if not self._export_path_input or not self._result_text:
            return

        export_path = self._export_path_input.text().strip()

        # Validate export path
        if not export_path:
            self._display_error("Please select an export file location")
            return

        # Execute export via callback
        try:
            result = self._export_callback(export_path)
            self._display_export_result(result)
        except Exception as e:
            self._display_error(f"Export failed: {str(e)}")

    def _on_import(self) -> None:
        """Handle Import button click."""
        if not self._import_path_input or not self._result_text:
            return

        import_path = self._import_path_input.text().strip()

        # Validate import path
        if not import_path:
            self._display_error("Please select an import file")
            return

        if not Path(import_path).exists():
            self._display_error(f"Import file does not exist: {import_path}")
            return

        # Confirm import operation
        reply = QMessageBox.question(
            self,
            "Confirm Import",
            "Import will create a new project.\n\n"
            "All data will be validated before import.\n\n"
            "Continue with import?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Execute import via callback
        try:
            result = self._import_callback(import_path)
            self._display_import_result(result)
        except Exception as e:
            self._display_error(f"Import failed: {str(e)}")

    def _display_export_result(self, result: ExportResultDTO) -> None:
        """Display export operation result.

        Args:
            result: Export result DTO
        """
        if not self._result_text:
            return

        if result.success:
            # Success message
            file_size_kb = result.get_file_size_kb()
            file_size_str = f"{file_size_kb} KB" if file_size_kb else "unknown size"

            message = (
                f"✓ Export successful!\n\n"
                f"Project: {result.project_name}\n"
                f"Exported to: {result.file_path}\n"
                f"File size: {file_size_str}\n\n"
                f"Statistics:\n"
                f"  - Entities: {result.entity_count}\n"
                f"  - Records: {result.record_count}\n"
                f"  - Field values: {result.field_value_count}\n\n"
                f"Format version: {result.format_version}\n"
                f"Exported at: {result.exported_at}"
            )
            self._result_text.setPlainText(message)
            self._result_text.setStyleSheet("color: green;")
        else:
            # Error message
            message = f"✗ Export failed\n\n{result.error_message}"
            self._result_text.setPlainText(message)
            self._result_text.setStyleSheet("color: red;")

    def _display_import_result(self, result: ImportResultDTO) -> None:
        """Display import operation result.

        Args:
            result: Import result DTO
        """
        if not self._result_text:
            return

        if result.success:
            # Success message
            message = (
                f"✓ Import successful!\n\n"
                f"Created project: {result.project_name}\n"
                f"Project ID: {result.project_id}\n\n"
                f"Format version: {result.format_version}"
            )

            # Include warnings if present
            if result.has_warnings:
                message += f"\n\nWarnings ({result.warning_count}):\n"
                for warning in result.warnings:
                    message += f"  - {warning}\n"

            self._result_text.setPlainText(message)
            self._result_text.setStyleSheet("color: green;")
        else:
            # Error message with validation errors
            message = f"✗ Import failed\n\n{result.error_message}\n\n"

            if result.has_validation_errors:
                message += f"Validation Errors ({result.error_count}):\n"
                for error in result.validation_errors[:10]:  # Show first 10 errors
                    message += (
                        f"  - {error.field_path}: {error.error_message} "
                        f"[{error.error_type}]\n"
                    )

                if result.error_count > 10:
                    message += f"  ... and {result.error_count - 10} more errors\n"

            self._result_text.setPlainText(message)
            self._result_text.setStyleSheet("color: red;")

    def _display_error(self, error_message: str) -> None:
        """Display error message in result text.

        Args:
            error_message: Error message to display
        """
        if self._result_text:
            self._result_text.setPlainText(f"✗ Error\n\n{error_message}")
            self._result_text.setStyleSheet("color: red;")

    @staticmethod
    def show_import_export(
        parent: Optional[QWidget],
        export_callback: Callable[[str], ExportResultDTO],
        import_callback: Callable[[str], ImportResultDTO],
        current_project_name: str,
    ) -> None:
        """Show import/export dialog.

        Args:
            parent: Parent widget
            export_callback: Callback to execute export
            import_callback: Callback to execute import
            current_project_name: Name of currently open project
        """
        dialog = ImportExportDialog(
            parent, export_callback, import_callback, current_project_name
        )
        dialog.exec()

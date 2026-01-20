"""Document generation dialog."""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.presentation.viewmodels.document_generation_viewmodel import (
    DocumentGenerationViewModel,
)
from doc_helper.presentation.views.base_view import BaseView


class DocumentGenerationDialog(BaseView):
    """Document generation dialog.

    Allows user to select template, format, and output path for document generation.

    v1 Implementation:
    - Template file selection
    - Format selection (Word/Excel/PDF)
    - Output path selection
    - Pre-generation validation check
    - Generate button
    - Progress display

    v2+ Deferred:
    - Output naming patterns with tokens
    - Document version history
    - Batch generation
    """

    def __init__(
        self,
        parent: QWidget,
        viewmodel: DocumentGenerationViewModel,
    ) -> None:
        """Initialize document generation dialog.

        Args:
            parent: Parent widget
            viewmodel: DocumentGenerationViewModel instance
        """
        super().__init__(parent)
        self._viewmodel = viewmodel

        # UI components
        self._template_entry: Optional[QLineEdit] = None
        self._output_entry: Optional[QLineEdit] = None
        self._format_group: Optional[QButtonGroup] = None
        self._word_radio: Optional[QRadioButton] = None
        self._excel_radio: Optional[QRadioButton] = None
        self._pdf_radio: Optional[QRadioButton] = None
        self._generate_button: Optional[QPushButton] = None
        self._progress_bar: Optional[QProgressBar] = None
        self._status_label: Optional[QLabel] = None
        self._validation_text: Optional[QTextEdit] = None

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Create dialog window
        self._root = QDialog(self._parent)
        self._root.setWindowTitle("Generate Document")
        self._root.resize(600, 500)
        self._root.setModal(True)

        # Main layout
        main_layout = QVBoxLayout(self._root)

        # Template selection
        template_group = QGroupBox("Template")
        template_layout = QHBoxLayout()
        template_group.setLayout(template_layout)

        self._template_entry = QLineEdit()
        template_layout.addWidget(self._template_entry, 1)

        browse_template_btn = QPushButton("Browse...")
        browse_template_btn.clicked.connect(self._on_browse_template)
        template_layout.addWidget(browse_template_btn)

        main_layout.addWidget(template_group)

        # Format selection
        format_group = QGroupBox("Document Format")
        format_layout = QVBoxLayout()
        format_group.setLayout(format_layout)

        self._format_group = QButtonGroup()

        self._word_radio = QRadioButton("Word Document (.docx)")
        self._word_radio.setChecked(True)
        self._format_group.addButton(self._word_radio, 0)
        format_layout.addWidget(self._word_radio)

        self._excel_radio = QRadioButton("Excel Workbook (.xlsx)")
        self._format_group.addButton(self._excel_radio, 1)
        format_layout.addWidget(self._excel_radio)

        self._pdf_radio = QRadioButton("PDF Document (.pdf)")
        self._format_group.addButton(self._pdf_radio, 2)
        format_layout.addWidget(self._pdf_radio)

        main_layout.addWidget(format_group)

        # Output path selection
        output_group = QGroupBox("Output Path")
        output_layout = QHBoxLayout()
        output_group.setLayout(output_layout)

        self._output_entry = QLineEdit()
        output_layout.addWidget(self._output_entry, 1)

        browse_output_btn = QPushButton("Browse...")
        browse_output_btn.clicked.connect(self._on_browse_output)
        output_layout.addWidget(browse_output_btn)

        main_layout.addWidget(output_group)

        # Validation errors
        validation_group = QGroupBox("Pre-Generation Validation")
        validation_layout = QVBoxLayout()
        validation_group.setLayout(validation_layout)

        self._validation_text = QTextEdit()
        self._validation_text.setReadOnly(True)
        self._validation_text.setMaximumHeight(150)
        validation_layout.addWidget(self._validation_text)

        main_layout.addWidget(validation_group, 1)  # Stretch factor

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        main_layout.addWidget(self._progress_bar)

        # Status label
        self._status_label = QLabel("")
        main_layout.addWidget(self._status_label)

        # Buttons
        buttons_layout = QHBoxLayout()

        self._generate_button = QPushButton("Generate")
        self._generate_button.clicked.connect(self._on_generate)
        buttons_layout.addWidget(self._generate_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self._on_cancel)
        buttons_layout.addWidget(cancel_button)

        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        # Bind to ViewModel property changes
        self._viewmodel.subscribe("can_generate", self._on_can_generate_changed)
        self._viewmodel.subscribe("validation_errors", self._on_validation_errors_changed)
        self._viewmodel.subscribe("is_generating", self._on_is_generating_changed)
        self._viewmodel.subscribe("generation_progress", self._on_progress_changed)
        self._viewmodel.subscribe("error_message", self._on_error_message_changed)
        self._viewmodel.subscribe("success_message", self._on_success_message_changed)

        # Initial validation check
        self._update_validation_display()

    def _on_browse_template(self) -> None:
        """Handle Browse Template button click."""
        filename, _ = QFileDialog.getOpenFileName(
            self._root,
            "Select Template",
            "",
            "Word Documents (*.docx);;Excel Workbooks (*.xlsx);;All Files (*.*)",
        )
        if filename and self._template_entry:
            self._template_entry.setText(filename)

    def _on_browse_output(self) -> None:
        """Handle Browse Output button click."""
        # Determine format based on selected radio button
        if self._word_radio and self._word_radio.isChecked():
            ext = ".docx"
            filter_str = "Word Documents (*.docx);;All Files (*.*)"
        elif self._excel_radio and self._excel_radio.isChecked():
            ext = ".xlsx"
            filter_str = "Excel Workbooks (*.xlsx);;All Files (*.*)"
        else:  # PDF
            ext = ".pdf"
            filter_str = "PDF Documents (*.pdf);;All Files (*.*)"

        filename, _ = QFileDialog.getSaveFileName(
            self._root,
            "Save Document As",
            "",
            filter_str,
        )
        if filename and self._output_entry:
            self._output_entry.setText(filename)

    def _on_generate(self) -> None:
        """Handle Generate button click."""
        # Validate inputs
        template_path = self._template_entry.text() if self._template_entry else ""
        output_path = self._output_entry.text() if self._output_entry else ""

        if not template_path:
            QMessageBox.critical(
                self._root, "Validation Error", "Please select a template file"
            )
            return

        if not output_path:
            QMessageBox.critical(
                self._root, "Validation Error", "Please specify an output path"
            )
            return

        # Determine format from radio buttons
        if self._word_radio and self._word_radio.isChecked():
            document_format = DocumentFormat.WORD
        elif self._excel_radio and self._excel_radio.isChecked():
            document_format = DocumentFormat.EXCEL
        else:
            document_format = DocumentFormat.PDF

        # Generate document
        success = self._viewmodel.generate_document(
            template_path=Path(template_path),
            output_path=Path(output_path),
            document_format=document_format,
        )

        if success:
            QMessageBox.information(
                self._root, "Success", "Document generated successfully"
            )
            self._on_cancel()  # Close dialog

    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        self.dispose()

    def _update_validation_display(self) -> None:
        """Update validation errors display."""
        if not self._validation_text:
            return

        errors = self._viewmodel.validation_errors
        if errors:
            text = "\n".join(f"• {error}" for error in errors)
            self._validation_text.setHtml(f'<span style="color: red;">{text}</span>')
        else:
            self._validation_text.setHtml(
                '<span style="color: green;">✓ No validation errors - ready to generate</span>'
            )

    def _on_can_generate_changed(self) -> None:
        """Handle can_generate property change."""
        if self._generate_button:
            self._generate_button.setEnabled(self._viewmodel.can_generate)

    def _on_validation_errors_changed(self) -> None:
        """Handle validation_errors property change."""
        self._update_validation_display()

    def _on_is_generating_changed(self) -> None:
        """Handle is_generating property change."""
        is_generating = self._viewmodel.is_generating

        # Disable/enable inputs during generation
        if self._template_entry:
            self._template_entry.setEnabled(not is_generating)
        if self._output_entry:
            self._output_entry.setEnabled(not is_generating)
        if self._generate_button:
            self._generate_button.setEnabled(not is_generating)

    def _on_progress_changed(self) -> None:
        """Handle generation_progress property change."""
        if self._progress_bar:
            progress = self._viewmodel.generation_progress
            self._progress_bar.setValue(int(progress * 100))

    def _on_error_message_changed(self) -> None:
        """Handle error_message property change."""
        if self._status_label:
            error = self._viewmodel.error_message
            if error:
                self._status_label.setText(error)
                self._status_label.setStyleSheet("color: red;")

    def _on_success_message_changed(self) -> None:
        """Handle success_message property change."""
        if self._status_label:
            success = self._viewmodel.success_message
            if success:
                self._status_label.setText(success)
                self._status_label.setStyleSheet("color: green;")

    def dispose(self) -> None:
        """Dispose of the view."""
        # Unsubscribe from ViewModel
        if self._viewmodel:
            self._viewmodel.unsubscribe("can_generate", self._on_can_generate_changed)
            self._viewmodel.unsubscribe("validation_errors", self._on_validation_errors_changed)
            self._viewmodel.unsubscribe("is_generating", self._on_is_generating_changed)
            self._viewmodel.unsubscribe("generation_progress", self._on_progress_changed)
            self._viewmodel.unsubscribe("error_message", self._on_error_message_changed)
            self._viewmodel.unsubscribe("success_message", self._on_success_message_changed)

        super().dispose()

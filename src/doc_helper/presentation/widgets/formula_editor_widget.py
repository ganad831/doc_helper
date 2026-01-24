"""Formula Editor Widget (Phase F-1: Formula Editor - Read-Only, Design-Time).

A reusable widget for editing and validating formula expressions.
Provides live syntax validation, type inference, and error display.

PHASE F-1 SCOPE:
- Multi-line text editor for formula input
- Live validation feedback
- Inferred result type display
- Error/warning display
- Field reference display

PHASE F-1 CONSTRAINTS:
- Read-only with respect to schema
- NO formula execution
- NO schema mutation
- NO formula persistence

ARCHITECTURE COMPLIANCE:
- Widget binds to FormulaEditorViewModel
- Widget does NOT import domain objects
- Widget does NOT call use-cases directly
"""

from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCharFormat, QColor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from doc_helper.presentation.viewmodels.formula_editor_viewmodel import (
    FormulaEditorViewModel,
)


class FormulaEditorWidget(QWidget):
    """Widget for editing and validating formula expressions.

    Provides:
    - Multi-line monospace text editor
    - Live validation with debouncing
    - Inferred result type display
    - Error/warning messages
    - Field references list

    Phase F-1 Compliance:
    - Read-only schema access via ViewModel
    - No schema mutation
    - No formula execution
    - No persistence

    Usage:
        viewmodel = FormulaEditorViewModel(formula_usecases)
        widget = FormulaEditorWidget(viewmodel, parent)

        # Set schema context (required for field reference validation)
        viewmodel.set_schema_context(schema_fields)

        # Optional: Set initial formula
        viewmodel.set_formula("field1 + field2")
    """

    # Debounce delay for validation (milliseconds)
    VALIDATION_DEBOUNCE_MS = 300

    def __init__(
        self,
        viewmodel: FormulaEditorViewModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize Formula Editor Widget.

        Args:
            viewmodel: FormulaEditorViewModel for state management
            parent: Parent widget
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._debounce_timer: Optional[QTimer] = None
        self._suppress_text_change = False

        # Build UI
        self._build_ui()

        # Subscribe to ViewModel changes
        self._subscribe_to_viewmodel()

        # Initial state update
        self._update_from_viewmodel()

    def _build_ui(self) -> None:
        """Build the widget UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Title
        title_label = QLabel("Formula Editor")
        title_label.setStyleSheet(
            "font-weight: bold; font-size: 11pt; padding: 5px;"
        )
        main_layout.addWidget(title_label)

        # Formula input
        self._formula_input = QPlainTextEdit()
        self._formula_input.setPlaceholderText(
            "Enter formula expression...\n"
            "Examples:\n"
            "  field1 + field2\n"
            "  max(value1, value2) * 100\n"
            "  if_else(is_active, total, 0)"
        )
        self._formula_input.setMinimumHeight(80)
        self._formula_input.setMaximumHeight(150)

        # Monospace font for formula editor
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._formula_input.setFont(font)

        self._formula_input.textChanged.connect(self._on_text_changed)
        main_layout.addWidget(self._formula_input)

        # Result type indicator
        type_frame = self._create_type_indicator()
        main_layout.addWidget(type_frame)

        # Error/warning display
        self._error_frame = self._create_error_display()
        main_layout.addWidget(self._error_frame)

        # Field references display
        self._references_frame = self._create_references_display()
        main_layout.addWidget(self._references_frame)

        # Available functions hint
        self._functions_label = QLabel()
        self._functions_label.setStyleSheet(
            "color: #718096; font-size: 8pt; font-style: italic; padding: 4px;"
        )
        self._functions_label.setWordWrap(True)
        self._update_functions_hint()
        main_layout.addWidget(self._functions_label)

        # Stretch to fill available space
        main_layout.addStretch()

    def _create_type_indicator(self) -> QFrame:
        """Create the result type indicator frame.

        Returns:
            QFrame containing result type display
        """
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { "
            "background-color: #f7fafc; "
            "border: 1px solid #e2e8f0; "
            "border-radius: 4px; "
            "padding: 4px; "
            "}"
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)

        # Type label
        type_label = QLabel("Result Type:")
        type_label.setStyleSheet("font-weight: bold; color: #4a5568;")
        layout.addWidget(type_label)

        # Type value
        self._type_value_label = QLabel("UNKNOWN")
        self._type_value_label.setStyleSheet(
            "color: #2d3748; font-family: monospace;"
        )
        layout.addWidget(self._type_value_label)

        # Validity indicator
        self._validity_indicator = QLabel()
        layout.addWidget(self._validity_indicator)

        layout.addStretch()

        return frame

    def _create_error_display(self) -> QFrame:
        """Create the error/warning display frame.

        Returns:
            QFrame containing error/warning messages
        """
        frame = QFrame()
        frame.setVisible(False)  # Hidden by default

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        # Error header
        self._error_header_label = QLabel()
        self._error_header_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._error_header_label)

        # Error messages
        self._error_messages_label = QLabel()
        self._error_messages_label.setWordWrap(True)
        self._error_messages_label.setStyleSheet("padding-left: 8px;")
        layout.addWidget(self._error_messages_label)

        return frame

    def _create_references_display(self) -> QFrame:
        """Create the field references display frame.

        Returns:
            QFrame containing field references list
        """
        frame = QFrame()
        frame.setVisible(False)  # Hidden by default
        frame.setStyleSheet(
            "QFrame { "
            "background-color: #edf2f7; "
            "border: 1px solid #e2e8f0; "
            "border-radius: 4px; "
            "}"
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)

        # References label
        refs_label = QLabel("Field References:")
        refs_label.setStyleSheet("font-weight: bold; color: #4a5568;")
        layout.addWidget(refs_label)

        # References value
        self._references_value_label = QLabel()
        self._references_value_label.setWordWrap(True)
        self._references_value_label.setStyleSheet(
            "color: #2d3748; font-family: monospace;"
        )
        layout.addWidget(self._references_value_label, 1)

        return frame

    def _subscribe_to_viewmodel(self) -> None:
        """Subscribe to ViewModel property changes."""
        self._viewmodel.subscribe("validation_result", self._update_from_viewmodel)
        self._viewmodel.subscribe("is_valid", self._update_validity_indicator)
        self._viewmodel.subscribe("inferred_type", self._update_type_display)
        self._viewmodel.subscribe("errors", self._update_error_display)
        self._viewmodel.subscribe("warnings", self._update_error_display)
        self._viewmodel.subscribe("field_references", self._update_references_display)

    def _update_from_viewmodel(self) -> None:
        """Update all UI elements from ViewModel state."""
        self._update_validity_indicator()
        self._update_type_display()
        self._update_error_display()
        self._update_references_display()

    def _on_text_changed(self) -> None:
        """Handle formula text change.

        Uses debouncing to avoid validating on every keystroke.
        """
        if self._suppress_text_change:
            return

        # Cancel any pending validation
        if self._debounce_timer:
            self._debounce_timer.stop()

        # Create new timer for debounced validation
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._validate_formula)
        self._debounce_timer.start(self.VALIDATION_DEBOUNCE_MS)

    def _validate_formula(self) -> None:
        """Validate the current formula text.

        Called after debounce delay.
        """
        formula_text = self._formula_input.toPlainText()
        self._viewmodel.set_formula(formula_text)

    def _update_validity_indicator(self) -> None:
        """Update the validity indicator (checkmark or X)."""
        if not self._viewmodel.has_formula:
            self._validity_indicator.setText("")
            return

        if self._viewmodel.is_valid:
            self._validity_indicator.setText("\u2714")  # Checkmark
            self._validity_indicator.setStyleSheet("color: #48bb78; font-size: 14pt;")
        else:
            self._validity_indicator.setText("\u2718")  # X mark
            self._validity_indicator.setStyleSheet("color: #f56565; font-size: 14pt;")

    def _update_type_display(self) -> None:
        """Update the inferred type display."""
        inferred_type = self._viewmodel.inferred_type

        self._type_value_label.setText(inferred_type)

        # Color-code by type
        type_colors = {
            "BOOLEAN": "#805ad5",  # Purple
            "NUMBER": "#3182ce",   # Blue
            "TEXT": "#38a169",     # Green
            "UNKNOWN": "#718096",  # Gray
        }

        color = type_colors.get(inferred_type, "#718096")
        self._type_value_label.setStyleSheet(
            f"color: {color}; font-family: monospace; font-weight: bold;"
        )

    def _update_error_display(self) -> None:
        """Update the error/warning display."""
        errors = self._viewmodel.errors
        warnings = self._viewmodel.warnings

        if not errors and not warnings:
            self._error_frame.setVisible(False)
            return

        self._error_frame.setVisible(True)

        # Build message text
        messages = []

        if errors:
            self._error_header_label.setText(f"Errors ({len(errors)})")
            self._error_header_label.setStyleSheet(
                "font-weight: bold; color: #c53030;"
            )
            self._error_frame.setStyleSheet(
                "QFrame { "
                "background-color: #fff5f5; "
                "border: 1px solid #fc8181; "
                "border-radius: 4px; "
                "}"
            )
            for error in errors:
                messages.append(f"\u2022 {error}")

        elif warnings:
            self._error_header_label.setText(f"Warnings ({len(warnings)})")
            self._error_header_label.setStyleSheet(
                "font-weight: bold; color: #b7791f;"
            )
            self._error_frame.setStyleSheet(
                "QFrame { "
                "background-color: #fffff0; "
                "border: 1px solid #f6e05e; "
                "border-radius: 4px; "
                "}"
            )
            for warning in warnings:
                messages.append(f"\u2022 {warning}")

        self._error_messages_label.setText("\n".join(messages))

    def _update_references_display(self) -> None:
        """Update the field references display."""
        references = self._viewmodel.field_references

        if not references:
            self._references_frame.setVisible(False)
            return

        self._references_frame.setVisible(True)
        self._references_value_label.setText(", ".join(references))

    def _update_functions_hint(self) -> None:
        """Update the available functions hint."""
        functions = self._viewmodel.available_functions
        if functions:
            # Show first few functions with ellipsis if more
            shown = functions[:8]
            hint = "Available functions: " + ", ".join(shown)
            if len(functions) > 8:
                hint += f", ... (+{len(functions) - 8} more)"
            self._functions_label.setText(hint)

    def set_formula(self, formula_text: str) -> None:
        """Set the formula text programmatically.

        Args:
            formula_text: Formula text to set
        """
        # Suppress text change handler to avoid double validation
        self._suppress_text_change = True
        try:
            self._formula_input.setPlainText(formula_text)
        finally:
            self._suppress_text_change = False

        # Validate immediately
        self._viewmodel.set_formula(formula_text)

    def get_formula(self) -> str:
        """Get the current formula text.

        Returns:
            Current formula text
        """
        return self._formula_input.toPlainText()

    def clear(self) -> None:
        """Clear the formula editor."""
        self._suppress_text_change = True
        try:
            self._formula_input.clear()
        finally:
            self._suppress_text_change = False

        self._viewmodel.clear_formula()

    def set_enabled(self, enabled: bool) -> None:
        """Set the enabled state of the editor.

        Args:
            enabled: True to enable, False to disable
        """
        self._formula_input.setEnabled(enabled)

    def dispose(self) -> None:
        """Clean up resources."""
        # Cancel any pending timer
        if self._debounce_timer:
            self._debounce_timer.stop()
            self._debounce_timer = None

        # Unsubscribe from ViewModel
        if self._viewmodel:
            self._viewmodel.dispose()

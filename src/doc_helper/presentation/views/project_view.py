"""Project editing view."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QFont, QKeySequence
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.presentation.viewmodels.project_viewmodel import ProjectViewModel
from doc_helper.presentation.views.base_view import BaseView
from doc_helper.presentation.widgets.field_widget import IFieldWidget


class ProjectView(BaseView):
    """Project editing view.

    Main window for editing project fields.

    v1 Implementation:
    - Entity navigation sidebar (v1: single entity - Soil Investigation)
    - Dynamic field form based on schema
    - Field widgets for all 12 field types
    - Save button
    - Validation error indicators
    - Document generation button

    v2+ Deferred:
    - Multi-entity navigation
    - Quick search
    - Field history
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        viewmodel: ProjectViewModel,
        entity_definition: EntityDefinition,
    ) -> None:
        """Initialize project view.

        Args:
            parent: Parent widget
            viewmodel: ProjectViewModel instance
            entity_definition: Entity definition for schema
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._entity_definition = entity_definition

        # UI components
        self._fields_widget: Optional[QWidget] = None
        self._save_button: Optional[QPushButton] = None
        self._generate_button: Optional[QPushButton] = None
        self._status_bar: Optional[QStatusBar] = None

        # Field widgets mapped by field ID
        self._field_widgets: dict[str, IFieldWidget] = {}

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Create main window
        self._root = QMainWindow(self._parent)
        self._root.setWindowTitle("Doc Helper - Project")
        self._root.resize(1024, 768)

        # Menu bar
        self._create_menu()

        # Central widget with main layout
        central_widget = QWidget()
        self._root.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Sidebar (v1: minimal - just project info)
        sidebar = self._create_sidebar()
        sidebar.setFixedWidth(200)
        main_layout.addWidget(sidebar)

        # Content area (fields form) with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._fields_widget = QWidget()
        fields_layout = QVBoxLayout(self._fields_widget)
        scroll_area.setWidget(self._fields_widget)

        main_layout.addWidget(scroll_area, 1)  # Stretch factor 1

        # Build field widgets
        self._build_field_widgets()

        # Status bar
        self._status_bar = QStatusBar()
        self._root.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        # Bind to ViewModel property changes
        self._viewmodel.subscribe("has_unsaved_changes", self._on_unsaved_changes)
        self._viewmodel.subscribe("project_name", self._on_project_name_changed)

    def _create_menu(self) -> None:
        """Create menu bar."""
        menubar = self._root.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        save_action = QAction("Save", self._root)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        generate_action = QAction("Generate Document", self._root)
        generate_action.triggered.connect(self._on_generate_document)
        file_menu.addAction(generate_action)

        file_menu.addSeparator()

        close_action = QAction("Close", self._root)
        close_action.triggered.connect(self._on_close)
        file_menu.addAction(close_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        undo_action = QAction("Undo", self._root)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self._root)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)

    def _create_sidebar(self) -> QWidget:
        """Create sidebar.

        Returns:
            Sidebar widget
        """
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)

        # Project info
        info_group = QGroupBox("Project")
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)

        project_name_label = QLabel(self._viewmodel.project_name)
        name_font = QFont("Arial", 10)
        name_font.setBold(True)
        project_name_label.setFont(name_font)
        project_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(project_name_label)

        sidebar_layout.addWidget(info_group)

        # Buttons
        self._save_button = QPushButton("Save")
        self._save_button.clicked.connect(self._on_save)
        sidebar_layout.addWidget(self._save_button)

        self._generate_button = QPushButton("Generate Document")
        self._generate_button.clicked.connect(self._on_generate_document)
        sidebar_layout.addWidget(self._generate_button)

        sidebar_layout.addStretch()

        return sidebar

    def _build_field_widgets(self) -> None:
        """Build field widgets based on entity definition."""
        if not self._fields_widget:
            return

        # TODO: Create field widgets based on entity definition
        # For now, placeholder
        placeholder_label = QLabel("Field widgets will be created here based on schema")
        self._fields_widget.layout().addWidget(placeholder_label)
        self._fields_widget.layout().addStretch()

    def _on_unsaved_changes(self) -> None:
        """Handle unsaved changes state change."""
        if self._viewmodel.has_unsaved_changes:
            self._root.setWindowTitle(f"Doc Helper - {self._viewmodel.project_name} *")
            self._status_bar.showMessage("Unsaved changes")
        else:
            self._root.setWindowTitle(f"Doc Helper - {self._viewmodel.project_name}")
            self._status_bar.showMessage("Saved")

    def _on_project_name_changed(self) -> None:
        """Handle project name change."""
        suffix = " *" if self._viewmodel.has_unsaved_changes else ""
        self._root.setWindowTitle(f"Doc Helper - {self._viewmodel.project_name}{suffix}")

    def _on_save(self) -> None:
        """Handle Save action."""
        if self._viewmodel.save_project():
            self._status_bar.showMessage("Project saved")
            QMessageBox.information(
                self._root, "Save", "Project saved successfully"
            )
        else:
            QMessageBox.critical(self._root, "Save Error", "Failed to save project")

    def _on_undo(self) -> None:
        """Handle Undo action."""
        # TODO: Implement undo via command pattern
        pass

    def _on_redo(self) -> None:
        """Handle Redo action."""
        # TODO: Implement redo via command pattern
        pass

    def _on_generate_document(self) -> None:
        """Handle Generate Document action."""
        # TODO: Show document generation dialog
        pass

    def _on_close(self) -> None:
        """Handle window close."""
        if self._viewmodel.has_unsaved_changes:
            reply = QMessageBox.question(
                self._root,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                if not self._viewmodel.save_project():
                    QMessageBox.critical(
                        self._root, "Save Error", "Failed to save project"
                    )
                    return

        self.dispose()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event.

        Args:
            event: Close event
        """
        self._on_close()
        event.accept()

    def dispose(self) -> None:
        """Dispose of the view."""
        # Unsubscribe from ViewModel
        if self._viewmodel:
            self._viewmodel.unsubscribe("has_unsaved_changes", self._on_unsaved_changes)
            self._viewmodel.unsubscribe("project_name", self._on_project_name_changed)

        # Dispose field widgets
        for widget in self._field_widgets.values():
            widget.dispose()
        self._field_widgets.clear()

        super().dispose()

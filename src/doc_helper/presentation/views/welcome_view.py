"""Welcome view."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from doc_helper.presentation.viewmodels.welcome_viewmodel import WelcomeViewModel
from doc_helper.presentation.views.base_view import BaseView


class WelcomeView(BaseView):
    """Welcome screen view.

    Displays recent projects and allows creating new projects.

    v1 Implementation:
    - Recent projects list (max 10)
    - Create New Project button
    - Open Project button (for selected project)
    - Simple list display with project names

    v2+ Deferred:
    - App type selection cards
    - Project templates
    - Search/filter projects
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        viewmodel: WelcomeViewModel,
    ) -> None:
        """Initialize welcome view.

        Args:
            parent: Parent widget
            viewmodel: WelcomeViewModel instance
        """
        super().__init__(parent)
        self._viewmodel = viewmodel

        # UI components
        self._projects_list: Optional[QListWidget] = None
        self._open_button: Optional[QPushButton] = None
        self._new_button: Optional[QPushButton] = None
        self._error_label: Optional[QLabel] = None

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Create main widget
        self._root = QWidget(self._parent)
        main_layout = QVBoxLayout(self._root)

        # Title
        title_label = QLabel("Doc Helper")
        title_font = QFont("Arial", 24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        main_layout.addSpacing(10)

        # Subtitle
        subtitle_label = QLabel("Document Generation Platform")
        subtitle_font = QFont("Arial", 12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle_label)
        main_layout.addSpacing(20)

        # Recent projects section
        projects_group = QGroupBox("Recent Projects")
        projects_layout = QVBoxLayout()
        projects_group.setLayout(projects_layout)

        # Projects list (has built-in scrollbar)
        self._projects_list = QListWidget()
        self._projects_list.itemDoubleClicked.connect(self._on_open_project)
        self._projects_list.itemSelectionChanged.connect(self._on_selection_changed)
        projects_layout.addWidget(self._projects_list)

        main_layout.addWidget(projects_group, 1)  # Stretch factor 1

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self._open_button = QPushButton("Open Project")
        self._open_button.clicked.connect(self._on_open_project)
        self._open_button.setEnabled(False)
        buttons_layout.addWidget(self._open_button)

        self._new_button = QPushButton("Create New Project")
        self._new_button.clicked.connect(self._on_create_project)
        buttons_layout.addWidget(self._new_button)

        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: red;")
        error_font = QFont("Arial", 9)
        self._error_label.setFont(error_font)
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._error_label)

        # Bind to ViewModel property changes
        self._viewmodel.subscribe("recent_projects", self._on_projects_changed)
        self._viewmodel.subscribe("error_message", self._on_error_changed)

        # Load recent projects
        self._viewmodel.load_recent_projects()

    def _on_projects_changed(self) -> None:
        """Handle recent projects list change."""
        if not self._projects_list:
            return

        # Clear list
        self._projects_list.clear()

        # Populate with project names
        for project in self._viewmodel.recent_projects:
            self._projects_list.addItem(project.name.value)

    def _on_error_changed(self) -> None:
        """Handle error message change."""
        if not self._error_label:
            return

        error = self._viewmodel.error_message
        if error:
            self._error_label.setText(error)
        else:
            self._error_label.setText("")

    def _on_selection_changed(self) -> None:
        """Handle list selection change."""
        if not self._projects_list or not self._open_button:
            return

        has_selection = len(self._projects_list.selectedItems()) > 0
        self._open_button.setEnabled(has_selection)

    def _on_open_project(self) -> None:
        """Handle Open Project button click."""
        if not self._projects_list:
            return

        selected_items = self._projects_list.selectedItems()
        if not selected_items:
            return

        index = self._projects_list.row(selected_items[0])
        # TODO: Open project at index
        # This will be handled by the application controller

    def _on_create_project(self) -> None:
        """Handle Create New Project button click."""
        # TODO: Show create project dialog
        # This will be handled by the application controller
        pass

    def dispose(self) -> None:
        """Dispose of the view."""
        # Unsubscribe from ViewModel
        if self._viewmodel:
            self._viewmodel.unsubscribe("recent_projects", self._on_projects_changed)
            self._viewmodel.unsubscribe("error_message", self._on_error_changed)

        super().dispose()

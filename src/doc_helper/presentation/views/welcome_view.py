"""Welcome view.

v2 PHASE 4: AppType-aware project creation with selection dialog.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from doc_helper.presentation.dialogs.new_project_dialog import NewProjectDialog
from doc_helper.presentation.viewmodels.welcome_viewmodel import WelcomeViewModel
from doc_helper.presentation.views.base_view import BaseView


class WelcomeView(BaseView):
    """Welcome screen view.

    Displays recent projects and allows creating new projects.

    v2 PHASE 4 Implementation:
    - Recent projects list (max 10)
    - Create New Project button with AppType selection dialog
    - Open Project button (for selected project)
    - Simple list display with project names

    Future Enhancements:
    - App type selection cards (instead of dialog)
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
        self._tools_button: Optional[QPushButton] = None
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

        # Tools button - shows available TOOL AppTypes
        self._tools_button = QPushButton("Tools")
        self._tools_button.clicked.connect(self._on_tools_clicked)
        buttons_layout.addWidget(self._tools_button)

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
        """Handle Create New Project button click.

        v2 PHASE 4: Show AppType selection dialog.
        """
        # Get available AppTypes from ViewModel
        available_app_types = self._viewmodel.get_available_app_types()

        if not available_app_types:
            QMessageBox.warning(
                self._root,
                "No AppTypes Available",
                "No AppTypes are currently available. Please ensure AppTypes are registered.",
            )
            return

        # Show new project dialog with AppType selection
        dialog = NewProjectDialog(self._root, available_app_types)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # Get dialog values
        name = dialog.get_project_name()
        app_type_id = dialog.get_selected_app_type_id()
        description = dialog.get_description()

        if not name or not app_type_id:
            return

        # Call viewmodel to create project
        success, project_id = self._viewmodel.create_new_project(
            name=name,
            app_type_id=app_type_id,
            description=description,
        )

        if success:
            QMessageBox.information(
                self._root,
                "Project Created",
                f"Project '{name}' created successfully.",
            )
            # TODO: Open the newly created project in project view
        else:
            # Error is already displayed via error_message binding
            pass

    def _on_tools_clicked(self) -> None:
        """Handle Tools button click.

        Shows a menu of available TOOL AppTypes. Delegates launching
        to ViewModel which routes through AppTypeRouter.
        """
        if not self._tools_button:
            return

        # Get available TOOL AppTypes from ViewModel
        tool_app_types = self._viewmodel.get_tool_app_types()

        if not tool_app_types:
            QMessageBox.information(
                self._root,
                "No Tools Available",
                "No tools are currently available.",
            )
            return

        # Create a popup menu with available tools
        menu = QMenu(self._tools_button)

        for tool in tool_app_types:
            action = menu.addAction(tool.name)
            # Store app_type_id in action data
            action.setData(tool.app_type_id)
            if tool.description:
                action.setToolTip(tool.description)

        # Show menu and handle selection
        action = menu.exec(self._tools_button.mapToGlobal(
            self._tools_button.rect().bottomLeft()
        ))

        if action:
            app_type_id = action.data()
            self._launch_tool(app_type_id)

    def _launch_tool(self, app_type_id: str) -> None:
        """Launch a TOOL AppType.

        Delegates to ViewModel, which routes through AppTypeRouter,
        then creates and shows the tool's view.

        Args:
            app_type_id: ID of TOOL AppType to launch
        """
        success, error = self._viewmodel.launch_tool(app_type_id)

        if not success:
            QMessageBox.warning(
                self._root,
                "Launch Failed",
                f"Could not launch tool: {error}",
            )
            return

        # Get the tool view from ViewModel
        tool_view = self._viewmodel.get_tool_view(app_type_id, self._root)

        if tool_view is None:
            error_msg = self._viewmodel.error_message or "Unknown error"
            QMessageBox.warning(
                self._root,
                "View Creation Failed",
                f"Could not create tool view: {error_msg}",
            )
            return

        # Show the tool view as a modal dialog
        if isinstance(tool_view, QDialog):
            tool_view.exec()
        else:
            # For non-dialog views, show as a window
            tool_view.show()

    def dispose(self) -> None:
        """Dispose of the view."""
        # Unsubscribe from ViewModel
        if self._viewmodel:
            self._viewmodel.unsubscribe("recent_projects", self._on_projects_changed)
            self._viewmodel.unsubscribe("error_message", self._on_error_changed)

        super().dispose()

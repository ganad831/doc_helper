"""ViewModel for Welcome screen.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md):
- Presentation layer uses DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary

v2 PHASE 4: AppType-aware project creation.
Exposes available AppTypes to UI for selection during project creation.
"""

from typing import Optional

from doc_helper.application.commands.create_project_command import CreateProjectCommand
from doc_helper.application.dto import ProjectSummaryDTO, AppTypeDTO
from doc_helper.application.queries.get_project_query import GetRecentProjectsQuery
from doc_helper.platform.registry.interfaces import IAppTypeRegistry
from doc_helper.platform.routing.app_type_router import IAppTypeRouter
# Domain imports moved to local scope to comply with DTO-only MVVM rule
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


class WelcomeViewModel(BaseViewModel):
    """ViewModel for Welcome screen.

    Manages recent projects list and project creation.

    v2 PHASE 4 Scope:
    - Display recent projects
    - Expose available AppTypes for selection
    - Create new project with AppType selection
    - Open existing project

    Example:
        vm = WelcomeViewModel(get_recent_query, create_command, app_type_registry)
        vm.load_recent_projects()
        for project in vm.recent_projects:
            print(project.name)

        app_types = vm.get_available_app_types()
        for app_type in app_types:
            print(f"{app_type.name}: {app_type.description}")
    """

    def __init__(
        self,
        get_recent_query: GetRecentProjectsQuery,
        create_project_command: CreateProjectCommand,
        app_type_registry: IAppTypeRegistry,
        app_type_router: Optional[IAppTypeRouter] = None,
    ) -> None:
        """Initialize WelcomeViewModel.

        Args:
            get_recent_query: Query for getting recent projects
            create_project_command: Command for creating new projects
            app_type_registry: Registry for available AppTypes
            app_type_router: Router for launching AppTypes (optional for backwards compat)
        """
        super().__init__()
        self._get_recent_query = get_recent_query
        self._create_project_command = create_project_command
        self._app_type_registry = app_type_registry
        self._app_type_router = app_type_router

        self._recent_projects: list[ProjectSummaryDTO] = []
        self._is_loading = False
        self._error_message: Optional[str] = None

    @property
    def recent_projects(self) -> list[ProjectSummaryDTO]:
        """Get list of recent projects.

        Returns:
            List of ProjectSummaryDTO objects (NOT domain objects)
        """
        return self._recent_projects

    @property
    def is_loading(self) -> bool:
        """Check if data is being loaded.

        Returns:
            True if loading
        """
        return self._is_loading

    @property
    def error_message(self) -> Optional[str]:
        """Get current error message.

        Returns:
            Error message if any, None otherwise
        """
        return self._error_message

    @property
    def has_recent_projects(self) -> bool:
        """Check if there are any recent projects.

        Returns:
            True if recent projects exist
        """
        return len(self._recent_projects) > 0

    def load_recent_projects(self, limit: int = 10) -> None:
        """Load recent projects from repository.

        Args:
            limit: Maximum number of projects to load
        """
        self._is_loading = True
        self._error_message = None
        self.notify_change("is_loading")
        self.notify_change("error_message")

        try:
            result = self._get_recent_query.execute(limit=limit)

            if result.is_success():
                self._recent_projects = result.value
                self._error_message = None
            else:
                self._recent_projects = []
                self._error_message = f"Failed to load recent projects: {result.error}"

        except Exception as e:
            self._recent_projects = []
            self._error_message = f"Error loading recent projects: {str(e)}"

        finally:
            self._is_loading = False
            self.notify_change("recent_projects")
            self.notify_change("has_recent_projects")
            self.notify_change("is_loading")
            self.notify_change("error_message")

    def get_available_app_types(self) -> list[AppTypeDTO]:
        """Get list of available DOCUMENT AppTypes.

        v2 PHASE 4: Returns AppType metadata for UI display.
        Only returns DOCUMENT AppTypes (for "Create New Project").
        TOOL AppTypes are accessed via get_tool_app_types().

        Returns:
            List of AppTypeDTO objects containing metadata (DOCUMENT only)
        """
        return [
            dto for dto in self._get_all_app_types()
            if dto.is_document
        ]

    def get_tool_app_types(self) -> list[AppTypeDTO]:
        """Get list of available TOOL AppTypes.

        Returns AppType metadata for TOOL AppTypes (Schema Designer, etc.)
        that should be shown in the "Tools" section.

        Returns:
            List of AppTypeDTO objects containing metadata (TOOL only)
        """
        return [
            dto for dto in self._get_all_app_types()
            if dto.is_tool
        ]

    def has_tool_app_types(self) -> bool:
        """Check if any TOOL AppTypes are available.

        Returns:
            True if at least one TOOL AppType is registered
        """
        return len(self.get_tool_app_types()) > 0

    def launch_tool(self, app_type_id: str) -> tuple[bool, Optional[str]]:
        """Launch a TOOL AppType.

        Delegates to AppTypeRouter to validate and set up context.
        The View should use the result to navigate to the appropriate UI.

        Args:
            app_type_id: ID of TOOL AppType to launch

        Returns:
            Tuple of (success: bool, error_message: str | None)
            - (True, None) if tool can be launched
            - (False, "error message") if validation fails
        """
        if self._app_type_router is None:
            self._error_message = "AppType router not configured"
            self.notify_change("error_message")
            return (False, self._error_message)

        success, error = self._app_type_router.launch_tool(app_type_id)

        if not success:
            self._error_message = error
            self.notify_change("error_message")
            return (False, error)

        # Clear any previous error on success
        self._error_message = None
        self.notify_change("error_message")
        return (True, None)

    def _get_all_app_types(self) -> list[AppTypeDTO]:
        """Get list of ALL registered AppTypes (internal).

        Returns:
            List of AppTypeDTO objects containing metadata
        """
        try:
            app_types = []
            for app_type_id in self._app_type_registry.list_app_type_ids():
                manifest = self._app_type_registry.get(app_type_id)
                if manifest:
                    app_types.append(
                        AppTypeDTO(
                            app_type_id=manifest.metadata.app_type_id,
                            name=manifest.metadata.name,
                            version=manifest.metadata.version,
                            description=manifest.metadata.description,
                            kind=manifest.metadata.kind.value,
                        )
                    )
            return app_types
        except Exception as e:
            # Return empty list on error (UI will handle gracefully)
            return []

    def create_new_project(
        self,
        name: str,
        app_type_id: str,
        description: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """Create a new project.

        v2 PHASE 4: Accepts app_type_id parameter for AppType selection.

        Args:
            name: Project name
            app_type_id: AppType identifier (e.g., "soil_investigation")
            description: Optional project description

        Returns:
            Tuple of (success: bool, project_id: str | None)
        """
        if not name or not name.strip():
            self._error_message = "Project name is required"
            self.notify_change("error_message")
            return (False, None)

        if not app_type_id or not app_type_id.strip():
            self._error_message = "AppType selection is required"
            self.notify_change("error_message")
            return (False, None)

        try:
            # v2 PHASE 4: Use app_type_id as entity_definition_id
            # (AppType determines the root entity structure)
            from doc_helper.domain.schema.schema_ids import EntityDefinitionId

            result = self._create_project_command.execute(
                name=name.strip(),
                entity_definition_id=EntityDefinitionId(app_type_id),
                description=description,
                app_type_id=app_type_id,
            )

            if result.is_success():
                project_id = result.value
                self._error_message = None
                self.notify_change("error_message")
                # Reload recent projects to include new project
                self.load_recent_projects()
                return (True, str(project_id.value))
            else:
                self._error_message = f"Failed to create project: {result.error}"
                self.notify_change("error_message")
                return (False, None)

        except Exception as e:
            self._error_message = f"Error creating project: {str(e)}"
            self.notify_change("error_message")
            return (False, None)

    def clear_error(self) -> None:
        """Clear current error message."""
        self._error_message = None
        self.notify_change("error_message")

    def dispose(self) -> None:
        """Clean up resources."""
        super().dispose()
        self._recent_projects.clear()

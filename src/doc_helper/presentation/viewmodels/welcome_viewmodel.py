"""ViewModel for Welcome screen.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md):
- Presentation layer uses DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary
"""

from typing import Optional

from doc_helper.application.commands.create_project_command import CreateProjectCommand
from doc_helper.application.dto import ProjectSummaryDTO
from doc_helper.application.queries.get_project_query import GetRecentProjectsQuery
# Domain imports moved to local scope to comply with DTO-only MVVM rule
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


class WelcomeViewModel(BaseViewModel):
    """ViewModel for Welcome screen.

    Manages recent projects list and project creation.

    v1 Scope:
    - Display recent projects (no app type selection)
    - Create new project (hardcoded to soil_investigation entity)
    - Open existing project

    v2+ Deferred:
    - App type selection cards
    - Project templates

    Example:
        vm = WelcomeViewModel(get_recent_query, create_command)
        vm.load_recent_projects()
        for project in vm.recent_projects:
            print(project.name)
    """

    def __init__(
        self,
        get_recent_query: GetRecentProjectsQuery,
        create_project_command: CreateProjectCommand,
    ) -> None:
        """Initialize WelcomeViewModel.

        Args:
            get_recent_query: Query for getting recent projects
            create_project_command: Command for creating new projects
        """
        super().__init__()
        self._get_recent_query = get_recent_query
        self._create_project_command = create_project_command

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

    def create_new_project(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """Create a new project.

        v1: Hardcoded to soil_investigation entity type.

        Args:
            name: Project name
            description: Optional project description

        Returns:
            Tuple of (success: bool, project_id: str | None)
        """
        if not name or not name.strip():
            self._error_message = "Project name is required"
            self.notify_change("error_message")
            return (False, None)

        try:
            # v1: Hardcoded entity definition for soil investigation
            from doc_helper.domain.schema.schema_ids import EntityDefinitionId

            result = self._create_project_command.execute(
                name=name.strip(),
                entity_definition_id=EntityDefinitionId("soil_investigation"),
                description=description,
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

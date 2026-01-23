"""Welcome Use Cases (Architecture Enforcement Phase).

Application layer use-case class that encapsulates all welcome screen operations.
Presentation layer MUST use this class instead of directly accessing
commands or queries.

RULE 0 ENFORCEMENT:
- Presentation ONLY calls use-case methods
- All domain type construction happens HERE
- All command/query orchestration happens HERE
- Returns primitives/DTOs to Presentation (no domain types)

This class wraps:
- CreateProjectCommand (create project)
- GetRecentProjectsQuery (get recent projects)
"""

from typing import Optional

from doc_helper.application.commands.create_project_command import CreateProjectCommand
from doc_helper.application.dto import ProjectSummaryDTO
from doc_helper.application.queries.get_project_query import GetRecentProjectsQuery


class WelcomeUseCases:
    """Use-case class for welcome screen operations.

    This class provides a clean boundary between Presentation and Application layers.
    Presentation layer injects this class and calls its methods with primitives.
    All domain type construction and command/query orchestration happens here.

    Usage in ViewModel:
        # ViewModel __init__ receives WelcomeUseCases via DI
        def __init__(self, welcome_usecases: WelcomeUseCases, ...):
            self._welcome_usecases = welcome_usecases

        # ViewModel calls use-case methods with primitives
        def create_project(self, name: str, app_type_id: str, ...):
            return self._welcome_usecases.create_project(name, app_type_id, ...)

    This replaces:
        # OLD (FORBIDDEN): ViewModel calls command.execute_with_str_ids(...)
        # and then unwraps result.value (which is ProjectId)
        result = self._create_project_command.execute_with_str_ids(...)
        return (True, str(project_id.value))  # unwrap domain ID
    """

    def __init__(
        self,
        create_project_command: CreateProjectCommand,
        get_recent_projects_query: GetRecentProjectsQuery,
    ) -> None:
        """Initialize WelcomeUseCases.

        Args:
            create_project_command: Command for creating projects
            get_recent_projects_query: Query for getting recent projects

        Note:
            Commands and queries are injected HERE (Application layer).
            Presentation receives only this use-case class.
        """
        self._create_project_command = create_project_command
        self._get_recent_projects_query = get_recent_projects_query

    def create_project(
        self,
        name: str,
        app_type_id: str,
        description: Optional[str] = None,
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Create a new project.

        Args:
            name: Project name
            app_type_id: AppType identifier
            description: Optional project description

        Returns:
            Tuple of (success, project_id_str, error_message):
            - success: True if project created
            - project_id_str: Project ID as string (on success)
            - error_message: Error message (on failure)
        """
        result = self._create_project_command.execute_with_str_ids(
            name=name,
            entity_definition_id_str=app_type_id,
            description=description,
            app_type_id=app_type_id,
        )

        if result.is_success():
            # Unwrap domain ProjectId to string HERE (not in Presentation)
            project_id = result.value
            return (True, str(project_id.value), None)
        else:
            return (False, None, result.error)

    def get_recent_projects(
        self,
        limit: int = 10,
    ) -> tuple[list[ProjectSummaryDTO], Optional[str]]:
        """Get recent projects.

        Args:
            limit: Maximum number of projects to return

        Returns:
            Tuple of (projects, error_message):
            - projects: List of ProjectSummaryDTO (empty on error)
            - error_message: Error message (None on success)
        """
        result = self._get_recent_projects_query.execute(limit=limit)

        if result.is_success():
            return (result.value, None)
        else:
            return ([], result.error)

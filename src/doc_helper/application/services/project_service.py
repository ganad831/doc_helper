"""Project application service.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan_FINAL.md H3):
- Application services accept primitives (string IDs), not domain types
- Services convert primitives to domain types internally
- ViewModels call services, not commands directly
- This service bridges presentation (strings) and domain (typed IDs)
"""

from typing import Optional
from uuid import UUID

from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.dto import ProjectDTO
from doc_helper.application.queries.get_project_query import GetProjectQuery
from doc_helper.domain.common.result import Result


class ProjectApplicationService:
    """Application service for project operations.

    Accepts string IDs from presentation layer and converts to typed domain IDs.
    This enforces the DTO-only MVVM rule - presentation never imports domain types.
    """

    def __init__(
        self,
        save_project_command: SaveProjectCommand,
        get_project_query: GetProjectQuery,
    ) -> None:
        """Initialize service with command and query dependencies.

        Args:
            save_project_command: Command for saving projects
            get_project_query: Query for retrieving projects
        """
        self._save_project_command = save_project_command
        self._get_project_query = get_project_query

    def save_project(self, project_id_str: str) -> Result[None, str]:
        """Save project by string ID.

        Args:
            project_id_str: Project ID as string (UUID format)

        Returns:
            Success(None) if saved successfully
            Failure(error) if save failed
        """
        # Import domain type locally to avoid polluting module namespace
        from doc_helper.domain.project.project_ids import ProjectId

        try:
            project_id = ProjectId(UUID(project_id_str))
            return self._save_project_command.execute(project_id)
        except (ValueError, AttributeError) as e:
            from doc_helper.domain.common.result import Failure
            return Failure(f"Invalid project ID: {e}")

    def get_project(self, project_id_str: str) -> Result[Optional[ProjectDTO], str]:
        """Get project by string ID.

        Args:
            project_id_str: Project ID as string (UUID format)

        Returns:
            Success(ProjectDTO) if found
            Success(None) if not found
            Failure(error) if query failed
        """
        # Import domain type locally
        from doc_helper.domain.project.project_ids import ProjectId

        try:
            project_id = ProjectId(UUID(project_id_str))
            return self._get_project_query.execute(project_id)
        except (ValueError, AttributeError) as e:
            from doc_helper.domain.common.result import Failure
            return Failure(f"Invalid project ID: {e}")

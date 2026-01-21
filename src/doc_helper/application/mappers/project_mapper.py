"""Project mapper - Domain → DTO conversion.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- ONE-WAY mapping: Domain → DTO only
- NO to_domain() or from_dto() methods
"""

from doc_helper.application.dto import ProjectDTO, ProjectSummaryDTO
from doc_helper.domain.project.project import Project


class ProjectMapper:
    """Maps Project domain aggregate to ProjectDTO for UI display.

    This mapper is ONE-WAY: Domain → DTO only.
    There is NO reverse mapping (to_domain, from_dto).
    Undo functionality uses UndoState DTOs, not reverse mapping.
    """

    @staticmethod
    def to_dto(project: Project) -> ProjectDTO:
        """Convert Project domain aggregate to ProjectDTO.

        v2 PHASE 4: Includes app_type_id for UI display.

        Args:
            project: Project domain aggregate

        Returns:
            ProjectDTO for UI display
        """
        return ProjectDTO(
            id=str(project.id.value),
            name=project.name,
            description=project.description,
            file_path=project.file_path,
            entity_definition_id=str(project.entity_definition_id.value),
            app_type_id=project.app_type_id,  # v2 PHASE 4
            field_count=project.field_count,
            is_saved=project.is_saved,
        )

    @staticmethod
    def to_summary_dto(project: Project) -> ProjectSummaryDTO:
        """Convert Project domain aggregate to ProjectSummaryDTO.

        Args:
            project: Project domain aggregate

        Returns:
            ProjectSummaryDTO for list display
        """
        return ProjectSummaryDTO(
            id=str(project.id.value),
            name=project.name,
            file_path=project.file_path,
            is_saved=project.is_saved,
        )

    # ❌ FORBIDDEN: No to_domain() method
    # ❌ FORBIDDEN: No from_dto() method
    # ❌ FORBIDDEN: No reverse mapping
    # Reason: Mappers are one-way only (unified_upgrade_plan.md H3)

"""Command for opening a project.

RULES (IMPLEMENTATION_RULES.md Section 5):
- Commands take IDs and primitive data, NOT domain objects
- Domain objects are loaded internally and never cross boundaries

ADR-031: Undo History Persistence
- Restores undo history after successful project open
- Undo history restoration is best-effort (failure doesn't prevent open)
- Reconstructs undo commands with fresh runtime dependencies

v2 PHASE 3: AppType-aware project lifecycle enforcement.
Validates that project's AppType exists in registry before opening.
"""

from typing import Optional

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.application.dto.project_dto import ProjectDTO
from doc_helper.application.mappers.project_mapper import ProjectMapper
from doc_helper.application.undo.undo_history_repository import IUndoHistoryRepository
from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.application.undo.undo_persistence_dto import UndoCommandPersistenceDTO
from doc_helper.application.undo.undoable_command import UndoableCommand
from doc_helper.application.undo.field_undo_command import SetFieldValueCommand, IFieldService
from doc_helper.platform.registry.interfaces import IAppTypeRegistry


class OpenProjectCommand:
    """Command to open a project.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Command handlers are stateless (dependencies injected)
    - Commands return Result[ProjectDTO, str] (DTO-only boundary)
    - Commands take IDs, not domain objects

    ADR-031: After successfully loading project, restores undo history
    to allow undo/redo continuation from previous session. Undo restoration
    failure is non-blocking (logs warning, project opens with empty undo stack).

    v2 PHASE 3 (AGENT_RULES.md Section 16):
    - Validates that project's app_type_id exists in registry after loading
    - Returns clear error if AppType not found or incompatible
    - Enforces AppType as first-class invariant of project lifecycle

    Example:
        command = OpenProjectCommand(
            project_repository=repo,
            app_type_registry=registry,
            undo_history_repository=undo_repo,
            undo_manager=undo_mgr,
            field_service=field_svc
        )
        result = command.execute(project_id=project_id)
        if isinstance(result, Success):
            project_dto = result.value  # ProjectDTO, not domain Project
            print(f"Project opened: {project_dto.name}")
    """

    def __init__(
        self,
        project_repository: IProjectRepository,
        app_type_registry: IAppTypeRegistry,
        undo_history_repository: Optional[IUndoHistoryRepository] = None,
        undo_manager: Optional[UndoManager] = None,
        field_service: Optional[IFieldService] = None,
    ) -> None:
        """Initialize command.

        Args:
            project_repository: Repository for loading projects
            app_type_registry: Registry for validating AppType existence
            undo_history_repository: Repository for loading undo history (optional)
            undo_manager: Undo manager for importing undo state (optional)
            field_service: Field service for reconstructing undo commands (optional)
        """
        if not isinstance(project_repository, IProjectRepository):
            raise TypeError("project_repository must implement IProjectRepository")
        if not isinstance(app_type_registry, IAppTypeRegistry):
            raise TypeError("app_type_registry must implement IAppTypeRegistry")
        self._project_repository = project_repository
        self._app_type_registry = app_type_registry
        self._undo_history_repository = undo_history_repository
        self._undo_manager = undo_manager
        self._field_service = field_service

    def execute(self, project_id: ProjectId) -> Result[ProjectDTO, str]:
        """Execute open project command.

        ADR-031: After successful load, restores undo history for session continuation.
        v2 PHASE 3: Validates that project's AppType exists in registry.

        Args:
            project_id: ID of project to open

        Returns:
            Success(ProjectDTO) if loaded, Failure(error) otherwise

        Validation Failures:
            - "project_id must be a ProjectId" - Invalid project ID type
            - "Failed to load project: ..." - Repository load failed
            - "Project not found: ..." - Project ID doesn't exist
            - "Cannot open project: AppType '{id}' not found. Available: ..." - AppType missing
        """
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        # Load project
        load_result = self._project_repository.get_by_id(project_id)
        if isinstance(load_result, Failure):
            return Failure(f"Failed to load project: {load_result.error}")

        project = load_result.value
        if project is None:
            return Failure(f"Project not found: {project_id.value}")

        # v2 PHASE 3: Validate project's AppType exists in registry
        if not self._app_type_registry.exists(project.app_type_id):
            available = self._app_type_registry.list_app_type_ids()
            available_str = ", ".join(sorted(available)) if available else "none"
            return Failure(
                f"Cannot open project: AppType '{project.app_type_id}' not found. "
                f"Available AppTypes: {available_str}. "
                f"The project requires AppType '{project.app_type_id}' which is not installed or registered."
            )

        # ADR-031: Restore undo history after successful project load
        # (failure is non-blocking - logs warning, opens with empty undo stack)
        self._restore_undo_history(project_id)

        # Map domain entity to DTO (domain objects never cross Application boundary)
        return Success(ProjectMapper.to_dto(project))

    def _restore_undo_history(self, project_id: ProjectId) -> None:
        """Restore undo history after successful project load.

        ADR-031: Best-effort restoration - failure logs warning but doesn't block.
        Commands are reconstructed with fresh runtime dependencies.

        Args:
            project_id: Project ID for undo history
        """
        # Skip if undo restoration not configured
        if (
            self._undo_history_repository is None
            or self._undo_manager is None
            or self._field_service is None
        ):
            return

        try:
            # Load undo history from repository
            load_result = self._undo_history_repository.load(
                project_id=str(project_id.value)
            )

            if isinstance(load_result, Failure):
                # ADR-031: Non-blocking failure - log warning
                print(
                    f"Warning: Failed to load undo history: {load_result.error}"
                )
                return

            undo_history_dto = load_result.value

            # No persisted undo history (new project or first open after feature)
            if undo_history_dto is None:
                return

            # Create command factory for reconstruction
            def command_factory(
                persistence_dto: UndoCommandPersistenceDTO,
            ) -> Optional[UndoableCommand]:
                """Reconstruct undo command from persistence DTO.

                ADR-031: Injects fresh runtime dependencies when reconstructing commands.

                Args:
                    persistence_dto: Persistence DTO containing command state

                Returns:
                    Reconstructed command or None if reconstruction fails
                """
                try:
                    if persistence_dto.command_type == "field_value":
                        # Reconstruct UndoFieldState from persistence DTO
                        state = persistence_dto.to_field_state()

                        # Create new command with fresh field_service dependency
                        return SetFieldValueCommand(
                            project_id=str(project_id.value),
                            state=state,
                            field_service=self._field_service,  # Fresh dependency
                        )

                    # TODO: Add support for override commands when implemented
                    # elif persistence_dto.command_type == "override":
                    #     state = persistence_dto.to_override_state()
                    #     return OverrideUndoCommand(...)

                    # Unknown command type - skip
                    print(
                        f"Warning: Unknown command type during undo restoration: "
                        f"{persistence_dto.command_type}"
                    )
                    return None

                except (ValueError, KeyError) as e:
                    # ADR-031: Best-effort - skip corrupted commands
                    print(
                        f"Warning: Failed to reconstruct undo command: {str(e)}"
                    )
                    return None

            # Restore undo/redo stacks in undo manager
            self._undo_manager.import_state(undo_history_dto, command_factory)

        except Exception as e:
            # ADR-031: Non-blocking failure - log warning
            print(f"Warning: Exception while restoring undo history: {str(e)}")

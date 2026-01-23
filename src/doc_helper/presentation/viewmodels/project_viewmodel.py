"""ViewModel for Project management.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md):
- Presentation layer uses DTOs, NOT domain objects
- Domain objects NEVER cross Application boundary
- Presentation passes string IDs to Application layer

UNDO/REDO (unified_upgrade_plan_FINAL.md U6 Phase 4):
- ViewModel uses FieldUndoService instead of UpdateFieldCommand directly
- ViewModel provides undo(), redo(), can_undo, can_redo for UI binding
- ViewModel subscribes to HistoryAdapter signals for state change notifications
- Undo stack cleared on project close/open (NOT on save)

ARCHITECTURE ENFORCEMENT (Rule 0 Compliance):
- ViewModel depends ONLY on Application layer use-cases and services
- NO command imports
- NO query imports
- NO facade imports
- NO repository access (direct or reach-through)
- NO domain ID unwrapping
- All orchestration delegated to Application layer
"""

from typing import Any, Optional

from doc_helper.application.dto import (
    EntityDefinitionDTO,
    EvaluationResultDTO,
    ExportResultDTO,
    FieldHistoryResultDTO,
    ImportResultDTO,
    ProjectDTO,
    SearchResultDTO,
    ValidationErrorDTO,
    ValidationResultDTO,
)
from doc_helper.application.mappers import EvaluationResultMapper, ValidationMapper
from doc_helper.application.services.control_service import ControlService
from doc_helper.application.services.field_undo_service import FieldUndoService
from doc_helper.application.services.formula_service import FormulaService
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.application.usecases.project_usecases import ProjectUseCases
from doc_helper.presentation.adapters.history_adapter import HistoryAdapter
from doc_helper.presentation.adapters.navigation_adapter import NavigationAdapter
from doc_helper.presentation.viewmodels.base_viewmodel import BaseViewModel


class ProjectViewModel(BaseViewModel):
    """ViewModel for Project management.

    Coordinates project editing, validation, formulas, and controls.

    Responsibilities:
    - Load and save projects
    - Update field values
    - Trigger formula evaluation
    - Trigger control rule evaluation
    - Track unsaved changes
    - Provide validation status

    NOTE: This ViewModel stores DTOs, not domain objects.
    Domain objects are handled internally by commands/queries.

    Example:
        vm = ProjectViewModel(services...)
        vm.load_project(project_id, entity_definition_dto)
        vm.update_field(field_id, new_value)
        vm.save_project()
    """

    def __init__(
        self,
        project_usecases: ProjectUseCases,
        validation_service: ValidationService,
        formula_service: FormulaService,
        control_service: ControlService,
        field_undo_service: FieldUndoService,
        history_adapter: HistoryAdapter,
        navigation_adapter: NavigationAdapter,
    ) -> None:
        """Initialize ProjectViewModel.

        ARCHITECTURE ENFORCEMENT (Rule 0 Compliance):
            ViewModel receives ONLY Application layer use-cases and services.
            NO commands, queries, facades, or repositories are injected.

        Args:
            project_usecases: Use-case class for ALL project operations
            validation_service: Service for validation
            formula_service: Service for formula evaluation
            control_service: Service for control rule evaluation
            field_undo_service: Undo-enabled field update service (U6 Phase 4)
            history_adapter: Qt signal bridge for undo/redo state (U6 Phase 4)
            navigation_adapter: Qt signal bridge for navigation state (U7)
        """
        super().__init__()
        self._project_usecases = project_usecases
        self._validation_service = validation_service
        self._formula_service = formula_service
        self._control_service = control_service
        self._field_undo_service = field_undo_service
        self._history_adapter = history_adapter
        self._navigation_adapter = navigation_adapter

        # Store IDs and DTOs, NOT domain objects
        self._project_id: Optional[str] = None
        self._project_dto: Optional[ProjectDTO] = None
        self._entity_definition_dto: Optional[EntityDefinitionDTO] = None
        self._has_unsaved_changes = False
        self._is_loading = False
        self._error_message: Optional[str] = None

        # Subscribe to undo/redo state changes (U6 Phase 4)
        self._history_adapter.can_undo_changed.connect(self._on_undo_state_changed)
        self._history_adapter.can_redo_changed.connect(self._on_redo_state_changed)

    @property
    def project_id(self) -> Optional[str]:
        """Get current project ID.

        Returns:
            Project ID as string or None
        """
        return self._project_id

    @property
    def current_project(self) -> Optional[ProjectDTO]:
        """Get currently loaded project DTO.

        Returns:
            Current ProjectDTO or None
        """
        return self._project_dto

    @property
    def entity_definition(self) -> Optional[EntityDefinitionDTO]:
        """Get entity definition DTO for current project.

        Returns:
            EntityDefinitionDTO or None
        """
        return self._entity_definition_dto

    @property
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes.

        Returns:
            True if project has unsaved changes
        """
        return self._has_unsaved_changes

    @property
    def is_loading(self) -> bool:
        """Check if project is being loaded.

        Returns:
            True if loading
        """
        return self._is_loading

    @property
    def error_message(self) -> Optional[str]:
        """Get current error message.

        Returns:
            Error message if any
        """
        return self._error_message

    @property
    def project_name(self) -> str:
        """Get current project name.

        Returns:
            Project name or empty string
        """
        return self._project_dto.name if self._project_dto else ""

    def load_project(
        self,
        project_id: str,
        entity_definition: EntityDefinitionDTO,
    ) -> bool:
        """Load a project.

        PHASE 6C: Now accepts string project_id instead of domain ProjectId.
        Domain ID construction happens in Application layer.

        Args:
            project_id: ID of project to load (string UUID format)
            entity_definition: Entity definition DTO for the project

        Returns:
            True if loaded successfully

        Side Effects:
            - Clears undo/redo stacks (per unified_upgrade_plan_FINAL.md v1.3.1)
            - Project open is an edit boundary

        Note:
            Undo stack is cleared on project close/open, NOT on save.
            User expectation: "I opened a different project, start fresh editing session."
        """
        # Clear undo/redo stacks BEFORE loading new project (project open is an edit boundary)
        self._history_adapter.clear()

        self._is_loading = True
        self._error_message = None
        self.notify_change("is_loading")
        self.notify_change("error_message")

        try:
            # Use ProjectUseCases which accepts string ID
            result = self._project_usecases.get_project(project_id)

            if result.is_success():
                project_dto = result.value
                if project_dto is None:
                    self._error_message = f"Project not found: {project_id}"
                    return False

                # Store IDs and DTOs
                self._project_id = project_id
                self._project_dto = project_dto
                self._entity_definition_dto = entity_definition
                self._has_unsaved_changes = False

                self.notify_change("project_id")
                self.notify_change("current_project")
                self.notify_change("entity_definition")
                self.notify_change("has_unsaved_changes")
                self.notify_change("project_name")

                return True
            else:
                self._error_message = f"Failed to load project: {result.error}"
                return False

        except Exception as e:
            self._error_message = f"Error loading project: {str(e)}"
            return False

        finally:
            self._is_loading = False
            self.notify_change("is_loading")
            self.notify_change("error_message")

    def update_field(
        self,
        field_id: str,
        value: Any,
    ) -> bool:
        """Update a field value with undo support.

        Args:
            field_id: Field ID as string (DTO-only MVVM compliance)
            value: New value

        Returns:
            True if updated successfully

        Side Effects (U6 Phase 4):
            - Creates undoable command
            - Adds command to undo stack
            - Clears redo stack (standard undo semantics)
            - Triggers formula recalc, control eval, validation

        Note:
            Now uses FieldUndoService instead of UpdateFieldCommand directly.
            This makes field changes undoable via Ctrl+Z.
        """
        if not self._project_id:
            self._error_message = "No project loaded"
            self.notify_change("error_message")
            return False

        try:
            # Use FieldUndoService for undoable field updates (U6 Phase 4)
            # OLD: result = self._update_field_command.execute(...)
            # NEW: result = self._field_undo_service.set_field_value(...)
            result = self._field_undo_service.set_field_value(
                project_id=self._project_id,
                field_id=field_id,
                new_value=value,
            )

            if result.is_success():
                # Reload project DTO to get updated state
                reload_result = self._project_usecases.get_project(
                    self._project_id
                )
                if reload_result.is_success() and reload_result.value:
                    self._project_dto = reload_result.value

                self._has_unsaved_changes = True
                self.notify_change("current_project")
                self.notify_change("has_unsaved_changes")
                return True
            else:
                self._error_message = f"Failed to update field: {result.error}"
                self.notify_change("error_message")
                return False

        except Exception as e:
            self._error_message = f"Error updating field: {str(e)}"
            self.notify_change("error_message")
            return False

    def save_project(self) -> bool:
        """Save current project.

        Uses ProjectUseCases which accepts string ID.

        Returns:
            True if saved successfully
        """
        if not self._project_id:
            self._error_message = "No project loaded"
            self.notify_change("error_message")
            return False

        try:
            # Use ProjectUseCases which accepts string ID
            result = self._project_usecases.save_project(self._project_id)

            if result.is_success():
                self._has_unsaved_changes = False
                self._error_message = None
                self.notify_change("has_unsaved_changes")
                self.notify_change("error_message")
                return True
            else:
                self._error_message = f"Failed to save project: {result.error}"
                self.notify_change("error_message")
                return False

        except Exception as e:
            self._error_message = f"Error saving project: {str(e)}"
            self.notify_change("error_message")
            return False

    def validate_project(self) -> ValidationResultDTO:
        """Validate current project.

        PHASE 6C: Uses string-accepting service method.

        Returns:
            ValidationResultDTO with errors
        """
        if not self._project_id or not self._entity_definition_dto:
            return ValidationResultDTO(
                is_valid=False,
                errors=(
                    ValidationErrorDTO(
                        field_id=None, field_path="", message="No project loaded"
                    ),
                ),
            )

        # Use string-accepting service method (Phase 6C)
        result = self._validation_service.validate_by_project_id_str(self._project_id)

        if result.is_failure():
            return ValidationResultDTO(
                is_valid=False,
                errors=(
                    ValidationErrorDTO(
                        field_id=None,
                        field_path="",
                        message=f"Validation failed: {result.error}",
                    ),
                ),
            )

        # Map domain result to DTO
        return ValidationMapper.to_dto(result.value)

    def evaluate_controls(self) -> Optional[EvaluationResultDTO]:
        """Evaluate control rules for current project.

        PHASE 6C: Uses string-accepting service method.

        Returns:
            EvaluationResultDTO if successful, None otherwise
        """
        if not self._project_id or not self._entity_definition_dto:
            return None

        # Use string-accepting service method (Phase 6C)
        result = self._control_service.evaluate_by_project_id_str(self._project_id)

        if result.is_success():
            # Map domain result to DTO
            return EvaluationResultMapper.to_dto(result.value)
        return None

    def clear_error(self) -> None:
        """Clear current error message."""
        self._error_message = None
        self.notify_change("error_message")

    # ========== UNDO/REDO METHODS (U6 Phase 4) ==========

    @property
    def can_undo(self) -> bool:
        """Check if undo is available.

        Returns:
            True if there are commands to undo
        """
        return self._history_adapter.can_undo

    @property
    def can_redo(self) -> bool:
        """Check if redo is available.

        Returns:
            True if there are commands to redo
        """
        return self._history_adapter.can_redo

    def undo(self) -> bool:
        """Undo last operation.

        Returns:
            True if undo succeeded, False otherwise

        Side Effects:
            - Restores previous state
            - Reloads project DTO to reflect changes
            - Emits property change notifications
        """
        success = self._history_adapter.undo()

        if success and self._project_id:
            # Reload project DTO to reflect undone changes
            reload_result = self._project_usecases.get_project(
                self._project_id
            )
            if reload_result.is_success() and reload_result.value:
                self._project_dto = reload_result.value
                self.notify_change("current_project")

        return success

    def redo(self) -> bool:
        """Redo previously undone operation.

        Returns:
            True if redo succeeded, False otherwise

        Side Effects:
            - Reapplies undone change
            - Reloads project DTO to reflect changes
            - Emits property change notifications
        """
        success = self._history_adapter.redo()

        if success and self._project_id:
            # Reload project DTO to reflect redone changes
            reload_result = self._project_usecases.get_project(
                self._project_id
            )
            if reload_result.is_success() and reload_result.value:
                self._project_dto = reload_result.value
                self.notify_change("current_project")

        return success

    def close_project(self) -> None:
        """Close current project.

        Side Effects:
            - Clears undo/redo stacks (per unified_upgrade_plan_FINAL.md v1.3.1)
            - Resets project state
            - Emits property change notifications

        Note:
            Undo stack is cleared on project close/open, NOT on save.
            User expectation: "I closed the project, I'm done editing it."
        """
        # Clear undo/redo stacks (project close is an edit boundary)
        self._history_adapter.clear()

        # Reset project state
        self._project_id = None
        self._project_dto = None
        self._entity_definition_dto = None
        self._has_unsaved_changes = False
        self._error_message = None

        self.notify_change("project_id")
        self.notify_change("current_project")
        self.notify_change("entity_definition")
        self.notify_change("has_unsaved_changes")
        self.notify_change("error_message")
        self.notify_change("project_name")

        # Clear navigation history on project close (NEW - U7)
        self._navigation_adapter.clear()

    # =========================================================================
    # Navigation operations (U7)
    # =========================================================================

    def navigate_to_entity(self, entity_id: str) -> None:
        """Navigate to an entity/tab.

        Args:
            entity_id: Entity identifier to navigate to

        Note:
            In v1 with single entity, this is mainly for future compatibility.
            Navigation history is still tracked for field-level navigation.
        """
        self._navigation_adapter.navigate_to_entity(entity_id)

    def navigate_to_group(self, entity_id: str, group_id: str) -> None:
        """Navigate to a group within an entity.

        Args:
            entity_id: Entity identifier
            group_id: Group identifier
        """
        self._navigation_adapter.navigate_to_group(entity_id, group_id)

    def navigate_to_field(
        self, entity_id: str, group_id: str, field_id: str
    ) -> None:
        """Navigate to a specific field.

        Args:
            entity_id: Entity identifier
            group_id: Group identifier
            field_id: Field identifier
        """
        self._navigation_adapter.navigate_to_field(entity_id, group_id, field_id)

    def go_back(self) -> bool:
        """Navigate back in navigation history.

        Returns:
            True if navigation was performed, False if at beginning
        """
        return self._navigation_adapter.go_back()

    def go_forward(self) -> bool:
        """Navigate forward in navigation history.

        Returns:
            True if navigation was performed, False if at end
        """
        return self._navigation_adapter.go_forward()

    @property
    def can_go_back(self) -> bool:
        """Check if back navigation is available."""
        return self._navigation_adapter.can_go_back

    @property
    def can_go_forward(self) -> bool:
        """Check if forward navigation is available."""
        return self._navigation_adapter.can_go_forward

    def _on_undo_state_changed(self, can_undo: bool) -> None:
        """Handle undo state change signal from HistoryAdapter.

        Args:
            can_undo: Whether undo is now available
        """
        self.notify_change("can_undo")

    def _on_redo_state_changed(self, can_redo: bool) -> None:
        """Handle redo state change signal from HistoryAdapter.

        Args:
            can_redo: Whether redo is now available
        """
        self.notify_change("can_redo")

    # ====================================================
    # SEARCH & HISTORY (ADR-026, ADR-027)
    # ====================================================

    def search_fields(self, search_term: str) -> list[SearchResultDTO]:
        """Search for fields within the current project.

        ADR-026: Search Architecture
        Searches field labels, field IDs, and field values.

        Architecture Compliance (Rule 0):
            Delegates to ProjectUseCases (Application layer).
            NO direct query access in Presentation.

        Args:
            search_term: The search string

        Returns:
            List of SearchResultDTO instances matching the search term
            Empty list if search not available or no matches found
        """
        if not self._project_usecases or not self._project_id:
            return []

        if not search_term or len(search_term.strip()) < 2:
            return []  # Minimum 2 characters required

        return self._project_usecases.search_fields(
            project_id=self._project_id,
            search_term=search_term.strip(),
            limit=100,
        )

    def get_field_history(
        self, field_id: str, limit: Optional[int] = 20, offset: int = 0
    ) -> Optional[FieldHistoryResultDTO]:
        """Get history entries for a specific field.

        ADR-027: Field History Storage
        Returns paginated history showing field value changes over time.

        Architecture Compliance (Rule 0):
            Delegates to ProjectUseCases (Application layer).
            NO direct query access in Presentation.

        Args:
            field_id: The field ID to get history for
            limit: Maximum number of entries to return (default: 20)
            offset: Number of entries to skip (for pagination, default: 0)

        Returns:
            FieldHistoryResultDTO with entries, or None if not available
        """
        if not self._project_usecases or not self._project_id:
            return None

        return self._project_usecases.get_field_history(
            project_id=self._project_id,
            field_id=field_id,
            limit=limit,
            offset=offset,
        )

    # ====================================================
    # IMPORT/EXPORT (ADR-039) - STUBS
    # ====================================================

    def export_project(self, output_file_path: str) -> ExportResultDTO:
        """Export current project to interchange format.

        ADR-039: Import/Export Data Format
        Uses ProjectUseCases which accepts string ID.

        Args:
            output_file_path: Path where to save the export file

        Returns:
            ExportResultDTO with success/failure information
        """
        if not self._project_id:
            return ExportResultDTO(
                success=False,
                file_path=None,
                project_id="",
                project_name="",
                error_message="No project loaded.",
                format_version="1.0",
                exported_at="",
                entity_count=0,
                record_count=0,
                field_value_count=0,
            )

        # Use ProjectUseCases which accepts string ID
        result = self._project_usecases.export_project(
            self._project_id, output_file_path
        )

        if result.is_success():
            return result.value
        else:
            return ExportResultDTO(
                success=False,
                file_path=None,
                project_id=self._project_id,
                project_name=self._project_dto.name if self._project_dto else "",
                error_message=result.error,
                format_version="1.0",
                exported_at="",
                entity_count=0,
                record_count=0,
                field_value_count=0,
            )

    def import_project(self, input_file_path: str) -> ImportResultDTO:
        """Import project from interchange format.

        ADR-039: Import/Export Data Format

        Architecture Compliance (Rule 0):
            Delegates to ProjectUseCases (Application layer).
            NO direct command access in Presentation.

        Args:
            input_file_path: Path to the import file

        Returns:
            ImportResultDTO with success/failure information

        Side Effects:
            - On success, the newly imported project is NOT automatically loaded
            - Caller should prompt user to open the imported project
        """
        if not self._project_usecases:
            return ImportResultDTO(
                success=False,
                project_id="",
                project_name="",
                error_message="Import feature not available.",
                format_version="",
                imported_at="",
                entity_count=0,
                record_count=0,
                field_value_count=0,
                validation_warnings=[],
            )

        return self._project_usecases.import_project(input_file_path)

    # ====================================================

    def dispose(self) -> None:
        """Clean up resources."""
        # Unsubscribe from HistoryAdapter signals
        self._history_adapter.can_undo_changed.disconnect(self._on_undo_state_changed)
        self._history_adapter.can_redo_changed.disconnect(self._on_redo_state_changed)

        # Dispose HistoryAdapter
        self._history_adapter.dispose()

        super().dispose()
        self._project_id = None
        self._project_dto = None
        self._entity_definition_dto = None

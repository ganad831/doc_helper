"""Control service for coordinating control rule evaluation.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md):
- Services can work with domain objects internally
- Methods called from presentation should take IDs and return Results
"""

from typing import Any, Optional

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.control.control_effect import ControlEffect
from doc_helper.domain.control.effect_evaluator import (
    ControlEffectEvaluator,
    EvaluationResult,
)
from doc_helper.domain.formula.evaluator import EvaluationContext
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.schema_ids import FieldDefinitionId
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class ControlService:
    """Service for evaluating control rules and applying effects.

    Coordinates control rule evaluation across project fields,
    determining which fields should be visible, enabled, or have their values set.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Service is stateless (no instance state beyond evaluator)
    - Service coordinates domain logic, doesn't contain it
    - Returns Result monad for error handling

    Example:
        service = ControlService(project_repo, schema_repo)
        result = service.evaluate_by_project_id(project_id)
        if isinstance(result, Success):
            effects = result.value
            # Apply effects to UI
    """

    def __init__(
        self,
        project_repository: Optional[IProjectRepository] = None,
        schema_repository: Optional[ISchemaRepository] = None,
    ) -> None:
        """Initialize control service.

        Args:
            project_repository: Repository for loading projects (optional for backward compat)
            schema_repository: Repository for loading schemas (optional for backward compat)
        """
        self._evaluator = ControlEffectEvaluator()
        self._project_repository = project_repository
        self._schema_repository = schema_repository

    def evaluate_by_project_id(
        self,
        project_id: ProjectId,
    ) -> Result[EvaluationResult, str]:
        """Evaluate controls for a project by its ID.

        This method loads the project and entity definition internally,
        suitable for calling from presentation layer.

        Args:
            project_id: ID of project to evaluate controls for

        Returns:
            Success(EvaluationResult) if evaluation completes, Failure(error) otherwise
        """
        if not self._project_repository:
            return Failure("ControlService requires project_repository for evaluate_by_project_id")
        if not self._schema_repository:
            return Failure("ControlService requires schema_repository for evaluate_by_project_id")
        if not isinstance(project_id, ProjectId):
            return Failure("project_id must be a ProjectId")

        # Load project
        project_result = self._project_repository.get_by_id(project_id)
        if isinstance(project_result, Failure):
            return Failure(f"Failed to load project: {project_result.error}")

        project = project_result.value
        if project is None:
            return Failure(f"Project not found: {project_id.value}")

        # Load entity definition
        entity_def_result = self._schema_repository.get_entity_definition(
            project.entity_definition_id
        )
        if isinstance(entity_def_result, Failure):
            return Failure(f"Failed to load entity definition: {entity_def_result.error}")

        entity_definition = entity_def_result.value
        if entity_definition is None:
            return Failure(f"Entity definition not found: {project.entity_definition_id.value}")

        # Evaluate controls
        return self.evaluate_controls(project, entity_definition)

    def evaluate_controls(
        self,
        project: Project,
        entity_definition: EntityDefinition,
    ) -> Result[EvaluationResult, str]:
        """Evaluate all control rules for a project.

        Args:
            project: Project to evaluate controls for
            entity_definition: Entity definition with control rules

        Returns:
            Success(EvaluationResult) if successful, Failure(error) otherwise
        """
        if not isinstance(project, Project):
            return Failure("project must be a Project instance")
        if not isinstance(entity_definition, EntityDefinition):
            return Failure("entity_definition must be an EntityDefinition")

        # Build field values dict for evaluation context
        field_values = {
            field_id.value: field_value.value
            for field_id, field_value in project.field_values.items()
        }

        # Get all control rules from entity definition
        control_rules = []
        for field_def in entity_definition.fields.values():
            if field_def.control_rules:
                control_rules.extend(field_def.control_rules)

        # Evaluate control rules
        return Success(self._evaluator.evaluate_rules(control_rules, field_values))

    def get_effects_for_field(
        self,
        field_id: FieldDefinitionId,
        evaluation_result: EvaluationResult,
    ) -> tuple[ControlEffect, ...]:
        """Get control effects that apply to a specific field.

        Args:
            field_id: Field to get effects for
            evaluation_result: Result of control evaluation

        Returns:
            Tuple of effects targeting the field
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")
        if not isinstance(evaluation_result, EvaluationResult):
            raise TypeError("evaluation_result must be an EvaluationResult")

        return evaluation_result.get_effects_for_field(field_id)

    def should_field_be_visible(
        self,
        field_id: FieldDefinitionId,
        evaluation_result: EvaluationResult,
        default_visible: bool = True,
    ) -> bool:
        """Check if a field should be visible based on control effects.

        Args:
            field_id: Field to check
            evaluation_result: Result of control evaluation
            default_visible: Default visibility if no effects apply

        Returns:
            True if field should be visible
        """
        from doc_helper.domain.control.control_effect import ControlType

        effects = self.get_effects_for_field(field_id, evaluation_result)

        # Check for visibility effects
        for effect in effects:
            if effect.control_type == ControlType.VISIBILITY:
                return bool(effect.value)

        return default_visible

    def should_field_be_enabled(
        self,
        field_id: FieldDefinitionId,
        evaluation_result: EvaluationResult,
        default_enabled: bool = True,
    ) -> bool:
        """Check if a field should be enabled based on control effects.

        Args:
            field_id: Field to check
            evaluation_result: Result of control evaluation
            default_enabled: Default enabled state if no effects apply

        Returns:
            True if field should be enabled
        """
        from doc_helper.domain.control.control_effect import ControlType

        effects = self.get_effects_for_field(field_id, evaluation_result)

        # Check for enable effects
        for effect in effects:
            if effect.control_type == ControlType.ENABLE:
                return bool(effect.value)

        return default_enabled

    def get_field_value_override(
        self,
        field_id: FieldDefinitionId,
        evaluation_result: EvaluationResult,
    ) -> Any | None:
        """Get value override for a field from control effects.

        Args:
            field_id: Field to check
            evaluation_result: Result of control evaluation

        Returns:
            Override value if VALUE_SET effect exists, None otherwise
        """
        from doc_helper.domain.control.control_effect import ControlType

        effects = self.get_effects_for_field(field_id, evaluation_result)

        # Check for value set effects (use last one if multiple)
        for effect in reversed(effects):
            if effect.control_type == ControlType.VALUE_SET:
                return effect.value

        return None

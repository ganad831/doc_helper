"""Control service for coordinating control rule evaluation."""

from typing import Any

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.control.control_effect import ControlEffect
from doc_helper.domain.control.effect_evaluator import (
    ControlEffectEvaluator,
    EvaluationResult,
)
from doc_helper.domain.formula.evaluator import EvaluationContext
from doc_helper.domain.project.project import Project
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class ControlService:
    """Service for evaluating control rules and applying effects.

    Coordinates control rule evaluation across project fields,
    determining which fields should be visible, enabled, or have their values set.

    RULES (IMPLEMENTATION_RULES.md Section 5):
    - Service is stateless (no instance state beyond evaluator)
    - Service coordinates domain logic, doesn't contain it
    - Returns Result monad for error handling

    Example:
        service = ControlService()
        result = service.evaluate_controls(
            project=project,
            entity_definition=entity_definition
        )
        if isinstance(result, Success):
            effects = result.value
            # Apply effects to UI
    """

    def __init__(self) -> None:
        """Initialize control service."""
        self._evaluator = ControlEffectEvaluator()

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

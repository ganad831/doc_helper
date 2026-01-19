"""Control effect evaluator.

Evaluates control rules to determine which effects should be applied.
"""

from dataclasses import dataclass
from typing import Any

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.control.control_effect import ControlEffect
from doc_helper.domain.control.control_rule import ControlRule
from doc_helper.domain.formula.evaluator import FormulaEvaluator, EvaluationContext
from doc_helper.domain.formula.parser import FormulaParser
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


@dataclass(frozen=True)
class EvaluationResult:
    """Result of evaluating control rules.

    Contains the effects that should be applied based on rule evaluation.
    """

    effects: tuple  # Tuple[ControlEffect, ...]
    errors: tuple  # Tuple[str, ...] - Evaluation errors (non-fatal)

    def __post_init__(self) -> None:
        """Validate evaluation result."""
        if not isinstance(self.effects, tuple):
            raise TypeError("effects must be a tuple")
        if not all(isinstance(effect, ControlEffect) for effect in self.effects):
            raise TypeError("effects must contain only ControlEffect instances")
        if not isinstance(self.errors, tuple):
            raise TypeError("errors must be a tuple")
        if not all(isinstance(error, str) for error in self.errors):
            raise TypeError("errors must contain only strings")

    @property
    def has_effects(self) -> bool:
        """Check if any effects should be applied.

        Returns:
            True if there are effects to apply
        """
        return len(self.effects) > 0

    @property
    def has_errors(self) -> bool:
        """Check if there were evaluation errors.

        Returns:
            True if there were errors
        """
        return len(self.errors) > 0

    def get_effects_for_field(
        self, field_id: FieldDefinitionId
    ) -> tuple:  # Tuple[ControlEffect, ...]
        """Get effects targeting a specific field.

        Args:
            field_id: Field to get effects for

        Returns:
            Tuple of effects targeting the field
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")
        return tuple(e for e in self.effects if e.target_field_id == field_id)


class ControlEffectEvaluator:
    """Evaluates control rules to determine which effects should be applied.

    The evaluator:
    - Evaluates rule conditions using the formula evaluator
    - Returns effects for rules where conditions are true
    - Handles enabled/disabled rules
    - Supports priority-based conflict resolution

    Example:
        # Evaluate rules
        evaluator = ControlEffectEvaluator()
        result = evaluator.evaluate_rules(
            rules=[rule1, rule2, rule3],
            field_values={"field1": 100, "field2": "test"},
            functions={"min": min, "max": max}
        )

        # Apply effects
        for effect in result.effects:
            apply_effect(effect)
    """

    def evaluate_rules(
        self,
        rules: list,  # List[ControlRule]
        field_values: dict,  # Dict[str, Any]
        functions: dict = None,  # Dict[str, Callable]
    ) -> EvaluationResult:
        """Evaluate a list of control rules.

        Args:
            rules: List of control rules to evaluate
            field_values: Current field values for condition evaluation
            functions: Optional functions available for formula evaluation

        Returns:
            EvaluationResult with effects to apply and any errors
        """
        if not isinstance(rules, list):
            raise TypeError("rules must be a list")
        if not all(isinstance(rule, ControlRule) for rule in rules):
            raise TypeError("rules must contain only ControlRule instances")
        if not isinstance(field_values, dict):
            raise TypeError("field_values must be a dict")
        if functions is not None and not isinstance(functions, dict):
            raise TypeError("functions must be a dict or None")

        if functions is None:
            functions = {}

        effects = []
        errors = []

        # Sort rules by priority (higher priority first)
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            # Skip disabled rules
            if not rule.is_enabled:
                continue

            # Evaluate rule condition
            result = self._evaluate_condition(rule.condition, field_values, functions)

            if isinstance(result, Failure):
                errors.append(
                    f"Rule '{rule.id.value}' condition evaluation failed: {result.error}"
                )
                continue

            # If condition is true, add effect
            if result.value is True:
                effects.append(rule.effect)

        return EvaluationResult(effects=tuple(effects), errors=tuple(errors))

    def evaluate_rule(
        self,
        rule: ControlRule,
        field_values: dict,  # Dict[str, Any]
        functions: dict = None,  # Dict[str, Callable]
    ) -> Result[bool, str]:
        """Evaluate a single control rule.

        Args:
            rule: Control rule to evaluate
            field_values: Current field values for condition evaluation
            functions: Optional functions available for formula evaluation

        Returns:
            Success(True) if condition is true, Success(False) if false, Failure if error
        """
        if not isinstance(rule, ControlRule):
            raise TypeError("rule must be a ControlRule")
        if not isinstance(field_values, dict):
            raise TypeError("field_values must be a dict")
        if functions is not None and not isinstance(functions, dict):
            raise TypeError("functions must be a dict or None")

        if functions is None:
            functions = {}

        # Skip disabled rules
        if not rule.is_enabled:
            return Success(False)

        # Evaluate condition
        return self._evaluate_condition(rule.condition, field_values, functions)

    def _evaluate_condition(
        self, condition: str, field_values: dict, functions: dict
    ) -> Result[bool, str]:
        """Evaluate a condition formula.

        Args:
            condition: Formula string to evaluate
            field_values: Current field values
            functions: Available functions

        Returns:
            Success(True/False) if evaluation succeeds, Failure if error
        """
        try:
            # Parse condition
            parser = FormulaParser(condition)
            ast = parser.parse()

            # Evaluate condition
            context = EvaluationContext(field_values=field_values, functions=functions)
            evaluator = FormulaEvaluator(context)
            result = evaluator.evaluate(ast)

            if isinstance(result, Failure):
                return Failure(f"Condition evaluation failed: {result.error}")

            # Ensure result is boolean
            if not isinstance(result.value, bool):
                return Failure(
                    f"Condition must evaluate to boolean, got {type(result.value).__name__}"
                )

            return Success(result.value)

        except Exception as e:
            return Failure(f"Error evaluating condition: {str(e)}")

    def resolve_conflicts(
        self, effects: list  # List[ControlEffect]
    ) -> list:  # List[ControlEffect]
        """Resolve conflicts when multiple effects target the same field.

        When multiple effects target the same field, keep only the first one
        (which comes from the highest priority rule due to sorting).

        Args:
            effects: List of effects (assumed to be priority-sorted)

        Returns:
            List of effects with conflicts resolved
        """
        if not isinstance(effects, list):
            raise TypeError("effects must be a list")
        if not all(isinstance(effect, ControlEffect) for effect in effects):
            raise TypeError("effects must contain only ControlEffect instances")

        seen_targets = set()
        resolved = []

        for effect in effects:
            field_id = effect.target_field_id
            if field_id not in seen_targets:
                seen_targets.add(field_id)
                resolved.append(effect)

        return resolved

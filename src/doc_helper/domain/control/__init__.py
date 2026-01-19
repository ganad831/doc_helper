"""Control domain.

Controls are conditional rules that affect field behavior:
- VALUE_SET: Set field value when condition is true
- VISIBILITY: Show/hide fields based on conditions
- ENABLE: Enable/disable fields based on conditions
"""

from doc_helper.domain.control.control_effect import ControlEffect, ControlType
from doc_helper.domain.control.control_rule import ControlRule
from doc_helper.domain.control.effect_evaluator import ControlEffectEvaluator, EvaluationResult

__all__ = [
    "ControlType",
    "ControlEffect",
    "ControlRule",
    "ControlEffectEvaluator",
    "EvaluationResult",
]

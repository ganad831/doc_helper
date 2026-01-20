"""Control mappers - Domain → DTO conversion.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- ONE-WAY mapping: Domain → DTO only
- NO to_domain() or from_dto() methods
"""

from doc_helper.application.dto import ControlEffectDTO, EvaluationResultDTO
from doc_helper.domain.control.control_effect import ControlEffect
from doc_helper.domain.control.effect_evaluator import EvaluationResult


class ControlEffectMapper:
    """Maps ControlEffect domain value object to ControlEffectDTO.

    This mapper is ONE-WAY: Domain → DTO only.
    """

    @staticmethod
    def to_dto(effect: ControlEffect) -> ControlEffectDTO:
        """Convert ControlEffect to ControlEffectDTO.

        Args:
            effect: ControlEffect domain value object

        Returns:
            ControlEffectDTO for UI display
        """
        return ControlEffectDTO(
            control_type=effect.control_type.value,
            target_field_id=str(effect.target_field_id.value),
            value=effect.value,
        )

    # ❌ FORBIDDEN: No to_domain() or from_dto() methods


class EvaluationResultMapper:
    """Maps EvaluationResult to EvaluationResultDTO.

    This mapper is ONE-WAY: Domain → DTO only.
    """

    @staticmethod
    def to_dto(result: EvaluationResult) -> EvaluationResultDTO:
        """Convert EvaluationResult to EvaluationResultDTO.

        Args:
            result: EvaluationResult domain value object

        Returns:
            EvaluationResultDTO for UI display
        """
        effect_dtos = tuple(
            ControlEffectMapper.to_dto(effect)
            for effect in result.effects
        )

        return EvaluationResultDTO(
            effects=effect_dtos,
            errors=result.errors,
        )

    # ❌ FORBIDDEN: No to_domain() or from_dto() methods

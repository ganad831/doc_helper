"""Unit tests for ControlEffectMapper and EvaluationResultMapper."""

import pytest

from doc_helper.application.dto import ControlEffectDTO, EvaluationResultDTO
from doc_helper.application.mappers import ControlEffectMapper, EvaluationResultMapper
from doc_helper.domain.control.control_effect import ControlEffect, ControlType
from doc_helper.domain.control.effect_evaluator import EvaluationResult
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class TestControlEffectMapper:
    """Tests for ControlEffectMapper."""

    def test_to_dto_value_set(self) -> None:
        """to_dto should convert VALUE_SET effect to DTO."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field_1"),
            value="computed_value",
        )

        dto = ControlEffectMapper.to_dto(effect)

        assert isinstance(dto, ControlEffectDTO)
        assert dto.control_type == "value_set"
        assert dto.target_field_id == "field_1"
        assert dto.value == "computed_value"

    def test_to_dto_visibility(self) -> None:
        """to_dto should convert VISIBILITY effect to DTO."""
        effect = ControlEffect(
            control_type=ControlType.VISIBILITY,
            target_field_id=FieldDefinitionId("field_2"),
            value=False,
        )

        dto = ControlEffectMapper.to_dto(effect)

        assert dto.control_type == "visibility"
        assert dto.target_field_id == "field_2"
        assert dto.value is False

    def test_to_dto_enable(self) -> None:
        """to_dto should convert ENABLE effect to DTO."""
        effect = ControlEffect(
            control_type=ControlType.ENABLE,
            target_field_id=FieldDefinitionId("field_3"),
            value=True,
        )

        dto = ControlEffectMapper.to_dto(effect)

        assert dto.control_type == "enable"
        assert dto.target_field_id == "field_3"
        assert dto.value is True

    def test_to_dto_is_immutable(self) -> None:
        """ControlEffectDTO should be immutable (frozen)."""
        effect = ControlEffect(
            control_type=ControlType.VALUE_SET,
            target_field_id=FieldDefinitionId("field_1"),
            value="test",
        )
        dto = ControlEffectMapper.to_dto(effect)

        with pytest.raises(Exception):  # frozen dataclass raises
            dto.value = "changed"  # type: ignore

    def test_no_reverse_mapping(self) -> None:
        """ControlEffectMapper should NOT have reverse mapping methods."""
        assert not hasattr(ControlEffectMapper, "to_domain")
        assert not hasattr(ControlEffectMapper, "from_dto")


class TestEvaluationResultMapper:
    """Tests for EvaluationResultMapper."""

    def test_to_dto_with_effects(self) -> None:
        """to_dto should convert EvaluationResult with effects to DTO."""
        effects = (
            ControlEffect(
                control_type=ControlType.VALUE_SET,
                target_field_id=FieldDefinitionId("field_1"),
                value="value_1",
            ),
            ControlEffect(
                control_type=ControlType.VISIBILITY,
                target_field_id=FieldDefinitionId("field_2"),
                value=True,
            ),
        )
        result = EvaluationResult(effects=effects, errors=())

        dto = EvaluationResultMapper.to_dto(result)

        assert isinstance(dto, EvaluationResultDTO)
        assert len(dto.effects) == 2
        assert dto.effects[0].control_type == "value_set"
        assert dto.effects[0].target_field_id == "field_1"
        assert dto.effects[1].control_type == "visibility"
        assert dto.effects[1].target_field_id == "field_2"
        assert len(dto.errors) == 0
        assert dto.has_effects is True
        assert dto.has_errors is False

    def test_to_dto_with_errors(self) -> None:
        """to_dto should convert EvaluationResult with errors to DTO."""
        result = EvaluationResult(
            effects=(),
            errors=("Error 1", "Error 2"),
        )

        dto = EvaluationResultMapper.to_dto(result)

        assert len(dto.effects) == 0
        assert len(dto.errors) == 2
        assert dto.errors == ("Error 1", "Error 2")
        assert dto.has_effects is False
        assert dto.has_errors is True

    def test_to_dto_empty(self) -> None:
        """to_dto should convert empty EvaluationResult to DTO."""
        result = EvaluationResult(effects=(), errors=())

        dto = EvaluationResultMapper.to_dto(result)

        assert len(dto.effects) == 0
        assert len(dto.errors) == 0
        assert dto.has_effects is False
        assert dto.has_errors is False

    def test_to_dto_is_immutable(self) -> None:
        """EvaluationResultDTO should be immutable (frozen)."""
        result = EvaluationResult(effects=(), errors=())
        dto = EvaluationResultMapper.to_dto(result)

        with pytest.raises(Exception):  # frozen dataclass raises
            dto.errors = ("new error",)  # type: ignore

    def test_no_reverse_mapping(self) -> None:
        """EvaluationResultMapper should NOT have reverse mapping methods."""
        assert not hasattr(EvaluationResultMapper, "to_domain")
        assert not hasattr(EvaluationResultMapper, "from_dto")

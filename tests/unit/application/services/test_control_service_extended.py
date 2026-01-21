"""Extended unit tests for ControlService to improve coverage.

This file contains additional tests for control_service.py to reach 85% coverage.
Tests focus on uncovered branches and error paths.
"""

from uuid import uuid4
from unittest.mock import Mock

import pytest

from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.control.control_rule import ControlRule, ControlRuleId
from doc_helper.domain.control.control_effect import ControlType, ControlEffect
from doc_helper.domain.control.effect_evaluator import EvaluationResult
from doc_helper.application.services.control_service import ControlService
from doc_helper.domain.common.i18n import TranslationKey


class TestControlServiceEvaluateByProjectId:
    """Tests for ControlService.evaluate_by_project_id method."""

    def test_missing_project_repository(self) -> None:
        """evaluate_by_project_id should fail when project_repository is None."""
        service = ControlService(project_repository=None, schema_repository=None)
        result = service.evaluate_by_project_id(ProjectId(uuid4()))

        assert isinstance(result, Failure)
        assert "requires project_repository" in result.error

    def test_missing_schema_repository(self) -> None:
        """evaluate_by_project_id should fail when schema_repository is None."""
        mock_repo = Mock()
        service = ControlService(project_repository=mock_repo, schema_repository=None)
        result = service.evaluate_by_project_id(ProjectId(uuid4()))

        assert isinstance(result, Failure)
        assert "requires schema_repository" in result.error

    def test_invalid_project_id_type(self) -> None:
        """evaluate_by_project_id should fail when project_id is not ProjectId."""
        mock_project_repo = Mock()
        mock_schema_repo = Mock()
        service = ControlService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )

        result = service.evaluate_by_project_id("not_a_project_id")  # type: ignore

        assert isinstance(result, Failure)
        assert "project_id must be a ProjectId" in result.error

    def test_project_load_failure(self) -> None:
        """evaluate_by_project_id should fail when project loading fails."""
        mock_project_repo = Mock()
        mock_project_repo.get_by_id.return_value = Failure("Database error")
        mock_schema_repo = Mock()

        service = ControlService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )
        result = service.evaluate_by_project_id(ProjectId(uuid4()))

        assert isinstance(result, Failure)
        assert "Failed to load project" in result.error

    def test_project_not_found(self) -> None:
        """evaluate_by_project_id should fail when project is not found."""
        mock_project_repo = Mock()
        mock_project_repo.get_by_id.return_value = Success(None)
        mock_schema_repo = Mock()

        service = ControlService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )
        project_id = ProjectId(uuid4())
        result = service.evaluate_by_project_id(project_id)

        assert isinstance(result, Failure)
        assert "Project not found" in result.error

    def test_entity_definition_load_failure(self) -> None:
        """evaluate_by_project_id should fail when entity definition loading fails."""
        entity_def_id = EntityDefinitionId("test_entity")
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def_id,
            field_values={},
        )

        mock_project_repo = Mock()
        mock_project_repo.get_by_id.return_value = Success(project)

        mock_schema_repo = Mock()
        mock_schema_repo.get_entity_definition.return_value = Failure("Schema error")

        service = ControlService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )
        result = service.evaluate_by_project_id(project.id)

        assert isinstance(result, Failure)
        assert "Failed to load entity definition" in result.error

    def test_entity_definition_not_found(self) -> None:
        """evaluate_by_project_id should fail when entity definition is not found."""
        entity_def_id = EntityDefinitionId("test_entity")
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def_id,
            field_values={},
        )

        mock_project_repo = Mock()
        mock_project_repo.get_by_id.return_value = Success(project)

        mock_schema_repo = Mock()
        mock_schema_repo.get_entity_definition.return_value = Success(None)

        service = ControlService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )
        result = service.evaluate_by_project_id(project.id)

        assert isinstance(result, Failure)
        assert "Entity definition not found" in result.error

    def test_success(self) -> None:
        """evaluate_by_project_id should succeed with valid repositories."""
        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={},
        )

        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def.id,
            field_values={},
        )

        mock_project_repo = Mock()
        mock_project_repo.get_by_id.return_value = Success(project)

        mock_schema_repo = Mock()
        mock_schema_repo.get_entity_definition.return_value = Success(entity_def)

        service = ControlService(
            project_repository=mock_project_repo, schema_repository=mock_schema_repo
        )
        result = service.evaluate_by_project_id(project.id)

        assert isinstance(result, Success)
        mock_project_repo.get_by_id.assert_called_once_with(project.id)
        mock_schema_repo.get_entity_definition.assert_called_once_with(entity_def.id)


class TestControlServiceEnableEffect:
    """Tests for ENABLE control effects."""

    def test_should_field_be_enabled_with_enable_effect_true(self) -> None:
        """should_field_be_enabled should return True when ENABLE control value is True."""
        enable_rule = ControlRule(
            id=ControlRuleId("enable_rule"),
            name_key=TranslationKey("rules.enable_control"),
            condition="trigger == True",
            effect=ControlEffect(
                control_type=ControlType.ENABLE,
                target_field_id=FieldDefinitionId("target_field"),
                value=True,
            ),
            enabled=True,
        )

        field_with_enable = FieldDefinition(
            id=FieldDefinitionId("target_field"),
            label_key=TranslationKey("fields.target"),
            field_type=FieldType.TEXT,
            constraints=(),
            control_rules=(enable_rule,),
        )

        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("trigger"): FieldDefinition(
                    id=FieldDefinitionId("trigger"),
                    label_key=TranslationKey("fields.trigger"),
                    field_type=FieldType.CHECKBOX,
                    constraints=(),
                ),
                FieldDefinitionId("target_field"): field_with_enable,
            },
        )

        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def.id,
            field_values={
                FieldDefinitionId("trigger"): FieldValue(
                    field_id=FieldDefinitionId("trigger"),
                    value=True,
                ),
            },
        )

        service = ControlService()
        eval_result = service.evaluate_controls(project, entity_def)
        assert isinstance(eval_result, Success)

        enabled = service.should_field_be_enabled(
            FieldDefinitionId("target_field"), eval_result.value
        )
        assert enabled is True

    def test_should_field_be_enabled_with_enable_effect_false(self) -> None:
        """should_field_be_enabled should return False when ENABLE control value is False."""
        disable_rule = ControlRule(
            id=ControlRuleId("disable_rule"),
            name_key=TranslationKey("rules.disable_control"),
            condition="trigger == True",
            effect=ControlEffect(
                control_type=ControlType.ENABLE,
                target_field_id=FieldDefinitionId("target_field"),
                value=False,
            ),
            enabled=True,
        )

        field_with_disable = FieldDefinition(
            id=FieldDefinitionId("target_field"),
            label_key=TranslationKey("fields.target"),
            field_type=FieldType.TEXT,
            constraints=(),
            control_rules=(disable_rule,),
        )

        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("trigger"): FieldDefinition(
                    id=FieldDefinitionId("trigger"),
                    label_key=TranslationKey("fields.trigger"),
                    field_type=FieldType.CHECKBOX,
                    constraints=(),
                ),
                FieldDefinitionId("target_field"): field_with_disable,
            },
        )

        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def.id,
            field_values={
                FieldDefinitionId("trigger"): FieldValue(
                    field_id=FieldDefinitionId("trigger"),
                    value=True,
                ),
            },
        )

        service = ControlService()
        eval_result = service.evaluate_controls(project, entity_def)
        assert isinstance(eval_result, Success)

        enabled = service.should_field_be_enabled(
            FieldDefinitionId("target_field"), eval_result.value
        )
        assert enabled is False


class TestControlServiceValueSetEffect:
    """Tests for VALUE_SET control effects."""

    def test_get_field_value_override_with_value_set_effect(self) -> None:
        """get_field_value_override should return value when VALUE_SET effect exists."""
        value_set_rule = ControlRule(
            id=ControlRuleId("value_set_rule"),
            name_key=TranslationKey("rules.value_set_control"),
            condition="trigger == True",
            effect=ControlEffect(
                control_type=ControlType.VALUE_SET,
                target_field_id=FieldDefinitionId("target_field"),
                value="auto_value",
            ),
            enabled=True,
        )

        field_with_value_set = FieldDefinition(
            id=FieldDefinitionId("target_field"),
            label_key=TranslationKey("fields.target"),
            field_type=FieldType.TEXT,
            constraints=(),
            control_rules=(value_set_rule,),
        )

        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("trigger"): FieldDefinition(
                    id=FieldDefinitionId("trigger"),
                    label_key=TranslationKey("fields.trigger"),
                    field_type=FieldType.CHECKBOX,
                    constraints=(),
                ),
                FieldDefinitionId("target_field"): field_with_value_set,
            },
        )

        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def.id,
            field_values={
                FieldDefinitionId("trigger"): FieldValue(
                    field_id=FieldDefinitionId("trigger"),
                    value=True,
                ),
            },
        )

        service = ControlService()
        eval_result = service.evaluate_controls(project, entity_def)
        assert isinstance(eval_result, Success)

        override_value = service.get_field_value_override(
            FieldDefinitionId("target_field"), eval_result.value
        )
        assert override_value == "auto_value"

    def test_get_field_value_override_without_effect(self) -> None:
        """get_field_value_override should return None when no VALUE_SET effect exists."""
        eval_result = EvaluationResult(effects=(), errors=())

        service = ControlService()
        override_value = service.get_field_value_override(
            FieldDefinitionId("some_field"), eval_result
        )
        assert override_value is None


class TestControlServiceGetEffectsForField:
    """Tests for get_effects_for_field validation."""

    def test_invalid_field_id_type(self) -> None:
        """get_effects_for_field should raise TypeError for invalid field_id."""
        eval_result = EvaluationResult(effects=(), errors=())

        service = ControlService()
        with pytest.raises(TypeError, match="field_id must be a FieldDefinitionId"):
            service.get_effects_for_field("not_a_field_id", eval_result)  # type: ignore

    def test_invalid_evaluation_result_type(self) -> None:
        """get_effects_for_field should raise TypeError for invalid evaluation_result."""
        service = ControlService()
        with pytest.raises(TypeError, match="evaluation_result must be an EvaluationResult"):
            service.get_effects_for_field(
                FieldDefinitionId("field"), "not_eval_result"  # type: ignore
            )

"""Unit tests for ControlService."""

from uuid import uuid4

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
from doc_helper.application.services.control_service import ControlService
from doc_helper.domain.common.i18n import TranslationKey


class TestControlService:
    """Tests for ControlService."""

    @pytest.fixture
    def service(self) -> ControlService:
        """Create control service instance."""
        return ControlService()

    @pytest.fixture
    def entity_definition(self) -> EntityDefinition:
        """Create sample entity definition with control rules."""
        # Control rule 1: details is visible when show_details is True
        control_rule_show = ControlRule(
            id=ControlRuleId("rule1"),
            name_key=TranslationKey("rules.show_details_control"),
            condition="show_details == True",
            effect=ControlEffect(
                control_type=ControlType.VISIBILITY,
                target_field_id=FieldDefinitionId("details"),
                value=True,
            ),
            enabled=True,
        )

        # Control rule 2: details is hidden when show_details is False
        control_rule_hide = ControlRule(
            id=ControlRuleId("rule2"),
            name_key=TranslationKey("rules.hide_details_control"),
            condition="show_details == False",
            effect=ControlEffect(
                control_type=ControlType.VISIBILITY,
                target_field_id=FieldDefinitionId("details"),
                value=False,
            ),
            enabled=True,
        )

        field1 = FieldDefinition(
            id=FieldDefinitionId("show_details"),
            label_key=TranslationKey("fields.show_details"),
            field_type=FieldType.CHECKBOX,
            constraints=(),
        )

        # Attach control rules to the field they target (details field)
        field2 = FieldDefinition(
            id=FieldDefinitionId("details"),
            label_key=TranslationKey("fields.details"),
            field_type=FieldType.TEXTAREA,
            constraints=(),
            control_rules=(control_rule_show, control_rule_hide),  # Both rules
        )

        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("show_details"): field1,
                FieldDefinitionId("details"): field2,
            },
        )

    @pytest.fixture
    def project_with_checkbox_on(
        self, entity_definition: EntityDefinition
    ) -> Project:
        """Create project with checkbox on."""
        return Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_definition.id,
            field_values={
                FieldDefinitionId("show_details"): FieldValue(
                    field_id=FieldDefinitionId("show_details"),
                    value=True,
                ),
            },
        )

    @pytest.fixture
    def project_with_checkbox_off(
        self, entity_definition: EntityDefinition
    ) -> Project:
        """Create project with checkbox off."""
        return Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_definition.id,
            field_values={
                FieldDefinitionId("show_details"): FieldValue(
                    field_id=FieldDefinitionId("show_details"),
                    value=False,
                ),
            },
        )

    def test_evaluate_controls_success(
        self,
        service: ControlService,
        project_with_checkbox_on: Project,
        entity_definition: EntityDefinition,
    ) -> None:
        """evaluate_controls should return evaluation result."""
        result = service.evaluate_controls(project_with_checkbox_on, entity_definition)

        assert isinstance(result, Success)
        # Result should contain evaluated control effects

    def test_evaluate_controls_requires_project(
        self, service: ControlService, entity_definition: EntityDefinition
    ) -> None:
        """evaluate_controls should require Project instance."""
        result = service.evaluate_controls("not a project", entity_definition)  # type: ignore

        assert isinstance(result, Failure)
        assert "project" in result.error.lower()

    def test_evaluate_controls_requires_entity_definition(
        self, service: ControlService, project_with_checkbox_on: Project
    ) -> None:
        """evaluate_controls should require EntityDefinition instance."""
        result = service.evaluate_controls(project_with_checkbox_on, "not an entity")  # type: ignore

        assert isinstance(result, Failure)
        assert "entity" in result.error.lower()

    def test_should_field_be_visible_when_control_makes_visible(
        self,
        service: ControlService,
        project_with_checkbox_on: Project,
        entity_definition: EntityDefinition,
    ) -> None:
        """should_field_be_visible should return True when control makes field visible."""
        eval_result = service.evaluate_controls(
            project_with_checkbox_on, entity_definition
        )
        assert isinstance(eval_result, Success)

        visible = service.should_field_be_visible(
            FieldDefinitionId("details"), eval_result.value, default_visible=False
        )

        assert visible is True

    def test_should_field_be_visible_when_control_makes_hidden(
        self,
        service: ControlService,
        project_with_checkbox_off: Project,
        entity_definition: EntityDefinition,
    ) -> None:
        """should_field_be_visible should return False when control makes field hidden."""
        eval_result = service.evaluate_controls(
            project_with_checkbox_off, entity_definition
        )
        assert isinstance(eval_result, Success)

        visible = service.should_field_be_visible(
            FieldDefinitionId("details"), eval_result.value, default_visible=True
        )

        assert visible is False

    def test_should_field_be_visible_uses_default_when_no_control(
        self, service: ControlService
    ) -> None:
        """should_field_be_visible should use default when no control affects field."""
        # Create empty evaluation result
        from doc_helper.domain.control.effect_evaluator import EvaluationResult

        eval_result = EvaluationResult(effects=(), errors=())

        # Check with default True
        visible = service.should_field_be_visible(
            FieldDefinitionId("some_field"), eval_result, default_visible=True
        )
        assert visible is True

        # Check with default False
        visible = service.should_field_be_visible(
            FieldDefinitionId("some_field"), eval_result, default_visible=False
        )
        assert visible is False

    def test_should_field_be_enabled_uses_default(
        self, service: ControlService
    ) -> None:
        """should_field_be_enabled should use default when no control affects field."""
        from doc_helper.domain.control.effect_evaluator import EvaluationResult

        eval_result = EvaluationResult(effects=(), errors=())

        # Check with default True
        enabled = service.should_field_be_enabled(
            FieldDefinitionId("some_field"), eval_result, default_enabled=True
        )
        assert enabled is True

        # Check with default False
        enabled = service.should_field_be_enabled(
            FieldDefinitionId("some_field"), eval_result, default_enabled=False
        )
        assert enabled is False

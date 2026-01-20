"""Unit tests for FormulaService."""

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
from doc_helper.application.services.formula_service import FormulaService
from doc_helper.domain.common.i18n import TranslationKey


class TestFormulaService:
    """Tests for FormulaService."""

    @pytest.fixture
    def service(self) -> FormulaService:
        """Create formula service instance."""
        return FormulaService()

    @pytest.fixture
    def entity_definition(self) -> EntityDefinition:
        """Create sample entity definition with formulas."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("base_value"): FieldDefinition(
                    id=FieldDefinitionId("base_value"),
                    label_key=TranslationKey("fields.base_value"),
                    field_type=FieldType.NUMBER,
                    constraints=(),
                ),
                FieldDefinitionId("multiplier"): FieldDefinition(
                    id=FieldDefinitionId("multiplier"),
                    label_key=TranslationKey("fields.multiplier"),
                    field_type=FieldType.NUMBER,
                    constraints=(),
                ),
                FieldDefinitionId("calculated"): FieldDefinition(
                    id=FieldDefinitionId("calculated"),
                    label_key=TranslationKey("fields.calculated"),
                    field_type=FieldType.CALCULATED,
                    constraints=(),
                    formula="base_value * multiplier",
                ),
            },
        )

    @pytest.fixture
    def project(self, entity_definition: EntityDefinition) -> Project:
        """Create project with field values."""
        return Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_definition.id,
            field_values={
                FieldDefinitionId("base_value"): FieldValue(
                    field_id=FieldDefinitionId("base_value"),
                    value=10,
                ),
                FieldDefinitionId("multiplier"): FieldValue(
                    field_id=FieldDefinitionId("multiplier"),
                    value=5,
                ),
            },
        )

    def test_evaluate_formula_success(self, service: FormulaService) -> None:
        """evaluate_formula should return result for valid formula."""
        result = service.evaluate_formula(
            formula="a + b * 2",
            field_values={"a": 10, "b": 5},
        )

        assert isinstance(result, Success)
        assert result.value == 20  # 10 + 5 * 2

    def test_evaluate_formula_with_error(self, service: FormulaService) -> None:
        """evaluate_formula should return error for invalid formula."""
        result = service.evaluate_formula(
            formula="a / 0",
            field_values={"a": 10},
        )

        assert isinstance(result, Failure)
        assert "division by zero" in result.error.lower()

    def test_evaluate_formula_with_missing_field(
        self, service: FormulaService
    ) -> None:
        """evaluate_formula should return error for missing field."""
        result = service.evaluate_formula(
            formula="a + b",
            field_values={"a": 10},  # Missing 'b'
        )

        assert isinstance(result, Failure)
        assert "b" in result.error.lower()

    def test_evaluate_project_formulas_success(
        self,
        service: FormulaService,
        project: Project,
        entity_definition: EntityDefinition,
    ) -> None:
        """evaluate_project_formulas should return results for all formulas."""
        result = service.evaluate_project_formulas(project, entity_definition)

        assert isinstance(result, Success)
        assert FieldDefinitionId("calculated") in result.value
        assert result.value[FieldDefinitionId("calculated")] == 50  # 10 * 5

    def test_evaluate_project_formulas_requires_project(
        self, service: FormulaService, entity_definition: EntityDefinition
    ) -> None:
        """evaluate_project_formulas should require Project instance."""
        result = service.evaluate_project_formulas("not a project", entity_definition)  # type: ignore

        assert isinstance(result, Failure)
        assert "project" in result.error.lower()

    def test_evaluate_project_formulas_requires_entity_definition(
        self, service: FormulaService, project: Project
    ) -> None:
        """evaluate_project_formulas should require EntityDefinition instance."""
        result = service.evaluate_project_formulas(project, "not an entity")  # type: ignore

        assert isinstance(result, Failure)
        assert "entity" in result.error.lower()

    def test_get_field_dependencies_success(self, service: FormulaService) -> None:
        """get_field_dependencies should return field references."""
        result = service.get_field_dependencies("a + b * c")

        assert isinstance(result, Success)
        assert result.value == {"a", "b", "c"}

    def test_get_field_dependencies_with_error(self, service: FormulaService) -> None:
        """get_field_dependencies should return error for invalid formula."""
        result = service.get_field_dependencies("a +")  # Incomplete formula

        assert isinstance(result, Failure)

    def test_get_field_dependencies_with_empty_formula(
        self, service: FormulaService
    ) -> None:
        """get_field_dependencies should return empty set for empty formula."""
        result = service.get_field_dependencies("")

        assert isinstance(result, Success)
        assert result.value == set()

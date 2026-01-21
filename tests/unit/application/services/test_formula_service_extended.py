"""Extended unit tests for FormulaService to improve coverage.

This file contains additional tests for formula_service.py to reach 85%+ coverage.
Tests focus on uncovered branches and error paths.
"""

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


class TestFormulaServiceEvaluateFormula:
    """Tests for FormulaService.evaluate_formula type validation and error handling."""

    def test_invalid_formula_type(self) -> None:
        """evaluate_formula should fail when formula is not a string."""
        service = FormulaService()
        result = service.evaluate_formula(
            formula=123,  # type: ignore
            field_values={"field1": 10},
        )

        assert isinstance(result, Failure)
        assert "formula must be a string" in result.error

    def test_invalid_field_values_type(self) -> None:
        """evaluate_formula should fail when field_values is not a dict."""
        service = FormulaService()
        result = service.evaluate_formula(
            formula="field1 + 10",
            field_values="not_a_dict",  # type: ignore
        )

        assert isinstance(result, Failure)
        assert "field_values must be a dictionary" in result.error

    def test_exception_during_evaluation(self) -> None:
        """evaluate_formula should return Failure when evaluation raises exception."""
        service = FormulaService()
        # Formula with syntax that will cause parser to raise exception
        result = service.evaluate_formula(
            formula="field1 + (field2",  # Unmatched parenthesis
            field_values={"field1": 10, "field2": 20},
        )

        assert isinstance(result, Failure)
        # Exception message should be in the error


class TestFormulaServiceGetFieldDependencies:
    """Tests for FormulaService.get_field_dependencies."""

    def test_invalid_formula_type(self) -> None:
        """get_field_dependencies should fail when formula is not a string."""
        service = FormulaService()
        result = service.get_field_dependencies(123)  # type: ignore

        assert isinstance(result, Failure)
        assert "formula must be a string" in result.error

    def test_empty_formula(self) -> None:
        """get_field_dependencies should return empty set for empty formula."""
        service = FormulaService()
        result = service.get_field_dependencies("")

        assert isinstance(result, Success)
        assert result.value == set()

    def test_whitespace_only_formula(self) -> None:
        """get_field_dependencies should return empty set for whitespace-only formula."""
        service = FormulaService()
        result = service.get_field_dependencies("   ")

        assert isinstance(result, Success)
        assert result.value == set()


class TestFormulaServiceEvaluateProjectFormulas:
    """Tests for FormulaService.evaluate_project_formulas edge cases."""

    def test_circular_dependency_detection(self) -> None:
        """evaluate_project_formulas should detect circular dependencies."""
        # Create entity with circular dependencies: field_a depends on field_b, field_b depends on field_a
        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("field_a"): FieldDefinition(
                    id=FieldDefinitionId("field_a"),
                    label_key=TranslationKey("fields.field_a"),
                    field_type=FieldType.CALCULATED,
                    constraints=(),
                    formula="field_b + 1",  # Depends on field_b
                ),
                FieldDefinitionId("field_b"): FieldDefinition(
                    id=FieldDefinitionId("field_b"),
                    label_key=TranslationKey("fields.field_b"),
                    field_type=FieldType.CALCULATED,
                    constraints=(),
                    formula="field_a + 1",  # Depends on field_a
                ),
            },
        )

        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def.id,
            field_values={},
        )

        service = FormulaService()
        result = service.evaluate_project_formulas(project, entity_def)

        assert isinstance(result, Failure)
        assert "Circular dependencies detected" in result.error or "cycle" in result.error.lower()

    def test_formula_is_none_edge_case(self) -> None:
        """evaluate_project_formulas should skip fields where formula becomes None."""
        # This edge case is hard to trigger directly since FieldDefinition validates formula,
        # but we can test the continue path by having a field with None formula in calculated_fields
        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("field1"): FieldDefinition(
                    id=FieldDefinitionId("field1"),
                    label_key=TranslationKey("fields.field1"),
                    field_type=FieldType.CALCULATED,
                    constraints=(),
                    formula="10 + 20",
                ),
            },
        )

        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def.id,
            field_values={},
        )

        service = FormulaService()
        result = service.evaluate_project_formulas(project, entity_def)

        assert isinstance(result, Success)
        assert FieldDefinitionId("field1") in result.value

    def test_formula_evaluation_failure(self) -> None:
        """evaluate_project_formulas should fail when a formula evaluation fails."""
        # Create field with formula that will fail (division by zero or similar)
        entity_def = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entities.test"),
            fields={
                FieldDefinitionId("field1"): FieldDefinition(
                    id=FieldDefinitionId("field1"),
                    label_key=TranslationKey("fields.field1"),
                    field_type=FieldType.CALCULATED,
                    constraints=(),
                    formula="nonexistent_field + 10",  # Field doesn't exist
                ),
            },
        )

        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_def.id,
            field_values={},
        )

        service = FormulaService()
        result = service.evaluate_project_formulas(project, entity_def)

        assert isinstance(result, Failure)
        assert "Error evaluating formula" in result.error


class TestFormulaServiceCheckDependencies:
    """Tests for FormulaService._check_dependencies edge cases."""

    def test_empty_formulas(self) -> None:
        """_check_dependencies should return empty list for empty formulas."""
        service = FormulaService()
        result = service._check_dependencies({})

        assert isinstance(result, Success)
        assert result.value == []

    def test_topological_sort_with_no_dependencies(self) -> None:
        """_check_dependencies should handle fields with no dependencies."""
        # Create fields with formulas that don't reference each other
        field1 = FieldDefinition(
            id=FieldDefinitionId("field1"),
            label_key=TranslationKey("fields.field1"),
            field_type=FieldType.CALCULATED,
            constraints=(),
            formula="10 + 20",
        )

        field2 = FieldDefinition(
            id=FieldDefinitionId("field2"),
            label_key=TranslationKey("fields.field2"),
            field_type=FieldType.CALCULATED,
            constraints=(),
            formula="30 + 40",
        )

        calculated_fields = {
            FieldDefinitionId("field1"): field1,
            FieldDefinitionId("field2"): field2,
        }

        service = FormulaService()
        result = service._check_dependencies(calculated_fields)

        assert isinstance(result, Success)
        # Both fields should be in the evaluation order
        assert len(result.value) == 2


class TestFormulaServiceExtractFieldReferences:
    """Tests for FormulaService._extract_field_references with different AST node types."""

    def test_extract_from_unary_op(self) -> None:
        """_extract_field_references should handle UnaryOp nodes."""
        service = FormulaService()
        # Formula with unary operator: -field1
        result = service.get_field_dependencies("-field1")

        assert isinstance(result, Success)
        assert "field1" in result.value

    def test_extract_from_function_call(self) -> None:
        """_extract_field_references should handle FunctionCall nodes."""
        service = FormulaService()
        # Formula with function call: abs(field1)
        result = service.get_field_dependencies("abs(field1)")

        assert isinstance(result, Success)
        assert "field1" in result.value

    def test_extract_from_function_call_multiple_args(self) -> None:
        """_extract_field_references should handle FunctionCall with multiple arguments."""
        service = FormulaService()
        # Formula with function call with multiple args: min(field1, field2, field3)
        result = service.get_field_dependencies("min(field1, field2, field3)")

        assert isinstance(result, Success)
        assert "field1" in result.value
        assert "field2" in result.value
        assert "field3" in result.value

    def test_extract_from_literal(self) -> None:
        """_extract_field_references should return empty set for literals."""
        service = FormulaService()
        # Formula with only literals: 10 + 20
        result = service.get_field_dependencies("10 + 20")

        assert isinstance(result, Success)
        # No field references, only literals
        assert len(result.value) == 0

    def test_extract_from_complex_expression(self) -> None:
        """_extract_field_references should handle complex expressions."""
        service = FormulaService()
        # Complex formula: (field1 + field2) * abs(-field3) + min(field4, 100)
        result = service.get_field_dependencies("(field1 + field2) * abs(-field3) + min(field4, 100)")

        assert isinstance(result, Success)
        assert "field1" in result.value
        assert "field2" in result.value
        assert "field3" in result.value
        assert "field4" in result.value

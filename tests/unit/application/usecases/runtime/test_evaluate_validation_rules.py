"""Unit tests for EvaluateValidationRulesUseCase (Phase R-2).

Tests runtime validation constraint evaluation with ADR-050 compliance.
"""

import pytest

from doc_helper.application.dto.export_dto import ConstraintExportDTO
from doc_helper.application.dto.runtime_dto import (
    ValidationEvaluationRequestDTO,
    ValidationEvaluationResultDTO,
    ValidationIssueDTO,
)
from doc_helper.application.dto.schema_dto import EntityDefinitionDTO, FieldDefinitionDTO
from doc_helper.application.usecases.runtime.evaluate_validation_rules import (
    EvaluateValidationRulesUseCase,
)


# ============================================================================
# Mock SchemaUseCases
# ============================================================================


class MockSchemaUseCases:
    """Mock SchemaUseCases for testing."""

    def __init__(
        self,
        entities: tuple[EntityDefinitionDTO, ...] = (),
        constraints_map: dict[str, tuple[ConstraintExportDTO, ...]] | None = None,
    ):
        """Initialize mock.

        Args:
            entities: Tuple of EntityDefinitionDTO
            constraints_map: Dict mapping field_id to tuple of ConstraintExportDTO
        """
        self.entities = entities
        self.constraints_map = constraints_map or {}
        self.should_fail = False

    def get_all_entities(self):
        """Return entities tuple directly. Raises exception on failure."""
        if self.should_fail:
            raise RuntimeError("Failed to fetch entities")
        return self.entities

    def list_constraints_for_field(self, entity_id: str, field_id: str):
        """Return constraints tuple directly. Raises exception on failure."""
        if self.should_fail:
            raise RuntimeError("Failed to fetch constraints")
        return self.constraints_map.get(field_id, ())


# ============================================================================
# Test RequiredConstraint
# ============================================================================


def test_required_constraint_with_none_value_fails():
    """RequiredConstraint should fail when value is None."""
    field = FieldDefinitionDTO(
        id="project_name",
        field_type="TEXT",
        label="Project Name",
        help_text=None,
        required=True,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "project_name": (
            ConstraintExportDTO(
                constraint_type="RequiredConstraint",
                parameters={"severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"project_name": None},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1
    assert result.errors[0].field_id == "project_name"
    assert result.errors[0].constraint_type == "RequiredConstraint"
    assert result.errors[0].severity == "ERROR"
    assert result.errors[0].code == "REQUIRED_FIELD_EMPTY"
    assert len(result.warnings) == 0
    assert len(result.info) == 0
    assert "project_name" in result.evaluated_fields
    assert "project_name" in result.failed_fields


def test_required_constraint_with_empty_string_fails():
    """RequiredConstraint should fail when value is empty string."""
    field = FieldDefinitionDTO(
        id="project_name",
        field_type="TEXT",
        label="Project Name",
        help_text=None,
        required=True,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "project_name": (
            ConstraintExportDTO(
                constraint_type="RequiredConstraint",
                parameters={"severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"project_name": ""},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1


def test_required_constraint_with_whitespace_only_fails():
    """RequiredConstraint should fail when value is whitespace only."""
    field = FieldDefinitionDTO(
        id="project_name",
        field_type="TEXT",
        label="Project Name",
        help_text=None,
        required=True,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "project_name": (
            ConstraintExportDTO(
                constraint_type="RequiredConstraint",
                parameters={"severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"project_name": "   "},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1


def test_required_constraint_with_valid_value_passes():
    """RequiredConstraint should pass when value is non-empty."""
    field = FieldDefinitionDTO(
        id="project_name",
        field_type="TEXT",
        label="Project Name",
        help_text=None,
        required=True,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "project_name": (
            ConstraintExportDTO(
                constraint_type="RequiredConstraint",
                parameters={"severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"project_name": "Test Project"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False
    assert len(result.errors) == 0
    assert len(result.warnings) == 0
    assert len(result.info) == 0


# ============================================================================
# Test MinLengthConstraint
# ============================================================================


def test_min_length_constraint_with_too_short_value_fails():
    """MinLengthConstraint should fail when value is too short."""
    field = FieldDefinitionDTO(
        id="description",
        field_type="TEXT",
        label="Description",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "description": (
            ConstraintExportDTO(
                constraint_type="MinLengthConstraint",
                parameters={"min_length": 10, "severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"description": "Short"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1
    assert result.errors[0].code == "VALUE_TOO_SHORT"
    assert result.errors[0].details["min_length"] == 10
    assert result.errors[0].details["actual_length"] == 5


def test_min_length_constraint_with_valid_value_passes():
    """MinLengthConstraint should pass when value is long enough."""
    field = FieldDefinitionDTO(
        id="description",
        field_type="TEXT",
        label="Description",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "description": (
            ConstraintExportDTO(
                constraint_type="MinLengthConstraint",
                parameters={"min_length": 10, "severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"description": "This is long enough"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False
    assert len(result.errors) == 0


def test_min_length_constraint_skips_none_value():
    """MinLengthConstraint should skip None values."""
    field = FieldDefinitionDTO(
        id="description",
        field_type="TEXT",
        label="Description",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "description": (
            ConstraintExportDTO(
                constraint_type="MinLengthConstraint",
                parameters={"min_length": 10, "severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"description": None},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False
    assert len(result.errors) == 0


# ============================================================================
# Test MaxLengthConstraint
# ============================================================================


def test_max_length_constraint_with_too_long_value_fails():
    """MaxLengthConstraint should fail when value is too long."""
    field = FieldDefinitionDTO(
        id="code",
        field_type="TEXT",
        label="Code",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "code": (
            ConstraintExportDTO(
                constraint_type="MaxLengthConstraint",
                parameters={"max_length": 5, "severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"code": "TOOLONG"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1
    assert result.errors[0].code == "VALUE_TOO_LONG"
    assert result.errors[0].details["max_length"] == 5
    assert result.errors[0].details["actual_length"] == 7


def test_max_length_constraint_with_valid_value_passes():
    """MaxLengthConstraint should pass when value is short enough."""
    field = FieldDefinitionDTO(
        id="code",
        field_type="TEXT",
        label="Code",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "code": (
            ConstraintExportDTO(
                constraint_type="MaxLengthConstraint",
                parameters={"max_length": 5, "severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"code": "OK"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False
    assert len(result.errors) == 0


# ============================================================================
# Test MinValueConstraint
# ============================================================================


def test_min_value_constraint_with_too_small_value_fails():
    """MinValueConstraint should fail when value is too small."""
    field = FieldDefinitionDTO(
        id="depth",
        field_type="NUMBER",
        label="Depth",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "depth": (
            ConstraintExportDTO(
                constraint_type="MinValueConstraint",
                parameters={"min_value": 0.0, "severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"depth": -5.0},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1
    assert result.errors[0].code == "VALUE_TOO_SMALL"
    assert result.errors[0].details["min_value"] == 0.0
    assert result.errors[0].details["actual_value"] == -5.0


def test_min_value_constraint_with_valid_value_passes():
    """MinValueConstraint should pass when value is large enough."""
    field = FieldDefinitionDTO(
        id="depth",
        field_type="NUMBER",
        label="Depth",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "depth": (
            ConstraintExportDTO(
                constraint_type="MinValueConstraint",
                parameters={"min_value": 0.0, "severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"depth": 10.0},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False
    assert len(result.errors) == 0


# ============================================================================
# Test MaxValueConstraint
# ============================================================================


def test_max_value_constraint_with_too_large_value_fails():
    """MaxValueConstraint should fail when value is too large."""
    field = FieldDefinitionDTO(
        id="depth",
        field_type="NUMBER",
        label="Depth",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "depth": (
            ConstraintExportDTO(
                constraint_type="MaxValueConstraint",
                parameters={"max_value": 100.0, "severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"depth": 150.0},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1
    assert result.errors[0].code == "VALUE_TOO_LARGE"
    assert result.errors[0].details["max_value"] == 100.0
    assert result.errors[0].details["actual_value"] == 150.0


def test_max_value_constraint_with_valid_value_passes():
    """MaxValueConstraint should pass when value is small enough."""
    field = FieldDefinitionDTO(
        id="depth",
        field_type="NUMBER",
        label="Depth",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "depth": (
            ConstraintExportDTO(
                constraint_type="MaxValueConstraint",
                parameters={"max_value": 100.0, "severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"depth": 50.0},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False
    assert len(result.errors) == 0


# ============================================================================
# Test PatternConstraint
# ============================================================================


def test_pattern_constraint_with_mismatch_fails():
    """PatternConstraint should fail when value doesn't match pattern."""
    field = FieldDefinitionDTO(
        id="email",
        field_type="TEXT",
        label="Email",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "email": (
            ConstraintExportDTO(
                constraint_type="PatternConstraint",
                parameters={
                    "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    "description": "valid email format",
                    "severity": "ERROR",
                },
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"email": "invalid-email"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1
    assert result.errors[0].code == "PATTERN_MISMATCH"


def test_pattern_constraint_with_match_passes():
    """PatternConstraint should pass when value matches pattern."""
    field = FieldDefinitionDTO(
        id="email",
        field_type="TEXT",
        label="Email",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "email": (
            ConstraintExportDTO(
                constraint_type="PatternConstraint",
                parameters={
                    "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    "description": "valid email format",
                    "severity": "ERROR",
                },
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"email": "test@example.com"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False
    assert len(result.errors) == 0


# ============================================================================
# Test AllowedValuesConstraint
# ============================================================================


def test_allowed_values_constraint_with_invalid_value_fails():
    """AllowedValuesConstraint should fail when value not in allowed list."""
    field = FieldDefinitionDTO(
        id="status",
        field_type="TEXT",
        label="Status",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "status": (
            ConstraintExportDTO(
                constraint_type="AllowedValuesConstraint",
                parameters={
                    "allowed_values": ["draft", "active", "archived"],
                    "severity": "ERROR",
                },
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"status": "invalid"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1
    assert result.errors[0].code == "VALUE_NOT_ALLOWED"


def test_allowed_values_constraint_with_valid_value_passes():
    """AllowedValuesConstraint should pass when value in allowed list."""
    field = FieldDefinitionDTO(
        id="status",
        field_type="TEXT",
        label="Status",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "status": (
            ConstraintExportDTO(
                constraint_type="AllowedValuesConstraint",
                parameters={
                    "allowed_values": ["draft", "active", "archived"],
                    "severity": "ERROR",
                },
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"status": "active"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False
    assert len(result.errors) == 0


# ============================================================================
# Test FileExtensionConstraint
# ============================================================================


def test_file_extension_constraint_with_invalid_extension_fails():
    """FileExtensionConstraint should fail when file has wrong extension."""
    field = FieldDefinitionDTO(
        id="document",
        field_type="FILE",
        label="Document",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "document": (
            ConstraintExportDTO(
                constraint_type="FileExtensionConstraint",
                parameters={
                    "allowed_extensions": ["pdf", "docx"],
                    "severity": "ERROR",
                },
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"document": {"name": "file.txt", "size_bytes": 1024}},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1
    assert result.errors[0].code == "FILE_EXTENSION_NOT_ALLOWED"


def test_file_extension_constraint_with_valid_extension_passes():
    """FileExtensionConstraint should pass when file has allowed extension."""
    field = FieldDefinitionDTO(
        id="document",
        field_type="FILE",
        label="Document",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "document": (
            ConstraintExportDTO(
                constraint_type="FileExtensionConstraint",
                parameters={
                    "allowed_extensions": ["pdf", "docx"],
                    "severity": "ERROR",
                },
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"document": {"name": "file.pdf", "size_bytes": 1024}},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False
    assert len(result.errors) == 0


# ============================================================================
# Test MaxFileSizeConstraint
# ============================================================================


def test_max_file_size_constraint_with_too_large_file_fails():
    """MaxFileSizeConstraint should fail when file is too large."""
    field = FieldDefinitionDTO(
        id="document",
        field_type="FILE",
        label="Document",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "document": (
            ConstraintExportDTO(
                constraint_type="MaxFileSizeConstraint",
                parameters={
                    "max_size_bytes": 1048576,  # 1 MB
                    "severity": "ERROR",
                },
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"document": {"name": "large.pdf", "size_bytes": 2097152}},  # 2 MB
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 1
    assert result.errors[0].code == "FILE_TOO_LARGE"


def test_max_file_size_constraint_with_valid_size_passes():
    """MaxFileSizeConstraint should pass when file size is acceptable."""
    field = FieldDefinitionDTO(
        id="document",
        field_type="FILE",
        label="Document",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "document": (
            ConstraintExportDTO(
                constraint_type="MaxFileSizeConstraint",
                parameters={
                    "max_size_bytes": 1048576,  # 1 MB
                    "severity": "ERROR",
                },
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"document": {"name": "small.pdf", "size_bytes": 524288}},  # 512 KB
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False
    assert len(result.errors) == 0


# ============================================================================
# Test Severity Handling
# ============================================================================


def test_warning_severity_does_not_block():
    """WARNING severity issues should not set blocking flag."""
    field = FieldDefinitionDTO(
        id="notes",
        field_type="TEXT",
        label="Notes",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "notes": (
            ConstraintExportDTO(
                constraint_type="MinLengthConstraint",
                parameters={"min_length": 10, "severity": "WARNING"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"notes": "Short"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False  # Warning does not block
    assert len(result.errors) == 0
    assert len(result.warnings) == 1
    assert result.warnings[0].severity == "WARNING"


def test_info_severity_does_not_block():
    """INFO severity issues should not set blocking flag."""
    field = FieldDefinitionDTO(
        id="notes",
        field_type="TEXT",
        label="Notes",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "notes": (
            ConstraintExportDTO(
                constraint_type="MinLengthConstraint",
                parameters={"min_length": 10, "severity": "INFO"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"notes": "Short"},
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is False  # Info does not block
    assert len(result.errors) == 0
    assert len(result.warnings) == 0
    assert len(result.info) == 1
    assert result.info[0].severity == "INFO"


# ============================================================================
# Test Multiple Fields
# ============================================================================


def test_multiple_fields_with_mixed_results():
    """Multiple fields with mixed validation results."""
    field1 = FieldDefinitionDTO(
        id="name",
        field_type="TEXT",
        label="Name",
        help_text=None,
        required=True,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    field2 = FieldDefinitionDTO(
        id="age",
        field_type="NUMBER",
        label="Age",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="person",
        name="Person",
        description=None,
        field_count=2,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field1, field2),
    )
    constraints_map = {
        "name": (
            ConstraintExportDTO(
                constraint_type="RequiredConstraint",
                parameters={"severity": "ERROR"},
            ),
        ),
        "age": (
            ConstraintExportDTO(
                constraint_type="MinValueConstraint",
                parameters={"min_value": 0.0, "severity": "ERROR"},
            ),
        ),
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="person",
        field_values={"name": "", "age": -5.0},  # Both fail
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.blocking is True
    assert len(result.errors) == 2
    assert len(result.evaluated_fields) == 2
    assert len(result.failed_fields) == 2


# ============================================================================
# Test Error Scenarios
# ============================================================================


def test_entity_not_found_returns_failure():
    """Evaluation should return failure when entity not found."""
    mock_schema = MockSchemaUseCases(entities=())
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="nonexistent",
        field_values={"field1": "value"},
    )

    result = use_case.execute(request)

    assert result.success is False
    assert "not found" in result.error_message.lower()


def test_schema_fetch_failure_returns_failure():
    """Evaluation should return failure when schema fetch fails."""
    mock_schema = MockSchemaUseCases()
    mock_schema.should_fail = True
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"field1": "value"},
    )

    result = use_case.execute(request)

    assert result.success is False
    assert "Failed to fetch" in result.error_message


# ============================================================================
# Test Determinism
# ============================================================================


def test_deterministic_evaluation():
    """Same inputs should produce same outputs (determinism)."""
    field = FieldDefinitionDTO(
        id="name",
        field_type="TEXT",
        label="Name",
        help_text=None,
        required=True,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    constraints_map = {
        "name": (
            ConstraintExportDTO(
                constraint_type="RequiredConstraint",
                parameters={"severity": "ERROR"},
            ),
        )
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateValidationRulesUseCase(schema_usecases=mock_schema)

    request = ValidationEvaluationRequestDTO(
        entity_id="project",
        field_values={"name": ""},
    )

    result1 = use_case.execute(request)
    result2 = use_case.execute(request)

    assert result1.success == result2.success
    assert result1.blocking == result2.blocking
    assert len(result1.errors) == len(result2.errors)
    assert result1.errors[0].field_id == result2.errors[0].field_id
    assert result1.errors[0].code == result2.errors[0].code

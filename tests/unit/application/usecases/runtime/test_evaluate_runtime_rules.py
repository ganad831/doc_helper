"""Unit tests for EvaluateRuntimeRulesUseCase (Phase R-3).

Tests orchestrated runtime evaluation with ADR-050 compliance.
"""

import pytest

from doc_helper.application.dto.export_dto import ConstraintExportDTO
from doc_helper.application.dto.runtime_dto import (
    RuntimeEvaluationRequestDTO,
    RuntimeEvaluationResultDTO,
)
from doc_helper.application.dto.schema_dto import EntityDefinitionDTO, FieldDefinitionDTO
from doc_helper.application.usecases.runtime.evaluate_runtime_rules import (
    EvaluateRuntimeRulesUseCase,
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

    def list_control_rules_for_field(self, entity_id: str, field_id: str):
        """Return empty tuple (control rules not used in R-3 orchestrator yet)."""
        return ()

    def list_output_mappings_for_field(self, entity_id: str, field_id: str):
        """Return empty tuple (output mappings not used in R-3 orchestrator yet)."""
        return ()


# ============================================================================
# Test Happy Path
# ============================================================================


def test_happy_path_all_rules_pass():
    """Happy path: All validation rules pass, not blocked."""
    # Arrange
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
        lookup_display_field=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        name_key="entity.test",
        description_key=None,
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
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    request = RuntimeEvaluationRequestDTO(
        entity_id="project",
        field_values={"name": "Test Project"},  # Valid value
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert isinstance(result, RuntimeEvaluationResultDTO)
    assert result.is_blocked is False
    assert result.blocking_reason is None
    assert result.control_rules_result is not None
    assert result.validation_result is not None
    assert result.validation_result.blocking is False
    assert len(result.validation_result.errors) == 0


# ============================================================================
# Test Validation Blocking
# ============================================================================


def test_validation_blocks_with_error_severity():
    """Validation with ERROR severity blocks runtime evaluation."""
    # Arrange
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
        lookup_display_field=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        name_key="entity.test",
        description_key=None,
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
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    request = RuntimeEvaluationRequestDTO(
        entity_id="project",
        field_values={"name": ""},  # Empty value → validation fails
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.is_blocked is True
    assert result.blocking_reason is not None
    assert "Validation failed" in result.blocking_reason
    assert "ERROR severity" in result.blocking_reason
    assert result.validation_result.blocking is True
    assert len(result.validation_result.errors) == 1
    assert result.output_mappings_result is None  # Not evaluated


def test_validation_warning_does_not_block():
    """Validation with WARNING severity does not block runtime evaluation."""
    # Arrange
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
        lookup_display_field=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        name_key="entity.test",
        description_key=None,
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
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    request = RuntimeEvaluationRequestDTO(
        entity_id="project",
        field_values={"notes": "Short"},  # Too short, but WARNING severity
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.is_blocked is False  # WARNING does not block
    assert result.blocking_reason is None
    assert result.validation_result.blocking is False
    assert len(result.validation_result.warnings) == 1
    assert len(result.validation_result.errors) == 0


# ============================================================================
# Test Multiple Fields
# ============================================================================


def test_multiple_fields_one_error_blocks():
    """Multiple fields with one ERROR blocks runtime evaluation."""
    # Arrange
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
        lookup_display_field=None,
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
        lookup_display_field=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="person",
        name="Person",
        description=None,
        name_key="entity.test",
        description_key=None,
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
                parameters={"min_value": 0.0, "severity": "WARNING"},
            ),
        ),
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    request = RuntimeEvaluationRequestDTO(
        entity_id="person",
        field_values={
            "name": "",  # ERROR: required field empty
            "age": -5.0,  # WARNING: negative age
        },
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.is_blocked is True  # ERROR blocks
    assert result.validation_result.blocking is True
    assert len(result.validation_result.errors) == 1  # name ERROR
    assert len(result.validation_result.warnings) == 1  # age WARNING


# ============================================================================
# Test Determinism
# ============================================================================


def test_deterministic_evaluation():
    """Same inputs produce identical outputs (determinism)."""
    # Arrange
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
        lookup_display_field=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        name_key="entity.test",
        description_key=None,
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
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    request = RuntimeEvaluationRequestDTO(
        entity_id="project",
        field_values={"name": ""},
    )

    # Act
    result1 = use_case.execute(request)
    result2 = use_case.execute(request)

    # Assert
    assert result1.is_blocked == result2.is_blocked
    assert result1.blocking_reason == result2.blocking_reason
    assert result1.validation_result.blocking == result2.validation_result.blocking
    assert len(result1.validation_result.errors) == len(result2.validation_result.errors)


# ============================================================================
# Test Purity (Input Unchanged)
# ============================================================================


def test_input_unchanged_after_evaluation():
    """Input field_values dict is not modified (purity)."""
    # Arrange
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
        lookup_display_field=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        name_key="entity.test",
        description_key=None,
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
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    # Create mutable input dict
    input_field_values = {"name": "Test"}
    original_values = input_field_values.copy()

    request = RuntimeEvaluationRequestDTO(
        entity_id="project",
        field_values=input_field_values,
    )

    # Act
    result = use_case.execute(request)

    # Assert - input dict unchanged
    assert input_field_values == original_values


# ============================================================================
# Test Execution Order
# ============================================================================


def test_validation_blocks_output_mapping_evaluation():
    """When validation blocks, output mappings are NOT evaluated."""
    # Arrange
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
        lookup_display_field=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        name_key="entity.test",
        description_key=None,
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
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    request = RuntimeEvaluationRequestDTO(
        entity_id="project",
        field_values={"name": ""},  # Validation will fail
    )

    # Act
    result = use_case.execute(request)

    # Assert - output mappings not evaluated
    assert result.is_blocked is True
    assert result.validation_result.blocking is True
    assert result.output_mappings_result is None  # Not evaluated


# ============================================================================
# Test Error Scenarios
# ============================================================================


def test_entity_not_found_validation_fails():
    """When entity not found, validation fails gracefully."""
    # Arrange
    mock_schema = MockSchemaUseCases(entities=())
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    request = RuntimeEvaluationRequestDTO(
        entity_id="nonexistent",
        field_values={"field1": "value"},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.validation_result.success is False
    assert "not found" in result.validation_result.error_message.lower()


# ============================================================================
# Test Component Results
# ============================================================================


def test_control_rules_result_always_present():
    """Control rules result always present (never None)."""
    # Arrange
    field = FieldDefinitionDTO(
        id="name",
        field_type="TEXT",
        label="Name",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        lookup_display_field=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        name_key="entity.test",
        description_key=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map={})
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    request = RuntimeEvaluationRequestDTO(
        entity_id="project",
        field_values={"name": "Test"},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.control_rules_result is not None
    # Phase R-4: control_rules_result is now EntityControlRulesEvaluationResultDTO
    assert result.control_rules_result.entity_id == "project"


def test_validation_result_always_present():
    """Validation result always present (never None)."""
    # Arrange
    field = FieldDefinitionDTO(
        id="name",
        field_type="TEXT",
        label="Name",
        help_text=None,
        required=False,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        lookup_display_field=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        name_key="entity.test",
        description_key=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(field,),
    )
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map={})
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    request = RuntimeEvaluationRequestDTO(
        entity_id="project",
        field_values={"name": "Test"},
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.validation_result is not None
    assert result.validation_result.success is True


# ============================================================================
# Test Blocking Reason Messages
# ============================================================================


def test_blocking_reason_includes_error_count():
    """Blocking reason includes number of ERROR issues."""
    # Arrange
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
        lookup_display_field=None,
        child_entity_id=None,
    )
    field2 = FieldDefinitionDTO(
        id="code",
        field_type="TEXT",
        label="Code",
        help_text=None,
        required=True,
        default_value=None,
        options=(),
        formula=None,
        is_calculated=False,
        is_choice_field=False,
        is_collection_field=False,
        lookup_entity_id=None,
        lookup_display_field=None,
        child_entity_id=None,
    )
    entity = EntityDefinitionDTO(
        id="project",
        name="Project",
        description=None,
        name_key="entity.test",
        description_key=None,
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
        "code": (
            ConstraintExportDTO(
                constraint_type="RequiredConstraint",
                parameters={"severity": "ERROR"},
            ),
        ),
    }
    mock_schema = MockSchemaUseCases(entities=(entity,), constraints_map=constraints_map)
    use_case = EvaluateRuntimeRulesUseCase(schema_usecases=mock_schema)

    request = RuntimeEvaluationRequestDTO(
        entity_id="project",
        field_values={"name": "", "code": ""},  # Both fail
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.is_blocked is True
    assert "2 ERROR severity" in result.blocking_reason or "2" in result.blocking_reason

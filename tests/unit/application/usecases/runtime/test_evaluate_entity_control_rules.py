"""Tests for EvaluateEntityControlRulesUseCase (Phase R-4).

Tests entity-level control rules aggregation.
"""

import pytest

from doc_helper.application.dto.runtime_dto import EntityControlRulesEvaluationResultDTO
from doc_helper.application.usecases.runtime.evaluate_entity_control_rules import (
    EvaluateEntityControlRulesUseCase,
)


# =============================================================================
# Mock SchemaUseCases (consistent with R-2/R-3 tests)
# =============================================================================


class MockSchemaUseCases:
    """Mock SchemaUseCases for testing (mimics R-2/R-3 pattern)."""

    def __init__(self, entities=None):
        """Initialize with optional entity definitions."""
        self._entities = entities or []

    def get_all_entities(self):
        """Return all entities."""
        return self._entities

    def list_control_rules_for_field(self, entity_id: str, field_id: str):
        """Return control rules for a field (empty for default tests)."""
        return ()  # No control rules by default


class MockEntityDTO:
    """Mock EntityDTO for testing."""

    def __init__(self, entity_id: str, fields=None):
        self.id = entity_id
        self.fields = fields or []


class MockFieldDTO:
    """Mock FieldDTO for testing."""

    def __init__(self, field_id: str, label: str = None):
        self.id = field_id
        self.label = label or field_id  # Default label to field_id


# =============================================================================
# Test 1: Entity aggregation correctness - Multiple fields
# =============================================================================


def test_multiple_fields_aggregation():
    """Test aggregation across multiple fields in entity."""
    # Setup: Entity with 3 fields
    field1 = MockFieldDTO("field1")
    field2 = MockFieldDTO("field2")
    field3 = MockFieldDTO("field3")

    entity = MockEntityDTO("test_entity", fields=[field1, field2, field3])
    schema_usecases = MockSchemaUseCases(entities=[entity])

    use_case = EvaluateEntityControlRulesUseCase(
        schema_usecases=schema_usecases,
    )

    # Execute
    result = use_case.execute(
        entity_id="test_entity",
        field_values={
            "field1": "value1",
            "field2": "value2",
            "field3": "value3",
        },
    )

    # Assert: All fields evaluated
    assert isinstance(result, EntityControlRulesEvaluationResultDTO)
    assert result.entity_id == "test_entity"
    assert len(result.field_results) == 3

    # Assert: Field IDs match
    field_ids = [fr.field_id for fr in result.field_results]
    assert "field1" in field_ids
    assert "field2" in field_ids
    assert "field3" in field_ids


# =============================================================================
# Test 2: Default control states (no rules)
# =============================================================================


def test_default_control_states():
    """Test default control states when no rules exist."""
    field1 = MockFieldDTO("field1")
    entity = MockEntityDTO("test_entity", fields=[field1])
    schema_usecases = MockSchemaUseCases(entities=[entity])

    use_case = EvaluateEntityControlRulesUseCase(
        schema_usecases=schema_usecases,
    )

    result = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "value1"},
    )

    # Assert: Default states (visible, enabled, not required)
    assert len(result.field_results) == 1
    field_result = result.field_results[0]
    assert field_result.field_id == "field1"
    assert field_result.visibility is True
    assert field_result.enabled is True
    assert field_result.required is False


# =============================================================================
# Test 3: Determinism - Same inputs produce same outputs
# =============================================================================


def test_deterministic_evaluation():
    """Test determinism: same inputs → identical outputs."""
    field1 = MockFieldDTO("field1")
    field2 = MockFieldDTO("field2")
    entity = MockEntityDTO("test_entity", fields=[field1, field2])
    schema_usecases = MockSchemaUseCases(entities=[entity])

    use_case = EvaluateEntityControlRulesUseCase(
        schema_usecases=schema_usecases,
    )

    field_values = {"field1": "test", "field2": "data"}

    # Execute twice with same inputs
    result1 = use_case.execute(
        entity_id="test_entity",
        field_values=field_values,
    )
    result2 = use_case.execute(
        entity_id="test_entity",
        field_values=field_values,
    )

    # Assert: Results identical
    assert result1.entity_id == result2.entity_id
    assert len(result1.field_results) == len(result2.field_results)

    for fr1, fr2 in zip(result1.field_results, result2.field_results):
        assert fr1.field_id == fr2.field_id
        assert fr1.visibility == fr2.visibility
        assert fr1.enabled == fr2.enabled
        assert fr1.required == fr2.required


# =============================================================================
# Test 4: Input unchanged after evaluation (purity)
# =============================================================================


def test_input_unchanged_after_evaluation():
    """Test purity: input field_values dict not modified."""
    field1 = MockFieldDTO("field1")
    entity = MockEntityDTO("test_entity", fields=[field1])
    schema_usecases = MockSchemaUseCases(entities=[entity])

    use_case = EvaluateEntityControlRulesUseCase(
        schema_usecases=schema_usecases,
    )

    # Original field values
    field_values = {"field1": "original"}
    original_copy = field_values.copy()

    # Execute
    use_case.execute(
        entity_id="test_entity",
        field_values=field_values,
    )

    # Assert: Input unchanged
    assert field_values == original_copy


# =============================================================================
# Test 5: Entity not found returns default
# =============================================================================


def test_entity_not_found_returns_default():
    """Test entity not found returns default result."""
    schema_usecases = MockSchemaUseCases(entities=[])  # No entities

    use_case = EvaluateEntityControlRulesUseCase(
        schema_usecases=schema_usecases,
    )

    result = use_case.execute(
        entity_id="nonexistent_entity",
        field_values={},
    )

    # Assert: Default result (no fields)
    assert result.entity_id == "nonexistent_entity"
    assert len(result.field_results) == 0
    assert result.has_any_rule is False


# =============================================================================
# Test 6: Empty entity (no fields)
# =============================================================================


def test_empty_entity_no_fields():
    """Test entity with no fields returns empty result."""
    entity = MockEntityDTO("empty_entity", fields=[])  # No fields
    schema_usecases = MockSchemaUseCases(entities=[entity])

    use_case = EvaluateEntityControlRulesUseCase(
        schema_usecases=schema_usecases,
    )

    result = use_case.execute(
        entity_id="empty_entity",
        field_values={},
    )

    # Assert: Empty field results
    assert result.entity_id == "empty_entity"
    assert len(result.field_results) == 0
    assert result.has_any_rule is False


# =============================================================================
# Test 7: Single-entity scope enforcement
# =============================================================================


def test_single_entity_scope():
    """Test single-entity scope: only evaluates requested entity."""
    # Setup: Two entities
    field1 = MockFieldDTO("field1")
    entity1 = MockEntityDTO("entity1", fields=[field1])

    field2 = MockFieldDTO("field2")
    entity2 = MockEntityDTO("entity2", fields=[field2])

    schema_usecases = MockSchemaUseCases(entities=[entity1, entity2])

    use_case = EvaluateEntityControlRulesUseCase(
        schema_usecases=schema_usecases,
    )

    # Execute: Request entity1 only
    result = use_case.execute(
        entity_id="entity1",
        field_values={"field1": "value1"},
    )

    # Assert: Only entity1 fields evaluated
    assert result.entity_id == "entity1"
    assert len(result.field_results) == 1
    assert result.field_results[0].field_id == "field1"


# =============================================================================
# Test 8: has_any_rule flag correctly determined
# =============================================================================


def test_has_any_rule_flag():
    """Test has_any_rule flag correctly reflects presence of rules."""
    field1 = MockFieldDTO("field1")
    entity = MockEntityDTO("test_entity", fields=[field1])
    schema_usecases = MockSchemaUseCases(entities=[entity])

    use_case = EvaluateEntityControlRulesUseCase(
        schema_usecases=schema_usecases,
    )

    result = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "value1"},
    )

    # Assert: No rules (all defaults)
    # Default: visibility=True, enabled=True, required=False
    # has_any_rule should be False
    assert result.has_any_rule is False


# =============================================================================
# Test 9: Schema fetch failure returns default
# =============================================================================


class FailingSchemaUseCases:
    """Mock SchemaUseCases that raises exception."""

    def get_all_entities(self):
        """Raise exception to simulate fetch failure."""
        raise Exception("Schema fetch failed")


def test_schema_fetch_failure_returns_default():
    """Test schema fetch failure returns default result."""
    schema_usecases = FailingSchemaUseCases()

    use_case = EvaluateEntityControlRulesUseCase(
        schema_usecases=schema_usecases,
    )

    result = use_case.execute(
        entity_id="test_entity",
        field_values={"field1": "value1"},
    )

    # Assert: Default result (no fields)
    assert result.entity_id == "test_entity"
    assert len(result.field_results) == 0
    assert result.has_any_rule is False


# =============================================================================
# Test 10: R-3 Integration - Control rules aggregated
# =============================================================================


def test_r3_integration_with_entity_control_rules():
    """Test R-3 orchestrator uses entity-level control rules aggregation."""
    from doc_helper.application.dto.runtime_dto import RuntimeEvaluationRequestDTO
    from doc_helper.application.usecases.runtime.evaluate_runtime_rules import (
        EvaluateRuntimeRulesUseCase,
    )

    # Setup: Entity with field
    field1 = MockFieldDTO("project_name")
    entity = MockEntityDTO("project", fields=[field1])
    schema_usecases = MockSchemaUseCases(entities=[entity])

    # Initialize R-3 orchestrator
    orchestrator = EvaluateRuntimeRulesUseCase(
        schema_usecases=schema_usecases,
    )

    # Execute R-3
    request = RuntimeEvaluationRequestDTO(
        entity_id="project",
        field_values={"project_name": "Test Project"},
    )
    result = orchestrator.execute(request)

    # Assert: control_rules_result is entity-level aggregation
    assert result.control_rules_result is not None
    assert isinstance(result.control_rules_result, EntityControlRulesEvaluationResultDTO)
    assert result.control_rules_result.entity_id == "project"
    assert len(result.control_rules_result.field_results) == 1


# =============================================================================
# Test 11: R-3 Integration - No placeholder remains
# =============================================================================


def test_r3_no_placeholder_control_rules():
    """Test R-3 no longer uses placeholder control rules result."""
    from doc_helper.application.dto.runtime_dto import RuntimeEvaluationRequestDTO
    from doc_helper.application.usecases.runtime.evaluate_runtime_rules import (
        EvaluateRuntimeRulesUseCase,
    )

    # Setup: Entity with multiple fields
    field1 = MockFieldDTO("field1")
    field2 = MockFieldDTO("field2")
    entity = MockEntityDTO("test_entity", fields=[field1, field2])
    schema_usecases = MockSchemaUseCases(entities=[entity])

    orchestrator = EvaluateRuntimeRulesUseCase(
        schema_usecases=schema_usecases,
    )

    request = RuntimeEvaluationRequestDTO(
        entity_id="test_entity",
        field_values={"field1": "value1", "field2": "value2"},
    )
    result = orchestrator.execute(request)

    # Assert: control_rules_result contains actual field results (not placeholder)
    assert result.control_rules_result.entity_id == "test_entity"
    assert len(result.control_rules_result.field_results) == 2  # Not empty/placeholder


# =============================================================================
# Test 12: Non-blocking behavior
# =============================================================================


def test_control_rules_never_block():
    """Test control rules never block runtime evaluation."""
    from doc_helper.application.dto.runtime_dto import RuntimeEvaluationRequestDTO
    from doc_helper.application.usecases.runtime.evaluate_runtime_rules import (
        EvaluateRuntimeRulesUseCase,
    )

    field1 = MockFieldDTO("field1")
    entity = MockEntityDTO("test_entity", fields=[field1])
    schema_usecases = MockSchemaUseCases(entities=[entity])

    orchestrator = EvaluateRuntimeRulesUseCase(
        schema_usecases=schema_usecases,
    )

    request = RuntimeEvaluationRequestDTO(
        entity_id="test_entity",
        field_values={"field1": "value1"},
    )
    result = orchestrator.execute(request)

    # Assert: Control rules evaluated but never block
    assert result.control_rules_result is not None
    # is_blocked should be False (no validation errors, no output mapping failures)
    assert result.is_blocked is False

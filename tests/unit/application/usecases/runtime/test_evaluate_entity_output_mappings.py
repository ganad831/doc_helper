"""Unit tests for EvaluateEntityOutputMappingsUseCase (Phase R-5).

Tests entity-level output mapping aggregation following ADR-050 requirements:
- Pull-based evaluation
- Deterministic behavior
- Blocking failures (ANY failure blocks entire entity)
- Single-entity scope
- Reuses Phase R-1 output mapping evaluation
"""

import pytest

from doc_helper.application.dto.export_dto import OutputMappingExportDTO
from doc_helper.application.dto.runtime_dto import (
    EntityOutputMappingsEvaluationDTO,
    OutputMappingEvaluationRequestDTO,
    OutputMappingEvaluationResultDTO,
)
from doc_helper.application.usecases.formula_usecases import FormulaUseCases
from doc_helper.application.usecases.runtime.evaluate_entity_output_mappings import (
    EvaluateEntityOutputMappingsUseCase,
)
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId


class MockSchemaRepository:
    """Mock schema repository for testing."""

    def __init__(self, entities: dict[EntityDefinitionId, EntityDefinition] | None = None):
        self.entities = entities or {}

    def exists(self, entity_id: EntityDefinitionId) -> bool:
        return entity_id in self.entities

    def get_by_id(self, entity_id: EntityDefinitionId):
        from doc_helper.domain.common.result import Success, Failure

        if entity_id in self.entities:
            return Success(self.entities[entity_id])
        else:
            return Failure(f"Entity {entity_id.value} not found")


class MockSchemaUseCases:
    """Mock SchemaUseCases for testing."""

    def __init__(
        self,
        schema_repository: MockSchemaRepository,
        field_mappings: dict[tuple[str, str], tuple[OutputMappingExportDTO, ...]] | None = None,
    ):
        self._schema_repository = schema_repository
        self.field_mappings = field_mappings or {}

    def list_output_mappings_for_field(
        self,
        entity_id: str,
        field_id: str,
    ) -> tuple[OutputMappingExportDTO, ...]:
        """Mock list_output_mappings_for_field."""
        key = (entity_id, field_id)
        return self.field_mappings.get(key, ())


# ============================================================================
# ADR-050 Compliance Tests: Entity-Level Aggregation
# ============================================================================


def test_single_field_single_output_mapping():
    """Test: Entity with single field, single output mapping → success.

    ADR-050: Entity-level aggregation succeeds if all field evaluations succeed.
    """
    # Arrange: Create entity with one field
    field1 = FieldDefinition(
        id=FieldDefinitionId("depth"),
        field_type=FieldType.NUMBER,
        label_key=TranslationKey("field.depth"),
        output_mappings=(
            OutputMappingExportDTO(
                target="NUMBER",
                formula_text="depth",
            ),
        ),
    )
    entity = EntityDefinition(
        id=EntityDefinitionId("project"),
        name_key=TranslationKey("entity.project"),
        fields={FieldDefinitionId("depth"): field1},
    )
    mock_repo = MockSchemaRepository(entities={EntityDefinitionId("project"): entity})
    mock_schema = MockSchemaUseCases(
        schema_repository=mock_repo,
        field_mappings={
            ("project", "depth"): (
                OutputMappingExportDTO(
                    target="NUMBER",
                    formula_text="depth",
                ),
            ),
        },
    )
    use_case = EvaluateEntityOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )

    # Act
    result = use_case.execute(
        entity_id="project",
        field_values={"depth": 5.0},
    )

    # Assert
    assert result.entity_id == "project"
    assert result.result.success is True
    assert result.result.values == {"NUMBER": 5.0}
    assert result.result.error is None


def test_multiple_fields_multiple_output_mappings():
    """Test: Entity with multiple fields, each with output mappings → aggregated.

    ADR-050: All successful output mappings aggregated into {target → value} map.
    """
    # Arrange: Create entity with two fields
    field1 = FieldDefinition(
        id=FieldDefinitionId("depth"),        field_type=FieldType.NUMBER,
        label_key=TranslationKey("field.Depth"),
        output_mappings=(
            OutputMappingExportDTO(
                target="NUMBER",
                formula_text="depth",
            ),
        ),
    )
    field2 = FieldDefinition(
        id=FieldDefinitionId("name"),        field_type=FieldType.TEXT,
        label_key=TranslationKey("field.project_name"),
        output_mappings=(
            OutputMappingExportDTO(
                target="TEXT",
                formula_text="name",
            ),
        ),
    )
    entity = EntityDefinition(
        id=EntityDefinitionId("project"),
        name_key=TranslationKey("field.Project"),
        fields={
            FieldDefinitionId("depth"): field1,
            FieldDefinitionId("name"): field2,
        },
    )
    mock_repo = MockSchemaRepository(entities={EntityDefinitionId("project"): entity})
    mock_schema = MockSchemaUseCases(
        schema_repository=mock_repo,
        field_mappings={
            ("project", "depth"): (
                OutputMappingExportDTO(
                    target="NUMBER",
                    formula_text="depth",
                ),
            ),
            ("project", "name"): (
                OutputMappingExportDTO(
                    target="TEXT",
                    formula_text="name",
                ),
            ),
        },
    )
    use_case = EvaluateEntityOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )

    # Act
    result = use_case.execute(
        entity_id="project",
        field_values={"depth": 10.0, "name": "Test Project"},
    )

    # Assert
    assert result.entity_id == "project"
    assert result.result.success is True
    assert result.result.values == {
        "NUMBER": 10.0,
        "TEXT": "Test Project",
    }
    assert result.result.error is None


def test_field_with_no_output_mappings_is_skipped():
    """Test: Field with no output mappings → skipped, not an error.

    ADR-050: Fields without output mappings are silently skipped.
    """
    # Arrange: Create entity with two fields, only one has output mapping
    field1 = FieldDefinition(
        id=FieldDefinitionId("depth"),        field_type=FieldType.NUMBER,
        label_key=TranslationKey("field.Depth"),
        output_mappings=(
            OutputMappingExportDTO(
                target="NUMBER",
                formula_text="depth",
            ),
        ),
    )
    field2 = FieldDefinition(
        id=FieldDefinitionId("description"),        field_type=FieldType.TEXT,
        label_key=TranslationKey("field.Description"),
        output_mappings=(),  # No output mappings
    )
    entity = EntityDefinition(
        id=EntityDefinitionId("project"),
        name_key=TranslationKey("field.Project"),
        fields={
            FieldDefinitionId("depth"): field1,
            FieldDefinitionId("description"): field2,
        },
    )
    mock_repo = MockSchemaRepository(entities={EntityDefinitionId("project"): entity})
    mock_schema = MockSchemaUseCases(
        schema_repository=mock_repo,
        field_mappings={
            ("project", "depth"): (
                OutputMappingExportDTO(
                    target="NUMBER",
                    formula_text="depth",
                ),
            ),
            # No mappings for "description"
        },
    )
    use_case = EvaluateEntityOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )

    # Act
    result = use_case.execute(
        entity_id="project",
        field_values={"depth": 5.0, "description": "Test"},
    )

    # Assert
    assert result.entity_id == "project"
    assert result.result.success is True
    assert result.result.values == {"NUMBER": 5.0}  # Only depth included
    assert result.result.error is None


def test_no_output_mappings_in_entity_returns_empty_success():
    """Test: Entity with no output mappings → success (empty result).

    ADR-050: No output mappings is NOT an error. Return empty success.
    """
    # Arrange: Create entity with fields but no output mappings
    field1 = FieldDefinition(
        id=FieldDefinitionId("depth"),        field_type=FieldType.NUMBER,
        label_key=TranslationKey("field.Depth"),
        output_mappings=(),  # No output mappings
    )
    entity = EntityDefinition(
        id=EntityDefinitionId("project"),
        name_key=TranslationKey("field.Project"),
        fields={FieldDefinitionId("depth"): field1},
    )
    mock_repo = MockSchemaRepository(entities={EntityDefinitionId("project"): entity})
    mock_schema = MockSchemaUseCases(
        schema_repository=mock_repo,
        field_mappings={},  # No mappings for any field
    )
    use_case = EvaluateEntityOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )

    # Act
    result = use_case.execute(
        entity_id="project",
        field_values={"depth": 5.0},
    )

    # Assert
    assert result.entity_id == "project"
    assert result.result.success is True
    assert result.result.values == {}  # Empty map
    assert result.result.error is None


def test_entity_not_found_returns_failure():
    """Test: Entity not found → failure.

    ADR-050: Entity not found blocks evaluation.
    """
    # Arrange: Empty repository
    mock_repo = MockSchemaRepository(entities={})
    mock_schema = MockSchemaUseCases(
        schema_repository=mock_repo,
        field_mappings={},
    )
    use_case = EvaluateEntityOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )

    # Act
    result = use_case.execute(
        entity_id="nonexistent",
        field_values={},
    )

    # Assert
    assert result.entity_id == "nonexistent"
    assert result.result.success is False
    assert result.result.values == {}
    assert "not found" in result.result.error.lower()


def test_entity_with_no_fields_returns_empty_success():
    """Test: Entity with no fields → success (empty result).

    ADR-050: Entity with no fields is valid, return empty success.
    """
    # Arrange: Create entity with no fields
    entity = EntityDefinition(
        id=EntityDefinitionId("project"),
        name_key=TranslationKey("field.Project"),
        fields={},  # No fields
    )
    mock_repo = MockSchemaRepository(entities={EntityDefinitionId("project"): entity})
    mock_schema = MockSchemaUseCases(
        schema_repository=mock_repo,
        field_mappings={},
    )
    use_case = EvaluateEntityOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )

    # Act
    result = use_case.execute(
        entity_id="project",
        field_values={},
    )

    # Assert
    assert result.entity_id == "project"
    assert result.result.success is True
    assert result.result.values == {}  # Empty map
    assert result.result.error is None


def test_first_output_mapping_failure_blocks_entity():
    """Test: First output mapping failure → entire entity evaluation blocked.

    ADR-050: Blocking semantics - ANY failure blocks entire entity.
    """
    # Arrange: Create entity with two fields, first has failing output mapping
    field1 = FieldDefinition(
        id=FieldDefinitionId("invalid_formula"),        field_type=FieldType.NUMBER,
        label_key=TranslationKey("field.invalid_formula_field"),
        output_mappings=(
            OutputMappingExportDTO(
                target="TEXT",
                formula_text="nonexistent_field",  # Will fail
            ),
        ),
    )
    field2 = FieldDefinition(
        id=FieldDefinitionId("name"),        field_type=FieldType.TEXT,
        label_key=TranslationKey("field.project_name"),
        output_mappings=(
            OutputMappingExportDTO(
                target="TEXT",
                formula_text="name",
            ),
        ),
    )
    entity = EntityDefinition(
        id=EntityDefinitionId("project"),
        name_key=TranslationKey("field.Project"),
        fields={
            FieldDefinitionId("invalid_formula"): field1,
            FieldDefinitionId("name"): field2,
        },
    )
    mock_repo = MockSchemaRepository(entities={EntityDefinitionId("project"): entity})
    mock_schema = MockSchemaUseCases(
        schema_repository=mock_repo,
        field_mappings={
            ("project", "invalid_formula"): (
                OutputMappingExportDTO(
                    target="TEXT",
                    formula_text="nonexistent_field",
                ),
            ),
            ("project", "name"): (
                OutputMappingExportDTO(
                    target="TEXT",
                    formula_text="name",
                ),
            ),
        },
    )
    use_case = EvaluateEntityOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )

    # Act
    result = use_case.execute(
        entity_id="project",
        field_values={"name": "Test Project"},  # Missing nonexistent_field
    )

    # Assert
    assert result.entity_id == "project"
    assert result.result.success is False
    assert result.result.values == {}  # No values on failure
    assert result.result.error is not None
    assert "invalid_formula" in result.result.error.lower()


def test_deterministic_evaluation():
    """Test: Determinism - same inputs → identical outputs.

    ADR-050: Same entity_id + field_values → identical results on multiple calls.
    """
    # Arrange
    field1 = FieldDefinition(
        id=FieldDefinitionId("depth"),        field_type=FieldType.NUMBER,
        label_key=TranslationKey("field.Depth"),
        output_mappings=(
            OutputMappingExportDTO(
                target="NUMBER",
                formula_text="depth",
            ),
        ),
    )
    entity = EntityDefinition(
        id=EntityDefinitionId("project"),
        name_key=TranslationKey("field.Project"),
        fields={FieldDefinitionId("depth"): field1},
    )
    mock_repo = MockSchemaRepository(entities={EntityDefinitionId("project"): entity})
    mock_schema = MockSchemaUseCases(
        schema_repository=mock_repo,
        field_mappings={
            ("project", "depth"): (
                OutputMappingExportDTO(
                    target="NUMBER",
                    formula_text="depth",
                ),
            ),
        },
    )
    use_case = EvaluateEntityOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )

    # Act: Execute twice with same inputs
    result1 = use_case.execute(
        entity_id="project",
        field_values={"depth": 5.0},
    )
    result2 = use_case.execute(
        entity_id="project",
        field_values={"depth": 5.0},
    )

    # Assert: Results should be identical
    assert result1.entity_id == result2.entity_id
    assert result1.result.success == result2.result.success
    assert result1.result.values == result2.result.values
    assert result1.result.error == result2.result.error


def test_mixed_field_types():
    """Test: Entity with TEXT, NUMBER, BOOLEAN fields → all types handled.

    ADR-050: All field types supported in entity-level aggregation.
    """
    # Arrange: Create entity with TEXT, NUMBER, BOOLEAN fields
    field1 = FieldDefinition(
        id=FieldDefinitionId("name"),        field_type=FieldType.TEXT,
        label_key=TranslationKey("field.project_name"),
        output_mappings=(
            OutputMappingExportDTO(
                target="TEXT",
                formula_text="name",
            ),
        ),
    )
    field2 = FieldDefinition(
        id=FieldDefinitionId("depth"),        field_type=FieldType.NUMBER,
        label_key=TranslationKey("field.Depth"),
        output_mappings=(
            OutputMappingExportDTO(
                target="NUMBER",
                formula_text="depth",
            ),
        ),
    )
    field3 = FieldDefinition(
        id=FieldDefinitionId("active"),        field_type=FieldType.CHECKBOX,
        label_key=TranslationKey("field.Active"),
        output_mappings=(
            OutputMappingExportDTO(
                target="BOOLEAN",
                formula_text="active",
            ),
        ),
    )
    entity = EntityDefinition(
        id=EntityDefinitionId("project"),
        name_key=TranslationKey("field.Project"),
        fields={
            FieldDefinitionId("name"): field1,
            FieldDefinitionId("depth"): field2,
            FieldDefinitionId("active"): field3,
        },
    )
    mock_repo = MockSchemaRepository(entities={EntityDefinitionId("project"): entity})
    mock_schema = MockSchemaUseCases(
        schema_repository=mock_repo,
        field_mappings={
            ("project", "name"): (
                OutputMappingExportDTO(
                    target="TEXT",
                    formula_text="name",
                ),
            ),
            ("project", "depth"): (
                OutputMappingExportDTO(
                    target="NUMBER",
                    formula_text="depth",
                ),
            ),
            ("project", "active"): (
                OutputMappingExportDTO(
                    target="BOOLEAN",
                    formula_text="active",
                ),
            ),
        },
    )
    use_case = EvaluateEntityOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )

    # Act
    result = use_case.execute(
        entity_id="project",
        field_values={"name": "Test", "depth": 10.5, "active": True},
    )

    # Assert
    assert result.entity_id == "project"
    assert result.result.success is True
    assert result.result.values == {
        "TEXT": "Test",
        "NUMBER": 10.5,
        "BOOLEAN": True,
    }
    assert result.result.error is None


def test_multiple_output_mappings_per_field():
    """Test: Single field with multiple output mappings → all evaluated.

    ADR-050: Fields can have multiple output mappings, all should be aggregated.
    """
    # Arrange: Create entity with one field having two output mappings
    field1 = FieldDefinition(
        id=FieldDefinitionId("depth"),        field_type=FieldType.NUMBER,
        label_key=TranslationKey("field.Depth"),
        output_mappings=(
            OutputMappingExportDTO(
                target="NUMBER",
                formula_text="depth",
            ),
            OutputMappingExportDTO(
                target="NUMBER",
                formula_text="depth * 100",
            ),
        ),
    )
    entity = EntityDefinition(
        id=EntityDefinitionId("project"),
        name_key=TranslationKey("field.Project"),
        fields={FieldDefinitionId("depth"): field1},
    )
    mock_repo = MockSchemaRepository(entities={EntityDefinitionId("project"): entity})
    mock_schema = MockSchemaUseCases(
        schema_repository=mock_repo,
        field_mappings={
            ("project", "depth"): (
                OutputMappingExportDTO(
                    target="NUMBER",
                    formula_text="depth",
                ),
                OutputMappingExportDTO(
                    target="NUMBER",
                    formula_text="depth * 100",
                ),
            ),
        },
    )
    use_case = EvaluateEntityOutputMappingsUseCase(
        schema_usecases=mock_schema,
        formula_usecases=FormulaUseCases(),
    )

    # Act
    result = use_case.execute(
        entity_id="project",
        field_values={"depth": 5.0},
    )

    # Assert
    assert result.entity_id == "project"
    assert result.result.success is True
    # Both mappings have target="NUMBER", R-1 returns first successful mapping
    # So first mapping (depth = 5.0) is evaluated and returned
    assert result.result.values == {
        "NUMBER": 5.0,  # First successful mapping is used
    }
    assert result.result.error is None

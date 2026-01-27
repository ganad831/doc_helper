"""Unit tests for AddOutputMappingCommand (Phase A6.1).

Tests for output mapping creation at the command layer, verifying:
- Successful creation
- Duplicate target rejection
- Input validation
- Entity/field existence checks

INVARIANTS (enforced by tests):
- Output mappings are DESIGN-TIME metadata only
- NO runtime execution occurs
- Output mappings stored in field's output_mappings tuple
- Only one mapping per target type per field
- Target must be TEXT, NUMBER, or BOOLEAN
"""

import pytest
from dataclasses import replace
from unittest.mock import Mock

from doc_helper.application.commands.schema.add_output_mapping_command import (
    AddOutputMappingCommand,
)
from doc_helper.application.dto.export_dto import OutputMappingExportDTO
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType


class TestAddOutputMappingCommand:
    """Unit tests for AddOutputMappingCommand."""

    @pytest.fixture
    def mock_field_definition(self) -> FieldDefinition:
        """Create mock field definition without output mappings."""
        return FieldDefinition(
            id=FieldDefinitionId("test_field"),
            label_key=TranslationKey("field.test"),
            field_type=FieldType.TEXT,
            output_mappings=(),
        )

    @pytest.fixture
    def mock_entity(self, mock_field_definition: FieldDefinition) -> Mock:
        """Create mock entity with field."""
        entity = Mock()
        entity.fields = {FieldDefinitionId("test_field"): mock_field_definition}
        entity.update_field = Mock()
        return entity

    @pytest.fixture
    def mock_schema_repository(self, mock_entity: Mock) -> Mock:
        """Create mock schema repository."""
        repository = Mock(spec=ISchemaRepository)
        repository.exists = Mock(return_value=True)
        repository.get_by_id = Mock(return_value=Success(mock_entity))
        repository.save = Mock(return_value=Success(None))
        return repository

    @pytest.fixture
    def command(self, mock_schema_repository: Mock) -> AddOutputMappingCommand:
        """Create command instance with mock repository."""
        return AddOutputMappingCommand(schema_repository=mock_schema_repository)

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_add_text_mapping_success(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully add TEXT output mapping.

        REQUIREMENT: Successful creation of output mapping.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="{{depth_from}} - {{depth_to}}",
        )

        # Assert success
        assert result.is_success()
        assert result.value == FieldDefinitionId("test_field")

        # Assert repository methods called correctly
        mock_schema_repository.exists.assert_called_once_with(
            EntityDefinitionId("project")
        )
        mock_schema_repository.get_by_id.assert_called_once()
        mock_schema_repository.save.assert_called_once()

        # Assert field was updated with new mapping
        mock_entity.update_field.assert_called_once()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert len(updated_field.output_mappings) == 1
        assert updated_field.output_mappings[0].target == "TEXT"
        assert updated_field.output_mappings[0].formula_text == "{{depth_from}} - {{depth_to}}"

    def test_add_number_mapping_success(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully add NUMBER output mapping."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="NUMBER",
            formula_text="{{area}} * {{density}}",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert updated_field.output_mappings[0].target == "NUMBER"

    def test_add_boolean_mapping_success(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully add BOOLEAN output mapping."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="BOOLEAN",
            formula_text="{{status}} == 'active'",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert updated_field.output_mappings[0].target == "BOOLEAN"

    def test_target_normalized_to_uppercase(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Target should be normalized to uppercase."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="text",  # lowercase
            formula_text="{{value}}",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert updated_field.output_mappings[0].target == "TEXT"

    def test_formula_text_trimmed(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Formula text should be trimmed."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="  padded_formula  ",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert updated_field.output_mappings[0].formula_text == "padded_formula"

    def test_add_multiple_different_targets(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should allow adding mappings with different target types."""
        # Setup: field already has TEXT mapping
        existing_mapping = OutputMappingExportDTO(
            target="TEXT",
            formula_text="existing_formula",
        )
        field_with_mapping = replace(
            mock_field_definition, output_mappings=(existing_mapping,)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_mapping}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="NUMBER",  # Different target
            formula_text="{{count}}",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert len(updated_field.output_mappings) == 2

    # =========================================================================
    # DUPLICATE TARGET REJECTION TESTS
    # =========================================================================

    def test_duplicate_target_rejected(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should reject duplicate target type on same field.

        INVARIANT: Only one mapping per target type per field.
        """
        # Setup: field already has TEXT mapping
        existing_mapping = OutputMappingExportDTO(
            target="TEXT",
            formula_text="existing_formula",
        )
        field_with_mapping = replace(
            mock_field_definition, output_mappings=(existing_mapping,)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_mapping}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",  # Duplicate target
            formula_text="new_formula",
        )

        assert result.is_failure()
        assert "already has an output mapping for target TEXT" in result.error
        assert "UpdateOutputMappingCommand" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_duplicate_target_case_insensitive(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Duplicate detection should be case-insensitive."""
        existing_mapping = OutputMappingExportDTO(
            target="TEXT",
            formula_text="existing_formula",
        )
        field_with_mapping = replace(
            mock_field_definition, output_mappings=(existing_mapping,)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_mapping}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="text",  # lowercase, should still match
            formula_text="new_formula",
        )

        assert result.is_failure()
        assert "already has an output mapping" in result.error

    # =========================================================================
    # INPUT VALIDATION TESTS
    # =========================================================================

    def test_missing_entity_id_rejected(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing entity_id."""
        result = command.execute(
            entity_id="",
            field_id="test_field",
            target="TEXT",
            formula_text="{{value}}",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()
        mock_schema_repository.save.assert_not_called()

    def test_missing_field_id_rejected(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing field_id."""
        result = command.execute(
            entity_id="project",
            field_id="",
            target="TEXT",
            formula_text="{{value}}",
        )

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

    def test_missing_target_rejected(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing target."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="",
            formula_text="{{value}}",
        )

        assert result.is_failure()
        assert "target is required" in result.error.lower()

    def test_missing_formula_text_rejected(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing formula_text."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="",
        )

        assert result.is_failure()
        assert "formula_text is required" in result.error.lower()

    def test_whitespace_only_entity_id_rejected(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject whitespace-only entity_id."""
        result = command.execute(
            entity_id="   ",
            field_id="test_field",
            target="TEXT",
            formula_text="{{value}}",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

    def test_invalid_target_rejected(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject invalid target type."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="INVALID_TARGET",
            formula_text="{{value}}",
        )

        assert result.is_failure()
        assert "invalid target" in result.error.lower()
        assert "INVALID_TARGET" in result.error
        mock_schema_repository.save.assert_not_called()

    # =========================================================================
    # ENTITY/FIELD EXISTENCE TESTS
    # =========================================================================

    def test_nonexistent_entity_rejected(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject if entity does not exist."""
        mock_schema_repository.exists.return_value = False

        result = command.execute(
            entity_id="nonexistent",
            field_id="test_field",
            target="TEXT",
            formula_text="{{value}}",
        )

        assert result.is_failure()
        assert "does not exist" in result.error.lower()
        assert "nonexistent" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_nonexistent_field_rejected(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should reject if field does not exist in entity."""
        result = command.execute(
            entity_id="project",
            field_id="nonexistent_field",
            target="TEXT",
            formula_text="{{value}}",
        )

        assert result.is_failure()
        assert "not found" in result.error.lower()
        assert "nonexistent_field" in result.error

    # =========================================================================
    # REPOSITORY ERROR PROPAGATION TESTS
    # =========================================================================

    def test_repository_load_failure_propagated(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should propagate repository load failure."""
        mock_schema_repository.get_by_id.return_value = Failure(
            "Database error: connection lost"
        )

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="{{value}}",
        )

        assert result.is_failure()
        assert "failed to load entity" in result.error.lower()

    def test_repository_save_failure_propagated(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should propagate repository save failure."""
        mock_schema_repository.save.return_value = Failure(
            "Database error: constraint violation"
        )

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="{{value}}",
        )

        assert result.is_failure()
        assert "failed to add output mapping" in result.error.lower()
        assert "database error" in result.error.lower()

    # =========================================================================
    # DESIGN-TIME INVARIANT TESTS
    # =========================================================================

    def test_design_time_only_invariant_documented(
        self,
        command: AddOutputMappingCommand,
    ) -> None:
        """Verify design-time invariant is documented in command.

        INVARIANT: Output mappings are design-time metadata only.
        """
        docstring = AddOutputMappingCommand.__doc__
        assert docstring is not None
        assert "design-time" in docstring.lower()

        execute_docstring = AddOutputMappingCommand.execute.__doc__
        assert execute_docstring is not None
        assert "design-time" in execute_docstring.lower()

    def test_no_runtime_execution(
        self,
        command: AddOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Adding output mapping should NOT trigger any runtime execution.

        INVARIANT: NO runtime execution occurs in this command.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="{{value}}",
        )

        assert result.is_success()

        # Assert ONLY these operations occurred (no runtime behavior)
        mock_schema_repository.exists.assert_called_once()
        mock_schema_repository.get_by_id.assert_called_once()
        mock_entity.update_field.assert_called_once()
        mock_schema_repository.save.assert_called_once()

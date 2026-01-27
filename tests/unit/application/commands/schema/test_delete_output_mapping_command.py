"""Unit tests for DeleteOutputMappingCommand (Phase A6.1).

Tests for output mapping deletion at the command layer, verifying:
- Successful deletion
- Non-existent mapping rejection
- No cascade effects
- Input validation

INVARIANTS (enforced by tests):
- Output mappings are DESIGN-TIME metadata only
- NO runtime execution occurs
- Deletion removes mapping from field's output_mappings tuple
- Deletion does NOT cascade to other mappings
- Deletion does NOT cascade to other fields
- Mapping must exist before deleting
"""

import pytest
from dataclasses import replace
from unittest.mock import Mock

from doc_helper.application.commands.schema.delete_output_mapping_command import (
    DeleteOutputMappingCommand,
)
from doc_helper.application.dto.export_dto import OutputMappingExportDTO
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType


class TestDeleteOutputMappingCommand:
    """Unit tests for DeleteOutputMappingCommand."""

    @pytest.fixture
    def existing_mapping(self) -> OutputMappingExportDTO:
        """Create existing output mapping."""
        return OutputMappingExportDTO(
            target="TEXT",
            formula_text="original_formula",
        )

    @pytest.fixture
    def mock_field_definition(
        self, existing_mapping: OutputMappingExportDTO
    ) -> FieldDefinition:
        """Create mock field definition with existing output mapping."""
        return FieldDefinition(
            id=FieldDefinitionId("test_field"),
            label_key=TranslationKey("field.test"),
            field_type=FieldType.TEXT,
            output_mappings=(existing_mapping,),
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
    def command(self, mock_schema_repository: Mock) -> DeleteOutputMappingCommand:
        """Create command instance with mock repository."""
        return DeleteOutputMappingCommand(schema_repository=mock_schema_repository)

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_delete_mapping_success(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully delete existing output mapping.

        REQUIREMENT: Successful deletion.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
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

        # Assert field was updated with mapping removed
        mock_entity.update_field.assert_called_once()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert len(updated_field.output_mappings) == 0

    def test_delete_preserves_other_mappings(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Delete should preserve other mappings on the same field.

        INVARIANT: Deletion does NOT cascade to other mappings.
        """
        # Setup: field has multiple mappings
        text_mapping = OutputMappingExportDTO(
            target="TEXT",
            formula_text="text_formula",
        )
        number_mapping = OutputMappingExportDTO(
            target="NUMBER",
            formula_text="number_formula",
        )
        boolean_mapping = OutputMappingExportDTO(
            target="BOOLEAN",
            formula_text="boolean_formula",
        )
        field_with_mappings = replace(
            mock_field_definition,
            output_mappings=(text_mapping, number_mapping, boolean_mapping),
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_mappings}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]

        # Should have 2 mappings remaining
        assert len(updated_field.output_mappings) == 2

        # TEXT should be removed, others preserved
        targets = {m.target for m in updated_field.output_mappings}
        assert "TEXT" not in targets
        assert "NUMBER" in targets
        assert "BOOLEAN" in targets

    def test_delete_number_mapping(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should delete NUMBER mapping successfully."""
        number_mapping = OutputMappingExportDTO(
            target="NUMBER",
            formula_text="number_formula",
        )
        field_with_number = replace(
            mock_field_definition, output_mappings=(number_mapping,)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_number}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="NUMBER",
        )

        assert result.is_success()

    def test_delete_boolean_mapping(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should delete BOOLEAN mapping successfully."""
        boolean_mapping = OutputMappingExportDTO(
            target="BOOLEAN",
            formula_text="boolean_formula",
        )
        field_with_boolean = replace(
            mock_field_definition, output_mappings=(boolean_mapping,)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_boolean}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="BOOLEAN",
        )

        assert result.is_success()

    def test_target_case_insensitive(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Target should be case-insensitive for matching."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="text",  # lowercase
        )

        assert result.is_success()

    # =========================================================================
    # NON-EXISTENT MAPPING REJECTION TESTS
    # =========================================================================

    def test_nonexistent_mapping_rejected(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should reject deletion of non-existent target type.

        REQUIREMENT: Mapping must exist before deleting.
        """
        # Field has TEXT, but we try to delete NUMBER
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="NUMBER",
        )

        assert result.is_failure()
        assert "no number output mapping found" in result.error.lower()
        assert "nothing to delete" in result.error.lower()
        mock_schema_repository.save.assert_not_called()

    def test_field_with_no_mappings_rejected(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should reject if field has no output mappings at all."""
        field_no_mappings = replace(mock_field_definition, output_mappings=())
        mock_entity.fields = {FieldDefinitionId("test_field"): field_no_mappings}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
        )

        assert result.is_failure()
        assert "no text output mapping found" in result.error.lower()

    # =========================================================================
    # NO CASCADE EFFECTS TESTS
    # =========================================================================

    def test_no_cascade_to_other_fields(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Deleting mapping should not affect other fields.

        INVARIANT: Deletion does NOT cascade to other fields.
        """
        # Add another field with its own mapping
        other_mapping = OutputMappingExportDTO(
            target="TEXT",
            formula_text="other_formula",
        )
        other_field = FieldDefinition(
            id=FieldDefinitionId("other_field"),
            label_key=TranslationKey("field.other"),
            field_type=FieldType.TEXT,
            output_mappings=(other_mapping,),
        )
        mock_entity.fields[FieldDefinitionId("other_field")] = other_field

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
        )

        assert result.is_success()

        # Only test_field should be updated
        call_args = mock_entity.update_field.call_args
        updated_field_id = call_args[0][0]
        assert updated_field_id == FieldDefinitionId("test_field")

        # Other field should not be touched
        assert mock_entity.update_field.call_count == 1

    def test_no_modification_to_other_entity_data(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Deleting mapping should not modify any other entity data.

        INVARIANT: Deletion does NOT cascade to entities.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
        )

        assert result.is_success()

        # Assert ONLY field update was called (no other entity modifications)
        mock_entity.update_field.assert_called_once()

    # =========================================================================
    # INPUT VALIDATION TESTS
    # =========================================================================

    def test_missing_entity_id_rejected(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing entity_id."""
        result = command.execute(
            entity_id="",
            field_id="test_field",
            target="TEXT",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()
        mock_schema_repository.save.assert_not_called()

    def test_missing_field_id_rejected(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing field_id."""
        result = command.execute(
            entity_id="project",
            field_id="",
            target="TEXT",
        )

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

    def test_missing_target_rejected(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing target."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="",
        )

        assert result.is_failure()
        assert "target is required" in result.error.lower()

    def test_whitespace_only_entity_id_rejected(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject whitespace-only entity_id."""
        result = command.execute(
            entity_id="   ",
            field_id="test_field",
            target="TEXT",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

    def test_invalid_target_rejected(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject invalid target type."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="INVALID_TARGET",
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
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject if entity does not exist."""
        mock_schema_repository.exists.return_value = False

        result = command.execute(
            entity_id="nonexistent",
            field_id="test_field",
            target="TEXT",
        )

        assert result.is_failure()
        assert "does not exist" in result.error.lower()
        assert "nonexistent" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_nonexistent_field_rejected(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should reject if field does not exist in entity."""
        result = command.execute(
            entity_id="project",
            field_id="nonexistent_field",
            target="TEXT",
        )

        assert result.is_failure()
        assert "not found" in result.error.lower()
        assert "nonexistent_field" in result.error

    # =========================================================================
    # REPOSITORY ERROR PROPAGATION TESTS
    # =========================================================================

    def test_repository_load_failure_propagated(
        self,
        command: DeleteOutputMappingCommand,
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
        )

        assert result.is_failure()
        assert "failed to load entity" in result.error.lower()

    def test_repository_save_failure_propagated(
        self,
        command: DeleteOutputMappingCommand,
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
        )

        assert result.is_failure()
        assert "failed to delete output mapping" in result.error.lower()
        assert "database error" in result.error.lower()

    # =========================================================================
    # DESIGN-TIME INVARIANT TESTS
    # =========================================================================

    def test_design_time_only_invariant_documented(
        self,
        command: DeleteOutputMappingCommand,
    ) -> None:
        """Verify design-time invariant is documented in command.

        INVARIANT: Output mappings are design-time metadata only.
        """
        docstring = DeleteOutputMappingCommand.__doc__
        assert docstring is not None
        assert "design-time" in docstring.lower()
        assert "cascade" in docstring.lower()

        execute_docstring = DeleteOutputMappingCommand.execute.__doc__
        assert execute_docstring is not None
        assert "design-time" in execute_docstring.lower()
        assert "cascade" in execute_docstring.lower()

    def test_no_runtime_execution(
        self,
        command: DeleteOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Deleting output mapping should NOT trigger any runtime execution.

        INVARIANT: NO runtime execution occurs in this command.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
        )

        assert result.is_success()

        # Assert ONLY these operations occurred (no runtime behavior)
        mock_schema_repository.exists.assert_called_once()
        mock_schema_repository.get_by_id.assert_called_once()
        mock_entity.update_field.assert_called_once()
        mock_schema_repository.save.assert_called_once()

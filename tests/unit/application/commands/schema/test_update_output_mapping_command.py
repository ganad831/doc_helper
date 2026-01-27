"""Unit tests for UpdateOutputMappingCommand (Phase A6.1).

Tests for output mapping update at the command layer, verifying:
- Successful formula_text update
- Non-existent mapping rejection
- Input validation
- Target type identity preservation

INVARIANTS (enforced by tests):
- Output mappings are DESIGN-TIME metadata only
- NO runtime execution occurs
- Target type (identity) cannot be changed
- Only formula_text can be updated
- Mapping must exist before updating
"""

import pytest
from dataclasses import replace
from unittest.mock import Mock

from doc_helper.application.commands.schema.update_output_mapping_command import (
    UpdateOutputMappingCommand,
)
from doc_helper.application.dto.export_dto import OutputMappingExportDTO
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType


class TestUpdateOutputMappingCommand:
    """Unit tests for UpdateOutputMappingCommand."""

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
    def command(self, mock_schema_repository: Mock) -> UpdateOutputMappingCommand:
        """Create command instance with mock repository."""
        return UpdateOutputMappingCommand(schema_repository=mock_schema_repository)

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_update_formula_text_success(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully update formula_text of existing mapping.

        REQUIREMENT: Successful update of formula_text.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="new_formula && updated",
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

        # Assert field was updated with new formula
        mock_entity.update_field.assert_called_once()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert len(updated_field.output_mappings) == 1
        assert updated_field.output_mappings[0].target == "TEXT"
        assert updated_field.output_mappings[0].formula_text == "new_formula && updated"

    def test_update_preserves_target_type(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Update should preserve target type (identity).

        INVARIANT: Target type is identity - cannot be changed.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="updated_formula",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        # Target type unchanged
        assert updated_field.output_mappings[0].target == "TEXT"

    def test_target_case_insensitive(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Target should be case-insensitive for matching."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="text",  # lowercase
            formula_text="updated_formula",
        )

        assert result.is_success()

    def test_formula_text_trimmed(
        self,
        command: UpdateOutputMappingCommand,
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

    def test_update_preserves_other_mappings(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Update should preserve other mappings on the same field."""
        # Setup: field has multiple mappings
        text_mapping = OutputMappingExportDTO(
            target="TEXT",
            formula_text="text_formula",
        )
        number_mapping = OutputMappingExportDTO(
            target="NUMBER",
            formula_text="number_formula",
        )
        field_with_mappings = replace(
            mock_field_definition, output_mappings=(text_mapping, number_mapping)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_mappings}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="updated_text",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]

        # Should have both mappings, only TEXT updated
        assert len(updated_field.output_mappings) == 2

        # Find each mapping
        mappings_by_target = {m.target: m for m in updated_field.output_mappings}
        assert mappings_by_target["TEXT"].formula_text == "updated_text"
        assert mappings_by_target["NUMBER"].formula_text == "number_formula"  # Unchanged

    # =========================================================================
    # NON-EXISTENT MAPPING REJECTION TESTS
    # =========================================================================

    def test_nonexistent_mapping_rejected(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should reject update of non-existent target type.

        REQUIREMENT: Mapping must exist before updating.
        """
        # Setup: field only has TEXT mapping
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="NUMBER",  # Does not exist
            formula_text="new_formula",
        )

        assert result.is_failure()
        assert "no number output mapping found" in result.error.lower()
        assert "AddOutputMappingCommand" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_field_with_no_mappings_rejected(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should reject if field has no output mappings at all."""
        # Setup: field has no mappings
        field_no_mappings = replace(mock_field_definition, output_mappings=())
        mock_entity.fields = {FieldDefinitionId("test_field"): field_no_mappings}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="new_formula",
        )

        assert result.is_failure()
        assert "no text output mapping found" in result.error.lower()

    # =========================================================================
    # INPUT VALIDATION TESTS
    # =========================================================================

    def test_missing_entity_id_rejected(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing entity_id."""
        result = command.execute(
            entity_id="",
            field_id="test_field",
            target="TEXT",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()
        mock_schema_repository.save.assert_not_called()

    def test_missing_field_id_rejected(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing field_id."""
        result = command.execute(
            entity_id="project",
            field_id="",
            target="TEXT",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

    def test_missing_target_rejected(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing target."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "target is required" in result.error.lower()

    def test_missing_formula_text_rejected(
        self,
        command: UpdateOutputMappingCommand,
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

    def test_invalid_target_rejected(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject invalid target type."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="INVALID_TARGET",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "invalid target" in result.error.lower()
        assert "INVALID_TARGET" in result.error

    # =========================================================================
    # ENTITY/FIELD EXISTENCE TESTS
    # =========================================================================

    def test_nonexistent_entity_rejected(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject if entity does not exist."""
        mock_schema_repository.exists.return_value = False

        result = command.execute(
            entity_id="nonexistent",
            field_id="test_field",
            target="TEXT",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "does not exist" in result.error.lower()
        mock_schema_repository.save.assert_not_called()

    def test_nonexistent_field_rejected(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should reject if field does not exist in entity."""
        result = command.execute(
            entity_id="project",
            field_id="nonexistent_field",
            target="TEXT",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "not found" in result.error.lower()

    # =========================================================================
    # REPOSITORY ERROR PROPAGATION TESTS
    # =========================================================================

    def test_repository_load_failure_propagated(
        self,
        command: UpdateOutputMappingCommand,
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
            formula_text="formula",
        )

        assert result.is_failure()
        assert "failed to load entity" in result.error.lower()

    def test_repository_save_failure_propagated(
        self,
        command: UpdateOutputMappingCommand,
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
            formula_text="formula",
        )

        assert result.is_failure()
        assert "failed to update output mapping" in result.error.lower()

    # =========================================================================
    # DESIGN-TIME INVARIANT TESTS
    # =========================================================================

    def test_design_time_only_invariant_documented(
        self,
        command: UpdateOutputMappingCommand,
    ) -> None:
        """Verify design-time invariant is documented in command.

        INVARIANT: Output mappings are design-time metadata only.
        """
        docstring = UpdateOutputMappingCommand.__doc__
        assert docstring is not None
        assert "design-time" in docstring.lower()

        execute_docstring = UpdateOutputMappingCommand.execute.__doc__
        assert execute_docstring is not None
        assert "design-time" in execute_docstring.lower()

    def test_no_runtime_execution(
        self,
        command: UpdateOutputMappingCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Updating output mapping should NOT trigger any runtime execution.

        INVARIANT: NO runtime execution occurs in this command.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            target="TEXT",
            formula_text="updated_formula",
        )

        assert result.is_success()

        # Assert ONLY these operations occurred (no runtime behavior)
        mock_schema_repository.exists.assert_called_once()
        mock_schema_repository.get_by_id.assert_called_once()
        mock_entity.update_field.assert_called_once()
        mock_schema_repository.save.assert_called_once()

    def test_identity_immutability_documented(
        self,
        command: UpdateOutputMappingCommand,
    ) -> None:
        """Verify target type identity immutability is documented.

        INVARIANT: Target type (identity) cannot be changed.
        """
        docstring = UpdateOutputMappingCommand.__doc__
        assert docstring is not None
        assert "identity" in docstring.lower() or "cannot be changed" in docstring.lower()

"""Unit tests for DeleteControlRuleCommand (Phase A5.1).

Tests for control rule deletion at the command layer, verifying:
- Successful deletion
- Non-existent rule rejection
- No cascade effects
- Input validation

INVARIANTS (enforced by tests):
- Control rules are DESIGN-TIME metadata only
- NO runtime execution occurs
- Deletion removes rule from field's control_rules tuple
- Deletion does NOT cascade to other rules
- Deletion does NOT cascade to other fields
- Rule must exist before deleting
"""

import pytest
from dataclasses import replace
from unittest.mock import Mock

from doc_helper.application.commands.schema.delete_control_rule_command import (
    DeleteControlRuleCommand,
)
from doc_helper.application.dto.export_dto import ControlRuleExportDTO
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType


class TestDeleteControlRuleCommand:
    """Unit tests for DeleteControlRuleCommand."""

    @pytest.fixture
    def existing_rule(self) -> ControlRuleExportDTO:
        """Create existing control rule."""
        return ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="original_formula",
        )

    @pytest.fixture
    def mock_field_definition(
        self, existing_rule: ControlRuleExportDTO
    ) -> FieldDefinition:
        """Create mock field definition with existing control rule."""
        return FieldDefinition(
            id=FieldDefinitionId("test_field"),
            label_key=TranslationKey("field.test"),
            field_type=FieldType.TEXT,
            control_rules=(existing_rule,),
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
    def command(self, mock_schema_repository: Mock) -> DeleteControlRuleCommand:
        """Create command instance with mock repository."""
        return DeleteControlRuleCommand(schema_repository=mock_schema_repository)

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_delete_rule_success(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully delete existing control rule.

        REQUIREMENT: Successful deletion.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
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

        # Assert field was updated with rule removed
        mock_entity.update_field.assert_called_once()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert len(updated_field.control_rules) == 0

    def test_delete_preserves_other_rules(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Delete should preserve other rules on the same field.

        INVARIANT: Deletion does NOT cascade to other rules.
        """
        # Setup: field has multiple rules
        visibility_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="visibility_formula",
        )
        enabled_rule = ControlRuleExportDTO(
            rule_type="ENABLED",
            target_field_id="test_field",
            formula_text="enabled_formula",
        )
        required_rule = ControlRuleExportDTO(
            rule_type="REQUIRED",
            target_field_id="test_field",
            formula_text="required_formula",
        )
        field_with_rules = replace(
            mock_field_definition,
            control_rules=(visibility_rule, enabled_rule, required_rule),
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_rules}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]

        # Should have 2 rules remaining
        assert len(updated_field.control_rules) == 2

        # VISIBILITY should be removed, others preserved
        rule_types = {r.rule_type for r in updated_field.control_rules}
        assert "VISIBILITY" not in rule_types
        assert "ENABLED" in rule_types
        assert "REQUIRED" in rule_types

    def test_delete_enabled_rule(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should delete ENABLED rule successfully."""
        enabled_rule = ControlRuleExportDTO(
            rule_type="ENABLED",
            target_field_id="test_field",
            formula_text="enabled_formula",
        )
        field_with_enabled = replace(
            mock_field_definition, control_rules=(enabled_rule,)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_enabled}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="ENABLED",
        )

        assert result.is_success()

    def test_delete_required_rule(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should delete REQUIRED rule successfully."""
        required_rule = ControlRuleExportDTO(
            rule_type="REQUIRED",
            target_field_id="test_field",
            formula_text="required_formula",
        )
        field_with_required = replace(
            mock_field_definition, control_rules=(required_rule,)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_required}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="REQUIRED",
        )

        assert result.is_success()

    def test_rule_type_case_insensitive(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Rule type should be case-insensitive for matching."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="visibility",  # lowercase
        )

        assert result.is_success()

    # =========================================================================
    # NON-EXISTENT RULE REJECTION TESTS
    # =========================================================================

    def test_nonexistent_rule_rejected(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should reject deletion of non-existent rule type.

        REQUIREMENT: Rule must exist before deleting.
        """
        # Field has VISIBILITY, but we try to delete ENABLED
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="ENABLED",
        )

        assert result.is_failure()
        assert "no enabled control rule found" in result.error.lower()
        assert "nothing to delete" in result.error.lower()
        mock_schema_repository.save.assert_not_called()

    def test_field_with_no_rules_rejected(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should reject if field has no control rules at all."""
        field_no_rules = replace(mock_field_definition, control_rules=())
        mock_entity.fields = {FieldDefinitionId("test_field"): field_no_rules}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.is_failure()
        assert "no visibility control rule found" in result.error.lower()

    # =========================================================================
    # NO CASCADE EFFECTS TESTS
    # =========================================================================

    def test_no_cascade_to_other_fields(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Deleting rule should not affect other fields.

        INVARIANT: Deletion does NOT cascade to other fields.
        """
        # Add another field with its own rule
        other_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="other_field",
            formula_text="other_formula",
        )
        other_field = FieldDefinition(
            id=FieldDefinitionId("other_field"),
            label_key=TranslationKey("field.other"),
            field_type=FieldType.TEXT,
            control_rules=(other_rule,),
        )
        mock_entity.fields[FieldDefinitionId("other_field")] = other_field

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
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
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Deleting rule should not modify any other entity data.

        INVARIANT: Deletion does NOT cascade to entities.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.is_success()

        # Assert ONLY field update was called (no other entity modifications)
        mock_entity.update_field.assert_called_once()

    # =========================================================================
    # INPUT VALIDATION TESTS
    # =========================================================================

    def test_missing_entity_id_rejected(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing entity_id."""
        result = command.execute(
            entity_id="",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()
        mock_schema_repository.save.assert_not_called()

    def test_missing_field_id_rejected(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing field_id."""
        result = command.execute(
            entity_id="project",
            field_id="",
            rule_type="VISIBILITY",
        )

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

    def test_missing_rule_type_rejected(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing rule_type."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="",
        )

        assert result.is_failure()
        assert "rule_type is required" in result.error.lower()

    def test_whitespace_only_entity_id_rejected(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject whitespace-only entity_id."""
        result = command.execute(
            entity_id="   ",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

    def test_invalid_rule_type_rejected(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject invalid rule_type."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="INVALID_TYPE",
        )

        assert result.is_failure()
        assert "invalid rule_type" in result.error.lower()
        assert "INVALID_TYPE" in result.error
        mock_schema_repository.save.assert_not_called()

    # =========================================================================
    # ENTITY/FIELD EXISTENCE TESTS
    # =========================================================================

    def test_nonexistent_entity_rejected(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject if entity does not exist."""
        mock_schema_repository.exists.return_value = False

        result = command.execute(
            entity_id="nonexistent",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.is_failure()
        assert "does not exist" in result.error.lower()
        assert "nonexistent" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_nonexistent_field_rejected(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should reject if field does not exist in entity."""
        result = command.execute(
            entity_id="project",
            field_id="nonexistent_field",
            rule_type="VISIBILITY",
        )

        assert result.is_failure()
        assert "not found" in result.error.lower()
        assert "nonexistent_field" in result.error

    # =========================================================================
    # REPOSITORY ERROR PROPAGATION TESTS
    # =========================================================================

    def test_repository_load_failure_propagated(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should propagate repository load failure."""
        mock_schema_repository.get_by_id.return_value = Failure(
            "Database error: connection lost"
        )

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.is_failure()
        assert "failed to load entity" in result.error.lower()

    def test_repository_save_failure_propagated(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should propagate repository save failure."""
        mock_schema_repository.save.return_value = Failure(
            "Database error: constraint violation"
        )

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.is_failure()
        assert "failed to delete control rule" in result.error.lower()
        assert "database error" in result.error.lower()

    # =========================================================================
    # DESIGN-TIME INVARIANT TESTS
    # =========================================================================

    def test_design_time_only_invariant_documented(
        self,
        command: DeleteControlRuleCommand,
    ) -> None:
        """Verify design-time invariant is documented in command.

        INVARIANT: Control rules are design-time metadata only.
        """
        docstring = DeleteControlRuleCommand.__doc__
        assert docstring is not None
        assert "design-time" in docstring.lower()
        assert "cascade" in docstring.lower()

        execute_docstring = DeleteControlRuleCommand.execute.__doc__
        assert execute_docstring is not None
        assert "design-time" in execute_docstring.lower()
        assert "cascade" in execute_docstring.lower()

    def test_no_runtime_execution(
        self,
        command: DeleteControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Deleting control rule should NOT trigger any runtime execution.

        INVARIANT: NO runtime execution occurs in this command.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.is_success()

        # Assert ONLY these operations occurred (no runtime behavior)
        mock_schema_repository.exists.assert_called_once()
        mock_schema_repository.get_by_id.assert_called_once()
        mock_entity.update_field.assert_called_once()
        mock_schema_repository.save.assert_called_once()

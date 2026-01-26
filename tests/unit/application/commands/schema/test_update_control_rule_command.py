"""Unit tests for UpdateControlRuleCommand (Phase A5.1).

Tests for control rule update at the command layer, verifying:
- Successful formula_text update
- Non-existent rule rejection
- Input validation
- Rule type identity preservation

INVARIANTS (enforced by tests):
- Control rules are DESIGN-TIME metadata only
- NO runtime execution occurs
- Rule type (identity) cannot be changed
- Only formula_text can be updated
- Rule must exist before updating
"""

import pytest
from dataclasses import replace
from unittest.mock import Mock

from doc_helper.application.commands.schema.update_control_rule_command import (
    UpdateControlRuleCommand,
)
from doc_helper.application.dto.export_dto import ControlRuleExportDTO
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType


class TestUpdateControlRuleCommand:
    """Unit tests for UpdateControlRuleCommand."""

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
    def command(self, mock_schema_repository: Mock) -> UpdateControlRuleCommand:
        """Create command instance with mock repository."""
        return UpdateControlRuleCommand(schema_repository=mock_schema_repository)

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_update_formula_text_success(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully update formula_text of existing rule.

        REQUIREMENT: Successful update of formula_text.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
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
        assert len(updated_field.control_rules) == 1
        assert updated_field.control_rules[0].rule_type == "VISIBILITY"
        assert updated_field.control_rules[0].formula_text == "new_formula && updated"

    def test_update_preserves_rule_type(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Update should preserve rule type (identity).

        INVARIANT: Rule type is identity - cannot be changed.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="updated_formula",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        # Rule type unchanged
        assert updated_field.control_rules[0].rule_type == "VISIBILITY"

    def test_rule_type_case_insensitive(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Rule type should be case-insensitive for matching."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="visibility",  # lowercase
            formula_text="updated_formula",
        )

        assert result.is_success()

    def test_formula_text_trimmed(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Formula text should be trimmed."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="  padded_formula  ",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert updated_field.control_rules[0].formula_text == "padded_formula"

    def test_update_preserves_other_rules(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Update should preserve other rules on the same field."""
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
        field_with_rules = replace(
            mock_field_definition, control_rules=(visibility_rule, enabled_rule)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_rules}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="updated_visibility",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]

        # Should have both rules, only VISIBILITY updated
        assert len(updated_field.control_rules) == 2

        # Find each rule
        rules_by_type = {r.rule_type: r for r in updated_field.control_rules}
        assert rules_by_type["VISIBILITY"].formula_text == "updated_visibility"
        assert rules_by_type["ENABLED"].formula_text == "enabled_formula"  # Unchanged

    # =========================================================================
    # NON-EXISTENT RULE REJECTION TESTS
    # =========================================================================

    def test_nonexistent_rule_rejected(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should reject update of non-existent rule type.

        REQUIREMENT: Rule must exist before updating.
        """
        # Setup: field only has VISIBILITY rule
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="ENABLED",  # Does not exist
            formula_text="new_formula",
        )

        assert result.is_failure()
        assert "no enabled control rule found" in result.error.lower()
        assert "AddControlRuleCommand" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_field_with_no_rules_rejected(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should reject if field has no control rules at all."""
        # Setup: field has no rules
        field_no_rules = replace(mock_field_definition, control_rules=())
        mock_entity.fields = {FieldDefinitionId("test_field"): field_no_rules}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="new_formula",
        )

        assert result.is_failure()
        assert "no visibility control rule found" in result.error.lower()

    # =========================================================================
    # INPUT VALIDATION TESTS
    # =========================================================================

    def test_missing_entity_id_rejected(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing entity_id."""
        result = command.execute(
            entity_id="",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()
        mock_schema_repository.save.assert_not_called()

    def test_missing_field_id_rejected(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing field_id."""
        result = command.execute(
            entity_id="project",
            field_id="",
            rule_type="VISIBILITY",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

    def test_missing_rule_type_rejected(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing rule_type."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "rule_type is required" in result.error.lower()

    def test_missing_formula_text_rejected(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject missing formula_text."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="",
        )

        assert result.is_failure()
        assert "formula_text is required" in result.error.lower()

    def test_invalid_rule_type_rejected(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject invalid rule_type."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="INVALID_TYPE",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "invalid rule_type" in result.error.lower()
        assert "INVALID_TYPE" in result.error

    # =========================================================================
    # ENTITY/FIELD EXISTENCE TESTS
    # =========================================================================

    def test_nonexistent_entity_rejected(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject if entity does not exist."""
        mock_schema_repository.exists.return_value = False

        result = command.execute(
            entity_id="nonexistent",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "does not exist" in result.error.lower()
        mock_schema_repository.save.assert_not_called()

    def test_nonexistent_field_rejected(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should reject if field does not exist in entity."""
        result = command.execute(
            entity_id="project",
            field_id="nonexistent_field",
            rule_type="VISIBILITY",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "not found" in result.error.lower()

    # =========================================================================
    # REPOSITORY ERROR PROPAGATION TESTS
    # =========================================================================

    def test_repository_load_failure_propagated(
        self,
        command: UpdateControlRuleCommand,
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
            formula_text="formula",
        )

        assert result.is_failure()
        assert "failed to load entity" in result.error.lower()

    def test_repository_save_failure_propagated(
        self,
        command: UpdateControlRuleCommand,
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
            formula_text="formula",
        )

        assert result.is_failure()
        assert "failed to update control rule" in result.error.lower()

    # =========================================================================
    # DESIGN-TIME INVARIANT TESTS
    # =========================================================================

    def test_design_time_only_invariant_documented(
        self,
        command: UpdateControlRuleCommand,
    ) -> None:
        """Verify design-time invariant is documented in command.

        INVARIANT: Control rules are design-time metadata only.
        """
        docstring = UpdateControlRuleCommand.__doc__
        assert docstring is not None
        assert "design-time" in docstring.lower()

        execute_docstring = UpdateControlRuleCommand.execute.__doc__
        assert execute_docstring is not None
        assert "design-time" in execute_docstring.lower()

    def test_no_runtime_execution(
        self,
        command: UpdateControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Updating control rule should NOT trigger any runtime execution.

        INVARIANT: NO runtime execution occurs in this command.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
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
        command: UpdateControlRuleCommand,
    ) -> None:
        """Verify rule type identity immutability is documented.

        INVARIANT: Rule type (identity) cannot be changed.
        """
        docstring = UpdateControlRuleCommand.__doc__
        assert docstring is not None
        assert "identity" in docstring.lower() or "cannot be changed" in docstring.lower()

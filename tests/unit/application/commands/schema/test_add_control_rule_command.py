"""Unit tests for AddControlRuleCommand (Phase A5.1).

Tests for control rule addition at the command layer, verifying:
- Successful addition
- Duplicate rule type rejection
- Input validation
- Entity/field existence checks

INVARIANTS (enforced by tests):
- Control rules are DESIGN-TIME metadata only
- NO runtime execution occurs
- One rule per type per field
- Rule stored in field's control_rules tuple
- Formula text stored as-is (no validation)
"""

import pytest
from dataclasses import replace
from unittest.mock import Mock

from doc_helper.application.commands.schema.add_control_rule_command import (
    AddControlRuleCommand,
)
from doc_helper.application.dto.export_dto import ControlRuleExportDTO
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType


class TestAddControlRuleCommand:
    """Unit tests for AddControlRuleCommand."""

    @pytest.fixture
    def mock_field_definition(self) -> FieldDefinition:
        """Create mock field definition with no control rules."""
        return FieldDefinition(
            id=FieldDefinitionId("test_field"),
            label_key=TranslationKey("field.test"),
            field_type=FieldType.TEXT,
            control_rules=(),  # Empty tuple - no rules yet
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
    def command(self, mock_schema_repository: Mock) -> AddControlRuleCommand:
        """Create command instance with mock repository."""
        return AddControlRuleCommand(schema_repository=mock_schema_repository)

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_add_visibility_rule_success(
        self,
        command: AddControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully add VISIBILITY control rule.

        REQUIREMENT: Successful addition of control rule.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="is_advanced_mode == true",
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

        # Assert field was updated with control rule
        mock_entity.update_field.assert_called_once()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert len(updated_field.control_rules) == 1
        assert updated_field.control_rules[0].rule_type == "VISIBILITY"
        assert updated_field.control_rules[0].formula_text == "is_advanced_mode == true"

    def test_add_enabled_rule_success(
        self,
        command: AddControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully add ENABLED control rule."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="ENABLED",
            formula_text="user_level > 5",
        )

        assert result.is_success()
        mock_entity.update_field.assert_called_once()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert updated_field.control_rules[0].rule_type == "ENABLED"

    def test_add_required_rule_success(
        self,
        command: AddControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully add REQUIRED control rule."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="REQUIRED",
            formula_text="mode == 'full'",
        )

        assert result.is_success()
        mock_entity.update_field.assert_called_once()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert updated_field.control_rules[0].rule_type == "REQUIRED"

    def test_rule_type_case_insensitive(
        self,
        command: AddControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Rule type should be case-insensitive and normalized to uppercase."""
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="visibility",  # lowercase
            formula_text="test_formula",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        assert updated_field.control_rules[0].rule_type == "VISIBILITY"  # Normalized

    def test_formula_text_stored_as_is(
        self,
        command: AddControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Formula text should be stored as-is (trimmed, no validation).

        INVARIANT: Formula text stored as-is (validation is caller's responsibility).
        """
        formula = "  complex && formula || with_operators  "
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text=formula,
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        # Should be trimmed
        assert updated_field.control_rules[0].formula_text == formula.strip()

    # =========================================================================
    # DUPLICATE RULE TYPE REJECTION TESTS
    # =========================================================================

    def test_duplicate_rule_type_rejected(
        self,
        command: AddControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should reject adding duplicate rule type.

        REQUIREMENT: One rule per type per field.
        INVARIANT: No duplicate rule type on field.
        """
        # Setup: field already has VISIBILITY rule
        existing_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="existing_formula",
        )
        field_with_rule = replace(
            mock_field_definition, control_rules=(existing_rule,)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_rule}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",  # Same type
            formula_text="new_formula",
        )

        assert result.is_failure()
        assert "already has a VISIBILITY control rule" in result.error
        assert "UpdateControlRuleCommand" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_can_add_different_rule_types(
        self,
        command: AddControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should allow adding different rule types to same field."""
        # Setup: field already has VISIBILITY rule
        existing_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="existing_formula",
        )
        field_with_rule = replace(
            mock_field_definition, control_rules=(existing_rule,)
        )
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_rule}

        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="ENABLED",  # Different type
            formula_text="new_formula",
        )

        assert result.is_success()
        call_args = mock_entity.update_field.call_args
        updated_field = call_args[0][1]
        # Should have both rules
        assert len(updated_field.control_rules) == 2

    # =========================================================================
    # INPUT VALIDATION TESTS
    # =========================================================================

    def test_missing_entity_id_rejected(
        self,
        command: AddControlRuleCommand,
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
        command: AddControlRuleCommand,
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
        mock_schema_repository.save.assert_not_called()

    def test_missing_rule_type_rejected(
        self,
        command: AddControlRuleCommand,
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
        mock_schema_repository.save.assert_not_called()

    def test_missing_formula_text_rejected(
        self,
        command: AddControlRuleCommand,
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
        mock_schema_repository.save.assert_not_called()

    def test_whitespace_only_entity_id_rejected(
        self,
        command: AddControlRuleCommand,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject whitespace-only entity_id."""
        result = command.execute(
            entity_id="   ",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="formula",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

    def test_invalid_rule_type_rejected(
        self,
        command: AddControlRuleCommand,
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
        assert "VISIBILITY" in result.error  # Suggests valid types
        mock_schema_repository.save.assert_not_called()

    # =========================================================================
    # ENTITY/FIELD EXISTENCE TESTS
    # =========================================================================

    def test_nonexistent_entity_rejected(
        self,
        command: AddControlRuleCommand,
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
        assert "nonexistent" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_nonexistent_field_rejected(
        self,
        command: AddControlRuleCommand,
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
        assert "nonexistent_field" in result.error
        mock_schema_repository.save.assert_not_called()

    # =========================================================================
    # REPOSITORY ERROR PROPAGATION TESTS
    # =========================================================================

    def test_repository_load_failure_propagated(
        self,
        command: AddControlRuleCommand,
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
        command: AddControlRuleCommand,
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
        assert "failed to add control rule" in result.error.lower()
        assert "database error" in result.error.lower()

    # =========================================================================
    # DESIGN-TIME INVARIANT TESTS
    # =========================================================================

    def test_design_time_only_invariant_documented(
        self,
        command: AddControlRuleCommand,
    ) -> None:
        """Verify design-time invariant is documented in command.

        INVARIANT: Control rules are design-time metadata only.
        """
        # Check docstring contains invariant documentation
        docstring = AddControlRuleCommand.__doc__
        assert docstring is not None
        assert "design-time" in docstring.lower()

        # Check execute method documents design-time behavior
        execute_docstring = AddControlRuleCommand.execute.__doc__
        assert execute_docstring is not None
        assert "design-time" in execute_docstring.lower()

    def test_no_runtime_execution(
        self,
        command: AddControlRuleCommand,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Adding control rule should NOT trigger any runtime execution.

        INVARIANT: NO runtime execution occurs in this command.
        """
        result = command.execute(
            entity_id="project",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="formula",
        )

        assert result.is_success()

        # Assert ONLY these operations occurred (no runtime behavior)
        mock_schema_repository.exists.assert_called_once()
        mock_schema_repository.get_by_id.assert_called_once()
        mock_entity.update_field.assert_called_once()
        mock_schema_repository.save.assert_called_once()

        # No other methods should be called (e.g., evaluate, execute, etc.)

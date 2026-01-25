"""Unit tests for DeleteFieldOptionCommand (Phase 2 Step 3)."""

from unittest.mock import Mock
import pytest

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.application.commands.schema.delete_field_option_command import (
    DeleteFieldOptionCommand,
)


class TestDeleteFieldOptionCommand:
    """Unit tests for DeleteFieldOptionCommand."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_dropdown_field(self) -> FieldDefinition:
        """Create mock DROPDOWN field with existing options."""
        return FieldDefinition(
            id=FieldDefinitionId("field_dropdown"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.dropdown.label"),
            required=False,
            options=(
                ("option1", TranslationKey("option.1")),
                ("option2", TranslationKey("option.2")),
                ("option3", TranslationKey("option.3")),
            ),
        )

    @pytest.fixture
    def mock_radio_field(self) -> FieldDefinition:
        """Create mock RADIO field with existing options."""
        return FieldDefinition(
            id=FieldDefinitionId("field_radio"),
            field_type=FieldType.RADIO,
            label_key=TranslationKey("field.radio.label"),
            required=True,
            options=(
                ("yes", TranslationKey("option.yes")),
                ("no", TranslationKey("option.no")),
                ("maybe", TranslationKey("option.maybe")),
            ),
        )

    @pytest.fixture
    def mock_text_field(self) -> FieldDefinition:
        """Create mock TEXT field (not a choice field)."""
        return FieldDefinition(
            id=FieldDefinitionId("field_text"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text.label"),
            required=False,
        )

    @pytest.fixture
    def mock_entity_with_dropdown_field(
        self, mock_dropdown_field: FieldDefinition
    ) -> EntityDefinition:
        """Create mock entity containing DROPDOWN field."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={mock_dropdown_field.id: mock_dropdown_field},
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def mock_entity_with_radio_field(
        self, mock_radio_field: FieldDefinition
    ) -> EntityDefinition:
        """Create mock entity containing RADIO field."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={mock_radio_field.id: mock_radio_field},
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def mock_entity_with_text_field(
        self, mock_text_field: FieldDefinition
    ) -> EntityDefinition:
        """Create mock entity containing TEXT field."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={mock_text_field.id: mock_text_field},
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def command(self, mock_repository: Mock) -> DeleteFieldOptionCommand:
        """Create command with mock repository."""
        return DeleteFieldOptionCommand(mock_repository)

    # =========================================================================
    # SUCCESS Cases
    # =========================================================================

    def test_delete_option_from_dropdown_field_success(
        self,
        command: DeleteFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should successfully delete option from DROPDOWN field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option2",
        )

        # Assert
        assert result.is_success()
        assert result.value == FieldDefinitionId("field_dropdown")

        # Verify repository calls
        mock_repository.exists.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.get_by_id.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.save.assert_called_once()

        # Verify option was deleted
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_dropdown")]
        assert len(updated_field.options) == 2
        option_values = [opt[0] for opt in updated_field.options]
        assert "option2" not in option_values
        assert "option1" in option_values
        assert "option3" in option_values

    def test_delete_option_from_radio_field_success(
        self,
        command: DeleteFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_radio_field: EntityDefinition,
    ) -> None:
        """Should successfully delete option from RADIO field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_radio_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_radio",
            option_value="maybe",
        )

        # Assert
        assert result.is_success()

        # Verify option was deleted
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_radio")]
        assert len(updated_field.options) == 2
        option_values = [opt[0] for opt in updated_field.options]
        assert "maybe" not in option_values
        assert "yes" in option_values
        assert "no" in option_values

    def test_delete_first_option_preserves_order(
        self,
        command: DeleteFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should preserve order when deleting first option."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option1",
        )

        # Assert
        assert result.is_success()

        # Verify remaining options preserve original order
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_dropdown")]
        assert updated_field.options[0][0] == "option2"
        assert updated_field.options[1][0] == "option3"

    def test_delete_last_option_preserves_order(
        self,
        command: DeleteFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should preserve order when deleting last option."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option3",
        )

        # Assert
        assert result.is_success()

        # Verify remaining options preserve original order
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_dropdown")]
        assert updated_field.options[0][0] == "option1"
        assert updated_field.options[1][0] == "option2"

    def test_delete_multiple_options_sequentially(
        self,
        command: DeleteFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should successfully delete multiple options sequentially."""
        # Setup: First delete
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute: Delete first option
        result1 = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option1",
        )

        # Assert first
        assert result1.is_success()

        # Update mock to return entity with 2 options for second delete
        saved_entity_after_first = mock_repository.save.call_args[0][0]
        mock_repository.get_by_id.return_value = Success(saved_entity_after_first)

        # Execute: Delete second option
        result2 = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option2",
        )

        # Assert second
        assert result2.is_success()

        # Verify final state has 1 option
        final_entity = mock_repository.save.call_args[0][0]
        final_field = final_entity.fields[FieldDefinitionId("field_dropdown")]
        assert len(final_field.options) == 1
        assert final_field.options[0][0] == "option3"

    # =========================================================================
    # FAILURE Cases
    # =========================================================================

    def test_reject_empty_entity_id(
        self, command: DeleteFieldOptionCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty entity_id."""
        result = command.execute(
            entity_id="",
            field_id="field_dropdown",
            option_value="option1",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_empty_field_id(
        self, command: DeleteFieldOptionCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty field_id."""
        result = command.execute(
            entity_id="test_entity",
            field_id="",
            option_value="option1",
        )

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_empty_option_value(
        self, command: DeleteFieldOptionCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty option_value."""
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="",
        )

        assert result.is_failure()
        assert "option_value is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_parent_entity_does_not_exist(
        self, command: DeleteFieldOptionCommand, mock_repository: Mock
    ) -> None:
        """Should reject when parent entity does not exist."""
        # Setup
        mock_repository.exists.return_value = False

        # Execute
        result = command.execute(
            entity_id="nonexistent_entity",
            field_id="field_dropdown",
            option_value="option1",
        )

        # Assert
        assert result.is_failure()
        assert "does not exist" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_field_does_not_exist(
        self,
        command: DeleteFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should reject when field does not exist in entity."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        # Execute (field_nonexistent doesn't exist)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_nonexistent",
            option_value="option1",
        )

        # Assert
        assert result.is_failure()
        assert "not found" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_non_choice_field(
        self,
        command: DeleteFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should reject deleting option from non-choice field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        # Execute (try to delete option from TEXT field)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            option_value="option1",
        )

        # Assert
        assert result.is_failure()
        assert "cannot delete option" in result.error.lower()
        assert "choice fields" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_option_does_not_exist(
        self,
        command: DeleteFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should reject deleting non-existent option."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        # Execute (option99 doesn't exist)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option99",
        )

        # Assert
        assert result.is_failure()
        assert "not found" in result.error.lower()
        assert "cannot delete non-existent option" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_repository_save_failure_propagated(
        self,
        command: DeleteFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should propagate repository save failure."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Failure("Database error: constraint violation")

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option1",
        )

        # Assert
        assert result.is_failure()
        assert "failed to save" in result.error.lower()

    def test_whitespace_option_value_trimmed(
        self,
        command: DeleteFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should trim whitespace from option_value."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute with whitespace
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="  option2  ",  # with whitespace
        )

        # Assert - should succeed after trimming
        assert result.is_success()

        # Verify option2 was deleted
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_dropdown")]
        option_values = [opt[0] for opt in updated_field.options]
        assert "option2" not in option_values

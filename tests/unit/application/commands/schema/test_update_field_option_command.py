"""Unit tests for UpdateFieldOptionCommand (Phase 2 Step 3)."""

from unittest.mock import Mock
import pytest

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.application.commands.schema.update_field_option_command import UpdateFieldOptionCommand


class TestUpdateFieldOptionCommand:
    """Unit tests for UpdateFieldOptionCommand."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_dropdown_field(self) -> FieldDefinition:
        """Create mock DROPDOWN field with options."""
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
        """Create mock RADIO field with options."""
        return FieldDefinition(
            id=FieldDefinitionId("field_radio"),
            field_type=FieldType.RADIO,
            label_key=TranslationKey("field.radio.label"),
            required=True,
            options=(
                ("yes", TranslationKey("option.yes")),
                ("no", TranslationKey("option.no")),
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
    def mock_entity_with_radio_field(self, mock_radio_field: FieldDefinition) -> EntityDefinition:
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
    def mock_entity_with_text_field(self, mock_text_field: FieldDefinition) -> EntityDefinition:
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
    def command(self, mock_repository: Mock) -> UpdateFieldOptionCommand:
        """Create command with mock repository."""
        return UpdateFieldOptionCommand(mock_repository)

    # =========================================================================
    # SUCCESS Cases
    # =========================================================================

    def test_update_option_in_dropdown_field_success(
        self,
        command: UpdateFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should successfully update option label_key in DROPDOWN field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option2",
            new_label_key="option.2.renamed",
        )

        # Assert
        assert result.is_success()
        assert result.value == FieldDefinitionId("field_dropdown")

        # Verify repository calls
        mock_repository.exists.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.get_by_id.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.save.assert_called_once()

        # Verify option was updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_dropdown")]

        # Check that option2's label was updated
        assert len(updated_field.options) == 3
        assert ("option2", TranslationKey("option.2.renamed")) in updated_field.options

        # Check that other options remain unchanged
        assert ("option1", TranslationKey("option.1")) in updated_field.options
        assert ("option3", TranslationKey("option.3")) in updated_field.options

    def test_update_option_in_radio_field_success(
        self,
        command: UpdateFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_radio_field: EntityDefinition,
    ) -> None:
        """Should successfully update option label_key in RADIO field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_radio_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_radio",
            option_value="yes",
            new_label_key="option.yes.renamed",
        )

        # Assert
        assert result.is_success()

        # Verify option was updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_radio")]

        assert len(updated_field.options) == 2
        assert ("yes", TranslationKey("option.yes.renamed")) in updated_field.options
        assert ("no", TranslationKey("option.no")) in updated_field.options

    def test_update_first_option(
        self,
        command: UpdateFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should successfully update first option in list."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option1",
            new_label_key="option.1.new",
        )

        # Assert
        assert result.is_success()

        # Verify option was updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_dropdown")]
        assert ("option1", TranslationKey("option.1.new")) in updated_field.options

    def test_update_last_option(
        self,
        command: UpdateFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should successfully update last option in list."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option3",
            new_label_key="option.3.new",
        )

        # Assert
        assert result.is_success()

        # Verify option was updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_dropdown")]
        assert ("option3", TranslationKey("option.3.new")) in updated_field.options

    # =========================================================================
    # FAILURE Cases
    # =========================================================================

    def test_reject_empty_entity_id(
        self, command: UpdateFieldOptionCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty entity_id."""
        result = command.execute(
            entity_id="",
            field_id="field_dropdown",
            option_value="option1",
            new_label_key="option.1.new",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_empty_field_id(
        self, command: UpdateFieldOptionCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty field_id."""
        result = command.execute(
            entity_id="test_entity",
            field_id="",
            option_value="option1",
            new_label_key="option.1.new",
        )

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_empty_option_value(
        self, command: UpdateFieldOptionCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty option_value."""
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="",
            new_label_key="option.new",
        )

        assert result.is_failure()
        assert "option_value is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_empty_new_label_key(
        self, command: UpdateFieldOptionCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty new_label_key."""
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option1",
            new_label_key="",
        )

        assert result.is_failure()
        assert "new_label_key is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_parent_entity_does_not_exist(
        self, command: UpdateFieldOptionCommand, mock_repository: Mock
    ) -> None:
        """Should reject when parent entity does not exist."""
        # Setup
        mock_repository.exists.return_value = False

        # Execute
        result = command.execute(
            entity_id="nonexistent_entity",
            field_id="field_dropdown",
            option_value="option1",
            new_label_key="option.1.new",
        )

        # Assert
        assert result.is_failure()
        assert "does not exist" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_field_does_not_exist(
        self,
        command: UpdateFieldOptionCommand,
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
            new_label_key="option.1.new",
        )

        # Assert
        assert result.is_failure()
        assert "not found" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_non_choice_field(
        self,
        command: UpdateFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should reject updating option in non-choice field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        # Execute (try to update option in TEXT field)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            option_value="option1",
            new_label_key="option.1.new",
        )

        # Assert
        assert result.is_failure()
        assert "cannot update option" in result.error.lower()
        assert "choice fields" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_nonexistent_option_value(
        self,
        command: UpdateFieldOptionCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should reject updating non-existent option."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        # Execute (option_nonexistent doesn't exist)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            option_value="option_nonexistent",
            new_label_key="option.new",
        )

        # Assert
        assert result.is_failure()
        assert "not found" in result.error.lower()
        assert "cannot update non-existent" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_repository_save_failure_propagated(
        self,
        command: UpdateFieldOptionCommand,
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
            new_label_key="option.1.new",
        )

        # Assert
        assert result.is_failure()
        assert "failed to save" in result.error.lower()

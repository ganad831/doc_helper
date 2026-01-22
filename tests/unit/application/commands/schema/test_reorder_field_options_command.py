"""Unit tests for ReorderFieldOptionsCommand (Phase 2 Step 3)."""

from unittest.mock import Mock
import pytest

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.application.commands.schema.reorder_field_options_command import ReorderFieldOptionsCommand


class TestReorderFieldOptionsCommand:
    """Unit tests for ReorderFieldOptionsCommand."""

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
    def command(self, mock_repository: Mock) -> ReorderFieldOptionsCommand:
        """Create command with mock repository."""
        return ReorderFieldOptionsCommand(mock_repository)

    # =========================================================================
    # SUCCESS Cases
    # =========================================================================

    def test_reorder_options_in_dropdown_field_success(
        self,
        command: ReorderFieldOptionsCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should successfully reorder options in DROPDOWN field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute - reverse order
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            new_option_order=["option3", "option2", "option1"],
        )

        # Assert
        assert result.is_success()
        assert result.value == FieldDefinitionId("field_dropdown")

        # Verify repository calls
        mock_repository.exists.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.get_by_id.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.save.assert_called_once()

        # Verify options were reordered
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_dropdown")]

        # Check new order
        assert len(updated_field.options) == 3
        assert updated_field.options[0] == ("option3", TranslationKey("option.3"))
        assert updated_field.options[1] == ("option2", TranslationKey("option.2"))
        assert updated_field.options[2] == ("option1", TranslationKey("option.1"))

    def test_reorder_options_in_radio_field_success(
        self,
        command: ReorderFieldOptionsCommand,
        mock_repository: Mock,
        mock_entity_with_radio_field: EntityDefinition,
    ) -> None:
        """Should successfully reorder options in RADIO field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_radio_field)
        mock_repository.save.return_value = Success(None)

        # Execute - different order
        result = command.execute(
            entity_id="test_entity",
            field_id="field_radio",
            new_option_order=["no", "maybe", "yes"],
        )

        # Assert
        assert result.is_success()

        # Verify options were reordered
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_radio")]

        assert len(updated_field.options) == 3
        assert updated_field.options[0] == ("no", TranslationKey("option.no"))
        assert updated_field.options[1] == ("maybe", TranslationKey("option.maybe"))
        assert updated_field.options[2] == ("yes", TranslationKey("option.yes"))

    def test_reorder_with_same_order_success(
        self,
        command: ReorderFieldOptionsCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should successfully handle reorder with same order (no change)."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute - same order as existing
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            new_option_order=["option1", "option2", "option3"],
        )

        # Assert
        assert result.is_success()

        # Verify options remain in same order
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_dropdown")]

        assert len(updated_field.options) == 3
        assert updated_field.options[0] == ("option1", TranslationKey("option.1"))
        assert updated_field.options[1] == ("option2", TranslationKey("option.2"))
        assert updated_field.options[2] == ("option3", TranslationKey("option.3"))

    def test_reorder_partial_swap(
        self,
        command: ReorderFieldOptionsCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should successfully swap two options while keeping third in place."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_repository.save.return_value = Success(None)

        # Execute - swap first and second, keep third
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            new_option_order=["option2", "option1", "option3"],
        )

        # Assert
        assert result.is_success()

        # Verify options were reordered correctly
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_dropdown")]

        assert updated_field.options[0] == ("option2", TranslationKey("option.2"))
        assert updated_field.options[1] == ("option1", TranslationKey("option.1"))
        assert updated_field.options[2] == ("option3", TranslationKey("option.3"))

    # =========================================================================
    # FAILURE Cases
    # =========================================================================

    def test_reject_empty_entity_id(
        self, command: ReorderFieldOptionsCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty entity_id."""
        result = command.execute(
            entity_id="",
            field_id="field_dropdown",
            new_option_order=["option1", "option2"],
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_empty_field_id(
        self, command: ReorderFieldOptionsCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty field_id."""
        result = command.execute(
            entity_id="test_entity",
            field_id="",
            new_option_order=["option1", "option2"],
        )

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_empty_new_option_order(
        self, command: ReorderFieldOptionsCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty new_option_order."""
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            new_option_order=[],
        )

        assert result.is_failure()
        assert "new_option_order is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_parent_entity_does_not_exist(
        self, command: ReorderFieldOptionsCommand, mock_repository: Mock
    ) -> None:
        """Should reject when parent entity does not exist."""
        # Setup
        mock_repository.exists.return_value = False

        # Execute
        result = command.execute(
            entity_id="nonexistent_entity",
            field_id="field_dropdown",
            new_option_order=["option1", "option2"],
        )

        # Assert
        assert result.is_failure()
        assert "does not exist" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_field_does_not_exist(
        self,
        command: ReorderFieldOptionsCommand,
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
            new_option_order=["option1", "option2"],
        )

        # Assert
        assert result.is_failure()
        assert "not found" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_non_choice_field(
        self,
        command: ReorderFieldOptionsCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should reject reordering options in non-choice field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        # Execute (try to reorder options in TEXT field)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            new_option_order=["option1", "option2"],
        )

        # Assert
        assert result.is_failure()
        assert "cannot reorder options" in result.error.lower()
        assert "choice fields" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_duplicate_values_in_new_order(
        self,
        command: ReorderFieldOptionsCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should reject new order with duplicate values."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        # Execute (option1 appears twice)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            new_option_order=["option1", "option2", "option1"],
        )

        # Assert
        assert result.is_failure()
        assert "duplicate" in result.error.lower()
        assert "exactly once" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_missing_option_in_new_order(
        self,
        command: ReorderFieldOptionsCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should reject new order missing existing options."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        # Execute (missing option3)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            new_option_order=["option1", "option2"],
        )

        # Assert
        assert result.is_failure()
        assert "missing" in result.error.lower()
        assert "option3" in result.error

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_extra_option_in_new_order(
        self,
        command: ReorderFieldOptionsCommand,
        mock_repository: Mock,
        mock_entity_with_dropdown_field: EntityDefinition,
    ) -> None:
        """Should reject new order with extra options not in existing."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        # Execute (option4 doesn't exist)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_dropdown",
            new_option_order=["option1", "option2", "option3", "option4"],
        )

        # Assert
        assert result.is_failure()
        assert "unknown" in result.error.lower()
        assert "option4" in result.error

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_repository_save_failure_propagated(
        self,
        command: ReorderFieldOptionsCommand,
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
            new_option_order=["option3", "option2", "option1"],
        )

        # Assert
        assert result.is_failure()
        assert "failed to save" in result.error.lower()

"""Unit tests for UpdateFieldCommand (Phase 2 Step 3)."""

from unittest.mock import Mock
import pytest

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.application.commands.schema.update_field_command import UpdateFieldCommand


class TestUpdateFieldCommand:
    """Unit tests for UpdateFieldCommand."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_text_field(self) -> FieldDefinition:
        """Create mock TEXT field for testing."""
        return FieldDefinition(
            id=FieldDefinitionId("field_text"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text.label"),
            help_text_key=TranslationKey("field.text.help"),
            required=True,
            default_value="default_text",
            formula=None,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
            constraints=(),
            options=(),
            control_rules=(),
        )

    @pytest.fixture
    def mock_calculated_field(self) -> FieldDefinition:
        """Create mock CALCULATED field for testing."""
        return FieldDefinition(
            id=FieldDefinitionId("field_calculated"),
            field_type=FieldType.CALCULATED,
            label_key=TranslationKey("field.calculated.label"),
            help_text_key=None,
            required=False,
            default_value=None,
            formula="{{field1}} + {{field2}}",
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
            constraints=(),
            options=(),
            control_rules=(),
        )

    @pytest.fixture
    def mock_lookup_field(self) -> FieldDefinition:
        """Create mock LOOKUP field for testing."""
        return FieldDefinition(
            id=FieldDefinitionId("field_lookup"),
            field_type=FieldType.LOOKUP,
            label_key=TranslationKey("field.lookup.label"),
            help_text_key=None,
            required=False,
            default_value=None,
            formula=None,
            lookup_entity_id="other_entity",
            lookup_display_field="name",
            child_entity_id=None,
            constraints=(),
            options=(),
            control_rules=(),
        )

    @pytest.fixture
    def mock_table_field(self) -> FieldDefinition:
        """Create mock TABLE field for testing."""
        return FieldDefinition(
            id=FieldDefinitionId("field_table"),
            field_type=FieldType.TABLE,
            label_key=TranslationKey("field.table.label"),
            help_text_key=None,
            required=False,
            default_value=None,
            formula=None,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id="child_entity",
            constraints=(),
            options=(),
            control_rules=(),
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
    def mock_entity_with_calculated_field(
        self, mock_calculated_field: FieldDefinition
    ) -> EntityDefinition:
        """Create mock entity containing CALCULATED field."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={mock_calculated_field.id: mock_calculated_field},
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def mock_entity_with_lookup_field(
        self, mock_lookup_field: FieldDefinition
    ) -> EntityDefinition:
        """Create mock entity containing LOOKUP field."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={mock_lookup_field.id: mock_lookup_field},
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def mock_entity_with_table_field(
        self, mock_table_field: FieldDefinition
    ) -> EntityDefinition:
        """Create mock entity containing TABLE field."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={mock_table_field.id: mock_table_field},
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def command(self, mock_repository: Mock) -> UpdateFieldCommand:
        """Create command with mock repository."""
        return UpdateFieldCommand(mock_repository)

    # =========================================================================
    # SUCCESS Cases
    # =========================================================================

    def test_update_label_key_success(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should successfully update field label_key."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity", field_id="field_text", label_key="field.text.label.updated"
        )

        # Assert
        assert result.is_success()
        assert result.value == FieldDefinitionId("field_text")

        # Verify repository calls
        mock_repository.exists.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.get_by_id.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.save.assert_called_once()

        # Verify field was updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]
        assert updated_field.label_key == TranslationKey("field.text.label.updated")

    def test_update_help_text_key_success(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should successfully update field help_text_key."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            help_text_key="field.text.help.updated",
        )

        # Assert
        assert result.is_success()

        # Verify field was updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]
        assert updated_field.help_text_key == TranslationKey("field.text.help.updated")

    def test_clear_help_text_key_success(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should successfully clear help_text_key by setting to empty string."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity", field_id="field_text", help_text_key=""
        )

        # Assert
        assert result.is_success()

        # Verify field help_text was cleared
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]
        assert updated_field.help_text_key is None

    def test_update_required_flag_success(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should successfully update required flag."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Success(None)

        # Execute (change from True to False)
        result = command.execute(entity_id="test_entity", field_id="field_text", required=False)

        # Assert
        assert result.is_success()

        # Verify field required was updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]
        assert updated_field.required is False

    def test_update_default_value_success(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should successfully update default_value."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity", field_id="field_text", default_value="new_default"
        )

        # Assert
        assert result.is_success()

        # Verify field default_value was updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]
        assert updated_field.default_value == "new_default"

    def test_clear_default_value_success(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should successfully clear default_value by setting to empty string."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(entity_id="test_entity", field_id="field_text", default_value="")

        # Assert
        assert result.is_success()

        # Verify field default_value was cleared
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]
        assert updated_field.default_value is None

    def test_update_formula_on_calculated_field_success(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_calculated_field: EntityDefinition,
    ) -> None:
        """Should successfully update formula on CALCULATED field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_calculated_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_calculated",
            formula="{{field1}} * {{field2}}",
        )

        # Assert
        assert result.is_success()

        # Verify formula was updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_calculated")]
        assert updated_field.formula == "{{field1}} * {{field2}}"

    def test_update_lookup_properties_on_lookup_field_success(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_lookup_field: EntityDefinition,
    ) -> None:
        """Should successfully update lookup properties on LOOKUP field."""
        # Setup
        mock_repository.exists.side_effect = lambda eid: True  # All entities exist
        mock_repository.get_by_id.return_value = Success(mock_entity_with_lookup_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_lookup",
            lookup_entity_id="new_lookup_entity",
            lookup_display_field="new_field",
        )

        # Assert
        assert result.is_success()

        # Verify lookup properties were updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_lookup")]
        assert updated_field.lookup_entity_id == "new_lookup_entity"
        assert updated_field.lookup_display_field == "new_field"

    def test_update_child_entity_on_table_field_success(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_table_field: EntityDefinition,
    ) -> None:
        """Should successfully update child_entity_id on TABLE field."""
        # Setup
        mock_repository.exists.side_effect = lambda eid: True  # All entities exist
        mock_repository.get_by_id.return_value = Success(mock_entity_with_table_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_table",
            child_entity_id="new_child_entity",
        )

        # Assert
        assert result.is_success()

        # Verify child_entity_id was updated
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_table")]
        assert updated_field.child_entity_id == "new_child_entity"

    # =========================================================================
    # FAILURE Cases
    # =========================================================================

    def test_reject_empty_entity_id(
        self, command: UpdateFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty entity_id."""
        result = command.execute(entity_id="", field_id="field_text", label_key="new.label")

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_empty_field_id(
        self, command: UpdateFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty field_id."""
        result = command.execute(entity_id="test_entity", field_id="", label_key="new.label")

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_parent_entity_does_not_exist(
        self, command: UpdateFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject update when parent entity does not exist."""
        # Setup
        mock_repository.exists.return_value = False

        # Execute
        result = command.execute(
            entity_id="nonexistent_entity", field_id="field_text", label_key="new.label"
        )

        # Assert
        assert result.is_failure()
        assert "does not exist" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_field_does_not_exist(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should reject update when field does not exist in entity."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        # Execute (field_nonexistent doesn't exist)
        result = command.execute(
            entity_id="test_entity", field_id="field_nonexistent", label_key="new.label"
        )

        # Assert
        assert result.is_failure()
        assert "not found" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_empty_label_key(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should reject empty label_key."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        # Execute
        result = command.execute(entity_id="test_entity", field_id="field_text", label_key="")

        # Assert
        assert result.is_failure()
        assert "label_key cannot be empty" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_formula_on_non_calculated_field(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should reject setting formula on non-CALCULATED field (Decision 6)."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        # Execute (try to set formula on TEXT field)
        result = command.execute(
            entity_id="test_entity", field_id="field_text", formula="{{field1}} + {{field2}}"
        )

        # Assert
        assert result.is_failure()
        assert "cannot set formula" in result.error.lower()
        assert "only valid for calculated" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_lookup_properties_on_non_lookup_field(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should reject setting lookup properties on non-LOOKUP field (Decision 6)."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        # Execute (try to set lookup properties on TEXT field)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            lookup_entity_id="other_entity",
        )

        # Assert
        assert result.is_failure()
        assert "cannot set lookup properties" in result.error.lower()
        assert "only valid for lookup" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_child_entity_on_non_table_field(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should reject setting child_entity_id on non-TABLE field (Decision 6)."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        # Execute (try to set child_entity_id on TEXT field)
        result = command.execute(
            entity_id="test_entity", field_id="field_text", child_entity_id="child_entity"
        )

        # Assert
        assert result.is_failure()
        assert "cannot set child_entity_id" in result.error.lower()
        assert "only valid for table" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_nonexistent_lookup_entity(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_lookup_field: EntityDefinition,
    ) -> None:
        """Should reject lookup_entity_id that does not exist."""
        # Setup
        mock_repository.exists.side_effect = lambda eid: eid.value == "test_entity"
        mock_repository.get_by_id.return_value = Success(mock_entity_with_lookup_field)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_lookup",
            lookup_entity_id="nonexistent_lookup",
        )

        # Assert
        assert result.is_failure()
        assert "lookup entity" in result.error.lower()
        assert "does not exist" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_nonexistent_child_entity(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_table_field: EntityDefinition,
    ) -> None:
        """Should reject child_entity_id that does not exist."""
        # Setup
        mock_repository.exists.side_effect = lambda eid: eid.value == "test_entity"
        mock_repository.get_by_id.return_value = Success(mock_entity_with_table_field)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_table",
            child_entity_id="nonexistent_child",
        )

        # Assert
        assert result.is_failure()
        assert "child entity" in result.error.lower()
        assert "does not exist" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_repository_save_failure_propagated(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should propagate repository save failure."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Failure("Database error: constraint violation")

        # Execute
        result = command.execute(
            entity_id="test_entity", field_id="field_text", label_key="new.label"
        )

        # Assert
        assert result.is_failure()
        assert "failed to save" in result.error.lower()

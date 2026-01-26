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
        # Create lookup entity with 'new_field' for validation
        new_lookup_entity = EntityDefinition(
            id=EntityDefinitionId("new_lookup_entity"),
            name_key=TranslationKey("entity.new_lookup"),
            description_key=None,
            fields={
                FieldDefinitionId("new_field"): FieldDefinition(
                    id=FieldDefinitionId("new_field"),
                    field_type=FieldType.TEXT,
                    label_key=TranslationKey("field.new_field"),
                    help_text_key=None,
                    required=False,
                    default_value=None,
                ),
            },
            is_root_entity=False,
            parent_entity_id=None,
        )

        # Setup mock to return appropriate entity based on ID
        def get_by_id_side_effect(entity_id: EntityDefinitionId):
            if entity_id.value == "new_lookup_entity":
                return Success(new_lookup_entity)
            return Success(mock_entity_with_lookup_field)

        mock_repository.exists.side_effect = lambda eid: True  # All entities exist
        mock_repository.get_by_id.side_effect = get_by_id_side_effect
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
    # RequiredConstraint Synchronization Tests (BUG FIX #4)
    # =========================================================================

    def test_update_required_false_removes_required_constraint(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
    ) -> None:
        """Should remove RequiredConstraint when required=False.

        BUG FIX #4: When editing a field and unchecking "Required", the
        RequiredConstraint must be removed from field.constraints.
        """
        from doc_helper.domain.validation.constraints import RequiredConstraint

        # Setup: Field with required=True and RequiredConstraint
        field_with_constraint = FieldDefinition(
            id=FieldDefinitionId("field_text"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text.label"),
            help_text_key=None,
            required=True,
            default_value=None,
            formula=None,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
            constraints=(RequiredConstraint(),),
            options=(),
            control_rules=(),
        )
        entity_with_required_field = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            fields={FieldDefinitionId("field_text"): field_with_constraint},
        )

        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(entity_with_required_field)
        mock_repository.save.return_value = Success(None)

        # Execute: Set required=False
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            required=False,
        )

        # Assert
        assert result.is_success()

        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]

        # CRITICAL: required flag AND constraints must be synchronized
        assert updated_field.required is False
        assert len(updated_field.constraints) == 0
        assert not any(isinstance(c, RequiredConstraint) for c in updated_field.constraints)

    def test_update_required_true_adds_required_constraint(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
    ) -> None:
        """Should add RequiredConstraint when required=True.

        When editing a field and checking "Required", the RequiredConstraint
        must be added to field.constraints if not already present.
        """
        from doc_helper.domain.validation.constraints import RequiredConstraint

        # Setup: Field with required=False and no constraints
        optional_field = FieldDefinition(
            id=FieldDefinitionId("field_text"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text.label"),
            help_text_key=None,
            required=False,
            default_value=None,
            formula=None,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
            constraints=(),
            options=(),
            control_rules=(),
        )
        entity_with_optional_field = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            fields={FieldDefinitionId("field_text"): optional_field},
        )

        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(entity_with_optional_field)
        mock_repository.save.return_value = Success(None)

        # Execute: Set required=True
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            required=True,
        )

        # Assert
        assert result.is_success()

        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]

        # CRITICAL: required flag AND constraints must be synchronized
        assert updated_field.required is True
        assert len(updated_field.constraints) == 1
        assert isinstance(updated_field.constraints[0], RequiredConstraint)

    def test_update_required_preserves_other_constraints(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
    ) -> None:
        """Should preserve other constraints when changing required flag.

        When toggling the required flag, any other constraints (like MinLength,
        MaxLength, Pattern) must be preserved.
        """
        from doc_helper.domain.validation.constraints import (
            RequiredConstraint,
            MinLengthConstraint,
            MaxLengthConstraint,
        )

        # Setup: Field with required=True, RequiredConstraint, and other constraints
        field_with_multiple_constraints = FieldDefinition(
            id=FieldDefinitionId("field_text"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text.label"),
            help_text_key=None,
            required=True,
            default_value=None,
            formula=None,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
            constraints=(
                RequiredConstraint(),
                MinLengthConstraint(min_length=5),
                MaxLengthConstraint(max_length=100),
            ),
            options=(),
            control_rules=(),
        )
        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            fields={FieldDefinitionId("field_text"): field_with_multiple_constraints},
        )

        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(entity)
        mock_repository.save.return_value = Success(None)

        # Execute: Set required=False (should remove RequiredConstraint only)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            required=False,
        )

        # Assert
        assert result.is_success()

        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]

        # CRITICAL: Other constraints must be preserved
        assert updated_field.required is False
        assert len(updated_field.constraints) == 2  # MinLength + MaxLength, no Required
        assert not any(isinstance(c, RequiredConstraint) for c in updated_field.constraints)
        assert any(isinstance(c, MinLengthConstraint) for c in updated_field.constraints)
        assert any(isinstance(c, MaxLengthConstraint) for c in updated_field.constraints)

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

    # ==========================================================================
    # CALCULATED FIELD INVARIANT TESTS
    # ==========================================================================

    def test_calculated_field_update_required_true_forces_false_no_constraints(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_calculated_field: EntityDefinition,
    ) -> None:
        """INVARIANT: CALCULATED fields NEVER have constraints.

        Even when updating required=True on a CALCULATED field, the result must be:
        - required=False (forced)
        - constraints=() (empty tuple)

        This prevents the backdoor where required=True would auto-create
        a RequiredConstraint for CALCULATED fields.
        """
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_calculated_field)
        mock_repository.save.return_value = Success(None)

        # Execute: Try to set required=True on CALCULATED field
        result = command.execute(
            entity_id="test_entity",
            field_id="field_calculated",
            required=True,  # This should be IGNORED for CALCULATED fields
        )

        # Assert
        assert result.is_success()

        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_calculated")]

        # INVARIANT ASSERTIONS
        assert updated_field.field_type == FieldType.CALCULATED
        assert updated_field.required is False, "CALCULATED fields must have required=False"
        assert updated_field.constraints == (), "CALCULATED fields must have no constraints"

    def test_calculated_field_strips_all_existing_constraints(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
    ) -> None:
        """INVARIANT: CALCULATED fields must have ALL constraints stripped.

        If a CALCULATED field somehow has constraints (from corrupted data),
        any update operation must strip them all.
        """
        from doc_helper.domain.validation.constraints import (
            RequiredConstraint,
            MinLengthConstraint,
        )

        # Setup: CALCULATED field with corrupted constraints (should not happen, but testing defense)
        corrupted_calc_field = FieldDefinition(
            id=FieldDefinitionId("field_calculated"),
            field_type=FieldType.CALCULATED,
            label_key=TranslationKey("field.calculated.label"),
            help_text_key=None,
            required=True,  # Corrupted: should be False
            default_value=None,
            formula="{{field1}} + {{field2}}",
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
            constraints=(RequiredConstraint(), MinLengthConstraint(min_length=5)),  # Corrupted
            options=(),
            control_rules=(),
        )
        entity_with_corrupted_field = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            fields={FieldDefinitionId("field_calculated"): corrupted_calc_field},
        )

        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(entity_with_corrupted_field)
        mock_repository.save.return_value = Success(None)

        # Execute: Any update should fix the corrupted state
        result = command.execute(
            entity_id="test_entity",
            field_id="field_calculated",
            required=True,  # Even trying to set required=True should result in False
        )

        # Assert
        assert result.is_success()

        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_calculated")]

        # INVARIANT: ALL constraints must be stripped, required must be False
        assert updated_field.required is False
        assert updated_field.constraints == ()
        assert len(updated_field.constraints) == 0

    # ==========================================================================
    # SELF-ENTITY LOOKUP INVARIANT TESTS
    # ==========================================================================

    def test_self_entity_lookup_rejected(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_lookup_field: EntityDefinition,
    ) -> None:
        """INVARIANT: LOOKUP fields cannot reference their own entity.

        A1.2-2: UpdateFieldCommand defensive safety net - prevents self-entity
        LOOKUP even if UseCases layer is bypassed.
        """
        # Setup
        mock_repository.exists.side_effect = lambda eid: True  # All entities exist
        mock_repository.get_by_id.return_value = Success(mock_entity_with_lookup_field)

        # Execute: Try to set lookup_entity_id to same entity
        result = command.execute(
            entity_id="test_entity",
            field_id="field_lookup",
            lookup_entity_id="test_entity",  # Same as entity_id - MUST FAIL
        )

        # Assert
        assert result.is_failure()
        assert "cannot reference its own entity" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    # ==========================================================================
    # FORMULA DESIGN-TIME SEMANTICS INVARIANT TEST (A3-4)
    # ==========================================================================

    def test_invalid_formula_syntax_accepted_at_design_time(
        self,
        command: UpdateFieldCommand,
        mock_repository: Mock,
        mock_entity_with_calculated_field: EntityDefinition,
    ) -> None:
        """INVARIANT: Formula is stored as OPAQUE STRING at design time.

        A3-4: Proves that syntactically invalid formula strings are accepted
        at design time with NO validation errors. The command performs:
        - NO formula parsing
        - NO formula validation (syntax or field references)
        - NO formula execution

        Formula validation and evaluation are runtime/export responsibilities.
        Schema Designer stores formulas as opaque strings.
        """
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_calculated_field)
        mock_repository.save.return_value = Success(None)

        # Execute: Set INVALID formula syntax that would fail any parser
        invalid_formula = "{{a}} + ???"  # Invalid syntax: '???' is not valid
        result = command.execute(
            entity_id="test_entity",
            field_id="field_calculated",
            formula=invalid_formula,
        )

        # Assert: Command MUST succeed (formula stored as-is, no validation)
        assert result.is_success(), (
            "INVARIANT VIOLATION: UpdateFieldCommand rejected invalid formula syntax. "
            "Formula must be stored as opaque string with NO design-time validation."
        )

        # Verify formula was stored EXACTLY as provided (opaque string)
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_calculated")]
        assert updated_field.formula == invalid_formula, (
            "INVARIANT VIOLATION: Formula was modified during storage. "
            "Must be stored as opaque string without modification."
        )

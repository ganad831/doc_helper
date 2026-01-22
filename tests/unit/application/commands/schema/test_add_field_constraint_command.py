"""Unit tests for AddFieldConstraintCommand (Phase 2 Step 3)."""

from unittest.mock import Mock
import pytest

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.validation.constraints import (
    RequiredConstraint,
    MinLengthConstraint,
    MaxLengthConstraint,
    MinValueConstraint,
    MaxValueConstraint,
)
from doc_helper.application.commands.schema.add_field_constraint_command import AddFieldConstraintCommand


class TestAddFieldConstraintCommand:
    """Unit tests for AddFieldConstraintCommand."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_text_field(self) -> FieldDefinition:
        """Create mock TEXT field without constraints."""
        return FieldDefinition(
            id=FieldDefinitionId("field_text"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text.label"),
            required=False,
            constraints=(),
        )

    @pytest.fixture
    def mock_text_field_with_constraint(self) -> FieldDefinition:
        """Create mock TEXT field with existing constraint."""
        return FieldDefinition(
            id=FieldDefinitionId("field_text"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text.label"),
            required=False,
            constraints=(RequiredConstraint(),),
        )

    @pytest.fixture
    def mock_number_field(self) -> FieldDefinition:
        """Create mock NUMBER field without constraints."""
        return FieldDefinition(
            id=FieldDefinitionId("field_number"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.number.label"),
            required=False,
            constraints=(),
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
    def mock_entity_with_text_field_with_constraint(
        self, mock_text_field_with_constraint: FieldDefinition
    ) -> EntityDefinition:
        """Create mock entity containing TEXT field with constraint."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={mock_text_field_with_constraint.id: mock_text_field_with_constraint},
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def mock_entity_with_number_field(
        self, mock_number_field: FieldDefinition
    ) -> EntityDefinition:
        """Create mock entity containing NUMBER field."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={mock_number_field.id: mock_number_field},
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def command(self, mock_repository: Mock) -> AddFieldConstraintCommand:
        """Create command with mock repository."""
        return AddFieldConstraintCommand(mock_repository)

    # =========================================================================
    # SUCCESS Cases
    # =========================================================================

    def test_add_required_constraint_to_text_field_success(
        self,
        command: AddFieldConstraintCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should successfully add RequiredConstraint to TEXT field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        constraint = RequiredConstraint()
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            constraint=constraint,
        )

        # Assert
        assert result.is_success()
        assert result.value == FieldDefinitionId("field_text")

        # Verify repository calls
        mock_repository.exists.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.get_by_id.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.save.assert_called_once()

        # Verify constraint was added
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]
        assert len(updated_field.constraints) == 1
        assert constraint in updated_field.constraints

    def test_add_min_length_constraint_to_text_field_success(
        self,
        command: AddFieldConstraintCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should successfully add MinLengthConstraint to TEXT field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        constraint = MinLengthConstraint(min_length=5)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            constraint=constraint,
        )

        # Assert
        assert result.is_success()

        # Verify constraint was added
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_text")]
        assert len(updated_field.constraints) == 1
        assert constraint in updated_field.constraints

    def test_add_max_value_constraint_to_number_field_success(
        self,
        command: AddFieldConstraintCommand,
        mock_repository: Mock,
        mock_entity_with_number_field: EntityDefinition,
    ) -> None:
        """Should successfully add MaxValueConstraint to NUMBER field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_number_field)
        mock_repository.save.return_value = Success(None)

        # Execute
        constraint = MaxValueConstraint(max_value=100.0)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_number",
            constraint=constraint,
        )

        # Assert
        assert result.is_success()

        # Verify constraint was added
        saved_entity = mock_repository.save.call_args[0][0]
        updated_field = saved_entity.fields[FieldDefinitionId("field_number")]
        assert len(updated_field.constraints) == 1
        assert constraint in updated_field.constraints

    def test_add_multiple_constraints_sequentially(
        self,
        command: AddFieldConstraintCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should successfully add multiple different constraints sequentially."""
        # Setup: First constraint
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Success(None)

        # Execute: Add first constraint
        constraint1 = RequiredConstraint()
        result1 = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            constraint=constraint1,
        )

        # Assert first
        assert result1.is_success()

        # Update mock to return entity with 1 constraint for second add
        saved_entity_after_first = mock_repository.save.call_args[0][0]
        mock_repository.get_by_id.return_value = Success(saved_entity_after_first)

        # Execute: Add second constraint (different type)
        constraint2 = MinLengthConstraint(min_length=10)
        result2 = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            constraint=constraint2,
        )

        # Assert second
        assert result2.is_success()

        # Verify final state has 2 constraints
        final_entity = mock_repository.save.call_args[0][0]
        final_field = final_entity.fields[FieldDefinitionId("field_text")]
        assert len(final_field.constraints) == 2
        assert constraint1 in final_field.constraints
        assert constraint2 in final_field.constraints

    # =========================================================================
    # FAILURE Cases
    # =========================================================================

    def test_reject_empty_entity_id(
        self, command: AddFieldConstraintCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty entity_id."""
        constraint = RequiredConstraint()
        result = command.execute(
            entity_id="",
            field_id="field_text",
            constraint=constraint,
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_empty_field_id(
        self, command: AddFieldConstraintCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty field_id."""
        constraint = RequiredConstraint()
        result = command.execute(
            entity_id="test_entity",
            field_id="",
            constraint=constraint,
        )

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_non_constraint_instance(
        self, command: AddFieldConstraintCommand, mock_repository: Mock
    ) -> None:
        """Should reject constraint that is not a FieldConstraint instance."""
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            constraint="not a constraint",  # Invalid type
        )

        assert result.is_failure()
        assert "must be a fieldconstraint instance" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_parent_entity_does_not_exist(
        self, command: AddFieldConstraintCommand, mock_repository: Mock
    ) -> None:
        """Should reject when parent entity does not exist."""
        # Setup
        mock_repository.exists.return_value = False

        # Execute
        constraint = RequiredConstraint()
        result = command.execute(
            entity_id="nonexistent_entity",
            field_id="field_text",
            constraint=constraint,
        )

        # Assert
        assert result.is_failure()
        assert "does not exist" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_field_does_not_exist(
        self,
        command: AddFieldConstraintCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should reject when field does not exist in entity."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        # Execute (field_nonexistent doesn't exist)
        constraint = RequiredConstraint()
        result = command.execute(
            entity_id="test_entity",
            field_id="field_nonexistent",
            constraint=constraint,
        )

        # Assert
        assert result.is_failure()
        assert "not found" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_duplicate_constraint(
        self,
        command: AddFieldConstraintCommand,
        mock_repository: Mock,
        mock_entity_with_text_field_with_constraint: EntityDefinition,
    ) -> None:
        """Should reject duplicate constraint (same type with same parameters)."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field_with_constraint)

        # Execute (try to add RequiredConstraint again - already exists)
        constraint = RequiredConstraint()  # Same type with same parameters
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            constraint=constraint,
        )

        # Assert
        assert result.is_failure()
        assert "already exists" in result.error.lower()
        assert "duplicate" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_allow_different_constraint_same_type(
        self,
        command: AddFieldConstraintCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should allow adding constraint of same type but different parameters."""
        # Setup: Add MinLengthConstraint(5) first
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Success(None)

        constraint1 = MinLengthConstraint(min_length=5)
        result1 = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            constraint=constraint1,
        )
        assert result1.is_success()

        # Update mock to return entity with 1 constraint
        saved_entity_after_first = mock_repository.save.call_args[0][0]
        mock_repository.get_by_id.return_value = Success(saved_entity_after_first)

        # Execute: Add MaxLengthConstraint(100) - different type, should succeed
        constraint2 = MaxLengthConstraint(max_length=100)
        result2 = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            constraint=constraint2,
        )

        # Assert
        assert result2.is_success()

        # Verify both constraints exist
        final_entity = mock_repository.save.call_args[0][0]
        final_field = final_entity.fields[FieldDefinitionId("field_text")]
        assert len(final_field.constraints) == 2

    def test_repository_save_failure_propagated(
        self,
        command: AddFieldConstraintCommand,
        mock_repository: Mock,
        mock_entity_with_text_field: EntityDefinition,
    ) -> None:
        """Should propagate repository save failure."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_text_field)
        mock_repository.save.return_value = Failure("Database error: constraint violation")

        # Execute
        constraint = RequiredConstraint()
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
            constraint=constraint,
        )

        # Assert
        assert result.is_failure()
        assert "failed to save" in result.error.lower()

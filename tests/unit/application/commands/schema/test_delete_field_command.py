"""Unit tests for DeleteFieldCommand (Phase 2 Step 3)."""

from unittest.mock import Mock
import pytest

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.application.commands.schema.delete_field_command import DeleteFieldCommand


class TestDeleteFieldCommand:
    """Unit tests for DeleteFieldCommand."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_text_field(self) -> FieldDefinition:
        """Create mock TEXT field."""
        return FieldDefinition(
            id=FieldDefinitionId("field_text"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text.label"),
            required=False,
        )

    @pytest.fixture
    def mock_number_field(self) -> FieldDefinition:
        """Create mock NUMBER field."""
        return FieldDefinition(
            id=FieldDefinitionId("field_number"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.number.label"),
            required=False,
        )

    @pytest.fixture
    def mock_entity_with_two_fields(
        self, mock_text_field: FieldDefinition, mock_number_field: FieldDefinition
    ) -> EntityDefinition:
        """Create mock entity with two fields."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={
                mock_text_field.id: mock_text_field,
                mock_number_field.id: mock_number_field,
            },
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def command(self, mock_repository: Mock) -> DeleteFieldCommand:
        """Create command with mock repository."""
        return DeleteFieldCommand(mock_repository)

    @pytest.fixture
    def empty_dependencies(self) -> dict:
        """Empty dependencies dict (no references)."""
        return {
            "referenced_by_formulas": [],
            "referenced_by_controls_source": [],
            "referenced_by_controls_target": [],
            "referenced_by_lookup_display": [],
        }

    # =========================================================================
    # SUCCESS Cases
    # =========================================================================

    def test_delete_field_with_no_dependencies_success(
        self,
        command: DeleteFieldCommand,
        mock_repository: Mock,
        mock_entity_with_two_fields: EntityDefinition,
        empty_dependencies: dict,
    ) -> None:
        """Should successfully delete field when no dependencies exist."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_two_fields)
        mock_repository.get_field_dependencies.return_value = Success(empty_dependencies)
        mock_repository.save.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
        )

        # Assert
        assert result.is_success()

        # Verify repository calls
        mock_repository.exists.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.get_by_id.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.get_field_dependencies.assert_called_once_with(
            EntityDefinitionId("test_entity"), FieldDefinitionId("field_text")
        )
        mock_repository.save.assert_called_once()

        # Verify field was removed from entity
        saved_entity = mock_repository.save.call_args[0][0]
        assert FieldDefinitionId("field_text") not in saved_entity.fields
        assert FieldDefinitionId("field_number") in saved_entity.fields  # Other field still exists

    # =========================================================================
    # FAILURE Cases
    # =========================================================================

    def test_reject_empty_entity_id(
        self, command: DeleteFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty entity_id."""
        result = command.execute(
            entity_id="",
            field_id="field_text",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_empty_field_id(
        self, command: DeleteFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty field_id."""
        result = command.execute(
            entity_id="test_entity",
            field_id="",
        )

        assert result.is_failure()
        assert "field_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_parent_entity_does_not_exist(
        self, command: DeleteFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject when parent entity does not exist."""
        # Setup
        mock_repository.exists.return_value = False

        # Execute
        result = command.execute(
            entity_id="nonexistent_entity",
            field_id="field_text",
        )

        # Assert
        assert result.is_failure()
        assert "does not exist" in result.error.lower()

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_field_does_not_exist(
        self,
        command: DeleteFieldCommand,
        mock_repository: Mock,
        mock_entity_with_two_fields: EntityDefinition,
    ) -> None:
        """Should reject when field does not exist in entity."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_two_fields)

        # Execute (field_nonexistent doesn't exist)
        result = command.execute(
            entity_id="test_entity",
            field_id="field_nonexistent",
        )

        # Assert
        assert result.is_failure()
        assert "not found" in result.error.lower()

        # Verify no dependency check or save attempted
        mock_repository.get_field_dependencies.assert_not_called()
        mock_repository.save.assert_not_called()

    def test_reject_field_with_formula_dependencies(
        self,
        command: DeleteFieldCommand,
        mock_repository: Mock,
        mock_entity_with_two_fields: EntityDefinition,
    ) -> None:
        """Should reject deletion when field is referenced by formulas."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_two_fields)
        mock_repository.get_field_dependencies.return_value = Success({
            "referenced_by_formulas": [("test_entity", "calculated_field")],
            "referenced_by_controls_source": [],
            "referenced_by_controls_target": [],
            "referenced_by_lookup_display": [],
        })

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
        )

        # Assert
        assert result.is_failure()
        assert "cannot delete" in result.error.lower()
        assert "referenced by" in result.error.lower()
        assert "formula" in result.error.lower()
        assert "test_entity.calculated_field" in result.error

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_field_with_control_source_dependencies(
        self,
        command: DeleteFieldCommand,
        mock_repository: Mock,
        mock_entity_with_two_fields: EntityDefinition,
    ) -> None:
        """Should reject deletion when field is source in control rules."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_two_fields)
        mock_repository.get_field_dependencies.return_value = Success({
            "referenced_by_formulas": [],
            "referenced_by_controls_source": [("test_entity", "target_field")],
            "referenced_by_controls_target": [],
            "referenced_by_lookup_display": [],
        })

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
        )

        # Assert
        assert result.is_failure()
        assert "cannot delete" in result.error.lower()
        assert "control rule" in result.error.lower()
        assert "as source" in result.error.lower()
        assert "test_entity.target_field" in result.error

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_field_with_control_target_dependencies(
        self,
        command: DeleteFieldCommand,
        mock_repository: Mock,
        mock_entity_with_two_fields: EntityDefinition,
    ) -> None:
        """Should reject deletion when field is target in control rules."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_two_fields)
        mock_repository.get_field_dependencies.return_value = Success({
            "referenced_by_formulas": [],
            "referenced_by_controls_source": [],
            "referenced_by_controls_target": [("test_entity", "source_field")],
            "referenced_by_lookup_display": [],
        })

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
        )

        # Assert
        assert result.is_failure()
        assert "cannot delete" in result.error.lower()
        assert "control rule" in result.error.lower()
        assert "as target" in result.error.lower()
        assert "test_entity.source_field" in result.error

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_field_with_lookup_display_dependencies(
        self,
        command: DeleteFieldCommand,
        mock_repository: Mock,
        mock_entity_with_two_fields: EntityDefinition,
    ) -> None:
        """Should reject deletion when field is used as lookup_display_field."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_two_fields)
        mock_repository.get_field_dependencies.return_value = Success({
            "referenced_by_formulas": [],
            "referenced_by_controls_source": [],
            "referenced_by_controls_target": [],
            "referenced_by_lookup_display": [("other_entity", "lookup_field")],
        })

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
        )

        # Assert
        assert result.is_failure()
        assert "cannot delete" in result.error.lower()
        assert "LOOKUP field" in result.error
        assert "display field" in result.error.lower()
        assert "other_entity.lookup_field" in result.error

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_reject_field_with_multiple_dependency_types(
        self,
        command: DeleteFieldCommand,
        mock_repository: Mock,
        mock_entity_with_two_fields: EntityDefinition,
    ) -> None:
        """Should reject deletion and list all dependency types."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_two_fields)
        mock_repository.get_field_dependencies.return_value = Success({
            "referenced_by_formulas": [("entity1", "calc_field")],
            "referenced_by_controls_source": [("entity2", "target_field")],
            "referenced_by_controls_target": [],
            "referenced_by_lookup_display": [("entity3", "lookup_field")],
        })

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
        )

        # Assert
        assert result.is_failure()
        assert "formula" in result.error.lower()
        assert "control rule" in result.error.lower()
        assert "LOOKUP field" in result.error
        assert "entity1.calc_field" in result.error
        assert "entity2.target_field" in result.error
        assert "entity3.lookup_field" in result.error

        # Verify no save attempted
        mock_repository.save.assert_not_called()

    def test_repository_save_failure_propagated(
        self,
        command: DeleteFieldCommand,
        mock_repository: Mock,
        mock_entity_with_two_fields: EntityDefinition,
        empty_dependencies: dict,
    ) -> None:
        """Should propagate repository save failure."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity_with_two_fields)
        mock_repository.get_field_dependencies.return_value = Success(empty_dependencies)
        mock_repository.save.return_value = Failure("Database error: cannot delete field")

        # Execute
        result = command.execute(
            entity_id="test_entity",
            field_id="field_text",
        )

        # Assert
        assert result.is_failure()
        assert "failed to delete" in result.error.lower()

"""Unit tests for UpdateEntityCommand (Phase 2 Step 3)."""

from unittest.mock import Mock
import pytest

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.application.commands.schema.update_entity_command import UpdateEntityCommand


class TestUpdateEntityCommand:
    """Unit tests for UpdateEntityCommand."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_entity(self) -> EntityDefinition:
        """Create mock entity for testing."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test_entity"),
            description_key=TranslationKey("entity.test_entity.description"),
            fields={},
            is_root_entity=False,
            parent_entity_id=EntityDefinitionId("parent_entity"),
        )

    @pytest.fixture
    def mock_root_entity(self) -> EntityDefinition:
        """Create mock root entity for testing."""
        return EntityDefinition(
            id=EntityDefinitionId("root_entity"),
            name_key=TranslationKey("entity.root_entity"),
            description_key=None,
            fields={},
            is_root_entity=True,
            parent_entity_id=None,
        )

    @pytest.fixture
    def command(self, mock_repository: Mock) -> UpdateEntityCommand:
        """Create command with mock repository."""
        return UpdateEntityCommand(mock_repository)

    # =========================================================================
    # SUCCESS Cases
    # =========================================================================

    def test_update_name_key_success(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should successfully update entity name_key."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity)
        mock_repository.update.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            name_key="entity.test_entity.updated"
        )

        # Assert
        assert result.is_success()
        assert result.value == EntityDefinitionId("test_entity")

        # Verify repository calls
        mock_repository.exists.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.get_by_id.assert_called_once_with(EntityDefinitionId("test_entity"))
        mock_repository.update.assert_called_once()

        # Verify entity was updated
        updated_entity = mock_repository.update.call_args[0][0]
        assert updated_entity.name_key == TranslationKey("entity.test_entity.updated")

    def test_update_description_key_success(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should successfully update entity description_key."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity)
        mock_repository.update.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            description_key="entity.test_entity.description.updated"
        )

        # Assert
        assert result.is_success()

        # Verify entity was updated
        updated_entity = mock_repository.update.call_args[0][0]
        assert updated_entity.description_key == TranslationKey("entity.test_entity.description.updated")

    def test_update_description_key_to_none(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should successfully clear description_key by setting to empty string."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity)
        mock_repository.update.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            description_key=""  # Empty string should clear description
        )

        # Assert
        assert result.is_success()

        # Verify entity description was cleared
        updated_entity = mock_repository.update.call_args[0][0]
        assert updated_entity.description_key is None

    def test_change_non_root_to_root_success(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should successfully change non-root entity to root when no other root exists."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity)
        mock_repository.get_root_entity.return_value = Failure("No root entity found")  # No existing root
        mock_repository.update.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            is_root_entity=True
        )

        # Assert
        assert result.is_success()

        # Verify entity became root and parent was cleared
        updated_entity = mock_repository.update.call_args[0][0]
        assert updated_entity.is_root_entity is True
        assert updated_entity.parent_entity_id is None

    def test_change_root_to_non_root_success(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_root_entity: EntityDefinition
    ) -> None:
        """Should successfully change root entity to non-root with valid parent."""
        # Setup
        mock_repository.exists.side_effect = lambda eid: True  # All entities exist
        mock_repository.get_by_id.return_value = Success(mock_root_entity)
        mock_repository.update.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="root_entity",
            is_root_entity=False,
            parent_entity_id="parent_entity"
        )

        # Assert
        assert result.is_success()

        # Verify entity became non-root with parent
        updated_entity = mock_repository.update.call_args[0][0]
        assert updated_entity.is_root_entity is False
        assert updated_entity.parent_entity_id == EntityDefinitionId("parent_entity")

    def test_change_parent_entity_success(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should successfully change parent_entity_id to valid parent."""
        # Setup
        mock_repository.exists.side_effect = lambda eid: True  # All entities exist
        mock_repository.get_by_id.side_effect = lambda eid: (
            Success(mock_entity) if eid.value == "test_entity"
            else Success(EntityDefinition(
                id=eid,
                name_key=TranslationKey("entity.other"),
                fields={},
                is_root_entity=False,
                parent_entity_id=None
            ))
        )
        mock_repository.update.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            parent_entity_id="new_parent"
        )

        # Assert
        assert result.is_success()

        # Verify parent changed
        updated_entity = mock_repository.update.call_args[0][0]
        assert updated_entity.parent_entity_id == EntityDefinitionId("new_parent")

    # =========================================================================
    # FAILURE Cases
    # =========================================================================

    def test_reject_empty_entity_id(
        self, command: UpdateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty entity_id."""
        result = command.execute(entity_id="", name_key="entity.updated")

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_entity_does_not_exist(
        self, command: UpdateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should reject update when entity does not exist."""
        # Setup
        mock_repository.exists.return_value = False

        # Execute
        result = command.execute(
            entity_id="nonexistent_entity",
            name_key="entity.updated"
        )

        # Assert
        assert result.is_failure()
        assert "does not exist" in result.error.lower()

        # Verify no update attempted
        mock_repository.update.assert_not_called()

    def test_reject_change_to_root_when_another_root_exists(
        self, command: UpdateEntityCommand, mock_repository: Mock,
        mock_entity: EntityDefinition, mock_root_entity: EntityDefinition
    ) -> None:
        """Should reject is_root_entity=True when another root already exists."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity)
        mock_repository.get_root_entity.return_value = Success(mock_root_entity)  # Existing root

        # Execute
        result = command.execute(
            entity_id="test_entity",
            is_root_entity=True
        )

        # Assert
        assert result.is_failure()
        assert "another root entity" in result.error.lower()
        assert "only one root entity" in result.error.lower()

        # Verify no update attempted
        mock_repository.update.assert_not_called()

    def test_reject_non_root_without_parent(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should reject non-root entity without parent_entity_id."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity)
        mock_repository.update.return_value = Success(None)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            parent_entity_id=""  # Empty parent for non-root
        )

        # Assert
        assert result.is_failure()
        assert "non-root entities must have a parent" in result.error.lower()

        # Verify no update attempted
        mock_repository.update.assert_not_called()

    def test_reject_parent_is_self(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should reject parent_entity_id equal to entity_id (self-reference)."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            parent_entity_id="test_entity"  # Self-reference
        )

        # Assert
        assert result.is_failure()
        assert "cannot be its own parent" in result.error.lower()
        assert "circular reference" in result.error.lower()

        # Verify no update attempted
        mock_repository.update.assert_not_called()

    def test_reject_circular_parent_reference(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should reject parent_entity_id that creates circular reference."""
        # Setup: test_entity -> parent_entity -> grandparent_entity
        # Trying to set: grandparent_entity.parent = test_entity (creates cycle)

        mock_repository.exists.side_effect = lambda eid: True  # All exist

        # Create entity hierarchy: test_entity -> parent -> grandparent
        test_entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            fields={},
            is_root_entity=False,
            parent_entity_id=None,  # Will set parent below
        )

        parent_entity = EntityDefinition(
            id=EntityDefinitionId("parent_entity"),
            name_key=TranslationKey("entity.parent"),
            fields={},
            is_root_entity=False,
            parent_entity_id=EntityDefinitionId("test_entity"),  # Points to test_entity
        )

        def mock_get_by_id(eid):
            if eid.value == "test_entity":
                return Success(test_entity)
            elif eid.value == "parent_entity":
                return Success(parent_entity)
            else:
                return Failure("Not found")

        mock_repository.get_by_id.side_effect = mock_get_by_id

        # Execute: Try to set test_entity.parent = parent_entity (creates cycle)
        result = command.execute(
            entity_id="test_entity",
            parent_entity_id="parent_entity"
        )

        # Assert
        assert result.is_failure()
        assert "circular reference" in result.error.lower()

        # Verify no update attempted
        mock_repository.update.assert_not_called()

    def test_reject_root_entity_with_parent(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_root_entity: EntityDefinition
    ) -> None:
        """Should reject setting parent_entity_id on root entity."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_root_entity)

        # Execute
        result = command.execute(
            entity_id="root_entity",
            parent_entity_id="parent_entity"  # Root cannot have parent
        )

        # Assert
        assert result.is_failure()
        assert "root entities cannot have a parent" in result.error.lower()

        # Verify no update attempted
        mock_repository.update.assert_not_called()

    def test_reject_empty_name_key(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should reject empty name_key."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity)

        # Execute
        result = command.execute(
            entity_id="test_entity",
            name_key=""  # Empty name_key
        )

        # Assert
        assert result.is_failure()
        assert "name_key cannot be empty" in result.error.lower()

        # Verify no update attempted
        mock_repository.update.assert_not_called()

    def test_repository_update_failure_propagated(
        self, command: UpdateEntityCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should propagate repository update failure."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_by_id.return_value = Success(mock_entity)
        mock_repository.update.return_value = Failure("Database error: constraint violation")

        # Execute
        result = command.execute(
            entity_id="test_entity",
            name_key="entity.updated"
        )

        # Assert
        assert result.is_failure()
        assert "failed to save entity" in result.error.lower()

"""Unit tests for CreateEntityCommand (Phase 2 Step 2)."""

import pytest
from unittest.mock import Mock

from doc_helper.application.commands.schema.create_entity_command import (
    CreateEntityCommand,
)
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class TestCreateEntityCommand:
    """Unit tests for CreateEntityCommand."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        repository = Mock(spec=ISchemaRepository)
        repository.exists = Mock(return_value=False)
        repository.save = Mock(return_value=Success(None))
        return repository

    @pytest.fixture
    def command(self, mock_repository: Mock) -> CreateEntityCommand:
        """Create command instance with mock repository."""
        return CreateEntityCommand(mock_repository)

    def test_create_entity_success(
        self, command: CreateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should successfully create entity when inputs are valid."""
        # Execute command
        result = command.execute(
            entity_id="test_entity",
            name_key="entity.test_entity",
            description_key="entity.test_entity.description",
            is_root_entity=False,
        )

        # Assert success
        assert result.is_success()
        assert result.value == EntityDefinitionId("test_entity")

        # Assert repository methods called correctly
        mock_repository.exists.assert_called_once_with(
            EntityDefinitionId("test_entity")
        )
        mock_repository.save.assert_called_once()

        # Check saved entity structure
        saved_entity = mock_repository.save.call_args[0][0]
        assert isinstance(saved_entity, EntityDefinition)
        assert saved_entity.id == EntityDefinitionId("test_entity")
        assert saved_entity.name_key == TranslationKey("entity.test_entity")
        assert saved_entity.description_key == TranslationKey(
            "entity.test_entity.description"
        )
        assert saved_entity.is_root_entity is False
        assert len(saved_entity.fields) == 0  # No fields yet

    def test_create_entity_without_description(
        self, command: CreateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should successfully create entity without description."""
        result = command.execute(
            entity_id="test_entity",
            name_key="entity.test_entity",
            is_root_entity=False,
        )

        assert result.is_success()
        saved_entity = mock_repository.save.call_args[0][0]
        assert saved_entity.description_key is None

    def test_create_root_entity(
        self, command: CreateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should successfully create root entity."""
        result = command.execute(
            entity_id="root_entity",
            name_key="entity.root_entity",
            is_root_entity=True,
        )

        assert result.is_success()
        saved_entity = mock_repository.save.call_args[0][0]
        assert saved_entity.is_root_entity is True
        assert saved_entity.parent_entity_id is None

    def test_create_entity_duplicate_rejection(
        self, command: CreateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should reject duplicate entity ID."""
        # Mock repository to indicate entity exists
        mock_repository.exists.return_value = True

        result = command.execute(
            entity_id="existing_entity",
            name_key="entity.existing_entity",
        )

        # Assert failure
        assert result.is_failure()
        assert "already exists" in result.error.lower()

        # Assert save not called
        mock_repository.save.assert_not_called()

    def test_create_entity_missing_entity_id(
        self, command: CreateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should reject missing entity_id."""
        result = command.execute(
            entity_id="",
            name_key="entity.test",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error

    def test_create_entity_missing_name_key(
        self, command: CreateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should reject missing name_key."""
        result = command.execute(
            entity_id="test_entity",
            name_key="",
        )

        assert result.is_failure()
        assert "name_key is required" in result.error

    def test_create_entity_root_with_parent_rejection(
        self, command: CreateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should reject root entity with parent_entity_id."""
        result = command.execute(
            entity_id="root_entity",
            name_key="entity.root_entity",
            is_root_entity=True,
            parent_entity_id="some_parent",
        )

        assert result.is_failure()
        assert "root entity cannot have a parent" in result.error.lower()

    def test_create_entity_with_parent(
        self, command: CreateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should successfully create entity with parent_entity_id."""
        result = command.execute(
            entity_id="child_entity",
            name_key="entity.child_entity",
            is_root_entity=False,
            parent_entity_id="parent_entity",
        )

        assert result.is_success()
        saved_entity = mock_repository.save.call_args[0][0]
        assert saved_entity.parent_entity_id == EntityDefinitionId("parent_entity")

    def test_create_entity_repository_save_failure(
        self, command: CreateEntityCommand, mock_repository: Mock
    ) -> None:
        """Should propagate repository save failure."""
        # Mock repository to return failure on save
        mock_repository.save.return_value = Failure("Database error: constraint violation")

        result = command.execute(
            entity_id="test_entity",
            name_key="entity.test_entity",
        )

        # Assert failure
        assert result.is_failure()
        assert "failed to save entity" in result.error.lower()
        assert "database error" in result.error.lower()

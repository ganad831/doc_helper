"""Unit tests for DeleteEntityCommand (Phase 2 Step 3)."""

from unittest.mock import Mock
import pytest

from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.application.commands.schema.delete_entity_command import DeleteEntityCommand


class TestDeleteEntityCommand:
    """Unit tests for DeleteEntityCommand."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_standalone_entity(self) -> EntityDefinition:
        """Create mock standalone entity (no dependencies)."""
        return EntityDefinition(
            id=EntityDefinitionId("standalone_entity"),
            name_key=TranslationKey("entity.standalone"),
            description_key=None,
            fields={},
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def command(self, mock_repository: Mock) -> DeleteEntityCommand:
        """Create command with mock repository."""
        return DeleteEntityCommand(mock_repository)

    @pytest.fixture
    def empty_dependencies(self) -> dict:
        """Empty dependencies dict (no references)."""
        return {
            "referenced_by_table_fields": [],
            "referenced_by_lookup_fields": [],
            "child_entities": [],
        }

    # =========================================================================
    # SUCCESS Cases
    # =========================================================================

    def test_delete_entity_with_no_dependencies_success(
        self,
        command: DeleteEntityCommand,
        mock_repository: Mock,
        empty_dependencies: dict,
    ) -> None:
        """Should successfully delete entity when no dependencies exist."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_entity_dependencies.return_value = Success(empty_dependencies)
        mock_repository.delete.return_value = Success(None)

        # Execute
        result = command.execute(entity_id="standalone_entity")

        # Assert
        assert result.is_success()

        # Verify repository calls
        mock_repository.exists.assert_called_once_with(EntityDefinitionId("standalone_entity"))
        mock_repository.get_entity_dependencies.assert_called_once_with(
            EntityDefinitionId("standalone_entity")
        )
        mock_repository.delete.assert_called_once_with(EntityDefinitionId("standalone_entity"))

    # =========================================================================
    # FAILURE Cases
    # =========================================================================

    def test_reject_empty_entity_id(
        self, command: DeleteEntityCommand, mock_repository: Mock
    ) -> None:
        """Should reject empty entity_id."""
        result = command.execute(entity_id="")

        assert result.is_failure()
        assert "entity_id is required" in result.error.lower()

        # No repository calls should be made
        mock_repository.exists.assert_not_called()

    def test_reject_entity_does_not_exist(
        self, command: DeleteEntityCommand, mock_repository: Mock
    ) -> None:
        """Should reject when entity does not exist."""
        # Setup
        mock_repository.exists.return_value = False

        # Execute
        result = command.execute(entity_id="nonexistent_entity")

        # Assert
        assert result.is_failure()
        assert "does not exist" in result.error.lower()

        # Verify no delete attempted
        mock_repository.delete.assert_not_called()

    def test_reject_entity_referenced_by_table_fields(
        self,
        command: DeleteEntityCommand,
        mock_repository: Mock,
    ) -> None:
        """Should reject deletion when entity is referenced by TABLE fields."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_entity_dependencies.return_value = Success({
            "referenced_by_table_fields": [("project", "boreholes_table")],
            "referenced_by_lookup_fields": [],
            "child_entities": [],
        })

        # Execute
        result = command.execute(entity_id="borehole")

        # Assert
        assert result.is_failure()
        assert "cannot delete" in result.error.lower()
        assert "referenced by" in result.error.lower()
        assert "TABLE field" in result.error
        assert "project.boreholes_table" in result.error

        # Verify no delete attempted
        mock_repository.delete.assert_not_called()

    def test_reject_entity_referenced_by_lookup_fields(
        self,
        command: DeleteEntityCommand,
        mock_repository: Mock,
    ) -> None:
        """Should reject deletion when entity is referenced by LOOKUP fields."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_entity_dependencies.return_value = Success({
            "referenced_by_table_fields": [],
            "referenced_by_lookup_fields": [("project", "contractor_lookup")],
            "child_entities": [],
        })

        # Execute
        result = command.execute(entity_id="contractor")

        # Assert
        assert result.is_failure()
        assert "cannot delete" in result.error.lower()
        assert "referenced by" in result.error.lower()
        assert "LOOKUP field" in result.error
        assert "project.contractor_lookup" in result.error

        # Verify no delete attempted
        mock_repository.delete.assert_not_called()

    def test_reject_entity_with_child_entities(
        self,
        command: DeleteEntityCommand,
        mock_repository: Mock,
    ) -> None:
        """Should reject deletion when entity has child entities."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_entity_dependencies.return_value = Success({
            "referenced_by_table_fields": [],
            "referenced_by_lookup_fields": [],
            "child_entities": ["borehole", "lab_test"],
        })

        # Execute
        result = command.execute(entity_id="project")

        # Assert
        assert result.is_failure()
        assert "cannot delete" in result.error.lower()
        assert "referenced by" in result.error.lower()
        assert "child" in result.error.lower()
        assert "borehole" in result.error
        assert "lab_test" in result.error

        # Verify no delete attempted
        mock_repository.delete.assert_not_called()

    def test_reject_entity_with_multiple_dependency_types(
        self,
        command: DeleteEntityCommand,
        mock_repository: Mock,
    ) -> None:
        """Should reject deletion and list all dependency types."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_entity_dependencies.return_value = Success({
            "referenced_by_table_fields": [("entity1", "table_field")],
            "referenced_by_lookup_fields": [("entity2", "lookup_field")],
            "child_entities": ["child1", "child2"],
        })

        # Execute
        result = command.execute(entity_id="complex_entity")

        # Assert
        assert result.is_failure()
        assert "TABLE field" in result.error
        assert "LOOKUP field" in result.error
        assert "child" in result.error.lower()
        assert "entity1.table_field" in result.error
        assert "entity2.lookup_field" in result.error
        assert "child1" in result.error
        assert "child2" in result.error

        # Verify no delete attempted
        mock_repository.delete.assert_not_called()

    def test_dependency_check_failure_propagated(
        self,
        command: DeleteEntityCommand,
        mock_repository: Mock,
    ) -> None:
        """Should propagate dependency check failure."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_entity_dependencies.return_value = Failure(
            "Database error: cannot query dependencies"
        )

        # Execute
        result = command.execute(entity_id="some_entity")

        # Assert
        assert result.is_failure()
        assert "failed to check dependencies" in result.error.lower()

        # Verify no delete attempted
        mock_repository.delete.assert_not_called()

    def test_repository_delete_failure_propagated(
        self,
        command: DeleteEntityCommand,
        mock_repository: Mock,
        empty_dependencies: dict,
    ) -> None:
        """Should propagate repository delete failure."""
        # Setup
        mock_repository.exists.return_value = True
        mock_repository.get_entity_dependencies.return_value = Success(empty_dependencies)
        mock_repository.delete.return_value = Failure("Database error: cannot delete entity")

        # Execute
        result = command.execute(entity_id="standalone_entity")

        # Assert
        assert result.is_failure()
        assert "failed to delete" in result.error.lower()

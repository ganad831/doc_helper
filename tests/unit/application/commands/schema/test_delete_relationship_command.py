"""Unit tests for DeleteRelationshipCommand (Phase A4.2).

Tests for relationship deletion at the command layer, verifying:
- Successful deletion
- Non-existent relationship rejection
- No cascade effects on fields or entities

INVARIANTS (enforced by tests):
- Relationships are design-time constructs
- Deletion does NOT cascade to fields
- Deletion does NOT cascade to entities
- Deletion does NOT modify other relationships
- Runtime semantics are deferred to later phases
"""

import pytest
from unittest.mock import Mock

from doc_helper.application.commands.schema.delete_relationship_command import (
    DeleteRelationshipCommand,
)
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.schema.relationship_repository import IRelationshipRepository
from doc_helper.domain.schema.schema_ids import RelationshipDefinitionId


class TestDeleteRelationshipCommand:
    """Unit tests for DeleteRelationshipCommand."""

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        repository = Mock(spec=IRelationshipRepository)
        # Default: relationship exists
        repository.exists = Mock(return_value=True)
        repository.delete = Mock(return_value=Success(None))
        return repository

    @pytest.fixture
    def command(
        self,
        mock_relationship_repository: Mock,
    ) -> DeleteRelationshipCommand:
        """Create command instance with mock repository."""
        return DeleteRelationshipCommand(
            relationship_repository=mock_relationship_repository,
        )

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_delete_relationship_success(
        self,
        command: DeleteRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should successfully delete existing relationship.

        REQUIREMENT: Successful delete.
        """
        result = command.execute(
            relationship_id="project_contains_boreholes",
        )

        # Assert success
        assert result.is_success()

        # Assert repository methods called correctly
        mock_relationship_repository.exists.assert_called_once_with(
            RelationshipDefinitionId("project_contains_boreholes")
        )
        mock_relationship_repository.delete.assert_called_once_with(
            RelationshipDefinitionId("project_contains_boreholes")
        )

    # =========================================================================
    # NON-EXISTENT RELATIONSHIP REJECTION TESTS
    # =========================================================================

    def test_nonexistent_relationship_rejected(
        self,
        command: DeleteRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject deletion of non-existent relationship.

        REQUIREMENT: Reject non-existent relationship.
        """
        mock_relationship_repository.exists.return_value = False

        result = command.execute(
            relationship_id="nonexistent",
        )

        assert result.is_failure()
        assert "does not exist" in result.error.lower()
        assert "nonexistent" in result.error

        # Assert delete not called
        mock_relationship_repository.delete.assert_not_called()

    # =========================================================================
    # NO CASCADE EFFECTS TESTS
    # =========================================================================

    def test_no_cascade_to_fields(
        self,
        command: DeleteRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Deleting relationship should not cascade to fields.

        REQUIREMENT: Verify no cascade effects.
        INVARIANT: Deletion does NOT cascade to fields.
        """
        result = command.execute(
            relationship_id="project_contains_boreholes",
        )

        assert result.is_success()

        # Assert ONLY delete was called on relationship repository
        mock_relationship_repository.delete.assert_called_once()

        # No schema repository operations should occur
        # (command only has relationship_repository)

    def test_no_cascade_to_entities(
        self,
        command: DeleteRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Deleting relationship should not cascade to entities.

        REQUIREMENT: Verify no cascade effects.
        INVARIANT: Deletion does NOT cascade to entities.
        """
        result = command.execute(
            relationship_id="project_contains_boreholes",
        )

        assert result.is_success()

        # Assert ONLY relationship operations occurred
        mock_relationship_repository.exists.assert_called_once()
        mock_relationship_repository.delete.assert_called_once()

        # No entity-modifying operations should exist on this command

    def test_no_modification_to_other_relationships(
        self,
        command: DeleteRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Deleting relationship should not modify other relationships.

        REQUIREMENT: Verify no cascade effects.
        INVARIANT: Deletion does NOT modify other relationships.
        """
        result = command.execute(
            relationship_id="project_contains_boreholes",
        )

        assert result.is_success()

        # Assert only one delete call with specific ID
        mock_relationship_repository.delete.assert_called_once_with(
            RelationshipDefinitionId("project_contains_boreholes")
        )

        # No update or save operations should occur
        if hasattr(mock_relationship_repository, 'update'):
            mock_relationship_repository.update.assert_not_called()
        if hasattr(mock_relationship_repository, 'save'):
            mock_relationship_repository.save.assert_not_called()

    # =========================================================================
    # MISSING REQUIRED FIELDS TESTS
    # =========================================================================

    def test_missing_relationship_id_rejected(
        self,
        command: DeleteRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject missing relationship_id."""
        result = command.execute(
            relationship_id="",
        )

        assert result.is_failure()
        assert "relationship_id is required" in result.error.lower()
        mock_relationship_repository.delete.assert_not_called()

    def test_invalid_relationship_id_rejected(
        self,
        command: DeleteRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject invalid relationship_id format."""
        result = command.execute(
            relationship_id="INVALID@ID",  # Invalid characters
        )

        assert result.is_failure()
        assert "invalid relationship_id" in result.error.lower()
        mock_relationship_repository.delete.assert_not_called()

    # =========================================================================
    # REPOSITORY ERROR PROPAGATION TESTS
    # =========================================================================

    def test_repository_delete_failure_propagated(
        self,
        command: DeleteRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should propagate repository delete failure."""
        mock_relationship_repository.delete.return_value = Failure(
            "Database error: foreign key constraint"
        )

        result = command.execute(
            relationship_id="project_contains_boreholes",
        )

        assert result.is_failure()
        assert "failed to delete relationship" in result.error.lower()
        assert "database error" in result.error.lower()

    # =========================================================================
    # DESIGN-TIME INVARIANT DOCUMENTATION TESTS
    # =========================================================================

    def test_design_time_only_invariant_documented(
        self,
        command: DeleteRelationshipCommand,
    ) -> None:
        """Verify design-time invariant is documented in command.

        INVARIANT: Relationships are design-time constructs.
        This test verifies the invariant is documented in the code.
        """
        # Check docstring contains invariant documentation
        docstring = DeleteRelationshipCommand.__doc__
        assert docstring is not None
        assert "design-time" in docstring.lower()
        assert "cascade" in docstring.lower()

        # Check execute method documents no-cascade behavior
        execute_docstring = DeleteRelationshipCommand.execute.__doc__
        assert execute_docstring is not None
        assert "cascade" in execute_docstring.lower()

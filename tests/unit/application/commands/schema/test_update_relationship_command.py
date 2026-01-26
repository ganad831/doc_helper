"""Unit tests for UpdateRelationshipCommand (Phase A4.2).

Tests for relationship metadata update at the command layer, verifying:
- Successful metadata update
- Non-existent relationship rejection
- Attempt to change source_entity_id rejection
- Attempt to change target_entity_id rejection
- No side effects on fields or entities

INVARIANTS (enforced by tests):
- Relationships are design-time constructs
- Editing does NOT imply runtime behavior
- Source and target entity cannot be changed
- Only metadata fields can be updated
- No cascade effects
- Runtime semantics are deferred to later phases
"""

import pytest
from unittest.mock import Mock

from doc_helper.application.commands.schema.update_relationship_command import (
    UpdateRelationshipCommand,
)
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.relationship_repository import IRelationshipRepository
from doc_helper.domain.schema.relationship_type import RelationshipType
from doc_helper.domain.schema.schema_ids import (
    EntityDefinitionId,
    RelationshipDefinitionId,
)


class TestUpdateRelationshipCommand:
    """Unit tests for UpdateRelationshipCommand."""

    @pytest.fixture
    def existing_relationship(self) -> RelationshipDefinition:
        """Create existing relationship for testing."""
        return RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.original"),
            description_key=None,
            inverse_name_key=None,
        )

    @pytest.fixture
    def mock_relationship_repository(
        self, existing_relationship: RelationshipDefinition
    ) -> Mock:
        """Create mock relationship repository."""
        repository = Mock(spec=IRelationshipRepository)
        # Default: relationship exists
        repository.exists = Mock(return_value=True)
        repository.get_by_id = Mock(return_value=Success(existing_relationship))
        repository.update = Mock(return_value=Success(None))
        return repository

    @pytest.fixture
    def command(
        self,
        mock_relationship_repository: Mock,
    ) -> UpdateRelationshipCommand:
        """Create command instance with mock repository."""
        return UpdateRelationshipCommand(
            relationship_repository=mock_relationship_repository,
        )

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_update_relationship_metadata_success(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should successfully update relationship metadata.

        REQUIREMENT: Successful update of metadata.
        """
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.updated",
            description_key="relationship.updated.desc",
            inverse_name_key="relationship.updated.inverse",
        )

        # Assert success
        assert result.is_success()

        # Assert repository methods called correctly
        mock_relationship_repository.exists.assert_called_once_with(
            RelationshipDefinitionId("project_contains_boreholes")
        )
        mock_relationship_repository.get_by_id.assert_called_once()
        mock_relationship_repository.update.assert_called_once()

        # Check updated relationship has new metadata
        updated_rel = mock_relationship_repository.update.call_args[0][0]
        assert isinstance(updated_rel, RelationshipDefinition)
        assert updated_rel.name_key == TranslationKey("relationship.updated")
        assert updated_rel.description_key == TranslationKey("relationship.updated.desc")
        assert updated_rel.inverse_name_key == TranslationKey("relationship.updated.inverse")

    def test_update_relationship_type_success(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should successfully update relationship type."""
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="REFERENCES",  # Changed from CONTAINS
            name_key="relationship.test",
        )

        assert result.is_success()

        updated_rel = mock_relationship_repository.update.call_args[0][0]
        assert updated_rel.relationship_type == RelationshipType.REFERENCES

    def test_update_clears_optional_fields(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
        existing_relationship: RelationshipDefinition,
    ) -> None:
        """Should clear optional fields when not provided."""
        # Setup: existing relationship has description
        existing_with_desc = RelationshipDefinition(
            id=existing_relationship.id,
            source_entity_id=existing_relationship.source_entity_id,
            target_entity_id=existing_relationship.target_entity_id,
            relationship_type=existing_relationship.relationship_type,
            name_key=existing_relationship.name_key,
            description_key=TranslationKey("relationship.existing.desc"),
            inverse_name_key=TranslationKey("relationship.existing.inverse"),
        )
        mock_relationship_repository.get_by_id.return_value = Success(existing_with_desc)

        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.updated",
            # No description_key or inverse_name_key
        )

        assert result.is_success()

        updated_rel = mock_relationship_repository.update.call_args[0][0]
        assert updated_rel.description_key is None
        assert updated_rel.inverse_name_key is None

    # =========================================================================
    # NON-EXISTENT RELATIONSHIP REJECTION TESTS
    # =========================================================================

    def test_nonexistent_relationship_rejected(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject update of non-existent relationship.

        REQUIREMENT: Reject non-existent relationship.
        """
        mock_relationship_repository.exists.return_value = False

        result = command.execute(
            relationship_id="nonexistent",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "does not exist" in result.error.lower()
        assert "nonexistent" in result.error

        # Assert update not called
        mock_relationship_repository.update.assert_not_called()

    # =========================================================================
    # CHANGE SOURCE/TARGET REJECTION TESTS
    # =========================================================================

    def test_change_source_entity_rejected(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject attempt to change source_entity_id.

        REQUIREMENT: Reject attempts to change source/target.
        INVARIANT: Source and target entity cannot be changed.
        """
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="different_source",  # Trying to change source
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "cannot change source_entity_id" in result.error.lower()
        assert "project" in result.error
        assert "different_source" in result.error

        # Assert update not called
        mock_relationship_repository.update.assert_not_called()

    def test_change_target_entity_rejected(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject attempt to change target_entity_id.

        REQUIREMENT: Reject attempts to change source/target.
        INVARIANT: Source and target entity cannot be changed.
        """
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="different_target",  # Trying to change target
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "cannot change target_entity_id" in result.error.lower()
        assert "borehole" in result.error
        assert "different_target" in result.error

        # Assert update not called
        mock_relationship_repository.update.assert_not_called()

    # =========================================================================
    # NO SIDE EFFECTS TESTS
    # =========================================================================

    def test_no_side_effects_on_fields_or_entities(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Updating relationship should not have side effects.

        REQUIREMENT: No side effects on fields or entities.
        INVARIANT: Editing does NOT imply runtime behavior.
        """
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.updated",
        )

        assert result.is_success()

        # Assert ONLY update was called on repository
        mock_relationship_repository.update.assert_called_once()

        # Relationship repository should not have other modification methods called
        assert not hasattr(mock_relationship_repository, 'save') or \
               not mock_relationship_repository.save.called

    # =========================================================================
    # MISSING REQUIRED FIELDS TESTS
    # =========================================================================

    def test_missing_relationship_id_rejected(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject missing relationship_id."""
        result = command.execute(
            relationship_id="",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "relationship_id is required" in result.error.lower()
        mock_relationship_repository.update.assert_not_called()

    def test_missing_source_entity_id_rejected(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject missing source_entity_id."""
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "source_entity_id is required" in result.error.lower()
        mock_relationship_repository.update.assert_not_called()

    def test_missing_target_entity_id_rejected(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject missing target_entity_id."""
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "target_entity_id is required" in result.error.lower()
        mock_relationship_repository.update.assert_not_called()

    def test_missing_relationship_type_rejected(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject missing relationship_type."""
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "relationship_type is required" in result.error.lower()
        mock_relationship_repository.update.assert_not_called()

    def test_missing_name_key_rejected(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject missing name_key."""
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="",
        )

        assert result.is_failure()
        assert "name_key is required" in result.error.lower()
        mock_relationship_repository.update.assert_not_called()

    def test_invalid_relationship_type_rejected(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject invalid relationship_type."""
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="INVALID_TYPE",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "invalid relationship_type" in result.error.lower()
        assert "INVALID_TYPE" in result.error
        mock_relationship_repository.update.assert_not_called()

    # =========================================================================
    # REPOSITORY ERROR PROPAGATION TESTS
    # =========================================================================

    def test_repository_update_failure_propagated(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should propagate repository update failure."""
        mock_relationship_repository.update.return_value = Failure(
            "Database error: constraint violation"
        )

        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "failed to update relationship" in result.error.lower()
        assert "database error" in result.error.lower()

    def test_repository_get_failure_propagated(
        self,
        command: UpdateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should propagate repository get failure."""
        mock_relationship_repository.get_by_id.return_value = Failure(
            "Database error: connection lost"
        )

        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "failed to load relationship" in result.error.lower()

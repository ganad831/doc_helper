"""Unit tests for CreateRelationshipCommand (Phase A4.1 - ADR-022).

Tests for relationship creation at the command layer, verifying:
- Successful relationship creation
- Self-relationship rejection (source == target)
- Duplicate relationship rejection (ADD-ONLY semantics)
- Missing entity rejection (source or target not found)
- No side effects on fields

Per ADR-022: Relationships are ADD-ONLY (no update/delete).
"""

import pytest
from unittest.mock import Mock

from doc_helper.application.commands.schema.create_relationship_command import (
    CreateRelationshipCommand,
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
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class TestCreateRelationshipCommand:
    """Unit tests for CreateRelationshipCommand."""

    @pytest.fixture
    def mock_schema_repository(self) -> Mock:
        """Create mock schema repository."""
        repository = Mock(spec=ISchemaRepository)
        # Default: entities exist
        repository.exists = Mock(return_value=True)
        return repository

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        repository = Mock(spec=IRelationshipRepository)
        # Default: no existing relationships
        repository.exists = Mock(return_value=False)
        repository.save = Mock(return_value=Success(None))
        return repository

    @pytest.fixture
    def command(
        self,
        mock_relationship_repository: Mock,
        mock_schema_repository: Mock,
    ) -> CreateRelationshipCommand:
        """Create command instance with mock repositories."""
        return CreateRelationshipCommand(
            relationship_repository=mock_relationship_repository,
            schema_repository=mock_schema_repository,
        )

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_create_relationship_success(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
        mock_schema_repository: Mock,
    ) -> None:
        """Should successfully create relationship when all inputs are valid.

        REQUIREMENT: Relationship can be added successfully.
        """
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.project_boreholes",
        )

        # Assert success
        assert result.is_success()
        assert result.value == RelationshipDefinitionId("project_contains_boreholes")

        # Assert repository methods called correctly
        mock_relationship_repository.exists.assert_called_once_with(
            RelationshipDefinitionId("project_contains_boreholes")
        )
        mock_schema_repository.exists.assert_any_call(EntityDefinitionId("project"))
        mock_schema_repository.exists.assert_any_call(EntityDefinitionId("borehole"))
        mock_relationship_repository.save.assert_called_once()

        # Check saved relationship structure
        saved_rel = mock_relationship_repository.save.call_args[0][0]
        assert isinstance(saved_rel, RelationshipDefinition)
        assert saved_rel.id == RelationshipDefinitionId("project_contains_boreholes")
        assert saved_rel.source_entity_id == EntityDefinitionId("project")
        assert saved_rel.target_entity_id == EntityDefinitionId("borehole")
        assert saved_rel.relationship_type == RelationshipType.CONTAINS
        assert saved_rel.name_key == TranslationKey("relationship.project_boreholes")

    def test_create_relationship_with_all_optional_fields(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should successfully create relationship with all optional fields."""
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.project_boreholes",
            description_key="relationship.project_boreholes.desc",
            inverse_name_key="relationship.borehole_project",
        )

        assert result.is_success()

        saved_rel = mock_relationship_repository.save.call_args[0][0]
        assert saved_rel.description_key == TranslationKey(
            "relationship.project_boreholes.desc"
        )
        assert saved_rel.inverse_name_key == TranslationKey(
            "relationship.borehole_project"
        )

    def test_create_relationship_references_type(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should successfully create REFERENCES relationship."""
        result = command.execute(
            relationship_id="sample_references_lab",
            source_entity_id="sample",
            target_entity_id="lab_test",
            relationship_type="REFERENCES",
            name_key="relationship.sample_lab",
        )

        assert result.is_success()
        saved_rel = mock_relationship_repository.save.call_args[0][0]
        assert saved_rel.relationship_type == RelationshipType.REFERENCES

    def test_create_relationship_associates_type(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should successfully create ASSOCIATES relationship."""
        result = command.execute(
            relationship_id="borehole_assoc_equipment",
            source_entity_id="borehole",
            target_entity_id="equipment",
            relationship_type="ASSOCIATES",
            name_key="relationship.borehole_equipment",
        )

        assert result.is_success()
        saved_rel = mock_relationship_repository.save.call_args[0][0]
        assert saved_rel.relationship_type == RelationshipType.ASSOCIATES

    # =========================================================================
    # SELF-RELATIONSHIP REJECTION TESTS
    # =========================================================================

    def test_self_relationship_rejected(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject relationship where source equals target.

        REQUIREMENT: Self-relationship is rejected.
        INVARIANT: source_entity_id != target_entity_id
        """
        result = command.execute(
            relationship_id="project_self_ref",
            source_entity_id="project",
            target_entity_id="project",  # Same as source - MUST FAIL
            relationship_type="CONTAINS",
            name_key="relationship.self",
        )

        # Assert failure
        assert result.is_failure()
        assert "source and target" in result.error.lower()
        assert "different" in result.error.lower()

        # Assert save not called
        mock_relationship_repository.save.assert_not_called()

    # =========================================================================
    # DUPLICATE RELATIONSHIP REJECTION TESTS
    # =========================================================================

    def test_duplicate_relationship_rejected(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject duplicate relationship ID.

        REQUIREMENT: Duplicate relationship is rejected.
        ADR-022: ADD-ONLY semantics - relationships cannot be updated.
        """
        # Mock repository to indicate relationship exists
        mock_relationship_repository.exists.return_value = True

        result = command.execute(
            relationship_id="existing_relationship",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.existing",
        )

        # Assert failure
        assert result.is_failure()
        assert "already exists" in result.error.lower()
        assert "ADD-ONLY" in result.error

        # Assert save not called
        mock_relationship_repository.save.assert_not_called()

    # =========================================================================
    # MISSING ENTITY REJECTION TESTS
    # =========================================================================

    def test_missing_source_entity_rejected(
        self,
        command: CreateRelationshipCommand,
        mock_schema_repository: Mock,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject relationship with non-existent source entity.

        REQUIREMENT: Missing entity is rejected.
        """
        # Mock: source entity does not exist
        def exists_side_effect(entity_id: EntityDefinitionId) -> bool:
            return entity_id.value != "nonexistent_source"

        mock_schema_repository.exists.side_effect = exists_side_effect

        result = command.execute(
            relationship_id="invalid_source_rel",
            source_entity_id="nonexistent_source",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        # Assert failure
        assert result.is_failure()
        assert "source entity" in result.error.lower()
        assert "does not exist" in result.error.lower()
        assert "nonexistent_source" in result.error

        # Assert save not called
        mock_relationship_repository.save.assert_not_called()

    def test_missing_target_entity_rejected(
        self,
        command: CreateRelationshipCommand,
        mock_schema_repository: Mock,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject relationship with non-existent target entity.

        REQUIREMENT: Missing entity is rejected.
        """
        # Mock: target entity does not exist
        def exists_side_effect(entity_id: EntityDefinitionId) -> bool:
            return entity_id.value != "nonexistent_target"

        mock_schema_repository.exists.side_effect = exists_side_effect

        result = command.execute(
            relationship_id="invalid_target_rel",
            source_entity_id="project",
            target_entity_id="nonexistent_target",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        # Assert failure
        assert result.is_failure()
        assert "target entity" in result.error.lower()
        assert "does not exist" in result.error.lower()
        assert "nonexistent_target" in result.error

        # Assert save not called
        mock_relationship_repository.save.assert_not_called()

    # =========================================================================
    # MISSING REQUIRED FIELDS TESTS
    # =========================================================================

    def test_missing_relationship_id_rejected(
        self,
        command: CreateRelationshipCommand,
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
        mock_relationship_repository.save.assert_not_called()

    def test_missing_source_entity_id_rejected(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject missing source_entity_id."""
        result = command.execute(
            relationship_id="test_rel",
            source_entity_id="",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "source_entity_id is required" in result.error.lower()
        mock_relationship_repository.save.assert_not_called()

    def test_missing_target_entity_id_rejected(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject missing target_entity_id."""
        result = command.execute(
            relationship_id="test_rel",
            source_entity_id="project",
            target_entity_id="",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "target_entity_id is required" in result.error.lower()
        mock_relationship_repository.save.assert_not_called()

    def test_missing_relationship_type_rejected(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject missing relationship_type."""
        result = command.execute(
            relationship_id="test_rel",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "relationship_type is required" in result.error.lower()
        mock_relationship_repository.save.assert_not_called()

    def test_missing_name_key_rejected(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject missing name_key."""
        result = command.execute(
            relationship_id="test_rel",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="",
        )

        assert result.is_failure()
        assert "name_key is required" in result.error.lower()
        mock_relationship_repository.save.assert_not_called()

    def test_invalid_relationship_type_rejected(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should reject invalid relationship_type."""
        result = command.execute(
            relationship_id="test_rel",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="INVALID_TYPE",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "invalid relationship_type" in result.error.lower()
        assert "INVALID_TYPE" in result.error
        mock_relationship_repository.save.assert_not_called()

    # =========================================================================
    # NO SIDE EFFECTS ON FIELDS TESTS
    # =========================================================================

    def test_no_side_effects_on_fields(
        self,
        command: CreateRelationshipCommand,
        mock_schema_repository: Mock,
        mock_relationship_repository: Mock,
    ) -> None:
        """Creating relationship should not modify entity fields.

        REQUIREMENT: No side effects on fields.
        Relationships are metadata only - they do NOT modify entities.
        """
        # Execute relationship creation
        result = command.execute(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.project_boreholes",
        )

        assert result.is_success()

        # Assert schema_repository.save was NOT called (entities not modified)
        mock_schema_repository.save.assert_not_called()

        # Assert only relationship_repository.save was called
        mock_relationship_repository.save.assert_called_once()

    # =========================================================================
    # REPOSITORY ERROR PROPAGATION TESTS
    # =========================================================================

    def test_repository_save_failure_propagated(
        self,
        command: CreateRelationshipCommand,
        mock_relationship_repository: Mock,
    ) -> None:
        """Should propagate repository save failure."""
        mock_relationship_repository.save.return_value = Failure(
            "Database error: constraint violation"
        )

        result = command.execute(
            relationship_id="test_rel",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.is_failure()
        assert "failed to save relationship" in result.error.lower()
        assert "database error" in result.error.lower()

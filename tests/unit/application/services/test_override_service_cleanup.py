"""Unit tests for OverrideService cleanup_synced_overrides (U8)."""

from uuid import uuid4

import pytest

from doc_helper.application.services.override_service import OverrideService
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.override.override_entity import Override
from doc_helper.domain.override.override_ids import OverrideId
from doc_helper.domain.override.override_state import OverrideState
from doc_helper.domain.override.repositories import IOverrideRepository
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class FakeOverrideRepository(IOverrideRepository):
    """Fake override repository for testing."""

    def __init__(self):
        self._overrides: dict[OverrideId, Override] = {}

    def get_by_id(self, override_id: OverrideId):
        override = self._overrides.get(override_id)
        if override:
            return Success(override)
        return Failure(f"Override {override_id} not found")

    def get_by_project_and_field(self, project_id: ProjectId, field_id: FieldDefinitionId):
        for override in self._overrides.values():
            if override.project_id == project_id and override.field_id == field_id:
                return Success(override)
        return Success(None)

    def list_by_project(self, project_id: ProjectId):
        project_overrides = tuple(
            override
            for override in self._overrides.values()
            if override.project_id == project_id
        )
        return Success(project_overrides)

    def save(self, override: Override):
        self._overrides[override.id] = override
        return Success(None)

    def delete(self, override_id: OverrideId):
        if override_id in self._overrides:
            del self._overrides[override_id]
            return Success(None)
        return Failure(f"Override {override_id} not found")

    def delete_by_project_and_field(self, project_id: ProjectId, field_id: FieldDefinitionId):
        to_delete = None
        for override_id, override in self._overrides.items():
            if override.project_id == project_id and override.field_id == field_id:
                to_delete = override_id
                break
        if to_delete:
            del self._overrides[to_delete]
        return Success(None)

    def exists(self, override_id: OverrideId):
        return Success(override_id in self._overrides)


class TestOverrideServiceCleanup:
    """Test OverrideService.cleanup_synced_overrides method (U8)."""

    @pytest.fixture
    def override_repository(self):
        """Create fake override repository."""
        return FakeOverrideRepository()

    @pytest.fixture
    def override_service(self, override_repository):
        """Create override service with fake repository."""
        return OverrideService(override_repository)

    @pytest.fixture
    def project_id(self):
        """Create project ID for testing."""
        return ProjectId(uuid4())

    def test_cleanup_synced_overrides_deletes_synced_state(
        self, override_service, override_repository, project_id
    ):
        """Test cleanup deletes overrides in SYNCED state."""
        # Create override in SYNCED state
        override = Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("field1"),
            override_value="Report Value",
            original_value="System Value",
            state=OverrideState.ACCEPTED,
        )
        override.mark_synced()
        override_repository.save(override)

        # Cleanup should delete the override
        result = override_service.cleanup_synced_overrides(project_id)

        assert isinstance(result, Success)
        assert result.value == 1  # One override cleaned up

        # Override should be deleted
        exists = override_repository.exists(override.id)
        assert exists.value is False

    def test_cleanup_synced_overrides_preserves_synced_formula_state(
        self, override_service, override_repository, project_id
    ):
        """Test cleanup preserves overrides in SYNCED_FORMULA state."""
        # Create override in SYNCED_FORMULA state
        override = Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("field1"),
            override_value="Report Value",
            original_value="System Value",
            state=OverrideState.ACCEPTED,
        )
        override.mark_synced_formula()
        override_repository.save(override)

        # Cleanup should NOT delete the override
        result = override_service.cleanup_synced_overrides(project_id)

        assert isinstance(result, Success)
        assert result.value == 0  # Zero overrides cleaned up

        # Override should still exist
        exists = override_repository.exists(override.id)
        assert exists.value is True

    def test_cleanup_synced_overrides_preserves_pending_state(
        self, override_service, override_repository, project_id
    ):
        """Test cleanup preserves overrides in PENDING state."""
        # Create override in PENDING state
        override = Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("field1"),
            override_value="Report Value",
            original_value="System Value",
            state=OverrideState.PENDING,
        )
        override_repository.save(override)

        # Cleanup should NOT delete the override
        result = override_service.cleanup_synced_overrides(project_id)

        assert isinstance(result, Success)
        assert result.value == 0  # Zero overrides cleaned up

        # Override should still exist
        exists = override_repository.exists(override.id)
        assert exists.value is True

    def test_cleanup_synced_overrides_preserves_accepted_state(
        self, override_service, override_repository, project_id
    ):
        """Test cleanup preserves overrides in ACCEPTED state."""
        # Create override in ACCEPTED state
        override = Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("field1"),
            override_value="Report Value",
            original_value="System Value",
            state=OverrideState.PENDING,
        )
        override.accept()
        override_repository.save(override)

        # Cleanup should NOT delete the override
        result = override_service.cleanup_synced_overrides(project_id)

        assert isinstance(result, Success)
        assert result.value == 0  # Zero overrides cleaned up

        # Override should still exist
        exists = override_repository.exists(override.id)
        assert exists.value is True

    def test_cleanup_synced_overrides_handles_multiple_overrides(
        self, override_service, override_repository, project_id
    ):
        """Test cleanup correctly handles mix of SYNCED and other states."""
        # Create 3 SYNCED overrides (should be deleted)
        for i in range(3):
            override = Override(
                id=OverrideId(uuid4()),
                project_id=project_id,
                field_id=FieldDefinitionId(f"synced_field_{i}"),
                override_value="Report Value",
                original_value="System Value",
                state=OverrideState.ACCEPTED,
            )
            override.mark_synced()
            override_repository.save(override)

        # Create 2 SYNCED_FORMULA overrides (should be preserved)
        for i in range(2):
            override = Override(
                id=OverrideId(uuid4()),
                project_id=project_id,
                field_id=FieldDefinitionId(f"formula_field_{i}"),
                override_value="Report Value",
                original_value="System Value",
                state=OverrideState.ACCEPTED,
            )
            override.mark_synced_formula()
            override_repository.save(override)

        # Create 1 PENDING override (should be preserved)
        override = Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("pending_field"),
            override_value="Report Value",
            original_value="System Value",
            state=OverrideState.PENDING,
        )
        override_repository.save(override)

        # Cleanup should delete only the 3 SYNCED overrides
        result = override_service.cleanup_synced_overrides(project_id)

        assert isinstance(result, Success)
        assert result.value == 3  # Three SYNCED overrides cleaned up

        # Verify count: started with 6, deleted 3, should have 3 remaining
        remaining = override_repository.list_by_project(project_id)
        assert len(remaining.value) == 3

    def test_cleanup_synced_overrides_with_no_overrides(
        self, override_service, project_id
    ):
        """Test cleanup with no overrides returns success with count 0."""
        result = override_service.cleanup_synced_overrides(project_id)

        assert isinstance(result, Success)
        assert result.value == 0

    def test_cleanup_synced_overrides_only_affects_specified_project(
        self, override_service, override_repository, project_id
    ):
        """Test cleanup only deletes overrides for the specified project."""
        # Create override for project_id (should be deleted)
        override1 = Override(
            id=OverrideId(uuid4()),
            project_id=project_id,
            field_id=FieldDefinitionId("field1"),
            override_value="Report Value",
            original_value="System Value",
            state=OverrideState.ACCEPTED,
        )
        override1.mark_synced()
        override_repository.save(override1)

        # Create override for different project (should NOT be deleted)
        other_project_id = ProjectId(uuid4())
        override2 = Override(
            id=OverrideId(uuid4()),
            project_id=other_project_id,
            field_id=FieldDefinitionId("field2"),
            override_value="Report Value",
            original_value="System Value",
            state=OverrideState.ACCEPTED,
        )
        override2.mark_synced()
        override_repository.save(override2)

        # Cleanup should only affect project_id
        result = override_service.cleanup_synced_overrides(project_id)

        assert isinstance(result, Success)
        assert result.value == 1

        # override1 should be deleted
        exists1 = override_repository.exists(override1.id)
        assert exists1.value is False

        # override2 should still exist
        exists2 = override_repository.exists(override2.id)
        assert exists2.value is True

    def test_cleanup_synced_overrides_requires_project_id(self, override_service):
        """Test cleanup requires ProjectId parameter."""
        result = override_service.cleanup_synced_overrides("not_a_project_id")

        assert isinstance(result, Failure)
        assert "ProjectId" in result.error

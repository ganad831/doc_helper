"""Unit tests for ProjectMapper."""

from uuid import uuid4

import pytest

from doc_helper.application.dto import ProjectDTO, ProjectSummaryDTO
from doc_helper.application.mappers import ProjectMapper
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import EntityDefinitionId


class TestProjectMapper:
    """Tests for ProjectMapper."""

    @pytest.fixture
    def saved_project(self) -> Project:
        """Create sample project that has been saved (has file_path)."""
        return Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("soil_investigation"),
            field_values={},
            description="A test project",
            file_path="/path/to/project.dhproj",
        )

    @pytest.fixture
    def unsaved_project(self) -> Project:
        """Create sample project that has not been saved (no file_path)."""
        return Project(
            id=ProjectId(uuid4()),
            name="Unsaved Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("soil_investigation"),
            field_values={},
            description="An unsaved project",
            file_path=None,
        )

    def test_to_dto_saved_project(self, saved_project: Project) -> None:
        """to_dto should convert saved Project to ProjectDTO with is_saved=True."""
        dto = ProjectMapper.to_dto(saved_project)

        assert isinstance(dto, ProjectDTO)
        assert dto.id == str(saved_project.id.value)
        assert dto.name == "Test Project"
        assert dto.description == "A test project"
        assert dto.file_path == "/path/to/project.dhproj"
        assert dto.entity_definition_id == "soil_investigation"
        assert dto.field_count == 0
        assert dto.is_saved is True  # Has file_path, so saved

    def test_to_dto_unsaved_project(self, unsaved_project: Project) -> None:
        """to_dto should convert unsaved Project to ProjectDTO with is_saved=False."""
        dto = ProjectMapper.to_dto(unsaved_project)

        assert isinstance(dto, ProjectDTO)
        assert dto.name == "Unsaved Project"
        assert dto.file_path is None
        assert dto.is_saved is False  # No file_path, so not saved

    def test_to_dto_is_immutable(self, saved_project: Project) -> None:
        """ProjectDTO should be immutable (frozen)."""
        dto = ProjectMapper.to_dto(saved_project)

        with pytest.raises(Exception):  # frozen dataclass raises
            dto.name = "Changed"  # type: ignore

    def test_to_summary_dto_saved(self, saved_project: Project) -> None:
        """to_summary_dto should convert saved Project to ProjectSummaryDTO."""
        dto = ProjectMapper.to_summary_dto(saved_project)

        assert isinstance(dto, ProjectSummaryDTO)
        assert dto.id == str(saved_project.id.value)
        assert dto.name == "Test Project"
        assert dto.file_path == "/path/to/project.dhproj"
        assert dto.is_saved is True

    def test_to_summary_dto_unsaved(self, unsaved_project: Project) -> None:
        """to_summary_dto should convert unsaved Project to ProjectSummaryDTO."""
        dto = ProjectMapper.to_summary_dto(unsaved_project)

        assert dto.name == "Unsaved Project"
        assert dto.file_path is None
        assert dto.is_saved is False

    def test_to_summary_dto_is_immutable(self, saved_project: Project) -> None:
        """ProjectSummaryDTO should be immutable (frozen)."""
        dto = ProjectMapper.to_summary_dto(saved_project)

        with pytest.raises(Exception):
            dto.name = "Changed"  # type: ignore

    def test_no_reverse_mapping(self) -> None:
        """ProjectMapper should NOT have reverse mapping methods."""
        # Verify one-way mapping (H3 requirement)
        assert not hasattr(ProjectMapper, "to_domain")
        assert not hasattr(ProjectMapper, "from_dto")

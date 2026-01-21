"""Unit tests for SearchResultDTO.

ADR-026: Search Architecture
- Tests immutability of search result DTO
- Tests helper methods for checking value presence and match type
- Tests frozen dataclass behavior
"""

import pytest

from doc_helper.application.dto import SearchResultDTO


class TestSearchResultDTO:
    """Tests for SearchResultDTO."""

    def test_create_with_all_fields(self) -> None:
        """Should create SearchResultDTO with all required fields."""
        # Arrange & Act
        dto = SearchResultDTO(
            field_id="site_location",
            field_label="Site Location",
            entity_id="project",
            entity_name="Project Information",
            current_value="123 Main Street",
            field_path="project.site_location",
            match_type="value",
        )

        # Assert
        assert dto.field_id == "site_location"
        assert dto.field_label == "Site Location"
        assert dto.entity_id == "project"
        assert dto.entity_name == "Project Information"
        assert dto.current_value == "123 Main Street"
        assert dto.field_path == "project.site_location"
        assert dto.match_type == "value"

    def test_create_with_none_current_value(self) -> None:
        """Should create SearchResultDTO with None current_value (unset field)."""
        # Arrange & Act
        dto = SearchResultDTO(
            field_id="site_notes",
            field_label="Site Notes",
            entity_id="project",
            entity_name="Project Information",
            current_value=None,
            field_path="project.site_notes",
            match_type="label",
        )

        # Assert
        assert dto.current_value is None

    def test_has_value_returns_true_when_value_set(self) -> None:
        """has_value() should return True when current_value is not None."""
        # Arrange
        dto = SearchResultDTO(
            field_id="owner_name",
            field_label="Owner Name",
            entity_id="project",
            entity_name="Project Information",
            current_value="John Doe",
            field_path="project.owner_name",
            match_type="value",
        )

        # Act & Assert
        assert dto.has_value() is True

    def test_has_value_returns_false_when_value_none(self) -> None:
        """has_value() should return False when current_value is None."""
        # Arrange
        dto = SearchResultDTO(
            field_id="optional_field",
            field_label="Optional Field",
            entity_id="project",
            entity_name="Project Information",
            current_value=None,
            field_path="project.optional_field",
            match_type="label",
        )

        # Act & Assert
        assert dto.has_value() is False

    def test_matches_label_returns_true_for_label_match(self) -> None:
        """matches_label() should return True when match_type is 'label'."""
        # Arrange
        dto = SearchResultDTO(
            field_id="location",
            field_label="Site Location",
            entity_id="project",
            entity_name="Project Information",
            current_value="Downtown",
            field_path="project.location",
            match_type="label",
        )

        # Act & Assert
        assert dto.matches_label() is True
        assert dto.matches_value() is False
        assert dto.matches_field_id() is False

    def test_matches_value_returns_true_for_value_match(self) -> None:
        """matches_value() should return True when match_type is 'value'."""
        # Arrange
        dto = SearchResultDTO(
            field_id="description",
            field_label="Description",
            entity_id="project",
            entity_name="Project Information",
            current_value="soil investigation at downtown site",
            field_path="project.description",
            match_type="value",
        )

        # Act & Assert
        assert dto.matches_label() is False
        assert dto.matches_value() is True
        assert dto.matches_field_id() is False

    def test_matches_field_id_returns_true_for_field_id_match(self) -> None:
        """matches_field_id() should return True when match_type is 'field_id'."""
        # Arrange
        dto = SearchResultDTO(
            field_id="site_location_code",
            field_label="Location Code",
            entity_id="project",
            entity_name="Project Information",
            current_value="LOC-001",
            field_path="project.site_location_code",
            match_type="field_id",
        )

        # Act & Assert
        assert dto.matches_label() is False
        assert dto.matches_value() is False
        assert dto.matches_field_id() is True

    def test_immutability_field_id(self) -> None:
        """SearchResultDTO should be immutable (frozen dataclass) - field_id."""
        # Arrange
        dto = SearchResultDTO(
            field_id="original_id",
            field_label="Label",
            entity_id="entity",
            entity_name="Entity",
            current_value="value",
            field_path="entity.original_id",
            match_type="label",
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            dto.field_id = "modified_id"  # type: ignore

    def test_immutability_current_value(self) -> None:
        """SearchResultDTO should be immutable (frozen dataclass) - current_value."""
        # Arrange
        dto = SearchResultDTO(
            field_id="field",
            field_label="Label",
            entity_id="entity",
            entity_name="Entity",
            current_value="original",
            field_path="entity.field",
            match_type="value",
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            dto.current_value = "modified"  # type: ignore

    def test_immutability_match_type(self) -> None:
        """SearchResultDTO should be immutable (frozen dataclass) - match_type."""
        # Arrange
        dto = SearchResultDTO(
            field_id="field",
            field_label="Label",
            entity_id="entity",
            entity_name="Entity",
            current_value="value",
            field_path="entity.field",
            match_type="label",
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            dto.match_type = "value"  # type: ignore

    def test_equality_based_on_all_fields(self) -> None:
        """Two DTOs with identical data should be equal."""
        # Arrange
        dto1 = SearchResultDTO(
            field_id="location",
            field_label="Location",
            entity_id="project",
            entity_name="Project",
            current_value="Downtown",
            field_path="project.location",
            match_type="label",
        )

        dto2 = SearchResultDTO(
            field_id="location",
            field_label="Location",
            entity_id="project",
            entity_name="Project",
            current_value="Downtown",
            field_path="project.location",
            match_type="label",
        )

        # Act & Assert
        assert dto1 == dto2

    def test_inequality_for_different_field_id(self) -> None:
        """Two DTOs with different field_id should not be equal."""
        # Arrange
        dto1 = SearchResultDTO(
            field_id="location1",
            field_label="Location",
            entity_id="project",
            entity_name="Project",
            current_value="Downtown",
            field_path="project.location1",
            match_type="label",
        )

        dto2 = SearchResultDTO(
            field_id="location2",
            field_label="Location",
            entity_id="project",
            entity_name="Project",
            current_value="Downtown",
            field_path="project.location2",
            match_type="label",
        )

        # Act & Assert
        assert dto1 != dto2

    def test_hash_consistency(self) -> None:
        """Two equal DTOs should have same hash."""
        # Arrange
        dto1 = SearchResultDTO(
            field_id="location",
            field_label="Location",
            entity_id="project",
            entity_name="Project",
            current_value="Downtown",
            field_path="project.location",
            match_type="label",
        )

        dto2 = SearchResultDTO(
            field_id="location",
            field_label="Location",
            entity_id="project",
            entity_name="Project",
            current_value="Downtown",
            field_path="project.location",
            match_type="label",
        )

        # Act & Assert
        assert hash(dto1) == hash(dto2)

        # Test that DTOs can be added to set
        dto_set = {dto1, dto2}
        assert len(dto_set) == 1  # Same DTO, so only one in set

    def test_field_path_format(self) -> None:
        """field_path should follow entity_id.field_id format."""
        # Arrange & Act
        dto = SearchResultDTO(
            field_id="depth",
            field_label="Depth",
            entity_id="borehole",
            entity_name="Borehole",
            current_value="10.5",
            field_path="borehole.depth",
            match_type="value",
        )

        # Assert
        assert dto.field_path == f"{dto.entity_id}.{dto.field_id}"

    def test_complex_current_value_types(self) -> None:
        """current_value should support complex types (lists, dicts)."""
        # Arrange & Act
        dto_list = SearchResultDTO(
            field_id="tags",
            field_label="Tags",
            entity_id="project",
            entity_name="Project",
            current_value=["tag1", "tag2", "tag3"],
            field_path="project.tags",
            match_type="value",
        )

        dto_dict = SearchResultDTO(
            field_id="metadata",
            field_label="Metadata",
            entity_id="project",
            entity_name="Project",
            current_value={"key": "value", "count": 42},
            field_path="project.metadata",
            match_type="value",
        )

        # Assert
        assert dto_list.current_value == ["tag1", "tag2", "tag3"]
        assert dto_dict.current_value == {"key": "value", "count": 42}

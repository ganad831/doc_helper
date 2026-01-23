"""Tests for AppTypeMetadata value object."""

import pytest

from doc_helper.app_types.contracts.app_type_metadata import (
    AppTypeKind,
    AppTypeMetadata,
)


class TestAppTypeMetadataCreation:
    """Tests for AppTypeMetadata creation and validation."""

    def test_valid_metadata_creation(self) -> None:
        """Valid metadata should be created successfully."""
        metadata = AppTypeMetadata(
            app_type_id="soil_investigation",
            name="Soil Investigation Report",
            version="1.0.0",
            description="Generate soil reports",
            icon_path="resources/icon.png",
        )
        assert metadata.app_type_id == "soil_investigation"
        assert metadata.name == "Soil Investigation Report"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Generate soil reports"
        assert metadata.icon_path == "resources/icon.png"

    def test_minimal_metadata_creation(self) -> None:
        """Metadata with only required fields should be valid."""
        metadata = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
        )
        assert metadata.app_type_id == "test_app"
        assert metadata.name == "Test App"
        assert metadata.version == "1.0.0"
        assert metadata.description is None
        assert metadata.icon_path is None

    def test_metadata_is_immutable(self) -> None:
        """Metadata should be immutable (frozen dataclass)."""
        metadata = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
        )
        with pytest.raises(AttributeError):
            metadata.app_type_id = "other_app"  # type: ignore

    def test_metadata_equality(self) -> None:
        """Metadata with same values should be equal."""
        metadata1 = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
        )
        metadata2 = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
        )
        assert metadata1 == metadata2

    def test_metadata_inequality(self) -> None:
        """Metadata with different values should not be equal."""
        metadata1 = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
        )
        metadata2 = AppTypeMetadata(
            app_type_id="other_app",
            name="Other App",
            version="2.0.0",
        )
        assert metadata1 != metadata2


class TestAppTypeMetadataValidation:
    """Tests for AppTypeMetadata field validation."""

    def test_empty_app_type_id_rejected(self) -> None:
        """Empty app_type_id should be rejected."""
        with pytest.raises(ValueError, match="app_type_id cannot be empty"):
            AppTypeMetadata(
                app_type_id="",
                name="Test App",
                version="1.0.0",
            )

    def test_empty_name_rejected(self) -> None:
        """Empty name should be rejected."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            AppTypeMetadata(
                app_type_id="test_app",
                name="",
                version="1.0.0",
            )

    def test_empty_version_rejected(self) -> None:
        """Empty version should be rejected."""
        with pytest.raises(ValueError, match="version cannot be empty"):
            AppTypeMetadata(
                app_type_id="test_app",
                name="Test App",
                version="",
            )

    def test_invalid_app_type_id_uppercase(self) -> None:
        """Uppercase in app_type_id should be rejected."""
        with pytest.raises(ValueError, match="must be lowercase"):
            AppTypeMetadata(
                app_type_id="TestApp",
                name="Test App",
                version="1.0.0",
            )

    def test_invalid_app_type_id_spaces(self) -> None:
        """Spaces in app_type_id should be rejected."""
        with pytest.raises(ValueError, match="must be lowercase"):
            AppTypeMetadata(
                app_type_id="test app",
                name="Test App",
                version="1.0.0",
            )

    def test_invalid_app_type_id_starts_with_number(self) -> None:
        """app_type_id starting with number should be rejected."""
        with pytest.raises(ValueError, match="must be lowercase"):
            AppTypeMetadata(
                app_type_id="123test",
                name="Test App",
                version="1.0.0",
            )

    def test_invalid_app_type_id_special_chars(self) -> None:
        """Special characters in app_type_id should be rejected."""
        with pytest.raises(ValueError, match="must be lowercase"):
            AppTypeMetadata(
                app_type_id="test-app",
                name="Test App",
                version="1.0.0",
            )

    def test_valid_app_type_id_with_underscores(self) -> None:
        """Underscores in app_type_id should be allowed."""
        metadata = AppTypeMetadata(
            app_type_id="soil_investigation",
            name="Soil Investigation",
            version="1.0.0",
        )
        assert metadata.app_type_id == "soil_investigation"

    def test_valid_app_type_id_with_numbers(self) -> None:
        """Numbers after first character should be allowed."""
        metadata = AppTypeMetadata(
            app_type_id="test2app",
            name="Test 2 App",
            version="1.0.0",
        )
        assert metadata.app_type_id == "test2app"

    def test_invalid_version_format(self) -> None:
        """Non-semantic version should be rejected."""
        with pytest.raises(ValueError, match="must follow semantic versioning"):
            AppTypeMetadata(
                app_type_id="test_app",
                name="Test App",
                version="v1.0",
            )

    def test_invalid_version_single_number(self) -> None:
        """Single number version should be rejected."""
        with pytest.raises(ValueError, match="must follow semantic versioning"):
            AppTypeMetadata(
                app_type_id="test_app",
                name="Test App",
                version="1",
            )

    def test_valid_version_with_prerelease(self) -> None:
        """Semantic version with prerelease should be valid."""
        metadata = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0-alpha",
        )
        assert metadata.version == "1.0.0-alpha"

    def test_valid_version_with_build_metadata(self) -> None:
        """Semantic version with build metadata should be valid."""
        metadata = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0+build.123",
        )
        assert metadata.version == "1.0.0+build.123"


class TestAppTypeKind:
    """Tests for AppTypeKind enum."""

    def test_document_kind_value(self) -> None:
        """DOCUMENT kind should have value 'document'."""
        assert AppTypeKind.DOCUMENT.value == "document"

    def test_tool_kind_value(self) -> None:
        """TOOL kind should have value 'tool'."""
        assert AppTypeKind.TOOL.value == "tool"

    def test_from_string_document(self) -> None:
        """from_string should parse 'document' correctly."""
        kind = AppTypeKind.from_string("document")
        assert kind == AppTypeKind.DOCUMENT

    def test_from_string_tool(self) -> None:
        """from_string should parse 'tool' correctly."""
        kind = AppTypeKind.from_string("tool")
        assert kind == AppTypeKind.TOOL

    def test_from_string_case_insensitive(self) -> None:
        """from_string should be case-insensitive."""
        assert AppTypeKind.from_string("DOCUMENT") == AppTypeKind.DOCUMENT
        assert AppTypeKind.from_string("Tool") == AppTypeKind.TOOL
        assert AppTypeKind.from_string("TOOL") == AppTypeKind.TOOL

    def test_from_string_invalid_raises(self) -> None:
        """from_string should raise ValueError for invalid kind."""
        with pytest.raises(ValueError, match="Invalid AppType kind"):
            AppTypeKind.from_string("invalid")


class TestAppTypeMetadataKind:
    """Tests for AppTypeMetadata kind field."""

    def test_default_kind_is_document(self) -> None:
        """Metadata without explicit kind should default to DOCUMENT."""
        metadata = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
        )
        assert metadata.kind == AppTypeKind.DOCUMENT

    def test_explicit_document_kind(self) -> None:
        """Metadata can be created with explicit DOCUMENT kind."""
        metadata = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
            kind=AppTypeKind.DOCUMENT,
        )
        assert metadata.kind == AppTypeKind.DOCUMENT

    def test_explicit_tool_kind(self) -> None:
        """Metadata can be created with explicit TOOL kind."""
        metadata = AppTypeMetadata(
            app_type_id="schema_designer",
            name="Schema Designer",
            version="1.0.0",
            kind=AppTypeKind.TOOL,
        )
        assert metadata.kind == AppTypeKind.TOOL

    def test_is_tool_for_tool_kind(self) -> None:
        """is_tool should return True for TOOL kind."""
        metadata = AppTypeMetadata(
            app_type_id="schema_designer",
            name="Schema Designer",
            version="1.0.0",
            kind=AppTypeKind.TOOL,
        )
        assert metadata.is_tool is True
        assert metadata.is_document is False

    def test_is_document_for_document_kind(self) -> None:
        """is_document should return True for DOCUMENT kind."""
        metadata = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
            kind=AppTypeKind.DOCUMENT,
        )
        assert metadata.is_document is True
        assert metadata.is_tool is False

    def test_is_document_for_default_kind(self) -> None:
        """is_document should return True when kind is not specified."""
        metadata = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
        )
        assert metadata.is_document is True
        assert metadata.is_tool is False

    def test_kind_included_in_equality(self) -> None:
        """Metadata with different kinds should not be equal."""
        metadata1 = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
            kind=AppTypeKind.DOCUMENT,
        )
        metadata2 = AppTypeMetadata(
            app_type_id="test_app",
            name="Test App",
            version="1.0.0",
            kind=AppTypeKind.TOOL,
        )
        assert metadata1 != metadata2

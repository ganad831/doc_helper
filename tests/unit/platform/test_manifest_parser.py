"""Tests for ManifestParser."""

import json
import tempfile
from pathlib import Path

import pytest

from doc_helper.app_types.contracts.app_type_metadata import AppTypeKind
from doc_helper.domain.common.result import Failure, Success
from doc_helper.platform.discovery.manifest_parser import (
    ManifestParseError,
    ManifestParser,
    ParsedManifest,
)


class TestManifestParserValidManifests:
    """Tests for parsing valid manifests."""

    @pytest.fixture
    def parser(self) -> ManifestParser:
        """Create parser instance."""
        return ManifestParser()

    @pytest.fixture
    def valid_manifest_dict(self) -> dict:
        """Return a valid manifest as dict."""
        return {
            "id": "soil_investigation",
            "name": "Soil Investigation Report",
            "version": "1.0.0",
            "description": "Generate professional soil investigation reports",
            "icon": "resources/icon.png",
            "schema": {
                "source": "config.db",
                "type": "sqlite",
            },
            "templates": {
                "word": ["templates/report.docx"],
                "excel": ["templates/data.xlsx"],
                "default": "templates/report.docx",
            },
            "capabilities": {
                "supports_pdf_export": True,
                "supports_excel_export": True,
                "supports_word_export": True,
            },
        }

    def test_parse_valid_manifest_file(
        self, parser: ManifestParser, valid_manifest_dict: dict
    ) -> None:
        """Valid manifest file should parse successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(valid_manifest_dict, f)

            result = parser.parse(manifest_path)

            assert isinstance(result, Success)
            manifest = result.value
            assert manifest.metadata.app_type_id == "soil_investigation"
            assert manifest.metadata.name == "Soil Investigation Report"
            assert manifest.metadata.version == "1.0.0"

    def test_parse_valid_manifest_string(
        self, parser: ManifestParser, valid_manifest_dict: dict
    ) -> None:
        """Valid manifest string should parse successfully."""
        json_str = json.dumps(valid_manifest_dict)
        result = parser.parse_string(json_str)

        assert isinstance(result, Success)
        manifest = result.value
        assert manifest.metadata.app_type_id == "soil_investigation"

    def test_parse_minimal_manifest(self, parser: ManifestParser) -> None:
        """Minimal valid manifest should parse successfully."""
        minimal = {
            "id": "test_app",
            "name": "Test App",
            "version": "1.0.0",
            "schema": {
                "source": "schema.db",
                "type": "sqlite",
            },
        }
        result = parser.parse_string(json.dumps(minimal))

        assert isinstance(result, Success)
        manifest = result.value
        assert manifest.metadata.app_type_id == "test_app"
        assert manifest.metadata.description is None
        assert manifest.metadata.icon_path is None
        assert len(manifest.templates.word) == 0
        assert manifest.capabilities.supports_pdf_export is True  # default

    def test_parsed_manifest_metadata(
        self, parser: ManifestParser, valid_manifest_dict: dict
    ) -> None:
        """Parsed manifest should have correct metadata."""
        result = parser.parse_string(json.dumps(valid_manifest_dict))

        assert isinstance(result, Success)
        metadata = result.value.metadata
        assert metadata.app_type_id == "soil_investigation"
        assert metadata.name == "Soil Investigation Report"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Generate professional soil investigation reports"
        assert metadata.icon_path == "resources/icon.png"

    def test_parsed_manifest_schema(
        self, parser: ManifestParser, valid_manifest_dict: dict
    ) -> None:
        """Parsed manifest should have correct schema config."""
        result = parser.parse_string(json.dumps(valid_manifest_dict))

        assert isinstance(result, Success)
        schema = result.value.schema
        assert schema.source == "config.db"
        assert schema.schema_type == "sqlite"

    def test_parsed_manifest_templates(
        self, parser: ManifestParser, valid_manifest_dict: dict
    ) -> None:
        """Parsed manifest should have correct templates config."""
        result = parser.parse_string(json.dumps(valid_manifest_dict))

        assert isinstance(result, Success)
        templates = result.value.templates
        assert templates.word == ("templates/report.docx",)
        assert templates.excel == ("templates/data.xlsx",)
        assert templates.default == "templates/report.docx"

    def test_parsed_manifest_capabilities(
        self, parser: ManifestParser, valid_manifest_dict: dict
    ) -> None:
        """Parsed manifest should have correct capabilities."""
        result = parser.parse_string(json.dumps(valid_manifest_dict))

        assert isinstance(result, Success)
        caps = result.value.capabilities
        assert caps.supports_pdf_export is True
        assert caps.supports_excel_export is True
        assert caps.supports_word_export is True

    def test_parsed_manifest_path(self, parser: ManifestParser) -> None:
        """Parsed manifest should include the manifest path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = {
                "id": "test_app",
                "name": "Test",
                "version": "1.0.0",
                "schema": {"source": "db", "type": "sqlite"},
            }
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)

            result = parser.parse(manifest_path)

            assert isinstance(result, Success)
            assert result.value.manifest_path == manifest_path


class TestManifestParserInvalidManifests:
    """Tests for parsing invalid manifests."""

    @pytest.fixture
    def parser(self) -> ManifestParser:
        """Create parser instance."""
        return ManifestParser()

    def test_parse_nonexistent_file(self, parser: ManifestParser) -> None:
        """Non-existent file should return failure."""
        result = parser.parse(Path("/nonexistent/manifest.json"))

        assert isinstance(result, Failure)
        assert "not found" in result.error.message.lower()

    def test_parse_directory_instead_of_file(self, parser: ManifestParser) -> None:
        """Directory path should return failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = parser.parse(Path(tmpdir))

            assert isinstance(result, Failure)
            assert "not a file" in result.error.message.lower()

    def test_parse_invalid_json(self, parser: ManifestParser) -> None:
        """Invalid JSON should return failure."""
        result = parser.parse_string("{ invalid json }")

        assert isinstance(result, Failure)
        assert "invalid json" in result.error.message.lower()

    def test_parse_non_object_json(self, parser: ManifestParser) -> None:
        """JSON that's not an object should return failure."""
        result = parser.parse_string('["array", "not", "object"]')

        assert isinstance(result, Failure)
        assert "must be a json object" in result.error.message.lower()

    def test_parse_missing_required_id(self, parser: ManifestParser) -> None:
        """Missing 'id' field should return failure."""
        manifest = {
            "name": "Test",
            "version": "1.0.0",
            "schema": {"source": "db", "type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Failure)
        assert "id" in result.error.message.lower()

    def test_parse_missing_required_name(self, parser: ManifestParser) -> None:
        """Missing 'name' field should return failure."""
        manifest = {
            "id": "test_app",
            "version": "1.0.0",
            "schema": {"source": "db", "type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Failure)
        assert "name" in result.error.message.lower()

    def test_parse_missing_required_version(self, parser: ManifestParser) -> None:
        """Missing 'version' field should return failure."""
        manifest = {
            "id": "test_app",
            "name": "Test",
            "schema": {"source": "db", "type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Failure)
        assert "version" in result.error.message.lower()

    def test_parse_missing_required_schema(self, parser: ManifestParser) -> None:
        """Missing 'schema' field should return failure."""
        manifest = {
            "id": "test_app",
            "name": "Test",
            "version": "1.0.0",
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Failure)
        assert "schema" in result.error.message.lower()

    def test_parse_missing_schema_source(self, parser: ManifestParser) -> None:
        """Missing 'schema.source' field should return failure."""
        manifest = {
            "id": "test_app",
            "name": "Test",
            "version": "1.0.0",
            "schema": {"type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Failure)
        assert "schema.source" in result.error.message.lower()

    def test_parse_missing_schema_type(self, parser: ManifestParser) -> None:
        """Missing 'schema.type' field should return failure."""
        manifest = {
            "id": "test_app",
            "name": "Test",
            "version": "1.0.0",
            "schema": {"source": "db"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Failure)
        assert "schema.type" in result.error.message.lower()

    def test_parse_invalid_schema_type(self, parser: ManifestParser) -> None:
        """Unsupported schema type should return failure."""
        manifest = {
            "id": "test_app",
            "name": "Test",
            "version": "1.0.0",
            "schema": {"source": "db", "type": "mongodb"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Failure)
        assert "unsupported" in result.error.message.lower()

    def test_parse_invalid_app_type_id_format(self, parser: ManifestParser) -> None:
        """Invalid app_type_id format should return failure."""
        manifest = {
            "id": "Test-App",  # uppercase and hyphen
            "name": "Test",
            "version": "1.0.0",
            "schema": {"source": "db", "type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Failure)
        assert "lowercase" in result.error.message.lower()

    def test_parse_invalid_version_format(self, parser: ManifestParser) -> None:
        """Invalid version format should return failure."""
        manifest = {
            "id": "test_app",
            "name": "Test",
            "version": "v1",  # not semver
            "schema": {"source": "db", "type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Failure)
        assert "semantic" in result.error.message.lower()

    def test_parse_schema_not_object(self, parser: ManifestParser) -> None:
        """Schema that's not an object should return failure."""
        manifest = {
            "id": "test_app",
            "name": "Test",
            "version": "1.0.0",
            "schema": "not an object",
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Failure)
        assert "object" in result.error.message.lower()


class TestManifestParseError:
    """Tests for ManifestParseError."""

    def test_error_with_path(self) -> None:
        """Error with path should include path in message."""
        path = Path("app_types/test/manifest.json")
        error = ManifestParseError("Invalid field", path)
        assert "manifest.json" in str(error)
        assert "Invalid field" in str(error)

    def test_error_without_path(self) -> None:
        """Error without path should still have message."""
        error = ManifestParseError("Invalid field")
        assert "Invalid field" in str(error)


class TestManifestParserKindField:
    """Tests for parsing the 'kind' field in manifests."""

    @pytest.fixture
    def parser(self) -> ManifestParser:
        """Create parser instance."""
        return ManifestParser()

    def test_parse_document_kind(self, parser: ManifestParser) -> None:
        """Manifest with kind='document' should parse as DOCUMENT."""
        manifest = {
            "id": "test_app",
            "name": "Test App",
            "version": "1.0.0",
            "kind": "document",
            "schema": {"source": "db", "type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Success)
        assert result.value.metadata.kind == AppTypeKind.DOCUMENT
        assert result.value.metadata.is_document is True
        assert result.value.metadata.is_tool is False

    def test_parse_tool_kind(self, parser: ManifestParser) -> None:
        """Manifest with kind='tool' should parse as TOOL."""
        manifest = {
            "id": "schema_designer",
            "name": "Schema Designer",
            "version": "1.0.0",
            "kind": "tool",
            "schema": {"source": "db", "type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Success)
        assert result.value.metadata.kind == AppTypeKind.TOOL
        assert result.value.metadata.is_tool is True
        assert result.value.metadata.is_document is False

    def test_parse_missing_kind_defaults_to_document(
        self, parser: ManifestParser
    ) -> None:
        """Manifest without 'kind' field should default to DOCUMENT."""
        manifest = {
            "id": "test_app",
            "name": "Test App",
            "version": "1.0.0",
            "schema": {"source": "db", "type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Success)
        assert result.value.metadata.kind == AppTypeKind.DOCUMENT

    def test_parse_kind_case_insensitive(self, parser: ManifestParser) -> None:
        """Kind field parsing should be case-insensitive."""
        manifest = {
            "id": "test_app",
            "name": "Test App",
            "version": "1.0.0",
            "kind": "TOOL",
            "schema": {"source": "db", "type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        assert isinstance(result, Success)
        assert result.value.metadata.kind == AppTypeKind.TOOL

    def test_parse_invalid_kind_defaults_to_document(
        self, parser: ManifestParser
    ) -> None:
        """Invalid kind value should default to DOCUMENT."""
        manifest = {
            "id": "test_app",
            "name": "Test App",
            "version": "1.0.0",
            "kind": "invalid_kind",
            "schema": {"source": "db", "type": "sqlite"},
        }
        result = parser.parse_string(json.dumps(manifest))

        # Invalid kind should still parse, defaulting to DOCUMENT
        assert isinstance(result, Success)
        assert result.value.metadata.kind == AppTypeKind.DOCUMENT

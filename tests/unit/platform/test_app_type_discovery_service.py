"""Tests for AppTypeDiscoveryService."""

import json
from pathlib import Path
from typing import Any

import pytest

from doc_helper.domain.common.result import Failure, Success
from doc_helper.platform.discovery.app_type_discovery_service import (
    AppTypeDiscoveryService,
    DiscoveryResult,
)


def create_manifest_json(
    app_type_id: str = "test_app",
    name: str = "Test App",
    version: str = "1.0.0",
    **kwargs: Any,
) -> str:
    """Create a valid manifest JSON string."""
    manifest = {
        "id": app_type_id,
        "name": name,
        "version": version,
        "schema": {"source": "config.db", "type": "sqlite"},
        **kwargs,
    }
    return json.dumps(manifest, indent=2)


class TestDiscoveryWithEmptyDirectory:
    """Tests for discovery with empty/missing directories."""

    @pytest.fixture
    def discovery_service(self) -> AppTypeDiscoveryService:
        """Create discovery service."""
        return AppTypeDiscoveryService()

    def test_empty_directory_returns_empty_result(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Empty directory should return empty result without errors."""
        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 0
        assert result.has_errors is False
        assert result.manifests == ()
        assert result.errors == ()

    def test_nonexistent_directory_returns_empty_result(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Non-existent directory should return empty result without errors."""
        nonexistent = tmp_path / "nonexistent"

        result = discovery_service.discover(nonexistent)

        assert result.manifest_count == 0
        assert result.has_errors is False

    def test_path_is_file_returns_empty_result(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Path that is a file should return empty result."""
        file_path = tmp_path / "some_file.txt"
        file_path.write_text("content")

        result = discovery_service.discover(file_path)

        assert result.manifest_count == 0
        assert result.has_errors is False


class TestDiscoveryWithValidAppTypes:
    """Tests for discovery with valid AppType directories."""

    @pytest.fixture
    def discovery_service(self) -> AppTypeDiscoveryService:
        """Create discovery service."""
        return AppTypeDiscoveryService()

    def test_single_valid_apptype(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Single valid AppType should be discovered."""
        app_type_dir = tmp_path / "soil_investigation"
        app_type_dir.mkdir()
        manifest_path = app_type_dir / "manifest.json"
        manifest_path.write_text(
            create_manifest_json("soil_investigation", "Soil Investigation")
        )

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 1
        assert result.has_errors is False
        assert result.manifests[0].metadata.app_type_id == "soil_investigation"
        assert result.manifests[0].metadata.name == "Soil Investigation"

    def test_multiple_valid_apptypes(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Multiple valid AppTypes should all be discovered."""
        # Create first AppType
        app1_dir = tmp_path / "soil_investigation"
        app1_dir.mkdir()
        (app1_dir / "manifest.json").write_text(
            create_manifest_json("soil_investigation", "Soil Investigation")
        )

        # Create second AppType
        app2_dir = tmp_path / "structural_report"
        app2_dir.mkdir()
        (app2_dir / "manifest.json").write_text(
            create_manifest_json("structural_report", "Structural Report")
        )

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 2
        assert result.has_errors is False
        # Results should be sorted by directory name
        assert result.manifests[0].metadata.app_type_id == "soil_investigation"
        assert result.manifests[1].metadata.app_type_id == "structural_report"

    def test_discovery_returns_sorted_by_directory_name(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Discovered AppTypes should be sorted alphabetically by directory."""
        # Create in non-alphabetical order
        for name in ["zebra_report", "alpha_report", "mid_report"]:
            app_dir = tmp_path / name
            app_dir.mkdir()
            (app_dir / "manifest.json").write_text(create_manifest_json(name, name))

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 3
        ids = [m.metadata.app_type_id for m in result.manifests]
        assert ids == ["alpha_report", "mid_report", "zebra_report"]


class TestDiscoverySkipsSpecialDirectories:
    """Tests for skipping special directories during discovery."""

    @pytest.fixture
    def discovery_service(self) -> AppTypeDiscoveryService:
        """Create discovery service."""
        return AppTypeDiscoveryService()

    def test_skips_contracts_directory(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Should skip the contracts directory."""
        contracts_dir = tmp_path / "contracts"
        contracts_dir.mkdir()
        # Even if it has a manifest, it should be skipped
        (contracts_dir / "manifest.json").write_text(
            create_manifest_json("contracts", "Contracts")
        )

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 0

    def test_skips_underscore_directories(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Should skip directories starting with underscore."""
        hidden_dir = tmp_path / "_template"
        hidden_dir.mkdir()
        (hidden_dir / "manifest.json").write_text(
            create_manifest_json("template", "Template")
        )

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 0

    def test_skips_dot_directories(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Should skip directories starting with dot."""
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "manifest.json").write_text(
            create_manifest_json("hidden", "Hidden")
        )

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 0

    def test_skips_files_in_root(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Should skip files (not directories) in the app_types root."""
        # Create a valid AppType
        app_dir = tmp_path / "valid_app"
        app_dir.mkdir()
        (app_dir / "manifest.json").write_text(
            create_manifest_json("valid_app", "Valid App")
        )

        # Create files that should be ignored
        (tmp_path / "__init__.py").write_text("")
        (tmp_path / "some_file.json").write_text("{}")

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 1
        assert result.manifests[0].metadata.app_type_id == "valid_app"

    def test_skips_directory_without_manifest(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Should skip directories that don't have manifest.json."""
        # Directory without manifest
        no_manifest_dir = tmp_path / "no_manifest_app"
        no_manifest_dir.mkdir()
        (no_manifest_dir / "config.db").write_text("")  # Has other files

        # Directory with manifest
        with_manifest_dir = tmp_path / "with_manifest_app"
        with_manifest_dir.mkdir()
        (with_manifest_dir / "manifest.json").write_text(
            create_manifest_json("with_manifest_app", "With Manifest")
        )

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 1
        assert result.manifests[0].metadata.app_type_id == "with_manifest_app"


class TestDiscoveryWithInvalidManifests:
    """Tests for discovery handling invalid manifests."""

    @pytest.fixture
    def discovery_service(self) -> AppTypeDiscoveryService:
        """Create discovery service."""
        return AppTypeDiscoveryService()

    def test_invalid_json_returns_error(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Invalid JSON should be recorded as error."""
        app_dir = tmp_path / "invalid_app"
        app_dir.mkdir()
        (app_dir / "manifest.json").write_text("{ invalid json }")

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 0
        assert result.has_errors is True
        assert len(result.errors) == 1
        assert "JSON" in result.errors[0].message

    def test_missing_required_field_returns_error(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Manifest missing required fields should be recorded as error."""
        app_dir = tmp_path / "incomplete_app"
        app_dir.mkdir()
        # Missing 'schema' field
        (app_dir / "manifest.json").write_text(
            json.dumps({"id": "incomplete_app", "name": "Incomplete", "version": "1.0.0"})
        )

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 0
        assert result.has_errors is True
        assert "schema" in result.errors[0].message.lower()

    def test_mixed_valid_and_invalid(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """Discovery should continue past invalid manifests."""
        # Create valid AppType
        valid_dir = tmp_path / "valid_app"
        valid_dir.mkdir()
        (valid_dir / "manifest.json").write_text(
            create_manifest_json("valid_app", "Valid App")
        )

        # Create invalid AppType
        invalid_dir = tmp_path / "invalid_app"
        invalid_dir.mkdir()
        (invalid_dir / "manifest.json").write_text("{ broken }")

        result = discovery_service.discover(tmp_path)

        assert result.manifest_count == 1
        assert result.has_errors is True
        assert len(result.errors) == 1
        assert result.manifests[0].metadata.app_type_id == "valid_app"


class TestDiscoverSingle:
    """Tests for discover_single method."""

    @pytest.fixture
    def discovery_service(self) -> AppTypeDiscoveryService:
        """Create discovery service."""
        return AppTypeDiscoveryService()

    def test_discover_single_valid(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """discover_single should return Success for valid AppType."""
        app_dir = tmp_path / "valid_app"
        app_dir.mkdir()
        (app_dir / "manifest.json").write_text(
            create_manifest_json("valid_app", "Valid App")
        )

        result = discovery_service.discover_single(app_dir)

        assert isinstance(result, Success)
        assert result.value.metadata.app_type_id == "valid_app"

    def test_discover_single_nonexistent(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """discover_single should return Failure for non-existent path."""
        nonexistent = tmp_path / "nonexistent"

        result = discovery_service.discover_single(nonexistent)

        assert isinstance(result, Failure)
        assert "not found" in result.error.message.lower()

    def test_discover_single_is_file(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """discover_single should return Failure when path is a file."""
        file_path = tmp_path / "some_file"
        file_path.write_text("content")

        result = discovery_service.discover_single(file_path)

        assert isinstance(result, Failure)
        assert "not a directory" in result.error.message.lower()

    def test_discover_single_missing_manifest(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """discover_single should return Failure when manifest.json missing."""
        app_dir = tmp_path / "no_manifest"
        app_dir.mkdir()

        result = discovery_service.discover_single(app_dir)

        assert isinstance(result, Failure)

    def test_discover_single_invalid_manifest(
        self, discovery_service: AppTypeDiscoveryService, tmp_path: Path
    ) -> None:
        """discover_single should return Failure for invalid manifest."""
        app_dir = tmp_path / "invalid_app"
        app_dir.mkdir()
        (app_dir / "manifest.json").write_text("{ broken json }")

        result = discovery_service.discover_single(app_dir)

        assert isinstance(result, Failure)
        assert "JSON" in result.error.message


class TestDiscoveryResult:
    """Tests for DiscoveryResult value object."""

    def test_empty_result_properties(self) -> None:
        """Empty result should have correct properties."""
        result = DiscoveryResult(manifests=(), errors=())

        assert result.manifest_count == 0
        assert result.has_errors is False

    def test_result_with_manifests(self) -> None:
        """Result with manifests should report count correctly."""
        from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata
        from doc_helper.platform.discovery.manifest_parser import (
            ManifestCapabilities,
            ManifestSchema,
            ManifestTemplates,
            ParsedManifest,
        )

        manifest = ParsedManifest(
            metadata=AppTypeMetadata(
                app_type_id="test_app",
                name="Test App",
                version="1.0.0",
            ),
            schema=ManifestSchema(source="config.db", schema_type="sqlite"),
            templates=ManifestTemplates(),
            capabilities=ManifestCapabilities(),
            manifest_path=Path("test/manifest.json"),
        )

        result = DiscoveryResult(manifests=(manifest,), errors=())

        assert result.manifest_count == 1
        assert result.has_errors is False

    def test_result_with_errors(self) -> None:
        """Result with errors should report has_errors correctly."""
        from doc_helper.platform.discovery.manifest_parser import ManifestParseError

        error = ManifestParseError("Test error", Path("test"))

        result = DiscoveryResult(manifests=(), errors=(error,))

        assert result.manifest_count == 0
        assert result.has_errors is True

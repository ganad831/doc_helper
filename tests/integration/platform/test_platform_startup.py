"""Integration tests for platform startup scenarios.

These tests verify that the platform starts correctly under various conditions,
including the critical Phase 1 scenario of an empty app_types/ directory.
"""

import json
from pathlib import Path
from typing import Generator

import pytest

from doc_helper.platform.discovery.app_type_discovery_service import (
    AppTypeDiscoveryService,
)
from doc_helper.platform.registry.app_type_registry import AppTypeRegistry
from doc_helper.platform.routing.app_type_router import AppTypeRouter


class TestPlatformStartupWithEmptyAppTypes:
    """Integration tests for platform startup with empty app_types/ directory.

    Phase 1 Requirement:
        The platform MUST start without crashing when app_types/ is empty.
        This is the expected state during Phase 1 before any AppTypes are migrated.
    """

    @pytest.fixture
    def empty_app_types_dir(self, tmp_path: Path) -> Generator[Path, None, None]:
        """Create an empty app_types directory structure."""
        app_types_dir = tmp_path / "app_types"
        app_types_dir.mkdir()
        # Create contracts subdirectory (always present but should be skipped)
        contracts_dir = app_types_dir / "contracts"
        contracts_dir.mkdir()
        (contracts_dir / "__init__.py").write_text("")
        yield app_types_dir

    def test_discovery_with_empty_directory_returns_empty_result(
        self, empty_app_types_dir: Path
    ) -> None:
        """Discovery should return empty result without errors."""
        discovery = AppTypeDiscoveryService()

        result = discovery.discover(empty_app_types_dir)

        assert result.manifest_count == 0
        assert result.has_errors is False

    def test_registry_starts_empty(self) -> None:
        """Registry should start empty."""
        registry = AppTypeRegistry()

        assert registry.count == 0
        assert registry.list_app_type_ids() == ()

    def test_router_has_no_current_apptype_initially(self) -> None:
        """Router should have no current AppType on startup."""
        registry = AppTypeRegistry()
        router = AppTypeRouter(registry)

        assert router.get_current_id() is None
        assert router.get_current_manifest() is None

    def test_full_startup_workflow_with_empty_app_types(
        self, empty_app_types_dir: Path
    ) -> None:
        """Full platform startup workflow should succeed with empty app_types."""
        # Step 1: Create services
        discovery = AppTypeDiscoveryService()
        registry = AppTypeRegistry()
        router = AppTypeRouter(registry)

        # Step 2: Discover AppTypes (should find none)
        result = discovery.discover(empty_app_types_dir)

        # Step 3: Register discovered AppTypes (none in this case)
        for manifest in result.manifests:
            registry.register(manifest)

        # Step 4: Verify platform state
        assert registry.count == 0
        assert router.get_current_id() is None
        assert result.has_errors is False

        # Platform startup complete without errors


class TestPlatformStartupWithValidAppTypes:
    """Integration tests for platform startup with valid AppTypes."""

    @pytest.fixture
    def app_types_dir_with_one_apptype(
        self, tmp_path: Path
    ) -> Generator[Path, None, None]:
        """Create app_types directory with one valid AppType."""
        app_types_dir = tmp_path / "app_types"
        app_types_dir.mkdir()

        # Create contracts subdirectory
        contracts_dir = app_types_dir / "contracts"
        contracts_dir.mkdir()
        (contracts_dir / "__init__.py").write_text("")

        # Create a valid AppType
        soil_dir = app_types_dir / "soil_investigation"
        soil_dir.mkdir()
        manifest = {
            "id": "soil_investigation",
            "name": "Soil Investigation Report",
            "version": "1.0.0",
            "description": "Generate soil investigation reports",
            "schema": {"source": "config.db", "type": "sqlite"},
            "templates": {
                "word": ["templates/standard_report.docx"],
                "default": "templates/standard_report.docx",
            },
        }
        (soil_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

        yield app_types_dir

    def test_full_startup_workflow_with_valid_apptype(
        self, app_types_dir_with_one_apptype: Path
    ) -> None:
        """Full platform startup workflow should discover and register AppTypes."""
        # Step 1: Create services
        discovery = AppTypeDiscoveryService()
        registry = AppTypeRegistry()
        router = AppTypeRouter(registry)

        # Step 2: Discover AppTypes
        result = discovery.discover(app_types_dir_with_one_apptype)

        assert result.manifest_count == 1
        assert result.has_errors is False

        # Step 3: Register discovered AppTypes
        for manifest in result.manifests:
            registry.register(manifest)

        assert registry.count == 1
        assert registry.exists("soil_investigation")

        # Step 4: Router can now set current AppType
        success = router.set_current("soil_investigation")
        assert success is True
        assert router.get_current_id() == "soil_investigation"

        # Get current manifest
        current = router.get_current_manifest()
        assert current is not None
        assert current.metadata.name == "Soil Investigation Report"


class TestPlatformStartupWithMixedAppTypes:
    """Integration tests for startup with both valid and invalid AppTypes."""

    @pytest.fixture
    def app_types_dir_mixed(self, tmp_path: Path) -> Generator[Path, None, None]:
        """Create app_types directory with valid and invalid AppTypes."""
        app_types_dir = tmp_path / "app_types"
        app_types_dir.mkdir()

        # Create contracts subdirectory
        contracts_dir = app_types_dir / "contracts"
        contracts_dir.mkdir()

        # Create a valid AppType
        valid_dir = app_types_dir / "valid_report"
        valid_dir.mkdir()
        valid_manifest = {
            "id": "valid_report",
            "name": "Valid Report",
            "version": "1.0.0",
            "schema": {"source": "config.db", "type": "sqlite"},
        }
        (valid_dir / "manifest.json").write_text(json.dumps(valid_manifest))

        # Create an invalid AppType (broken JSON)
        invalid_dir = app_types_dir / "broken_app"
        invalid_dir.mkdir()
        (invalid_dir / "manifest.json").write_text("{ broken json }")

        # Create another valid AppType
        valid2_dir = app_types_dir / "another_valid"
        valid2_dir.mkdir()
        valid2_manifest = {
            "id": "another_valid",
            "name": "Another Valid",
            "version": "2.0.0",
            "schema": {"source": "schema.db", "type": "sqlite"},
        }
        (valid2_dir / "manifest.json").write_text(json.dumps(valid2_manifest))

        yield app_types_dir

    def test_startup_continues_past_invalid_manifests(
        self, app_types_dir_mixed: Path
    ) -> None:
        """Platform should continue startup even with some invalid manifests."""
        # Step 1: Create services
        discovery = AppTypeDiscoveryService()
        registry = AppTypeRegistry()
        router = AppTypeRouter(registry)

        # Step 2: Discover AppTypes
        result = discovery.discover(app_types_dir_mixed)

        # Should find 2 valid, 1 error
        assert result.manifest_count == 2
        assert result.has_errors is True
        assert len(result.errors) == 1

        # Step 3: Register only valid AppTypes
        for manifest in result.manifests:
            registry.register(manifest)

        # Step 4: Verify valid AppTypes are available
        assert registry.count == 2
        assert registry.exists("valid_report")
        assert registry.exists("another_valid")

        # Invalid AppType is NOT registered
        assert not registry.exists("broken_app")

        # Router can use valid AppTypes
        assert router.set_current("valid_report") is True
        assert router.set_current("another_valid") is True


class TestPlatformStartupWithNonexistentDirectory:
    """Integration tests for platform startup when app_types/ doesn't exist."""

    def test_startup_with_nonexistent_directory(self, tmp_path: Path) -> None:
        """Platform should handle non-existent app_types directory gracefully."""
        nonexistent = tmp_path / "nonexistent_app_types"

        discovery = AppTypeDiscoveryService()
        registry = AppTypeRegistry()
        router = AppTypeRouter(registry)

        # Discovery should not crash
        result = discovery.discover(nonexistent)

        assert result.manifest_count == 0
        assert result.has_errors is False

        # Platform continues with empty registry
        assert registry.count == 0
        assert router.get_current_id() is None

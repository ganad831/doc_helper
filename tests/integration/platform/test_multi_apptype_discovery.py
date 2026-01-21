"""Integration tests for multi-AppType discovery.

Tests that platform can discover and register multiple AppTypes
(soil_investigation and test_report) without conflicts.
"""

import pytest
from pathlib import Path

from doc_helper.platform.discovery.app_type_discovery_service import (
    AppTypeDiscoveryService,
)
from doc_helper.platform.registry.app_type_registry import AppTypeRegistry


class TestMultiAppTypeDiscovery:
    """Test discovery of multiple AppTypes."""

    @pytest.fixture
    def discovery_service(self) -> AppTypeDiscoveryService:
        """Create discovery service."""
        return AppTypeDiscoveryService()

    @pytest.fixture
    def registry(self) -> AppTypeRegistry:
        """Create registry."""
        return AppTypeRegistry()

    @pytest.fixture
    def app_types_path(self) -> Path:
        """Get app_types directory path."""
        return Path("src/doc_helper/app_types")

    def test_discovers_soil_investigation_apptype(
        self, discovery_service: AppTypeDiscoveryService, app_types_path: Path
    ) -> None:
        """Test that soil_investigation AppType is discovered."""
        result = discovery_service.discover(app_types_path)

        assert result.manifest_count > 0
        assert any(m.metadata.app_type_id == "soil_investigation" for m in result.manifests)

    def test_discovers_test_report_apptype(
        self, discovery_service: AppTypeDiscoveryService, app_types_path: Path
    ) -> None:
        """Test that test_report AppType is discovered."""
        result = discovery_service.discover(app_types_path)

        assert result.manifest_count > 0
        assert any(m.metadata.app_type_id == "test_report" for m in result.manifests)

    def test_discovers_both_apptypes(
        self, discovery_service: AppTypeDiscoveryService, app_types_path: Path
    ) -> None:
        """Test that both AppTypes are discovered together."""
        result = discovery_service.discover(app_types_path)

        # Should find at least 2 AppTypes
        assert result.manifest_count >= 2

        # Extract IDs
        discovered_ids = {m.metadata.app_type_id for m in result.manifests}

        # Both should be present
        assert "soil_investigation" in discovered_ids
        assert "test_report" in discovered_ids

    def test_both_apptypes_have_valid_manifests(
        self, discovery_service: AppTypeDiscoveryService, app_types_path: Path
    ) -> None:
        """Test that both AppTypes have valid manifests."""
        result = discovery_service.discover(app_types_path)

        # No errors
        assert not result.has_errors

        # Find manifests
        soil_manifest = next(
            m for m in result.manifests
            if m.metadata.app_type_id == "soil_investigation"
        )
        test_manifest = next(
            m for m in result.manifests
            if m.metadata.app_type_id == "test_report"
        )

        # Validate soil_investigation
        assert soil_manifest.metadata.name == "Soil Investigation Report"
        assert soil_manifest.metadata.version == "1.0.0"
        assert soil_manifest.schema.source == "config.db"
        assert soil_manifest.schema.schema_type == "sqlite"

        # Validate test_report
        assert test_manifest.metadata.name == "Test Report"
        assert test_manifest.metadata.version == "1.0.0"
        assert test_manifest.schema.source == "config.db"
        assert test_manifest.schema.schema_type == "sqlite"

    def test_can_register_both_apptypes(
        self,
        discovery_service: AppTypeDiscoveryService,
        registry: AppTypeRegistry,
        app_types_path: Path,
    ) -> None:
        """Test that both AppTypes can be registered in same registry."""
        # Discover
        result = discovery_service.discover(app_types_path)

        # Import AppTypes
        from doc_helper.app_types.soil_investigation import SoilInvestigationAppType
        from doc_helper.app_types.test_report import TestReportAppType

        # Create instances
        soil_app = SoilInvestigationAppType()
        test_app = TestReportAppType()

        # Register both
        registry.register(soil_app)
        registry.register(test_app)

        # Verify registration
        assert registry.count == 2
        assert registry.exists("soil_investigation")
        assert registry.exists("test_report")

    def test_registered_apptypes_are_isolated(
        self, registry: AppTypeRegistry
    ) -> None:
        """Test that registered AppTypes don't interfere with each other."""
        from doc_helper.app_types.soil_investigation import SoilInvestigationAppType
        from doc_helper.app_types.test_report import TestReportAppType

        soil_app = SoilInvestigationAppType()
        test_app = TestReportAppType()

        registry.register(soil_app)
        registry.register(test_app)

        # Get each AppType
        retrieved_soil = registry.get("soil_investigation")
        retrieved_test = registry.get("test_report")

        # Verify they are different instances
        assert retrieved_soil is soil_app
        assert retrieved_test is test_app
        assert retrieved_soil is not retrieved_test

        # Verify metadata is isolated
        assert retrieved_soil.metadata.app_type_id == "soil_investigation"
        assert retrieved_test.metadata.app_type_id == "test_report"
        assert retrieved_soil.metadata.name != retrieved_test.metadata.name

    def test_apptypes_sorted_alphabetically(
        self, discovery_service: AppTypeDiscoveryService, app_types_path: Path
    ) -> None:
        """Test that discovered AppTypes are sorted alphabetically."""
        result = discovery_service.discover(app_types_path)

        # Get IDs in discovery order
        ids = [m.metadata.app_type_id for m in result.manifests]

        # Should be sorted
        assert ids == sorted(ids)

        # Soil investigation should come before test_report
        soil_idx = ids.index("soil_investigation")
        test_idx = ids.index("test_report")
        assert soil_idx < test_idx

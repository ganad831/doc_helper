"""Tests for AppTypeRegistry."""

from pathlib import Path

import pytest

from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata
from doc_helper.platform.discovery.manifest_parser import (
    ManifestCapabilities,
    ManifestSchema,
    ManifestTemplates,
    ParsedManifest,
)
from doc_helper.platform.registry.app_type_registry import AppTypeRegistry


def create_manifest(
    app_type_id: str,
    name: str = "Test App",
    version: str = "1.0.0",
) -> ParsedManifest:
    """Helper to create test manifests."""
    return ParsedManifest(
        metadata=AppTypeMetadata(
            app_type_id=app_type_id,
            name=name,
            version=version,
        ),
        schema=ManifestSchema(source="config.db", schema_type="sqlite"),
        templates=ManifestTemplates(),
        capabilities=ManifestCapabilities(),
        manifest_path=Path(f"app_types/{app_type_id}/manifest.json"),
    )


class TestAppTypeRegistryBasics:
    """Tests for basic registry operations."""

    @pytest.fixture
    def registry(self) -> AppTypeRegistry:
        """Create empty registry."""
        return AppTypeRegistry()

    def test_empty_registry_has_count_zero(self, registry: AppTypeRegistry) -> None:
        """Empty registry should have count 0."""
        assert registry.count == 0

    def test_empty_registry_list_empty(self, registry: AppTypeRegistry) -> None:
        """Empty registry should return empty list."""
        assert registry.list_app_type_ids() == ()
        assert registry.list_all() == ()
        assert registry.list_metadata() == ()


class TestAppTypeRegistration:
    """Tests for registering AppTypes."""

    @pytest.fixture
    def registry(self) -> AppTypeRegistry:
        """Create empty registry."""
        return AppTypeRegistry()

    def test_register_single_apptype(self, registry: AppTypeRegistry) -> None:
        """Registering an AppType should increase count."""
        manifest = create_manifest("soil_investigation", "Soil Investigation")
        registry.register(manifest)

        assert registry.count == 1
        assert registry.exists("soil_investigation")

    def test_register_multiple_apptypes(self, registry: AppTypeRegistry) -> None:
        """Registering multiple AppTypes should all be stored."""
        manifest1 = create_manifest("soil_investigation", "Soil Investigation")
        manifest2 = create_manifest("structural_report", "Structural Report")

        registry.register(manifest1)
        registry.register(manifest2)

        assert registry.count == 2
        assert registry.exists("soil_investigation")
        assert registry.exists("structural_report")

    def test_register_duplicate_raises(self, registry: AppTypeRegistry) -> None:
        """Registering duplicate app_type_id should raise ValueError."""
        manifest1 = create_manifest("test_app", "Test App v1")
        manifest2 = create_manifest("test_app", "Test App v2")

        registry.register(manifest1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(manifest2)


class TestAppTypeLookup:
    """Tests for looking up registered AppTypes."""

    @pytest.fixture
    def registry_with_apptypes(self) -> AppTypeRegistry:
        """Create registry with pre-registered AppTypes."""
        registry = AppTypeRegistry()
        registry.register(create_manifest("soil_investigation", "Soil Investigation", "1.0.0"))
        registry.register(create_manifest("structural_report", "Structural Report", "2.0.0"))
        return registry

    def test_get_existing_apptype(
        self, registry_with_apptypes: AppTypeRegistry
    ) -> None:
        """Getting existing AppType should return manifest."""
        manifest = registry_with_apptypes.get("soil_investigation")

        assert manifest is not None
        assert manifest.metadata.app_type_id == "soil_investigation"
        assert manifest.metadata.name == "Soil Investigation"

    def test_get_nonexistent_apptype(
        self, registry_with_apptypes: AppTypeRegistry
    ) -> None:
        """Getting non-existent AppType should return None."""
        manifest = registry_with_apptypes.get("nonexistent")

        assert manifest is None

    def test_get_metadata_existing(
        self, registry_with_apptypes: AppTypeRegistry
    ) -> None:
        """Getting metadata for existing AppType should return metadata."""
        metadata = registry_with_apptypes.get_metadata("soil_investigation")

        assert metadata is not None
        assert metadata.app_type_id == "soil_investigation"
        assert metadata.name == "Soil Investigation"

    def test_get_metadata_nonexistent(
        self, registry_with_apptypes: AppTypeRegistry
    ) -> None:
        """Getting metadata for non-existent AppType should return None."""
        metadata = registry_with_apptypes.get_metadata("nonexistent")

        assert metadata is None

    def test_exists_true_for_registered(
        self, registry_with_apptypes: AppTypeRegistry
    ) -> None:
        """exists() should return True for registered AppType."""
        assert registry_with_apptypes.exists("soil_investigation") is True
        assert registry_with_apptypes.exists("structural_report") is True

    def test_exists_false_for_unregistered(
        self, registry_with_apptypes: AppTypeRegistry
    ) -> None:
        """exists() should return False for unregistered AppType."""
        assert registry_with_apptypes.exists("nonexistent") is False


class TestAppTypeListing:
    """Tests for listing registered AppTypes."""

    @pytest.fixture
    def registry_with_apptypes(self) -> AppTypeRegistry:
        """Create registry with pre-registered AppTypes (in non-alphabetical order)."""
        registry = AppTypeRegistry()
        registry.register(create_manifest("structural_report", "Structural Report"))
        registry.register(create_manifest("soil_investigation", "Soil Investigation"))
        registry.register(create_manifest("environmental_report", "Environmental Report"))
        return registry

    def test_list_app_type_ids_sorted(
        self, registry_with_apptypes: AppTypeRegistry
    ) -> None:
        """list_app_type_ids() should return sorted IDs."""
        ids = registry_with_apptypes.list_app_type_ids()

        assert ids == (
            "environmental_report",
            "soil_investigation",
            "structural_report",
        )

    def test_list_all_sorted(
        self, registry_with_apptypes: AppTypeRegistry
    ) -> None:
        """list_all() should return manifests sorted by ID."""
        manifests = registry_with_apptypes.list_all()

        assert len(manifests) == 3
        assert manifests[0].metadata.app_type_id == "environmental_report"
        assert manifests[1].metadata.app_type_id == "soil_investigation"
        assert manifests[2].metadata.app_type_id == "structural_report"

    def test_list_metadata_sorted(
        self, registry_with_apptypes: AppTypeRegistry
    ) -> None:
        """list_metadata() should return metadata sorted by ID."""
        metadata_list = registry_with_apptypes.list_metadata()

        assert len(metadata_list) == 3
        assert metadata_list[0].app_type_id == "environmental_report"
        assert metadata_list[1].app_type_id == "soil_investigation"
        assert metadata_list[2].app_type_id == "structural_report"


class TestAppTypeUnregistration:
    """Tests for unregistering AppTypes."""

    @pytest.fixture
    def registry_with_apptype(self) -> AppTypeRegistry:
        """Create registry with one AppType."""
        registry = AppTypeRegistry()
        registry.register(create_manifest("test_app", "Test App"))
        return registry

    def test_unregister_existing_apptype(
        self, registry_with_apptype: AppTypeRegistry
    ) -> None:
        """Unregistering existing AppType should remove it."""
        result = registry_with_apptype.unregister("test_app")

        assert result is True
        assert registry_with_apptype.exists("test_app") is False
        assert registry_with_apptype.count == 0

    def test_unregister_nonexistent_apptype(
        self, registry_with_apptype: AppTypeRegistry
    ) -> None:
        """Unregistering non-existent AppType should return False."""
        result = registry_with_apptype.unregister("nonexistent")

        assert result is False
        assert registry_with_apptype.count == 1  # unchanged


class TestAppTypeClear:
    """Tests for clearing the registry."""

    def test_clear_removes_all(self) -> None:
        """clear() should remove all registered AppTypes."""
        registry = AppTypeRegistry()
        registry.register(create_manifest("app1", "App 1"))
        registry.register(create_manifest("app2", "App 2"))
        registry.register(create_manifest("app3", "App 3"))

        assert registry.count == 3

        registry.clear()

        assert registry.count == 0
        assert registry.list_app_type_ids() == ()

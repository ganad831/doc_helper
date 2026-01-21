"""Tests for AppTypeRouter."""

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
from doc_helper.platform.routing.app_type_router import AppTypeRouter, IAppTypeRouter


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


class TestAppTypeRouterInterface:
    """Tests that AppTypeRouter implements IAppTypeRouter."""

    def test_implements_interface(self) -> None:
        """AppTypeRouter should implement IAppTypeRouter."""
        registry = AppTypeRegistry()
        router = AppTypeRouter(registry)

        assert isinstance(router, IAppTypeRouter)


class TestAppTypeRouterInitialState:
    """Tests for router initial state."""

    @pytest.fixture
    def router(self) -> AppTypeRouter:
        """Create router with empty registry."""
        return AppTypeRouter(AppTypeRegistry())

    def test_initial_current_id_is_none(self, router: AppTypeRouter) -> None:
        """Initially no AppType should be current."""
        assert router.get_current_id() is None

    def test_initial_current_manifest_is_none(self, router: AppTypeRouter) -> None:
        """Initially current manifest should be None."""
        assert router.get_current_manifest() is None

    def test_initial_current_metadata_is_none(self, router: AppTypeRouter) -> None:
        """Initially current metadata should be None."""
        assert router.get_current_metadata() is None


class TestSetCurrent:
    """Tests for set_current method."""

    @pytest.fixture
    def registry_with_apptype(self) -> AppTypeRegistry:
        """Create registry with one AppType."""
        registry = AppTypeRegistry()
        registry.register(create_manifest("soil_investigation", "Soil Investigation"))
        return registry

    def test_set_current_existing_returns_true(
        self, registry_with_apptype: AppTypeRegistry
    ) -> None:
        """set_current should return True for registered AppType."""
        router = AppTypeRouter(registry_with_apptype)

        result = router.set_current("soil_investigation")

        assert result is True

    def test_set_current_updates_current_id(
        self, registry_with_apptype: AppTypeRegistry
    ) -> None:
        """set_current should update the current id."""
        router = AppTypeRouter(registry_with_apptype)

        router.set_current("soil_investigation")

        assert router.get_current_id() == "soil_investigation"

    def test_set_current_nonexistent_returns_false(
        self, registry_with_apptype: AppTypeRegistry
    ) -> None:
        """set_current should return False for unregistered AppType."""
        router = AppTypeRouter(registry_with_apptype)

        result = router.set_current("nonexistent")

        assert result is False

    def test_set_current_nonexistent_does_not_change_current(
        self, registry_with_apptype: AppTypeRegistry
    ) -> None:
        """set_current with invalid id should not change current."""
        router = AppTypeRouter(registry_with_apptype)
        router.set_current("soil_investigation")

        router.set_current("nonexistent")  # Should fail

        assert router.get_current_id() == "soil_investigation"  # Unchanged

    def test_set_current_can_change_apptype(
        self, registry_with_apptype: AppTypeRegistry
    ) -> None:
        """set_current should be able to switch between AppTypes."""
        registry_with_apptype.register(
            create_manifest("structural_report", "Structural Report")
        )
        router = AppTypeRouter(registry_with_apptype)

        router.set_current("soil_investigation")
        assert router.get_current_id() == "soil_investigation"

        router.set_current("structural_report")
        assert router.get_current_id() == "structural_report"


class TestClearCurrent:
    """Tests for clear_current method."""

    @pytest.fixture
    def router_with_current(self) -> AppTypeRouter:
        """Create router with current AppType set."""
        registry = AppTypeRegistry()
        registry.register(create_manifest("test_app", "Test App"))
        router = AppTypeRouter(registry)
        router.set_current("test_app")
        return router

    def test_clear_current_sets_id_to_none(
        self, router_with_current: AppTypeRouter
    ) -> None:
        """clear_current should set current id to None."""
        router_with_current.clear_current()

        assert router_with_current.get_current_id() is None

    def test_clear_current_sets_manifest_to_none(
        self, router_with_current: AppTypeRouter
    ) -> None:
        """clear_current should make current manifest return None."""
        router_with_current.clear_current()

        assert router_with_current.get_current_manifest() is None

    def test_clear_current_sets_metadata_to_none(
        self, router_with_current: AppTypeRouter
    ) -> None:
        """clear_current should make current metadata return None."""
        router_with_current.clear_current()

        assert router_with_current.get_current_metadata() is None

    def test_clear_current_idempotent(
        self, router_with_current: AppTypeRouter
    ) -> None:
        """Calling clear_current multiple times should be safe."""
        router_with_current.clear_current()
        router_with_current.clear_current()  # Should not raise

        assert router_with_current.get_current_id() is None


class TestGetCurrentManifest:
    """Tests for get_current_manifest method."""

    @pytest.fixture
    def registry(self) -> AppTypeRegistry:
        """Create registry with AppType."""
        registry = AppTypeRegistry()
        registry.register(
            create_manifest("soil_investigation", "Soil Investigation", "2.0.0")
        )
        return registry

    def test_get_current_manifest_returns_manifest(
        self, registry: AppTypeRegistry
    ) -> None:
        """get_current_manifest should return the current manifest."""
        router = AppTypeRouter(registry)
        router.set_current("soil_investigation")

        manifest = router.get_current_manifest()

        assert manifest is not None
        assert manifest.metadata.app_type_id == "soil_investigation"
        assert manifest.metadata.name == "Soil Investigation"
        assert manifest.metadata.version == "2.0.0"

    def test_get_current_manifest_none_when_not_set(
        self, registry: AppTypeRegistry
    ) -> None:
        """get_current_manifest should return None when not set."""
        router = AppTypeRouter(registry)

        manifest = router.get_current_manifest()

        assert manifest is None


class TestGetCurrentMetadata:
    """Tests for get_current_metadata method."""

    @pytest.fixture
    def registry(self) -> AppTypeRegistry:
        """Create registry with AppType."""
        registry = AppTypeRegistry()
        registry.register(
            create_manifest("soil_investigation", "Soil Investigation", "2.0.0")
        )
        return registry

    def test_get_current_metadata_returns_metadata(
        self, registry: AppTypeRegistry
    ) -> None:
        """get_current_metadata should return metadata for current AppType."""
        router = AppTypeRouter(registry)
        router.set_current("soil_investigation")

        metadata = router.get_current_metadata()

        assert metadata is not None
        assert metadata.app_type_id == "soil_investigation"
        assert metadata.name == "Soil Investigation"
        assert metadata.version == "2.0.0"

    def test_get_current_metadata_none_when_not_set(
        self, registry: AppTypeRegistry
    ) -> None:
        """get_current_metadata should return None when not set."""
        router = AppTypeRouter(registry)

        metadata = router.get_current_metadata()

        assert metadata is None


class TestIsValidAppType:
    """Tests for is_valid_app_type method."""

    @pytest.fixture
    def router(self) -> AppTypeRouter:
        """Create router with registry containing AppTypes."""
        registry = AppTypeRegistry()
        registry.register(create_manifest("soil_investigation", "Soil Investigation"))
        registry.register(create_manifest("structural_report", "Structural Report"))
        return AppTypeRouter(registry)

    def test_is_valid_true_for_registered(self, router: AppTypeRouter) -> None:
        """is_valid_app_type should return True for registered AppType."""
        assert router.is_valid_app_type("soil_investigation") is True
        assert router.is_valid_app_type("structural_report") is True

    def test_is_valid_false_for_unregistered(self, router: AppTypeRouter) -> None:
        """is_valid_app_type should return False for unregistered AppType."""
        assert router.is_valid_app_type("nonexistent") is False
        assert router.is_valid_app_type("") is False


class TestRouterWithRegistryChanges:
    """Tests for router behavior when registry changes."""

    def test_router_sees_newly_registered_apptype(self) -> None:
        """Router should see AppTypes registered after router creation."""
        registry = AppTypeRegistry()
        router = AppTypeRouter(registry)

        # Register after router created
        registry.register(create_manifest("new_app", "New App"))

        assert router.is_valid_app_type("new_app") is True
        assert router.set_current("new_app") is True

    def test_router_loses_current_if_apptype_unregistered(self) -> None:
        """If current AppType is unregistered, manifest lookup returns None."""
        registry = AppTypeRegistry()
        registry.register(create_manifest("test_app", "Test App"))
        router = AppTypeRouter(registry)
        router.set_current("test_app")

        # Unregister the current AppType
        registry.unregister("test_app")

        # Current ID is still set, but manifest lookup fails
        assert router.get_current_id() == "test_app"
        assert router.get_current_manifest() is None
        assert router.get_current_metadata() is None

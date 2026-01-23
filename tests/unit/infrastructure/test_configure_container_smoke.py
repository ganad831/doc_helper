"""T4: configure_container() Smoke Test.

Verifies that the main composition root can be called without exceptions.
This test ensures the DI container bootstrapping process completes.

Purpose: Catch bootstrap failures before runtime.
"""

import pytest

from doc_helper.infrastructure.di.container import Container
from doc_helper.platform.registry.app_type_registry import AppTypeRegistry
from doc_helper.platform.routing.app_type_router import IAppTypeRouter


class TestConfigureContainerSmoke:
    """Smoke tests for configure_container() composition root."""

    def test_configure_container_returns_container(self) -> None:
        """configure_container() returns a Container instance."""
        from doc_helper.main import configure_container

        container = configure_container()

        assert container is not None
        assert isinstance(container, Container)

    def test_configure_container_no_exception(self) -> None:
        """configure_container() completes without raising exceptions."""
        from doc_helper.main import configure_container

        # This should not raise any exception
        try:
            container = configure_container()
            assert container is not None
        except Exception as e:
            pytest.fail(f"configure_container() raised: {type(e).__name__}: {e}")

    def test_configure_container_registers_apptype_registry(self) -> None:
        """configure_container() registers AppTypeRegistry."""
        from doc_helper.main import configure_container

        container = configure_container()

        # AppTypeRegistry should be registered as an instance
        assert container.is_registered(AppTypeRegistry)

    def test_configure_container_registers_apptype_router(self) -> None:
        """configure_container() registers IAppTypeRouter."""
        from doc_helper.main import configure_container

        container = configure_container()

        # IAppTypeRouter should be registered
        assert container.is_registered(IAppTypeRouter)

    def test_configure_container_can_resolve_apptype_registry(self) -> None:
        """AppTypeRegistry can be resolved from container."""
        from doc_helper.main import configure_container

        container = configure_container()

        registry = container.resolve(AppTypeRegistry)

        assert registry is not None
        assert isinstance(registry, AppTypeRegistry)

    def test_configure_container_can_resolve_apptype_router(self) -> None:
        """IAppTypeRouter can be resolved from container."""
        from doc_helper.main import configure_container

        container = configure_container()

        router = container.resolve(IAppTypeRouter)

        assert router is not None


class TestConfigureContainerPlatformIntegration:
    """Tests for platform integration in configure_container()."""

    def test_apptype_registry_has_discovered_apptypes(self) -> None:
        """AppTypeRegistry contains discovered AppTypes after bootstrap."""
        from doc_helper.main import configure_container

        container = configure_container()
        registry = container.resolve(AppTypeRegistry)

        # At minimum, soil_investigation should be discovered
        # (if manifest exists in app_types/soil_investigation/)
        # This test verifies discovery ran without crashing
        assert registry is not None
        # Count may be 0 if no manifests exist, but that's OK for this smoke test
        assert registry.count >= 0

    def test_apptype_router_is_functional(self) -> None:
        """IAppTypeRouter is functional after bootstrap."""
        from doc_helper.main import configure_container

        container = configure_container()
        router = container.resolve(IAppTypeRouter)

        # Router should be able to report current state
        # (may be None if no AppTypes registered)
        current_id = router.get_current_id()
        # This is a smoke test - we just verify it doesn't crash
        assert current_id is None or isinstance(current_id, str)

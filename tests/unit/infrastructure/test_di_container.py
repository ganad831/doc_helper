"""Tests for DI container."""

import pytest

from doc_helper.infrastructure.di.container import Container


class IDummyService:
    """Dummy service interface for testing."""

    pass


class DummyService(IDummyService):
    """Dummy service implementation for testing."""

    def __init__(self, value: str = "default"):
        """Initialize with optional value."""
        self.value = value
        self.call_count = 0

    def do_something(self) -> str:
        """Test method."""
        self.call_count += 1
        return f"{self.value}_{self.call_count}"


class TestContainer:
    """Tests for Container class."""

    def test_register_singleton(self):
        """Test singleton registration."""
        container = Container()

        # Register singleton
        container.register_singleton(
            IDummyService,
            lambda: DummyService("test"),
        )

        # Resolve twice - should get same instance
        service1 = container.resolve(IDummyService)
        service2 = container.resolve(IDummyService)

        assert service1 is service2
        assert isinstance(service1, DummyService)
        assert service1.value == "test"

    def test_register_scoped(self):
        """Test scoped registration."""
        container = Container()

        # Register scoped
        container.register_scoped(
            IDummyService,
            lambda: DummyService("scoped"),
        )

        # Resolve twice in same scope - should get same instance
        service1 = container.resolve(IDummyService)
        service2 = container.resolve(IDummyService)
        assert service1 is service2

        # Begin new scope - should get new instance
        container.begin_scope()
        service3 = container.resolve(IDummyService)
        assert service3 is not service1
        assert isinstance(service3, DummyService)
        assert service3.value == "scoped"

    def test_register_transient(self):
        """Test transient registration."""
        container = Container()

        # Register transient
        container.register_transient(
            IDummyService,
            lambda: DummyService("transient"),
        )

        # Resolve twice - should get different instances
        service1 = container.resolve(IDummyService)
        service2 = container.resolve(IDummyService)

        assert service1 is not service2
        assert isinstance(service1, DummyService)
        assert isinstance(service2, DummyService)
        assert service1.value == "transient"
        assert service2.value == "transient"

    def test_register_instance(self):
        """Test instance registration."""
        container = Container()

        # Create instance
        instance = DummyService("instance")

        # Register instance
        container.register_instance(IDummyService, instance)

        # Resolve - should get same instance
        service = container.resolve(IDummyService)
        assert service is instance

    def test_resolve_unregistered_service(self):
        """Test resolving unregistered service raises KeyError."""
        container = Container()

        with pytest.raises(KeyError, match="Service.*not registered"):
            container.resolve(IDummyService)

    def test_begin_scope_clears_scoped_instances(self):
        """Test begin_scope clears scoped instances."""
        container = Container()

        # Register scoped service
        container.register_scoped(
            IDummyService,
            lambda: DummyService("scoped"),
        )

        # Resolve service
        service1 = container.resolve(IDummyService)

        # Begin new scope
        container.begin_scope()

        # Resolve again - should get new instance
        service2 = container.resolve(IDummyService)
        assert service2 is not service1

    def test_end_scope_clears_scoped_instances(self):
        """Test end_scope clears scoped instances."""
        container = Container()

        # Register scoped service
        container.register_scoped(
            IDummyService,
            lambda: DummyService("scoped"),
        )

        # Resolve service
        service1 = container.resolve(IDummyService)

        # End scope
        container.end_scope()

        # Resolve again - should get new instance
        service2 = container.resolve(IDummyService)
        assert service2 is not service1

    def test_is_registered(self):
        """Test is_registered check."""
        container = Container()

        # Not registered
        assert not container.is_registered(IDummyService)

        # Register
        container.register_singleton(
            IDummyService,
            lambda: DummyService(),
        )

        # Now registered
        assert container.is_registered(IDummyService)

    def test_clear_removes_all_registrations(self):
        """Test clear removes all registrations."""
        container = Container()

        # Register services
        container.register_singleton(
            IDummyService,
            lambda: DummyService(),
        )

        # Clear
        container.clear()

        # Should be unregistered
        assert not container.is_registered(IDummyService)

    def test_register_singleton_with_non_callable_factory_raises_error(self):
        """Test register_singleton with non-callable factory raises TypeError."""
        container = Container()

        with pytest.raises(TypeError, match="factory must be callable"):
            container.register_singleton(IDummyService, "not_callable")  # type: ignore

    def test_register_scoped_with_non_callable_factory_raises_error(self):
        """Test register_scoped with non-callable factory raises TypeError."""
        container = Container()

        with pytest.raises(TypeError, match="factory must be callable"):
            container.register_scoped(IDummyService, "not_callable")  # type: ignore

    def test_register_transient_with_non_callable_factory_raises_error(self):
        """Test register_transient with non-callable factory raises TypeError."""
        container = Container()

        with pytest.raises(TypeError, match="factory must be callable"):
            container.register_transient(IDummyService, "not_callable")  # type: ignore

    def test_singleton_factory_called_once(self):
        """Test singleton factory is called only once."""
        container = Container()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return DummyService(f"call_{call_count}")

        container.register_singleton(IDummyService, factory)

        # Resolve multiple times
        service1 = container.resolve(IDummyService)
        service2 = container.resolve(IDummyService)
        service3 = container.resolve(IDummyService)

        # Factory should be called only once
        assert call_count == 1
        assert service1 is service2 is service3

    def test_scoped_factory_called_once_per_scope(self):
        """Test scoped factory is called once per scope."""
        container = Container()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return DummyService(f"call_{call_count}")

        container.register_scoped(IDummyService, factory)

        # Resolve in first scope
        service1 = container.resolve(IDummyService)
        service2 = container.resolve(IDummyService)
        assert call_count == 1
        assert service1 is service2

        # New scope
        container.begin_scope()

        # Resolve in second scope
        service3 = container.resolve(IDummyService)
        assert call_count == 2
        assert service3 is not service1

    def test_transient_factory_called_every_time(self):
        """Test transient factory is called every time."""
        container = Container()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return DummyService(f"call_{call_count}")

        container.register_transient(IDummyService, factory)

        # Resolve multiple times
        service1 = container.resolve(IDummyService)
        service2 = container.resolve(IDummyService)
        service3 = container.resolve(IDummyService)

        # Factory should be called three times
        assert call_count == 3
        assert service1 is not service2
        assert service2 is not service3
        assert service1.value == "call_1"
        assert service2.value == "call_2"
        assert service3.value == "call_3"

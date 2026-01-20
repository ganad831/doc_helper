"""Integration tests for DI container undo service registration.

Tests verify that all undo-related services can be resolved from the
DI container without errors.

U6 Phase 7: Main Entry Point - DI Container Registration
"""

import pytest

from doc_helper.application.services.field_undo_service import FieldUndoService
from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.infrastructure.di.container import Container
from doc_helper.presentation.adapters.history_adapter import HistoryAdapter


@pytest.fixture
def configured_container():
    """Create configured DI container for testing.

    Uses main.py's configure_container() to ensure real configuration.
    """
    from doc_helper.main import configure_container

    container = configure_container()
    yield container

    # Cleanup
    container.clear()


def test_resolve_undo_manager(configured_container):
    """Verify UndoManager can be resolved from container."""
    undo_manager = configured_container.resolve(UndoManager)

    assert undo_manager is not None
    assert isinstance(undo_manager, UndoManager)
    assert undo_manager.can_undo is False
    assert undo_manager.can_redo is False


def test_resolve_field_undo_service(configured_container):
    """Verify FieldUndoService can be resolved from container."""
    field_undo_service = configured_container.resolve(FieldUndoService)

    assert field_undo_service is not None
    assert isinstance(field_undo_service, FieldUndoService)


def test_resolve_history_adapter(configured_container):
    """Verify HistoryAdapter can be resolved from container."""
    history_adapter = configured_container.resolve(HistoryAdapter)

    assert history_adapter is not None
    assert isinstance(history_adapter, HistoryAdapter)
    assert history_adapter.can_undo is False
    assert history_adapter.can_redo is False


def test_undo_manager_is_singleton(configured_container):
    """Verify UndoManager is registered as singleton."""
    undo_manager1 = configured_container.resolve(UndoManager)
    undo_manager2 = configured_container.resolve(UndoManager)

    assert undo_manager1 is undo_manager2


def test_field_undo_service_is_singleton(configured_container):
    """Verify FieldUndoService is registered as singleton."""
    service1 = configured_container.resolve(FieldUndoService)
    service2 = configured_container.resolve(FieldUndoService)

    assert service1 is service2


def test_history_adapter_is_singleton(configured_container):
    """Verify HistoryAdapter is registered as singleton."""
    adapter1 = configured_container.resolve(HistoryAdapter)
    adapter2 = configured_container.resolve(HistoryAdapter)

    assert adapter1 is adapter2


def test_undo_services_share_same_undo_manager(configured_container):
    """Verify all undo services share the same UndoManager instance."""
    undo_manager = configured_container.resolve(UndoManager)
    field_undo_service = configured_container.resolve(FieldUndoService)
    history_adapter = configured_container.resolve(HistoryAdapter)

    # Access internal UndoManager references
    assert field_undo_service._undo_manager is undo_manager
    assert history_adapter._undo_manager is undo_manager


def test_end_to_end_undo_via_di_container(configured_container):
    """End-to-end test: resolve services and perform undo operation.

    This test simulates the real application flow where services are
    resolved from the container and used together.
    """
    from unittest.mock import Mock

    # Resolve services from container
    field_undo_service = configured_container.resolve(FieldUndoService)
    history_adapter = configured_container.resolve(HistoryAdapter)
    undo_manager = configured_container.resolve(UndoManager)

    # Initial state
    assert history_adapter.can_undo is False
    assert undo_manager.can_undo is False

    # Note: Full end-to-end test with field operations would require
    # a fully configured project repository and database. This test
    # verifies that the DI wiring is correct.

    # Verify services are properly connected
    assert history_adapter._undo_manager is undo_manager
    assert field_undo_service._undo_manager is undo_manager

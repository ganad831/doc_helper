"""Unit tests for undo service DI registration.

RULES (unified_upgrade_plan_FINAL.md U6 Phase 3):
- Verify UndoManager resolves correctly
- Verify FieldUndoService resolves with correct dependencies
- Verify OverrideUndoService resolves with correct dependencies
- Verify HistoryAdapter resolves with correct dependencies
- Verify singleton lifecycle (same instance on multiple resolves)
"""

import pytest
from typing import Any

from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.application.services.field_undo_service import (
    FieldUndoService,
    IFieldService,
)
from doc_helper.application.services.override_undo_service import (
    OverrideUndoService,
    IOverrideService,
)
from doc_helper.presentation.adapters.history_adapter import HistoryAdapter
from doc_helper.infrastructure.di.container import Container, register_undo_services
from doc_helper.domain.common.result import Success, Failure, Result


class MockFieldService:
    """Mock implementation of IFieldService protocol."""

    def get_field_value(
        self,
        project_id: str,
        field_id: str,
    ) -> Result[Any, str]:
        """Mock get_field_value implementation."""
        return Success("mock_value")

    def set_field_value(
        self,
        project_id: str,
        field_id: str,
        value: Any,
    ) -> bool:
        """Mock set_field_value implementation."""
        return True


class MockOverrideService:
    """Mock implementation of IOverrideService protocol."""

    def get_override_state(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[str, str]:
        """Mock get_override_state implementation."""
        return Success("PENDING")

    def get_override_field_id(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[str, str]:
        """Mock get_override_field_id implementation."""
        return Success("field_1")

    def get_override_value(
        self,
        project_id: str,
        override_id: str,
    ) -> Result[Any, str]:
        """Mock get_override_value implementation."""
        return Success("override_value")

    def accept_override(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        """Mock accept_override implementation."""
        return True

    def reject_override(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        """Mock reject_override implementation."""
        return True

    def restore_override_to_pending(
        self,
        project_id: str,
        override_id: str,
    ) -> bool:
        """Mock restore_override_to_pending implementation."""
        return True


@pytest.fixture
def container():
    """Create fresh Container instance."""
    return Container()


@pytest.fixture
def mock_field_service():
    """Create MockFieldService instance."""
    return MockFieldService()


@pytest.fixture
def mock_override_service():
    """Create MockOverrideService instance."""
    return MockOverrideService()


def test_register_undo_services_succeeds(
    container, mock_field_service, mock_override_service
):
    """Test: register_undo_services completes without errors."""
    # Should not raise
    register_undo_services(container, mock_field_service, mock_override_service)


def test_undo_manager_resolves(container, mock_field_service, mock_override_service):
    """Test: UndoManager can be resolved."""
    register_undo_services(container, mock_field_service, mock_override_service)

    undo_manager = container.resolve(UndoManager)

    assert isinstance(undo_manager, UndoManager)
    assert undo_manager.can_undo is False
    assert undo_manager.can_redo is False


def test_field_undo_service_resolves(
    container, mock_field_service, mock_override_service
):
    """Test: FieldUndoService can be resolved with correct dependencies."""
    register_undo_services(container, mock_field_service, mock_override_service)

    field_undo_service = container.resolve(FieldUndoService)

    assert isinstance(field_undo_service, FieldUndoService)
    # Verify it has internal references (duck typing check)
    assert hasattr(field_undo_service, "_field_service")
    assert hasattr(field_undo_service, "_undo_manager")


def test_override_undo_service_resolves(
    container, mock_field_service, mock_override_service
):
    """Test: OverrideUndoService can be resolved with correct dependencies."""
    register_undo_services(container, mock_field_service, mock_override_service)

    override_undo_service = container.resolve(OverrideUndoService)

    assert isinstance(override_undo_service, OverrideUndoService)
    # Verify it has internal references
    assert hasattr(override_undo_service, "_override_service")
    assert hasattr(override_undo_service, "_field_service")
    assert hasattr(override_undo_service, "_undo_manager")


def test_history_adapter_resolves(
    container, mock_field_service, mock_override_service
):
    """Test: HistoryAdapter can be resolved with correct dependencies."""
    register_undo_services(container, mock_field_service, mock_override_service)

    history_adapter = container.resolve(HistoryAdapter)

    assert isinstance(history_adapter, HistoryAdapter)
    # Verify it has internal reference
    assert hasattr(history_adapter, "_undo_manager")


def test_undo_manager_is_singleton(
    container, mock_field_service, mock_override_service
):
    """Test: UndoManager is registered as singleton (same instance on multiple resolves)."""
    register_undo_services(container, mock_field_service, mock_override_service)

    undo_manager_1 = container.resolve(UndoManager)
    undo_manager_2 = container.resolve(UndoManager)

    # Should be exact same instance (singleton)
    assert undo_manager_1 is undo_manager_2


def test_field_undo_service_is_singleton(
    container, mock_field_service, mock_override_service
):
    """Test: FieldUndoService is registered as singleton."""
    register_undo_services(container, mock_field_service, mock_override_service)

    service_1 = container.resolve(FieldUndoService)
    service_2 = container.resolve(FieldUndoService)

    # Should be exact same instance (singleton)
    assert service_1 is service_2


def test_override_undo_service_is_singleton(
    container, mock_field_service, mock_override_service
):
    """Test: OverrideUndoService is registered as singleton."""
    register_undo_services(container, mock_field_service, mock_override_service)

    service_1 = container.resolve(OverrideUndoService)
    service_2 = container.resolve(OverrideUndoService)

    # Should be exact same instance (singleton)
    assert service_1 is service_2


def test_history_adapter_is_singleton(
    container, mock_field_service, mock_override_service
):
    """Test: HistoryAdapter is registered as singleton."""
    register_undo_services(container, mock_field_service, mock_override_service)

    adapter_1 = container.resolve(HistoryAdapter)
    adapter_2 = container.resolve(HistoryAdapter)

    # Should be exact same instance (singleton)
    assert adapter_1 is adapter_2


def test_shared_undo_manager_across_services(
    container, mock_field_service, mock_override_service
):
    """Test: All services share the same UndoManager instance."""
    register_undo_services(container, mock_field_service, mock_override_service)

    undo_manager = container.resolve(UndoManager)
    field_undo_service = container.resolve(FieldUndoService)
    override_undo_service = container.resolve(OverrideUndoService)
    history_adapter = container.resolve(HistoryAdapter)

    # All services should reference the exact same UndoManager instance
    assert field_undo_service._undo_manager is undo_manager
    assert override_undo_service._undo_manager is undo_manager
    assert history_adapter._undo_manager is undo_manager


def test_end_to_end_undo_flow(container, mock_field_service, mock_override_service):
    """Test: End-to-end undo flow through DI-resolved services."""
    register_undo_services(container, mock_field_service, mock_override_service)

    # Resolve services
    field_undo_service = container.resolve(FieldUndoService)
    undo_manager = container.resolve(UndoManager)
    history_adapter = container.resolve(HistoryAdapter)

    # Execute a field change command
    result = field_undo_service.set_field_value(
        project_id="project-1",
        field_id="field-1",
        new_value="new_value",
    )

    # Verify command executed
    assert result.is_success
    assert undo_manager.can_undo is True
    assert history_adapter.can_undo is True

    # Undo the command
    undo_result = history_adapter.undo()

    # Verify undo succeeded
    assert undo_result is True
    assert undo_manager.can_undo is False
    assert undo_manager.can_redo is True
    assert history_adapter.can_redo is True

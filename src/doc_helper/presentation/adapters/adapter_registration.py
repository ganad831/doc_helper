"""Presentation adapter registration for DI container.

This module registers presentation-layer adapters (HistoryAdapter, NavigationAdapter)
with the DI container. This is called from the presentation composition root,
NOT from infrastructure, to maintain Clean Architecture layer boundaries.

ARCHITECTURAL FIX:
- Presentation adapters are registered by Presentation layer (not Infrastructure)
- Infrastructure container.py does NOT import presentation modules
- This preserves: Infrastructure → Domain + Application only
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from doc_helper.infrastructure.di.container import Container


def register_history_adapter(container: "Container") -> None:
    """Register HistoryAdapter with the container.

    HistoryAdapter bridges UndoManager (Application) to Qt signals (Presentation).
    This registration is done in Presentation layer to avoid Infrastructure
    importing Presentation.

    Args:
        container: DI container instance

    Dependencies:
        - UndoManager must be registered before calling this function

    Example:
        # In presentation composition root:
        from doc_helper.presentation.adapters.adapter_registration import (
            register_history_adapter,
        )
        register_history_adapter(container)
    """
    from doc_helper.application.undo.undo_manager import UndoManager
    from doc_helper.presentation.adapters.history_adapter import HistoryAdapter

    container.register_singleton(
        HistoryAdapter,
        lambda: HistoryAdapter(
            undo_manager=container.resolve(UndoManager),
        ),
    )


def register_navigation_adapter(container: "Container") -> None:
    """Register NavigationAdapter with the container.

    NavigationAdapter bridges NavigationHistory (Application) to Qt signals (Presentation).
    This registration is done in Presentation layer to avoid Infrastructure
    importing Presentation.

    Args:
        container: DI container instance

    Dependencies:
        - NavigationHistory must be registered before calling this function

    Example:
        # In presentation composition root:
        from doc_helper.presentation.adapters.adapter_registration import (
            register_navigation_adapter,
        )
        register_navigation_adapter(container)
    """
    from doc_helper.application.navigation.navigation_history import NavigationHistory
    from doc_helper.presentation.adapters.navigation_adapter import NavigationAdapter

    container.register_singleton(
        NavigationAdapter,
        lambda: NavigationAdapter(
            navigation_history=container.resolve(NavigationHistory),
        ),
    )


def register_all_presentation_adapters(container: "Container") -> None:
    """Register all presentation adapters with the container.

    Convenience function to register all presentation-layer adapters at once.

    Args:
        container: DI container instance

    Dependencies:
        - UndoManager must be registered
        - NavigationHistory must be registered

    Example:
        # In presentation composition root:
        from doc_helper.presentation.adapters.adapter_registration import (
            register_all_presentation_adapters,
        )
        # After registering application services:
        register_all_presentation_adapters(container)
    """
    register_history_adapter(container)
    register_navigation_adapter(container)

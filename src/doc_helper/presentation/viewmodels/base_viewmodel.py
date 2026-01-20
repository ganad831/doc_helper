"""Base ViewModel for MVVM pattern.

Provides common functionality for all ViewModels including property change notification.
"""

from typing import Any, Callable, Optional


class BaseViewModel:
    """Base class for all ViewModels.

    ViewModels coordinate between Views (UI) and Application Layer.
    They hold presentation state and expose it via properties/methods.

    RULES:
    - ViewModels are stateful (hold presentation state)
    - ViewModels should NOT contain business logic
    - ViewModels coordinate calls to Application Layer
    - ViewModels provide data in formats suitable for UI

    Example:
        class MyViewModel(BaseViewModel):
            def __init__(self):
                super().__init__()
                self._data = None

            @property
            def data(self):
                return self._data

            def load_data(self):
                # Call application layer, update state
                self._data = "loaded"
                self.notify_change("data")
    """

    def __init__(self) -> None:
        """Initialize base ViewModel."""
        self._change_handlers: dict[str, list[Callable]] = {}

    def subscribe(self, property_name: str, handler: Callable) -> None:
        """Subscribe to property changes.

        Args:
            property_name: Name of property to observe
            handler: Callback function when property changes
        """
        if property_name not in self._change_handlers:
            self._change_handlers[property_name] = []
        self._change_handlers[property_name].append(handler)

    def unsubscribe(self, property_name: str, handler: Callable) -> None:
        """Unsubscribe from property changes.

        Args:
            property_name: Name of property
            handler: Callback function to remove
        """
        if property_name in self._change_handlers:
            if handler in self._change_handlers[property_name]:
                self._change_handlers[property_name].remove(handler)

    def notify_change(self, property_name: str) -> None:
        """Notify subscribers that a property has changed.

        Args:
            property_name: Name of property that changed
        """
        if property_name in self._change_handlers:
            for handler in self._change_handlers[property_name]:
                handler()

    def dispose(self) -> None:
        """Clean up resources.

        Override in subclasses to release resources.
        """
        self._change_handlers.clear()

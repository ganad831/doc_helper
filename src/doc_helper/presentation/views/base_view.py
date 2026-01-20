"""Base view class."""

from abc import ABC, abstractmethod
from typing import Optional

from PyQt6.QtWidgets import QWidget


class BaseView(ABC):
    """Base class for all views.

    Provides common functionality for view lifecycle and layout.

    v1 Implementation:
    - Basic window/widget setup
    - Lifecycle methods (initialize, show, hide, dispose)
    - Common styling

    Design:
    - Each view is either a window (QMainWindow/QDialog) or widget (QWidget)
    - Views bind to ViewModels via property change notifications
    - Views translate user interactions into ViewModel method calls
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize base view.

        Args:
            parent: Parent widget (None for root window)
        """
        self._parent = parent
        self._root: Optional[QWidget] = None
        self._is_initialized = False

    @abstractmethod
    def _build_ui(self) -> None:
        """Build the UI components.

        Subclasses must implement this to create their UI.
        """
        pass

    def initialize(self) -> None:
        """Initialize the view.

        Creates UI components and sets up bindings.
        """
        if not self._is_initialized:
            self._build_ui()
            self._is_initialized = True

    def show(self) -> None:
        """Show the view."""
        if not self._is_initialized:
            self.initialize()

        if self._root:
            self._root.show()

    def hide(self) -> None:
        """Hide the view."""
        if self._root:
            self._root.hide()

    def dispose(self) -> None:
        """Dispose of the view and clean up resources."""
        if self._root:
            self._root.close()
            self._root.deleteLater()
            self._root = None
        self._is_initialized = False

    def is_visible(self) -> bool:
        """Check if view is currently visible.

        Returns:
            True if visible
        """
        if not self._root:
            return False

        return self._root.isVisible()

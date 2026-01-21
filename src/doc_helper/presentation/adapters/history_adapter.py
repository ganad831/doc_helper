"""Qt bridge for UndoManager state changes.

RULES (unified_upgrade_plan_FINAL.md U6 Phase 2):
- Adapts UndoManager to PyQt6 signal/slot mechanism
- Emits signals when undo/redo state changes
- Provides methods for triggering undo/redo/clear operations

ADR-031: Undo History Persistence (UX Notes):
- Undo persistence is transparent to this adapter
- UndoManager handles serialization/deserialization on save/open
- Undo survives application restart (restored on project open)
- Undo survives save operations (NOT cleared on save)
- Undo cleared only on explicit project close
- Adapter signals (can_undo_changed, undo_text_changed) automatically reflect
  restored state after project open
- No special UX needed in presentation layer for persistence
"""

from PyQt6.QtCore import QObject, pyqtSignal

from doc_helper.application.undo.undo_manager import UndoManager


class HistoryAdapter(QObject):
    """Adapts UndoManager to Qt signal/slot mechanism.

    Bridges between framework-independent UndoManager and PyQt6 UI.
    Emits Qt signals when undo/redo state changes, allowing UI components
    to bind to these signals for enabling/disabling buttons, updating tooltips, etc.

    Example:
        undo_manager = UndoManager()
        adapter = HistoryAdapter(undo_manager)

        # Connect to signals
        adapter.can_undo_changed.connect(undo_button.setEnabled)
        adapter.can_redo_changed.connect(redo_button.setEnabled)
        adapter.undo_text_changed.connect(lambda text: undo_button.setToolTip(text))

        # Trigger operations
        adapter.undo()
        adapter.redo()
        adapter.clear()
    """

    # Signals for UI state updates
    can_undo_changed = pyqtSignal(bool)
    can_redo_changed = pyqtSignal(bool)
    undo_text_changed = pyqtSignal(str)
    redo_text_changed = pyqtSignal(str)

    def __init__(self, undo_manager: UndoManager):
        """Initialize HistoryAdapter.

        Args:
            undo_manager: The UndoManager instance to adapt
        """
        super().__init__()
        self._undo_manager = undo_manager

        # Subscribe to UndoManager state changes
        self._undo_manager.subscribe(self._on_state_changed)

    def _on_state_changed(self) -> None:
        """Emit Qt signals when undo state changes.

        Called by UndoManager whenever:
        - Command executed (undo stack grows, redo cleared)
        - Undo performed (undo stack shrinks, redo stack grows)
        - Redo performed (redo stack shrinks, undo stack grows)
        - Stacks cleared (on project close/open)
        """
        self.can_undo_changed.emit(self._undo_manager.can_undo)
        self.can_redo_changed.emit(self._undo_manager.can_redo)
        self.undo_text_changed.emit(self._undo_manager.undo_description or "")
        self.redo_text_changed.emit(self._undo_manager.redo_description or "")

    def undo(self) -> bool:
        """Trigger undo operation.

        Returns:
            True if undo succeeded, False if nothing to undo or undo failed

        Side Effects:
            - Calls UndoManager.undo()
            - Emits state change signals (can_undo_changed, can_redo_changed, etc.)
        """
        return self._undo_manager.undo()

    def redo(self) -> bool:
        """Trigger redo operation.

        Returns:
            True if redo succeeded, False if nothing to redo or redo failed

        Side Effects:
            - Calls UndoManager.redo()
            - Emits state change signals (can_undo_changed, can_redo_changed, etc.)
        """
        return self._undo_manager.redo()

    def clear(self) -> None:
        """Clear undo/redo stacks.

        Called on project close or project open.

        Side Effects:
            - Calls UndoManager.clear()
            - Emits state change signals (can_undo_changed=False, can_redo_changed=False)
        """
        self._undo_manager.clear()

    @property
    def can_undo(self) -> bool:
        """Check if undo is available.

        Returns:
            True if there are commands to undo
        """
        return self._undo_manager.can_undo

    @property
    def can_redo(self) -> bool:
        """Check if redo is available.

        Returns:
            True if there are commands to redo
        """
        return self._undo_manager.can_redo

    def dispose(self) -> None:
        """Dispose of the adapter.

        Unsubscribes from UndoManager to prevent memory leaks.
        Should be called when the adapter is no longer needed.
        """
        self._undo_manager.unsubscribe(self._on_state_changed)

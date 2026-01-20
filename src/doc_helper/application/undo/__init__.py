"""Undo/Redo system for Doc Helper.

RULES (unified_upgrade_plan.md v1.3, H2, ADR-021):
- UndoState DTOs are INTERNAL to Application layer
- UndoState DTOs must NEVER be imported in presentation/
- UndoState DTOs must NEVER be returned from queries
- This module uses COMMAND-BASED undo model (not snapshot)

Module Structure:
- undo_manager.py: UndoStack, RedoStack, execute/undo/redo
- undo_state_dto.py: UndoFieldState, UndoOverrideState (internal DTOs)
- undoable_command.py: UndoableCommand interface
- field_undo_command.py: SetFieldValueCommand
- override_undo_command.py: AcceptOverrideCommand, RejectOverrideCommand
"""

from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.application.undo.undoable_command import UndoableCommand
from doc_helper.application.undo.undo_state_dto import (
    UndoFieldState,
    UndoOverrideState,
)
from doc_helper.application.undo.field_undo_command import SetFieldValueCommand
from doc_helper.application.undo.override_undo_command import (
    AcceptOverrideCommand,
    RejectOverrideCommand,
)

__all__ = [
    "UndoManager",
    "UndoableCommand",
    "UndoFieldState",
    "UndoOverrideState",
    "SetFieldValueCommand",
    "AcceptOverrideCommand",
    "RejectOverrideCommand",
]

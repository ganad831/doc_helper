"""Persistence DTOs for undo history storage.

ADR-031: Undo History Persistence
RULES:
- INTERNAL to Application layer (NOT for presentation)
- Used ONLY for serialization/deserialization of undo history
- Contains minimal state needed to reconstruct undo commands
- No execution state, only reversal state (field ID, old/new values)
"""

from dataclasses import dataclass
from typing import Any, Literal

from doc_helper.application.undo.undo_state_dto import UndoFieldState, UndoOverrideState


@dataclass(frozen=True)
class UndoCommandPersistenceDTO:
    """Persistence DTO for a single undo command.

    ADR-031: Minimal persistence - contains only state needed to reverse operations.
    No execution state, runtime context, or intermediate computations.

    Wraps either UndoFieldState or UndoOverrideState for uniform storage.

    Attributes:
        command_type: Type of command ("field_value" or "override")
        state_data: Serializable state data (dict representation of state DTO)
        timestamp: ISO timestamp string (for ordering and debugging)

    Example:
        # Field value command
        cmd = UndoCommandPersistenceDTO(
            command_type="field_value",
            state_data={
                "field_id": "site_location",
                "previous_value": "123 Main St",
                "new_value": "456 Oak Ave",
                "was_formula_computed": False,
                "timestamp": "2026-01-21T10:00:00.000Z"
            },
            timestamp="2026-01-21T10:00:00.000Z"
        )
    """

    command_type: Literal["field_value", "override"]
    state_data: dict[str, Any]  # Serializable dict representation of state DTO
    timestamp: str  # ISO timestamp string

    @classmethod
    def from_field_state(cls, state: UndoFieldState) -> "UndoCommandPersistenceDTO":
        """Create persistence DTO from UndoFieldState.

        Args:
            state: UndoFieldState to persist

        Returns:
            UndoCommandPersistenceDTO wrapping field state

        Example:
            field_state = UndoFieldState.create(
                field_id="site_location",
                previous_value="123 Main St",
                new_value="456 Oak Ave"
            )
            persistence_dto = UndoCommandPersistenceDTO.from_field_state(field_state)
        """
        return cls(
            command_type="field_value",
            state_data={
                "field_id": state.field_id,
                "previous_value": state.previous_value,
                "new_value": state.new_value,
                "was_formula_computed": state.was_formula_computed,
                "timestamp": state.timestamp,
            },
            timestamp=state.timestamp,
        )

    @classmethod
    def from_override_state(
        cls, state: UndoOverrideState
    ) -> "UndoCommandPersistenceDTO":
        """Create persistence DTO from UndoOverrideState.

        Args:
            state: UndoOverrideState to persist

        Returns:
            UndoCommandPersistenceDTO wrapping override state

        Example:
            override_state = UndoOverrideState.create(
                override_id="override-123",
                field_id="soil_type",
                previous_override_state="PENDING",
                previous_field_value="Clay",
                accepted_value="Sand"
            )
            persistence_dto = UndoCommandPersistenceDTO.from_override_state(override_state)
        """
        return cls(
            command_type="override",
            state_data={
                "override_id": state.override_id,
                "field_id": state.field_id,
                "previous_override_state": state.previous_override_state,
                "previous_field_value": state.previous_field_value,
                "accepted_value": state.accepted_value,
                "affected_formula_fields": list(
                    state.affected_formula_fields
                ),  # Tuple → list for JSON
                "timestamp": state.timestamp,
            },
            timestamp=state.timestamp,
        )

    def to_field_state(self) -> UndoFieldState:
        """Reconstruct UndoFieldState from persistence DTO.

        ADR-031: Restoration is best-effort. If state_data is corrupted or
        incompatible, this will raise an exception (handled by caller).

        Returns:
            Reconstructed UndoFieldState

        Raises:
            ValueError: If command_type is not "field_value"
            KeyError: If required keys missing from state_data

        Example:
            persistence_dto = UndoCommandPersistenceDTO(...)
            field_state = persistence_dto.to_field_state()
        """
        if self.command_type != "field_value":
            raise ValueError(
                f"Cannot convert {self.command_type} to UndoFieldState"
            )

        return UndoFieldState(
            field_id=self.state_data["field_id"],
            previous_value=self.state_data["previous_value"],
            new_value=self.state_data["new_value"],
            was_formula_computed=self.state_data["was_formula_computed"],
            timestamp=self.state_data["timestamp"],
        )

    def to_override_state(self) -> UndoOverrideState:
        """Reconstruct UndoOverrideState from persistence DTO.

        ADR-031: Restoration is best-effort. If state_data is corrupted or
        incompatible, this will raise an exception (handled by caller).

        Returns:
            Reconstructed UndoOverrideState

        Raises:
            ValueError: If command_type is not "override"
            KeyError: If required keys missing from state_data

        Example:
            persistence_dto = UndoCommandPersistenceDTO(...)
            override_state = persistence_dto.to_override_state()
        """
        if self.command_type != "override":
            raise ValueError(
                f"Cannot convert {self.command_type} to UndoOverrideState"
            )

        return UndoOverrideState(
            override_id=self.state_data["override_id"],
            field_id=self.state_data["field_id"],
            previous_override_state=self.state_data["previous_override_state"],
            previous_field_value=self.state_data["previous_field_value"],
            accepted_value=self.state_data["accepted_value"],
            affected_formula_fields=tuple(
                self.state_data["affected_formula_fields"]
            ),  # List → tuple
            timestamp=self.state_data["timestamp"],
        )


@dataclass(frozen=True)
class UndoHistoryPersistenceDTO:
    """Persistence DTO for entire undo history (undo + redo stacks).

    ADR-031: Project-scoped storage of undo stack state.

    Attributes:
        project_id: Project this undo history belongs to
        undo_stack: List of undo commands (newest at end)
        redo_stack: List of redo commands (newest at end)
        max_stack_depth: Maximum stack depth (bounded stack)
        last_modified: ISO timestamp of last undo/redo operation

    Example:
        history = UndoHistoryPersistenceDTO(
            project_id="proj-123",
            undo_stack=[cmd1, cmd2, cmd3],
            redo_stack=[],
            max_stack_depth=50,
            last_modified="2026-01-21T10:00:00.000Z"
        )
    """

    project_id: str
    undo_stack: tuple[UndoCommandPersistenceDTO, ...]
    redo_stack: tuple[UndoCommandPersistenceDTO, ...]
    max_stack_depth: int  # Bounded stack depth (architectural policy: 50)
    last_modified: str  # ISO timestamp

    @classmethod
    def create_empty(cls, project_id: str, max_stack_depth: int = 50) -> "UndoHistoryPersistenceDTO":
        """Create empty undo history for new project.

        Args:
            project_id: Project identifier
            max_stack_depth: Maximum stack depth (default: 50)

        Returns:
            Empty UndoHistoryPersistenceDTO

        Example:
            empty_history = UndoHistoryPersistenceDTO.create_empty("proj-123")
        """
        from datetime import datetime

        return cls(
            project_id=project_id,
            undo_stack=(),
            redo_stack=(),
            max_stack_depth=max_stack_depth,
            last_modified=datetime.utcnow().isoformat(),
        )

    def is_empty(self) -> bool:
        """Check if both stacks are empty.

        Returns:
            True if no undo or redo commands exist

        Example:
            if history.is_empty():
                print("No undo history")
        """
        return len(self.undo_stack) == 0 and len(self.redo_stack) == 0

    def stack_size(self) -> int:
        """Get total size of both stacks.

        Returns:
            Combined size of undo and redo stacks

        Example:
            size = history.stack_size()
            print(f"Total operations: {size}")
        """
        return len(self.undo_stack) + len(self.redo_stack)

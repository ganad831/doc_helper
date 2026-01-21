"""Unit tests for UndoCommandPersistenceDTO and UndoHistoryPersistenceDTO.

ADR-031: Undo History Persistence
- Tests serialization/deserialization of undo state
- Tests round-trip conversion (state → persistence DTO → state)
- Tests validation and error handling
"""

from datetime import datetime

import pytest

from doc_helper.application.undo.undo_persistence_dto import (
    UndoCommandPersistenceDTO,
    UndoHistoryPersistenceDTO,
)
from doc_helper.application.undo.undo_state_dto import (
    UndoFieldState,
    UndoOverrideState,
)


class TestUndoCommandPersistenceDTO:
    """Tests for UndoCommandPersistenceDTO."""

    def test_from_field_state(self) -> None:
        """from_field_state should convert UndoFieldState to persistence DTO."""
        # Arrange
        field_state = UndoFieldState.create(
            field_id="site_location",
            previous_value="123 Main St",
            new_value="456 Oak Ave",
            was_formula_computed=False,
        )

        # Act
        persistence_dto = UndoCommandPersistenceDTO.from_field_state(field_state)

        # Assert
        assert persistence_dto.command_type == "field_value"
        assert persistence_dto.state_data["field_id"] == "site_location"
        assert persistence_dto.state_data["previous_value"] == "123 Main St"
        assert persistence_dto.state_data["new_value"] == "456 Oak Ave"
        assert persistence_dto.state_data["was_formula_computed"] is False
        assert "timestamp" in persistence_dto.state_data
        assert persistence_dto.timestamp == field_state.timestamp

    def test_from_override_state(self) -> None:
        """from_override_state should convert UndoOverrideState to persistence DTO."""
        # Arrange
        override_state = UndoOverrideState.create(
            override_id="override-123",
            field_id="soil_type",
            previous_override_state="PENDING",
            previous_field_value="Clay",
            accepted_value="Sand",
            affected_formula_fields=("bearing_capacity", "settlement"),
        )

        # Act
        persistence_dto = UndoCommandPersistenceDTO.from_override_state(override_state)

        # Assert
        assert persistence_dto.command_type == "override"
        assert persistence_dto.state_data["override_id"] == "override-123"
        assert persistence_dto.state_data["field_id"] == "soil_type"
        assert persistence_dto.state_data["previous_override_state"] == "PENDING"
        assert persistence_dto.state_data["previous_field_value"] == "Clay"
        assert persistence_dto.state_data["accepted_value"] == "Sand"
        assert persistence_dto.state_data["affected_formula_fields"] == [
            "bearing_capacity",
            "settlement",
        ]
        assert "timestamp" in persistence_dto.state_data
        assert persistence_dto.timestamp == override_state.timestamp

    def test_to_field_state_round_trip(self) -> None:
        """to_field_state should reconstruct original UndoFieldState."""
        # Arrange
        original_state = UndoFieldState.create(
            field_id="project_name",
            previous_value="Old Project",
            new_value="New Project",
            was_formula_computed=False,
        )

        # Act: Convert to persistence DTO and back
        persistence_dto = UndoCommandPersistenceDTO.from_field_state(original_state)
        reconstructed_state = persistence_dto.to_field_state()

        # Assert: Reconstructed state matches original
        assert reconstructed_state.field_id == original_state.field_id
        assert reconstructed_state.previous_value == original_state.previous_value
        assert reconstructed_state.new_value == original_state.new_value
        assert (
            reconstructed_state.was_formula_computed
            == original_state.was_formula_computed
        )
        assert reconstructed_state.timestamp == original_state.timestamp

    def test_to_override_state_round_trip(self) -> None:
        """to_override_state should reconstruct original UndoOverrideState."""
        # Arrange
        original_state = UndoOverrideState.create(
            override_id="override-456",
            field_id="foundation_depth",
            previous_override_state="ACCEPTED",
            previous_field_value="2.5",
            accepted_value="3.0",
            affected_formula_fields=("volume", "cost"),
        )

        # Act: Convert to persistence DTO and back
        persistence_dto = UndoCommandPersistenceDTO.from_override_state(original_state)
        reconstructed_state = persistence_dto.to_override_state()

        # Assert: Reconstructed state matches original
        assert reconstructed_state.override_id == original_state.override_id
        assert reconstructed_state.field_id == original_state.field_id
        assert (
            reconstructed_state.previous_override_state
            == original_state.previous_override_state
        )
        assert (
            reconstructed_state.previous_field_value
            == original_state.previous_field_value
        )
        assert reconstructed_state.accepted_value == original_state.accepted_value
        assert (
            reconstructed_state.affected_formula_fields
            == original_state.affected_formula_fields
        )
        assert reconstructed_state.timestamp == original_state.timestamp

    def test_to_field_state_rejects_override_type(self) -> None:
        """to_field_state should raise ValueError for override command type."""
        # Arrange
        override_state = UndoOverrideState.create(
            override_id="override-789",
            field_id="test_field",
            previous_override_state="PENDING",
            previous_field_value="A",
            accepted_value="B",
        )
        persistence_dto = UndoCommandPersistenceDTO.from_override_state(override_state)

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot convert override to UndoFieldState"):
            persistence_dto.to_field_state()

    def test_to_override_state_rejects_field_value_type(self) -> None:
        """to_override_state should raise ValueError for field_value command type."""
        # Arrange
        field_state = UndoFieldState.create(
            field_id="test_field",
            previous_value="X",
            new_value="Y",
        )
        persistence_dto = UndoCommandPersistenceDTO.from_field_state(field_state)

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot convert field_value to UndoOverrideState"):
            persistence_dto.to_override_state()


class TestUndoHistoryPersistenceDTO:
    """Tests for UndoHistoryPersistenceDTO."""

    @pytest.fixture
    def sample_undo_commands(self) -> tuple[UndoCommandPersistenceDTO, ...]:
        """Create sample undo commands."""
        cmd1 = UndoCommandPersistenceDTO.from_field_state(
            UndoFieldState.create(
                field_id="F1",
                previous_value="A",
                new_value="B",
            )
        )
        cmd2 = UndoCommandPersistenceDTO.from_field_state(
            UndoFieldState.create(
                field_id="F2",
                previous_value="C",
                new_value="D",
            )
        )
        return (cmd1, cmd2)

    @pytest.fixture
    def sample_redo_commands(self) -> tuple[UndoCommandPersistenceDTO, ...]:
        """Create sample redo commands."""
        cmd = UndoCommandPersistenceDTO.from_field_state(
            UndoFieldState.create(
                field_id="F3",
                previous_value="E",
                new_value="F",
            )
        )
        return (cmd,)

    def test_create_undo_history(
        self,
        sample_undo_commands: tuple[UndoCommandPersistenceDTO, ...],
        sample_redo_commands: tuple[UndoCommandPersistenceDTO, ...],
    ) -> None:
        """UndoHistoryPersistenceDTO should store undo/redo stacks."""
        # Arrange & Act
        history = UndoHistoryPersistenceDTO(
            project_id="proj-123",
            undo_stack=sample_undo_commands,
            redo_stack=sample_redo_commands,
            max_stack_depth=50,
            last_modified="2026-01-21T10:00:00.000Z",
        )

        # Assert
        assert history.project_id == "proj-123"
        assert len(history.undo_stack) == 2
        assert len(history.redo_stack) == 1
        assert history.max_stack_depth == 50
        assert history.last_modified == "2026-01-21T10:00:00.000Z"

    def test_create_empty_undo_history(self) -> None:
        """create_empty should create undo history with empty stacks."""
        # Act
        history = UndoHistoryPersistenceDTO.create_empty(
            project_id="proj-456", max_stack_depth=100
        )

        # Assert
        assert history.project_id == "proj-456"
        assert len(history.undo_stack) == 0
        assert len(history.redo_stack) == 0
        assert history.max_stack_depth == 100
        assert history.last_modified  # Should have timestamp

    def test_is_empty_with_empty_stacks(self) -> None:
        """is_empty should return True when both stacks are empty."""
        # Arrange
        history = UndoHistoryPersistenceDTO.create_empty(project_id="proj-789")

        # Act & Assert
        assert history.is_empty() is True

    def test_is_empty_with_undo_stack(
        self, sample_undo_commands: tuple[UndoCommandPersistenceDTO, ...]
    ) -> None:
        """is_empty should return False when undo stack has commands."""
        # Arrange
        history = UndoHistoryPersistenceDTO(
            project_id="proj-123",
            undo_stack=sample_undo_commands,
            redo_stack=(),
            max_stack_depth=50,
            last_modified=datetime.utcnow().isoformat(),
        )

        # Act & Assert
        assert history.is_empty() is False

    def test_is_empty_with_redo_stack(
        self, sample_redo_commands: tuple[UndoCommandPersistenceDTO, ...]
    ) -> None:
        """is_empty should return False when redo stack has commands."""
        # Arrange
        history = UndoHistoryPersistenceDTO(
            project_id="proj-123",
            undo_stack=(),
            redo_stack=sample_redo_commands,
            max_stack_depth=50,
            last_modified=datetime.utcnow().isoformat(),
        )

        # Act & Assert
        assert history.is_empty() is False

    def test_stack_size(
        self,
        sample_undo_commands: tuple[UndoCommandPersistenceDTO, ...],
        sample_redo_commands: tuple[UndoCommandPersistenceDTO, ...],
    ) -> None:
        """stack_size should return combined size of both stacks."""
        # Arrange
        history = UndoHistoryPersistenceDTO(
            project_id="proj-123",
            undo_stack=sample_undo_commands,  # 2 commands
            redo_stack=sample_redo_commands,  # 1 command
            max_stack_depth=50,
            last_modified=datetime.utcnow().isoformat(),
        )

        # Act & Assert
        assert history.stack_size() == 3  # 2 + 1

    def test_stack_size_empty(self) -> None:
        """stack_size should return 0 for empty history."""
        # Arrange
        history = UndoHistoryPersistenceDTO.create_empty(project_id="proj-456")

        # Act & Assert
        assert history.stack_size() == 0

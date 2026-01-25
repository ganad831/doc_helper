"""Unit tests for ProjectViewModel undo/redo integration.

RULES (unified_upgrade_plan_FINAL.md U6 Phase 4):
- Test ViewModel undo/redo methods
- Test property delegation (can_undo, can_redo)
- Test signal subscriptions
- Test undo stack cleared on project open/close
- Test undo stack NOT cleared on save

Architecture Enforcement: Updated to use ProjectUseCases (not facades).
"""

import pytest
from typing import Any
from unittest.mock import MagicMock, Mock
from uuid import uuid4

from doc_helper.application.usecases.project_usecases import ProjectUseCases
from doc_helper.application.dto import ProjectDTO, EntityDefinitionDTO
from doc_helper.application.services.field_undo_service import FieldUndoService
from doc_helper.domain.common.result import Success, Failure, Result
from doc_helper.presentation.adapters.history_adapter import HistoryAdapter
from doc_helper.presentation.viewmodels.project_viewmodel import ProjectViewModel


# Test constants
TEST_PROJECT_UUID = uuid4()


@pytest.fixture
def mock_project_usecases():
    """Create mock ProjectUseCases."""
    usecases = Mock(spec=ProjectUseCases)
    # Default successful get_project
    usecases.get_project.return_value = Success(None)
    usecases.save_project.return_value = Success(None)
    usecases.export_project.return_value = Success(None)
    return usecases


@pytest.fixture
def mock_validation_service():
    """Create mock ValidationService."""
    return Mock()


@pytest.fixture
def mock_formula_service():
    """Create mock FormulaService."""
    return Mock()


@pytest.fixture
def mock_control_service():
    """Create mock ControlService."""
    return Mock()


@pytest.fixture
def mock_field_undo_service():
    """Create mock FieldUndoService."""
    service = Mock(spec=FieldUndoService)
    service.set_field_value.return_value = Success(None)
    return service


@pytest.fixture
def mock_history_adapter():
    """Create mock HistoryAdapter."""
    adapter = Mock(spec=HistoryAdapter)
    adapter.can_undo = False
    adapter.can_redo = False
    adapter.undo.return_value = True
    adapter.redo.return_value = True
    adapter.clear.return_value = None
    adapter.dispose.return_value = None
    # Mock signal connections
    adapter.can_undo_changed = Mock()
    adapter.can_redo_changed = Mock()
    adapter.can_undo_changed.connect = Mock()
    adapter.can_redo_changed.connect = Mock()
    adapter.can_undo_changed.disconnect = Mock()
    adapter.can_redo_changed.disconnect = Mock()
    return adapter


@pytest.fixture
def mock_navigation_adapter():
    """Create mock NavigationAdapter."""
    adapter = Mock()
    adapter.navigate_to_entity = Mock()
    adapter.go_back = Mock()
    adapter.go_forward = Mock()
    adapter.can_go_back = False
    adapter.can_go_forward = False
    return adapter


@pytest.fixture
def mock_validation_mapper():
    """Create mock ValidationMapper for Phase H-3."""
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def viewmodel(
    mock_project_usecases,
    mock_validation_service,
    mock_formula_service,
    mock_control_service,
    mock_field_undo_service,
    mock_history_adapter,
    mock_navigation_adapter,
    mock_validation_mapper,
):
    """Create ProjectViewModel instance."""
    return ProjectViewModel(
        project_usecases=mock_project_usecases,
        validation_service=mock_validation_service,
        formula_service=mock_formula_service,
        control_service=mock_control_service,
        field_undo_service=mock_field_undo_service,
        history_adapter=mock_history_adapter,
        navigation_adapter=mock_navigation_adapter,
        validation_mapper=mock_validation_mapper,
    )


def test_create_viewmodel(viewmodel):
    """Test: ProjectViewModel instance created successfully."""
    assert isinstance(viewmodel, ProjectViewModel)


def test_viewmodel_subscribes_to_history_adapter_signals(mock_history_adapter, viewmodel):
    """Test: ViewModel subscribes to HistoryAdapter signals on creation."""
    # Verify can_undo_changed signal subscription
    mock_history_adapter.can_undo_changed.connect.assert_called_once()

    # Verify can_redo_changed signal subscription
    mock_history_adapter.can_redo_changed.connect.assert_called_once()


def test_can_undo_delegates_to_history_adapter(viewmodel, mock_history_adapter):
    """Test: can_undo property delegates to HistoryAdapter."""
    # Mock HistoryAdapter returns False
    mock_history_adapter.can_undo = False
    assert viewmodel.can_undo is False

    # Mock HistoryAdapter returns True
    mock_history_adapter.can_undo = True
    assert viewmodel.can_undo is True


def test_can_redo_delegates_to_history_adapter(viewmodel, mock_history_adapter):
    """Test: can_redo property delegates to HistoryAdapter."""
    # Mock HistoryAdapter returns False
    mock_history_adapter.can_redo = False
    assert viewmodel.can_redo is False

    # Mock HistoryAdapter returns True
    mock_history_adapter.can_redo = True
    assert viewmodel.can_redo is True


def test_undo_forwards_to_history_adapter(viewmodel, mock_history_adapter):
    """Test: undo() method forwards to HistoryAdapter.undo()."""
    # Mock successful undo
    mock_history_adapter.undo.return_value = True

    result = viewmodel.undo()

    # Verify HistoryAdapter.undo() was called
    mock_history_adapter.undo.assert_called_once()
    assert result is True


def test_redo_forwards_to_history_adapter(viewmodel, mock_history_adapter):
    """Test: redo() method forwards to HistoryAdapter.redo()."""
    # Mock successful redo
    mock_history_adapter.redo.return_value = True

    result = viewmodel.redo()

    # Verify HistoryAdapter.redo() was called
    mock_history_adapter.redo.assert_called_once()
    assert result is True


def test_update_field_uses_field_undo_service(
    viewmodel, mock_field_undo_service, mock_project_usecases
):
    """Test: update_field() uses FieldUndoService instead of UpdateFieldCommand."""
    # Setup: Load project first
    project_dto = ProjectDTO(
        id=str(TEST_PROJECT_UUID),
        name="Test Project",
        description=None,
        file_path=None,
        entity_definition_id="entity-1",
        app_type_id="soil_investigation",  # v2 PHASE 4
        field_count=0,
        is_saved=True,
    )
    mock_project_usecases.get_project.return_value = Success(project_dto)

    # PHASE 6C: load_project now takes string ID
    project_id = str(TEST_PROJECT_UUID)
    entity_def = EntityDefinitionDTO(
        id="entity-1",
        name="Test Entity",
        description=None,
        field_count=0,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(),
    )

    viewmodel.load_project(project_id, entity_def)

    # Mock successful field update
    mock_field_undo_service.set_field_value.return_value = Success(None)

    # Update field - PHASE 6C: field_id is now a string
    field_id = "field-1"
    result = viewmodel.update_field(field_id, "new_value")

    # Verify FieldUndoService was called (NOT UpdateFieldCommand)
    mock_field_undo_service.set_field_value.assert_called_once_with(
        project_id=str(TEST_PROJECT_UUID),
        field_id=field_id,  # Now a string
        new_value="new_value",
    )
    assert result is True


def test_load_project_clears_undo_stack(
    viewmodel, mock_history_adapter, mock_project_usecases
):
    """Test: load_project() clears undo/redo stacks."""
    # Mock successful project load
    project_dto = ProjectDTO(
        id=str(TEST_PROJECT_UUID),
        name="Test Project",
        description=None,
        file_path=None,
        entity_definition_id="entity-1",
        app_type_id="soil_investigation",  # v2 PHASE 4
        field_count=0,
        is_saved=True,
    )
    mock_project_usecases.get_project.return_value = Success(project_dto)

    # PHASE 6C: load_project now takes string ID
    project_id = str(TEST_PROJECT_UUID)
    entity_def = EntityDefinitionDTO(
        id="entity-1",
        name="Test Entity",
        description=None,
        field_count=0,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(),
    )

    viewmodel.load_project(project_id, entity_def)

    # Verify HistoryAdapter.clear() was called
    mock_history_adapter.clear.assert_called_once()


def test_close_project_clears_undo_stack(viewmodel, mock_history_adapter):
    """Test: close_project() clears undo/redo stacks."""
    viewmodel.close_project()

    # Verify HistoryAdapter.clear() was called
    mock_history_adapter.clear.assert_called_once()


def test_save_project_does_not_clear_undo_stack(
    viewmodel, mock_history_adapter, mock_project_usecases
):
    """Test: save_project() does NOT clear undo/redo stacks."""
    # Setup: Load project first
    project_dto = ProjectDTO(
        id=str(TEST_PROJECT_UUID),
        name="Test Project",
        description=None,
        file_path=None,
        entity_definition_id="entity-1",
        app_type_id="soil_investigation",  # v2 PHASE 4
        field_count=0,
        is_saved=True,
    )
    mock_project_usecases.get_project.return_value = Success(project_dto)

    # PHASE 6C: load_project now takes string ID
    project_id = str(TEST_PROJECT_UUID)
    entity_def = EntityDefinitionDTO(
        id="entity-1",
        name="Test Entity",
        description=None,
        field_count=0,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(),
    )

    viewmodel.load_project(project_id, entity_def)

    # Reset clear() call count (called by load_project)
    mock_history_adapter.clear.reset_mock()

    # Mock successful save
    mock_project_usecases.save_project.return_value = Success(None)

    # Save project
    viewmodel.save_project()

    # Verify HistoryAdapter.clear() was NOT called
    mock_history_adapter.clear.assert_not_called()


def test_dispose_unsubscribes_from_history_adapter(viewmodel, mock_history_adapter):
    """Test: dispose() unsubscribes from HistoryAdapter signals."""
    viewmodel.dispose()

    # Verify can_undo_changed signal disconnection
    mock_history_adapter.can_undo_changed.disconnect.assert_called_once()

    # Verify can_redo_changed signal disconnection
    mock_history_adapter.can_redo_changed.disconnect.assert_called_once()

    # Verify HistoryAdapter disposal
    mock_history_adapter.dispose.assert_called_once()


def test_undo_reloads_project_dto(
    viewmodel, mock_history_adapter, mock_project_usecases
):
    """Test: undo() reloads project DTO after successful undo."""
    # Setup: Load project first
    project_dto = ProjectDTO(
        id=str(TEST_PROJECT_UUID),
        name="Test Project",
        description=None,
        file_path=None,
        entity_definition_id="entity-1",
        app_type_id="soil_investigation",  # v2 PHASE 4
        field_count=1,
        is_saved=True,
    )
    mock_project_usecases.get_project.return_value = Success(project_dto)

    # PHASE 6C: load_project now takes string ID
    project_id = str(TEST_PROJECT_UUID)
    entity_def = EntityDefinitionDTO(
        id="entity-1",
        name="Test Entity",
        description=None,
        field_count=0,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(),
    )

    viewmodel.load_project(project_id, entity_def)

    # Reset usecases call count
    mock_project_usecases.get_project.reset_mock()

    # Mock successful undo
    mock_history_adapter.undo.return_value = True

    # Mock reloaded project DTO (with undone value)
    updated_project_dto = ProjectDTO(
        id=str(TEST_PROJECT_UUID),
        name="Test Project",
        description=None,
        file_path=None,
        entity_definition_id="entity-1",
        app_type_id="soil_investigation",  # v2 PHASE 4
        field_count=1,
        is_saved=True,
    )
    mock_project_usecases.get_project.return_value = Success(updated_project_dto)

    # Undo
    result = viewmodel.undo()

    # Verify project was reloaded
    assert result is True
    mock_project_usecases.get_project.assert_called_once()
    assert viewmodel.current_project == updated_project_dto


def test_redo_reloads_project_dto(
    viewmodel, mock_history_adapter, mock_project_usecases
):
    """Test: redo() reloads project DTO after successful redo."""
    # Setup: Load project first
    project_dto = ProjectDTO(
        id=str(TEST_PROJECT_UUID),
        name="Test Project",
        description=None,
        file_path=None,
        entity_definition_id="entity-1",
        app_type_id="soil_investigation",  # v2 PHASE 4
        field_count=1,
        is_saved=True,
    )
    mock_project_usecases.get_project.return_value = Success(project_dto)

    # PHASE 6C: load_project now takes string ID
    project_id = str(TEST_PROJECT_UUID)
    entity_def = EntityDefinitionDTO(
        id="entity-1",
        name="Test Entity",
        description=None,
        field_count=0,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(),
    )

    viewmodel.load_project(project_id, entity_def)

    # Reset usecases call count
    mock_project_usecases.get_project.reset_mock()

    # Mock successful redo
    mock_history_adapter.redo.return_value = True

    # Mock reloaded project DTO (with redone value)
    updated_project_dto = ProjectDTO(
        id=str(TEST_PROJECT_UUID),
        name="Test Project",
        description=None,
        file_path=None,
        entity_definition_id="entity-1",
        app_type_id="soil_investigation",  # v2 PHASE 4
        field_count=1,
        is_saved=True,
    )
    mock_project_usecases.get_project.return_value = Success(updated_project_dto)

    # Redo
    result = viewmodel.redo()

    # Verify project was reloaded
    assert result is True
    mock_project_usecases.get_project.assert_called_once()
    assert viewmodel.current_project == updated_project_dto

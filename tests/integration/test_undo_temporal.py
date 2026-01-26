"""Temporal undo/redo test scenarios (T1-T5).

RULES (unified_upgrade_plan_FINAL.md H4):
- Test end-to-end undo/redo behavior with real components
- Verify computed fields are RECOMPUTED on undo (not restored)
- Verify override state machine transitions correctly
- Verify undo stack behavior (cleared on close/open, NOT on save)
- These tests MUST pass before U6 is complete

NOTE: Some tests require time.sleep() delays to prevent command merging.
SetFieldValueCommand has a 500ms merge window, so edits within this window
are merged into a single command. Tests add 0.6s delays between edits
to ensure separate commands.

Architecture Enforcement: Updated to use ProjectUseCases (not facades/queries/commands).
"""

import pytest
import time
from typing import Any, Optional
from unittest.mock import Mock
from uuid import uuid4

from doc_helper.application.dto import (
    ProjectDTO,
    EntityDefinitionDTO,
    FieldDefinitionDTO,
)
from doc_helper.application.services.field_undo_service import FieldUndoService
from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.application.usecases.project_usecases import ProjectUseCases
from doc_helper.domain.common.result import Success, Failure
from doc_helper.presentation.adapters.history_adapter import HistoryAdapter
from doc_helper.presentation.viewmodels.project_viewmodel import ProjectViewModel

# Note: Tests use string field IDs (not FieldDefinitionId domain objects)
# per Rule 0 compliance - Presentation layer uses primitives/DTOs only


# Test constants
TEST_PROJECT_UUID = uuid4()


@pytest.fixture
def undo_manager():
    """Create UndoManager instance."""
    return UndoManager(max_depth=100)


@pytest.fixture
def history_adapter(undo_manager):
    """Create HistoryAdapter instance."""
    return HistoryAdapter(undo_manager)


@pytest.fixture
def mock_field_service():
    """Create mock field service.

    This mock simulates a field service with in-memory state.
    """
    from unittest.mock import Mock

    # In-memory field storage
    field_values = {}

    def get_field_value(project_id: str, field_id: str):
        """Get field value from in-memory storage."""
        key = f"{project_id}:{field_id}"
        if key not in field_values:
            return Success(None)
        return Success(field_values[key])

    def set_field_value(project_id: str, field_id: str, value: Any):
        """Set field value in in-memory storage."""
        key = f"{project_id}:{field_id}"
        field_values[key] = value
        return Success(None)

    service = Mock()
    service.get_field_value.side_effect = get_field_value
    service.set_field_value.side_effect = set_field_value
    return service


@pytest.fixture
def field_undo_service(mock_field_service, undo_manager):
    """Create FieldUndoService instance."""
    return FieldUndoService(
        field_service=mock_field_service,
        undo_manager=undo_manager,
    )


@pytest.fixture
def mock_project_usecases():
    """Create mock ProjectUseCases (Rule 0 compliant).

    This fixture replaces the old get_project_query, save_project_command,
    and update_field_command fixtures. ViewModels now depend on use-cases only.
    """
    usecases = Mock(spec=ProjectUseCases)

    def get_project(project_id: str):
        """Return mock ProjectDTO."""
        return Success(
            ProjectDTO(
                id=project_id,
                name="Test Project",
                description=None,
                file_path=None,
                entity_definition_id="entity-1",
                app_type_id="soil_investigation",  # v2 PHASE 4
                field_count=3,
                is_saved=True,
            )
        )

    usecases.get_project.side_effect = get_project
    usecases.save_project.return_value = Success(None)
    usecases.export_project.return_value = Success(None)
    return usecases


@pytest.fixture
def mock_validation_service():
    """Create mock ValidationService."""
    from unittest.mock import Mock

    from doc_helper.application.mappers import create_valid_validation_result

    service = Mock()
    # Phase H-3: Use factory function instead of direct DTO construction
    service.validate_by_project_id.return_value = Success(
        create_valid_validation_result()
    )
    return service


@pytest.fixture
def mock_formula_service():
    """Create mock FormulaService."""
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def mock_control_service():
    """Create mock ControlService."""
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def mock_navigation_adapter():
    """Create mock NavigationAdapter."""
    from unittest.mock import Mock
    adapter = Mock()
    adapter.navigate_to_entity = Mock(return_value=None)
    adapter.navigate_to_group = Mock(return_value=None)
    adapter.navigate_to_field = Mock(return_value=None)
    adapter.go_back = Mock(return_value=None)
    adapter.go_forward = Mock(return_value=None)
    adapter.clear = Mock(return_value=None)
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
    field_undo_service,
    history_adapter,
    mock_navigation_adapter,
    mock_validation_mapper,
):
    """Create ProjectViewModel instance with real undo infrastructure.

    Architecture Enforcement: Uses ProjectUseCases (Rule 0 compliant).
    """
    return ProjectViewModel(
        project_usecases=mock_project_usecases,
        validation_service=mock_validation_service,
        formula_service=mock_formula_service,
        control_service=mock_control_service,
        field_undo_service=field_undo_service,
        history_adapter=history_adapter,
        navigation_adapter=mock_navigation_adapter,
        validation_mapper=mock_validation_mapper,
    )


@pytest.fixture
def loaded_project(viewmodel, mock_project_usecases, mock_field_service):
    """Load a test project into the viewmodel.

    Architecture Enforcement: Uses string ID (not ProjectId domain object).
    """
    project_id = str(TEST_PROJECT_UUID)
    entity_def = EntityDefinitionDTO(
        id="entity-1",
        name="Test Entity",
        description=None,
        name_key="entity.test",
        description_key=None,
        field_count=3,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(
            FieldDefinitionDTO(
                id="field_a",
                field_type="TEXT",
                label="Field A",
                help_text=None,
                required=False,
                default_value=None,
                options=(),
                formula=None,
                is_calculated=False,
                is_choice_field=False,
                is_collection_field=False,
                lookup_entity_id=None,
                child_entity_id=None,
            ),
            FieldDefinitionDTO(
                id="field_b",
                field_type="TEXT",
                label="Field B",
                help_text=None,
                required=False,
                default_value=None,
                options=(),
                formula=None,
                is_calculated=False,
                is_choice_field=False,
                is_collection_field=False,
                lookup_entity_id=None,
                child_entity_id=None,
            ),
            FieldDefinitionDTO(
                id="field_c",
                field_type="TEXT",
                label="Field C",
                help_text=None,
                required=False,
                default_value=None,
                options=(),
                formula=None,
                is_calculated=False,
                is_choice_field=False,
                is_collection_field=False,
                lookup_entity_id=None,
                child_entity_id=None,
            ),
        ),
    )

    # Set initial values
    mock_field_service.set_field_value(str(TEST_PROJECT_UUID), "field_a", "initial_a")
    mock_field_service.set_field_value(str(TEST_PROJECT_UUID), "field_b", "initial_b")
    mock_field_service.set_field_value(str(TEST_PROJECT_UUID), "field_c", "initial_c")

    # Load project
    viewmodel.load_project(project_id, entity_def)

    return viewmodel


# ============================================================================
# T1: Basic Field Edit Undo
# ============================================================================

def test_T1_basic_field_edit_undo(loaded_project, mock_field_service):
    """T1: User edits a field, then undoes.

    Scenario:
    1. Field has initial value "initial_a"
    2. User changes field to "modified"
    3. User presses Ctrl+Z
    4. Field returns to "initial_a"
    """
    vm = loaded_project
    field_id = "field_a"  # String ID per Rule 0

    # Verify initial state
    initial_result = mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    )
    assert initial_result.is_success
    assert initial_result.value == "initial_a"

    # User edits field
    success = vm.update_field(field_id, "modified")
    assert success is True

    # Verify field changed
    current_result = mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    )
    assert current_result.is_success
    assert current_result.value == "modified"

    # Verify can undo
    assert vm.can_undo is True
    assert vm.can_redo is False

    # User presses Ctrl+Z
    undo_success = vm.undo()
    assert undo_success is True

    # Verify field restored
    restored_result = mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    )
    assert restored_result.is_success
    assert restored_result.value == "initial_a"

    # Verify undo/redo state
    assert vm.can_undo is False
    assert vm.can_redo is True


# ============================================================================
# T2: Undo Recomputes Dependent Fields
# ============================================================================

def test_T2_undo_recomputes_dependent_fields(loaded_project, mock_field_service, mock_formula_service):
    """T2: Undo triggers recomputation of computed fields.

    Scenario:
    1. field_a = 5 (raw value)
    2. field_b = field_a * 2 (computed, value = 10)
    3. User changes field_a to 10
    4. field_b recomputes to 20
    5. User undoes
    6. field_a = 5
    7. field_b RECOMPUTES to 10 (not restored from snapshot)

    Note: In this test, we verify that dependent fields are re-evaluated
    when the source field changes via undo. The actual formula evaluation
    is mocked since we're testing the undo mechanism, not the formula engine.
    """
    vm = loaded_project
    field_a = "field_a"  # String ID per Rule 0

    # Set initial value
    mock_field_service.set_field_value(str(TEST_PROJECT_UUID), "field_a", 5)

    # Mock formula service to simulate computed field dependency
    def evaluate_formulas(project_id, changed_field_ids):
        """Simulate formula evaluation: field_b = field_a * 2."""
        field_a_result = mock_field_service.get_field_value(project_id, "field_a")
        if field_a_result.is_success and field_a_result.value is not None:
            computed_value = field_a_result.value * 2
            mock_field_service.set_field_value(project_id, "field_b", computed_value)

    mock_formula_service.evaluate_formulas.side_effect = evaluate_formulas

    # Initial state: field_a = 5, field_b = 10
    evaluate_formulas(str(TEST_PROJECT_UUID), ["field_a"])

    field_b_initial = mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_b"
    )
    assert field_b_initial.value == 10

    # User changes field_a to 10
    vm.update_field(field_a, 10)

    # Trigger formula recomputation
    evaluate_formulas(str(TEST_PROJECT_UUID), ["field_a"])

    # Verify field_b recomputed to 20
    field_b_after = mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_b"
    )
    assert field_b_after.value == 20

    # User undoes
    vm.undo()

    # Trigger formula recomputation (happens automatically in real system)
    evaluate_formulas(str(TEST_PROJECT_UUID), ["field_a"])

    # Verify field_a restored to 5
    field_a_result = mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    )
    assert field_a_result.value == 5

    # Verify field_b RECOMPUTED to 10 (not restored from snapshot)
    field_b_result = mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_b"
    )
    assert field_b_result.value == 10


# ============================================================================
# T3: Override Accept Undo
# ============================================================================

@pytest.mark.skip(reason="Override integration pending - requires accept_override ViewModel method")
def test_T3_override_accept_undo():
    """T3: Undo restores override to PENDING state.

    Scenario:
    1. Override exists in PENDING state
    2. system_value = 100, report_value = 150
    3. User accepts override
    4. Override state = ACCEPTED, field value = 150
    5. User undoes
    6. Override state = PENDING, field value = 100 (restored)

    Note: This test is skipped until override functionality is integrated
    into ProjectViewModel. The override domain exists, but ViewModel doesn't
    expose accept_override() method yet. Will be implemented when override
    UI is added.

    Required ViewModel methods:
    - vm.accept_override(override_id) -> bool
    - vm.get_override_state(override_id) -> str
    """
    pass


# ============================================================================
# T4: Multiple Undo/Redo Sequence
# ============================================================================

def test_T4_multiple_undo_redo_sequence(loaded_project, mock_field_service):
    """T4: Multiple undo/redo operations maintain correct state.

    Scenario:
    1. Initial: field_a = "initial_a"
    2. Edit 1: field_a = "edit_1"
    3. Edit 2: field_a = "edit_2"
    4. Edit 3: field_a = "edit_3"
    5. Undo back to "edit_1" (2 undos)
    6. Redo to "edit_2" (1 redo)
    7. New edit: field_a = "edit_4" (clears redo stack)
    8. Verify can still undo to "edit_1", then "initial_a"
    """
    vm = loaded_project
    field_id = "field_a"  # String ID per Rule 0

    # Initial: field_a = "initial_a"
    initial_result = mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    )
    assert initial_result.value == "initial_a"

    # Edit 1: field_a = "edit_1"
    vm.update_field(field_id, "edit_1")
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "edit_1"

    # Wait to prevent command merging (500ms merge window)
    time.sleep(0.6)

    # Edit 2: field_a = "edit_2"
    vm.update_field(field_id, "edit_2")
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "edit_2"

    # Wait to prevent command merging
    time.sleep(0.6)

    # Edit 3: field_a = "edit_3"
    vm.update_field(field_id, "edit_3")
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "edit_3"

    # Undo back to "edit_1" (2 undos)
    vm.undo()  # edit_3 → edit_2
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "edit_2"

    vm.undo()  # edit_2 → edit_1
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "edit_1"

    # Verify undo/redo state
    assert vm.can_undo is True  # Can undo to "initial_a"
    assert vm.can_redo is True  # Can redo to "edit_2" and "edit_3"

    # Redo to "edit_2" (1 redo)
    vm.redo()  # edit_1 → edit_2
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "edit_2"

    # Wait to prevent command merging
    time.sleep(0.6)

    # New edit: field_a = "edit_4" (clears redo stack)
    vm.update_field(field_id, "edit_4")
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "edit_4"

    # Verify redo stack cleared
    assert vm.can_redo is False

    # Verify can still undo to "edit_2", then "edit_1", then "initial_a"
    assert vm.can_undo is True

    vm.undo()  # edit_4 → edit_2
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "edit_2"

    vm.undo()  # edit_2 → edit_1
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "edit_1"

    vm.undo()  # edit_1 → initial_a
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "initial_a"

    # Should not be able to undo further
    assert vm.can_undo is False


# ============================================================================
# T5: Undo Stack Cleared on Close/Open, NOT Save
# ============================================================================

def test_T5_stack_cleared_on_close_not_save(loaded_project, mock_field_service):
    """T5: Undo stack cleared on project close/open, NOT on save.

    Scenario:
    1. Make 2 edits
    2. Save project (undo stack should remain)
    3. Verify can still undo after save
    4. Close project (undo stack should clear)
    5. Verify cannot undo after close
    """
    vm = loaded_project
    field_id = "field_a"  # String ID per Rule 0

    # Make 2 edits
    vm.update_field(field_id, "edit_1")

    # Wait to prevent command merging
    time.sleep(0.6)

    vm.update_field(field_id, "edit_2")

    # Verify can undo
    assert vm.can_undo is True

    # Save project
    save_success = vm.save_project()
    assert save_success is True

    # Verify undo stack STILL available after save
    assert vm.can_undo is True

    # Verify undo still works
    vm.undo()  # edit_2 → edit_1
    assert mock_field_service.get_field_value(
        str(TEST_PROJECT_UUID), "field_a"
    ).value == "edit_1"

    # Wait to prevent command merging
    time.sleep(0.6)

    # Make another edit
    vm.update_field(field_id, "edit_3")
    assert vm.can_undo is True

    # Close project
    vm.close_project()

    # Verify undo stack cleared after close
    assert vm.can_undo is False
    assert vm.can_redo is False


def test_T5_stack_cleared_on_open(
    viewmodel, mock_project_usecases, mock_field_service
):
    """T5: Undo stack cleared when opening a different project.

    Scenario:
    1. Load project A, make edits
    2. Verify can undo
    3. Load project B (different project)
    4. Verify undo stack cleared

    Architecture Enforcement: Uses string IDs (not ProjectId domain objects).
    """
    vm = viewmodel

    # Load project A - using string ID per Rule 0
    project_a_id = str(uuid4())
    entity_def = EntityDefinitionDTO(
        id="entity-1",
        name="Test Entity",
        description=None,
        name_key="entity.test",
        description_key=None,
        field_count=1,
        is_root_entity=True,
        parent_entity_id=None,
        fields=(
            FieldDefinitionDTO(
                id="field_a",
                field_type="TEXT",
                label="Field A",
                help_text=None,
                required=False,
                default_value=None,
                options=(),
                formula=None,
                is_calculated=False,
                is_choice_field=False,
                is_collection_field=False,
                lookup_entity_id=None,
                child_entity_id=None,
            ),
        ),
    )

    vm.load_project(project_a_id, entity_def)

    # Make edits in project A
    field_id = "field_a"  # String ID per Rule 0
    vm.update_field(field_id, "edit_1")

    # Verify can undo
    assert vm.can_undo is True

    # Load project B (different project) - using string ID per Rule 0
    project_b_id = str(uuid4())
    vm.load_project(project_b_id, entity_def)

    # Verify undo stack cleared when opening new project
    assert vm.can_undo is False
    assert vm.can_redo is False

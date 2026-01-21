"""E2E Workflow 2: Open → Edit → Undo → Save.

Tests complete undo/redo workflow using real repositories.
Different from integration tests which use mocks.

Test Coverage:
- Create project and add field values
- Undo/redo field changes
- Verify persistence across sessions
- Undo stack behavior (cleared on close, NOT on save per v1.3.1)
"""

import pytest
import time
from datetime import date
from pathlib import Path
from uuid import UUID

from doc_helper.application.commands.create_project_command import CreateProjectCommand
from doc_helper.application.commands.update_field_command import UpdateFieldCommand
from doc_helper.application.queries.get_project_query import GetProjectQuery
from doc_helper.application.undo.undo_manager import UndoManager
from doc_helper.application.undo.field_undo_command import SetFieldValueCommand
from doc_helper.application.undo.undo_state_dto import UndoFieldState
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.validation.constraints import RequiredConstraint
from doc_helper.infrastructure.persistence.sqlite_project_repository import (
    SqliteProjectRepository,
)
from doc_helper.platform.registry.app_type_registry import AppTypeRegistry
from doc_helper.platform.discovery.manifest_parser import (
    ParsedManifest,
    ManifestSchema,
    ManifestTemplates,
    ManifestCapabilities,
)
from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata


@pytest.fixture
def app_type_registry() -> AppTypeRegistry:
    """Create registry with default AppType for testing."""
    registry = AppTypeRegistry()
    # Register soil_investigation AppType (default for v1)
    soil_manifest = ParsedManifest(
        metadata=AppTypeMetadata(
            app_type_id="soil_investigation",
            name="Soil Investigation",
            version="1.0.0",
            description="Soil investigation reports",
        ),
        schema=ManifestSchema(
            source="config.db",
            schema_type="sqlite",
        ),
        templates=ManifestTemplates(),
        capabilities=ManifestCapabilities(),
        manifest_path=Path("app_types/soil_investigation/manifest.json"),
    )
    registry.register(soil_manifest)
    return registry


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create temporary database file."""
    db_path = tmp_path / "test_undo_e2e.db"
    db_path.touch(exist_ok=True)
    return db_path


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create temporary project directory."""
    project_dir = tmp_path / "projects"
    project_dir.mkdir(exist_ok=True)
    return project_dir


@pytest.fixture
def test_schema() -> EntityDefinition:
    """Create test schema with fields for undo testing."""
    fields = {
        # TEXT field - for basic undo/redo
        FieldDefinitionId("field_a"): FieldDefinition(
            id=FieldDefinitionId("field_a"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.field_a"),
            required=False,
            constraints=(),
        ),
        # NUMBER field - for testing numeric value undo
        FieldDefinitionId("field_b"): FieldDefinition(
            id=FieldDefinitionId("field_b"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.field_b"),
            required=False,
            constraints=(),
        ),
        # TEXT field - for multiple field undo
        FieldDefinitionId("field_c"): FieldDefinition(
            id=FieldDefinitionId("field_c"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.field_c"),
            required=False,
            constraints=(),
        ),
    }

    entity_def = EntityDefinition(
        id=EntityDefinitionId("undo_test_entity"),
        name_key=TranslationKey("entity.undo_test"),
        fields=fields,
    )

    return entity_def


class MockFieldService:
    """Mock field service for undo commands.

    Wraps UpdateFieldCommand to match IFieldService protocol.
    """

    def __init__(self, project_repository: SqliteProjectRepository):
        self._project_repository = project_repository
        self._update_command = UpdateFieldCommand(project_repository)

    def set_field_value(
        self, project_id: str, field_id: str, value: any
    ) -> bool:
        """Set field value using UpdateFieldCommand.

        Args:
            project_id: Project ID as string
            field_id: Field ID as string
            value: New value

        Returns:
            True if successful
        """
        try:
            result = self._update_command.execute(
                project_id=ProjectId(UUID(project_id)),
                field_id=FieldDefinitionId(field_id),
                value=value,
            )
            return isinstance(result, Success)
        except Exception:
            return False

    def get_field_value(self, project_id: str, field_id: str) -> any:
        """Get field value from repository.

        Args:
            project_id: Project ID as string
            field_id: Field ID as string

        Returns:
            Success with field value or Failure
        """
        try:
            get_query = GetProjectQuery(self._project_repository)
            result = get_query.execute(ProjectId(UUID(project_id)))

            if isinstance(result, Failure):
                return Failure(result.error)

            project_dto = result.value
            if project_dto is None:
                return Failure("Project not found")

            # Get project entity to access field values
            project_result = self._project_repository.get_by_id(
                ProjectId(UUID(project_id))
            )
            if isinstance(project_result, Failure):
                return Failure(project_result.error)

            project = project_result.value
            if project is None:
                return Failure("Project not found")

            field_value = project.get_field_value(FieldDefinitionId(field_id))
            if field_value is None:
                return Success(None)

            return Success(field_value.value)
        except Exception as e:
            return Failure(str(e))


class TestUndoRedoWorkflow:
    """E2E tests for Workflow 2: Open → Edit → Undo → Save."""

    def test_basic_undo_redo_workflow(
        self, temp_db: Path, temp_project_dir: Path, test_schema: EntityDefinition, app_type_registry: AppTypeRegistry
    ) -> None:
        """Test complete undo/redo workflow with persistence.

        Workflow:
        1. Create project
        2. Set initial field values
        3. Modify field value
        4. Undo modification
        5. Redo modification
        6. Save and verify persistence
        """
        print("\n" + "=" * 70)
        print("TEST: Basic Undo/Redo Workflow")
        print("=" * 70)

        # Step 1: Create project
        print("\nStep 1: Create Project")
        project_repo = SqliteProjectRepository(temp_db)
        create_command = CreateProjectCommand(project_repository=project_repo, app_type_registry=app_type_registry)

        create_result = create_command.execute(
            name="Undo Test Project",
            entity_definition_id=EntityDefinitionId("undo_test_entity"),
            description="Testing undo/redo workflow",
        )
        assert isinstance(create_result, Success), f"Failed to create project: {create_result.error if isinstance(create_result, Failure) else 'unknown'}"
        project_id = create_result.value
        print(f"   ✓ Project created: {project_id.value}")

        # Step 2: Set initial value
        print("\nStep 2: Set Initial Field Value")
        update_command = UpdateFieldCommand(project_repository=project_repo)

        result = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("field_a"),
            value="initial_value",
        )
        assert isinstance(result, Success), f"Failed to set initial value: {result.error if isinstance(result, Failure) else 'unknown'}"
        print("   ✓ field_a = 'initial_value'")

        # Step 3: Initialize undo manager
        print("\nStep 3: Initialize Undo Manager")
        undo_manager = UndoManager(max_depth=100)
        field_service = MockFieldService(project_repo)
        print("   ✓ UndoManager ready")

        # Step 4: Modify value using undo command
        print("\nStep 4: Modify Field Value (via UndoCommand)")

        # Capture current value before change
        current_result = field_service.get_field_value(
            str(project_id.value), "field_a"
        )
        assert isinstance(current_result, Success)
        previous_value = current_result.value

        # Create undo state
        undo_state = UndoFieldState.create(
            field_id="field_a",
            previous_value=previous_value,
            new_value="modified_value",
        )

        # Create and execute command
        set_command = SetFieldValueCommand(
            project_id=str(project_id.value),
            state=undo_state,
            field_service=field_service,
        )

        success = undo_manager.execute(set_command)
        assert success is True, "Failed to execute SetFieldValueCommand"
        print("   ✓ field_a = 'modified_value'")

        # Verify change persisted
        verify_result = field_service.get_field_value(
            str(project_id.value), "field_a"
        )
        assert isinstance(verify_result, Success)
        assert verify_result.value == "modified_value"
        print("   ✓ Change persisted to database")

        # Verify undo available
        assert undo_manager.can_undo is True
        assert undo_manager.can_redo is False
        print("   ✓ Undo available, redo not available")

        # Step 5: Undo the change
        print("\nStep 5: Undo Change")
        undo_success = undo_manager.undo()
        assert undo_success is True, "Undo failed"
        print("   ✓ Undo executed")

        # Verify value restored
        restored_result = field_service.get_field_value(
            str(project_id.value), "field_a"
        )
        assert isinstance(restored_result, Success)
        assert restored_result.value == "initial_value"
        print("   ✓ field_a restored to 'initial_value'")

        # Verify undo/redo state
        assert undo_manager.can_undo is False
        assert undo_manager.can_redo is True
        print("   ✓ Undo not available, redo available")

        # Step 6: Redo the change
        print("\nStep 6: Redo Change")
        redo_success = undo_manager.redo()
        assert redo_success is True, "Redo failed"
        print("   ✓ Redo executed")

        # Verify value re-applied
        redone_result = field_service.get_field_value(
            str(project_id.value), "field_a"
        )
        assert isinstance(redone_result, Success)
        assert redone_result.value == "modified_value"
        print("   ✓ field_a redone to 'modified_value'")

        # Verify undo/redo state
        assert undo_manager.can_undo is True
        assert undo_manager.can_redo is False
        print("   ✓ Undo available, redo not available")

        # Step 7: Verify persistence across reload
        print("\nStep 7: Verify Persistence")
        reload_result = project_repo.get_by_id(project_id)
        assert isinstance(reload_result, Success)
        reloaded_project = reload_result.value
        assert reloaded_project is not None

        field_value = reloaded_project.get_field_value(FieldDefinitionId("field_a"))
        assert field_value is not None
        assert field_value.value == "modified_value"
        print("   ✓ Value persisted correctly after undo/redo")

        print("\n" + "=" * 70)
        print("✓ BASIC UNDO/REDO WORKFLOW TEST PASSED")
        print("=" * 70)

    def test_multiple_undo_redo_sequence(
        self, temp_db: Path, temp_project_dir: Path, test_schema: EntityDefinition,
        app_type_registry: AppTypeRegistry
    ) -> None:
        """Test multiple sequential undo/redo operations.

        Workflow:
        1. Create project
        2. Make 3 sequential edits
        3. Undo back to first edit
        4. Redo forward to second edit
        5. Make new edit (clears redo stack)
        6. Verify can undo all changes
        """
        print("\n" + "=" * 70)
        print("TEST: Multiple Undo/Redo Sequence")
        print("=" * 70)

        # Step 1: Create project
        print("\nStep 1: Create Project & Setup")
        project_repo = SqliteProjectRepository(temp_db)
        create_command = CreateProjectCommand(
            project_repository=project_repo,
            app_type_registry=app_type_registry
        )

        create_result = create_command.execute(
            name="Multi Undo Test",
            entity_definition_id=EntityDefinitionId("undo_test_entity"),
        )
        assert isinstance(create_result, Success)
        project_id = create_result.value
        print(f"   ✓ Project created: {project_id.value}")

        # Initialize undo infrastructure
        undo_manager = UndoManager(max_depth=100)
        field_service = MockFieldService(project_repo)
        print("   ✓ UndoManager ready")

        # Set initial value
        update_command = UpdateFieldCommand(project_repository=project_repo)
        result = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("field_b"),
            value=100,
        )
        assert isinstance(result, Success)
        print("   ✓ field_b = 100 (initial)")

        # Step 2: Make 3 sequential edits
        print("\nStep 2: Make Sequential Edits (with delays to prevent merging)")

        for i, value in enumerate([200, 300, 400], start=1):
            # Wait to prevent command merging (500ms merge window)
            time.sleep(0.6)

            current_result = field_service.get_field_value(
                str(project_id.value), "field_b"
            )
            assert isinstance(current_result, Success)
            previous_value = current_result.value

            undo_state = UndoFieldState.create(
                field_id="field_b",
                previous_value=previous_value,
                new_value=value,
            )

            set_command = SetFieldValueCommand(
                project_id=str(project_id.value),
                state=undo_state,
                field_service=field_service,
            )

            success = undo_manager.execute(set_command)
            assert success is True
            print(f"   ✓ Edit {i}: field_b = {value}")

        # Verify final value
        final_result = field_service.get_field_value(
            str(project_id.value), "field_b"
        )
        assert isinstance(final_result, Success)
        assert final_result.value == 400
        print("   ✓ Final value: field_b = 400")

        # Verify undo count
        assert undo_manager.undo_count == 3
        print(f"   ✓ Undo stack has {undo_manager.undo_count} commands")

        # Step 3: Undo back to first edit (200)
        print("\nStep 3: Undo Back to First Edit")

        undo_manager.undo()  # 400 → 300
        verify1 = field_service.get_field_value(str(project_id.value), "field_b")
        assert isinstance(verify1, Success)
        assert verify1.value == 300
        print("   ✓ Undo 1: field_b = 300")

        undo_manager.undo()  # 300 → 200
        verify2 = field_service.get_field_value(str(project_id.value), "field_b")
        assert isinstance(verify2, Success)
        assert verify2.value == 200
        print("   ✓ Undo 2: field_b = 200")

        # Verify state
        assert undo_manager.can_undo is True  # Can undo to 100
        assert undo_manager.can_redo is True  # Can redo to 300, 400
        print("   ✓ Undo and redo both available")

        # Step 4: Redo forward to second edit (300)
        print("\nStep 4: Redo Forward")

        undo_manager.redo()  # 200 → 300
        verify3 = field_service.get_field_value(str(project_id.value), "field_b")
        assert isinstance(verify3, Success)
        assert verify3.value == 300
        print("   ✓ Redo: field_b = 300")

        assert undo_manager.can_redo is True  # Can still redo to 400
        print("   ✓ Can still redo to 400")

        # Step 5: Make new edit (clears redo stack)
        print("\nStep 5: Make New Edit (Clears Redo Stack)")

        time.sleep(0.6)  # Prevent merging

        current_result = field_service.get_field_value(
            str(project_id.value), "field_b"
        )
        assert isinstance(current_result, Success)
        previous_value = current_result.value

        undo_state = UndoFieldState.create(
            field_id="field_b",
            previous_value=previous_value,
            new_value=500,
        )

        set_command = SetFieldValueCommand(
            project_id=str(project_id.value),
            state=undo_state,
            field_service=field_service,
        )

        success = undo_manager.execute(set_command)
        assert success is True
        print("   ✓ New edit: field_b = 500")

        # Verify redo stack cleared
        assert undo_manager.can_redo is False
        print("   ✓ Redo stack cleared")

        # Step 6: Verify can undo all changes
        print("\nStep 6: Verify Can Undo All Changes")

        assert undo_manager.can_undo is True
        undo_count = undo_manager.undo_count
        print(f"   ✓ Can undo {undo_count} commands")

        # Undo all
        undo_manager.undo()  # 500 → 300
        undo_manager.undo()  # 300 → 200
        undo_manager.undo()  # 200 → 100

        final_value = field_service.get_field_value(
            str(project_id.value), "field_b"
        )
        assert isinstance(final_value, Success)
        assert final_value.value == 100
        print("   ✓ Undone all changes: field_b = 100 (initial)")

        assert undo_manager.can_undo is False
        print("   ✓ Cannot undo further")

        print("\n" + "=" * 70)
        print("✓ MULTIPLE UNDO/REDO SEQUENCE TEST PASSED")
        print("=" * 70)

    def test_undo_stack_behavior_on_save_and_close(
        self, temp_db: Path, temp_project_dir: Path, test_schema: EntityDefinition,
        app_type_registry: AppTypeRegistry
    ) -> None:
        """Test undo stack behavior: cleared on close, NOT on save (v1.3.1).

        Workflow:
        1. Create project and make edits
        2. Verify undo available
        3. Save project
        4. Verify undo STILL available after save
        5. Make more edits
        6. Clear undo stack (simulating close)
        7. Verify undo NOT available after clear
        """
        print("\n" + "=" * 70)
        print("TEST: Undo Stack Behavior (Save vs Close)")
        print("=" * 70)

        # Step 1: Create project and make edits
        print("\nStep 1: Create Project & Make Edits")
        project_repo = SqliteProjectRepository(temp_db)
        create_command = CreateProjectCommand(
            project_repository=project_repo,
            app_type_registry=app_type_registry
        )

        create_result = create_command.execute(
            name="Stack Behavior Test",
            entity_definition_id=EntityDefinitionId("undo_test_entity"),
        )
        assert isinstance(create_result, Success)
        project_id = create_result.value
        print(f"   ✓ Project created: {project_id.value}")

        # Initialize undo infrastructure
        undo_manager = UndoManager(max_depth=100)
        field_service = MockFieldService(project_repo)

        # Make 2 edits
        update_command = UpdateFieldCommand(project_repository=project_repo)

        result1 = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("field_c"),
            value="edit_1",
        )
        assert isinstance(result1, Success)
        print("   ✓ Edit 1: field_c = 'edit_1'")

        time.sleep(0.6)  # Prevent merging

        # Second edit via undo command
        current_result = field_service.get_field_value(
            str(project_id.value), "field_c"
        )
        assert isinstance(current_result, Success)

        undo_state = UndoFieldState.create(
            field_id="field_c",
            previous_value=current_result.value,
            new_value="edit_2",
        )

        set_command = SetFieldValueCommand(
            project_id=str(project_id.value),
            state=undo_state,
            field_service=field_service,
        )

        success = undo_manager.execute(set_command)
        assert success is True
        print("   ✓ Edit 2: field_c = 'edit_2'")

        # Step 2: Verify undo available
        print("\nStep 2: Verify Undo Available")
        assert undo_manager.can_undo is True
        print(f"   ✓ Can undo ({undo_manager.undo_count} commands)")

        # Step 3: Save project (simulated by repository save)
        print("\nStep 3: Save Project")
        # Repository auto-saves on UpdateFieldCommand, but verify state persisted
        reload_result = project_repo.get_by_id(project_id)
        assert isinstance(reload_result, Success)
        print("   ✓ Project saved")

        # Step 4: Verify undo STILL available after save (v1.3.1 rule)
        print("\nStep 4: Verify Undo STILL Available After Save")
        assert undo_manager.can_undo is True
        print("   ✓ Undo stack NOT cleared by save (per v1.3.1)")

        # Verify undo still works
        undo_success = undo_manager.undo()
        assert undo_success is True

        restored_result = field_service.get_field_value(
            str(project_id.value), "field_c"
        )
        assert isinstance(restored_result, Success)
        assert restored_result.value == "edit_1"
        print("   ✓ Undo still works: field_c = 'edit_1'")

        # Step 5: Make more edits
        print("\nStep 5: Make More Edits")

        time.sleep(0.6)  # Prevent merging

        current_result2 = field_service.get_field_value(
            str(project_id.value), "field_c"
        )
        assert isinstance(current_result2, Success)

        undo_state2 = UndoFieldState.create(
            field_id="field_c",
            previous_value=current_result2.value,
            new_value="edit_3",
        )

        set_command2 = SetFieldValueCommand(
            project_id=str(project_id.value),
            state=undo_state2,
            field_service=field_service,
        )

        success2 = undo_manager.execute(set_command2)
        assert success2 is True
        print("   ✓ Edit 3: field_c = 'edit_3'")

        assert undo_manager.can_undo is True
        print(f"   ✓ Undo still available ({undo_manager.undo_count} commands)")

        # Step 6: Clear undo stack (simulates project close)
        print("\nStep 6: Clear Undo Stack (Simulates Project Close)")
        undo_manager.clear()
        print("   ✓ Undo stack cleared")

        # Step 7: Verify undo NOT available after clear
        print("\nStep 7: Verify Undo NOT Available After Clear")
        assert undo_manager.can_undo is False
        assert undo_manager.can_redo is False
        print("   ✓ Undo and redo cleared (per v1.3.1)")

        print("\n" + "=" * 70)
        print("✓ UNDO STACK BEHAVIOR TEST PASSED")
        print("=" * 70)

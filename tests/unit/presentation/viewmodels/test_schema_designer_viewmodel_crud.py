"""Tests for SchemaDesignerViewModel entity/field CRUD operations (Phase SD-5).

Tests the entity and field management features added in Phases SD-3 and SD-4.

ARCHITECTURAL NOTE (Rule 0 Compliance):
- ViewModel constructor takes SchemaUseCases (application layer use-case)
- NOT individual queries/commands or repositories
- All orchestration delegated to SchemaUseCases
"""

import pytest
from unittest.mock import MagicMock

from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.dto.schema_dto import EntityDefinitionDTO, FieldDefinitionDTO
from doc_helper.application.dto.export_dto import ConstraintExportDTO
from doc_helper.application.usecases.schema_usecases import SchemaUseCases
from doc_helper.presentation.viewmodels.schema_designer_viewmodel import (
    SchemaDesignerViewModel,
)


class TestSchemaDesignerViewModelEntityCRUD:
    """Tests for entity CRUD operations in SchemaDesignerViewModel (Phase SD-3)."""

    @pytest.fixture
    def mock_schema_usecases(self) -> MagicMock:
        """Create mock SchemaUseCases (Rule 0 compliant)."""
        usecases = MagicMock(spec=SchemaUseCases)
        usecases.get_all_entities.return_value = ()
        usecases.get_all_relationships.return_value = ()
        usecases.get_field_validation_rules.return_value = ()
        usecases.get_entity_list_for_selection.return_value = ()
        return usecases

    @pytest.fixture
    def viewmodel(
        self,
        mock_schema_usecases: MagicMock,
    ) -> SchemaDesignerViewModel:
        """Create viewmodel with SchemaUseCases dependency."""
        return SchemaDesignerViewModel(
            schema_usecases=mock_schema_usecases,
        )

    # =========================================================================
    # Create Entity
    # =========================================================================

    def test_create_entity_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """create_entity should delegate to use-case and reload on success."""
        mock_schema_usecases.create_entity.return_value = OperationResult.ok("new_entity")
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        result = viewmodel.create_entity(
            entity_id="new_entity",
            name_key="entity.new",
            is_root_entity=False,
        )

        assert result.success is True
        assert result.value == "new_entity"
        mock_schema_usecases.create_entity.assert_called_once()

    def test_create_entity_reloads_entities_on_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """create_entity should reload entities after success."""
        mock_schema_usecases.create_entity.return_value = OperationResult.ok("test")
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        viewmodel.create_entity(
            entity_id="test",
            name_key="entity.test",
            is_root_entity=False,
        )

        # get_all_entities called for reload after creation
        assert mock_schema_usecases.get_all_entities.call_count >= 1

    def test_create_entity_failure_does_not_reload(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """create_entity should NOT reload entities on failure."""
        mock_schema_usecases.create_entity.return_value = OperationResult.fail("Error")

        # Reset the call count
        mock_schema_usecases.get_all_entities.reset_mock()

        result = viewmodel.create_entity(
            entity_id="test",
            name_key="entity.test",
            is_root_entity=False,
        )

        assert result.success is False
        mock_schema_usecases.get_all_entities.assert_not_called()

    # =========================================================================
    # Update Entity (Phase SD-3)
    # =========================================================================

    def test_update_entity_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """update_entity should delegate to use-case and reload on success."""
        mock_schema_usecases.update_entity.return_value = OperationResult.ok("updated_entity")
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        result = viewmodel.update_entity(
            entity_id="updated_entity",
            name_key="entity.updated",
        )

        assert result.success is True
        mock_schema_usecases.update_entity.assert_called_once_with(
            entity_id="updated_entity",
            name_key="entity.updated",
            description_key=None,
            is_root_entity=None,
        )

    def test_update_entity_failure(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """update_entity should return failure from use-case."""
        mock_schema_usecases.update_entity.return_value = OperationResult.fail("Not found")

        result = viewmodel.update_entity(
            entity_id="nonexistent",
            name_key="entity.test",
        )

        assert result.success is False
        assert "Not found" in result.error

    # =========================================================================
    # Delete Entity (Phase SD-3)
    # =========================================================================

    def test_delete_entity_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_entity should delegate to use-case and reload on success."""
        mock_schema_usecases.delete_entity.return_value = OperationResult.ok(None)
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        result = viewmodel.delete_entity(entity_id="test_entity")

        assert result.success is True
        mock_schema_usecases.delete_entity.assert_called_once_with(entity_id="test_entity")

    def test_delete_entity_clears_selection_if_deleted(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_entity should clear selection if deleted entity was selected."""
        # Setup: Select the entity first
        viewmodel._selected_entity_id = "test_entity"

        mock_schema_usecases.delete_entity.return_value = OperationResult.ok(None)
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        viewmodel.delete_entity(entity_id="test_entity")

        assert viewmodel._selected_entity_id is None

    def test_delete_entity_failure_with_dependencies(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_entity should return detailed error when dependencies exist."""
        mock_schema_usecases.delete_entity.return_value = OperationResult.fail(
            "Cannot delete: referenced by TABLE fields"
        )

        result = viewmodel.delete_entity(entity_id="referenced_entity")

        assert result.success is False
        assert "referenced" in result.error.lower()


class TestSchemaDesignerViewModelFieldCRUD:
    """Tests for field CRUD operations in SchemaDesignerViewModel (Phase SD-4)."""

    @pytest.fixture
    def mock_schema_usecases(self) -> MagicMock:
        """Create mock SchemaUseCases (Rule 0 compliant)."""
        usecases = MagicMock(spec=SchemaUseCases)
        usecases.get_all_entities.return_value = ()
        usecases.get_all_relationships.return_value = ()
        usecases.get_field_validation_rules.return_value = ()
        usecases.get_entity_list_for_selection.return_value = ()
        return usecases

    @pytest.fixture
    def viewmodel(
        self,
        mock_schema_usecases: MagicMock,
    ) -> SchemaDesignerViewModel:
        """Create viewmodel with SchemaUseCases dependency."""
        return SchemaDesignerViewModel(
            schema_usecases=mock_schema_usecases,
        )

    # =========================================================================
    # Add Field
    # =========================================================================

    def test_add_field_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_field should delegate to use-case and reload on success."""
        mock_schema_usecases.add_field.return_value = OperationResult.ok("new_field")
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        # Select entity first
        viewmodel._selected_entity_id = "test_entity"

        result = viewmodel.add_field(
            entity_id="test_entity",
            field_id="new_field",
            field_type="TEXT",
            label_key="field.new",
        )

        assert result.success is True
        assert result.value == "new_field"
        mock_schema_usecases.add_field.assert_called_once()

    def test_add_field_reselects_entity_to_refresh_fields(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_field should re-select entity to refresh field list."""
        mock_schema_usecases.add_field.return_value = OperationResult.ok("new_field")
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        viewmodel._selected_entity_id = "test_entity"

        viewmodel.add_field(
            entity_id="test_entity",
            field_id="new_field",
            field_type="TEXT",
            label_key="field.new",
        )

        # Entities reloaded to refresh field list
        assert mock_schema_usecases.get_all_entities.call_count >= 1

    # =========================================================================
    # Update Field (Phase SD-4)
    # =========================================================================

    def test_update_field_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """update_field should delegate to use-case and reload on success."""
        mock_schema_usecases.update_field.return_value = OperationResult.ok("updated_field")
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        viewmodel._selected_entity_id = "test_entity"

        result = viewmodel.update_field(
            entity_id="test_entity",
            field_id="updated_field",
            label_key="field.updated",
        )

        assert result.success is True
        mock_schema_usecases.update_field.assert_called_once()

    def test_update_field_failure(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """update_field should return failure from use-case."""
        mock_schema_usecases.update_field.return_value = OperationResult.fail("Field not found")

        result = viewmodel.update_field(
            entity_id="test_entity",
            field_id="nonexistent",
            label_key="field.test",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    # =========================================================================
    # Delete Field (Phase SD-4)
    # =========================================================================

    def test_delete_field_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_field should delegate to use-case and reload on success."""
        mock_schema_usecases.delete_field.return_value = OperationResult.ok(None)
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        result = viewmodel.delete_field(
            entity_id="test_entity",
            field_id="test_field",
        )

        assert result.success is True
        mock_schema_usecases.delete_field.assert_called_once_with(
            entity_id="test_entity",
            field_id="test_field",
        )

    def test_delete_field_clears_selection_if_deleted(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_field should clear field selection if deleted field was selected."""
        viewmodel._selected_field_id = "test_field"

        mock_schema_usecases.delete_field.return_value = OperationResult.ok(None)
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        viewmodel.delete_field(
            entity_id="test_entity",
            field_id="test_field",
        )

        assert viewmodel._selected_field_id is None

    def test_delete_field_failure_with_dependencies(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_field should return detailed error when dependencies exist."""
        mock_schema_usecases.delete_field.return_value = OperationResult.fail(
            "Cannot delete: referenced by formulas"
        )

        result = viewmodel.delete_field(
            entity_id="test_entity",
            field_id="referenced_field",
        )

        assert result.success is False
        assert "referenced" in result.error.lower()


class TestSchemaDesignerViewModelConstraintOperations:
    """Tests for constraint operations in SchemaDesignerViewModel (Phase SD-2)."""

    @pytest.fixture
    def mock_schema_usecases(self) -> MagicMock:
        """Create mock SchemaUseCases (Rule 0 compliant)."""
        usecases = MagicMock(spec=SchemaUseCases)
        usecases.get_all_entities.return_value = ()
        usecases.get_all_relationships.return_value = ()
        usecases.get_field_validation_rules.return_value = ()
        usecases.get_entity_list_for_selection.return_value = ()
        return usecases

    @pytest.fixture
    def viewmodel(
        self,
        mock_schema_usecases: MagicMock,
    ) -> SchemaDesignerViewModel:
        """Create viewmodel with SchemaUseCases dependency."""
        return SchemaDesignerViewModel(
            schema_usecases=mock_schema_usecases,
        )

    def test_add_constraint_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_constraint should delegate to use-case and refresh validation rules."""
        mock_schema_usecases.add_constraint.return_value = OperationResult.ok(None)
        mock_schema_usecases.get_field_validation_rules.return_value = ("REQUIRED",)

        viewmodel._selected_entity_id = "test_entity"
        viewmodel._selected_field_id = "test_field"

        result = viewmodel.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="REQUIRED",
            severity="ERROR",
        )

        assert result.success is True
        mock_schema_usecases.add_constraint.assert_called_once()

    def test_add_constraint_refreshes_validation_rules(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_constraint should refresh validation rules on success."""
        mock_schema_usecases.add_constraint.return_value = OperationResult.ok(None)
        mock_schema_usecases.get_field_validation_rules.return_value = ()

        viewmodel._selected_entity_id = "test_entity"
        viewmodel._selected_field_id = "test_field"

        # Track change notifications
        changes_notified = []

        def track_change():
            changes_notified.append("validation_rules")

        viewmodel.subscribe("validation_rules", track_change)

        viewmodel.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="REQUIRED",
            severity="ERROR",
        )

        assert "validation_rules" in changes_notified


class TestSchemaDesignerViewModelAdvancedConstraints:
    """Tests for Phase SD-6 advanced constraint operations."""

    @pytest.fixture
    def mock_schema_usecases(self) -> MagicMock:
        """Create mock SchemaUseCases (Rule 0 compliant)."""
        usecases = MagicMock(spec=SchemaUseCases)
        usecases.get_all_entities.return_value = ()
        usecases.get_all_relationships.return_value = ()
        usecases.get_field_validation_rules.return_value = ()
        usecases.get_entity_list_for_selection.return_value = ()
        return usecases

    @pytest.fixture
    def viewmodel(
        self,
        mock_schema_usecases: MagicMock,
    ) -> SchemaDesignerViewModel:
        """Create viewmodel with SchemaUseCases dependency."""
        return SchemaDesignerViewModel(
            schema_usecases=mock_schema_usecases,
        )

    def test_add_pattern_constraint_passes_parameters(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_constraint should pass pattern parameters to use-case (Phase SD-6)."""
        mock_schema_usecases.add_constraint.return_value = OperationResult.ok(None)

        viewmodel._selected_entity_id = "test_entity"
        viewmodel._selected_field_id = "test_field"

        viewmodel.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="PATTERN",
            severity="ERROR",
            pattern=r"^[A-Z]{2}\d{4}$",
            pattern_description="2 letters + 4 digits",
        )

        mock_schema_usecases.add_constraint.assert_called_once_with(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="PATTERN",
            value=None,
            severity="ERROR",
            pattern=r"^[A-Z]{2}\d{4}$",
            pattern_description="2 letters + 4 digits",
            allowed_values=None,
            allowed_extensions=None,
            max_size_bytes=None,
        )

    def test_add_allowed_values_constraint_passes_parameters(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_constraint should pass allowed_values to use-case (Phase SD-6)."""
        mock_schema_usecases.add_constraint.return_value = OperationResult.ok(None)

        viewmodel._selected_entity_id = "test_entity"
        viewmodel._selected_field_id = "test_field"

        viewmodel.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="ALLOWED_VALUES",
            severity="ERROR",
            allowed_values=("value1", "value2", "value3"),
        )

        mock_schema_usecases.add_constraint.assert_called_once_with(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="ALLOWED_VALUES",
            value=None,
            severity="ERROR",
            pattern=None,
            pattern_description=None,
            allowed_values=("value1", "value2", "value3"),
            allowed_extensions=None,
            max_size_bytes=None,
        )

    def test_add_file_extension_constraint_passes_parameters(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_constraint should pass allowed_extensions to use-case (Phase SD-6)."""
        mock_schema_usecases.add_constraint.return_value = OperationResult.ok(None)

        viewmodel._selected_entity_id = "test_entity"
        viewmodel._selected_field_id = "test_field"

        viewmodel.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="FILE_EXTENSION",
            severity="ERROR",
            allowed_extensions=(".pdf", ".doc", ".docx"),
        )

        mock_schema_usecases.add_constraint.assert_called_once_with(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="FILE_EXTENSION",
            value=None,
            severity="ERROR",
            pattern=None,
            pattern_description=None,
            allowed_values=None,
            allowed_extensions=(".pdf", ".doc", ".docx"),
            max_size_bytes=None,
        )

    def test_add_max_file_size_constraint_passes_parameters(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_constraint should pass max_size_bytes to use-case (Phase SD-6)."""
        mock_schema_usecases.add_constraint.return_value = OperationResult.ok(None)

        viewmodel._selected_entity_id = "test_entity"
        viewmodel._selected_field_id = "test_field"

        viewmodel.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="MAX_FILE_SIZE",
            severity="ERROR",
            max_size_bytes=10485760,  # 10 MB
        )

        mock_schema_usecases.add_constraint.assert_called_once_with(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="MAX_FILE_SIZE",
            value=None,
            severity="ERROR",
            pattern=None,
            pattern_description=None,
            allowed_values=None,
            allowed_extensions=None,
            max_size_bytes=10485760,
        )


class TestConstraintUniquenessEnforcement:
    """Regression tests for constraint uniqueness invariant.

    BUG: The system allowed adding multiple constraints of the same type to a single field.
    Example: A field could have two RequiredConstraint or two MinLengthConstraint.

    FIX: SchemaUseCases.add_constraint now checks existing constraints and blocks duplicates.
    ViewModel delegates to UseCases and displays errors verbatim.

    INVARIANT: Each constraint type may exist at most once per field.
    Enforced at: Application Layer (SchemaUseCases), NOT ViewModel.
    """

    @pytest.fixture
    def mock_schema_usecases(self) -> MagicMock:
        """Create mock SchemaUseCases."""
        usecases = MagicMock(spec=SchemaUseCases)
        usecases.get_all_entities.return_value = ()
        usecases.get_all_relationships.return_value = ()
        usecases.get_field_validation_rules.return_value = ()
        usecases.get_entity_list_for_selection.return_value = ()
        usecases.list_control_rules_for_field.return_value = ()
        usecases.list_output_mappings_for_field.return_value = ()
        usecases.list_field_options.return_value = ()
        return usecases

    @pytest.fixture
    def viewmodel(
        self,
        mock_schema_usecases: MagicMock,
    ) -> SchemaDesignerViewModel:
        """Create viewmodel with SchemaUseCases dependency."""
        return SchemaDesignerViewModel(
            schema_usecases=mock_schema_usecases,
        )

    def test_adding_duplicate_constraint_type_is_blocked(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """REGRESSION TEST: Adding same constraint type twice must be blocked.

        Uniqueness is enforced by SchemaUseCases (Application Layer).
        ViewModel delegates and returns the error verbatim.
        """
        # Setup: SchemaUseCases returns failure for duplicate constraint
        mock_schema_usecases.add_constraint.return_value = OperationResult.fail(
            "A MIN_LENGTH constraint already exists for this field. "
            "Each constraint type may only appear once per field. "
            "Delete the existing constraint first if you want to change its value."
        )

        # ACT: Try to add a MIN_LENGTH constraint (UseCases will reject it)
        result = viewmodel.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="MIN_LENGTH",
            value=10,
            severity="ERROR",
        )

        # ASSERT: Operation must fail (error from UseCases passed through)
        assert result.success is False
        assert "MIN_LENGTH constraint already exists" in result.error

        # ViewModel DID call UseCases (it delegates, doesn't check itself)
        mock_schema_usecases.add_constraint.assert_called_once()

    def test_adding_different_constraint_types_is_allowed(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """Adding different constraint types to same field should work.

        ViewModel delegates to UseCases. If UseCases accepts, ViewModel succeeds.
        """
        # Setup: UseCases accepts the constraint
        mock_schema_usecases.add_constraint.return_value = OperationResult.ok(
            "test_field"
        )

        # ACT: Add a MAX_LENGTH constraint
        result = viewmodel.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="MAX_LENGTH",
            value=100,
            severity="ERROR",
        )

        # ASSERT: Operation succeeds (UseCases accepted it)
        assert result.success is True

        # ViewModel MUST delegate to UseCases
        mock_schema_usecases.add_constraint.assert_called_once()

    def test_adding_constraint_to_field_with_no_existing_constraints(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """Adding first constraint to a field should work.

        ViewModel delegates to UseCases. If UseCases accepts, ViewModel succeeds.
        """
        # Setup: UseCases accepts the constraint
        mock_schema_usecases.add_constraint.return_value = OperationResult.ok(
            "test_field"
        )

        # ACT: Add a REQUIRED constraint
        result = viewmodel.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="REQUIRED",
            severity="ERROR",
        )

        # ASSERT: Operation succeeds
        assert result.success is True
        mock_schema_usecases.add_constraint.assert_called_once()


class TestSchemaDesignerViewModelUIStateSync:
    """Regression tests for Phase S-3 Bug Fix: UI State Synchronization.

    BUG: When a field is added/updated/deleted via commands, the Fields panel
    and Validation Rules panel in Schema Designer UI did NOT update immediately.

    ROOT CAUSE: SchemaDesignerViewModel kept stale DTO snapshots instead of
    re-querying after mutation.

    FIX: _reload_schema_state() method that re-queries authoritative data
    and notifies ALL affected properties.
    """

    @pytest.fixture
    def mock_schema_usecases(self) -> MagicMock:
        """Create mock SchemaUseCases (Rule 0 compliant)."""
        usecases = MagicMock(spec=SchemaUseCases)
        usecases.get_all_entities.return_value = ()
        usecases.get_all_relationships.return_value = ()
        usecases.get_field_validation_rules.return_value = ()
        usecases.get_entity_list_for_selection.return_value = ()
        usecases.list_control_rules_for_field.return_value = ()
        usecases.list_output_mappings_for_field.return_value = ()
        usecases.list_field_options.return_value = ()
        return usecases

    @pytest.fixture
    def viewmodel(
        self,
        mock_schema_usecases: MagicMock,
    ) -> SchemaDesignerViewModel:
        """Create viewmodel with SchemaUseCases dependency."""
        return SchemaDesignerViewModel(
            schema_usecases=mock_schema_usecases,
        )

    def test_add_field_immediately_updates_fields_property(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """REGRESSION TEST: add_field should immediately update fields property.

        Phase S-3 Bug Fix:
        - Before fix: fields property returned stale data after add_field
        - After fix: fields property returns fresh data including new field
        """
        # Setup: Entity with no fields initially
        entity_before = EntityDefinitionDTO(
            id="test_entity",
            name="Test Entity",
            name_key="entity.test",
            description=None,
            description_key=None,
            field_count=0,
            is_root_entity=False,
            parent_entity_id=None,
            fields=(),
        )

        # After add_field: Entity with one field
        new_field = FieldDefinitionDTO(
            id="new_field",
            field_type="TEXT",
            label="New Field",
            help_text=None,
            required=False,
            is_required=False,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )
        entity_after = EntityDefinitionDTO(
            id="test_entity",
            name="Test Entity",
            name_key="entity.test",
            description=None,
            description_key=None,
            field_count=1,
            is_root_entity=False,
            parent_entity_id=None,
            fields=(new_field,),
        )

        # Configure mock to return empty initially, then updated after add
        call_count = [0]

        def get_entities_side_effect():
            call_count[0] += 1
            if call_count[0] <= 1:
                return (entity_before,)
            return (entity_after,)

        mock_schema_usecases.get_all_entities.side_effect = get_entities_side_effect
        mock_schema_usecases.add_field.return_value = OperationResult.ok("new_field")

        # Load initial state and select entity
        viewmodel.load_entities()
        viewmodel.select_entity("test_entity")

        # Verify initial state: no fields
        assert len(viewmodel.fields) == 0

        # Track change notifications
        notifications = []

        def track_fields_change():
            notifications.append("fields")

        def track_validation_rules_change():
            notifications.append("validation_rules")

        viewmodel.subscribe("fields", track_fields_change)
        viewmodel.subscribe("validation_rules", track_validation_rules_change)

        # ACT: Add a field
        result = viewmodel.add_field(
            entity_id="test_entity",
            field_id="new_field",
            field_type="TEXT",
            label_key="field.new",
        )

        # ASSERT: Operation succeeded
        assert result.success is True

        # CRITICAL ASSERTION: fields property immediately reflects the new field
        assert len(viewmodel.fields) == 1
        assert viewmodel.fields[0].id == "new_field"

        # CRITICAL ASSERTION: Both properties were notified
        assert "fields" in notifications, "fields change not notified"
        assert "validation_rules" in notifications, "validation_rules change not notified"

        # CRITICAL ASSERTION: Entity selection preserved
        assert viewmodel.selected_entity_id == "test_entity"

    def test_update_field_immediately_updates_fields_property(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """REGRESSION TEST: update_field should immediately update fields property."""
        # Setup: Entity with one field
        field_before = FieldDefinitionDTO(
            id="test_field",
            field_type="TEXT",
            label="Old Label",
            help_text=None,
            required=False,
            is_required=False,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )
        entity_before = EntityDefinitionDTO(
            id="test_entity",
            name="Test Entity",
            name_key="entity.test",
            description=None,
            description_key=None,
            field_count=1,
            is_root_entity=False,
            parent_entity_id=None,
            fields=(field_before,),
        )

        # After update_field: Field with new label
        field_after = FieldDefinitionDTO(
            id="test_field",
            field_type="TEXT",
            label="New Label",
            help_text=None,
            required=True,  # Changed
            is_required=True,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )
        entity_after = EntityDefinitionDTO(
            id="test_entity",
            name="Test Entity",
            name_key="entity.test",
            description=None,
            description_key=None,
            field_count=1,
            is_root_entity=False,
            parent_entity_id=None,
            fields=(field_after,),
        )

        # Configure mock
        call_count = [0]

        def get_entities_side_effect():
            call_count[0] += 1
            if call_count[0] <= 1:
                return (entity_before,)
            return (entity_after,)

        mock_schema_usecases.get_all_entities.side_effect = get_entities_side_effect
        mock_schema_usecases.update_field.return_value = OperationResult.ok("test_field")

        # Load initial state and select entity/field
        viewmodel.load_entities()
        viewmodel.select_entity("test_entity")
        viewmodel.select_field("test_field")

        # Verify initial state
        assert viewmodel.fields[0].label == "Old Label"
        assert viewmodel.fields[0].required is False

        # ACT: Update the field
        result = viewmodel.update_field(
            entity_id="test_entity",
            field_id="test_field",
            label_key="field.new",
            required=True,
        )

        # ASSERT: Operation succeeded
        assert result.success is True

        # CRITICAL ASSERTION: fields property immediately reflects the update
        assert viewmodel.fields[0].label == "New Label"
        assert viewmodel.fields[0].required is True

        # CRITICAL ASSERTION: Selections preserved
        assert viewmodel.selected_entity_id == "test_entity"
        assert viewmodel.selected_field_id == "test_field"

    def test_delete_field_immediately_clears_from_fields_property(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """REGRESSION TEST: delete_field should immediately remove from fields property."""
        # Setup: Entity with one field
        field = FieldDefinitionDTO(
            id="test_field",
            field_type="TEXT",
            label="Test Field",
            help_text=None,
            required=False,
            is_required=False,
            default_value=None,
            options=(),
            formula=None,
            is_calculated=False,
            is_choice_field=False,
            is_collection_field=False,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
        )
        entity_before = EntityDefinitionDTO(
            id="test_entity",
            name="Test Entity",
            name_key="entity.test",
            description=None,
            description_key=None,
            field_count=1,
            is_root_entity=False,
            parent_entity_id=None,
            fields=(field,),
        )

        # After delete: Entity with no fields
        entity_after = EntityDefinitionDTO(
            id="test_entity",
            name="Test Entity",
            name_key="entity.test",
            description=None,
            description_key=None,
            field_count=0,
            is_root_entity=False,
            parent_entity_id=None,
            fields=(),
        )

        # Configure mock
        call_count = [0]

        def get_entities_side_effect():
            call_count[0] += 1
            if call_count[0] <= 1:
                return (entity_before,)
            return (entity_after,)

        mock_schema_usecases.get_all_entities.side_effect = get_entities_side_effect
        mock_schema_usecases.delete_field.return_value = OperationResult.ok(None)

        # Load initial state and select entity/field
        viewmodel.load_entities()
        viewmodel.select_entity("test_entity")
        viewmodel.select_field("test_field")

        # Verify initial state
        assert len(viewmodel.fields) == 1
        assert viewmodel.selected_field_id == "test_field"

        # ACT: Delete the field
        result = viewmodel.delete_field(
            entity_id="test_entity",
            field_id="test_field",
        )

        # ASSERT: Operation succeeded
        assert result.success is True

        # CRITICAL ASSERTION: fields property immediately reflects deletion
        assert len(viewmodel.fields) == 0

        # CRITICAL ASSERTION: Field selection cleared (field no longer exists)
        assert viewmodel.selected_field_id is None

        # CRITICAL ASSERTION: Entity selection preserved
        assert viewmodel.selected_entity_id == "test_entity"

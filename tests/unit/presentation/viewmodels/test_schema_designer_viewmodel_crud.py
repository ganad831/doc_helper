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

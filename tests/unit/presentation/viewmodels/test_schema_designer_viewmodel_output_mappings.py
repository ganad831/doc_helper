"""Tests for SchemaDesignerViewModel output mappings operations (Phase F-13).

Tests the persisted output mappings features added in Phase F-13.

PHASE F-13 COMPLIANCE:
- Design-time only operations
- NO runtime execution
- NO formula evaluation or preview
- Delegates to SchemaUseCases for all operations

ARCHITECTURAL NOTE (Rule 0 Compliance):
- ViewModel constructor takes SchemaUseCases (application layer use-case)
- NOT individual queries/commands or repositories
- All orchestration delegated to SchemaUseCases
"""

import pytest
from unittest.mock import MagicMock

from doc_helper.application.dto.export_dto import OutputMappingExportDTO
from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.usecases.schema_usecases import SchemaUseCases
from doc_helper.presentation.viewmodels.schema_designer_viewmodel import (
    SchemaDesignerViewModel,
)


class TestSchemaDesignerViewModelOutputMappings:
    """Tests for persisted output mappings operations in SchemaDesignerViewModel (Phase F-13)."""

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
    # Load Output Mappings
    # =========================================================================

    def test_load_output_mappings_when_no_field_selected(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """load_output_mappings should clear output mappings when no field selected."""
        viewmodel.load_output_mappings()

        assert viewmodel.output_mappings == ()
        assert viewmodel.has_output_mappings is False
        mock_schema_usecases.list_output_mappings_for_field.assert_not_called()

    def test_load_output_mappings_when_field_selected(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """load_output_mappings should load output mappings from use-case when field selected."""
        # Setup field selection
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        # Setup mock return value
        output_mappings = (
            OutputMappingExportDTO(
                target="TEXT",
                formula_text="{{depth_from}} - {{depth_to}}",
            ),
        )
        mock_schema_usecases.list_output_mappings_for_field.return_value = output_mappings

        viewmodel.load_output_mappings()

        assert viewmodel.output_mappings == output_mappings
        assert viewmodel.has_output_mappings is True
        mock_schema_usecases.list_output_mappings_for_field.assert_called_once_with(
            entity_id="entity1",
            field_id="field1",
        )

    def test_load_output_mappings_when_no_mappings_exist(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """load_output_mappings should handle empty output mappings."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"
        mock_schema_usecases.list_output_mappings_for_field.return_value = ()

        viewmodel.load_output_mappings()

        assert viewmodel.output_mappings == ()
        assert viewmodel.has_output_mappings is False

    # =========================================================================
    # Select Field (Phase F-13 Integration)
    # =========================================================================

    def test_select_field_loads_output_mappings(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """select_field should load output mappings for the selected field."""
        viewmodel._selected_entity_id = "entity1"
        mock_schema_usecases.list_output_mappings_for_field.return_value = ()

        viewmodel.select_field("field1")

        assert mock_schema_usecases.list_output_mappings_for_field.called

    # =========================================================================
    # Add Output Mapping
    # =========================================================================

    def test_add_output_mapping_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_output_mapping should delegate to use-case and reload on success."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.add_output_mapping.return_value = OperationResult.ok("field1")
        mock_schema_usecases.list_output_mappings_for_field.return_value = ()
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        result = viewmodel.add_output_mapping(
            target="TEXT",
            formula_text="{{depth_from}} - {{depth_to}}",
        )

        assert result.success is True
        mock_schema_usecases.add_output_mapping.assert_called_once_with(
            entity_id="entity1",
            field_id="field1",
            target="TEXT",
            formula_text="{{depth_from}} - {{depth_to}}",
        )
        # Should reload output mappings and entities
        mock_schema_usecases.list_output_mappings_for_field.assert_called()
        mock_schema_usecases.get_all_entities.assert_called()

    def test_add_output_mapping_when_no_field_selected(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_output_mapping should return error when no field selected."""
        result = viewmodel.add_output_mapping(
            target="TEXT",
            formula_text="{{depth_from}} - {{depth_to}}",
        )

        assert result.success is False
        assert "No field selected" in result.error
        mock_schema_usecases.add_output_mapping.assert_not_called()

    def test_add_output_mapping_failure_does_not_reload(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_output_mapping should NOT reload on failure."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.add_output_mapping.return_value = OperationResult.fail(
            "Invalid formula"
        )
        mock_schema_usecases.list_output_mappings_for_field.reset_mock()
        mock_schema_usecases.get_all_entities.reset_mock()

        result = viewmodel.add_output_mapping(
            target="TEXT",
            formula_text="invalid formula",
        )

        assert result.success is False
        mock_schema_usecases.list_output_mappings_for_field.assert_not_called()
        mock_schema_usecases.get_all_entities.assert_not_called()

    # =========================================================================
    # Update Output Mapping
    # =========================================================================

    def test_update_output_mapping_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """update_output_mapping should delegate to use-case and reload on success."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.update_output_mapping.return_value = OperationResult.ok("field1")
        mock_schema_usecases.list_output_mappings_for_field.return_value = ()
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        result = viewmodel.update_output_mapping(
            target="TEXT",
            formula_text="{{depth_from}} + {{depth_to}}",
        )

        assert result.success is True
        mock_schema_usecases.update_output_mapping.assert_called_once_with(
            entity_id="entity1",
            field_id="field1",
            target="TEXT",
            formula_text="{{depth_from}} + {{depth_to}}",
        )
        # Should reload output mappings and entities
        mock_schema_usecases.list_output_mappings_for_field.assert_called()
        mock_schema_usecases.get_all_entities.assert_called()

    def test_update_output_mapping_when_no_field_selected(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """update_output_mapping should return error when no field selected."""
        result = viewmodel.update_output_mapping(
            target="TEXT",
            formula_text="{{depth_from}} + {{depth_to}}",
        )

        assert result.success is False
        assert "No field selected" in result.error
        mock_schema_usecases.update_output_mapping.assert_not_called()

    def test_update_output_mapping_failure(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """update_output_mapping should return failure from use-case."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.update_output_mapping.return_value = OperationResult.fail(
            "Mapping not found"
        )

        result = viewmodel.update_output_mapping(
            target="TEXT",
            formula_text="{{depth_from}} + {{depth_to}}",
        )

        assert result.success is False
        assert "Mapping not found" in result.error

    # =========================================================================
    # Delete Output Mapping
    # =========================================================================

    def test_delete_output_mapping_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_output_mapping should delegate to use-case and reload on success."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.delete_output_mapping.return_value = OperationResult.ok(None)
        mock_schema_usecases.list_output_mappings_for_field.return_value = ()
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        result = viewmodel.delete_output_mapping(target="TEXT")

        assert result.success is True
        mock_schema_usecases.delete_output_mapping.assert_called_once_with(
            entity_id="entity1",
            field_id="field1",
            target="TEXT",
        )
        # Should reload output mappings and entities
        mock_schema_usecases.list_output_mappings_for_field.assert_called()
        mock_schema_usecases.get_all_entities.assert_called()

    def test_delete_output_mapping_when_no_field_selected(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_output_mapping should return error when no field selected."""
        result = viewmodel.delete_output_mapping(target="TEXT")

        assert result.success is False
        assert "No field selected" in result.error
        mock_schema_usecases.delete_output_mapping.assert_not_called()

    def test_delete_output_mapping_failure(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_output_mapping should return failure from use-case."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.delete_output_mapping.return_value = OperationResult.fail(
            "Mapping not found"
        )

        result = viewmodel.delete_output_mapping(target="TEXT")

        assert result.success is False
        assert "Mapping not found" in result.error

    # =========================================================================
    # Properties
    # =========================================================================

    def test_output_mappings_property(
        self,
        viewmodel: SchemaDesignerViewModel,
    ) -> None:
        """output_mappings property should return current output mappings."""
        output_mappings = (
            OutputMappingExportDTO(
                target="TEXT",
                formula_text="{{depth_from}} - {{depth_to}}",
            ),
        )
        viewmodel._output_mappings = output_mappings

        assert viewmodel.output_mappings == output_mappings

    def test_has_output_mappings_property_when_mappings_exist(
        self,
        viewmodel: SchemaDesignerViewModel,
    ) -> None:
        """has_output_mappings should return True when output mappings exist."""
        viewmodel._output_mappings = (
            OutputMappingExportDTO(
                target="TEXT",
                formula_text="{{depth_from}} - {{depth_to}}",
            ),
        )

        assert viewmodel.has_output_mappings is True

    def test_has_output_mappings_property_when_no_mappings(
        self,
        viewmodel: SchemaDesignerViewModel,
    ) -> None:
        """has_output_mappings should return False when no output mappings."""
        viewmodel._output_mappings = ()

        assert viewmodel.has_output_mappings is False

    # =========================================================================
    # Dispose (Phase F-13 cleanup)
    # =========================================================================

    def test_dispose_clears_output_mappings(
        self,
        viewmodel: SchemaDesignerViewModel,
    ) -> None:
        """dispose should clear output mappings state."""
        viewmodel._output_mappings = (
            OutputMappingExportDTO(
                target="TEXT",
                formula_text="{{depth_from}} - {{depth_to}}",
            ),
        )

        viewmodel.dispose()

        assert viewmodel._output_mappings == ()

"""Tests for SchemaDesignerViewModel control rules operations (Phase F-11).

Tests the persisted control rules features added in Phase F-11.

PHASE F-11 COMPLIANCE:
- Design-time only operations
- NO runtime enforcement
- NO execution against live data
- Delegates to SchemaUseCases for all operations

ARCHITECTURAL NOTE (Rule 0 Compliance):
- ViewModel constructor takes SchemaUseCases (application layer use-case)
- NOT individual queries/commands or repositories
- All orchestration delegated to SchemaUseCases
"""

import pytest
from unittest.mock import MagicMock

from doc_helper.application.dto.export_dto import ControlRuleExportDTO
from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.dto.schema_dto import EntityDefinitionDTO, FieldDefinitionDTO
from doc_helper.application.usecases.schema_usecases import SchemaUseCases
from doc_helper.presentation.viewmodels.schema_designer_viewmodel import (
    SchemaDesignerViewModel,
)


class TestSchemaDesignerViewModelControlRules:
    """Tests for persisted control rules operations in SchemaDesignerViewModel (Phase F-11)."""

    @pytest.fixture
    def mock_schema_usecases(self) -> MagicMock:
        """Create mock SchemaUseCases (Rule 0 compliant)."""
        usecases = MagicMock(spec=SchemaUseCases)
        usecases.get_all_entities.return_value = ()
        usecases.get_all_relationships.return_value = ()
        usecases.get_field_validation_rules.return_value = ()
        usecases.get_entity_list_for_selection.return_value = ()
        usecases.list_control_rules_for_field.return_value = ()
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
    # Load Control Rules
    # =========================================================================

    def test_load_control_rules_when_no_field_selected(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """load_control_rules should clear control rules when no field selected."""
        viewmodel.load_control_rules()

        assert viewmodel.control_rules == ()
        assert viewmodel.has_control_rules is False
        mock_schema_usecases.list_control_rules_for_field.assert_not_called()

    def test_load_control_rules_when_field_selected(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """load_control_rules should load control rules from use-case when field selected."""
        # Setup field selection
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        # Setup mock return value
        control_rules = (
            ControlRuleExportDTO(
                rule_type="VISIBILITY",
                target_field_id="field2",
                formula_text="{{status}} == 'active'",
            ),
        )
        mock_schema_usecases.list_control_rules_for_field.return_value = control_rules

        viewmodel.load_control_rules()

        assert viewmodel.control_rules == control_rules
        assert viewmodel.has_control_rules is True
        mock_schema_usecases.list_control_rules_for_field.assert_called_once_with(
            entity_id="entity1",
            field_id="field1",
        )

    def test_load_control_rules_when_no_rules_exist(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """load_control_rules should handle empty control rules."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"
        mock_schema_usecases.list_control_rules_for_field.return_value = ()

        viewmodel.load_control_rules()

        assert viewmodel.control_rules == ()
        assert viewmodel.has_control_rules is False

    # =========================================================================
    # Select Field (Phase F-11 Integration)
    # =========================================================================

    def test_select_field_loads_control_rules(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """select_field should load control rules for the selected field."""
        viewmodel._selected_entity_id = "entity1"
        mock_schema_usecases.list_control_rules_for_field.return_value = ()

        viewmodel.select_field("field1")

        assert mock_schema_usecases.list_control_rules_for_field.called

    # =========================================================================
    # Add Control Rule
    # =========================================================================

    def test_add_control_rule_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_control_rule should delegate to use-case and reload on success."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.add_control_rule.return_value = OperationResult.ok("field1")
        mock_schema_usecases.list_control_rules_for_field.return_value = ()
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        result = viewmodel.add_control_rule(
            rule_type="VISIBILITY",
            target_field_id="field2",
            formula_text="{{status}} == 'active'",
        )

        assert result.success is True
        mock_schema_usecases.add_control_rule.assert_called_once_with(
            entity_id="entity1",
            field_id="field1",
            rule_type="VISIBILITY",
            formula_text="{{status}} == 'active'",
        )
        # Should reload control rules and entities
        mock_schema_usecases.list_control_rules_for_field.assert_called()
        mock_schema_usecases.get_all_entities.assert_called()

    def test_add_control_rule_when_no_field_selected(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_control_rule should return error when no field selected."""
        result = viewmodel.add_control_rule(
            rule_type="VISIBILITY",
            target_field_id="field2",
            formula_text="{{status}} == 'active'",
        )

        assert result.success is False
        assert "No field selected" in result.error
        mock_schema_usecases.add_control_rule.assert_not_called()

    def test_add_control_rule_failure_does_not_reload(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """add_control_rule should NOT reload on failure."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.add_control_rule.return_value = OperationResult.fail("Invalid formula")
        mock_schema_usecases.list_control_rules_for_field.reset_mock()
        mock_schema_usecases.get_all_entities.reset_mock()

        result = viewmodel.add_control_rule(
            rule_type="VISIBILITY",
            target_field_id="field2",
            formula_text="invalid formula",
        )

        assert result.success is False
        mock_schema_usecases.list_control_rules_for_field.assert_not_called()
        mock_schema_usecases.get_all_entities.assert_not_called()

    # =========================================================================
    # Update Control Rule
    # =========================================================================

    def test_update_control_rule_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """update_control_rule should delegate to use-case and reload on success."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.update_control_rule.return_value = OperationResult.ok("field1")
        mock_schema_usecases.list_control_rules_for_field.return_value = ()
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        result = viewmodel.update_control_rule(
            rule_type="VISIBILITY",
            formula_text="{{status}} == 'inactive'",
        )

        assert result.success is True
        mock_schema_usecases.update_control_rule.assert_called_once_with(
            entity_id="entity1",
            field_id="field1",
            rule_type="VISIBILITY",
            formula_text="{{status}} == 'inactive'",
        )
        # Should reload control rules and entities
        mock_schema_usecases.list_control_rules_for_field.assert_called()
        mock_schema_usecases.get_all_entities.assert_called()

    def test_update_control_rule_when_no_field_selected(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """update_control_rule should return error when no field selected."""
        result = viewmodel.update_control_rule(
            rule_type="VISIBILITY",
            formula_text="{{status}} == 'inactive'",
        )

        assert result.success is False
        assert "No field selected" in result.error
        mock_schema_usecases.update_control_rule.assert_not_called()

    def test_update_control_rule_failure(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """update_control_rule should return failure from use-case."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.update_control_rule.return_value = OperationResult.fail(
            "Rule not found"
        )

        result = viewmodel.update_control_rule(
            rule_type="VISIBILITY",
            formula_text="{{status}} == 'inactive'",
        )

        assert result.success is False
        assert "Rule not found" in result.error

    # =========================================================================
    # Delete Control Rule
    # =========================================================================

    def test_delete_control_rule_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_control_rule should delegate to use-case and reload on success."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.delete_control_rule.return_value = OperationResult.ok(None)
        mock_schema_usecases.list_control_rules_for_field.return_value = ()
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        result = viewmodel.delete_control_rule(rule_type="VISIBILITY")

        assert result.success is True
        mock_schema_usecases.delete_control_rule.assert_called_once_with(
            entity_id="entity1",
            field_id="field1",
            rule_type="VISIBILITY",
        )
        # Should reload control rules and entities
        mock_schema_usecases.list_control_rules_for_field.assert_called()
        mock_schema_usecases.get_all_entities.assert_called()

    def test_delete_control_rule_when_no_field_selected(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_control_rule should return error when no field selected."""
        result = viewmodel.delete_control_rule(rule_type="VISIBILITY")

        assert result.success is False
        assert "No field selected" in result.error
        mock_schema_usecases.delete_control_rule.assert_not_called()

    def test_delete_control_rule_failure(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """delete_control_rule should return failure from use-case."""
        viewmodel._selected_entity_id = "entity1"
        viewmodel._selected_field_id = "field1"

        mock_schema_usecases.delete_control_rule.return_value = OperationResult.fail(
            "Rule not found"
        )

        result = viewmodel.delete_control_rule(rule_type="VISIBILITY")

        assert result.success is False
        assert "Rule not found" in result.error

    # =========================================================================
    # Properties
    # =========================================================================

    def test_control_rules_property(
        self,
        viewmodel: SchemaDesignerViewModel,
    ) -> None:
        """control_rules property should return current control rules."""
        control_rules = (
            ControlRuleExportDTO(
                rule_type="VISIBILITY",
                target_field_id="field2",
                formula_text="{{status}} == 'active'",
            ),
        )
        viewmodel._control_rules = control_rules

        assert viewmodel.control_rules == control_rules

    def test_has_control_rules_property_when_rules_exist(
        self,
        viewmodel: SchemaDesignerViewModel,
    ) -> None:
        """has_control_rules should return True when control rules exist."""
        viewmodel._control_rules = (
            ControlRuleExportDTO(
                rule_type="VISIBILITY",
                target_field_id="field2",
                formula_text="{{status}} == 'active'",
            ),
        )

        assert viewmodel.has_control_rules is True

    def test_has_control_rules_property_when_no_rules(
        self,
        viewmodel: SchemaDesignerViewModel,
    ) -> None:
        """has_control_rules should return False when no control rules."""
        viewmodel._control_rules = ()

        assert viewmodel.has_control_rules is False

    # =========================================================================
    # Dispose (Phase F-11 cleanup)
    # =========================================================================

    def test_dispose_clears_control_rules(
        self,
        viewmodel: SchemaDesignerViewModel,
    ) -> None:
        """dispose should clear control rules state."""
        viewmodel._control_rules = (
            ControlRuleExportDTO(
                rule_type="VISIBILITY",
                target_field_id="field2",
                formula_text="{{status}} == 'active'",
            ),
        )

        viewmodel.dispose()

        assert viewmodel._control_rules == ()

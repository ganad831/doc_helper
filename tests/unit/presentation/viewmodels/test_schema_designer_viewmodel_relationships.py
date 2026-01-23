"""Tests for SchemaDesignerViewModel relationship features (Phase 6B - ADR-022).

Tests the relationship management features added to SchemaDesignerViewModel.

ARCHITECTURAL NOTE (Rule 0 Compliance):
- ViewModel constructor now takes SchemaUseCases (application layer use-case)
- NOT individual queries/commands or repositories
- All orchestration delegated to SchemaUseCases
"""

import pytest
from unittest.mock import MagicMock, Mock

from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.queries.schema.get_relationships_query import (
    RelationshipDTO,
)
from doc_helper.application.usecases.schema_usecases import SchemaUseCases
from doc_helper.presentation.viewmodels.schema_designer_viewmodel import (
    SchemaDesignerViewModel,
)


class TestSchemaDesignerViewModelRelationships:
    """Tests for relationship features in SchemaDesignerViewModel."""

    @pytest.fixture
    def mock_schema_usecases(self) -> MagicMock:
        """Create mock SchemaUseCases (Rule 0 compliant)."""
        usecases = MagicMock(spec=SchemaUseCases)
        usecases.get_all_entities.return_value = ()
        usecases.get_all_relationships.return_value = ()
        usecases.get_field_validation_rules.return_value = ()
        usecases.create_relationship.return_value = OperationResult.ok("test_relationship_id")
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

    # -------------------------------------------------------------------------
    # Constructor Tests
    # -------------------------------------------------------------------------

    def test_constructor_accepts_schema_usecases(
        self,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """ViewModel should accept SchemaUseCases dependency."""
        vm = SchemaDesignerViewModel(
            schema_usecases=mock_schema_usecases,
        )
        assert vm is not None
        assert vm._schema_usecases is mock_schema_usecases

    # -------------------------------------------------------------------------
    # Property Tests
    # -------------------------------------------------------------------------

    def test_relationships_property_initially_empty(
        self, viewmodel: SchemaDesignerViewModel
    ) -> None:
        """relationships property should be empty initially."""
        assert viewmodel.relationships == ()

    def test_entity_relationships_empty_when_no_entity_selected(
        self, viewmodel: SchemaDesignerViewModel
    ) -> None:
        """entity_relationships should be empty when no entity selected."""
        assert viewmodel.entity_relationships == ()

    def test_entity_relationships_filters_by_selected_entity(
        self, viewmodel: SchemaDesignerViewModel
    ) -> None:
        """entity_relationships should filter by selected entity."""
        # Setup: Inject test relationships
        viewmodel._relationships = (
            RelationshipDTO(
                id="rel1",
                source_entity_id="project",
                target_entity_id="borehole",
                relationship_type="CONTAINS",
                name_key="relationship.test1",
                description_key=None,
                inverse_name_key=None,
            ),
            RelationshipDTO(
                id="rel2",
                source_entity_id="borehole",
                target_entity_id="sample",
                relationship_type="CONTAINS",
                name_key="relationship.test2",
                description_key=None,
                inverse_name_key=None,
            ),
            RelationshipDTO(
                id="rel3",
                source_entity_id="sample",
                target_entity_id="lab",
                relationship_type="REFERENCES",
                name_key="relationship.test3",
                description_key=None,
                inverse_name_key=None,
            ),
        )

        # Act: Select "borehole" entity
        viewmodel._selected_entity_id = "borehole"

        # Assert: Should get relationships where borehole is source OR target
        result = viewmodel.entity_relationships
        assert len(result) == 2
        ids = {r.id for r in result}
        assert ids == {"rel1", "rel2"}

    # -------------------------------------------------------------------------
    # Load Relationships Tests
    # -------------------------------------------------------------------------

    def test_load_relationships_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """load_relationships should load via use-case."""
        # Setup
        mock_schema_usecases.get_all_relationships.return_value = ()

        # Act
        result = viewmodel.load_relationships()

        # Assert
        assert result is True
        mock_schema_usecases.get_all_relationships.assert_called_once()

    def test_load_relationships_notifies_change(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """load_relationships should notify 'relationships' change."""
        # Setup
        mock_schema_usecases.get_all_relationships.return_value = ()
        callback_called = False

        def on_change():
            nonlocal callback_called
            callback_called = True

        viewmodel.subscribe("relationships", on_change)

        # Act
        viewmodel.load_relationships()

        # Assert
        assert callback_called

    def test_load_entities_also_loads_relationships(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """load_entities should also call load_relationships."""
        # Setup
        mock_schema_usecases.get_all_entities.return_value = ()
        mock_schema_usecases.get_all_relationships.return_value = ()

        # Act
        viewmodel.load_entities()

        # Assert
        mock_schema_usecases.get_all_relationships.assert_called_once()

    # -------------------------------------------------------------------------
    # Select Entity Tests (Relationship Notification)
    # -------------------------------------------------------------------------

    def test_select_entity_notifies_entity_relationships(
        self, viewmodel: SchemaDesignerViewModel
    ) -> None:
        """select_entity should notify 'entity_relationships' change."""
        callback_called = False

        def on_change():
            nonlocal callback_called
            callback_called = True

        viewmodel.subscribe("entity_relationships", on_change)

        # Act
        viewmodel.select_entity("project")

        # Assert
        assert callback_called

    # -------------------------------------------------------------------------
    # Create Relationship Tests
    # -------------------------------------------------------------------------

    def test_create_relationship_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """create_relationship should create via use-case and reload."""
        # Setup
        mock_schema_usecases.create_relationship.return_value = OperationResult.ok("project_contains_boreholes")
        mock_schema_usecases.get_all_relationships.return_value = ()

        # Act
        result = viewmodel.create_relationship(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        # Assert
        assert result.success is True
        assert result.value == "project_contains_boreholes"
        mock_schema_usecases.create_relationship.assert_called_once_with(
            relationship_id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
            description_key=None,
            inverse_name_key=None,
        )

    def test_create_relationship_reloads_after_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """create_relationship should reload relationships after success."""
        # Setup
        mock_schema_usecases.create_relationship.return_value = OperationResult.ok("test")
        mock_schema_usecases.get_all_relationships.return_value = ()

        # Act
        viewmodel.create_relationship(
            relationship_id="test",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        # Assert - get_all_relationships called for reload after successful creation
        assert mock_schema_usecases.get_all_relationships.call_count >= 1

    def test_create_relationship_passes_optional_fields(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_schema_usecases: MagicMock,
    ) -> None:
        """create_relationship should pass optional fields to use-case."""
        # Setup
        mock_schema_usecases.create_relationship.return_value = OperationResult.ok("test")
        mock_schema_usecases.get_all_relationships.return_value = ()

        # Act
        result = viewmodel.create_relationship(
            relationship_id="test",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
            description_key="relationship.test.desc",
            inverse_name_key="relationship.test.inverse",
        )

        # Assert
        assert result.success is True
        mock_schema_usecases.create_relationship.assert_called_once_with(
            relationship_id="test",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
            description_key="relationship.test.desc",
            inverse_name_key="relationship.test.inverse",
        )

    # -------------------------------------------------------------------------
    # Entity List for Relationship Tests
    # -------------------------------------------------------------------------

    def test_get_entity_list_for_relationship_empty(
        self, viewmodel: SchemaDesignerViewModel, mock_schema_usecases: MagicMock
    ) -> None:
        """get_entity_list_for_relationship should return empty when no entities."""
        mock_schema_usecases.get_entity_list_for_selection.return_value = ()
        result = viewmodel.get_entity_list_for_relationship()
        assert result == ()

    def test_get_entity_list_for_relationship_returns_id_name_pairs(
        self, viewmodel: SchemaDesignerViewModel, mock_schema_usecases: MagicMock
    ) -> None:
        """get_entity_list_for_relationship should return (id, name) tuples."""
        # Setup: Configure mock to return entity pairs
        mock_schema_usecases.get_entity_list_for_selection.return_value = (
            ("project", "Project"),
            ("borehole", "Borehole"),
        )

        # Act
        result = viewmodel.get_entity_list_for_relationship()

        # Assert
        assert len(result) == 2
        assert result[0] == ("project", "Project")
        assert result[1] == ("borehole", "Borehole")

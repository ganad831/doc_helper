"""Tests for SchemaDesignerViewModel relationship features (Phase 6B - ADR-022).

Tests the relationship management features added to SchemaDesignerViewModel.

ARCHITECTURAL NOTE:
- ViewModel constructor now takes GetSchemaEntitiesQuery (application layer)
- NOT ISchemaRepository (domain layer) - Clean Architecture compliance
"""

import pytest
from unittest.mock import MagicMock, Mock

from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.queries.schema.get_relationships_query import (
    RelationshipDTO,
)
from doc_helper.domain.common.result import Success, Failure
from doc_helper.presentation.viewmodels.schema_designer_viewmodel import (
    SchemaDesignerViewModel,
)


class TestSchemaDesignerViewModelRelationships:
    """Tests for relationship features in SchemaDesignerViewModel."""

    @pytest.fixture
    def mock_schema_query(self) -> MagicMock:
        """Create mock schema query (application layer)."""
        query = MagicMock()
        query.execute.return_value = Success(())
        query.get_field_validation_rules.return_value = ()
        # Mock the internal repository for commands (accessed via _schema_repository)
        query._schema_repository = MagicMock()
        query._schema_repository.exists.return_value = True
        return query

    @pytest.fixture
    def mock_relationship_query(self) -> MagicMock:
        """Create mock relationship query (application layer)."""
        query = MagicMock()
        query.execute.return_value = Success(())
        return query

    @pytest.fixture
    def mock_create_relationship_fn(self) -> MagicMock:
        """Create mock relationship creator function (application layer)."""
        fn = MagicMock()
        fn.return_value = OperationResult.ok("test_relationship_id")
        return fn

    @pytest.fixture
    def mock_translation_service(self) -> MagicMock:
        """Create mock translation service."""
        service = MagicMock()
        service.get_current_language.return_value = "en"
        service.get.return_value = "Translated Text"
        return service

    @pytest.fixture
    def viewmodel(
        self,
        mock_schema_query: MagicMock,
        mock_translation_service: MagicMock,
        mock_relationship_query: MagicMock,
        mock_create_relationship_fn: MagicMock,
    ) -> SchemaDesignerViewModel:
        """Create viewmodel with all dependencies."""
        return SchemaDesignerViewModel(
            schema_query=mock_schema_query,
            translation_service=mock_translation_service,
            relationship_query=mock_relationship_query,
            create_relationship_fn=mock_create_relationship_fn,
        )

    # -------------------------------------------------------------------------
    # Constructor Tests
    # -------------------------------------------------------------------------

    def test_constructor_accepts_relationship_query(
        self,
        mock_schema_query: MagicMock,
        mock_translation_service: MagicMock,
        mock_relationship_query: MagicMock,
        mock_create_relationship_fn: MagicMock,
    ) -> None:
        """ViewModel should accept optional relationship query."""
        vm = SchemaDesignerViewModel(
            schema_query=mock_schema_query,
            translation_service=mock_translation_service,
            relationship_query=mock_relationship_query,
            create_relationship_fn=mock_create_relationship_fn,
        )
        assert vm is not None
        assert vm._relationship_query is mock_relationship_query
        assert vm._create_relationship_fn is mock_create_relationship_fn

    def test_constructor_works_without_relationship_query(
        self,
        mock_schema_query: MagicMock,
        mock_translation_service: MagicMock,
    ) -> None:
        """ViewModel should work without relationship query."""
        vm = SchemaDesignerViewModel(
            schema_query=mock_schema_query,
            translation_service=mock_translation_service,
            # No relationship_query or create_relationship_fn
        )
        assert vm is not None
        assert vm._relationship_query is None
        assert vm._create_relationship_fn is None

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
        mock_relationship_query: MagicMock,
    ) -> None:
        """load_relationships should load via query."""
        # Setup
        mock_relationship_query.execute.return_value = Success(())

        # Act
        result = viewmodel.load_relationships()

        # Assert
        assert result is True
        mock_relationship_query.execute.assert_called_once()

    def test_load_relationships_without_query(
        self,
        mock_schema_query: MagicMock,
        mock_translation_service: MagicMock,
    ) -> None:
        """load_relationships should succeed with empty result when no query."""
        vm = SchemaDesignerViewModel(
            schema_query=mock_schema_query,
            translation_service=mock_translation_service,
            # No relationship_query
        )

        result = vm.load_relationships()

        assert result is True
        assert vm.relationships == ()

    def test_load_relationships_notifies_change(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_relationship_query: MagicMock,
    ) -> None:
        """load_relationships should notify 'relationships' change."""
        # Setup
        mock_relationship_query.execute.return_value = Success(())
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
        mock_schema_query: MagicMock,
        mock_relationship_query: MagicMock,
    ) -> None:
        """load_entities should also call load_relationships."""
        # Setup
        mock_schema_query.execute.return_value = Success(())
        mock_relationship_query.execute.return_value = Success(())

        # Act
        viewmodel.load_entities()

        # Assert
        mock_relationship_query.execute.assert_called_once()

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
        mock_create_relationship_fn: MagicMock,
        mock_relationship_query: MagicMock,
    ) -> None:
        """create_relationship should create via function and reload."""
        # Setup
        mock_create_relationship_fn.return_value = OperationResult.ok("project_contains_boreholes")
        mock_relationship_query.execute.return_value = Success(())

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
        mock_create_relationship_fn.assert_called_once_with(
            "project_contains_boreholes",
            "project",
            "borehole",
            "CONTAINS",
            "relationship.test",
            None,  # description_key
            None,  # inverse_name_key
        )

    def test_create_relationship_without_function_fails(
        self,
        mock_schema_query: MagicMock,
        mock_translation_service: MagicMock,
    ) -> None:
        """create_relationship should fail when no function configured."""
        vm = SchemaDesignerViewModel(
            schema_query=mock_schema_query,
            translation_service=mock_translation_service,
            # No create_relationship_fn
        )

        result = vm.create_relationship(
            relationship_id="test",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        assert result.success is False
        assert "not configured" in result.error.lower()

    def test_create_relationship_reloads_after_success(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_create_relationship_fn: MagicMock,
        mock_relationship_query: MagicMock,
    ) -> None:
        """create_relationship should reload relationships after success."""
        # Setup
        mock_create_relationship_fn.return_value = OperationResult.ok("test")
        mock_relationship_query.execute.return_value = Success(())

        # Act
        viewmodel.create_relationship(
            relationship_id="test",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.test",
        )

        # Assert - execute called for reload after successful creation
        assert mock_relationship_query.execute.call_count >= 1

    def test_create_relationship_passes_optional_fields(
        self,
        viewmodel: SchemaDesignerViewModel,
        mock_create_relationship_fn: MagicMock,
        mock_relationship_query: MagicMock,
    ) -> None:
        """create_relationship should pass optional fields to function."""
        # Setup
        mock_create_relationship_fn.return_value = OperationResult.ok("test")
        mock_relationship_query.execute.return_value = Success(())

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
        mock_create_relationship_fn.assert_called_once_with(
            "test",
            "project",
            "borehole",
            "CONTAINS",
            "relationship.test",
            "relationship.test.desc",
            "relationship.test.inverse",
        )

    # -------------------------------------------------------------------------
    # Entity List for Relationship Tests
    # -------------------------------------------------------------------------

    def test_get_entity_list_for_relationship_empty(
        self, viewmodel: SchemaDesignerViewModel
    ) -> None:
        """get_entity_list_for_relationship should return empty when no entities."""
        result = viewmodel.get_entity_list_for_relationship()
        assert result == ()

    def test_get_entity_list_for_relationship_returns_id_name_pairs(
        self, viewmodel: SchemaDesignerViewModel
    ) -> None:
        """get_entity_list_for_relationship should return (id, name) tuples."""
        # Setup: Inject test entities via DTOs
        from doc_helper.application.dto.schema_dto import EntityDefinitionDTO

        viewmodel._entities = (
            EntityDefinitionDTO(
                id="project",
                name="Project",
                description=None,
                field_count=5,
                is_root_entity=True,
                parent_entity_id=None,
                fields=(),
            ),
            EntityDefinitionDTO(
                id="borehole",
                name="Borehole",
                description=None,
                field_count=10,
                is_root_entity=False,
                parent_entity_id=None,
                fields=(),
            ),
        )

        # Act
        result = viewmodel.get_entity_list_for_relationship()

        # Assert
        assert len(result) == 2
        assert result[0] == ("project", "Project")
        assert result[1] == ("borehole", "Borehole")

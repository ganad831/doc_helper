"""Tests for WelcomeViewModel AppType filtering."""

from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest

from doc_helper.app_types.contracts.app_type_metadata import AppTypeKind, AppTypeMetadata
from doc_helper.application.commands.create_project_command import CreateProjectCommand
from doc_helper.application.dto import AppTypeDTO
from doc_helper.application.queries.get_project_query import GetRecentProjectsQuery
from doc_helper.platform.discovery.manifest_parser import (
    ManifestCapabilities,
    ManifestSchema,
    ManifestTemplates,
    ParsedManifest,
)
from doc_helper.platform.registry.app_type_registry import AppTypeRegistry
from doc_helper.platform.registry.interfaces import IAppTypeRegistry
from doc_helper.platform.routing.app_type_router import AppTypeRouter, IAppTypeRouter
from doc_helper.presentation.viewmodels.welcome_viewmodel import WelcomeViewModel


def create_manifest(
    app_type_id: str,
    name: str,
    kind: AppTypeKind = AppTypeKind.DOCUMENT,
    version: str = "1.0.0",
) -> ParsedManifest:
    """Helper to create test manifests."""
    return ParsedManifest(
        metadata=AppTypeMetadata(
            app_type_id=app_type_id,
            name=name,
            version=version,
            kind=kind,
        ),
        schema=ManifestSchema(source="config.db", schema_type="sqlite"),
        templates=ManifestTemplates(),
        capabilities=ManifestCapabilities(),
        manifest_path=Path(f"app_types/{app_type_id}/manifest.json"),
    )


class TestWelcomeViewModelAppTypeFiltering:
    """Tests for AppType filtering in WelcomeViewModel."""

    @pytest.fixture
    def mock_recent_query(self) -> MagicMock:
        """Create mock GetRecentProjectsQuery."""
        return MagicMock(spec=GetRecentProjectsQuery)

    @pytest.fixture
    def mock_create_command(self) -> MagicMock:
        """Create mock CreateProjectCommand."""
        return MagicMock(spec=CreateProjectCommand)

    @pytest.fixture
    def registry_with_mixed_apptypes(self) -> AppTypeRegistry:
        """Create registry with both DOCUMENT and TOOL AppTypes."""
        registry = AppTypeRegistry()
        registry.register(
            create_manifest("soil_investigation", "Soil Investigation", AppTypeKind.DOCUMENT)
        )
        registry.register(
            create_manifest("structural_report", "Structural Report", AppTypeKind.DOCUMENT)
        )
        registry.register(
            create_manifest("schema_designer", "Schema Designer", AppTypeKind.TOOL)
        )
        return registry

    @pytest.fixture
    def router(self, registry_with_mixed_apptypes: AppTypeRegistry) -> AppTypeRouter:
        """Create router with registry."""
        return AppTypeRouter(registry_with_mixed_apptypes)

    @pytest.fixture
    def viewmodel(
        self,
        mock_recent_query: MagicMock,
        mock_create_command: MagicMock,
        registry_with_mixed_apptypes: AppTypeRegistry,
        router: AppTypeRouter,
    ) -> WelcomeViewModel:
        """Create WelcomeViewModel with mixed AppTypes."""
        return WelcomeViewModel(
            get_recent_query=mock_recent_query,
            create_project_command=mock_create_command,
            app_type_registry=registry_with_mixed_apptypes,
            app_type_router=router,
        )

    def test_get_available_app_types_returns_only_document(
        self, viewmodel: WelcomeViewModel
    ) -> None:
        """get_available_app_types should return only DOCUMENT AppTypes."""
        app_types = viewmodel.get_available_app_types()

        assert len(app_types) == 2
        assert all(dto.kind == "document" for dto in app_types)
        app_type_ids = [dto.app_type_id for dto in app_types]
        assert "soil_investigation" in app_type_ids
        assert "structural_report" in app_type_ids
        assert "schema_designer" not in app_type_ids

    def test_get_tool_app_types_returns_only_tool(
        self, viewmodel: WelcomeViewModel
    ) -> None:
        """get_tool_app_types should return only TOOL AppTypes."""
        tools = viewmodel.get_tool_app_types()

        assert len(tools) == 1
        assert all(dto.kind == "tool" for dto in tools)
        assert tools[0].app_type_id == "schema_designer"
        assert tools[0].name == "Schema Designer"

    def test_has_tool_app_types_true_when_tools_exist(
        self, viewmodel: WelcomeViewModel
    ) -> None:
        """has_tool_app_types should return True when TOOL AppTypes exist."""
        assert viewmodel.has_tool_app_types() is True

    def test_has_tool_app_types_false_when_no_tools(
        self,
        mock_recent_query: MagicMock,
        mock_create_command: MagicMock,
    ) -> None:
        """has_tool_app_types should return False when no TOOL AppTypes exist."""
        registry = AppTypeRegistry()
        registry.register(
            create_manifest("soil_investigation", "Soil Investigation", AppTypeKind.DOCUMENT)
        )
        router = AppTypeRouter(registry)
        viewmodel = WelcomeViewModel(
            get_recent_query=mock_recent_query,
            create_project_command=mock_create_command,
            app_type_registry=registry,
            app_type_router=router,
        )

        assert viewmodel.has_tool_app_types() is False

    def test_get_available_app_types_includes_kind_in_dto(
        self, viewmodel: WelcomeViewModel
    ) -> None:
        """AppTypeDTO should include the kind field."""
        app_types = viewmodel.get_available_app_types()

        for dto in app_types:
            assert hasattr(dto, "kind")
            assert dto.kind == "document"
            assert dto.is_document is True
            assert dto.is_tool is False

    def test_get_tool_app_types_includes_kind_in_dto(
        self, viewmodel: WelcomeViewModel
    ) -> None:
        """AppTypeDTO from get_tool_app_types should include correct kind."""
        tools = viewmodel.get_tool_app_types()

        for dto in tools:
            assert dto.kind == "tool"
            assert dto.is_tool is True
            assert dto.is_document is False


class TestWelcomeViewModelLaunchTool:
    """Tests for launch_tool in WelcomeViewModel."""

    @pytest.fixture
    def mock_recent_query(self) -> MagicMock:
        """Create mock GetRecentProjectsQuery."""
        return MagicMock(spec=GetRecentProjectsQuery)

    @pytest.fixture
    def mock_create_command(self) -> MagicMock:
        """Create mock CreateProjectCommand."""
        return MagicMock(spec=CreateProjectCommand)

    @pytest.fixture
    def registry_with_tool(self) -> AppTypeRegistry:
        """Create registry with a TOOL AppType."""
        registry = AppTypeRegistry()
        registry.register(
            create_manifest("schema_designer", "Schema Designer", AppTypeKind.TOOL)
        )
        registry.register(
            create_manifest("soil_investigation", "Soil Investigation", AppTypeKind.DOCUMENT)
        )
        return registry

    @pytest.fixture
    def router(self, registry_with_tool: AppTypeRegistry) -> AppTypeRouter:
        """Create router with registry."""
        return AppTypeRouter(registry_with_tool)

    @pytest.fixture
    def viewmodel(
        self,
        mock_recent_query: MagicMock,
        mock_create_command: MagicMock,
        registry_with_tool: AppTypeRegistry,
        router: AppTypeRouter,
    ) -> WelcomeViewModel:
        """Create WelcomeViewModel with tool AppType."""
        return WelcomeViewModel(
            get_recent_query=mock_recent_query,
            create_project_command=mock_create_command,
            app_type_registry=registry_with_tool,
            app_type_router=router,
        )

    def test_launch_tool_success(self, viewmodel: WelcomeViewModel) -> None:
        """launch_tool should succeed for valid TOOL AppType."""
        success, error = viewmodel.launch_tool("schema_designer")

        assert success is True
        assert error is None

    def test_launch_tool_fails_for_document(self, viewmodel: WelcomeViewModel) -> None:
        """launch_tool should fail for DOCUMENT AppType."""
        success, error = viewmodel.launch_tool("soil_investigation")

        assert success is False
        assert error is not None
        assert "not a TOOL" in error

    def test_launch_tool_fails_for_nonexistent(self, viewmodel: WelcomeViewModel) -> None:
        """launch_tool should fail for nonexistent AppType."""
        success, error = viewmodel.launch_tool("nonexistent")

        assert success is False
        assert error is not None
        assert "not found" in error

    def test_launch_tool_sets_error_message_on_failure(
        self, viewmodel: WelcomeViewModel
    ) -> None:
        """launch_tool should set error_message on failure."""
        viewmodel.launch_tool("nonexistent")

        assert viewmodel.error_message is not None
        assert "not found" in viewmodel.error_message

    def test_launch_tool_clears_error_on_success(
        self, viewmodel: WelcomeViewModel
    ) -> None:
        """launch_tool should clear error_message on success."""
        # Set an error first
        viewmodel._error_message = "Previous error"

        viewmodel.launch_tool("schema_designer")

        assert viewmodel.error_message is None

    def test_launch_tool_without_router_fails(
        self,
        mock_recent_query: MagicMock,
        mock_create_command: MagicMock,
        registry_with_tool: AppTypeRegistry,
    ) -> None:
        """launch_tool should fail gracefully when router is not configured."""
        viewmodel = WelcomeViewModel(
            get_recent_query=mock_recent_query,
            create_project_command=mock_create_command,
            app_type_registry=registry_with_tool,
            app_type_router=None,  # No router
        )

        success, error = viewmodel.launch_tool("schema_designer")

        assert success is False
        assert error is not None
        assert "not configured" in error

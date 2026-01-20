"""Integration tests for composition root.

These tests verify that the DI container is configured correctly
and all services can be resolved without errors.

RULES (AGENT_RULES.md Section 2):
- Domain layer has zero dependencies (not in container)
- Presentation → Application only
- Application → Domain only
- Infrastructure implements domain interfaces
"""

import pytest
from pathlib import Path
import sys

# Import main module to get configure_container
from doc_helper.main import configure_container
from doc_helper.application.commands.create_project_command import CreateProjectCommand
from doc_helper.application.queries.get_project_query import GetRecentProjectsQuery
from doc_helper.application.services.formula_service import FormulaService
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.application.services.control_service import ControlService
from doc_helper.application.document.document_generation_service import DocumentGenerationService
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.document.transformer_registry import TransformerRegistry
from doc_helper.infrastructure.document.word_document_adapter import WordDocumentAdapter
from doc_helper.infrastructure.document.excel_document_adapter import ExcelDocumentAdapter
from doc_helper.infrastructure.document.pdf_document_adapter import PdfDocumentAdapter
from doc_helper.presentation.viewmodels.welcome_viewmodel import WelcomeViewModel


class TestCompositionRoot:
    """Tests for DI composition root."""

    @pytest.fixture
    def container(self):
        """Create configured container for testing."""
        return configure_container()

    def test_container_not_none(self, container):
        """Test container is created."""
        assert container is not None

    @pytest.mark.skip(reason="Requires config.db file which may not exist in test environment")
    def test_resolve_schema_repository(self, container):
        """Test schema repository can be resolved."""
        repo = container.resolve(ISchemaRepository)
        assert repo is not None
        assert isinstance(repo, ISchemaRepository)

    def test_resolve_project_repository(self, container):
        """Test project repository can be resolved."""
        repo = container.resolve(IProjectRepository)
        assert repo is not None
        assert isinstance(repo, IProjectRepository)

    def test_resolve_transformer_registry(self, container):
        """Test transformer registry can be resolved."""
        registry = container.resolve(TransformerRegistry)
        assert registry is not None
        assert isinstance(registry, TransformerRegistry)

        # Verify transformers are registered
        assert registry.has("uppercase")
        assert registry.has("lowercase")
        assert registry.has("number")
        assert registry.has("date")
        assert registry.has("boolean")

    def test_resolve_document_adapters(self, container):
        """Test document adapters can be resolved."""
        word = container.resolve(WordDocumentAdapter)
        excel = container.resolve(ExcelDocumentAdapter)
        pdf = container.resolve(PdfDocumentAdapter)

        assert word is not None
        assert excel is not None
        assert pdf is not None

    def test_resolve_application_services(self, container):
        """Test application services can be resolved."""
        formula_svc = container.resolve(FormulaService)
        validation_svc = container.resolve(ValidationService)
        control_svc = container.resolve(ControlService)
        doc_gen_svc = container.resolve(DocumentGenerationService)

        assert formula_svc is not None
        assert validation_svc is not None
        assert control_svc is not None
        assert doc_gen_svc is not None

    def test_resolve_commands(self, container):
        """Test commands can be resolved."""
        create_cmd = container.resolve(CreateProjectCommand)
        assert create_cmd is not None

    def test_resolve_queries(self, container):
        """Test queries can be resolved."""
        recent_query = container.resolve(GetRecentProjectsQuery)
        assert recent_query is not None

    def test_resolve_viewmodels(self, container):
        """Test viewmodels can be resolved."""
        welcome_vm = container.resolve(WelcomeViewModel)
        assert welcome_vm is not None

    @pytest.mark.skip(reason="Requires config.db file which may not exist in test environment")
    def test_singleton_lifetime_schema_repository(self, container):
        """Test schema repository is singleton."""
        repo1 = container.resolve(ISchemaRepository)
        repo2 = container.resolve(ISchemaRepository)
        assert repo1 is repo2

    def test_scoped_lifetime_project_repository(self, container):
        """Test project repository is scoped."""
        repo1 = container.resolve(IProjectRepository)
        repo2 = container.resolve(IProjectRepository)

        # Same scope - same instance
        assert repo1 is repo2

        # New scope - new instance
        container.begin_scope()
        repo3 = container.resolve(IProjectRepository)
        assert repo3 is not repo1

    def test_singleton_lifetime_formula_service(self, container):
        """Test formula service is singleton."""
        svc1 = container.resolve(FormulaService)
        svc2 = container.resolve(FormulaService)
        assert svc1 is svc2

    def test_singleton_lifetime_welcome_viewmodel(self, container):
        """Test welcome viewmodel is singleton."""
        vm1 = container.resolve(WelcomeViewModel)
        vm2 = container.resolve(WelcomeViewModel)
        assert vm1 is vm2

    def test_all_registered_services_resolve_without_error(self, container):
        """Test all registered services can be resolved without errors.

        This is a smoke test to ensure the entire dependency graph is valid.
        """
        # Skip ISchemaRepository as it requires config.db file
        services = [
            IProjectRepository,
            TransformerRegistry,
            WordDocumentAdapter,
            ExcelDocumentAdapter,
            PdfDocumentAdapter,
            FormulaService,
            ValidationService,
            ControlService,
            DocumentGenerationService,
            CreateProjectCommand,
            GetRecentProjectsQuery,
            WelcomeViewModel,
        ]

        for service_type in services:
            service = container.resolve(service_type)
            assert service is not None, f"Failed to resolve {service_type.__name__}"

    def test_container_clear(self, container):
        """Test container clear removes all registrations."""
        # Resolve a service to ensure it's cached
        _ = container.resolve(FormulaService)

        # Clear
        container.clear()

        # Should not be registered anymore
        assert not container.is_registered(FormulaService)

    def test_scope_management(self, container):
        """Test scope begin/end works correctly."""
        # Resolve scoped service
        repo1 = container.resolve(IProjectRepository)

        # End scope
        container.end_scope()

        # Resolve again - should be new instance
        repo2 = container.resolve(IProjectRepository)
        assert repo2 is not repo1

        # Begin scope
        container.begin_scope()

        # Resolve again - should be new instance
        repo3 = container.resolve(IProjectRepository)
        assert repo3 is not repo2
        assert repo3 is not repo1


class TestDependencyWiring:
    """Tests to verify dependencies are wired correctly."""

    @pytest.fixture
    def container(self):
        """Create configured container for testing."""
        return configure_container()

    def test_create_project_command_has_repository(self, container):
        """Test CreateProjectCommand is wired with repository."""
        cmd = container.resolve(CreateProjectCommand)

        # Command should have a repository (check internal state)
        assert cmd._project_repository is not None
        assert isinstance(cmd._project_repository, IProjectRepository)

    def test_welcome_viewmodel_has_dependencies(self, container):
        """Test WelcomeViewModel is wired with query and command."""
        vm = container.resolve(WelcomeViewModel)

        # ViewModel should have query and command
        assert vm._get_recent_query is not None
        assert vm._create_project_command is not None
        assert isinstance(vm._get_recent_query, GetRecentProjectsQuery)
        assert isinstance(vm._create_project_command, CreateProjectCommand)

    def test_document_generation_service_has_dependencies(self, container):
        """Test DocumentGenerationService is wired with adapters and registry."""
        svc = container.resolve(DocumentGenerationService)

        # Service should have adapters and transformer registry
        assert svc._adapters is not None
        assert svc._transformer_registry is not None
        assert len(svc._adapters) == 3  # word, excel, pdf
        assert isinstance(svc._transformer_registry, TransformerRegistry)

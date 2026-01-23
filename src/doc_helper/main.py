"""Main entry point for Doc Helper application.

This is the composition root where all dependencies are wired together.

ARCHITECTURAL RULES (AGENT_RULES.md Section 2):
- Presentation → Application only
- Application → Domain only
- Infrastructure → Domain + Application
- Domain → NOTHING

LIFETIME RULES:
- Singleton: Shared across application (repositories, registries, adapters)
- Scoped: Per-project session (cleared on project open/close)
- Transient: Created each time (rarely used)

V2 PLATFORM INTEGRATION:
- AppTypes discovered from app_types/ directory at startup
- Schema loading routed through AppType implementation
- Projects associated with app_type_id for multi-app-type support
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from doc_helper.application.commands.create_project_command import (
    CreateProjectCommand,
)
from doc_helper.application.commands.export_project_command import (
    ExportProjectCommand,
)
from doc_helper.application.commands.import_project_command import (
    ImportProjectCommand,
)
from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.commands.update_field_command import UpdateFieldCommand
from doc_helper.application.queries.get_field_history_query import (
    GetFieldHistoryQuery,
)
from doc_helper.application.queries.search_fields_query import SearchFieldsQuery
from doc_helper.application.document.document_generation_service import (
    DocumentGenerationService,
)
from doc_helper.application.queries.get_project_query import GetProjectQuery
from doc_helper.application.queries.get_project_query import GetRecentProjectsQuery
from doc_helper.application.services.control_service import ControlService
from doc_helper.application.services.field_service import FieldService
from doc_helper.application.services.formula_service import FormulaService
from doc_helper.application.services.override_service import OverrideService
from doc_helper.application.services.translation_service import TranslationApplicationService
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.domain.override.repositories import IOverrideRepository
from doc_helper.domain.project.field_history_repository import IFieldHistoryRepository
from doc_helper.application.search import ISearchRepository
from doc_helper.infrastructure.persistence.sqlite_override_repository import (
    SqliteOverrideRepository,
)
from doc_helper.infrastructure.persistence.sqlite_field_history_repository import (
    SqliteFieldHistoryRepository,
)
from doc_helper.infrastructure.persistence.sqlite_search_repository import (
    SqliteSearchRepository,
)
from doc_helper.infrastructure.interchange.json_project_exporter import (
    JsonProjectExporter,
)
from doc_helper.infrastructure.interchange.json_project_importer import (
    JsonProjectImporter,
)
from doc_helper.domain.document.transformer_registry import TransformerRegistry
from doc_helper.domain.document.transformers import (
    BooleanTransformer,
    CapitalizeTransformer,
    ConcatTransformer,
    CurrencyTransformer,
    DateTimeTransformer,
    DateTransformer,
    DecimalTransformer,
    IfEmptyTransformer,
    IfNullTransformer,
    IntegerTransformer,
    LowercaseTransformer,
    NumberTransformer,
    ReplaceTransformer,
    SubstringTransformer,
    TimeTransformer,
    TitleTransformer,
    UppercaseTransformer,
    YesNoTransformer,
)
from doc_helper.domain.common.translation import ITranslationService
from doc_helper.domain.project.project_repository import IProjectRepository
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.infrastructure.di.container import (
    Container,
    register_navigation_services,
    register_undo_services,
)
from doc_helper.infrastructure.i18n.json_translation_service import (
    JsonTranslationService,
)
from doc_helper.presentation.adapters.qt_translation_adapter import QtTranslationAdapter
from doc_helper.infrastructure.document.excel_document_adapter import (
    ExcelDocumentAdapter,
)
from doc_helper.infrastructure.document.pdf_document_adapter import PdfDocumentAdapter
from doc_helper.infrastructure.document.word_document_adapter import (
    WordDocumentAdapter,
)
from doc_helper.infrastructure.persistence.sqlite_project_repository import (
    SqliteProjectRepository,
)
from doc_helper.infrastructure.persistence.sqlite_schema_repository import (
    SqliteSchemaRepository,
)
from doc_helper.presentation.viewmodels.project_viewmodel import ProjectViewModel
from doc_helper.presentation.viewmodels.welcome_viewmodel import WelcomeViewModel
from doc_helper.presentation.views.welcome_view import WelcomeView

# Platform imports (v2 architecture)
from doc_helper.platform.discovery.app_type_discovery_service import (
    AppTypeDiscoveryService,
)
from doc_helper.platform.platform_services import PlatformServices
from doc_helper.platform.registry.app_type_registry import AppTypeRegistry
from doc_helper.platform.routing.app_type_router import AppTypeRouter, IAppTypeRouter

# AppType implementations
from doc_helper.app_types.soil_investigation import (
    SoilInvestigationAppType,
    DEFAULT_APP_TYPE_ID,
)
from doc_helper.app_types.schema_designer import SchemaDesignerAppType


def configure_container() -> Container:
    """Configure the dependency injection container.

    This is the single composition root for the entire application.

    Returns:
        Configured container with all services registered
    """
    container = Container()

    # ========================================================================
    # PLATFORM: AppType Discovery and Registry (v2 Architecture)
    # ========================================================================

    # Create platform infrastructure
    app_type_registry = AppTypeRegistry()
    app_type_router = AppTypeRouter(app_type_registry)

    # Discover AppTypes from app_types/ directory
    # Note: For v1, we also manually register SoilInvestigationAppType
    # to ensure it's available even if discovery doesn't find manifest
    app_types_dir = Path(__file__).parent / "app_types"
    discovery_service = AppTypeDiscoveryService()
    discovery_result = discovery_service.discover(app_types_dir)

    # Register discovered AppTypes
    for manifest in discovery_result.manifests:
        app_type_registry.register(manifest)

    # For v1 compatibility: Set soil_investigation as current AppType
    # This ensures schema loading works through the AppType
    if app_type_registry.exists(DEFAULT_APP_TYPE_ID):
        app_type_router.set_current(DEFAULT_APP_TYPE_ID)

    # Register platform services in container
    container.register_instance(AppTypeRegistry, app_type_registry)
    container.register_instance(IAppTypeRouter, app_type_router)

    # ========================================================================
    # INFRASTRUCTURE: Persistence (Singleton)
    # ========================================================================

    # Schema repository - routed through AppType (v2 platform integration)
    # For v1: Uses soil_investigation AppType's schema repository
    # The path is determined by the AppType package location
    # Note: In test environments, config.db may not exist - handle gracefully
    soil_app_type = SoilInvestigationAppType()
    try:
        schema_repository = soil_app_type.get_schema_repository()
        container.register_instance(ISchemaRepository, schema_repository)
    except FileNotFoundError:
        # Schema database not found - this is OK for tests
        # Production deployments must ensure config.db exists
        pass

    # Project repository - scoped (per-project session)
    # Note: v1 uses a single database file for all projects,
    # but the repository instance is scoped to ensure proper lifecycle management.
    # New instance created on begin_scope(), cleared on end_scope().
    projects_db_path = Path("data/projects.db")
    container.register_scoped(
        IProjectRepository,
        lambda: SqliteProjectRepository(db_path=projects_db_path),
    )

    # Override repository - SQLite persistent storage
    # Note: Overrides stored in same database as projects for simplicity
    container.register_singleton(
        IOverrideRepository,
        lambda: SqliteOverrideRepository(db_path=projects_db_path),
    )

    # Field History repository - SQLite persistent storage (ADR-027)
    # Note: Field history stored in same database as projects
    container.register_singleton(
        IFieldHistoryRepository,
        lambda: SqliteFieldHistoryRepository(db_path=projects_db_path),
    )

    # Search repository - SQLite implementation (ADR-026)
    # Note: Search operates on project database
    container.register_singleton(
        ISearchRepository,
        lambda: SqliteSearchRepository(db_path=projects_db_path),
    )

    # ========================================================================
    # INFRASTRUCTURE: Import/Export Services (Singleton - ADR-039)
    # ========================================================================

    # JSON Project Exporter - Serializes projects to JSON interchange format
    container.register_singleton(
        JsonProjectExporter,
        lambda: JsonProjectExporter(),
    )

    # JSON Project Importer - Deserializes projects from JSON interchange format
    container.register_singleton(
        JsonProjectImporter,
        lambda: JsonProjectImporter(),
    )

    # ========================================================================
    # INFRASTRUCTURE: i18n Service (Singleton)
    # ========================================================================

    # Translation service - loads translations from JSON files
    translations_dir = Path("translations")
    container.register_singleton(
        ITranslationService,
        lambda: JsonTranslationService(translations_dir=translations_dir),
    )

    # ========================================================================
    # INFRASTRUCTURE: Document Adapters (Singleton)
    # ========================================================================

    # Word adapter
    word_adapter = WordDocumentAdapter()
    container.register_instance(WordDocumentAdapter, word_adapter)

    # Excel adapter
    excel_adapter = ExcelDocumentAdapter()
    container.register_instance(ExcelDocumentAdapter, excel_adapter)

    # PDF adapter
    pdf_adapter = PdfDocumentAdapter()
    container.register_instance(PdfDocumentAdapter, pdf_adapter)

    # ========================================================================
    # DOMAIN: Transformer Registry (Singleton)
    # ========================================================================

    # Create and populate transformer registry
    transformer_registry = TransformerRegistry()

    # Register text transformers
    transformer_registry.register(UppercaseTransformer())
    transformer_registry.register(LowercaseTransformer())
    transformer_registry.register(CapitalizeTransformer())
    transformer_registry.register(TitleTransformer())

    # Register number transformers
    transformer_registry.register(NumberTransformer())
    transformer_registry.register(DecimalTransformer())
    transformer_registry.register(IntegerTransformer())

    # Register date transformers
    transformer_registry.register(DateTransformer())
    transformer_registry.register(DateTimeTransformer())
    transformer_registry.register(TimeTransformer())

    # Register currency transformers
    transformer_registry.register(CurrencyTransformer())

    # Register boolean transformers
    transformer_registry.register(BooleanTransformer())
    transformer_registry.register(YesNoTransformer())

    # Register string operation transformers
    transformer_registry.register(ConcatTransformer())
    transformer_registry.register(SubstringTransformer())
    transformer_registry.register(ReplaceTransformer())

    # Register conditional transformers
    transformer_registry.register(IfEmptyTransformer())
    transformer_registry.register(IfNullTransformer())

    container.register_instance(TransformerRegistry, transformer_registry)

    # ========================================================================
    # PLATFORM: TOOL AppType Initialization
    # ========================================================================

    # Create PlatformServices for AppType initialization
    # Note: ITranslationService must be resolved (registered above)
    translation_service = container.resolve(ITranslationService)
    platform_services = PlatformServices(
        translation_service=translation_service,
        transformer_registry=transformer_registry,
    )

    # Initialize TOOL AppTypes that need to be accessible from WelcomeView
    schema_designer_app_type = SchemaDesignerAppType()
    schema_designer_app_type.initialize(platform_services)

    # Store initialized tool AppTypes for WelcomeViewModel
    tool_app_types: dict[str, object] = {
        schema_designer_app_type.app_type_id: schema_designer_app_type,
    }

    # ========================================================================
    # APPLICATION: Services (Singleton - Stateless)
    # ========================================================================

    # Formula service (stateless)
    container.register_singleton(
        FormulaService,
        lambda: FormulaService(),
    )

    # Validation service (stateless)
    container.register_singleton(
        ValidationService,
        lambda: ValidationService(),
    )

    # Control service (stateless)
    container.register_singleton(
        ControlService,
        lambda: ControlService(),
    )

    # Document generation service
    container.register_singleton(
        DocumentGenerationService,
        lambda: DocumentGenerationService(
            adapters={
                DocumentFormat.WORD.value: container.resolve(WordDocumentAdapter),
                DocumentFormat.EXCEL.value: container.resolve(ExcelDocumentAdapter),
                DocumentFormat.PDF.value: container.resolve(PdfDocumentAdapter),
            },
            transformer_registry=container.resolve(TransformerRegistry),
        ),
    )

    # ========================================================================
    # APPLICATION: Commands & Queries (Singleton - Stateless)
    # ========================================================================

    # Commands
    container.register_singleton(
        CreateProjectCommand,
        lambda: CreateProjectCommand(
            project_repository=container.resolve(IProjectRepository),
            app_type_registry=container.resolve(AppTypeRegistry),
        ),
    )

    container.register_singleton(
        UpdateFieldCommand,
        lambda: UpdateFieldCommand(
            project_repository=container.resolve(IProjectRepository),
        ),
    )

    container.register_singleton(
        SaveProjectCommand,
        lambda: SaveProjectCommand(
            project_repository=container.resolve(IProjectRepository),
        ),
    )

    # Import/Export commands (ADR-039)
    container.register_singleton(
        ExportProjectCommand,
        lambda: ExportProjectCommand(
            project_repository=container.resolve(IProjectRepository),
            schema_repository=container.resolve(ISchemaRepository),
            project_exporter=container.resolve(JsonProjectExporter),
        ),
    )

    container.register_singleton(
        ImportProjectCommand,
        lambda: ImportProjectCommand(
            project_repository=container.resolve(IProjectRepository),
            schema_repository=container.resolve(ISchemaRepository),
            project_importer=container.resolve(JsonProjectImporter),
            validation_service=container.resolve(ValidationService),
            app_type_registry=container.resolve(IAppTypeRegistry),
        ),
    )

    # Queries
    container.register_singleton(
        GetRecentProjectsQuery,
        lambda: GetRecentProjectsQuery(
            project_repository=container.resolve(IProjectRepository),
        ),
    )

    container.register_singleton(
        GetProjectQuery,
        lambda: GetProjectQuery(
            project_repository=container.resolve(IProjectRepository),
        ),
    )

    # Search query (ADR-026)
    container.register_singleton(
        SearchFieldsQuery,
        lambda: SearchFieldsQuery(
            search_repository=container.resolve(ISearchRepository),
        ),
    )

    # Field History query (ADR-027)
    container.register_singleton(
        GetFieldHistoryQuery,
        lambda: GetFieldHistoryQuery(
            field_history_repository=container.resolve(IFieldHistoryRepository),
        ),
    )

    # ========================================================================
    # APPLICATION: Field and Override Services (Singleton - U6 Phase 7)
    # ========================================================================

    # Field service - wraps UpdateFieldCommand for undo integration
    container.register_singleton(
        FieldService,
        lambda: FieldService(
            update_field_command=container.resolve(UpdateFieldCommand),
            get_project_query=container.resolve(GetProjectQuery),
        ),
    )

    # Override service - stub implementation for Phase 7
    # Full implementation deferred to override UI integration
    container.register_singleton(
        OverrideService,
        lambda: OverrideService(
            override_repository=container.resolve(IOverrideRepository),
        ),
    )

    # ========================================================================
    # APPLICATION: Undo Infrastructure (Singleton - U6 Phase 7)
    # ========================================================================

    # Register undo services: UndoManager, FieldUndoService, OverrideUndoService, HistoryAdapter
    register_undo_services(
        container,
        field_service=container.resolve(FieldService),
        override_service=container.resolve(OverrideService),
    )

    # ========================================================================
    # APPLICATION: Navigation Infrastructure (Singleton - U7)
    # ========================================================================

    # Register navigation services: NavigationHistory, NavigationAdapter
    register_navigation_services(container)

    # ========================================================================
    # PRESENTATION: ViewModels (Scoped - Per Project Session)
    # ========================================================================

    # WelcomeViewModel (singleton - no project context, v2 PHASE 4: AppType-aware)
    # Note: tool_app_types captured from PLATFORM section above
    container.register_singleton(
        WelcomeViewModel,
        lambda tool_types=tool_app_types: WelcomeViewModel(
            get_recent_query=container.resolve(GetRecentProjectsQuery),
            create_project_command=container.resolve(CreateProjectCommand),
            app_type_registry=container.resolve(AppTypeRegistry),
            app_type_router=container.resolve(IAppTypeRouter),
            tool_app_types=tool_types,
        ),
    )

    # TODO: Register remaining ViewModels
    # - ProjectViewModel (scoped)
    # - FieldViewModel (scoped)
    # - EntityViewModel (scoped)
    # - SchemaEditorViewModel (singleton)
    # - OverrideViewModel (scoped)
    # - DocumentGenerationViewModel (scoped)

    return container


def create_app(container: Container) -> QApplication:
    """Create and configure Qt application.

    Args:
        container: Configured DI container

    Returns:
        Configured QApplication instance
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Doc Helper")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Doc Helper")

    return app


def main() -> int:
    """Application entry point.

    Returns:
        Exit code (0 = success, non-zero = error)
    """
    # Configure dependency injection
    container = configure_container()

    # Create Qt application
    app = create_app(container)

    # ========================================================================
    # PRESENTATION: Qt Translation Adapter (Singleton - requires QApplication)
    # ========================================================================

    # Register QtTranslationAdapter after QApplication is created
    # This adapter bridges ITranslationService to Qt UI with RTL/LTR support
    # Wrap domain ITranslationService with application-layer service (DTO-based)
    domain_translation_service = container.resolve(ITranslationService)
    translation_app_service = TranslationApplicationService(domain_translation_service)
    qt_translation_adapter = QtTranslationAdapter(
        translation_service=translation_app_service,
        app=app,
    )
    container.register_instance(QtTranslationAdapter, qt_translation_adapter)

    # Create welcome view
    welcome_vm = container.resolve(WelcomeViewModel)
    welcome_view = WelcomeView(parent=None, viewmodel=welcome_vm)
    welcome_view.show()

    # Start event loop
    exit_code = app.exec()

    # Cleanup
    container.clear()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

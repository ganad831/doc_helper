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
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from doc_helper.application.commands.create_project_command import (
    CreateProjectCommand,
)
from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.commands.update_field_command import UpdateFieldCommand
from doc_helper.application.document.document_generation_service import (
    DocumentGenerationService,
)
from doc_helper.application.queries.get_project_query import GetProjectQuery
from doc_helper.application.queries.get_project_query import GetRecentProjectsQuery
from doc_helper.application.services.control_service import ControlService
from doc_helper.application.services.field_service import FieldService
from doc_helper.application.services.formula_service import FormulaService
from doc_helper.application.services.override_service import OverrideService
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.domain.override.repositories import IOverrideRepository
from doc_helper.infrastructure.persistence.fake_override_repository import (
    FakeOverrideRepository,
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


def configure_container() -> Container:
    """Configure the dependency injection container.

    This is the single composition root for the entire application.

    Returns:
        Configured container with all services registered
    """
    container = Container()

    # ========================================================================
    # INFRASTRUCTURE: Persistence (Singleton)
    # ========================================================================

    # Schema repository - reads from config.db (v1: hardcoded path)
    schema_db_path = Path("app_types/soil_investigation/config.db")
    container.register_singleton(
        ISchemaRepository,
        lambda: SqliteSchemaRepository(db_path=schema_db_path),
    )

    # Project repository - scoped per project session
    # Note: In v1, we use a placeholder path. This will be updated when
    # opening a specific project via container.begin_scope()
    container.register_scoped(
        IProjectRepository,
        lambda: SqliteProjectRepository(db_path="current_project.db"),
    )

    # Override repository - fake in-memory implementation (v1 temporary)
    # Note: Will be replaced with SqliteOverrideRepository when override UI is fully implemented
    container.register_singleton(
        IOverrideRepository,
        lambda: FakeOverrideRepository(),
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

    # WelcomeViewModel (singleton - no project context)
    container.register_singleton(
        WelcomeViewModel,
        lambda: WelcomeViewModel(
            get_recent_query=container.resolve(GetRecentProjectsQuery),
            create_project_command=container.resolve(CreateProjectCommand),
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
    qt_translation_adapter = QtTranslationAdapter(
        translation_service=container.resolve(ITranslationService),
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

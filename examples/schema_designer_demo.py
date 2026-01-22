"""Demonstration of Schema Designer UI (Phase 2, Step 1: READ-ONLY).

This script demonstrates how to launch the Schema Designer view
to explore schema definitions.

Usage:
    python -m examples.schema_designer_demo

Requirements:
    - Phase 1 must be complete (schema repository implementation exists)
    - config.db must exist with meta-schema entities
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
    SqliteSchemaRepository,
)
from doc_helper.infrastructure.persistence.sqlite.connection import DatabaseConnection
from doc_helper.infrastructure.i18n.json_translation_service import (
    JsonTranslationService,
)
from doc_helper.domain.common.i18n import Language
from doc_helper.presentation.viewmodels.schema_designer_viewmodel import (
    SchemaDesignerViewModel,
)
from doc_helper.presentation.views.schema_designer_view import SchemaDesignerView


def main():
    """Launch Schema Designer demo."""
    # Create Qt application
    app = QApplication(sys.argv)

    # Path to config database (adjust as needed)
    # Assuming config.db is in app_types/schema_designer/config.db
    config_db_path = (
        Path(__file__).parent.parent / "app_types" / "schema_designer" / "config.db"
    )

    if not config_db_path.exists():
        print(f"ERROR: config.db not found at {config_db_path}")
        print("Please ensure Phase 1 is complete and meta-schema exists.")
        sys.exit(1)

    # Create database connection
    db_connection = DatabaseConnection(str(config_db_path))

    # Create schema repository
    schema_repository = SqliteSchemaRepository(db_connection)

    # Create translation service
    translations_path = Path(__file__).parent.parent / "translations"
    translation_service = JsonTranslationService(
        translations_directory=str(translations_path),
        default_language=Language.ENGLISH,
    )

    # Create ViewModel
    viewmodel = SchemaDesignerViewModel(
        schema_repository=schema_repository,
        translation_service=translation_service,
    )

    # Create View
    view = SchemaDesignerView(viewmodel=viewmodel)

    # Show the view
    view.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

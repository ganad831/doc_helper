"""Soil Investigation AppType implementation.

This is the first AppType extracted from v1. It provides:
- Schema repository pointing to config.db
- Template configuration
- AppType metadata

Dependency Rules (ADR-V2-003):
- MAY import from domain/, application/, app_types/contracts/
- MUST NOT import from platform/
- MUST NOT import from other app_types/{other}/
"""

from pathlib import Path
from typing import TYPE_CHECKING

from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata
from doc_helper.app_types.contracts.i_app_type import IAppType
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.infrastructure.persistence.sqlite_schema_repository import (
    SqliteSchemaRepository,
)

if TYPE_CHECKING:
    from doc_helper.app_types.contracts.i_platform_services import IPlatformServices
    from doc_helper.domain.document.transformer_registry import TransformerRegistry


# Default app_type_id for v1 compatibility and auto-migration
DEFAULT_APP_TYPE_ID = "soil_investigation"


class SoilInvestigationAppType(IAppType):
    """Soil Investigation Report AppType.

    This AppType generates professional soil investigation reports.
    It is the first AppType extracted from v1 and serves as the
    reference implementation for future AppTypes.

    Features:
    - SQLite schema database (config.db)
    - Word and Excel template support
    - PDF export capability
    - All 15+ built-in transformers

    Usage:
        app_type = SoilInvestigationAppType()
        app_type.initialize(platform_services)

        schema_repo = app_type.get_schema_repository()
        entities = schema_repo.get_all_entities()
    """

    def __init__(self) -> None:
        """Initialize AppType."""
        self._platform_services: "IPlatformServices | None" = None
        self._package_dir = Path(__file__).parent

    @property
    def app_type_id(self) -> str:
        """Get unique AppType identifier.

        Returns:
            "soil_investigation"
        """
        return DEFAULT_APP_TYPE_ID

    @property
    def metadata(self) -> AppTypeMetadata:
        """Get AppType display metadata.

        Returns:
            AppTypeMetadata with name, version, description
        """
        return AppTypeMetadata(
            app_type_id=self.app_type_id,
            name="Soil Investigation Report",
            version="1.0.0",
            description="Generate professional soil investigation reports",
            icon_path=None,  # v1: no custom icon
        )

    def get_schema_repository(self) -> ISchemaRepository:
        """Get schema repository for this AppType.

        Returns:
            SqliteSchemaRepository pointing to config.db

        Note:
            In v1, config.db may not exist (tests use mocks).
            The repository handles missing file gracefully.
        """
        config_db_path = self._package_dir / "config.db"
        return SqliteSchemaRepository(db_path=config_db_path)

    def register_transformers(self, registry: "TransformerRegistry") -> None:
        """Register custom transformers for this AppType.

        Args:
            registry: TransformerRegistry to register transformers with

        Note:
            v1 uses only built-in transformers. Custom transformers
            would be added here for domain-specific formatting.
        """
        # v1: No custom transformers - all are built-in
        # Future: Could register Arabic geological terms, etc.
        pass

    def initialize(self, platform_services: "IPlatformServices") -> None:
        """Initialize AppType with platform services.

        Args:
            platform_services: Platform services (translation, transformers, etc.)

        Note:
            Called by Platform after discovery and before use.
        """
        self._platform_services = platform_services

    def get_template_directory(self) -> Path:
        """Get path to templates directory.

        Returns:
            Path to templates/ within this AppType package
        """
        return self._package_dir / "templates"

    def get_default_template(self) -> str | None:
        """Get default template filename.

        Returns:
            Default template filename or None
        """
        # v1: No default template specified
        # Templates are selected manually before generation
        return None


# Export for convenient import
__all__ = ["SoilInvestigationAppType", "DEFAULT_APP_TYPE_ID"]

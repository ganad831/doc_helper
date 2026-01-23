"""Schema Designer AppType implementation.

This is a TOOL AppType for designing and editing schema definitions.
It does NOT produce documents - it's a utility for schema management.

Dependency Rules (ADR-V2-003):
- MAY import from domain/, application/, app_types/contracts/
- MUST NOT import from platform/
- MUST NOT import from other app_types/{other}/
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from doc_helper.app_types.contracts.app_type_metadata import AppTypeKind, AppTypeMetadata
from doc_helper.app_types.contracts.i_app_type import IAppType
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.infrastructure.persistence.sqlite_schema_repository import (
    SqliteSchemaRepository,
)

if TYPE_CHECKING:
    from doc_helper.app_types.contracts.i_platform_services import IPlatformServices
    from doc_helper.domain.document.transformer_registry import TransformerRegistry


# Default app_type_id
SCHEMA_DESIGNER_APP_TYPE_ID = "schema_designer"


class SchemaDesignerAppType(IAppType):
    """Schema Designer TOOL AppType.

    This AppType provides a utility for designing and editing schema
    definitions. It does NOT produce documents - users use it to
    manage entity and field definitions for other AppTypes.

    Features:
    - View all entities and fields in a schema
    - Create new entities and fields
    - Edit entity and field properties
    - Export/import schema definitions

    Usage:
        app_type = SchemaDesignerAppType()
        app_type.initialize(platform_services)

        # For TOOL AppTypes, get the view
        view = app_type.create_view(parent_widget)
    """

    def __init__(self) -> None:
        """Initialize AppType."""
        self._platform_services: "IPlatformServices | None" = None
        self._package_dir = Path(__file__).parent
        self._schema_repository: Optional[ISchemaRepository] = None

    @property
    def app_type_id(self) -> str:
        """Get unique AppType identifier.

        Returns:
            "schema_designer"
        """
        return SCHEMA_DESIGNER_APP_TYPE_ID

    @property
    def metadata(self) -> AppTypeMetadata:
        """Get AppType display metadata.

        Returns:
            AppTypeMetadata with kind=TOOL
        """
        return AppTypeMetadata(
            app_type_id=self.app_type_id,
            name="Schema Designer",
            version="1.0.0",
            kind=AppTypeKind.TOOL,
            description="Design and edit schema definitions for document types",
            icon_path=None,
        )

    def get_schema_repository(self) -> ISchemaRepository:
        """Get schema repository for this AppType.

        For Schema Designer, this returns a repository pointing to
        the default schema database. In production, this would be
        configurable to point to any AppType's schema.

        Returns:
            SqliteSchemaRepository pointing to config.db
        """
        if self._schema_repository is None:
            # Default to soil_investigation schema for now
            # TODO: Make configurable to edit any AppType's schema
            from doc_helper.app_types.soil_investigation import SoilInvestigationAppType
            soil_app = SoilInvestigationAppType()
            self._schema_repository = soil_app.get_schema_repository()
        return self._schema_repository

    def set_schema_repository(self, repository: ISchemaRepository) -> None:
        """Set the schema repository to edit.

        Allows Schema Designer to edit different AppType schemas.

        Args:
            repository: Schema repository to edit
        """
        self._schema_repository = repository

    def register_transformers(self, registry: "TransformerRegistry") -> None:
        """Register custom transformers for this AppType.

        Args:
            registry: TransformerRegistry to register transformers with

        Note:
            Schema Designer doesn't produce documents, so no transformers.
        """
        # TOOL AppType: No document output, no transformers needed
        pass

    def initialize(self, platform_services: "IPlatformServices") -> None:
        """Initialize AppType with platform services.

        Args:
            platform_services: Platform services (translation, transformers, etc.)
        """
        self._platform_services = platform_services

    def get_template_directory(self) -> Path:
        """Get path to templates directory.

        Returns:
            Path to templates/ (empty for TOOL AppTypes)
        """
        return self._package_dir / "templates"

    def get_default_template(self) -> str | None:
        """Get default template filename.

        Returns:
            None (TOOL AppTypes don't have templates)
        """
        return None


# Export for convenient import
__all__ = ["SchemaDesignerAppType", "SCHEMA_DESIGNER_APP_TYPE_ID"]

"""Test Report AppType implementation.

This is a minimal AppType used for platform validation and testing.
It provides a simple schema with 3 fields to prove AppType isolation.

Purpose:
- Validate multi-AppType platform architecture
- Test AppType discovery and registration
- Prove AppTypes don't interfere with each other

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
from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
    SqliteSchemaRepository,
)

if TYPE_CHECKING:
    from doc_helper.app_types.contracts.i_platform_services import IPlatformServices
    from doc_helper.domain.document.transformer_registry import TransformerRegistry


class TestReportAppType(IAppType):
    """Minimal Test Report AppType.

    This AppType is intentionally minimal to serve as a validation
    tool for the multi-AppType platform architecture.

    Schema:
    - 1 entity: report_info (singleton)
    - 3 fields: title (TEXT), date (DATE), summary (TEXTAREA)
    - No formulas, no controls, no overrides

    Usage:
        app_type = TestReportAppType()
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
            "test_report"
        """
        return "test_report"

    @property
    def metadata(self) -> AppTypeMetadata:
        """Get AppType display metadata.

        Returns:
            AppTypeMetadata with name, version, description
        """
        return AppTypeMetadata(
            app_type_id=self.app_type_id,
            name="Test Report",
            version="1.0.0",
            description="Minimal test report for platform validation",
            icon_path=None,
        )

    def get_schema_repository(self) -> ISchemaRepository:
        """Get schema repository for this AppType.

        Returns:
            SqliteSchemaRepository pointing to config.db

        Note:
            The config.db contains minimal schema for testing.
        """
        config_db_path = self._package_dir / "config.db"
        return SqliteSchemaRepository(db_path=config_db_path)

    def register_transformers(self, registry: "TransformerRegistry") -> None:
        """Register custom transformers for this AppType.

        Args:
            registry: TransformerRegistry to register transformers with

        Note:
            This minimal AppType uses only built-in transformers.
        """
        # No custom transformers for minimal test AppType
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
            Default template filename
        """
        return "test_report.docx"


# Export for convenient import
__all__ = ["TestReportAppType"]

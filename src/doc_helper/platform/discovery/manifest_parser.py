"""Manifest parser for AppType manifest.json files.

Parses and validates AppType manifests against the defined schema.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from doc_helper.app_types.contracts.app_type_metadata import AppTypeKind, AppTypeMetadata
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.common.value_object import ValueObject


class ManifestParseError(Exception):
    """Exception raised when manifest parsing fails."""

    def __init__(self, message: str, manifest_path: Optional[Path] = None):
        self.message = message
        self.manifest_path = manifest_path
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.manifest_path:
            return f"Error parsing {self.manifest_path}: {self.message}"
        return f"Manifest parse error: {self.message}"


@dataclass(frozen=True)
class ManifestSchema(ValueObject):
    """Validated manifest schema configuration.

    Represents the 'schema' section of an AppType manifest.
    """

    source: str
    schema_type: str

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("schema.source cannot be empty")
        if not self.schema_type:
            raise ValueError("schema.type cannot be empty")
        if self.schema_type not in ("sqlite",):
            raise ValueError(f"Unsupported schema type: {self.schema_type}")


@dataclass(frozen=True)
class ManifestTemplates(ValueObject):
    """Validated manifest templates configuration.

    Represents the 'templates' section of an AppType manifest.
    """

    word: tuple[str, ...] = ()
    excel: tuple[str, ...] = ()
    default: Optional[str] = None

    def __post_init__(self) -> None:
        # Validate that default template is in one of the template lists
        if self.default:
            all_templates = self.word + self.excel
            if self.default not in all_templates:
                raise ValueError(
                    f"Default template '{self.default}' not found in template lists"
                )


@dataclass(frozen=True)
class ManifestCapabilities(ValueObject):
    """Validated manifest capabilities configuration.

    Represents the 'capabilities' section of an AppType manifest.
    """

    supports_pdf_export: bool = True
    supports_excel_export: bool = True
    supports_word_export: bool = True


@dataclass(frozen=True)
class ParsedManifest(ValueObject):
    """Complete parsed and validated AppType manifest.

    This is the output of ManifestParser.parse() - a fully validated
    manifest ready for use by the Platform.

    Attributes:
        metadata: AppType display metadata (id, name, version, description, icon)
        schema: Schema configuration (source path, type)
        templates: Template configuration (word, excel, default)
        capabilities: Capability flags
        manifest_path: Path to the manifest.json file
    """

    metadata: AppTypeMetadata
    schema: ManifestSchema
    templates: ManifestTemplates
    capabilities: ManifestCapabilities
    manifest_path: Path


class ManifestParser:
    """Parser for AppType manifest.json files.

    Parses manifest files and validates them against the expected schema.
    Returns Result[ParsedManifest, ManifestParseError] to allow graceful
    error handling during discovery.

    Manifest Format (ADR-V2-002):
        {
            "id": "soil_investigation",
            "name": "Soil Investigation Report",
            "version": "1.0.0",
            "kind": "document",
            "description": "Generate professional soil investigation reports",
            "icon": "resources/icon.png",
            "schema": {
                "source": "config.db",
                "type": "sqlite"
            },
            "templates": {
                "word": ["templates/report.docx"],
                "excel": ["templates/data.xlsx"],
                "default": "templates/report.docx"
            },
            "capabilities": {
                "supports_pdf_export": true,
                "supports_excel_export": true,
                "supports_word_export": true
            }
        }

    Required Fields:
        - id: Unique identifier (lowercase, alphanumeric, underscores)
        - name: Human-readable display name
        - version: Semantic version (X.Y.Z)
        - schema.source: Relative path to schema database
        - schema.type: Schema format (currently only "sqlite")

    Optional Fields:
        - kind: AppType classification ("document" or "tool", defaults to "document")
        - description: Short description for UI display
        - icon: Relative path to icon file
        - templates.*: Template paths
        - capabilities.*: Feature flags

    Usage:
        parser = ManifestParser()
        result = parser.parse(Path("app_types/soil_investigation/manifest.json"))
        if isinstance(result, Success):
            manifest = result.value
            print(f"Loaded: {manifest.metadata.name}")
        else:
            print(f"Error: {result.error.message}")
    """

    # JSON Schema for manifest validation (simplified inline schema)
    REQUIRED_FIELDS = ("id", "name", "version", "schema")
    REQUIRED_SCHEMA_FIELDS = ("source", "type")

    def parse(self, manifest_path: Path) -> Result[ParsedManifest, ManifestParseError]:
        """Parse and validate a manifest.json file.

        Args:
            manifest_path: Path to manifest.json file

        Returns:
            Result containing ParsedManifest or ManifestParseError
        """
        # Check file exists
        if not manifest_path.exists():
            return Failure(
                ManifestParseError("File not found", manifest_path)
            )

        if not manifest_path.is_file():
            return Failure(
                ManifestParseError("Path is not a file", manifest_path)
            )

        # Parse JSON
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return Failure(
                ManifestParseError(f"Invalid JSON: {e}", manifest_path)
            )
        except IOError as e:
            return Failure(
                ManifestParseError(f"Could not read file: {e}", manifest_path)
            )

        # Validate structure
        return self._validate_and_build(data, manifest_path)

    def parse_string(
        self, json_string: str, source_path: Optional[Path] = None
    ) -> Result[ParsedManifest, ManifestParseError]:
        """Parse manifest from a JSON string.

        Useful for testing and when manifest is loaded from other sources.

        Args:
            json_string: JSON string containing manifest
            source_path: Optional path for error messages

        Returns:
            Result containing ParsedManifest or ManifestParseError
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            return Failure(
                ManifestParseError(f"Invalid JSON: {e}", source_path)
            )

        return self._validate_and_build(data, source_path or Path("(string)"))

    def _validate_and_build(
        self, data: dict[str, Any], manifest_path: Path
    ) -> Result[ParsedManifest, ManifestParseError]:
        """Validate manifest data and build ParsedManifest.

        Args:
            data: Parsed JSON data
            manifest_path: Path for error messages

        Returns:
            Result containing ParsedManifest or ManifestParseError
        """
        # Check it's a dict
        if not isinstance(data, dict):
            return Failure(
                ManifestParseError("Manifest must be a JSON object", manifest_path)
            )

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                return Failure(
                    ManifestParseError(f"Missing required field: '{field}'", manifest_path)
                )

        # Validate and extract schema
        schema_data = data.get("schema", {})
        if not isinstance(schema_data, dict):
            return Failure(
                ManifestParseError("'schema' must be an object", manifest_path)
            )

        for field in self.REQUIRED_SCHEMA_FIELDS:
            if field not in schema_data:
                return Failure(
                    ManifestParseError(
                        f"Missing required field: 'schema.{field}'", manifest_path
                    )
                )

        # Build components
        try:
            metadata = self._build_metadata(data, manifest_path)
        except ValueError as e:
            return Failure(ManifestParseError(str(e), manifest_path))

        try:
            schema = self._build_schema(schema_data, manifest_path)
        except ValueError as e:
            return Failure(ManifestParseError(str(e), manifest_path))

        try:
            templates = self._build_templates(data.get("templates", {}), manifest_path)
        except ValueError as e:
            return Failure(ManifestParseError(str(e), manifest_path))

        try:
            capabilities = self._build_capabilities(
                data.get("capabilities", {}), manifest_path
            )
        except ValueError as e:
            return Failure(ManifestParseError(str(e), manifest_path))

        # Build final manifest
        return Success(
            ParsedManifest(
                metadata=metadata,
                schema=schema,
                templates=templates,
                capabilities=capabilities,
                manifest_path=manifest_path,
            )
        )

    def _build_metadata(
        self, data: dict[str, Any], manifest_path: Path
    ) -> AppTypeMetadata:
        """Build AppTypeMetadata from manifest data."""
        # Parse kind field (defaults to DOCUMENT if not specified)
        kind_str = data.get("kind", "document")
        try:
            kind = AppTypeKind.from_string(kind_str)
        except ValueError:
            # Default to DOCUMENT for backwards compatibility
            kind = AppTypeKind.DOCUMENT

        return AppTypeMetadata(
            app_type_id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            version=str(data.get("version", "")),
            kind=kind,
            description=data.get("description"),
            icon_path=data.get("icon"),
        )

    def _build_schema(
        self, schema_data: dict[str, Any], manifest_path: Path
    ) -> ManifestSchema:
        """Build ManifestSchema from manifest data."""
        return ManifestSchema(
            source=str(schema_data.get("source", "")),
            schema_type=str(schema_data.get("type", "")),
        )

    def _build_templates(
        self, templates_data: dict[str, Any], manifest_path: Path
    ) -> ManifestTemplates:
        """Build ManifestTemplates from manifest data."""
        if not templates_data:
            return ManifestTemplates()

        word_templates = templates_data.get("word", [])
        excel_templates = templates_data.get("excel", [])
        default_template = templates_data.get("default")

        # Ensure lists
        if not isinstance(word_templates, list):
            word_templates = []
        if not isinstance(excel_templates, list):
            excel_templates = []

        return ManifestTemplates(
            word=tuple(str(t) for t in word_templates),
            excel=tuple(str(t) for t in excel_templates),
            default=str(default_template) if default_template else None,
        )

    def _build_capabilities(
        self, capabilities_data: dict[str, Any], manifest_path: Path
    ) -> ManifestCapabilities:
        """Build ManifestCapabilities from manifest data."""
        if not capabilities_data:
            return ManifestCapabilities()

        return ManifestCapabilities(
            supports_pdf_export=bool(
                capabilities_data.get("supports_pdf_export", True)
            ),
            supports_excel_export=bool(
                capabilities_data.get("supports_excel_export", True)
            ),
            supports_word_export=bool(
                capabilities_data.get("supports_word_export", True)
            ),
        )

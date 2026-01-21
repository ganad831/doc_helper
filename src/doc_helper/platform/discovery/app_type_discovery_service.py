"""AppType discovery service.

Scans app_types/ directory for valid AppType packages.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.common.value_object import ValueObject
from doc_helper.platform.discovery.manifest_parser import (
    ManifestParseError,
    ManifestParser,
    ParsedManifest,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DiscoveryResult(ValueObject):
    """Result of AppType discovery.

    Contains successfully discovered AppTypes and any errors encountered.
    This allows the Platform to continue with valid AppTypes even if
    some AppType packages are invalid.

    Attributes:
        manifests: Tuple of successfully parsed manifests
        errors: Tuple of errors encountered during discovery
    """

    manifests: tuple[ParsedManifest, ...]
    errors: tuple[ManifestParseError, ...]

    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred during discovery."""
        return len(self.errors) > 0

    @property
    def manifest_count(self) -> int:
        """Number of successfully discovered manifests."""
        return len(self.manifests)


class AppTypeDiscoveryService:
    """Service for discovering AppType packages.

    Scans a directory for AppType packages (subdirectories containing
    manifest.json files) and validates their manifests.

    Discovery Process (ADR-V2-002):
    1. Scan app_types/ directory for subdirectories
    2. For each subdirectory, look for manifest.json
    3. Parse and validate manifest against schema
    4. Return successfully parsed manifests (errors logged)

    Graceful Error Handling:
    - Invalid manifests are logged but don't stop discovery
    - Missing manifest.json files are logged but don't stop discovery
    - Directories without manifest.json are silently skipped
    - Empty app_types/ directory returns empty result (no crash)

    Usage:
        discovery = AppTypeDiscoveryService()
        result = discovery.discover(Path("src/doc_helper/app_types"))

        for manifest in result.manifests:
            print(f"Found: {manifest.metadata.name}")

        if result.has_errors:
            for error in result.errors:
                print(f"Error: {error.message}")

    Phase 1 Behavior:
        In Phase 1, app_types/ is empty (no AppTypes migrated yet).
        The discovery service handles this gracefully, returning an
        empty DiscoveryResult with no errors.
    """

    MANIFEST_FILENAME = "manifest.json"

    def __init__(self, parser: Optional[ManifestParser] = None) -> None:
        """Initialize discovery service.

        Args:
            parser: ManifestParser instance (default: create new)
        """
        self._parser = parser or ManifestParser()

    def discover(self, app_types_path: Path) -> DiscoveryResult:
        """Discover all AppTypes in the given directory.

        Args:
            app_types_path: Path to app_types/ directory

        Returns:
            DiscoveryResult containing discovered manifests and errors

        Note:
            - Non-existent directory returns empty result
            - Empty directory returns empty result
            - Invalid manifests are collected as errors
        """
        manifests: list[ParsedManifest] = []
        errors: list[ManifestParseError] = []

        # Handle non-existent directory gracefully
        if not app_types_path.exists():
            logger.info(f"AppTypes directory does not exist: {app_types_path}")
            return DiscoveryResult(manifests=(), errors=())

        if not app_types_path.is_dir():
            logger.warning(f"AppTypes path is not a directory: {app_types_path}")
            return DiscoveryResult(manifests=(), errors=())

        # Scan subdirectories
        for item in sorted(app_types_path.iterdir()):
            # Skip non-directories and special directories
            if not item.is_dir():
                continue
            if item.name.startswith("_") or item.name.startswith("."):
                continue
            if item.name == "contracts":
                # Skip the contracts directory (shared interfaces)
                continue

            # Look for manifest.json
            manifest_path = item / self.MANIFEST_FILENAME
            if not manifest_path.exists():
                logger.debug(f"No manifest.json in {item.name}, skipping")
                continue

            # Parse manifest
            logger.info(f"Discovering AppType: {item.name}")
            result = self._parser.parse(manifest_path)

            if isinstance(result, Success):
                manifest = result.value
                logger.info(
                    f"Discovered: {manifest.metadata.name} "
                    f"(v{manifest.metadata.version})"
                )
                manifests.append(manifest)
            else:
                error = result.error
                logger.warning(f"Failed to parse manifest in {item.name}: {error.message}")
                errors.append(error)

        logger.info(
            f"Discovery complete: {len(manifests)} AppTypes found, "
            f"{len(errors)} errors"
        )

        return DiscoveryResult(
            manifests=tuple(manifests),
            errors=tuple(errors),
        )

    def discover_single(
        self, app_type_path: Path
    ) -> Result[ParsedManifest, ManifestParseError]:
        """Discover a single AppType by path.

        Args:
            app_type_path: Path to AppType directory (not manifest.json)

        Returns:
            Result containing ParsedManifest or ManifestParseError
        """
        if not app_type_path.exists():
            return Failure(
                ManifestParseError(
                    "AppType directory not found", app_type_path
                )
            )

        if not app_type_path.is_dir():
            return Failure(
                ManifestParseError(
                    "Path is not a directory", app_type_path
                )
            )

        manifest_path = app_type_path / self.MANIFEST_FILENAME
        return self._parser.parse(manifest_path)

"""Platform discovery package.

This package handles discovering and parsing AppType modules:
- ManifestParser: Parse and validate manifest.json files
- AppTypeDiscoveryService: Scan app_types/ for valid AppType packages

Discovery Process (ADR-V2-002):
1. Scan app_types/ directory for subdirectories
2. For each subdirectory, look for manifest.json
3. Parse and validate manifest against schema
4. Return list of discovered AppType manifests
"""

from doc_helper.platform.discovery.app_type_discovery_service import (
    AppTypeDiscoveryService,
)
from doc_helper.platform.discovery.manifest_parser import (
    ManifestParseError,
    ManifestParser,
)

__all__ = [
    "ManifestParser",
    "ManifestParseError",
    "AppTypeDiscoveryService",
]

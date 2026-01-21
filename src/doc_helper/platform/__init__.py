"""Platform package.

This package contains the Platform Host infrastructure for managing AppTypes:
- discovery/: AppType discovery and manifest parsing
- registry/: AppType registration and lookup
- routing/: Request routing to appropriate AppType
- composition/: Platform-level DI container (future)

Platform Responsibilities (ADR-V2-001):
- AppType Discovery: Scanning app_types/ directory for valid AppType packages
- AppType Lifecycle: Loading, initializing, and unloading AppType modules
- AppType Registry: Maintaining a registry of available AppTypes
- Routing: Directing requests to the appropriate AppType based on project identity
- Shared Infrastructure: Providing cross-cutting services (persistence, events, i18n)

Dependency Rules (ADR-V2-003):
- platform/ MAY import from: domain/, application/, app_types/contracts/
- platform/ MUST NOT import from: infrastructure/, presentation/
- platform/ MUST NOT import from: any specific app_types/{apptype}/
"""

from doc_helper.platform.discovery.app_type_discovery_service import (
    AppTypeDiscoveryService,
)
from doc_helper.platform.discovery.manifest_parser import (
    ManifestParseError,
    ManifestParser,
)
from doc_helper.platform.registry.app_type_registry import AppTypeRegistry
from doc_helper.platform.registry.interfaces import IAppTypeRegistry
from doc_helper.platform.routing.app_type_router import (
    AppTypeRouter,
    IAppTypeRouter,
)

__all__ = [
    # Discovery
    "ManifestParser",
    "ManifestParseError",
    "AppTypeDiscoveryService",
    # Registry
    "IAppTypeRegistry",
    "AppTypeRegistry",
    # Routing
    "IAppTypeRouter",
    "AppTypeRouter",
]

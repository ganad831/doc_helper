"""AppType Contracts package.

This package defines the contract interfaces between Platform Host and AppType modules.

Contracts:
- IAppType: Interface that all AppType modules must implement
- IPlatformServices: Interface for services Platform provides to AppTypes
- AppTypeMetadata: Immutable value object for AppType display information

Dependency Rules (ADR-V2-003):
- app_types/contracts/ MAY import from domain/common/ only
- app_types/contracts/ MUST NOT import from any other package
- These contracts define the Platform-AppType boundary (ADR-V2-001)
"""

from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata
from doc_helper.app_types.contracts.i_app_type import IAppType
from doc_helper.app_types.contracts.i_platform_services import IPlatformServices

__all__ = [
    "IAppType",
    "IPlatformServices",
    "AppTypeMetadata",
]

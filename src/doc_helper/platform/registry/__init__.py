"""Platform registry package.

This package handles AppType registration and lookup:
- IAppTypeRegistry: Interface for AppType registry
- AppTypeRegistry: Implementation of registry

Registry Responsibilities (ADR-V2-001):
- Maintain a registry of available AppTypes
- Provide lookup by app_type_id
- List all registered AppTypes
"""

from doc_helper.platform.registry.app_type_registry import AppTypeRegistry
from doc_helper.platform.registry.interfaces import IAppTypeRegistry

__all__ = [
    "IAppTypeRegistry",
    "AppTypeRegistry",
]

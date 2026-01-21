"""Platform routing package.

This package handles routing operations to the appropriate AppType:
- IAppTypeRouter: Interface for routing operations
- AppTypeRouter: Implementation of router

Routing Responsibilities (ADR-V2-001):
- Direct requests to appropriate AppType based on project identity
- Validate AppType availability before routing
- Provide current context information

Phase 1 Status:
    In Phase 1, routing is not fully implemented as there is only
    one AppType. The interface is defined for Phase 2+ when multiple
    AppTypes exist and routing becomes necessary.
"""

from doc_helper.platform.routing.app_type_router import (
    AppTypeRouter,
    IAppTypeRouter,
)

__all__ = [
    "IAppTypeRouter",
    "AppTypeRouter",
]

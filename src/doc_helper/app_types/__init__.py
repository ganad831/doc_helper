"""App Types package.

This package contains:
- contracts/: Interface contracts that all AppTypes must implement (IAppType, IPlatformServices)
- {app_type_name}/: Individual AppType implementations (e.g., soil_investigation in Phase 2)

Dependency Rules (ADR-V2-003):
- AppType modules MAY import from domain/, application/, app_types/contracts/
- AppType modules MUST NOT import from other app_types/{other_apptype}/
- AppType modules MUST NOT import from platform/
"""

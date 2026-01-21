"""AppType Data Transfer Object.

v2 PHASE 4: DTO for exposing AppType metadata to presentation layer.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppTypeDTO:
    """DTO for AppType metadata.

    Used by presentation layer to display available AppTypes
    and current project's AppType.

    Attributes:
        app_type_id: Unique identifier for the AppType
        name: Display name
        version: Semantic version string
        description: User-facing description
    """

    app_type_id: str
    name: str
    version: str
    description: str

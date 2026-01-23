"""AppType Data Transfer Object.

v2 PHASE 4: DTO for exposing AppType metadata to presentation layer.
"""

from dataclasses import dataclass
from typing import Optional


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
        kind: Classification ("document" or "tool")
    """

    app_type_id: str
    name: str
    version: str
    description: Optional[str] = None
    kind: str = "document"

    @property
    def is_tool(self) -> bool:
        """Check if this is a TOOL AppType."""
        return self.kind == "tool"

    @property
    def is_document(self) -> bool:
        """Check if this is a DOCUMENT AppType."""
        return self.kind == "document"

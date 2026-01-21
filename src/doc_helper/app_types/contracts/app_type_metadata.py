"""AppType metadata value object.

Immutable value object containing display information for an AppType.
"""

from dataclasses import dataclass
from typing import Optional

from doc_helper.domain.common.value_object import ValueObject


@dataclass(frozen=True)
class AppTypeMetadata(ValueObject):
    """Immutable metadata for an AppType.

    Contains display information used by the Platform to show available
    AppTypes to users (Welcome screen, project creation dialogs, etc.).

    Attributes:
        app_type_id: Unique identifier (lowercase, alphanumeric, underscores)
        name: Human-readable display name
        version: Semantic version string (X.Y.Z)
        description: Short description for UI display (optional)
        icon_path: Relative path to icon file within AppType package (optional)

    Example:
        metadata = AppTypeMetadata(
            app_type_id="soil_investigation",
            name="Soil Investigation Report",
            version="1.0.0",
            description="Generate professional soil investigation reports",
            icon_path="resources/icon.png"
        )

    Rules (ADR-V2-002):
        - app_type_id must be unique across all registered AppTypes
        - app_type_id must match regex: ^[a-z][a-z0-9_]*$
        - version must follow semantic versioning
    """

    app_type_id: str
    name: str
    version: str
    description: Optional[str] = None
    icon_path: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate metadata fields."""
        if not self.app_type_id:
            raise ValueError("app_type_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.version:
            raise ValueError("version cannot be empty")

        # Validate app_type_id format
        import re

        if not re.match(r"^[a-z][a-z0-9_]*$", self.app_type_id):
            raise ValueError(
                f"app_type_id must be lowercase alphanumeric with underscores, "
                f"starting with a letter. Got: '{self.app_type_id}'"
            )

        # Validate semantic version format (basic check)
        if not re.match(r"^\d+\.\d+\.\d+", self.version):
            raise ValueError(
                f"version must follow semantic versioning (X.Y.Z). Got: '{self.version}'"
            )

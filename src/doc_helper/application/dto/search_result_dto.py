"""Data Transfer Objects for search results.

ADR-026: Search Architecture
- Read-only query operation (CQRS)
- Immutable DTOs for presentation layer
- Contains navigation hints (field path, entity ID)
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class SearchResultDTO:
    """Immutable search result for presentation layer.

    ADR-026: Search Architecture
    - Represents a single searchable field
    - Contains field metadata and current value
    - Provides navigation hints for UI

    Attributes:
        field_id: Unique identifier for the field
        field_label: Translatable display label for the field
        entity_id: Entity containing the field
        entity_name: Translatable display name for the entity
        current_value: Current field value (None if unset)
        field_path: Dot-separated path for navigation (e.g., "project.site_location")
        match_type: Type of match ("label", "value", "field_id")

    Example:
        result = SearchResultDTO(
            field_id="site_location",
            field_label="Site Location",
            entity_id="project",
            entity_name="Project Information",
            current_value="123 Main Street",
            field_path="project.site_location",
            match_type="value"
        )
    """

    field_id: str
    field_label: str
    entity_id: str
    entity_name: str
    current_value: Optional[Any]
    field_path: str
    match_type: str  # "label", "value", "field_id"

    def has_value(self) -> bool:
        """Check if field has a value.

        Returns:
            True if current_value is not None
        """
        return self.current_value is not None

    def matches_label(self) -> bool:
        """Check if match was on field label.

        Returns:
            True if match_type is "label"
        """
        return self.match_type == "label"

    def matches_value(self) -> bool:
        """Check if match was on field value.

        Returns:
            True if match_type is "value"
        """
        return self.match_type == "value"

    def matches_field_id(self) -> bool:
        """Check if match was on field identifier.

        Returns:
            True if match_type is "field_id"
        """
        return self.match_type == "field_id"

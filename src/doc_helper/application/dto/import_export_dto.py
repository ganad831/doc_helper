"""Import/Export DTOs for UI display.

ADR-039: Import/Export Data Format
RULES (AGENT_RULES.md Section 3-4):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ImportValidationErrorDTO:
    """Validation error encountered during import.

    ADR-039: Provides field-specific validation failure information
    to enable users to correct import data.

    Attributes:
        entity_id: Entity where validation failed
        record_id: Record identifier (for collections)
        field_id: Field where validation failed
        error_message: Human-readable error description
        error_type: Type of validation error (REQUIRED, TYPE_MISMATCH, CONSTRAINT, etc.)
        field_path: Dot-separated path for navigation (e.g., "borehole[BH-001].depth")
    """

    entity_id: str
    record_id: str | None
    field_id: str
    error_message: str
    error_type: str
    field_path: str

    def is_type_error(self) -> bool:
        """Check if error is a type mismatch."""
        return self.error_type == "TYPE_MISMATCH"

    def is_constraint_error(self) -> bool:
        """Check if error is a validation constraint failure."""
        return self.error_type == "CONSTRAINT"

    def is_required_error(self) -> bool:
        """Check if error is a missing required field."""
        return self.error_type == "REQUIRED"


@dataclass(frozen=True)
class ImportResultDTO:
    """Result of project import operation.

    ADR-039: Import always creates new project (never modifies existing).
    Success returns project_id of created project.
    Failure returns validation errors with field paths.

    Attributes:
        success: Whether import succeeded
        project_id: ID of created project (None if failure)
        project_name: Name of created project (None if failure)
        error_message: Overall error message (None if success)
        validation_errors: List of field-specific validation errors (empty if success)
        format_version: Interchange format version of imported data
        source_app_version: Application version that exported the data
        warnings: Non-fatal warnings (schema differences, deprecated fields, etc.)
    """

    success: bool
    project_id: str | None
    project_name: str | None
    error_message: str | None
    validation_errors: tuple[ImportValidationErrorDTO, ...]
    format_version: str
    source_app_version: str | None
    warnings: tuple[str, ...]

    @property
    def has_validation_errors(self) -> bool:
        """Check if result contains validation errors."""
        return len(self.validation_errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if result contains warnings."""
        return len(self.warnings) > 0

    @property
    def error_count(self) -> int:
        """Get count of validation errors."""
        return len(self.validation_errors)

    @property
    def warning_count(self) -> int:
        """Get count of warnings."""
        return len(self.warnings)

    def get_errors_by_entity(self, entity_id: str) -> tuple[ImportValidationErrorDTO, ...]:
        """Get validation errors for a specific entity.

        Args:
            entity_id: Entity ID to filter by

        Returns:
            Tuple of validation errors for the entity
        """
        return tuple(e for e in self.validation_errors if e.entity_id == entity_id)


@dataclass(frozen=True)
class ExportResultDTO:
    """Result of project export operation.

    ADR-039: Export serializes complete project to interchange format.
    Success returns file path where export was written.
    Failure returns error message.

    Attributes:
        success: Whether export succeeded
        file_path: Absolute path to exported file (None if failure)
        project_id: ID of exported project
        project_name: Name of exported project
        error_message: Error message (None if success)
        format_version: Interchange format version used for export
        exported_at: ISO-8601 timestamp of export
        entity_count: Number of entities exported
        record_count: Total number of records exported
        field_value_count: Total number of field values exported
    """

    success: bool
    file_path: str | None
    project_id: str
    project_name: str
    error_message: str | None
    format_version: str
    exported_at: str
    entity_count: int
    record_count: int
    field_value_count: int

    @property
    def has_error(self) -> bool:
        """Check if export failed."""
        return not self.success

    def get_file_size_kb(self) -> int | None:
        """Get exported file size in kilobytes.

        Returns:
            File size in KB, or None if export failed or file not accessible
        """
        if not self.success or not self.file_path:
            return None

        from pathlib import Path

        try:
            file_path = Path(self.file_path)
            if file_path.exists():
                return file_path.stat().st_size // 1024
        except Exception:
            pass

        return None


@dataclass(frozen=True)
class InterchangeFormatInfoDTO:
    """Information about supported interchange format.

    ADR-039: Provides format capabilities and compatibility information
    for presentation layer to display to users.

    Attributes:
        format_version: Current interchange format version
        format_name: Human-readable format name
        file_extension: File extension for exports (e.g., ".json")
        supports_import: Whether format supports import
        supports_export: Whether format supports export
        description: Format description for users
        compatibility_info: Backward compatibility information
    """

    format_version: str
    format_name: str
    file_extension: str
    supports_import: bool
    supports_export: bool
    description: str
    compatibility_info: str

    @property
    def is_bidirectional(self) -> bool:
        """Check if format supports both import and export."""
        return self.supports_import and self.supports_export

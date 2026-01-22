"""Schema Export DTOs (Phase 2 Step 4, updated Phase 3).

DTOs for schema export data structure.
These are the data structures that will be serialized to the export file.

RULES:
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- Use primitive types only (strings, bools, numbers)
- Translation keys exported as strings (not resolved)

Phase 3 Updates:
- Added optional version field to SchemaExportDTO (Decision 5)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ConstraintExportDTO:
    """Export DTO for a field constraint.

    Contains constraint type and parameters as raw values.
    No runtime semantics - just metadata.
    """

    constraint_type: str  # e.g., "RequiredConstraint", "MinLengthConstraint"
    parameters: dict  # Constraint-specific parameters


@dataclass(frozen=True)
class FieldOptionExportDTO:
    """Export DTO for a field option (DROPDOWN/RADIO).

    Contains option value and label key.
    """

    value: str  # Option value
    label_key: str  # Translation key for label (not resolved)


@dataclass(frozen=True)
class FieldExportDTO:
    """Export DTO for a field definition.

    Contains all allowed field metadata for export.
    EXCLUDES: formula, lookup_entity_id, child_entity_id, control_rules
    """

    id: str  # Field identifier
    field_type: str  # Field type (TEXT, NUMBER, etc.)
    label_key: str  # Translation key for label
    required: bool  # Whether field is required
    help_text_key: Optional[str] = None  # Translation key for help text
    default_value: Optional[str] = None  # Default value as string
    options: tuple = ()  # Tuple of FieldOptionExportDTO for choice fields
    constraints: tuple = ()  # Tuple of ConstraintExportDTO


@dataclass(frozen=True)
class EntityExportDTO:
    """Export DTO for an entity definition.

    Contains all allowed entity metadata for export.
    """

    id: str  # Entity identifier
    name_key: str  # Translation key for name
    is_root_entity: bool  # Whether this is a root entity
    description_key: Optional[str] = None  # Translation key for description
    fields: tuple = ()  # Tuple of FieldExportDTO


@dataclass(frozen=True)
class SchemaExportDTO:
    """Export DTO for the complete schema.

    Top-level export structure containing all entities and metadata.

    Phase 3: Added optional version field (Decision 5).
    """

    schema_id: str  # Schema/project identifier (Phase 2 Decision 7)
    entities: tuple  # Tuple of EntityExportDTO
    version: Optional[str] = None  # Optional semantic version (Phase 3 Decision 5)


@dataclass(frozen=True)
class ExportWarning:
    """A warning generated during export.

    Warnings do not prevent export, but are reported to the user.
    """

    category: str  # Warning category (e.g., "incomplete_entity", "excluded_data")
    message: str  # Human-readable warning message


@dataclass(frozen=True)
class ExportResult:
    """Result of schema export operation.

    Contains either success data with optional warnings,
    or failure information.
    """

    success: bool
    export_data: Optional[SchemaExportDTO] = None  # Present on success
    warnings: tuple = ()  # Tuple of ExportWarning (present on success)
    error: Optional[str] = None  # Present on failure

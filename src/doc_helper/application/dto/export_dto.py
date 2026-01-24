"""Schema Export DTOs (Phase 2 Step 4, updated Phase 3, Phase 6A, Phase F-10, Phase F-12.5).

DTOs for schema export data structure.
These are the data structures that will be serialized to the export file.

RULES:
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- Use primitive types only (strings, bools, numbers)
- Translation keys exported as strings (not resolved)

Phase 3 Updates:
- Added optional version field to SchemaExportDTO (Decision 5)

Phase 6A Updates (ADR-022):
- Added RelationshipExportDTO for relationship definitions
- Added relationships field to SchemaExportDTO

Phase F-10 Updates:
- Added ControlRuleExportDTO for control rule definitions
- Added control_rules field to FieldExportDTO
- Control rules are DESIGN-TIME metadata only (no runtime execution)

Phase F-12.5 Updates:
- Added OutputMappingExportDTO for output mapping definitions
- Added output_mappings field to FieldExportDTO
- Output mappings are DESIGN-TIME metadata only (no runtime execution)
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
    EXCLUDES: formula, lookup_entity_id, child_entity_id

    Phase F-10: Added control_rules field for design-time control rule metadata.
    Phase F-12.5: Added output_mappings field for design-time output mapping metadata.
    """

    id: str  # Field identifier
    field_type: str  # Field type (TEXT, NUMBER, etc.)
    label_key: str  # Translation key for label
    required: bool  # Whether field is required
    help_text_key: Optional[str] = None  # Translation key for help text
    default_value: Optional[str] = None  # Default value as string
    options: tuple = ()  # Tuple of FieldOptionExportDTO for choice fields
    constraints: tuple = ()  # Tuple of ConstraintExportDTO
    control_rules: tuple = ()  # Tuple of ControlRuleExportDTO (Phase F-10)
    output_mappings: tuple = ()  # Tuple of OutputMappingExportDTO (Phase F-12.5)


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
class RelationshipExportDTO:
    """Export DTO for a relationship definition (Phase 6A - ADR-022).

    Contains relationship metadata for export.
    RelationshipType is descriptive metadata only (no runtime behavior).
    """

    id: str  # Relationship identifier
    source_entity_id: str  # Source entity ID
    target_entity_id: str  # Target entity ID
    relationship_type: str  # Type (CONTAINS, REFERENCES, ASSOCIATES)
    name_key: str  # Translation key for relationship name
    description_key: Optional[str] = None  # Translation key for description
    inverse_name_key: Optional[str] = None  # Translation key for inverse name


@dataclass(frozen=True)
class ControlRuleExportDTO:
    """Export DTO for a control rule definition (Phase F-10).

    Contains control rule metadata for schema export.
    Control rules are DESIGN-TIME metadata only - NO runtime execution.

    Phase F-10 Constraints:
    - Associated with a specific field (target_field_id)
    - Rule type determines UI behavior (VISIBILITY, ENABLED, REQUIRED)
    - Formula must be a valid BOOLEAN formula
    - No runtime observers, listeners, or auto-recompute
    - Design-time schema metadata only
    """

    rule_type: str  # Control rule type (VISIBILITY, ENABLED, REQUIRED)
    target_field_id: str  # Field this rule applies to
    formula_text: str  # Boolean formula expression


@dataclass(frozen=True)
class OutputMappingExportDTO:
    """Export DTO for an output mapping definition (Phase F-12.5).

    Contains output mapping metadata for schema export.
    Output mappings are DESIGN-TIME metadata only - NO runtime execution.

    Phase F-12.5 Constraints:
    - Associated with a specific field
    - Target type determines output format (TEXT, NUMBER, BOOLEAN)
    - Formula transforms field value for document output
    - No runtime observers, listeners, or auto-recompute
    - Design-time schema metadata only
    """

    target: str  # Output target type (TEXT, NUMBER, BOOLEAN)
    formula_text: str  # Formula expression for output transformation


@dataclass(frozen=True)
class SchemaExportDTO:
    """Export DTO for the complete schema.

    Top-level export structure containing all entities and metadata.

    Phase 3: Added optional version field (Decision 5).
    Phase 6A: Added relationships field (ADR-022).
    """

    schema_id: str  # Schema/project identifier (Phase 2 Decision 7)
    entities: tuple  # Tuple of EntityExportDTO
    version: Optional[str] = None  # Optional semantic version (Phase 3 Decision 5)
    relationships: tuple = ()  # Tuple of RelationshipExportDTO (Phase 6A)


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

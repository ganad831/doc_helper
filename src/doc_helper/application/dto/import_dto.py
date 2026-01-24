"""Schema Import DTOs (Phase 4, updated Phase F-10).

DTOs for schema import operation results.

APPROVED DECISIONS:
- Decision 1: Identical schema behavior → User choice via parameter
- Decision 2: Compatible schema behavior → Replace with detailed change list
- Decision 3: Incompatible schema default → Fail by default (require force)
- Decision 4: Default enforcement policy → STRICT (block incompatible)
- Decision 5: Version field handling → Warn if version goes backward
- Decision 6: Empty entity handling → Warn but allow
- Decision 7: Unknown constraint type → Fail import (strict validation)

Phase F-10 Updates:
- Added control_rule_count to ImportResult statistics
- Added control_rule_invalid validation error category

RULES:
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- Use primitive types only (strings, bools, numbers)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from doc_helper.domain.schema.schema_compatibility import CompatibilityResult


class EnforcementPolicy(str, Enum):
    """Import enforcement policy levels.

    Controls how compatibility issues are handled during import.

    STRICT: Block import if schema is incompatible (default)
    WARN: Allow import but include warnings
    NONE: No enforcement, allow all imports
    """

    STRICT = "strict"
    WARN = "warn"
    NONE = "none"


class IdenticalSchemaAction(str, Enum):
    """Action to take when importing identical schema.

    SKIP: Don't import, return success (no-op)
    REPLACE: Import anyway, replacing existing
    """

    SKIP = "skip"
    REPLACE = "replace"


@dataclass(frozen=True)
class ImportWarning:
    """A warning generated during import.

    Warnings do not prevent import, but are reported to the user.

    Categories:
    - version_backward: Imported version is older than existing
    - empty_entity: Entity has no fields
    - compatibility: Non-breaking change detected
    - identical_schema: Schema is identical (when action=REPLACE)
    """

    category: str
    message: str


@dataclass(frozen=True)
class ImportValidationError:
    """A validation error that prevents import.

    Contains location and details of the validation failure.

    Categories:
    - json_syntax: Invalid JSON syntax
    - missing_required: Required field missing
    - invalid_type: Wrong data type
    - invalid_value: Invalid value (e.g., unknown field type)
    - unknown_constraint: Unrecognized constraint type
    - control_rule_invalid: Control rule validation failed (Phase F-10)
      - Invalid rule type
      - Invalid target field reference
      - Formula fails governance (F-6)
      - Formula is not BOOLEAN type
    """

    category: str
    message: str
    location: Optional[str] = None  # e.g., "entities[0].fields[2].field_type"


@dataclass(frozen=True)
class ImportResult:
    """Result of schema import operation.

    Contains:
    - Success/failure status
    - Imported schema metadata
    - Compatibility result (if existing schema was present)
    - Validation errors (if failed)
    - Warnings (always included)
    - Import statistics (entities, fields, relationships, control rules)

    IMPORTANT: Compatibility result is ALWAYS included when existing
    schema was present, regardless of import success/failure.

    Phase F-10: Added control_rule_count for import statistics.
    """

    success: bool
    schema_id: Optional[str] = None  # Imported schema ID
    imported_version: Optional[str] = None  # Version from import file
    existing_version: Optional[str] = None  # Version before import (if any)
    compatibility_result: Optional[CompatibilityResult] = None  # Phase 3 comparison
    validation_errors: tuple = ()  # Tuple of ImportValidationError
    warnings: tuple = ()  # Tuple of ImportWarning
    entity_count: int = 0  # Number of entities imported
    field_count: int = 0  # Total fields imported
    relationship_count: int = 0  # Number of relationships imported (Phase 6A)
    control_rule_count: int = 0  # Number of control rules imported (Phase F-10)
    was_identical: bool = False  # True if schema was identical to existing
    was_skipped: bool = False  # True if identical schema was skipped (no-op)
    error: Optional[str] = None  # General error message (if failed)

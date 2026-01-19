"""Override domain.

The Override domain manages user overrides of computed/controlled field values.

Key components:
- OverrideState: State machine states (PENDING, ACCEPTED, SYNCED)
- Override: Entity tracking override lifecycle
- Conflict detection: Identifies conflicts between formulas and controls
"""

from doc_helper.domain.override.conflict_detector import ConflictDetector, ConflictInfo
from doc_helper.domain.override.override_entity import Override
from doc_helper.domain.override.override_ids import OverrideId
from doc_helper.domain.override.override_state import OverrideState

__all__ = [
    "ConflictDetector",
    "ConflictInfo",
    "Override",
    "OverrideId",
    "OverrideState",
]

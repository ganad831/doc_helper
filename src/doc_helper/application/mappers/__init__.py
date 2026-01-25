"""Application Mappers - one-way domain-to-DTO conversion.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H3):
- Mappers are ONE-WAY: Domain → DTO only
- NO to_domain() or from_dto() methods (FORBIDDEN)
- Mappers live ONLY in application/mappers/
- Undo does NOT use reverse mapping (uses UndoState DTOs instead)
- All mappers have unit tests
"""

from doc_helper.application.mappers.project_mapper import ProjectMapper
from doc_helper.application.mappers.schema_mapper import (
    EntityDefinitionMapper,
    FieldDefinitionMapper,
)
from doc_helper.application.mappers.field_mapper import FieldValueMapper
from doc_helper.application.mappers.validation_mapper import (
    ValidationMapper,
    create_valid_validation_result,
    create_error_validation_result,
)
from doc_helper.application.mappers.override_mapper import OverrideMapper
from doc_helper.application.mappers.control_mapper import (
    ControlEffectMapper,
    EvaluationResultMapper,
)
from doc_helper.application.mappers.field_history_mapper import FieldHistoryMapper

__all__ = [
    "ProjectMapper",
    "EntityDefinitionMapper",
    "FieldDefinitionMapper",
    "FieldValueMapper",
    "ValidationMapper",
    "create_valid_validation_result",
    "create_error_validation_result",
    "OverrideMapper",
    "ControlEffectMapper",
    "EvaluationResultMapper",
    "FieldHistoryMapper",
]

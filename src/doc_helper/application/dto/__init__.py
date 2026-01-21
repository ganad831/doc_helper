"""Application DTOs - UI-facing data transfer objects.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are owned by the Application layer
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- DTOs are NOT persistence models
- Domain objects must NEVER cross the Application boundary

UI DTOs may be consumed by Presentation layer.
Undo-state DTOs (in application/undo/) are internal and FORBIDDEN in Presentation.
"""

from doc_helper.application.dto.project_dto import (
    ProjectDTO,
    ProjectSummaryDTO,
)
from doc_helper.application.dto.schema_dto import (
    EntityDefinitionDTO,
    FieldDefinitionDTO,
    FieldOptionDTO,
)
from doc_helper.application.dto.field_dto import (
    FieldValueDTO,
    FieldStateDTO,
)
from doc_helper.application.dto.validation_dto import (
    ValidationResultDTO,
    ValidationErrorDTO,
)
from doc_helper.application.dto.override_dto import (
    OverrideDTO,
    ConflictDTO,
)
from doc_helper.application.dto.document_dto import (
    DocumentFormatDTO,
    TemplateDTO,
    GenerationResultDTO,
)
from doc_helper.application.dto.control_dto import (
    ControlEffectDTO,
    EvaluationResultDTO,
)
from doc_helper.application.dto.i18n_dto import (
    LanguageDTO,
    TextDirectionDTO,
    LanguageInfoDTO,
)
from doc_helper.application.dto.field_history_dto import (
    FieldHistoryEntryDTO,
    FieldHistoryResultDTO,
)
from doc_helper.application.dto.search_result_dto import (
    SearchResultDTO,
)

__all__ = [
    # Project DTOs
    "ProjectDTO",
    "ProjectSummaryDTO",
    # Schema DTOs
    "EntityDefinitionDTO",
    "FieldDefinitionDTO",
    "FieldOptionDTO",
    # Field DTOs
    "FieldValueDTO",
    "FieldStateDTO",
    # Validation DTOs
    "ValidationResultDTO",
    "ValidationErrorDTO",
    # Override DTOs
    "OverrideDTO",
    "ConflictDTO",
    # Document DTOs
    "DocumentFormatDTO",
    "TemplateDTO",
    "GenerationResultDTO",
    # Control DTOs
    "ControlEffectDTO",
    "EvaluationResultDTO",
    # i18n DTOs
    "LanguageDTO",
    "TextDirectionDTO",
    "LanguageInfoDTO",
    # Field History DTOs
    "FieldHistoryEntryDTO",
    "FieldHistoryResultDTO",
    # Search DTOs
    "SearchResultDTO",
]

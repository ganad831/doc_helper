"""Runtime use cases package (Phase R-1, Phase R-2, Phase R-3, Phase R-4, Phase R-4.5, Phase R-5).

Contains use cases for runtime evaluation:
- Control rules (Phase R-1)
- Output mappings (Phase R-1)
- Validation constraints (Phase R-2)
- Orchestrated runtime evaluation (Phase R-3) ← AUTHORITATIVE ENTRY POINT
- Entity-level control rules aggregation (Phase R-4)
- Form runtime state adapter (Phase R-4.5)
- Entity-level output mappings aggregation (Phase R-5)

Phase R-3: Use EvaluateRuntimeRulesUseCase as the single runtime entry point.
Phase R-4: Entity-level control rule aggregation used by R-3.
Phase R-4.5: Form runtime state adapter for UI consumption.
Phase R-5: Entity-level output mappings aggregation for document generation.
"""

from doc_helper.application.usecases.runtime.build_form_runtime_state import (
    BuildFormRuntimeStateUseCase,
)
from doc_helper.application.usecases.runtime.evaluate_control_rules import (
    EvaluateControlRulesUseCase,
)
from doc_helper.application.usecases.runtime.evaluate_entity_control_rules import (
    EvaluateEntityControlRulesUseCase,
)
from doc_helper.application.usecases.runtime.evaluate_entity_output_mappings import (
    EvaluateEntityOutputMappingsUseCase,
)
from doc_helper.application.usecases.runtime.evaluate_output_mappings import (
    EvaluateOutputMappingsUseCase,
)
from doc_helper.application.usecases.runtime.evaluate_runtime_rules import (
    EvaluateRuntimeRulesUseCase,
)
from doc_helper.application.usecases.runtime.evaluate_validation_rules import (
    EvaluateValidationRulesUseCase,
)

__all__ = [
    "BuildFormRuntimeStateUseCase",  # Phase R-4.5: Form runtime state adapter
    "EvaluateControlRulesUseCase",
    "EvaluateEntityControlRulesUseCase",  # Phase R-4: Entity-level aggregation
    "EvaluateEntityOutputMappingsUseCase",  # Phase R-5: Output mappings aggregation
    "EvaluateOutputMappingsUseCase",
    "EvaluateValidationRulesUseCase",
    "EvaluateRuntimeRulesUseCase",  # Phase R-3: Authoritative entry point
]

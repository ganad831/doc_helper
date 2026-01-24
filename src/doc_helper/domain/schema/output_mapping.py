"""Output Mapping for field-level document output transformation (Phase F-12.5).

OutputMapping is a design-time value object that defines how a field's value
should be transformed for document output (Word, Excel, PDF).

PHASE F-12.5 CONSTRAINTS:
- Pure value object (NO behavior)
- NO execution logic
- NO validation logic
- NO side effects
- Design-time metadata only
"""

from dataclasses import dataclass
from typing import Optional

from doc_helper.domain.common.value_object import ValueObject


@dataclass(frozen=True)
class OutputMapping(ValueObject):
    """Output mapping definition for a field (Phase F-12.5).

    OutputMapping is an immutable value object that describes how a field's
    value should be transformed when writing to document outputs.

    RULES (Phase F-12.5):
    - OutputMapping is immutable (frozen dataclass)
    - NO execution logic (pure data)
    - NO validation logic (validation in application layer)
    - Design-time metadata only

    Example:
        # Text output with formula
        mapping = OutputMapping(
            target="TEXT",
            formula_text="{{depth_from}} - {{depth_to}}",
        )

        # Number output with calculation
        mapping = OutputMapping(
            target="NUMBER",
            formula_text="{{area}} * {{density}}",
        )

        # Boolean output with condition
        mapping = OutputMapping(
            target="BOOLEAN",
            formula_text="{{status}} == 'active'",
        )
    """

    target: str  # Output target type (TEXT, NUMBER, BOOLEAN)
    formula_text: str  # Formula expression for output transformation

    def __post_init__(self) -> None:
        """Validate output mapping structure.

        PHASE F-12.5 RULES:
        - Immutability checks only
        - NO semantic validation (application layer responsibility)
        - NO formula execution
        """
        # Validate target is a string (type check first)
        if not isinstance(self.target, str):
            raise ValueError(f"Output mapping target must be a string, got {type(self.target)}")

        # Validate target is not empty or whitespace-only
        if not self.target.strip():
            raise ValueError("Output mapping target cannot be empty")

        # Validate formula_text is a string (type check first)
        if not isinstance(self.formula_text, str):
            raise ValueError(
                f"Output mapping formula_text must be a string, got {type(self.formula_text)}"
            )

        # Validate formula_text is not empty or whitespace-only
        if not self.formula_text.strip():
            raise ValueError("Output mapping formula_text cannot be empty")

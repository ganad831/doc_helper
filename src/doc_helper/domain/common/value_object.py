"""Base value object class.

Value objects are immutable objects defined by their attributes (ADR-010).
"""

from abc import ABC
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValueObject(ABC):
    """Base class for all value objects.

    Value objects:
    - Are immutable (frozen=True)
    - Have structural equality (compared by value, not identity)
    - Have no identity
    - Are side-effect free
    - Are thread-safe

    RULES (IMPLEMENTATION_RULES.md Section 3.3):
    - All value objects MUST be frozen dataclasses
    - NO setters or mutating methods
    - Updates return new instances
    - NO mutable attributes (lists, dicts, sets)
    - Use tuples instead of lists for collections

    Example:
        @dataclass(frozen=True)
        class FieldId(ValueObject):
            value: str

            def __post_init__(self) -> None:
                if not self.value:
                    raise ValueError("FieldId cannot be empty")

    Anti-pattern (DO NOT DO):
        @dataclass
        class BadValueObject(ValueObject):  # ❌ Missing frozen=True
            value: str
            items: List[str]  # ❌ Mutable collection

        obj.value = "new"  # ❌ Would violate immutability
    """

    def __eq__(self, other: Any) -> bool:
        """Value objects are equal if all attributes are equal."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Hash based on all attributes for use in sets/dicts."""
        # Dataclass with frozen=True automatically implements __hash__
        # This is here for documentation
        return super().__hash__()

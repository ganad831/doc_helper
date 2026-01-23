"""Application-layer operation result for Presentation layer consumption.

This DTO provides a simple success/error result type that Presentation
layer can use without importing domain Result monad.

ARCHITECTURAL FIX:
- Replaces domain Result[T, E] in ViewModel public interfaces
- Keeps domain Result internal to Application layer
- Simple, behavior-free data container per DTO rules
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OperationResult:
    """Result of an operation for Presentation layer.

    This is a simple DTO that replaces domain Result monad
    at the Application-Presentation boundary.

    RULES:
    - Immutable (frozen dataclass)
    - No behavior beyond simple property access
    - Uses primitive types only
    - Presentation layer imports this, NOT domain Result
    """

    success: bool
    value: Optional[str] = None  # Success value (e.g., created entity ID)
    error: Optional[str] = None  # Error message if failed

    @staticmethod
    def ok(value: str) -> "OperationResult":
        """Create success result.

        Args:
            value: Success value (typically an ID)

        Returns:
            OperationResult with success=True
        """
        return OperationResult(success=True, value=value, error=None)

    @staticmethod
    def fail(error: str) -> "OperationResult":
        """Create failure result.

        Args:
            error: Error message

        Returns:
            OperationResult with success=False
        """
        return OperationResult(success=False, value=None, error=error)

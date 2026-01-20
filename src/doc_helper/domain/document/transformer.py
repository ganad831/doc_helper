"""Transformer interface and base implementation."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ITransformer(ABC):
    """Interface for value transformers.

    Transformers convert field values into formatted strings suitable
    for document generation.

    Each transformer has a unique name and transforms a value according
    to specific formatting rules.

    Example:
        class UppercaseTransformer(ITransformer):
            @property
            def name(self) -> str:
                return "uppercase"

            def transform(self, value: Any, **kwargs) -> str:
                if value is None:
                    return ""
                return str(value).upper()

        transformer = UppercaseTransformer()
        result = transformer.transform("hello")  # "HELLO"
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get transformer name.

        Returns:
            Unique transformer identifier
        """
        pass

    @abstractmethod
    def transform(self, value: Any, **kwargs) -> str:
        """Transform value to string.

        Args:
            value: Value to transform
            **kwargs: Additional transformer-specific options

        Returns:
            Formatted string representation
        """
        pass


class BaseTransformer(ITransformer):
    """Base transformer with common utilities.

    Provides helper methods for null handling and type conversion.
    """

    def _handle_none(self, value: Any, default: str = "") -> Optional[str]:
        """Handle None values.

        Args:
            value: Value to check
            default: Default string if value is None

        Returns:
            None if value is None, otherwise None (continue processing)
        """
        if value is None:
            return default
        return None

    def _to_str(self, value: Any) -> str:
        """Convert value to string safely.

        Args:
            value: Value to convert

        Returns:
            String representation
        """
        if value is None:
            return ""
        return str(value)

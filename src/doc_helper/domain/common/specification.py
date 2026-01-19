"""Specification pattern for composable business rules.

Encapsulates business logic that can be combined and reused.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


T = TypeVar("T")  # Type being specified


class Specification(ABC, Generic[T]):
    """Base class for specifications.

    Specifications:
    - Encapsulate a business rule
    - Can be combined with And, Or, Not
    - Return True if candidate satisfies the rule
    - Used for validation, filtering, querying

    RULES (IMPLEMENTATION_RULES.md Section 3):
    - Specifications are reusable business rules
    - Keep them focused (single responsibility)
    - Compose simple specs into complex ones
    - NO side effects in is_satisfied_by()

    Example:
        class RequiredFieldSpec(Specification[FieldValue]):
            def is_satisfied_by(self, candidate: FieldValue) -> bool:
                return candidate.value is not None and candidate.value != ""

        class MinLengthSpec(Specification[FieldValue]):
            def __init__(self, min_length: int):
                self.min_length = min_length

            def is_satisfied_by(self, candidate: FieldValue) -> bool:
                return len(str(candidate.value)) >= self.min_length

        # Composition:
        spec = RequiredFieldSpec().and_(MinLengthSpec(5))
        is_valid = spec.is_satisfied_by(field_value)
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies this specification.

        Args:
            candidate: The object to check

        Returns:
            True if candidate satisfies the specification
        """
        pass

    def and_(self, other: "Specification[T]") -> "AndSpecification[T]":
        """Combine with another specification using AND logic.

        Args:
            other: Another specification

        Returns:
            New specification that requires both conditions
        """
        return AndSpecification(self, other)

    def or_(self, other: "Specification[T]") -> "OrSpecification[T]":
        """Combine with another specification using OR logic.

        Args:
            other: Another specification

        Returns:
            New specification that requires either condition
        """
        return OrSpecification(self, other)

    def not_(self) -> "NotSpecification[T]":
        """Negate this specification.

        Returns:
            New specification that inverts this condition
        """
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    """Specification that combines two specs with AND logic."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        """Initialize AND specification.

        Args:
            left: Left specification
            right: Right specification
        """
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies both specifications.

        Args:
            candidate: The object to check

        Returns:
            True if candidate satisfies both specs
        """
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)


class OrSpecification(Specification[T]):
    """Specification that combines two specs with OR logic."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        """Initialize OR specification.

        Args:
            left: Left specification
            right: Right specification
        """
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies either specification.

        Args:
            candidate: The object to check

        Returns:
            True if candidate satisfies either spec
        """
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)


class NotSpecification(Specification[T]):
    """Specification that negates another spec."""

    def __init__(self, spec: Specification[T]):
        """Initialize NOT specification.

        Args:
            spec: Specification to negate
        """
        self.spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate does NOT satisfy the specification.

        Args:
            candidate: The object to check

        Returns:
            True if candidate does NOT satisfy the spec
        """
        return not self.spec.is_satisfied_by(candidate)

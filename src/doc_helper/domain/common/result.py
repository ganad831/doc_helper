"""Result monad for explicit error handling.

Railway-oriented programming pattern (ADR-008).
"""

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union


T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Mapped success type


@dataclass(frozen=True)
class Success(Generic[T]):
    """Represents a successful operation result."""

    value: T

    def is_success(self) -> bool:
        """Check if result is success."""
        return True

    def is_failure(self) -> bool:
        """Check if result is failure."""
        return False


@dataclass(frozen=True)
class Failure(Generic[E]):
    """Represents a failed operation result."""

    error: E

    def is_success(self) -> bool:
        """Check if result is success."""
        return False

    def is_failure(self) -> bool:
        """Check if result is failure."""
        return True


# Result type is a union of Success or Failure
Result = Union[Success[T], Failure[E]]


# Helper functions for working with Results


def map_result(result: Result[T, E], fn: Callable[[T], U]) -> Result[U, E]:
    """Map a function over the success value.

    If result is Success, applies fn to the value.
    If result is Failure, returns the failure unchanged.

    Args:
        result: The Result to map over
        fn: Function to apply to success value

    Returns:
        New Result with mapped value or original failure

    Example:
        result = Success(5)
        mapped = map_result(result, lambda x: x * 2)
        # mapped = Success(10)
    """
    if isinstance(result, Success):
        return Success(fn(result.value))
    return result


def bind_result(result: Result[T, E], fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
    """Bind (flatMap) a function that returns a Result.

    If result is Success, applies fn to the value.
    If result is Failure, returns the failure unchanged.

    Args:
        result: The Result to bind over
        fn: Function that returns a Result

    Returns:
        Result returned by fn or original failure

    Example:
        def divide(x: int) -> Result[int, str]:
            if x == 0:
                return Failure("Division by zero")
            return Success(10 // x)

        result = Success(2)
        bound = bind_result(result, divide)
        # bound = Success(5)
    """
    if isinstance(result, Success):
        return fn(result.value)
    return result


def unwrap(result: Result[T, E]) -> T:
    """Extract the success value or raise an exception.

    WARNING: Only use this when you're certain the result is a success.
    Prefer pattern matching or is_success() checks.

    Args:
        result: The Result to unwrap

    Returns:
        The success value

    Raises:
        ValueError: If result is a Failure

    Example:
        result = Success(42)
        value = unwrap(result)  # value = 42
    """
    if isinstance(result, Success):
        return result.value
    raise ValueError(f"Cannot unwrap Failure: {result.error}")


def unwrap_or(result: Result[T, E], default: T) -> T:
    """Extract the success value or return a default.

    Args:
        result: The Result to unwrap
        default: Value to return if result is Failure

    Returns:
        Success value or default

    Example:
        result = Failure("error")
        value = unwrap_or(result, 0)  # value = 0
    """
    if isinstance(result, Success):
        return result.value
    return default


def unwrap_or_else(result: Result[T, E], fn: Callable[[E], T]) -> T:
    """Extract the success value or compute from error.

    Args:
        result: The Result to unwrap
        fn: Function to compute value from error

    Returns:
        Success value or computed value

    Example:
        result = Failure("error")
        value = unwrap_or_else(result, lambda e: 0)  # value = 0
    """
    if isinstance(result, Success):
        return result.value
    return fn(result.error)


def map_error(result: Result[T, E], fn: Callable[[E], U]) -> Result[T, U]:
    """Map a function over the error value.

    If result is Failure, applies fn to the error.
    If result is Success, returns the success unchanged.

    Args:
        result: The Result to map over
        fn: Function to apply to error value

    Returns:
        New Result with mapped error or original success

    Example:
        result = Failure("error")
        mapped = map_error(result, lambda e: f"Failed: {e}")
        # mapped = Failure("Failed: error")
    """
    if isinstance(result, Failure):
        return Failure(fn(result.error))
    return result

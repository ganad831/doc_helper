"""Tests for Result monad."""

import pytest

from doc_helper.domain.common.result import (
    Failure,
    Result,
    Success,
    bind_result,
    map_error,
    map_result,
    unwrap,
    unwrap_or,
    unwrap_or_else,
)


class TestSuccess:
    """Tests for Success type."""

    def test_success_is_success(self) -> None:
        """Success should identify as success."""
        result: Result[int, str] = Success(42)
        assert result.is_success()
        assert not result.is_failure()

    def test_success_contains_value(self) -> None:
        """Success should contain the value."""
        result: Result[int, str] = Success(42)
        assert isinstance(result, Success)
        assert result.value == 42


class TestFailure:
    """Tests for Failure type."""

    def test_failure_is_failure(self) -> None:
        """Failure should identify as failure."""
        result: Result[int, str] = Failure("error")
        assert result.is_failure()
        assert not result.is_success()

    def test_failure_contains_error(self) -> None:
        """Failure should contain the error."""
        result: Result[int, str] = Failure("error")
        assert isinstance(result, Failure)
        assert result.error == "error"


class TestMapResult:
    """Tests for map_result function."""

    def test_map_success(self) -> None:
        """map_result should transform success value."""
        result: Result[int, str] = Success(5)
        mapped = map_result(result, lambda x: x * 2)
        assert isinstance(mapped, Success)
        assert mapped.value == 10

    def test_map_failure(self) -> None:
        """map_result should leave failure unchanged."""
        result: Result[int, str] = Failure("error")
        mapped = map_result(result, lambda x: x * 2)
        assert isinstance(mapped, Failure)
        assert mapped.error == "error"


class TestBindResult:
    """Tests for bind_result function."""

    def test_bind_success_to_success(self) -> None:
        """bind_result should chain success results."""

        def divide(x: int) -> Result[int, str]:
            if x == 0:
                return Failure("Division by zero")
            return Success(10 // x)

        result: Result[int, str] = Success(2)
        bound = bind_result(result, divide)
        assert isinstance(bound, Success)
        assert bound.value == 5

    def test_bind_success_to_failure(self) -> None:
        """bind_result should propagate failure from function."""

        def divide(x: int) -> Result[int, str]:
            if x == 0:
                return Failure("Division by zero")
            return Success(10 // x)

        result: Result[int, str] = Success(0)
        bound = bind_result(result, divide)
        assert isinstance(bound, Failure)
        assert bound.error == "Division by zero"

    def test_bind_failure(self) -> None:
        """bind_result should not call function on failure."""

        def divide(x: int) -> Result[int, str]:
            if x == 0:
                return Failure("Division by zero")
            return Success(10 // x)

        result: Result[int, str] = Failure("original error")
        bound = bind_result(result, divide)
        assert isinstance(bound, Failure)
        assert bound.error == "original error"


class TestUnwrap:
    """Tests for unwrap functions."""

    def test_unwrap_success(self) -> None:
        """unwrap should extract success value."""
        result: Result[int, str] = Success(42)
        value = unwrap(result)
        assert value == 42

    def test_unwrap_failure_raises(self) -> None:
        """unwrap should raise on failure."""
        result: Result[int, str] = Failure("error")
        with pytest.raises(ValueError, match="Cannot unwrap Failure"):
            unwrap(result)

    def test_unwrap_or_success(self) -> None:
        """unwrap_or should return value for success."""
        result: Result[int, str] = Success(42)
        value = unwrap_or(result, 0)
        assert value == 42

    def test_unwrap_or_failure(self) -> None:
        """unwrap_or should return default for failure."""
        result: Result[int, str] = Failure("error")
        value = unwrap_or(result, 0)
        assert value == 0

    def test_unwrap_or_else_success(self) -> None:
        """unwrap_or_else should return value for success."""
        result: Result[int, str] = Success(42)
        value = unwrap_or_else(result, lambda e: 0)
        assert value == 42

    def test_unwrap_or_else_failure(self) -> None:
        """unwrap_or_else should compute from error for failure."""
        result: Result[int, str] = Failure("error")
        value = unwrap_or_else(result, lambda e: len(e))
        assert value == 5  # len("error")


class TestMapError:
    """Tests for map_error function."""

    def test_map_error_failure(self) -> None:
        """map_error should transform failure error."""
        result: Result[int, str] = Failure("error")
        mapped = map_error(result, lambda e: f"Failed: {e}")
        assert isinstance(mapped, Failure)
        assert mapped.error == "Failed: error"

    def test_map_error_success(self) -> None:
        """map_error should leave success unchanged."""
        result: Result[int, str] = Success(42)
        mapped = map_error(result, lambda e: f"Failed: {e}")
        assert isinstance(mapped, Success)
        assert mapped.value == 42

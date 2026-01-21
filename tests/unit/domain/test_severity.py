"""Unit tests for Severity value object.

Tests ADR-025: Validation Severity Levels implementation.
"""

import pytest

from doc_helper.domain.validation.severity import Severity


class TestSeverityEnum:
    """Tests for Severity enum values."""

    def test_severity_has_three_levels(self) -> None:
        """Severity should have exactly three levels: ERROR, WARNING, INFO."""
        assert Severity.ERROR.value == "ERROR"
        assert Severity.WARNING.value == "WARNING"
        assert Severity.INFO.value == "INFO"

    def test_severity_is_string_enum(self) -> None:
        """Severity should be a string enum for serialization."""
        assert isinstance(Severity.ERROR, str)
        assert isinstance(Severity.WARNING, str)
        assert isinstance(Severity.INFO, str)


class TestBlocksWorkflow:
    """Tests for blocks_workflow() method."""

    def test_error_blocks_workflow(self) -> None:
        """ERROR severity should block workflows unconditionally."""
        assert Severity.ERROR.blocks_workflow() is True

    def test_warning_does_not_block_workflow(self) -> None:
        """WARNING severity should not block workflows unconditionally."""
        assert Severity.WARNING.blocks_workflow() is False

    def test_info_does_not_block_workflow(self) -> None:
        """INFO severity should not block workflows unconditionally."""
        assert Severity.INFO.blocks_workflow() is False


class TestRequiresConfirmation:
    """Tests for requires_confirmation() method."""

    def test_warning_requires_confirmation(self) -> None:
        """WARNING severity should require user confirmation."""
        assert Severity.WARNING.requires_confirmation() is True

    def test_error_does_not_require_confirmation(self) -> None:
        """ERROR severity blocks outright, no confirmation needed."""
        assert Severity.ERROR.requires_confirmation() is False

    def test_info_does_not_require_confirmation(self) -> None:
        """INFO severity never blocks, no confirmation needed."""
        assert Severity.INFO.requires_confirmation() is False


class TestIsInformational:
    """Tests for is_informational() method."""

    def test_info_is_informational(self) -> None:
        """INFO severity should be informational only."""
        assert Severity.INFO.is_informational() is True

    def test_error_is_not_informational(self) -> None:
        """ERROR severity is not informational."""
        assert Severity.ERROR.is_informational() is False

    def test_warning_is_not_informational(self) -> None:
        """WARNING severity is not informational."""
        assert Severity.WARNING.is_informational() is False


class TestDefault:
    """Tests for default() class method."""

    def test_default_is_error(self) -> None:
        """Default severity should be ERROR for backward compatibility."""
        assert Severity.default() == Severity.ERROR

    def test_default_returns_severity(self) -> None:
        """Default should return a Severity enum."""
        assert isinstance(Severity.default(), Severity)


class TestSeverityComparison:
    """Tests for Severity comparison and equality."""

    def test_severity_equality(self) -> None:
        """Severity values should support equality comparison."""
        assert Severity.ERROR == Severity.ERROR
        assert Severity.WARNING == Severity.WARNING
        assert Severity.INFO == Severity.INFO

    def test_severity_inequality(self) -> None:
        """Different severity levels should not be equal."""
        assert Severity.ERROR != Severity.WARNING
        assert Severity.WARNING != Severity.INFO
        assert Severity.ERROR != Severity.INFO

    def test_severity_string_comparison(self) -> None:
        """Severity should compare equal to its string value."""
        assert Severity.ERROR == "ERROR"
        assert Severity.WARNING == "WARNING"
        assert Severity.INFO == "INFO"


class TestSeverityADR025Compliance:
    """Tests verifying ADR-025 compliance."""

    def test_severity_is_explicit_not_inferred(self) -> None:
        """Severity is declared explicitly, not inferred at runtime.

        ADR-025 Rule: Severity is explicit (not inferred at runtime)
        """
        # This test documents that severity is a first-class value
        # that must be explicitly set, not derived from context
        severity = Severity.ERROR
        assert severity.value == "ERROR"
        # Severity cannot be calculated from other properties
        # It must be declared when creating constraints

    def test_default_severity_preserves_backward_compatibility(self) -> None:
        """Default severity is ERROR to preserve existing blocking behavior.

        ADR-025 Rule: Backward compatible - existing constraints default to ERROR
        """
        default = Severity.default()
        assert default == Severity.ERROR
        assert default.blocks_workflow() is True

    def test_workflow_control_semantics(self) -> None:
        """Each severity level has distinct workflow control semantics.

        ADR-025 Rules:
        - ERROR: Blocks workflows unconditionally (must be resolved)
        - WARNING: Allows continuation with explicit user confirmation
        - INFO: Informational only, never blocks workflows
        """
        # ERROR blocks
        assert Severity.ERROR.blocks_workflow() is True
        assert Severity.ERROR.requires_confirmation() is False
        assert Severity.ERROR.is_informational() is False

        # WARNING requires confirmation
        assert Severity.WARNING.blocks_workflow() is False
        assert Severity.WARNING.requires_confirmation() is True
        assert Severity.WARNING.is_informational() is False

        # INFO never blocks
        assert Severity.INFO.blocks_workflow() is False
        assert Severity.INFO.requires_confirmation() is False
        assert Severity.INFO.is_informational() is True

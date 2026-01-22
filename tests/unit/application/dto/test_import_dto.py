"""Unit tests for Import DTOs (Phase 4)."""

import pytest

from doc_helper.application.dto.import_dto import (
    EnforcementPolicy,
    IdenticalSchemaAction,
    ImportResult,
    ImportValidationError,
    ImportWarning,
)
from doc_helper.domain.schema.schema_compatibility import CompatibilityLevel, CompatibilityResult


class TestEnforcementPolicy:
    """Tests for EnforcementPolicy enum."""

    def test_strict_value(self) -> None:
        """STRICT policy should have correct value."""
        assert EnforcementPolicy.STRICT.value == "strict"

    def test_warn_value(self) -> None:
        """WARN policy should have correct value."""
        assert EnforcementPolicy.WARN.value == "warn"

    def test_none_value(self) -> None:
        """NONE policy should have correct value."""
        assert EnforcementPolicy.NONE.value == "none"


class TestIdenticalSchemaAction:
    """Tests for IdenticalSchemaAction enum."""

    def test_skip_value(self) -> None:
        """SKIP action should have correct value."""
        assert IdenticalSchemaAction.SKIP.value == "skip"

    def test_replace_value(self) -> None:
        """REPLACE action should have correct value."""
        assert IdenticalSchemaAction.REPLACE.value == "replace"


class TestImportWarning:
    """Tests for ImportWarning DTO."""

    def test_create_warning(self) -> None:
        """Should create warning with category and message."""
        warning = ImportWarning(
            category="version_backward",
            message="Imported version is older",
        )
        assert warning.category == "version_backward"
        assert warning.message == "Imported version is older"

    def test_warning_is_immutable(self) -> None:
        """Warning should be immutable."""
        warning = ImportWarning(
            category="test",
            message="test message",
        )
        with pytest.raises(AttributeError):
            warning.category = "changed"


class TestImportValidationError:
    """Tests for ImportValidationError DTO."""

    def test_create_error_without_location(self) -> None:
        """Should create error without location."""
        error = ImportValidationError(
            category="json_syntax",
            message="Invalid JSON",
        )
        assert error.category == "json_syntax"
        assert error.message == "Invalid JSON"
        assert error.location is None

    def test_create_error_with_location(self) -> None:
        """Should create error with location."""
        error = ImportValidationError(
            category="invalid_value",
            message="Invalid field type",
            location="entities[0].fields[2].field_type",
        )
        assert error.location == "entities[0].fields[2].field_type"

    def test_error_is_immutable(self) -> None:
        """Error should be immutable."""
        error = ImportValidationError(
            category="test",
            message="test",
        )
        with pytest.raises(AttributeError):
            error.category = "changed"


class TestImportResult:
    """Tests for ImportResult DTO."""

    def test_create_success_result(self) -> None:
        """Should create successful import result."""
        result = ImportResult(
            success=True,
            schema_id="test_schema",
            imported_version="1.0.0",
            entity_count=3,
            field_count=15,
        )
        assert result.success is True
        assert result.schema_id == "test_schema"
        assert result.imported_version == "1.0.0"
        assert result.entity_count == 3
        assert result.field_count == 15
        assert result.error is None

    def test_create_failure_result(self) -> None:
        """Should create failed import result."""
        error = ImportValidationError(
            category="json_syntax",
            message="Invalid JSON",
        )
        result = ImportResult(
            success=False,
            validation_errors=(error,),
            error="Validation failed",
        )
        assert result.success is False
        assert len(result.validation_errors) == 1
        assert result.error == "Validation failed"

    def test_create_result_with_warnings(self) -> None:
        """Should create result with warnings."""
        warning = ImportWarning(
            category="empty_entity",
            message="Entity has no fields",
        )
        result = ImportResult(
            success=True,
            warnings=(warning,),
            entity_count=1,
            field_count=0,
        )
        assert len(result.warnings) == 1
        assert result.warnings[0].category == "empty_entity"

    def test_create_result_with_compatibility(self) -> None:
        """Should create result with compatibility info."""
        compat_result = CompatibilityResult(
            level=CompatibilityLevel.COMPATIBLE,
            changes=(),
        )
        result = ImportResult(
            success=True,
            compatibility_result=compat_result,
            entity_count=2,
            field_count=10,
        )
        assert result.compatibility_result is not None
        assert result.compatibility_result.level == CompatibilityLevel.COMPATIBLE

    def test_create_skipped_result(self) -> None:
        """Should create result for skipped import (identical schema)."""
        result = ImportResult(
            success=True,
            was_identical=True,
            was_skipped=True,
            entity_count=2,
            field_count=10,
        )
        assert result.was_identical is True
        assert result.was_skipped is True

    def test_result_is_immutable(self) -> None:
        """Result should be immutable."""
        result = ImportResult(success=True)
        with pytest.raises(AttributeError):
            result.success = False

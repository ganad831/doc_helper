"""Unit tests for SchemaCompatibility types (Phase 3)."""

import pytest

from doc_helper.domain.schema.schema_change import ChangeType, SchemaChange
from doc_helper.domain.schema.schema_compatibility import (
    CompatibilityLevel,
    CompatibilityResult,
)
from doc_helper.domain.schema.schema_version import SchemaVersion


class TestCompatibilityLevel:
    """Unit tests for CompatibilityLevel enum."""

    def test_identical_display_name(self) -> None:
        """Should have 'Identical' display name."""
        assert CompatibilityLevel.IDENTICAL.display_name == "Identical"

    def test_compatible_display_name(self) -> None:
        """Should have 'Compatible' display name."""
        assert CompatibilityLevel.COMPATIBLE.display_name == "Compatible"

    def test_incompatible_display_name(self) -> None:
        """Should have 'Incompatible' display name."""
        assert CompatibilityLevel.INCOMPATIBLE.display_name == "Incompatible"

    def test_descriptions_not_empty(self) -> None:
        """All levels should have descriptions."""
        for level in CompatibilityLevel:
            assert level.description
            assert len(level.description) > 0


class TestCompatibilityResult:
    """Unit tests for CompatibilityResult value object."""

    # =========================================================================
    # Creation Tests
    # =========================================================================

    def test_create_identical_result(self) -> None:
        """Should create identical result with no changes."""
        result = CompatibilityResult(
            level=CompatibilityLevel.IDENTICAL,
            changes=(),
        )
        assert result.level == CompatibilityLevel.IDENTICAL
        assert result.total_changes == 0

    def test_create_compatible_result(self) -> None:
        """Should create compatible result with non-breaking changes."""
        changes = (
            SchemaChange(ChangeType.FIELD_ADDED, "project", "new_field"),
        )
        result = CompatibilityResult(
            level=CompatibilityLevel.COMPATIBLE,
            changes=changes,
        )
        assert result.level == CompatibilityLevel.COMPATIBLE
        assert result.total_changes == 1

    def test_create_incompatible_result(self) -> None:
        """Should create incompatible result with breaking changes."""
        changes = (
            SchemaChange(ChangeType.FIELD_REMOVED, "project", "old_field"),
        )
        result = CompatibilityResult(
            level=CompatibilityLevel.INCOMPATIBLE,
            changes=changes,
        )
        assert result.level == CompatibilityLevel.INCOMPATIBLE
        assert result.total_changes == 1

    def test_create_result_with_versions(self) -> None:
        """Should store version information."""
        result = CompatibilityResult(
            level=CompatibilityLevel.IDENTICAL,
            changes=(),
            source_version=SchemaVersion(1, 0, 0),
            target_version=SchemaVersion(1, 1, 0),
        )
        assert result.source_version == SchemaVersion(1, 0, 0)
        assert result.target_version == SchemaVersion(1, 1, 0)

    # =========================================================================
    # Level Check Properties
    # =========================================================================

    def test_is_identical_true(self) -> None:
        """Should return True for identical level."""
        result = CompatibilityResult(
            level=CompatibilityLevel.IDENTICAL,
            changes=(),
        )
        assert result.is_identical is True
        assert result.is_compatible is True
        assert result.is_incompatible is False

    def test_is_compatible_true(self) -> None:
        """Should return True for compatible level."""
        result = CompatibilityResult(
            level=CompatibilityLevel.COMPATIBLE,
            changes=(),
        )
        assert result.is_identical is False
        assert result.is_compatible is True
        assert result.is_incompatible is False

    def test_is_incompatible_true(self) -> None:
        """Should return True for incompatible level."""
        result = CompatibilityResult(
            level=CompatibilityLevel.INCOMPATIBLE,
            changes=(),
        )
        assert result.is_identical is False
        assert result.is_compatible is False
        assert result.is_incompatible is True

    # =========================================================================
    # Change Counting Tests
    # =========================================================================

    def test_total_changes_count(self) -> None:
        """Should count all changes."""
        changes = (
            SchemaChange(ChangeType.FIELD_ADDED, "e1", "f1"),
            SchemaChange(ChangeType.FIELD_REMOVED, "e1", "f2"),
            SchemaChange(ChangeType.ENTITY_ADDED, "e2"),
        )
        result = CompatibilityResult(
            level=CompatibilityLevel.INCOMPATIBLE,
            changes=changes,
        )
        assert result.total_changes == 3

    def test_breaking_changes_filter(self) -> None:
        """Should filter to only breaking changes."""
        changes = (
            SchemaChange(ChangeType.FIELD_ADDED, "e1", "f1"),  # non-breaking
            SchemaChange(ChangeType.FIELD_REMOVED, "e1", "f2"),  # breaking
            SchemaChange(ChangeType.ENTITY_ADDED, "e2"),  # non-breaking
            SchemaChange(ChangeType.FIELD_TYPE_CHANGED, "e1", "f3"),  # breaking
        )
        result = CompatibilityResult(
            level=CompatibilityLevel.INCOMPATIBLE,
            changes=changes,
        )
        assert result.breaking_change_count == 2
        breaking = result.breaking_changes
        assert len(breaking) == 2
        assert all(c.is_breaking for c in breaking)

    def test_non_breaking_changes_filter(self) -> None:
        """Should filter to only non-breaking changes."""
        changes = (
            SchemaChange(ChangeType.FIELD_ADDED, "e1", "f1"),  # non-breaking
            SchemaChange(ChangeType.FIELD_REMOVED, "e1", "f2"),  # breaking
            SchemaChange(ChangeType.ENTITY_ADDED, "e2"),  # non-breaking
        )
        result = CompatibilityResult(
            level=CompatibilityLevel.INCOMPATIBLE,
            changes=changes,
        )
        assert result.non_breaking_change_count == 2
        non_breaking = result.non_breaking_changes
        assert len(non_breaking) == 2
        assert all(not c.is_breaking for c in non_breaking)

    # =========================================================================
    # Summary Tests
    # =========================================================================

    def test_summary_identical(self) -> None:
        """Should generate identical summary."""
        result = CompatibilityResult(
            level=CompatibilityLevel.IDENTICAL,
            changes=(),
        )
        assert "identical" in result.summary.lower()

    def test_summary_with_breaking_changes(self) -> None:
        """Should include breaking change count in summary."""
        changes = (
            SchemaChange(ChangeType.FIELD_REMOVED, "e1", "f1"),
            SchemaChange(ChangeType.FIELD_REMOVED, "e1", "f2"),
        )
        result = CompatibilityResult(
            level=CompatibilityLevel.INCOMPATIBLE,
            changes=changes,
        )
        assert "2 breaking" in result.summary

    def test_summary_with_mixed_changes(self) -> None:
        """Should include both breaking and non-breaking counts."""
        changes = (
            SchemaChange(ChangeType.FIELD_REMOVED, "e1", "f1"),  # breaking
            SchemaChange(ChangeType.FIELD_ADDED, "e1", "f2"),  # non-breaking
            SchemaChange(ChangeType.FIELD_ADDED, "e1", "f3"),  # non-breaking
        )
        result = CompatibilityResult(
            level=CompatibilityLevel.INCOMPATIBLE,
            changes=changes,
        )
        assert "1 breaking" in result.summary
        assert "2 non-breaking" in result.summary

    # =========================================================================
    # Grouping Tests
    # =========================================================================

    def test_get_changes_by_entity(self) -> None:
        """Should group changes by entity ID."""
        changes = (
            SchemaChange(ChangeType.FIELD_ADDED, "entity_a", "f1"),
            SchemaChange(ChangeType.FIELD_ADDED, "entity_b", "f2"),
            SchemaChange(ChangeType.FIELD_REMOVED, "entity_a", "f3"),
        )
        result = CompatibilityResult(
            level=CompatibilityLevel.INCOMPATIBLE,
            changes=changes,
        )
        grouped = result.get_changes_by_entity()

        assert len(grouped) == 2
        assert len(grouped["entity_a"]) == 2
        assert len(grouped["entity_b"]) == 1

    def test_get_changes_by_entity_empty(self) -> None:
        """Should return empty dict for no changes."""
        result = CompatibilityResult(
            level=CompatibilityLevel.IDENTICAL,
            changes=(),
        )
        grouped = result.get_changes_by_entity()
        assert grouped == {}

"""Unit tests for SchemaVersion value object (Phase 3)."""

import pytest

from doc_helper.domain.schema.schema_version import SchemaVersion


class TestSchemaVersion:
    """Unit tests for SchemaVersion."""

    # =========================================================================
    # Creation Tests
    # =========================================================================

    def test_create_version_success(self) -> None:
        """Should create version with valid components."""
        version = SchemaVersion(1, 2, 3)
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_create_initial_version(self) -> None:
        """Should create initial version 1.0.0."""
        version = SchemaVersion.initial()
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_create_version_from_string(self) -> None:
        """Should parse version from string."""
        version = SchemaVersion.from_string("2.1.0")
        assert version.major == 2
        assert version.minor == 1
        assert version.patch == 0

    def test_create_version_from_string_with_whitespace(self) -> None:
        """Should handle whitespace in version string."""
        version = SchemaVersion.from_string("  1.0.0  ")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    # =========================================================================
    # Validation Tests
    # =========================================================================

    def test_reject_negative_major(self) -> None:
        """Should reject negative major version."""
        with pytest.raises(ValueError, match="Major version must be non-negative"):
            SchemaVersion(-1, 0, 0)

    def test_reject_negative_minor(self) -> None:
        """Should reject negative minor version."""
        with pytest.raises(ValueError, match="Minor version must be non-negative"):
            SchemaVersion(1, -1, 0)

    def test_reject_negative_patch(self) -> None:
        """Should reject negative patch version."""
        with pytest.raises(ValueError, match="Patch version must be non-negative"):
            SchemaVersion(1, 0, -1)

    def test_reject_empty_string(self) -> None:
        """Should reject empty version string."""
        with pytest.raises(ValueError, match="Version string cannot be empty"):
            SchemaVersion.from_string("")

    def test_reject_invalid_format(self) -> None:
        """Should reject invalid version format."""
        with pytest.raises(ValueError, match="Invalid version format"):
            SchemaVersion.from_string("1.0")

    def test_reject_non_numeric(self) -> None:
        """Should reject non-numeric version components."""
        with pytest.raises(ValueError, match="Invalid version format"):
            SchemaVersion.from_string("1.a.0")

    # =========================================================================
    # String Representation Tests
    # =========================================================================

    def test_str_representation(self) -> None:
        """Should return MAJOR.MINOR.PATCH string."""
        version = SchemaVersion(2, 1, 3)
        assert str(version) == "2.1.3"

    def test_str_round_trip(self) -> None:
        """Should round-trip through string conversion."""
        original = SchemaVersion(1, 2, 3)
        parsed = SchemaVersion.from_string(str(original))
        assert parsed == original

    # =========================================================================
    # Comparison Tests
    # =========================================================================

    def test_equality(self) -> None:
        """Should compare equal versions correctly."""
        v1 = SchemaVersion(1, 0, 0)
        v2 = SchemaVersion(1, 0, 0)
        assert v1 == v2

    def test_inequality(self) -> None:
        """Should detect unequal versions."""
        v1 = SchemaVersion(1, 0, 0)
        v2 = SchemaVersion(1, 0, 1)
        assert v1 != v2

    def test_less_than_major(self) -> None:
        """Should compare major versions correctly."""
        v1 = SchemaVersion(1, 9, 9)
        v2 = SchemaVersion(2, 0, 0)
        assert v1 < v2
        assert not v2 < v1

    def test_less_than_minor(self) -> None:
        """Should compare minor versions correctly."""
        v1 = SchemaVersion(1, 0, 9)
        v2 = SchemaVersion(1, 1, 0)
        assert v1 < v2
        assert not v2 < v1

    def test_less_than_patch(self) -> None:
        """Should compare patch versions correctly."""
        v1 = SchemaVersion(1, 0, 0)
        v2 = SchemaVersion(1, 0, 1)
        assert v1 < v2
        assert not v2 < v1

    def test_greater_than(self) -> None:
        """Should support greater than comparison."""
        v1 = SchemaVersion(2, 0, 0)
        v2 = SchemaVersion(1, 9, 9)
        assert v1 > v2
        assert not v2 > v1

    def test_less_than_or_equal(self) -> None:
        """Should support less than or equal comparison."""
        v1 = SchemaVersion(1, 0, 0)
        v2 = SchemaVersion(1, 0, 0)
        v3 = SchemaVersion(1, 0, 1)
        assert v1 <= v2
        assert v1 <= v3
        assert not v3 <= v1

    def test_greater_than_or_equal(self) -> None:
        """Should support greater than or equal comparison."""
        v1 = SchemaVersion(1, 0, 1)
        v2 = SchemaVersion(1, 0, 1)
        v3 = SchemaVersion(1, 0, 0)
        assert v1 >= v2
        assert v1 >= v3
        assert not v3 >= v1

    # =========================================================================
    # Bump Tests
    # =========================================================================

    def test_bump_major(self) -> None:
        """Should bump major and reset minor/patch."""
        version = SchemaVersion(1, 2, 3)
        bumped = version.bump_major()
        assert bumped == SchemaVersion(2, 0, 0)

    def test_bump_minor(self) -> None:
        """Should bump minor and reset patch."""
        version = SchemaVersion(1, 2, 3)
        bumped = version.bump_minor()
        assert bumped == SchemaVersion(1, 3, 0)

    def test_bump_patch(self) -> None:
        """Should bump patch only."""
        version = SchemaVersion(1, 2, 3)
        bumped = version.bump_patch()
        assert bumped == SchemaVersion(1, 2, 4)

    def test_bump_is_immutable(self) -> None:
        """Should not modify original version."""
        version = SchemaVersion(1, 0, 0)
        _ = version.bump_major()
        assert version == SchemaVersion(1, 0, 0)

    # =========================================================================
    # Compatibility Tests
    # =========================================================================

    def test_compatible_same_major(self) -> None:
        """Should be compatible with same major version."""
        v1 = SchemaVersion(1, 0, 0)
        v2 = SchemaVersion(1, 5, 3)
        assert v1.is_compatible_with(v2)
        assert v2.is_compatible_with(v1)

    def test_incompatible_different_major(self) -> None:
        """Should be incompatible with different major version."""
        v1 = SchemaVersion(1, 9, 9)
        v2 = SchemaVersion(2, 0, 0)
        assert not v1.is_compatible_with(v2)
        assert not v2.is_compatible_with(v1)

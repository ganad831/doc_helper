"""Schema Version value object (Phase 3).

Semantic versioning for schema definitions.
Format: MAJOR.MINOR.PATCH

APPROVED DECISIONS:
- Decision 1: Semantic versioning (MAJOR.MINOR.PATCH)
- Decision 5: Version field is optional in export
"""

from dataclasses import dataclass
import re
from typing import Optional

from doc_helper.domain.common.value_object import ValueObject


@dataclass(frozen=True)
class SchemaVersion(ValueObject):
    """Semantic version for schema definitions.

    Format: MAJOR.MINOR.PATCH
    - MAJOR: Breaking changes (entity/field deleted, type changed)
    - MINOR: Non-breaking structural changes (additions)
    - PATCH: Metadata-only changes

    Examples:
        version = SchemaVersion(1, 0, 0)
        version = SchemaVersion.from_string("2.1.0")
        version = SchemaVersion.initial()  # 1.0.0

    RULES:
    - All components must be non-negative integers
    - Version comparison follows semantic versioning rules
    - Version is informational only (does not block operations)
    """

    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        """Validate version components."""
        if self.major < 0:
            raise ValueError(f"Major version must be non-negative: {self.major}")
        if self.minor < 0:
            raise ValueError(f"Minor version must be non-negative: {self.minor}")
        if self.patch < 0:
            raise ValueError(f"Patch version must be non-negative: {self.patch}")

    def __str__(self) -> str:
        """String representation: MAJOR.MINOR.PATCH."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "SchemaVersion") -> bool:
        """Compare versions for ordering."""
        if not isinstance(other, SchemaVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: "SchemaVersion") -> bool:
        """Compare versions for ordering."""
        if not isinstance(other, SchemaVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __gt__(self, other: "SchemaVersion") -> bool:
        """Compare versions for ordering."""
        if not isinstance(other, SchemaVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: "SchemaVersion") -> bool:
        """Compare versions for ordering."""
        if not isinstance(other, SchemaVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    @staticmethod
    def initial() -> "SchemaVersion":
        """Create initial version 1.0.0.

        Returns:
            SchemaVersion(1, 0, 0)
        """
        return SchemaVersion(1, 0, 0)

    @staticmethod
    def from_string(version_str: str) -> "SchemaVersion":
        """Parse version from string.

        Args:
            version_str: Version string in format "MAJOR.MINOR.PATCH"

        Returns:
            SchemaVersion instance

        Raises:
            ValueError: If format is invalid
        """
        if not version_str:
            raise ValueError("Version string cannot be empty")

        pattern = r"^(\d+)\.(\d+)\.(\d+)$"
        match = re.match(pattern, version_str.strip())

        if not match:
            raise ValueError(
                f"Invalid version format: '{version_str}'. "
                "Expected MAJOR.MINOR.PATCH (e.g., '1.0.0')"
            )

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))

        return SchemaVersion(major, minor, patch)

    def bump_major(self) -> "SchemaVersion":
        """Create new version with incremented major (resets minor and patch).

        Use for breaking changes.

        Returns:
            New SchemaVersion with major+1, minor=0, patch=0
        """
        return SchemaVersion(self.major + 1, 0, 0)

    def bump_minor(self) -> "SchemaVersion":
        """Create new version with incremented minor (resets patch).

        Use for non-breaking additions.

        Returns:
            New SchemaVersion with same major, minor+1, patch=0
        """
        return SchemaVersion(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "SchemaVersion":
        """Create new version with incremented patch.

        Use for metadata-only changes.

        Returns:
            New SchemaVersion with same major and minor, patch+1
        """
        return SchemaVersion(self.major, self.minor, self.patch + 1)

    def is_compatible_with(self, other: "SchemaVersion") -> bool:
        """Check if this version is compatible with another.

        Compatibility means same major version.

        Args:
            other: Version to check compatibility with

        Returns:
            True if major versions match
        """
        return self.major == other.major

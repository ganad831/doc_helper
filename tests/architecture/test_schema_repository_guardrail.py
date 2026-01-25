"""Architectural guardrail: Prevent legacy schema repository reintroduction.

This test enforces Phase M-1 authority decision:
- AUTHORITATIVE: sqlite/repositories/schema_repository.py
- FORBIDDEN: sqlite_schema_repository.py (any location)

If this test fails, a legacy schema repository has been reintroduced.
This is a BLOCKING ARCHITECTURAL VIOLATION.

Do NOT:
- Skip this test
- Add compatibility layers
- Create aliases or re-exports
- Bypass with feature flags

Reference: Phase M-1 through M-4 repository consolidation.
"""

import ast
import pytest
from pathlib import Path


# Authoritative repository location (the ONLY valid schema repository)
AUTHORITATIVE_REPO = Path(
    "src/doc_helper/infrastructure/persistence/sqlite/repositories/schema_repository.py"
)

# Forbidden patterns - these must NEVER appear in the codebase
FORBIDDEN_FILENAMES = [
    "sqlite_schema_repository.py",
]

FORBIDDEN_IMPORT_PATTERNS = [
    "from doc_helper.infrastructure.persistence.sqlite_schema_repository",
    "import doc_helper.infrastructure.persistence.sqlite_schema_repository",
    "from doc_helper.infrastructure.persistence import sqlite_schema_repository",
]

FORBIDDEN_SYMBOL_IN_LEGACY_PATH = "SqliteSchemaRepository"


class TestSchemaRepositoryGuardrail:
    """Architectural guardrail tests for schema repository authority."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent

    def test_authoritative_repository_exists(self, repo_root: Path) -> None:
        """The authoritative schema repository MUST exist."""
        authoritative_path = repo_root / AUTHORITATIVE_REPO
        assert authoritative_path.exists(), (
            f"ARCHITECTURAL VIOLATION: Authoritative schema repository missing.\n"
            f"Expected: {AUTHORITATIVE_REPO}\n"
            f"The sole authoritative schema repository has been deleted or moved.\n"
            f"This is a blocking violation."
        )

    def test_legacy_repository_file_does_not_exist(self, repo_root: Path) -> None:
        """Legacy schema repository file MUST NOT exist anywhere."""
        src_dir = repo_root / "src"

        for forbidden_filename in FORBIDDEN_FILENAMES:
            matches = list(src_dir.rglob(forbidden_filename))
            assert len(matches) == 0, (
                f"ARCHITECTURAL VIOLATION: Legacy schema repository detected.\n"
                f"Forbidden file found: {matches}\n"
                f"The legacy repository was removed in Phase M-4.\n"
                f"Reintroduction is a blocking architectural violation.\n"
                f"Authoritative repository: {AUTHORITATIVE_REPO}"
            )

    def test_no_legacy_imports_in_source(self, repo_root: Path) -> None:
        """No source file may import the legacy schema repository."""
        src_dir = repo_root / "src"
        violations = []

        for py_file in src_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                for pattern in FORBIDDEN_IMPORT_PATTERNS:
                    if pattern in content:
                        violations.append(f"{py_file}: contains '{pattern}'")
            except Exception:
                continue

        assert len(violations) == 0, (
            f"ARCHITECTURAL VIOLATION: Legacy imports detected.\n"
            f"Violations:\n" + "\n".join(f"  - {v}" for v in violations) + "\n"
            f"The legacy repository was removed in Phase M-4.\n"
            f"All imports must use: "
            f"from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository"
        )

    def test_no_legacy_imports_in_tests(self, repo_root: Path) -> None:
        """No test file may import the legacy schema repository."""
        tests_dir = repo_root / "tests"
        violations = []

        for py_file in tests_dir.rglob("*.py"):
            # Skip this guardrail test itself
            if py_file.name == "test_schema_repository_guardrail.py":
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                for pattern in FORBIDDEN_IMPORT_PATTERNS:
                    if pattern in content:
                        violations.append(f"{py_file}: contains '{pattern}'")
            except Exception:
                continue

        assert len(violations) == 0, (
            f"ARCHITECTURAL VIOLATION: Legacy imports in tests.\n"
            f"Violations:\n" + "\n".join(f"  - {v}" for v in violations) + "\n"
            f"Tests must use the authoritative repository only."
        )

    def test_authoritative_repository_exports_correct_class(
        self, repo_root: Path
    ) -> None:
        """The authoritative repository must export SqliteSchemaRepository."""
        authoritative_path = repo_root / AUTHORITATIVE_REPO

        if not authoritative_path.exists():
            pytest.skip("Authoritative repository missing (separate test failure)")

        content = authoritative_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        class_names = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]

        assert "SqliteSchemaRepository" in class_names, (
            f"ARCHITECTURAL VIOLATION: Authoritative repository malformed.\n"
            f"Expected class 'SqliteSchemaRepository' not found in:\n"
            f"  {AUTHORITATIVE_REPO}\n"
            f"The authoritative repository must define this class."
        )

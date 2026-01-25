"""Architectural guard: Repository methods must not call other public methods.

This prevents nested connection bugs where a public method opens a connection
and then calls another public method that tries to open a second connection.

Rule: Public methods (no underscore prefix) in repositories MUST NOT call
other public methods of the same class. They should use private helpers instead.

KNOWN LIMITATIONS:
1. This guard only catches DIRECT public→public calls (e.g., `self.get_by_id()`).
   It does NOT detect indirect calls through private helpers:
       def public_a(): self._helper()
       def _helper(): self.public_b()  # Not caught
   This is acceptable because our `_*_with_cursor()` helpers are cursor-based
   by design, enforcing connection safety through the pattern itself.

2. This is a static analysis guard - runtime behavior is tested separately in
   test_schema_bootstrap.py::test_get_all_does_not_raise_nested_connection_error
"""

import ast
import inspect
from pathlib import Path

import pytest


class PublicMethodCallVisitor(ast.NodeVisitor):
    """AST visitor that detects public method calls within public methods."""

    def __init__(self, class_name: str, public_methods: set[str]) -> None:
        self.class_name = class_name
        self.public_methods = public_methods
        self.current_method: str | None = None
        self.violations: list[tuple[str, str, int]] = []  # (caller, callee, line)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Track if we're in a public method (no underscore prefix)
        if not node.name.startswith("_"):
            self.current_method = node.name
            self.generic_visit(node)
            self.current_method = None
        else:
            self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check for self.method_name() calls
        if (
            self.current_method
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
        ):
            called_method = node.func.attr
            # If calling another public method (not private/dunder)
            if (
                called_method in self.public_methods
                and called_method != self.current_method
                and not called_method.startswith("_")
            ):
                self.violations.append(
                    (self.current_method, called_method, node.lineno)
                )

        self.generic_visit(node)


def get_public_methods(tree: ast.AST) -> set[str]:
    """Extract all public method names from an AST."""
    methods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    methods.add(item.name)
    return methods


def uses_sqlite_connection_context_manager(source: str) -> bool:
    """Check if the repository uses SqliteConnection context manager pattern.

    Repositories that receive a raw connection in __init__ (e.g., attachment_repository)
    don't have the nested connection issue and should be excluded from this test.

    Args:
        source: Python source code

    Returns:
        True if uses SqliteConnection pattern, False if uses raw connection injection
    """
    # Check if SqliteConnection is imported and used
    return "SqliteConnection" in source and "with self._connection as conn:" in source


def check_repository_for_nested_calls(file_path: Path) -> list[str]:
    """Check a repository file for public methods calling other public methods.

    Args:
        file_path: Path to the repository Python file

    Returns:
        List of violation messages
    """
    source = file_path.read_text(encoding="utf-8")

    # Skip repositories that don't use SqliteConnection context manager pattern
    # (e.g., attachment_repository receives raw connection, no nested connection risk)
    if not uses_sqlite_connection_context_manager(source):
        return []

    tree = ast.parse(source)

    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and "Repository" in node.name:
            # Get all public methods in this class
            public_methods = set()
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    public_methods.add(item.name)

            # Check for violations
            visitor = PublicMethodCallVisitor(node.name, public_methods)
            visitor.visit(node)

            for caller, callee, line in visitor.violations:
                violations.append(
                    f"{file_path.name}:{line} - {node.name}.{caller}() calls "
                    f"public method {callee}() - use private helper instead"
                )

    return violations


class TestRepositoryNoNestedCalls:
    """Guard test: Repository public methods must not call other public methods."""

    def test_schema_repository_no_nested_public_calls(self) -> None:
        """SqliteSchemaRepository must not have nested public method calls."""
        repo_path = Path(
            "src/doc_helper/infrastructure/persistence/sqlite/repositories/schema_repository.py"
        )

        if not repo_path.exists():
            pytest.skip(f"Repository file not found: {repo_path}")

        violations = check_repository_for_nested_calls(repo_path)

        assert not violations, (
            "Repository has public methods calling other public methods "
            "(risk of nested connection errors):\n" + "\n".join(violations)
        )

    def test_all_sqlite_repositories_no_nested_public_calls(self) -> None:
        """All SQLite repositories must not have nested public method calls."""
        repo_dirs = [
            Path("src/doc_helper/infrastructure/persistence/sqlite/repositories"),
            Path("src/doc_helper/infrastructure/persistence"),
        ]

        all_violations = []

        for repo_dir in repo_dirs:
            if not repo_dir.exists():
                continue

            for repo_file in repo_dir.glob("*repository*.py"):
                # Skip __init__.py and test files
                if repo_file.name.startswith("_") or "test" in repo_file.name:
                    continue

                violations = check_repository_for_nested_calls(repo_file)
                all_violations.extend(violations)

        assert not all_violations, (
            "Repositories have public methods calling other public methods "
            "(risk of nested connection errors):\n" + "\n".join(all_violations)
        )

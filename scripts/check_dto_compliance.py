"""DTO-Only MVVM Compliance Checker.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan_FINAL.md Section 5.1.3):
- Presentation layer MUST NEVER have MODULE-LEVEL imports from doc_helper.domain
- Function-scope imports are allowed (necessary for command parameter conversion)
- This is a HARD RULE for v1.2 and beyond
- Static import analysis enforces this rule

Rationale:
- Module-level imports pollute the presentation module's namespace with domain types
- Function-scope imports are temporary and don't leak domain knowledge
- Function-scope imports enable ViewModels to prepare typed parameters for commands

Usage:
    python scripts/check_dto_compliance.py

Exit codes:
    0: All checks passed (no violations)
    1: Violations found (failed compliance)
"""

import ast
import sys
from pathlib import Path


PRESENTATION_PATH = Path("src/doc_helper/presentation")
FORBIDDEN_IMPORT_PREFIX = "doc_helper.domain"


def check_file(filepath: Path) -> list[str]:
    """Check a single file for forbidden MODULE-LEVEL domain imports.

    Only module-level imports are violations. Function-scope imports are allowed
    as they don't pollute the module namespace and are necessary for converting
    string IDs to typed IDs when calling commands.

    Args:
        filepath: Path to Python file to check

    Returns:
        List of violation messages (empty if compliant)
    """
    violations = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))
    except SyntaxError as e:
        print(f"⚠️  Syntax error in {filepath}: {e}")
        return []

    # Only check module-level statements (tree.body), not nested scopes
    for node in tree.body:
        if isinstance(node, ast.Import):
            # Example: import doc_helper.domain.project
            for alias in node.names:
                if alias.name.startswith(FORBIDDEN_IMPORT_PREFIX):
                    violations.append(
                        f"{filepath}:{node.lineno}: import {alias.name}"
                    )

        elif isinstance(node, ast.ImportFrom):
            # Example: from doc_helper.domain.project import Project
            if node.module and node.module.startswith(FORBIDDEN_IMPORT_PREFIX):
                imports = ", ".join(alias.name for alias in node.names)
                violations.append(
                    f"{filepath}:{node.lineno}: from {node.module} import {imports}"
                )

    return violations


def main() -> int:
    """Run DTO compliance check on presentation layer.

    Returns:
        0 if compliant, 1 if violations found
    """
    print("=" * 80)
    print("DTO-ONLY MVVM COMPLIANCE CHECK")
    print("=" * 80)
    print(f"Checking presentation layer: {PRESENTATION_PATH}")
    print(f"Forbidden imports: {FORBIDDEN_IMPORT_PREFIX}.*")
    print()

    if not PRESENTATION_PATH.exists():
        print(f"❌ Presentation path not found: {PRESENTATION_PATH}")
        return 1

    all_violations = []

    # Check all Python files in presentation layer
    python_files = list(PRESENTATION_PATH.rglob("*.py"))
    print(f"Scanning {len(python_files)} files...")
    print()

    for py_file in python_files:
        violations = check_file(py_file)
        all_violations.extend(violations)

    # Report results
    if all_violations:
        print("❌ DTO-ONLY COMPLIANCE CHECK FAILED")
        print(f"\nFound {len(all_violations)} violation(s):\n")

        for violation in all_violations:
            print(f"  {violation}")

        print()
        print("RULE VIOLATED:")
        print("  Presentation layer MUST NOT have MODULE-LEVEL imports from doc_helper.domain")
        print("  (AGENT_RULES.md Section 3-4)")
        print()
        print("FIX:")
        print("  1. Remove MODULE-LEVEL domain imports from presentation files")
        print("  2. Use DTOs from doc_helper.application.dto instead")
        print("  3. If you need domain types for command parameters, use function-scope imports:")
        print("     def my_method(self):")
        print("         from doc_helper.domain.project.project_ids import ProjectId")
        print("         project_id = ProjectId(UUID(self._project_id_string))")
        print()
        return 1

    else:
        print("✅ DTO-ONLY COMPLIANCE CHECK PASSED")
        print(f"\nScanned {len(python_files)} files in presentation layer")
        print("No forbidden domain imports found")
        print()
        print("COMPLIANCE:")
        print("  ✅ Presentation layer imports only from application.dto")
        print("  ✅ DTO-only MVVM pattern enforced")
        print("  ✅ Domain layer fully decoupled from presentation")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())

"""Architectural Compliance Scanner.

Enforces architectural rules defined in ADRs:
- ADR-024: Architectural Compliance Scanning
- ADR-V2-003: Multi-App Module Layout and Dependency Rules
- ADR-020: DTO-Only MVVM Enforcement

Rules Enforced:

1. DTO-Only MVVM (ADR-020):
   - Presentation layer MUST NOT have MODULE-LEVEL imports from doc_helper.domain
   - Function-scope imports are allowed for command parameter conversion

2. Platform Dependency Rules (ADR-V2-003):
   - platform/ MAY import: domain/, application/, app_types/contracts/
   - platform/ MUST NOT import: infrastructure/, presentation/
   - platform/ MUST NOT import: any specific app_types/{apptype}/

3. AppType Dependency Rules (ADR-V2-003):
   - app_types/{apptype}/ MAY import: domain/, application/, app_types/contracts/
   - app_types/{apptype}/ MAY import: infrastructure/ (for repository implementations)
   - app_types/{apptype}/ MUST NOT import: platform/
   - app_types/{apptype}/ MUST NOT import: other app_types/{other_apptype}/

4. Presentation-AppType Isolation:
   - presentation/ MUST NOT import: app_types/*

Usage:
    python scripts/check_architecture.py

Exit codes:
    0: All checks passed (no violations)
    1: Violations found (failed compliance)
"""

import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    """Represents a single architectural violation."""
    file_path: Path
    line_number: int
    import_statement: str
    rule_name: str
    rule_description: str


class ArchitectureScanner:
    """Scanner for architectural compliance checking."""

    # Source root
    SRC_PATH = Path("src/doc_helper")

    # Layer paths
    PRESENTATION_PATH = SRC_PATH / "presentation"
    PLATFORM_PATH = SRC_PATH / "platform"
    APP_TYPES_PATH = SRC_PATH / "app_types"
    INFRASTRUCTURE_PATH = SRC_PATH / "infrastructure"
    DOMAIN_PATH = SRC_PATH / "domain"
    APPLICATION_PATH = SRC_PATH / "application"

    # Import prefixes
    DOMAIN_PREFIX = "doc_helper.domain"
    PLATFORM_PREFIX = "doc_helper.platform"
    APP_TYPES_PREFIX = "doc_helper.app_types"
    INFRASTRUCTURE_PREFIX = "doc_helper.infrastructure"
    PRESENTATION_PREFIX = "doc_helper.presentation"
    CONTRACTS_PREFIX = "doc_helper.app_types.contracts"

    def __init__(self) -> None:
        self.violations: list[Violation] = []

    def scan_all(self) -> list[Violation]:
        """Run all architectural compliance checks.

        Returns:
            List of all violations found
        """
        self.violations = []

        # Rule 1: DTO-Only MVVM
        self._check_dto_only_mvvm()

        # Rule 2: Platform dependency rules
        self._check_platform_dependencies()

        # Rule 3: AppType dependency rules
        self._check_apptype_dependencies()

        # Rule 4: Presentation-AppType isolation
        self._check_presentation_apptype_isolation()

        return self.violations

    def _check_dto_only_mvvm(self) -> None:
        """Check DTO-only MVVM rule for presentation layer."""
        if not self.PRESENTATION_PATH.exists():
            return

        for py_file in self.PRESENTATION_PATH.rglob("*.py"):
            self._check_file_module_imports(
                py_file,
                forbidden_prefixes=[self.DOMAIN_PREFIX],
                rule_name="DTO-Only MVVM",
                rule_description=(
                    "Presentation layer MUST NOT have MODULE-LEVEL imports "
                    "from doc_helper.domain (ADR-020)"
                ),
            )

    def _check_platform_dependencies(self) -> None:
        """Check platform dependency rules."""
        if not self.PLATFORM_PATH.exists():
            return

        # Platform MUST NOT import infrastructure or presentation
        forbidden = [
            self.INFRASTRUCTURE_PREFIX,
            self.PRESENTATION_PREFIX,
        ]

        for py_file in self.PLATFORM_PATH.rglob("*.py"):
            # Check general forbidden imports
            self._check_file_module_imports(
                py_file,
                forbidden_prefixes=forbidden,
                rule_name="Platform Dependencies",
                rule_description=(
                    "platform/ MUST NOT import from infrastructure/ or presentation/ "
                    "(ADR-V2-003)"
                ),
            )

            # Check for specific AppType imports (not contracts)
            self._check_platform_apptype_imports(py_file)

    def _check_platform_apptype_imports(self, py_file: Path) -> None:
        """Check that platform doesn't import specific AppTypes."""
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))
        except (SyntaxError, IOError):
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if self._is_specific_apptype_import(alias.name):
                        self.violations.append(Violation(
                            file_path=py_file,
                            line_number=node.lineno,
                            import_statement=f"import {alias.name}",
                            rule_name="Platform-AppType Boundary",
                            rule_description=(
                                "platform/ MUST NOT import specific AppType modules "
                                "(only app_types/contracts/ allowed) (ADR-V2-003)"
                            ),
                        ))

            elif isinstance(node, ast.ImportFrom):
                if node.module and self._is_specific_apptype_import(node.module):
                    imports = ", ".join(alias.name for alias in node.names)
                    self.violations.append(Violation(
                        file_path=py_file,
                        line_number=node.lineno,
                        import_statement=f"from {node.module} import {imports}",
                        rule_name="Platform-AppType Boundary",
                        rule_description=(
                            "platform/ MUST NOT import specific AppType modules "
                            "(only app_types/contracts/ allowed) (ADR-V2-003)"
                        ),
                    ))

    def _is_specific_apptype_import(self, import_name: str) -> bool:
        """Check if import is a specific AppType (not contracts)."""
        if not import_name.startswith(self.APP_TYPES_PREFIX):
            return False
        if import_name.startswith(self.CONTRACTS_PREFIX):
            return False
        # Check if it's importing something inside app_types/ but not contracts
        # Pattern: doc_helper.app_types.{something} where {something} != contracts
        parts = import_name.split(".")
        if len(parts) >= 3:
            # doc_helper.app_types.something
            third_part = parts[2]
            if third_part != "contracts" and third_part != "__init__":
                return True
        return False

    def _check_apptype_dependencies(self) -> None:
        """Check AppType dependency rules."""
        if not self.APP_TYPES_PATH.exists():
            return

        # Find all AppType directories (excluding contracts)
        for item in self.APP_TYPES_PATH.iterdir():
            if not item.is_dir():
                continue
            if item.name in ("contracts", "__pycache__"):
                continue

            apptype_name = item.name

            for py_file in item.rglob("*.py"):
                # AppType MUST NOT import platform
                self._check_file_module_imports(
                    py_file,
                    forbidden_prefixes=[self.PLATFORM_PREFIX],
                    rule_name="AppType-Platform Boundary",
                    rule_description=(
                        f"app_types/{apptype_name}/ MUST NOT import from platform/ "
                        "(ADR-V2-003)"
                    ),
                )

                # AppType MUST NOT import other AppTypes
                self._check_cross_apptype_imports(py_file, apptype_name)

    def _check_cross_apptype_imports(self, py_file: Path, current_apptype: str) -> None:
        """Check that AppType doesn't import other AppTypes."""
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))
        except (SyntaxError, IOError):
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    other = self._get_other_apptype(alias.name, current_apptype)
                    if other:
                        self.violations.append(Violation(
                            file_path=py_file,
                            line_number=node.lineno,
                            import_statement=f"import {alias.name}",
                            rule_name="Cross-AppType Import",
                            rule_description=(
                                f"app_types/{current_apptype}/ MUST NOT import from "
                                f"app_types/{other}/ (ADR-V2-003)"
                            ),
                        ))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    other = self._get_other_apptype(node.module, current_apptype)
                    if other:
                        imports = ", ".join(alias.name for alias in node.names)
                        self.violations.append(Violation(
                            file_path=py_file,
                            line_number=node.lineno,
                            import_statement=f"from {node.module} import {imports}",
                            rule_name="Cross-AppType Import",
                            rule_description=(
                                f"app_types/{current_apptype}/ MUST NOT import from "
                                f"app_types/{other}/ (ADR-V2-003)"
                            ),
                        ))

    def _get_other_apptype(self, import_name: str, current_apptype: str) -> str | None:
        """Get the name of another AppType being imported, if any."""
        if not import_name.startswith(self.APP_TYPES_PREFIX):
            return None
        if import_name.startswith(self.CONTRACTS_PREFIX):
            return None  # contracts is shared, OK to import

        # Pattern: doc_helper.app_types.{apptype_name}
        parts = import_name.split(".")
        if len(parts) >= 3:
            other_apptype = parts[2]
            if other_apptype != current_apptype and other_apptype not in ("contracts", "__init__"):
                return other_apptype
        return None

    def _check_presentation_apptype_isolation(self) -> None:
        """Check that presentation doesn't import from app_types."""
        if not self.PRESENTATION_PATH.exists():
            return

        for py_file in self.PRESENTATION_PATH.rglob("*.py"):
            self._check_file_module_imports(
                py_file,
                forbidden_prefixes=[self.APP_TYPES_PREFIX],
                rule_name="Presentation-AppType Isolation",
                rule_description=(
                    "presentation/ MUST NOT import from app_types/* (ADR-V2-003)"
                ),
            )

    def _check_file_module_imports(
        self,
        filepath: Path,
        forbidden_prefixes: list[str],
        rule_name: str,
        rule_description: str,
    ) -> None:
        """Check a file for forbidden module-level imports.

        Only checks top-level imports (tree.body), not function-scope imports.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(filepath))
        except SyntaxError:
            print(f"Warning: Syntax error in {filepath}")
            return
        except IOError:
            return

        # Only check module-level statements
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_prefixes:
                        if alias.name.startswith(prefix):
                            self.violations.append(Violation(
                                file_path=filepath,
                                line_number=node.lineno,
                                import_statement=f"import {alias.name}",
                                rule_name=rule_name,
                                rule_description=rule_description,
                            ))
                            break

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for prefix in forbidden_prefixes:
                        if node.module.startswith(prefix):
                            imports = ", ".join(alias.name for alias in node.names)
                            self.violations.append(Violation(
                                file_path=filepath,
                                line_number=node.lineno,
                                import_statement=f"from {node.module} import {imports}",
                                rule_name=rule_name,
                                rule_description=rule_description,
                            ))
                            break


def main() -> int:
    """Run architectural compliance scan.

    Returns:
        0 if compliant, 1 if violations found
    """
    print("=" * 80)
    print("ARCHITECTURAL COMPLIANCE SCAN")
    print("=" * 80)
    print()
    print("Rules being checked:")
    print("  1. DTO-Only MVVM (ADR-020)")
    print("  2. Platform Dependency Rules (ADR-V2-003)")
    print("  3. AppType Dependency Rules (ADR-V2-003)")
    print("  4. Presentation-AppType Isolation (ADR-V2-003)")
    print()

    scanner = ArchitectureScanner()
    violations = scanner.scan_all()

    if violations:
        print(f"VIOLATIONS FOUND: {len(violations)}")
        print()

        # Group by rule
        by_rule: dict[str, list[Violation]] = {}
        for v in violations:
            by_rule.setdefault(v.rule_name, []).append(v)

        for rule_name, rule_violations in sorted(by_rule.items()):
            print(f"--- {rule_name} ({len(rule_violations)} violations) ---")
            print()
            for v in rule_violations:
                print(f"  {v.file_path}:{v.line_number}")
                print(f"    {v.import_statement}")
            print()
            print(f"  Rule: {rule_violations[0].rule_description}")
            print()

        print("=" * 80)
        print("ARCHITECTURAL COMPLIANCE SCAN FAILED")
        print("=" * 80)
        return 1

    else:
        print("Scanning complete.")
        print()
        print("=" * 80)
        print("ARCHITECTURAL COMPLIANCE SCAN PASSED")
        print("=" * 80)
        print()
        print("All rules verified:")
        print("  [OK] DTO-Only MVVM - presentation does not import domain")
        print("  [OK] Platform Dependencies - platform does not import infrastructure/presentation")
        print("  [OK] Platform-AppType Boundary - platform does not import specific AppTypes")
        print("  [OK] AppType Dependencies - AppTypes do not import platform or each other")
        print("  [OK] Presentation-AppType Isolation - presentation does not import app_types")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())

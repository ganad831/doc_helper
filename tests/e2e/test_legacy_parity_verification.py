"""Legacy parity verification test.

PHASE 3: Legacy Parity Verification
=====================================

This test verifies that all required legacy features from the old codebase
have been implemented in the new architecture.

Based on unified_upgrade_plan_FINAL.md Section 2.1: Legacy Parity Matrix

VERIFICATION APPROACH:
- Check for presence of key files and classes
- Verify each feature has required components
- Report which features are implemented vs missing
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional

import pytest

from doc_helper.domain.schema.field_type import FieldType


class LegacyFeature:
    """Represents a legacy feature to verify."""

    def __init__(
        self,
        name: str,
        description: str,
        required_files: Optional[List[str]] = None,
        required_classes: Optional[List[str]] = None,
        verification_func: Optional[callable] = None,
    ):
        """Initialize legacy feature.

        Args:
            name: Feature name
            description: Feature description
            required_files: List of file paths that must exist
            required_classes: List of fully-qualified class names that must exist
            verification_func: Optional custom verification function
        """
        self.name = name
        self.description = description
        self.required_files = required_files or []
        self.required_classes = required_classes or []
        self.verification_func = verification_func
        self.is_implemented = False
        self.missing_components: List[str] = []


class TestLegacyParityVerification:
    """Verify legacy feature parity."""

    def test_legacy_parity_matrix(self):
        """Verify all required legacy features are implemented.

        This test systematically checks each legacy feature from the parity matrix
        and reports which are implemented and which are missing.
        """
        # ============================================================
        # DEFINE LEGACY FEATURES TO VERIFY
        # ============================================================

        features = [
            # ============================================================
            # P0: CRITICAL FEATURES (Must be present)
            # ============================================================
            LegacyFeature(
                name="Project CRUD",
                description="Create, Open, Save, Delete projects",
                required_files=[
                    "src/doc_helper/application/commands/create_project_command.py",
                    "src/doc_helper/application/queries/get_project_query.py",
                    "src/doc_helper/application/commands/save_project_command.py",
                ],
                required_classes=[
                    "doc_helper.application.commands.create_project_command.CreateProjectCommand",
                    "doc_helper.application.queries.get_project_query.GetProjectQuery",
                    "doc_helper.application.commands.save_project_command.SaveProjectCommand",
                ],
            ),
            LegacyFeature(
                name="12 Field Types",
                description="All 12 field types implemented",
                verification_func=self._verify_12_field_types,
            ),
            LegacyFeature(
                name="Validation System",
                description="Field validation with constraints",
                required_files=[
                    "src/doc_helper/domain/validation/constraints.py",
                    "src/doc_helper/domain/validation/validation_result.py",
                    "src/doc_helper/application/services/validation_service.py",
                ],
                required_classes=[
                    "doc_helper.domain.validation.constraints.RequiredConstraint",
                    "doc_helper.domain.validation.validation_result.ValidationResult",
                    "doc_helper.application.services.validation_service.ValidationService",
                ],
            ),
            LegacyFeature(
                name="Formula System",
                description="Formula evaluation with dependency tracking",
                required_files=[
                    "src/doc_helper/domain/formula/parser.py",
                    "src/doc_helper/domain/formula/evaluator.py",
                    "src/doc_helper/application/services/formula_service.py",
                ],
                required_classes=[
                    "doc_helper.domain.formula.parser.FormulaParser",
                    "doc_helper.domain.formula.evaluator.FormulaEvaluator",
                    "doc_helper.application.services.formula_service.FormulaService",
                ],
            ),
            LegacyFeature(
                name="Control System",
                description="Inter-field dependencies (VALUE_SET, VISIBILITY, ENABLE)",
                required_files=[
                    "src/doc_helper/domain/control/control_rule.py",
                    "src/doc_helper/domain/control/control_effect.py",
                    "src/doc_helper/application/services/control_service.py",
                ],
                required_classes=[
                    "doc_helper.domain.control.control_rule.ControlRule",
                    "doc_helper.domain.control.control_effect.ControlEffect",
                    "doc_helper.application.services.control_service.ControlService",
                ],
            ),
            LegacyFeature(
                name="Override System",
                description="Override state machine (PENDING → ACCEPTED → SYNCED)",
                required_files=[
                    "src/doc_helper/domain/override/override_entity.py",
                    "src/doc_helper/domain/override/override_state.py",
                ],
                required_classes=[
                    "doc_helper.domain.override.override_entity.Override",
                    "doc_helper.domain.override.override_state.OverrideState",
                ],
            ),
            LegacyFeature(
                name="Transformers (15+)",
                description="Bidirectional value transformers for document generation",
                required_files=[
                    "src/doc_helper/domain/document/transformer.py",
                    "src/doc_helper/domain/document/transformers.py",
                ],
                verification_func=self._verify_transformers,
            ),
            LegacyFeature(
                name="Word/Excel/PDF Adapters",
                description="Document generation adapters",
                required_files=[
                    "src/doc_helper/infrastructure/document/word_document_adapter.py",
                    "src/doc_helper/infrastructure/document/excel_document_adapter.py",
                    "src/doc_helper/infrastructure/document/pdf_document_adapter.py",
                ],
            ),
            # ============================================================
            # P1: IMPORTANT FEATURES (Should be present)
            # ============================================================
            LegacyFeature(
                name="Undo/Redo System",
                description="Command-based undo/redo",
                required_files=[
                    "src/doc_helper/application/undo/undo_manager.py",
                    "src/doc_helper/application/undo/field_undo_command.py",
                ],
                required_classes=[
                    "doc_helper.application.undo.undo_manager.UndoManager",
                    "doc_helper.application.undo.field_undo_command.SetFieldValueCommand",
                ],
            ),
            LegacyFeature(
                name="i18n System",
                description="Multi-language support (English/Arabic) with RTL",
                required_files=[
                    "src/doc_helper/domain/common/i18n.py",
                    "src/doc_helper/infrastructure/i18n/json_translation_service.py",
                    "src/doc_helper/application/services/translation_service.py",
                    "src/doc_helper/presentation/adapters/qt_translation_adapter.py",
                ],
                required_classes=[
                    "doc_helper.domain.common.i18n.Language",
                    "doc_helper.domain.common.i18n.TextDirection",
                    "doc_helper.infrastructure.i18n.json_translation_service.JsonTranslationService",
                    "doc_helper.application.services.translation_service.TranslationApplicationService",
                    "doc_helper.presentation.adapters.qt_translation_adapter.QtTranslationAdapter",
                ],
            ),
            # ============================================================
            # P2: OPTIONAL FEATURES (May be missing in v1)
            # ============================================================
            LegacyFeature(
                name="Recent Projects",
                description="Track last 5 projects for quick reopen",
                required_files=[
                    "src/doc_helper/infrastructure/filesystem/recent_projects_storage.py",
                ],
            ),
            LegacyFeature(
                name="Tab Navigation History",
                description="Back/forward navigation between tabs",
                required_files=[
                    "src/doc_helper/presentation/adapters/navigation_adapter.py",
                ],
            ),
            LegacyFeature(
                name="Figure Numbering",
                description="Automatic figure caption numbering",
                required_files=[
                    "src/doc_helper/domain/file/figure_number.py",
                ],
            ),
            LegacyFeature(
                name="Settings Dialog",
                description="Settings dialog with language selector",
                required_files=[
                    "src/doc_helper/presentation/dialogs/settings_dialog.py",
                ],
            ),
            LegacyFeature(
                name="Menu Bar",
                description="Main menu bar with File/Edit/View menus",
                verification_func=self._verify_menu_bar,
            ),
            LegacyFeature(
                name="Auto-save Before Generate",
                description="Automatically save project before document generation",
                verification_func=self._verify_auto_save,
            ),
            LegacyFeature(
                name="Override Cleanup Post-Gen",
                description="Cleanup SYNCED overrides after document generation",
                verification_func=self._verify_override_cleanup,
            ),
        ]

        # ============================================================
        # VERIFY EACH FEATURE
        # ============================================================

        for feature in features:
            feature.is_implemented, feature.missing_components = self._verify_feature(
                feature
            )

        # ============================================================
        # GENERATE REPORT
        # ============================================================

        report = self._generate_report(features)
        print("\n" + "=" * 80)
        print("LEGACY PARITY VERIFICATION REPORT")
        print("=" * 80)
        print(report)
        print("=" * 80)

        # ============================================================
        # ASSERT: All P0 features must be present
        # ============================================================

        p0_features = features[:8]  # First 8 are P0
        missing_p0 = [f for f in p0_features if not f.is_implemented]

        if missing_p0:
            missing_names = [f.name for f in missing_p0]
            pytest.fail(
                f"CRITICAL: {len(missing_p0)} P0 features missing: {missing_names}"
            )

    def _verify_feature(self, feature: LegacyFeature) -> tuple[bool, List[str]]:
        """Verify a single feature.

        Args:
            feature: Feature to verify

        Returns:
            Tuple of (is_implemented, missing_components)
        """
        missing = []

        # Check required files
        for file_path in feature.required_files:
            if not Path(file_path).exists():
                missing.append(f"File: {file_path}")

        # Check required classes
        for class_path in feature.required_classes:
            if not self._class_exists(class_path):
                missing.append(f"Class: {class_path}")

        # Run custom verification function
        if feature.verification_func:
            custom_result = feature.verification_func()
            if custom_result is not True:
                missing.append(f"Custom check: {custom_result}")

        is_implemented = len(missing) == 0
        return is_implemented, missing

    def _class_exists(self, fully_qualified_name: str) -> bool:
        """Check if a class exists by fully-qualified name.

        Args:
            fully_qualified_name: e.g., "doc_helper.domain.project.project.Project"

        Returns:
            True if class can be imported
        """
        try:
            parts = fully_qualified_name.split(".")
            module_name = ".".join(parts[:-1])
            class_name = parts[-1]

            module = importlib.import_module(module_name)
            return hasattr(module, class_name)
        except (ImportError, AttributeError):
            return False

    def _verify_12_field_types(self) -> bool:
        """Verify all 12 field types are present.

        Returns:
            True if all 12 field types present, error message otherwise
        """
        expected_types = {
            "TEXT",
            "TEXTAREA",
            "NUMBER",
            "DATE",
            "DROPDOWN",
            "CHECKBOX",
            "RADIO",
            "CALCULATED",
            "LOOKUP",
            "FILE",
            "IMAGE",
            "TABLE",
        }

        actual_types = {ft.name for ft in FieldType}

        missing = expected_types - actual_types
        if missing:
            return f"Missing field types: {missing}"

        return True

    def _verify_transformers(self) -> bool:
        """Verify 15+ transformers are present.

        Returns:
            True if 15+ transformers present, error message otherwise
        """
        # Check that transformer files exist
        transformer_file = Path("src/doc_helper/domain/document/transformers.py")

        if not transformer_file.exists():
            return "Transformers file missing"

        # Count transformer classes in the file
        try:
            from doc_helper.domain.document.transformers import get_all_transformers
            transformers = get_all_transformers()
            transformer_count = len(transformers)

            if transformer_count < 15:
                return f"Only {transformer_count} transformers found (expected 15+)"

            return True
        except ImportError as e:
            return f"Failed to import transformers: {e}"

    def _verify_menu_bar(self) -> bool:
        """Verify menu bar is implemented in MainWindow.

        Returns:
            True if menu bar present, error message otherwise
        """
        main_window_path = Path("src/doc_helper/presentation/views/main_window.py")

        if not main_window_path.exists():
            return "MainWindow file missing"

        # Read file and check for menu creation
        content = main_window_path.read_text(encoding="utf-8")
        has_menu = (
            "menuBar" in content or "create_menu" in content or "QMenuBar" in content
        )

        if not has_menu:
            return "Menu bar code not found in MainWindow"

        return True

    def _verify_auto_save(self) -> bool:
        """Verify auto-save before generate is implemented.

        Returns:
            True if auto-save present, error message otherwise
        """
        generate_command_path = Path(
            "src/doc_helper/application/commands/document/generate_document.py"
        )

        if not generate_command_path.exists():
            return "GenerateDocumentCommand file missing"

        # Check if generate command saves before generation
        content = generate_command_path.read_text(encoding="utf-8")
        has_auto_save = (
            "save_project" in content.lower() or "auto_save" in content.lower()
        )

        if not has_auto_save:
            return "Auto-save logic not found in GenerateDocumentCommand"

        return True

    def _verify_override_cleanup(self) -> bool:
        """Verify override cleanup post-generation is implemented.

        Returns:
            True if cleanup present, error message otherwise
        """
        cleanup_command_path = Path(
            "src/doc_helper/application/commands/override/cleanup_synced.py"
        )

        if not cleanup_command_path.exists():
            return "Cleanup command file missing"

        return True

    def _generate_report(self, features: List[LegacyFeature]) -> str:
        """Generate human-readable report.

        Args:
            features: List of verified features

        Returns:
            Report string
        """
        lines = []

        # Summary
        implemented_count = sum(1 for f in features if f.is_implemented)
        total_count = len(features)
        percentage = (implemented_count / total_count) * 100

        lines.append(f"\nSUMMARY: {implemented_count}/{total_count} features implemented ({percentage:.1f}%)")
        lines.append("")

        # P0 Features
        lines.append("P0 FEATURES (Critical):")
        lines.append("-" * 40)
        for feature in features[:8]:
            status = "✅" if feature.is_implemented else "❌"
            lines.append(f"{status} {feature.name}")
            if not feature.is_implemented:
                for component in feature.missing_components:
                    lines.append(f"   - Missing: {component}")
        lines.append("")

        # P1 Features
        lines.append("P1 FEATURES (Important):")
        lines.append("-" * 40)
        for feature in features[8:10]:
            status = "✅" if feature.is_implemented else "❌"
            lines.append(f"{status} {feature.name}")
            if not feature.is_implemented:
                for component in feature.missing_components:
                    lines.append(f"   - Missing: {component}")
        lines.append("")

        # P2 Features
        lines.append("P2 FEATURES (Optional):")
        lines.append("-" * 40)
        for feature in features[10:]:
            status = "✅" if feature.is_implemented else "❌"
            lines.append(f"{status} {feature.name}")
            if not feature.is_implemented:
                for component in feature.missing_components:
                    lines.append(f"   - Missing: {component}")
        lines.append("")

        return "\n".join(lines)


# ============================================================
# TEST EXECUTION
# ============================================================
# Run with: pytest tests/e2e/test_legacy_parity_verification.py -v -s
#
# This test will:
# 1. Check for presence of all required files and classes
# 2. Verify each legacy feature is implemented
# 3. Generate a detailed report showing what's missing
# 4. FAIL if any P0 (critical) features are missing
# 5. PASS if all P0 features are present (P1/P2 warnings only)

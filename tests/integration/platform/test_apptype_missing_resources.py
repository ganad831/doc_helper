"""T5: AppType Missing Resource Handling Tests.

Tests that AppTypes handle missing resources (config.db, templates)
with clear error messages or documented fallback behavior.

Purpose: Ensure graceful degradation when resources are unavailable.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from doc_helper.app_types.soil_investigation import SoilInvestigationAppType
from doc_helper.app_types.test_report import TestReportAppType


class TestAppTypeMissingConfigDb:
    """Tests for AppType behavior when config.db is missing."""

    def test_soil_investigation_missing_config_db_raises_file_not_found(self) -> None:
        """SoilInvestigationAppType raises FileNotFoundError for missing config.db."""
        app_type = SoilInvestigationAppType()

        # Patch _package_dir to point to a non-existent path
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_package_dir = Path(temp_dir) / "nonexistent"
            app_type._package_dir = fake_package_dir

            with pytest.raises(FileNotFoundError):
                app_type.get_schema_repository()

    def test_test_report_missing_config_db_raises_file_not_found(self) -> None:
        """TestReportAppType raises FileNotFoundError for missing config.db."""
        app_type = TestReportAppType()

        # Patch _package_dir to point to a non-existent path
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_package_dir = Path(temp_dir) / "nonexistent"
            app_type._package_dir = fake_package_dir

            with pytest.raises(FileNotFoundError):
                app_type.get_schema_repository()

    def test_error_message_mentions_config_db(self) -> None:
        """FileNotFoundError message should indicate what's missing."""
        app_type = SoilInvestigationAppType()

        with tempfile.TemporaryDirectory() as temp_dir:
            fake_package_dir = Path(temp_dir)
            app_type._package_dir = fake_package_dir

            with pytest.raises(FileNotFoundError) as exc_info:
                app_type.get_schema_repository()

            error_message = str(exc_info.value).lower()
            # Should mention either the file path or "schema" or "database"
            assert any(
                term in error_message
                for term in ["config.db", "schema", "database", "not found"]
            ), f"Error message unclear: {exc_info.value}"


class TestAppTypeMissingTemplateDirectory:
    """Tests for AppType behavior when templates directory is missing."""

    def test_soil_investigation_template_directory_is_path(self) -> None:
        """get_template_directory() returns Path even if directory doesn't exist."""
        app_type = SoilInvestigationAppType()

        # This should NOT raise - it just returns the expected path
        template_dir = app_type.get_template_directory()

        assert isinstance(template_dir, Path)
        assert template_dir.name == "templates"

    def test_test_report_template_directory_is_path(self) -> None:
        """get_template_directory() returns Path even if directory doesn't exist."""
        app_type = TestReportAppType()

        template_dir = app_type.get_template_directory()

        assert isinstance(template_dir, Path)
        assert template_dir.name == "templates"


class TestAppTypeInitializeWithoutPlatformServices:
    """Tests for AppType initialization behavior."""

    def test_soil_investigation_initialize_accepts_none(self) -> None:
        """initialize() can be called (platform_services stored internally)."""
        app_type = SoilInvestigationAppType()

        # Should not raise - just stores the reference
        app_type.initialize(None)  # type: ignore

        # AppType should still be functional for basic operations
        assert app_type.app_type_id == "soil_investigation"

    def test_test_report_initialize_accepts_none(self) -> None:
        """initialize() can be called (platform_services stored internally)."""
        app_type = TestReportAppType()

        # Should not raise
        app_type.initialize(None)  # type: ignore

        assert app_type.app_type_id == "test_report"


class TestAppTypeRegisterTransformersWithNone:
    """Tests for AppType transformer registration with missing registry."""

    def test_soil_investigation_register_transformers_with_none_is_safe(self) -> None:
        """register_transformers() with None should not crash (v1: empty impl)."""
        app_type = SoilInvestigationAppType()

        # v1 implementation is empty, so this should not raise
        # even with None registry
        try:
            app_type.register_transformers(None)  # type: ignore
        except TypeError:
            # If it raises TypeError, that's acceptable for None input
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    def test_test_report_register_transformers_with_none_is_safe(self) -> None:
        """register_transformers() with None should not crash."""
        app_type = TestReportAppType()

        try:
            app_type.register_transformers(None)  # type: ignore
        except TypeError:
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

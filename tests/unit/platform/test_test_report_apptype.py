"""T3: TestReportAppType Unit Tests.

Direct unit tests for TestReportAppType to verify:
- Instantiation works
- Properties return expected values
- IAppType interface compliance

These tests do NOT require config.db or other external resources.
"""

import pytest
from pathlib import Path

from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata
from doc_helper.app_types.contracts.i_app_type import IAppType
from doc_helper.app_types.test_report import TestReportAppType


class TestTestReportAppTypeInstantiation:
    """Tests for TestReportAppType creation."""

    def test_can_instantiate(self) -> None:
        """TestReportAppType can be created without errors."""
        app_type = TestReportAppType()
        assert app_type is not None

    def test_implements_iapptype(self) -> None:
        """TestReportAppType implements IAppType interface."""
        app_type = TestReportAppType()
        assert isinstance(app_type, IAppType)


class TestTestReportAppTypeProperties:
    """Tests for TestReportAppType properties."""

    @pytest.fixture
    def app_type(self) -> TestReportAppType:
        """Create AppType instance for testing."""
        return TestReportAppType()

    def test_app_type_id_returns_correct_value(
        self, app_type: TestReportAppType
    ) -> None:
        """app_type_id property returns 'test_report'."""
        assert app_type.app_type_id == "test_report"

    def test_metadata_returns_app_type_metadata(
        self, app_type: TestReportAppType
    ) -> None:
        """metadata property returns AppTypeMetadata instance."""
        metadata = app_type.metadata
        assert isinstance(metadata, AppTypeMetadata)

    def test_metadata_has_correct_app_type_id(
        self, app_type: TestReportAppType
    ) -> None:
        """metadata.app_type_id matches app_type_id property."""
        assert app_type.metadata.app_type_id == app_type.app_type_id

    def test_metadata_has_name(self, app_type: TestReportAppType) -> None:
        """metadata has a non-empty name."""
        assert app_type.metadata.name
        assert len(app_type.metadata.name) > 0

    def test_metadata_has_version(self, app_type: TestReportAppType) -> None:
        """metadata has a version string."""
        assert app_type.metadata.version
        assert len(app_type.metadata.version) > 0


class TestTestReportAppTypeMethods:
    """Tests for TestReportAppType methods."""

    @pytest.fixture
    def app_type(self) -> TestReportAppType:
        """Create AppType instance for testing."""
        return TestReportAppType()

    def test_get_schema_repository_is_callable(
        self, app_type: TestReportAppType
    ) -> None:
        """get_schema_repository method exists and is callable."""
        assert hasattr(app_type, "get_schema_repository")
        assert callable(app_type.get_schema_repository)

    def test_register_transformers_is_callable(
        self, app_type: TestReportAppType
    ) -> None:
        """register_transformers method exists and is callable."""
        assert hasattr(app_type, "register_transformers")
        assert callable(app_type.register_transformers)

    def test_initialize_is_callable(
        self, app_type: TestReportAppType
    ) -> None:
        """initialize method exists and is callable."""
        assert hasattr(app_type, "initialize")
        assert callable(app_type.initialize)

    def test_get_template_directory_returns_path(
        self, app_type: TestReportAppType
    ) -> None:
        """get_template_directory returns a Path object."""
        template_dir = app_type.get_template_directory()
        assert isinstance(template_dir, Path)

    def test_get_template_directory_ends_with_templates(
        self, app_type: TestReportAppType
    ) -> None:
        """get_template_directory returns path ending with 'templates'."""
        template_dir = app_type.get_template_directory()
        assert template_dir.name == "templates"

    def test_get_default_template_returns_filename(
        self, app_type: TestReportAppType
    ) -> None:
        """get_default_template returns a template filename."""
        default_template = app_type.get_default_template()
        # TestReportAppType defines a default template
        assert default_template == "test_report.docx"


class TestTestReportAppTypeIAppTypeCompliance:
    """Tests verifying full IAppType interface compliance."""

    def test_has_all_iapptype_methods(self) -> None:
        """TestReportAppType has all IAppType interface methods."""
        app_type = TestReportAppType()

        # Properties
        assert hasattr(app_type, "app_type_id")
        assert hasattr(app_type, "metadata")

        # Methods
        assert hasattr(app_type, "get_schema_repository")
        assert hasattr(app_type, "register_transformers")
        assert hasattr(app_type, "initialize")

    def test_properties_are_not_none(self) -> None:
        """All required properties return non-None values."""
        app_type = TestReportAppType()

        assert app_type.app_type_id is not None
        assert app_type.metadata is not None


class TestTestReportAppTypeDiffersFromSoilInvestigation:
    """Tests that verify TestReportAppType is distinct from SoilInvestigationAppType."""

    def test_different_app_type_ids(self) -> None:
        """TestReportAppType has different app_type_id from SoilInvestigationAppType."""
        from doc_helper.app_types.soil_investigation import SoilInvestigationAppType

        soil_app = SoilInvestigationAppType()
        test_app = TestReportAppType()

        assert soil_app.app_type_id != test_app.app_type_id
        assert soil_app.app_type_id == "soil_investigation"
        assert test_app.app_type_id == "test_report"

    def test_different_metadata_names(self) -> None:
        """TestReportAppType has different metadata name."""
        from doc_helper.app_types.soil_investigation import SoilInvestigationAppType

        soil_app = SoilInvestigationAppType()
        test_app = TestReportAppType()

        assert soil_app.metadata.name != test_app.metadata.name

"""T2: SoilInvestigationAppType Unit Tests.

Direct unit tests for SoilInvestigationAppType to verify:
- Instantiation works
- Properties return expected values
- IAppType interface compliance

These tests do NOT require config.db or other external resources.
"""

import pytest
from pathlib import Path

from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata
from doc_helper.app_types.contracts.i_app_type import IAppType
from doc_helper.app_types.soil_investigation import (
    SoilInvestigationAppType,
    DEFAULT_APP_TYPE_ID,
)


class TestSoilInvestigationAppTypeInstantiation:
    """Tests for SoilInvestigationAppType creation."""

    def test_can_instantiate(self) -> None:
        """SoilInvestigationAppType can be created without errors."""
        app_type = SoilInvestigationAppType()
        assert app_type is not None

    def test_implements_iapptype(self) -> None:
        """SoilInvestigationAppType implements IAppType interface."""
        app_type = SoilInvestigationAppType()
        assert isinstance(app_type, IAppType)

    def test_default_app_type_id_constant(self) -> None:
        """DEFAULT_APP_TYPE_ID is 'soil_investigation'."""
        assert DEFAULT_APP_TYPE_ID == "soil_investigation"


class TestSoilInvestigationAppTypeProperties:
    """Tests for SoilInvestigationAppType properties."""

    @pytest.fixture
    def app_type(self) -> SoilInvestigationAppType:
        """Create AppType instance for testing."""
        return SoilInvestigationAppType()

    def test_app_type_id_returns_correct_value(
        self, app_type: SoilInvestigationAppType
    ) -> None:
        """app_type_id property returns 'soil_investigation'."""
        assert app_type.app_type_id == "soil_investigation"

    def test_app_type_id_matches_constant(
        self, app_type: SoilInvestigationAppType
    ) -> None:
        """app_type_id matches DEFAULT_APP_TYPE_ID constant."""
        assert app_type.app_type_id == DEFAULT_APP_TYPE_ID

    def test_metadata_returns_app_type_metadata(
        self, app_type: SoilInvestigationAppType
    ) -> None:
        """metadata property returns AppTypeMetadata instance."""
        metadata = app_type.metadata
        assert isinstance(metadata, AppTypeMetadata)

    def test_metadata_has_correct_app_type_id(
        self, app_type: SoilInvestigationAppType
    ) -> None:
        """metadata.app_type_id matches app_type_id property."""
        assert app_type.metadata.app_type_id == app_type.app_type_id

    def test_metadata_has_name(self, app_type: SoilInvestigationAppType) -> None:
        """metadata has a non-empty name."""
        assert app_type.metadata.name
        assert len(app_type.metadata.name) > 0

    def test_metadata_has_version(self, app_type: SoilInvestigationAppType) -> None:
        """metadata has a version string."""
        assert app_type.metadata.version
        assert len(app_type.metadata.version) > 0


class TestSoilInvestigationAppTypeMethods:
    """Tests for SoilInvestigationAppType methods."""

    @pytest.fixture
    def app_type(self) -> SoilInvestigationAppType:
        """Create AppType instance for testing."""
        return SoilInvestigationAppType()

    def test_get_schema_repository_is_callable(
        self, app_type: SoilInvestigationAppType
    ) -> None:
        """get_schema_repository method exists and is callable."""
        assert hasattr(app_type, "get_schema_repository")
        assert callable(app_type.get_schema_repository)

    def test_register_transformers_is_callable(
        self, app_type: SoilInvestigationAppType
    ) -> None:
        """register_transformers method exists and is callable."""
        assert hasattr(app_type, "register_transformers")
        assert callable(app_type.register_transformers)

    def test_initialize_is_callable(
        self, app_type: SoilInvestigationAppType
    ) -> None:
        """initialize method exists and is callable."""
        assert hasattr(app_type, "initialize")
        assert callable(app_type.initialize)

    def test_get_template_directory_returns_path(
        self, app_type: SoilInvestigationAppType
    ) -> None:
        """get_template_directory returns a Path object."""
        template_dir = app_type.get_template_directory()
        assert isinstance(template_dir, Path)

    def test_get_template_directory_ends_with_templates(
        self, app_type: SoilInvestigationAppType
    ) -> None:
        """get_template_directory returns path ending with 'templates'."""
        template_dir = app_type.get_template_directory()
        assert template_dir.name == "templates"

    def test_get_default_template_returns_none_or_string(
        self, app_type: SoilInvestigationAppType
    ) -> None:
        """get_default_template returns None or a string (v1: None)."""
        default_template = app_type.get_default_template()
        assert default_template is None or isinstance(default_template, str)


class TestSoilInvestigationAppTypeIAppTypeCompliance:
    """Tests verifying full IAppType interface compliance."""

    def test_has_all_iapptype_methods(self) -> None:
        """SoilInvestigationAppType has all IAppType interface methods."""
        app_type = SoilInvestigationAppType()

        # Properties
        assert hasattr(app_type, "app_type_id")
        assert hasattr(app_type, "metadata")

        # Methods
        assert hasattr(app_type, "get_schema_repository")
        assert hasattr(app_type, "register_transformers")
        assert hasattr(app_type, "initialize")

    def test_properties_are_not_none(self) -> None:
        """All required properties return non-None values."""
        app_type = SoilInvestigationAppType()

        assert app_type.app_type_id is not None
        assert app_type.metadata is not None
